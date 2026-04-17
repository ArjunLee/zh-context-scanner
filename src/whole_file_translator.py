"""
File: whole_file_translator.py
Description: Whole-file translation engine using OpenAI SDK for DeepSeek API
Author: Arjun Li
Created: 2026-04-15
Last Modified: 2026-04-17
Related modules: models.py, backup_manager.py, prompts/
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from pathlib import Path

from openai import APIConnectionError, APIError, AsyncOpenAI, RateLimitError

from src.llm_client import LLMClientManager, LLMConfig
from src.models import (
    FileTranslationResult,
    TranslationMode,
    replace_file_header_keys_in_content,
)
from src.prompts import build_prompt_with_terminology
from src.solid_logger import get_logger

MAX_TOKENS = 32000  # Approximate token limit for safety
CHARS_PER_TOKEN = 2.5  # Approximate chars per token for Chinese code
MAX_CONCURRENT = 3  # Max concurrent API calls

# DeepSeek model output limits (from official docs)
# deepseek-chat: DEFAULT 4K, MAXIMUM 8K
# deepseek-reasoner: DEFAULT 32K, MAXIMUM 64K
DEEPSEEK_CHAT_MAX_OUTPUT = 8192
DEEPSEEK_REASONER_MAX_OUTPUT = 64000


def estimate_tokens(content: str) -> int:
    """Estimate token count for content.

    Args:
        content: Text content to estimate

    Returns:
        Estimated token count
    """
    return int(len(content) / CHARS_PER_TOKEN)


class WholeFileTranslator:
    """Translate entire source files via LLM API using OpenAI SDK.

    Supports two translation modes:
    - COMMENT_ONLY: Only translate Chinese comments (incremental)
    - FULL: Translate ALL Chinese text (whole-file)

    Auto-binding feature:
    - COMMENT_ONLY -> deepseek-chat (fast, cheap, 8K output)
    - FULL -> deepseek-reasoner (64K output for large files)
    - Can be overridden with force_model=True
    """

    # Recommended models for each translation mode
    RECOMMENDED_MODELS = {
        TranslationMode.COMMENT_ONLY: "deepseek-chat",
        TranslationMode.FULL: "deepseek-reasoner",
    }

    @staticmethod
    def get_recommended_model(mode: TranslationMode) -> str:
        """Get recommended model for translation mode.

        Args:
            mode: Translation mode (comment_only or full)

        Returns:
            Recommended model name
        """
        return WholeFileTranslator.RECOMMENDED_MODELS.get(mode, "deepseek-chat")

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
        max_concurrent: int = MAX_CONCURRENT,
        force_model: bool = False,
    ) -> None:
        self.api_key = api_key
        self.configured_model = model  # User configured model
        self.model = model  # Current active model (may change)
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.force_model = force_model  # Skip auto-binding
        self._llm_client: LLMClientManager | None = None
        self._semaphore: asyncio.Semaphore | None = None

    def _get_llm_client(self) -> LLMClientManager:
        """Get or create LLM client manager."""
        if self._llm_client is None:
            config = LLMConfig(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model,
                max_concurrent=self.max_concurrent,
            )
            self._llm_client = LLMClientManager(config)
        return self._llm_client

    def _get_client(self) -> AsyncOpenAI:
        """Get OpenAI client (backward compatibility)."""
        return self._get_llm_client()._get_client()

    def _get_semaphore(self) -> asyncio.Semaphore:
        """Get or create semaphore for concurrent control."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self._semaphore

    def _calculate_max_output_tokens(self, estimated_input_tokens: int) -> int:
        """Calculate appropriate max_tokens based on model and input size.

        Args:
            estimated_input_tokens: Estimated token count for input file

        Returns:
            max_tokens value to use in API call
        """
        # Output size is typically similar to input size for translation
        estimated_output = int(estimated_input_tokens * 1.1)

        if self.model == "deepseek-reasoner":
            # deepseek-reasoner: max 64K output
            return min(estimated_output, DEEPSEEK_REASONER_MAX_OUTPUT)
        else:
            # deepseek-chat: max 8K output
            return min(estimated_output, DEEPSEEK_CHAT_MAX_OUTPUT)

    async def close(self) -> None:
        """Close the client."""
        if self._llm_client:
            await self._llm_client.close()
            self._llm_client = None

    async def translate_file(
        self,
        file_path: Path,
        mode: TranslationMode,
    ) -> FileTranslationResult:
        """Translate a source file.

        Strategy:
        - COMMENT_ONLY: Extract comments, translate each, replace in-place
        - FULL: Whole-file translation (send entire file to LLM)

        Auto-binding:
        - If force_model=False, automatically select best model for mode
        - COMMENT_ONLY -> deepseek-chat, FULL -> deepseek-reasoner

        Args:
            file_path: Path to the source file
            mode: Translation mode (comment_only or full)

        Returns:
            FileTranslationResult with original and translated content
        """
        logger = get_logger()

        # Auto-binding: select best model for mode (unless forced)
        if not self.force_model:
            recommended = self.get_recommended_model(mode)
            if recommended != self.model:
                logger.info(
                    f"Auto-binding: {mode.value} -> {recommended} "
                    f"(configured: {self.configured_model})"
                )
                self.model = recommended
                # Reset client for new model
                if self._llm_client:
                    await self._llm_client.close()
                    self._llm_client = None

        if not file_path.exists():
            return FileTranslationResult(
                file_path=file_path,
                original_content="",
                translated_content="",
                mode=mode,
                success=False,
                error="File not found",
            )

        # Branch: COMMENT_ONLY uses CommentTranslator for incremental replacement
        if mode == TranslationMode.COMMENT_ONLY:
            return await self._translate_comments_incremental(file_path, mode)

        # Branch: FULL uses whole-file translation
        return await self._translate_whole_file(file_path, mode)

    async def _translate_comments_incremental(
        self,
        file_path: Path,
        mode: TranslationMode,
    ) -> FileTranslationResult:
        """Incremental comment translation using CommentTranslator.

        This delegates to CommentTranslator for comment-only mode.
        """
        from src.comment_translator import CommentTranslator

        logger = get_logger()
        original_content = file_path.read_text(encoding="utf-8", errors="replace")

        # Use CommentTranslator for comment-only translation
        translator = CommentTranslator(
            api_key=self.api_key,
            model=self.model,
            base_url=self.base_url,
            max_concurrent=self.max_concurrent,
        )

        # Extract comments with Chinese
        comments = translator.extract_comments_with_chinese(file_path)
        if not comments:
            logger.info(f"No Chinese comments found in {file_path.name}")
            return FileTranslationResult(
                file_path=file_path,
                original_content=original_content,
                translated_content=original_content,  # No changes
                mode=mode,
                success=True,
                error=None,
            )

        logger.log_api_request(
            base_url=self.base_url,
            model=self.model,
            file_name=file_path.name,
            comment_count=len(comments),
        )

        import time
        start_time = time.perf_counter()

        # Batch translate comments
        translations = await translator.translate_comments_batch(comments, file_path)
        await translator.close()

        duration_ms = (time.perf_counter() - start_time) * 1000

        successful = [t for t in translations if t.success]
        failed = [t for t in translations if not t.success]

        # Log summary with duration
        logger.log_api_response(
            file_name=file_path.name,
            success_count=len(successful),
            fail_count=len(failed),
            duration_ms=duration_ms,
        )

        # Apply replacements
        modified_content = original_content
        lines = modified_content.splitlines(keepends=True)

        for t in successful:
            idx = t.line_no - 1
            if idx < len(lines):
                line_ending = "\n" if lines[idx].endswith("\n") else ""
                lines[idx] = t.translated_text + line_ending

        modified_content = "".join(lines)

        return FileTranslationResult(
            file_path=file_path,
            original_content=original_content,
            translated_content=modified_content,
            mode=mode,
            success=len(successful) > 0,
            error=None if not failed else f"{len(failed)} comments failed to translate",
        )

    async def _translate_whole_file(
        self,
        file_path: Path,
        mode: TranslationMode,
    ) -> FileTranslationResult:
        """Whole-file translation (send entire file to LLM)."""
        logger = get_logger()

        original_content = file_path.read_text(encoding="utf-8", errors="replace")
        estimated_tokens = estimate_tokens(original_content)

        # Replace file header keys with cached translations before sending to LLM
        content_for_translation = replace_file_header_keys_in_content(original_content)

        max_output_limit = DEEPSEEK_REASONER_MAX_OUTPUT if self.model == "deepseek-reasoner" else DEEPSEEK_CHAT_MAX_OUTPUT

        # Check if file output would exceed model's max_tokens limit
        # Output size ≈ input size for translation, add 10% buffer
        estimated_output_tokens = int(estimated_tokens * 1.1)
        if estimated_output_tokens > max_output_limit:
            model_hint = "deepseek-reasoner (64K output)" if self.model == "deepseek-chat" else "split into smaller files"
            return FileTranslationResult(
                file_path=file_path,
                original_content=original_content,
                translated_content="",
                mode=mode,
                success=False,
                error=f"Output exceeds {self.model} limit: ~{estimated_output_tokens} tokens (max {max_output_limit}). Try: {model_hint}",
            )

        # Global safety limit (context window)
        if estimated_tokens > MAX_TOKENS:
            return FileTranslationResult(
                file_path=file_path,
                original_content=original_content,
                translated_content="",
                mode=mode,
                success=False,
                error=f"File too large: ~{estimated_tokens} tokens (global max {MAX_TOKENS})",
            )

        original_lines = len(original_content.splitlines())

        # Build mode description for prompt
        mode_desc = "comment_only: Only translate Chinese in comments"
        if mode == TranslationMode.FULL:
            mode_desc = "full: Translate ALL Chinese text including comments, log strings, string literals, UI text"

        prompt = build_prompt_with_terminology(
            prompt_type="whole_file",
            file_type=file_path.suffix.lstrip(".") or "code",
            mode_description=mode_desc,
            file_name=file_path.name,
            original_code=content_for_translation,
            additional_instructions=f"TOTAL LINES: {original_lines}",
        )

        logger.log_api_request(
            base_url=self.base_url,
            model=self.model,
            file_name=file_path.name,
            comment_count=original_lines,
        )

        import time
        start_time = time.perf_counter()

        semaphore = self._get_semaphore()

        async with semaphore:
            try:
                client = self._get_client()
                # DeepSeek API default max_tokens=4096, must set explicitly
                # deepseek-chat: max 8K output; deepseek-reasoner: max 64K output
                max_output_tokens = self._calculate_max_output_tokens(estimated_tokens)

                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    stream=False,
                    max_tokens=max_output_tokens,
                )

                duration_ms = (time.perf_counter() - start_time) * 1000

                raw_content = response.choices[0].message.content or ""
                translated_content = self._clean_llm_response(raw_content)
                translated_lines = len(translated_content.splitlines())

                # Check for truncation marker
                if "INCOMPLETE" in translated_content:
                    error_msg = "Translation truncated (INCOMPLETE marker found)"
                    logger.log_api_response(
                        file_name=file_path.name,
                        success_count=0,
                        fail_count=1,
                        duration_ms=duration_ms,
                    )
                    return FileTranslationResult(
                        file_path=file_path,
                        original_content=original_content,
                        translated_content="",
                        mode=mode,
                        success=False,
                        error=error_msg,
                    )

                # Check line count integrity (reject if >10% missing)
                line_diff_ratio = abs(original_lines - translated_lines) / max(original_lines, 1)
                if line_diff_ratio > 0.10:
                    error_msg = f"Translation incomplete: {original_lines} -> {translated_lines} lines ({line_diff_ratio:.1%} missing)"
                    logger.log_api_response(
                        file_name=file_path.name,
                        success_count=0,
                        fail_count=1,
                        duration_ms=duration_ms,
                    )
                    return FileTranslationResult(
                        file_path=file_path,
                        original_content=original_content,
                        translated_content=translated_content,
                        mode=mode,
                        success=False,
                        error=error_msg,
                    )

                logger.log_api_response(
                    file_name=file_path.name,
                    success_count=1,
                    fail_count=0,
                    duration_ms=duration_ms,
                )
                logger.log_from_api_response(
                    original_text=original_content[:50],
                    translated_text=translated_content[:50],
                    duration_ms=duration_ms,
                    api_response=response,
                )
                logger.log_parse_result(translated_lines, "whole-file translation")

                if original_lines != translated_lines:
                    logger.warning(
                        f"[{logger.utc_now_iso()}] [WARNING] Line mismatch: {original_lines} -> {translated_lines}"
                    )

                return FileTranslationResult(
                    file_path=file_path,
                    original_content=original_content,
                    translated_content=translated_content,
                    mode=mode,
                    success=True,
                )

            except RateLimitError as e:
                error_msg = f"Rate limit: {e}"
                logger.error(error_msg)
                return FileTranslationResult(
                    file_path=file_path,
                    original_content=original_content,
                    translated_content="",
                    mode=mode,
                    success=False,
                    error=error_msg,
                )

            except APIConnectionError as e:
                error_msg = f"Connection error: {e}"
                logger.error(error_msg)
                return FileTranslationResult(
                    file_path=file_path,
                    original_content=original_content,
                    translated_content="",
                    mode=mode,
                    success=False,
                    error=error_msg,
                )

            except APIError as e:
                error_msg = f"API error: {e}"
                logger.error(error_msg)
                return FileTranslationResult(
                    file_path=file_path,
                    original_content=original_content,
                    translated_content="",
                    mode=mode,
                    success=False,
                    error=error_msg,
                )

            except Exception as e:
                error_msg = str(e)
                logger.error(error_msg)
                return FileTranslationResult(
                    file_path=file_path,
                    original_content=original_content,
                    translated_content="",
                    mode=mode,
                    success=False,
                    error=error_msg,
                )

    def _clean_llm_response(self, raw_content: str) -> str:
        """Clean LLM response - remove markdown blocks and preamble."""
        content = raw_content.strip()

        if content.startswith("```"):
            content = re.sub(r"^```(?:\w+)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)

        preamble_patterns = [
            r"^Here's the translated[^:]*:\s*\n",
            r"^Here is the translated[^:]*:\s*\n",
            r"^The translation[^:]*:\s*\n",
            r"^Below is the translated[^:]*:\s*\n",
        ]
        for pattern in preamble_patterns:
            content = re.sub(pattern, "", content, flags=re.IGNORECASE)

        return content.strip()

    def apply_translation(
        self,
        result: FileTranslationResult,
        backup_dir: Path | None = None,
        relative_root: Path | None = None,
        strict_line_count: bool = False,
    ) -> bool:
        """Apply translation result to the original file with backup.

        Args:
            result: Translation result to apply
            backup_dir: Directory for backups (None = no backup)
            relative_root: Root path for calculating relative backup path
            strict_line_count: If True, reject when line counts mismatch

        Returns:
            True if successful, False otherwise
        """
        logger = get_logger()

        if not result.success:
            logger.error("Translation was not successful")
            return False

        if not result.translated_content:
            logger.error("No translated content")
            return False

        original_lines = len(result.original_content.splitlines())
        translated_lines = len(result.translated_content.splitlines())

        if strict_line_count and original_lines != translated_lines:
            logger.error(
                f"Line count mismatch, aborting (strict mode): {original_lines} vs {translated_lines}"
            )
            return False

        if original_lines != translated_lines:
            logger.warning(
                f"Line mismatch: {original_lines} vs {translated_lines}"
            )

        if backup_dir and relative_root:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rel_path = result.file_path.relative_to(relative_root)
            backup_path = backup_dir / timestamp / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_text(result.original_content, encoding="utf-8")
            logger.info(f"Backup saved: {backup_path}")

        result.file_path.write_text(result.translated_content, encoding="utf-8")
        return True
