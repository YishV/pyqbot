"""日志初始化。"""
from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from .config import BotConfig


def setup_logger(config: BotConfig) -> None:
    level = config.get("log.level", "INFO")
    log_dir = Path(config.get("log.dir", "logs"))
    rotation = config.get("log.rotation", "00:00")
    retention = config.get("log.retention", "14 days")

    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}:{line}</cyan> - <level>{message}</level>",
    )
    logger.add(
        log_dir / "pyqbot_{time:YYYY-MM-DD}.log",
        level=level,
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        enqueue=True,
    )

    # 互动日志：只记录用户↔机器人的对话流水，独立成文件、固定 INFO 级别，
    # 通过 logger.bind(chat=True).info(...) 触发。
    logger.add(
        log_dir / "chat_{time:YYYY-MM-DD}.log",
        level="INFO",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        enqueue=True,
        filter=lambda record: record["extra"].get("chat") is True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
    )

    logger.info(f"日志系统初始化完成 level={level} dir={log_dir}")
