"""
File: comment_translator.py
Description: Incremental comment translation (extract -> translate -> replace)
Author: Arjun Li
Created: 2026-04-15
Last Modified: 2026-04-17
Related modules: models.py, whole_file_translator.py, comment_patterns.py, prompts/
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path

from openai import APIError, AsyncOpenAI

from src.comment_patterns import CommentType, extract_all_comments
from src.llm_client import LLMClientManager, LLMConfig
from src.models import replace_file_header_keys_in_line
from src.prompts import build_prompt_with_terminology
from src.solid_logger import get_logger


@dataclass
class CommentTranslationMatch:
    """A single comment match for translation."""
    line_no: int
    original_text: str
    language: str
    comment_type: CommentType
    comment_content: str


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

    MAX_TOKENS = 500

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-v4-flash",
        base_url: str = "https://api.deepseek.com",
        max_concurrent: int = 15,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self._llm_client: LLMClientManager | None = None
        self._semaphore: asyncio.Semaphore | None = None

    def _get_llm_client(self) -> LLMClientManager:
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
    ) -> list[CommentTranslationMatch]:
        """Extract all comments using universal patterns."""
        raw_matches = extract_all_comments(file_path)
        language = self.detect_language(file_path)

        matches = []
        for m in raw_matches:
            matches.append(CommentTranslationMatch(
                line_no=m.line_no,
                original_text=m.original_text,
                language=language,
                comment_type=m.comment_type,
                comment_content=m.comment_content,
            ))

        return matches

    def get_context_lines(
        self,
        file_path: Path,
        line_no: int,
        context_size: int = 3,
    ) -> str:
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
        comment: CommentTranslationMatch,
        file_path: Path,
    ) -> CommentTranslation:
        logger = get_logger()

        replaced_text = replace_file_header_keys_in_line(comment.original_text)
        comment_to_translate = CommentTranslationMatch(
            line_no=comment.line_no,
            original_text=replaced_text,
            language=comment.language,
            comment_type=comment.comment_type,
            comment_content=comment.comment_content,
        ) if replaced_text != comment.original_text else comment

        context = self.get_context_lines(file_path, comment_to_translate.line_no)

        prompt = build_prompt_with_terminology(
            prompt_type="comment",
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
                translated = (msg.content or "").strip()

                if comment.comment_type == CommentType.TRAILING_COMMENT:
                    translated = self._reconstruct_trailing_comment(
                        comment.original_text, translated
                    )
                else:
                    original_prefix = self._extract_comment_prefix(comment.original_text)
                    translated = self._clean_comment_prefix(translated, original_prefix)
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
        match = re.match(r"^\s*(///|//|#|\*)", line)
        if match:
            return match.group(1)
        return ""

    def _extract_indent(self, line: str) -> str:
        match = re.match(r"^(\s+)", line)
        if match:
            return match.group(0)
        return ""

    def _clean_comment_prefix(self, translated: str, original_prefix: str) -> str:
        content = translated.strip()

        prefix_patterns = [
            r"^///\s*",
            r"^//\s*",
            r"^#\s*",
            r"^\*\s*",
            r"^///\s*///\s*",
            r"^//\s*//\s*",
        ]

        for pattern in prefix_patterns:
            content = re.sub(pattern, "", content)

        return content.strip()

    def _reconstruct_trailing_comment(self, original: str, translated: str) -> str:
        """Reconstruct trailing comment: preserve code part, replace comment only.

        For lines like: `  | 'noCover'             // 无封面图标`
        We need to preserve `  | 'noCover'             ` and only replace `无封面图标`.
        """
        translated = translated.strip()

        pos = original.find("//")
        if pos == -1:
            return translated

        code_part = original[:pos]
        delimiter = "//"

        # Handle LLM returning full line vs just comment
        # Find // in translated output to extract comment content
        trans_comment_pos = translated.find("//")
        if trans_comment_pos != -1:
            # LLM returned full line, extract comment part after //
            comment_content = translated[trans_comment_pos + 2:].strip()
        elif translated.startswith("//"):
            # LLM returned // prefix + comment
            comment_content = translated[2:].strip()
        else:
            # LLM returned just the comment text
            comment_content = translated

        return code_part + delimiter + " " + comment_content

    async def translate_comments_batch(
        self,
        comments: list[CommentTranslationMatch],
        file_path: Path,
    ) -> list[CommentTranslation]:
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
        logger = get_logger()

        successful = [t for t in translations if t.success]
        if not successful:
            logger.warning("No successful translations to apply")
            return False

        content = file_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines(keepends=True)

        if backup_dir and relative_root:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rel_path = file_path.relative_to(relative_root)
            backup_path = backup_dir / timestamp / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_text(content, encoding="utf-8")
            logger.info(f"Backup saved: {backup_path}")

        for translation in successful:
            idx = translation.line_no - 1
            if idx < len(lines):
                line_ending = "\n" if lines[idx].endswith("\n") else ""
                lines[idx] = translation.translated_text + line_ending

        file_path.write_text("".join(lines), encoding="utf-8")
        logger.info(f"Applied {len(successful)} comment translations to {file_path.name}")
        return True


async def translate_file_comments(
    file_path: Path,
    api_key: str,
    model: str = "deepseek-v4-flash",
) -> tuple[list[CommentTranslationMatch], list[CommentTranslation]]:
    translator = CommentTranslator(api_key=api_key, model=model)

    comments = translator.extract_comments_with_chinese(file_path)
    if not comments:
        await translator.close()
        return [], []

    translations = await translator.translate_comments_batch(comments, file_path)
    await translator.close()

    return comments, translations
