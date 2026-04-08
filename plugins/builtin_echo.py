"""内置 /echo 指令。"""
from __future__ import annotations

from bot import Plugin, on_command


class EchoPlugin(Plugin):
    name = "echo"
    description = "复读机"

    @on_command("echo", help_text="复读你说的话，用法: /echo <内容>")
    async def handle_echo(self, message, args: list[str]) -> None:
        if not args:
            await self.bot.reply(message, "用法: /echo <内容>")
            return
        await self.bot.reply(message, " ".join(args))
