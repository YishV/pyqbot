"""配置加载模块。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass
class BotConfig:
    raw: dict[str, Any] = field(default_factory=dict)
    app_id: str = ""
    secret: str = ""

    def get(self, path: str, default: Any = None) -> Any:
        """支持点号路径取值，例如 cfg.get('bot.command_prefix')。"""
        node: Any = self.raw
        for key in path.split("."):
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node


def load_config(config_path: str | Path = "config/config.yaml") -> BotConfig:
    load_dotenv()

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(
            f"配置文件不存在: {path}，请先复制 config/config.example.yaml"
        )

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    app_id = os.getenv("QQ_BOT_APP_ID", "").strip()
    secret = os.getenv("QQ_BOT_SECRET", "").strip()
    if not app_id or not secret:
        raise ValueError("环境变量 QQ_BOT_APP_ID / QQ_BOT_SECRET 未配置")

    return BotConfig(raw=raw, app_id=app_id, secret=secret)
