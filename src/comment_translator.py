"""
File: comment_translator.py
Description: Incremental comment translation (extract -> translate -> replace)
Author: Arjun Li
Created: 2026-04-15
Last Modified: 2026-04-15
Related modules: models.py, whole_file_translator.py
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path

from openai import APIError, AsyncOpenAI

from src.llm_client import LLMClientManager, LLMConfig
from src.models import replace_file_header_keys_in_line
from src.solid_logger import get_logger

# Comment patterns for different languages
COMMENT_PATTERNS = {
    "rust": [
        r"^\s*///.*",  # Doc comment
        r"^\s*//.*",   # Single-line comment
    ],
    "python": [
        r"^\s*#.*",    # Single-line comment
    ],
    "default": [
        r"^\s*//.*",
        r"^\s*#.*",
        r"^\s*///.*",
    ],
}

# Chinese character detection pattern
CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]+")

# Translation prompt template
COMMENT_TRANSLATION_PROMPT = """Translate the Chinese text in the following code comment to English.

RULES:
1. Output ONLY the translated comment line, no explanations
2. Keep the comment prefix (//, #, ///) exactly as-is
3. Preserve the original indentation
4. Technical terms stay in English (API, TOML, Steam, JSON, etc.)
5. Keep the comment concise and developer-friendly

ORIGINAL COMMENT (line {line_no}):
{original_comment}

CONTEXT (surrounding lines):
{context}

TRANSLATED COMMENT:"""


@dataclass
class CommentMatch:
    """A single comment containing Chinese text."""
    line_no: int
    original_text: str
    language: str


@dataclass
class CommentTranslation:
    """Result of translating a single comment."""
    line_no: int
    original_text: str
    translated_text: str
    success: bool
    error: str | None = None


class CommentTranslator:
    """Incremental comment translation: extract, translate, replace."""

    MAX_TOKENS = 500  # Max output tokens for comment translation

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
        max_concurrent: int = 15,  # Increased from 5 to 15 for better throughput
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.max_concurrent = max_concurrent
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
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self._semaphore

    async def close(self) -> None:
        if self._llm_client:
            await self._llm_client.close()
            self._llm_client = None

    def detect_language(self, file_path: Path) -> str:
        """Detect language from file extension."""
        ext = file_path.suffix.lower()
        lang_map = {
            ".rs": "rust",
            ".py": "python",
            ".ts": "default",
            ".tsx": "default",
            ".js": "default",
            ".jsx": "default",
            ".go": "default",
            ".java": "default",
            ".c": "default",
            ".cpp": "default",
            ".h": "default",
        }
        return lang_map.get(ext, "default")

    def extract_comments_with_chinese(
        self,
        file_path: Path,
    ) -> list[CommentMatch]:
        """Extract all comments containing Chinese text."""
        language = self.detect_language(file_path)
        patterns = COMMENT_PATTERNS.get(language, COMMENT_PATTERNS["default"])
        combined_pattern = re.compile("|".join(patterns))

        content = file_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines(keepends=True)

        matches = []
        for i, line in enumerate(lines, start=1):
            if combined_pattern.match(line) and CHINESE_PATTERN.search(line):
                matches.append(CommentMatch(
                    line_no=i,
                    original_text=line.rstrip("\n\r"),
                    language=language,
                ))

        return matches

    def get_context_lines(
        self,
        file_path: Path,
        line_no: int,
        context_size: int = 3,
    ) -> str:
        """Get surrounding lines for context."""
        content = file_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()

        start = max(0, line_no - context_size - 1)
        end = min(len(lines), line_no + context_size)

        context_lines = []
        for i in range(start, end):
            marker = ">>>" if i == line_no - 1 else "   "
            context_lines.append(f"{marker} {i + 1}: {lines[i][:80]}")

        return "\n".join(context_lines)

    async def translate_single_comment(
        self,
        comment: CommentMatch,
        file_path: Path,
    ) -> CommentTranslation:
        """Translate a single comment with context."""
        logger = get_logger()

        # Priority: replace header key with cached translation
        replaced_text = replace_file_header_keys_in_line(comment.original_text)
        if replaced_text != comment.original_text:
            # Key replaced, value still needs LLM translation
            comment_to_translate = CommentMatch(
                line_no=comment.line_no,
                original_text=replaced_text,
                language=comment.language,
            )
        else:
            comment_to_translate = comment

        # Call API
        context = self.get_context_lines(file_path, comment_to_translate.line_no)

        prompt = COMMENT_TRANSLATION_PROMPT.format(
            line_no=comment_to_translate.line_no,
            original_comment=comment_to_translate.original_text,
            context=context,
        )

        semaphore = self._get_semaphore()

        async with semaphore:
            try:
                import time
                start_time = time.perf_counter()

                client = self._get_client()
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=self.MAX_TOKENS,
                    stream=False,
                )

                duration_ms = (time.perf_counter() - start_time) * 1000

                msg = response.choices[0].message
                translated = msg.content or ""
                translated = translated.strip()

                # Clean: remove any duplicate comment prefixes LLM might have added
                original_prefix = self._extract_comment_prefix(comment.original_text)
                translated = self._clean_comment_prefix(translated, original_prefix)

                # Ensure correct prefix with original indentation
                original_indent = self._extract_indent(comment.original_text)
                translated = original_indent + original_prefix + " " + translated

                logger.log_from_api_response(
                    original_text=comment.original_text,
                    translated_text=translated,
                    duration_ms=duration_ms,
                    api_response=response,
                )

                return CommentTranslation(
                    line_no=comment.line_no,
                    original_text=comment.original_text,
                    translated_text=translated,
                    success=True,
                )

            except APIError as e:
                logger.error(f"API error at line {comment.line_no}: {e}")
                return CommentTranslation(
                    line_no=comment.line_no,
                    original_text=comment.original_text,
                    translated_text="",
                    success=False,
                    error=str(e),
                )

            except Exception as e:
                logger.error(f"Error at line {comment.line_no}: {e}")
                return CommentTranslation(
                    line_no=comment.line_no,
                    original_text=comment.original_text,
                    translated_text="",
                    success=False,
                    error=str(e),
                )

    def _extract_comment_prefix(self, line: str) -> str:
        """Extract the comment prefix (//, #, ///) without indentation."""
        # Skip leading whitespace, then capture prefix
        match = re.match(r"^\s*(///|//|#)", line)
        if match:
            return match.group(1)  # Prefix only, excluding indent
        return ""

    def _extract_indent(self, line: str) -> str:
        """Extract the indentation (leading whitespace) from a line."""
        match = re.match(r"^(\s+)", line)
        if match:
            return match.group(0)
        return ""

    def _clean_comment_prefix(self, translated: str, original_prefix: str) -> str:
        """Remove any comment prefixes LLM might have added, return clean content."""
        # Remove leading whitespace
        content = translated.strip()

        # Remove any comment prefixes that might be present
        # Common patterns: ///, //, #, possibly duplicated
        prefix_patterns = [
            r"^///\s*",      # Rust doc comment
            r"^//\s*",       # Single-line comment
            r"^#\s*",        # Python comment
            r"^///\s*///\s*",  # Double doc comment (LLM mistake)
            r"^//\s*//\s*",    # Double comment (LLM mistake)
        ]

        for pattern in prefix_patterns:
            content = re.sub(pattern, "", content)

        return content.strip()

    async def translate_comments_batch(
        self,
        comments: list[CommentMatch],
        file_path: Path,
    ) -> list[CommentTranslation]:
        """Translate multiple comments concurrently."""
        tasks = [
            self.translate_single_comment(comment, file_path)
            for comment in comments
        ]
        results = await asyncio.gather(*tasks)
        return list(results)

    def apply_replacements(
        self,
        file_path: Path,
        translations: list[CommentTranslation],
        backup_dir: Path | None = None,
        relative_root: Path | None = None,
    ) -> bool:
        """Apply comment replacements to the file."""
        logger = get_logger()

        # Filter successful translations only
        successful = [t for t in translations if t.success]
        if not successful:
            logger.warning("No successful translations to apply")
            return False

        content = file_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines(keepends=True)

        # Backup before modification
        if backup_dir and relative_root:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rel_path = file_path.relative_to(relative_root)
            backup_path = backup_dir / timestamp / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_text(content, encoding="utf-8")
            logger.info(f"Backup saved: {backup_path}")

        # Apply replacements
        for translation in successful:
            idx = translation.line_no - 1
            if idx < len(lines):
                line_ending = "\n" if lines[idx].endswith("\n") else ""
                lines[idx] = translation.translated_text + line_ending

        # Write back
        file_path.write_text("".join(lines), encoding="utf-8")
        logger.info(
            f"Applied {len(successful)} comment translations to {file_path.name}"
        )
        return True


async def translate_file_comments(
    file_path: Path,
    api_key: str,
    model: str = "deepseek-chat",
) -> tuple[list[CommentMatch], list[CommentTranslation]]:
    """High-level function: extract and translate comments from a file.

    Returns:
        Tuple of (extracted comments, translation results)
    """
    translator = CommentTranslator(api_key=api_key, model=model)

    comments = translator.extract_comments_with_chinese(file_path)
    if not comments:
        await translator.close()
        return [], []

    translations = await translator.translate_comments_batch(comments, file_path)
    await translator.close()

    return comments, translations
