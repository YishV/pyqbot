"""内置 /help 指令：列出所有已注册指令。"""
from __future__ import annotations

from bot import Plugin, on_command


class HelpPlugin(Plugin):
    name = "help"
    description = "查看指令列表"

    @on_command("help", help_text="查看所有可用指令")
    async def handle_help(self, message, args: list[str]) -> None:
        prefix = self.bot.config.get("bot.command_prefix", "/")
        lines = ["📖 指令列表："]
        for cmd_name, (_plugin, _handler, help_text) in sorted(
            self.bot.plugins.commands.items()
        ):
            lines.append(f"  {prefix}{cmd_name} — {help_text or '(无说明)'}")
        await self.bot.reply(message, "\n".join(lines))


class AboutPlugin(Plugin):
    name = "about"
    description = "关于机器人"

    @on_command("about", help_text="查看机器人信息")
    async def handle_about(self, message, args: list[str]) -> None:
        name = self.bot.config.get("bot.name", "pyqbot")
        await self.bot.reply(
            message,
            f"🤖 {name}\n基于 qq-botpy 的插件化机器人\nhttps://bot.q.qq.com/wiki/develop/pythonsdk/",
        )
