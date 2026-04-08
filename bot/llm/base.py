"""LLM provider 基类与通用类型。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


Role = Literal["system", "user", "assistant"]


@dataclass
class ChatMessage:
    role: Role
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class ChatResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class LLMError(Exception):
    """LLM 调用相关错误。"""


class BaseProvider(ABC):
    """所有 LLM provider 的基类。"""

    name: str = "base"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise LLMError(f"{self.name} provider 缺少 API Key")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens
        self.timeout = timeout

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None = None,
    ) -> ChatResult:
        """发起一次对话，返回模型回复 + token 用量。"""
