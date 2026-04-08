"""OpenAI 兼容协议 provider（DeepSeek / Kimi / 通义 / Ollama 等都可用）。"""
from __future__ import annotations

import httpx

from .base import BaseProvider, ChatMessage, ChatResult, LLMError


class OpenAIProvider(BaseProvider):
    name = "openai"

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None = None,
    ) -> ChatResult:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        msg_list: list[dict] = []
        if system:
            msg_list.append({"role": "system", "content": system})
        msg_list.extend(m.to_dict() for m in messages if m.role != "system")

        payload = {
            "model": self.model,
            "messages": msg_list,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise LLMError(f"网络错误: {exc}") from exc

        if resp.status_code != 200:
            raise LLMError(f"OpenAI API 错误 {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        try:
            text = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError) as exc:
            raise LLMError(f"OpenAI 响应结构异常: {exc}") from exc

        if not text:
            raise LLMError("OpenAI 返回了空内容")

        usage = data.get("usage", {}) or {}
        return ChatResult(
            text=text,
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
        )
