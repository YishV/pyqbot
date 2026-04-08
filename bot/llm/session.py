"""会话上下文管理：多轮对话 + 过期淘汰 + 并发锁。"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from .base import ChatMessage


@dataclass
class Session:
    messages: list[ChatMessage] = field(default_factory=list)
    updated_at: float = field(default_factory=time.time)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class SessionStore:
    def __init__(self, max_turns: int = 10, ttl: int = 1800) -> None:
        self.max_turns = max_turns  # 一问一答 = 1 轮，实际消息数 = turns * 2
        self.ttl = ttl
        self._sessions: dict[str, Session] = {}

    def _key(self, scope_id: str, user_id: str) -> str:
        return f"{scope_id}::{user_id}"

    def get(self, scope_id: str, user_id: str) -> Session:
        key = self._key(scope_id, user_id)
        sess = self._sessions.get(key)
        now = time.time()
        if sess is None or now - sess.updated_at > self.ttl:
            sess = Session()
            self._sessions[key] = sess
        return sess

    def append(self, session: Session, role: str, content: str) -> None:
        session.messages.append(ChatMessage(role=role, content=content))  # type: ignore[arg-type]
        session.updated_at = time.time()
        # 保留最近 max_turns 轮
        max_msgs = self.max_turns * 2
        if len(session.messages) > max_msgs:
            session.messages = session.messages[-max_msgs:]

    def reset(self, scope_id: str, user_id: str) -> bool:
        key = self._key(scope_id, user_id)
        return self._sessions.pop(key, None) is not None

    def cleanup_expired(self) -> int:
        now = time.time()
        expired = [k for k, s in self._sessions.items() if now - s.updated_at > self.ttl]
        for k in expired:
            self._sessions.pop(k, None)
        return len(expired)
