"""Anthropic Claude provider。"""
from __future__ import annotations

import httpx

from .base import BaseProvider, ChatMessage, ChatResult, LLMError


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None = None,
    ) -> ChatResult:
        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [m.to_dict() for m in messages if m.role != "system"],
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise LLMError(f"网络错误: {exc}") from exc

        if resp.status_code != 200:
            raise LLMError(f"Anthropic API 错误 {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        blocks = data.get("content", [])
        texts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
        text = "".join(texts).strip()
        if not text:
            raise LLMError("Anthropic 返回了空内容")

        usage = data.get("usage", {}) or {}
        return ChatResult(
            text=text,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
        )
