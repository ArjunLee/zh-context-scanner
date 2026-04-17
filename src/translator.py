"""
File: translator.py
Description: DeepSeek translation client with async, batch and caching support
Author: Arjun Li
Created: 2026-04-15
Last Modified: 2026-04-17
Related modules: prompts/, models.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import httpx

from src.models import ScanMatch, TranslationResult
from src.prompts import build_prompt_with_terminology
from src.solid_logger import get_logger


@dataclass
class TranslationCache:
    """Simple in-memory translation cache."""
    cache: dict[str, str] = field(default_factory=dict)

    def get(self, text: str) -> str | None:
        """Get cached translation."""
        return self.cache.get(text)

    def set(self, text: str, translation: str) -> None:
        """Set cached translation."""
        self.cache[text] = translation

    def contains(self, text: str) -> bool:
        """Check if translation is cached."""
        return text in self.cache


# Global cache instance
TRANSLATION_CACHE = TranslationCache()


class Translator:
    """DeepSeek API translation client."""

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.deepseek.com/chat/completions",  # Legacy: use llm_client.py instead
        model: str = "deepseek-chat",
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def translate_single(
        self,
        chinese_text: str,
        line_content: str,
    ) -> TranslationResult:
        """Translate a single Chinese text."""
        cached = TRANSLATION_CACHE.get(chinese_text)
        if cached:
            return TranslationResult(original=chinese_text, translated=cached, cached=True)

        prompt = build_prompt_with_terminology(
            prompt_type="single",
            line_content=line_content,
            chinese_text=chinese_text,
        )

        client = await self._get_client()
        response = await client.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
        )
        response.raise_for_status()
        result = response.json()
        translated = result["choices"][0]["message"]["content"].strip()

        TRANSLATION_CACHE.set(chinese_text, translated)
        return TranslationResult(original=chinese_text, translated=translated, cached=False)

    async def translate_batch(
        self,
        texts: list[str],
    ) -> dict[str, str]:
        """Translate multiple texts in a single API call."""
        logger = get_logger()
        texts_json = json.dumps(texts, ensure_ascii=False)
        prompt = build_prompt_with_terminology(prompt_type="batch", texts_json=texts_json)

        logger.log_api_request(
            base_url=self.api_url.replace("/chat/completions", ""),
            model=self.model,
            file_name="batch_translate",
            comment_count=len(texts),
        )

        import time
        start_time = time.perf_counter()

        client = await self._get_client()
        response = await client.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.log_api_response(
            file_name="batch_translate",
            success_count=len(texts),
            fail_count=0,
            duration_ms=duration_ms,
        )

        try:
            translations = json.loads(content)
            logger.log_parse_result(len(translations), repr(list(translations.items())[:3]))
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    translations = json.loads(content[start:end])
                    logger.log_parse_result(len(translations), repr(list(translations.items())[:3]))
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON from API response")
                    logger.debug(f"Raw content: {content[:500]}")
                    translations = {}
            else:
                logger.error("No JSON object found in API response")
                logger.debug(f"Raw content: {content[:500]}")
                translations = {}

        for text, translated in translations.items():
            TRANSLATION_CACHE.set(text, translated)

        return translations

    async def translate_file_matches(
        self,
        matches: list[ScanMatch],
    ) -> dict[str, str]:
        """Translate all matches from a file.

        Returns mapping of original text -> translated text.
        """
        unique_texts = list(set(m.matched_text for m in matches if not m.warning))

        # Check cache first
        uncached = [t for t in unique_texts if not TRANSLATION_CACHE.contains(t)]
        cached_translations = {
            t: TRANSLATION_CACHE.get(t)
            for t in unique_texts
            if TRANSLATION_CACHE.contains(t)
        }

        if uncached:
            batch_result = await self.translate_batch(uncached)
            return {**cached_translations, **batch_result}

        return cached_translations


async def test_translation(api_key: str) -> bool:
    """Test if translation API is working."""
    translator = Translator(api_key)
    try:
        result = await translator.translate_single("测试", "# 测试")
        await translator.close()
        return bool(result.translated)
    except Exception:
        await translator.close()
        return False
