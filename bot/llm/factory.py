"""根据配置构建 provider 实例。"""
from __future__ import annotations

import os

from .anthropic_provider import AnthropicProvider
from .base import BaseProvider, LLMError
from .openai_provider import OpenAIProvider


def build_provider(llm_config: dict) -> BaseProvider:
    name = (llm_config.get("provider") or "").lower()
    timeout = float(llm_config.get("timeout", 30))

    if name == "anthropic":
        cfg = llm_config.get("anthropic", {}) or {}
        return AnthropicProvider(
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            model=cfg.get("model", "claude-sonnet-4-6"),
            base_url=cfg.get("base_url", "https://api.anthropic.com"),
            max_tokens=int(cfg.get("max_tokens", 1024)),
            timeout=timeout,
        )

    if name == "openai":
        cfg = llm_config.get("openai", {}) or {}
        return OpenAIProvider(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=cfg.get("model", "gpt-4o-mini"),
            base_url=cfg.get("base_url", "https://api.openai.com/v1"),
            max_tokens=int(cfg.get("max_tokens", 1024)),
            timeout=timeout,
        )

    raise LLMError(f"未知的 LLM provider: {name}")
