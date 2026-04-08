"""指令解析。"""
from __future__ import annotations

import shlex
from dataclasses import dataclass


@dataclass
class ParsedCommand:
    name: str
    args: list[str]
    raw: str


def parse_command(content: str, prefix: str = "/") -> ParsedCommand | None:
    """将一条消息文本解析为指令。解析失败返回 None。"""
    if not content:
        return None

    # 去掉可能存在的 @机器人 前缀（botpy 一般已处理，这里做兜底）
    text = content.strip()
    if text.startswith("<@"):
        idx = text.find(">")
        if idx != -1:
            text = text[idx + 1 :].strip()

    if not text.startswith(prefix):
        return None

    body = text[len(prefix) :].strip()
    if not body:
        return None

    try:
        tokens = shlex.split(body)
    except ValueError:
        tokens = body.split()

    if not tokens:
        return None

    return ParsedCommand(name=tokens[0].lower(), args=tokens[1:], raw=body)
