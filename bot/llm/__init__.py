"""LLM 抽象层：支持多 provider 切换。"""
from .base import BaseProvider, ChatMessage, ChatResult, LLMError
from .factory import build_provider

__all__ = ["BaseProvider", "ChatMessage", "ChatResult", "LLMError", "build_provider"]
