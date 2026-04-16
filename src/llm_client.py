"""
File: llm_client.py
Description: Unified LLM client manager (supports multiple providers via OpenAI-compatible API)
Author: Arjun Li
Created: 2026-04-15
Last Modified: 2026-04-15
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """LLM configuration."""
    api_key: str
    base_url: str
    model: str
    max_concurrent: int = 5
    timeout: float = 30.0


class LLMClientManager:
    """Unified LLM client manager.
    
    Supports multiple providers via OpenAI-compatible API:
    - DeepSeek (default)
    - OpenAI
    - Alibaba Cloud Bailian (Qwen)
    - Moonshot (Kimi)
    - MiniMax
    - SiliconFlow
    - Azure OpenAI
    - Any other OpenAI-compatible service
    """
    
    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._client = None
    
    def _get_client(self):
        """Get or create OpenAI-compatible async client."""
        from openai import AsyncOpenAI
        
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
        return self._client
    
    async def close(self) -> None:
        """Close the client."""
        if self._client:
            await self._client.close()
            self._client = None
    
    @staticmethod
    def get_default_base_url() -> str:
        """Get default base URL (DeepSeek)."""
        return "https://api.deepseek.com"
    
    @staticmethod
    def get_default_model() -> str:
        """Get default model name (DeepSeek)."""
        return "deepseek-chat"


# Default configuration constants
DEFAULT_BASE_URL = LLMClientManager.get_default_base_url()
DEFAULT_MODEL = LLMClientManager.get_default_model()
