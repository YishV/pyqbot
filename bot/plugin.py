"""插件系统：基类、装饰器、加载器。"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any, Awaitable, Callable

from loguru import logger

CommandHandler = Callable[[Any, Any, list[str]], Awaitable[None]]
MessageHandler = Callable[[Any, Any], Awaitable[None]]


def on_command(name: str, help_text: str = "") -> Callable:
    """装饰器：把方法标记为指令处理器。"""
    def decorator(func: CommandHandler) -> CommandHandler:
        func.__pyqbot_command__ = {"name": name.lower(), "help": help_text}  # type: ignore[attr-defined]
        return func
    return decorator


def on_message() -> Callable:
    """装饰器：把方法标记为原始消息处理器（所有消息都会走一遍）。"""
    def decorator(func: MessageHandler) -> MessageHandler:
        func.__pyqbot_message__ = True  # type: ignore[attr-defined]
        return func
    return decorator


class Plugin:
    """插件基类。业务插件继承它，并用 @on_command / @on_message 注册回调。"""

    name: str = ""
    description: str = ""

    def __init__(self, bot: Any) -> None:
        self.bot = bot
        if not self.name:
            self.name = self.__class__.__name__

    async def on_load(self) -> None:
        """插件加载钩子。"""

    async def on_unload(self) -> None:
        """插件卸载钩子。"""


class PluginManager:
    def __init__(self, bot: Any, plugin_dir: str = "plugins", disabled: list[str] | None = None) -> None:
        self.bot = bot
        self.plugin_dir = plugin_dir
        self.disabled = set(disabled or [])
        self.plugins: list[Plugin] = []
        self.commands: dict[str, tuple[Plugin, CommandHandler, str]] = {}
        self.message_handlers: list[tuple[Plugin, MessageHandler]] = []

    def discover(self) -> None:
        """扫描插件目录，自动加载所有 Plugin 子类。"""
        root = Path(self.plugin_dir)
        if not root.exists():
            logger.warning(f"插件目录不存在: {root}")
            return

        package = self.plugin_dir.replace("/", ".")
        for mod_info in pkgutil.iter_modules([str(root)]):
            mod_name = mod_info.name
            if mod_name in self.disabled:
                logger.info(f"跳过已禁用插件: {mod_name}")
                continue
            full_name = f"{package}.{mod_name}"
            try:
                module = importlib.import_module(full_name)
            except Exception as exc:
                logger.exception(f"插件 {full_name} 加载失败: {exc}")
                continue

            for _, cls in inspect.getmembers(module, inspect.isclass):
                if cls is Plugin or not issubclass(cls, Plugin):
                    continue
                if cls.__module__ != module.__name__:
                    continue
                self._register(cls)

    def _register(self, cls: type[Plugin]) -> None:
        instance = cls(self.bot)
        self.plugins.append(instance)

        for _, member in inspect.getmembers(instance, inspect.iscoroutinefunction):
            meta = getattr(member, "__pyqbot_command__", None)
            if meta:
                cmd_name = meta["name"]
                if cmd_name in self.commands:
                    logger.warning(f"指令冲突 /{cmd_name}，已被 {instance.name} 覆盖")
                self.commands[cmd_name] = (instance, member, meta["help"])
            if getattr(member, "__pyqbot_message__", False):
                self.message_handlers.append((instance, member))

        logger.info(f"插件已注册: {instance.name}")

    async def load_all(self) -> None:
        for p in self.plugins:
            try:
                await p.on_load()
            except Exception as exc:
                logger.exception(f"插件 {p.name} on_load 异常: {exc}")
