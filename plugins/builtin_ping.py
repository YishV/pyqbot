"""内置 /ping 指令。"""
from __future__ import annotations

from bot import Plugin, on_command


class PingPlugin(Plugin):
    name = "ping"
    description = "存活检测"

    @on_command("ping", help_text="测试机器人是否在线")
    async def handle_ping(self, message, args: list[str]) -> None:
        await self.bot.reply(message, "pong 🏓")
