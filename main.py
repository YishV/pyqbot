"""程序入口。"""
from __future__ import annotations

import sys

from loguru import logger

from bot import PyQBot
from bot.config import load_config
from bot.logger import setup_logger


def main() -> None:
    try:
        config = load_config("config/config.yaml")
    except (FileNotFoundError, ValueError) as exc:
        print(f"[启动失败] {exc}", file=sys.stderr)
        sys.exit(1)

    setup_logger(config)
    logger.info("==== pyqbot 启动 ====")

    bot = PyQBot(config)
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("收到 Ctrl+C，机器人退出")
    except Exception as exc:
        logger.exception(f"机器人异常退出: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
