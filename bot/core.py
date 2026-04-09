"""Bot 主类：封装 botpy.Client，做事件分发。"""
from __future__ import annotations

import botpy
from botpy.message import C2CMessage, GroupMessage, Message
from loguru import logger

from .command import parse_command
from .config import BotConfig
from .plugin import PluginManager


class _InnerClient(botpy.Client):
    """botpy 的 Client 子类，把事件转发给 PyQBot。"""

    def __init__(self, outer: "PyQBot", intents: botpy.Intents, is_sandbox: bool = False) -> None:
        super().__init__(intents=intents, is_sandbox=is_sandbox)
        self.outer = outer

    async def on_ready(self) -> None:  # type: ignore[override]
        logger.info(f"机器人已上线: {self.robot.name}")

    async def on_at_message_create(self, message: Message) -> None:  # type: ignore[override]
        await self.outer.dispatch_message(message)

    async def on_group_at_message_create(self, message: GroupMessage) -> None:  # type: ignore[override]
        await self.outer.dispatch_message(message)

    async def on_c2c_message_create(self, message: C2CMessage) -> None:  # type: ignore[override]
        await self.outer.dispatch_message(message)

    async def on_direct_message_create(self, message: Message) -> None:  # type: ignore[override]
        await self.outer.dispatch_message(message)


class PyQBot:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.plugins = PluginManager(
            bot=self,
            plugin_dir=config.get("plugins.dir", "plugins"),
            disabled=config.get("plugins.disabled", []),
        )
        self._client: _InnerClient | None = None

    # ---------- 生命周期 ----------
    def run(self) -> None:
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        intents = self._build_intents()
        self.plugins.discover()

        is_sandbox = bool(self.config.get("bot.sandbox", False))
        self._client = _InnerClient(self, intents, is_sandbox=is_sandbox)
        logger.info(f"环境: {'沙箱' if is_sandbox else '正式'}")

        # 加载插件 on_load（在事件循环里执行）
        loop.run_until_complete(self.plugins.load_all())

        logger.info("开始连接 QQ 开放平台 ...")
        self._client.run(appid=self.config.app_id, secret=self.config.secret)

    # ---------- 事件分发 ----------
    async def dispatch_message(self, message: Message | GroupMessage | C2CMessage) -> None:
        content = getattr(message, "content", "") or ""
        logger.debug(f"收到消息: {content!r}")

        # 1. 通用消息钩子
        for plugin, handler in self.plugins.message_handlers:
            try:
                await handler(message)
            except Exception as exc:
                logger.exception(f"[{plugin.name}] on_message 异常: {exc}")

        # 2. 指令分发
        prefix = self.config.get("bot.command_prefix", "/")
        parsed = parse_command(content, prefix=prefix)
        if parsed is None:
            return

        entry = self.plugins.commands.get(parsed.name)
        if entry is None:
            logger.debug(f"未知指令: {parsed.name}")
            return

        plugin, handler, _help = entry
        try:
            # 同上：handler 是 bound method，不要再传 plugin
            await handler(message, parsed.args)
        except Exception as exc:
            logger.exception(f"[{plugin.name}] /{parsed.name} 执行异常: {exc}")
            await self.reply(message, f"指令执行出错: {exc}")

    # ---------- 工具方法 ----------
    async def reply(self, message: Message | GroupMessage | C2CMessage, content: str) -> None:
        """统一回复，兼容频道消息 & 群消息。"""
        try:
            if isinstance(message, GroupMessage):
                await message.reply(content=content)
            else:
                await message.reply(content=content)
        except Exception as exc:
            logger.exception(f"回复消息失败: {exc}")

    def _build_intents(self) -> botpy.Intents:
        cfg = self.config.get("intents", {}) or {}
        return botpy.Intents(**{k: bool(v) for k, v in cfg.items()})
