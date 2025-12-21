"""LLM client factory with concurrency limits."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

import dspy
from loguru import logger


class LLMClientFactory:
    """Create DSPy LM clients with uniform configuration and request pooling."""

    def __init__(self, max_concurrent_requests: int = 4) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._clients: Dict[str, dspy.LM] = {}

    def _cache_key(self, llm_config: Dict[str, Any]) -> str:
        provider = (llm_config.get("provider") or "").lower()
        return "|".join(
            [
                provider,
                (llm_config.get("model") or "").lower(),
                (llm_config.get("api_key") or ""),
                str(llm_config.get("temperature", "")),
                str(llm_config.get("max_tokens", "")),
                (llm_config.get("location") or ""),
                (llm_config.get("base_url") or ""),
            ]
        )

    def create_client(self, llm_config: Dict[str, Any]) -> dspy.LM:
        key = self._cache_key(llm_config)
        if key in self._clients:
            return self._clients[key]

        provider = llm_config.get("provider")
        model = llm_config.get("model")
        api_key = llm_config.get("api_key")
        temperature = llm_config.get("temperature", 0.15)
        max_tokens = llm_config.get("max_tokens", 4000)

        if provider is None or api_key is None:
            raise ValueError("LLM provider and api_key must be configured")

        provider = provider.lower()
        model_name = model or ""

        if provider == "deepseek":
            client = dspy.LM(
                f"deepseek/{model_name}" if model_name else "deepseek/deepseek-chat",
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif provider == "qwen":
            location = llm_config.get("location", "china").lower()
            if location == "china":
                api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            else:
                api_base = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
            model_name = model_name or "qwen-max"
            client = dspy.LM(
                f"dashscope/{model_name}",
                api_base=api_base,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif provider == "anthropic":
            client = dspy.LM(
                f"anthropic/{model_name}" if model_name else "anthropic/claude-sonnet-4.5",
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif provider == "xai":
            client = dspy.LM(
                f"xai/{model_name}" if model_name else "xai/grok-4",
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif provider == "google":
            client = dspy.LM(
                f"gemini/{model_name}" if model_name else "gemini/gemini-2.5-pro",
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif provider == "openai":
            client = dspy.LM(
                f"openai/{model_name}" if model_name else "openai/gpt-5",
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        elif provider == "custom":
            base_url = llm_config.get("base_url")
            if not base_url or not model_name:
                raise ValueError("Custom provider requires model and base_url")
            client = dspy.LM(
                model=model_name,
                api_base=base_url,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        logger.info("Initialized LLM client for provider '%s' model '%s'", provider, model_name)
        self._clients[key] = client
        return client

    @asynccontextmanager
    async def request_slot(self, provider: Optional[str] = None) -> AsyncIterator[None]:
        """Throttle concurrent LLM requests."""
        label = provider or "llm"
        logger.debug("Waiting for LLM slot (%s)", label)
        await self._semaphore.acquire()
        try:
            yield
        finally:
            self._semaphore.release()
            logger.debug("Released LLM slot (%s)", label)
