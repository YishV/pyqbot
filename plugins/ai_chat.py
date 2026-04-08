"""AI 对话插件：@机器人或 /chat 触发多轮对话，带每日 token 限流 & 元气少女人设。"""
from __future__ import annotations

import asyncio

from loguru import logger

from bot import Plugin, on_command, on_message
from bot.command import parse_command
from bot.llm import LLMError, build_provider
from bot.llm.rate_limiter import DailyTokenLimiter
from bot.llm.session import SessionStore


# QQ 单条消息字符上限（留点余量）
MAX_REPLY_LEN = 1800


def _chunk(text: str, size: int = MAX_REPLY_LEN) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


def _build_system_prompt(base_prompt: str, persona_name: str) -> str:
    header = f"你叫{persona_name}，是一个 QQ 机器人。\n"
    return header + (base_prompt or "").strip()


class AIChatPlugin(Plugin):
    name = "ai_chat"
    description = "基于 LLM 的多轮对话（带每日限流）"

    def __init__(self, bot) -> None:
        super().__init__(bot)
        self.llm_config: dict = bot.config.get("llm", {}) or {}
        self.enabled: bool = bool(self.llm_config.get("enabled", False))
        self.auto_reply: bool = bool(self.llm_config.get("auto_reply_on_at", True))
        self.timeout: float = float(self.llm_config.get("timeout", 30))
        self.persona_name: str = self.llm_config.get("persona_name") or "小桃"

        self.system_prompt = _build_system_prompt(
            self.llm_config.get("system_prompt") or "",
            self.persona_name,
        )

        sess_cfg = self.llm_config.get("session", {}) or {}
        self.sessions = SessionStore(
            max_turns=int(sess_cfg.get("max_turns", 10)),
            ttl=int(sess_cfg.get("ttl", 1800)),
        )

        rl_cfg = self.llm_config.get("rate_limit", {}) or {}
        self.limiter = DailyTokenLimiter(
            daily_limit=int(rl_cfg.get("daily_tokens", 0))
        )
        self.exhausted_message: str = (
            rl_cfg.get("exhausted_message")
            or f"呜呜~ 今天说了好多话，{self.persona_name}累啦，想休息一下下 (っ˘ω˘ς )"
        ).strip()

        self.provider = None
        if self.enabled:
            try:
                self.provider = build_provider(self.llm_config)
                logger.info(
                    f"AI 对话已启用 persona={self.persona_name} "
                    f"provider={self.provider.name} model={self.provider.model} "
                    f"daily_limit={self.limiter.daily_limit}"
                )
            except LLMError as exc:
                logger.error(f"AI 对话初始化失败: {exc}")
                self.enabled = False

    # ---------------- 指令 ----------------
    @on_command("chat", help_text="与 AI 对话，用法: /chat <内容>")
    async def handle_chat(self, message, args: list[str]) -> None:
        if not args:
            await self.bot.reply(message, "用法: /chat <内容>")
            return
        await self._do_chat(message, " ".join(args))

    @on_command("reset", help_text="清空你与 AI 的会话历史")
    async def handle_reset(self, message, args: list[str]) -> None:
        scope_id, user_id = self._ids(message)
        ok = self.sessions.reset(scope_id, user_id)
        await self.bot.reply(
            message,
            f"✅ 会话已清空，{self.persona_name}重新上线咯 (๑•̀ㅂ•́)و"
            if ok
            else "你当前没有会话哦",
        )

    @on_command("model", help_text="查看当前使用的 AI 模型")
    async def handle_model(self, message, args: list[str]) -> None:
        if not self.enabled or self.provider is None:
            await self.bot.reply(message, "AI 对话未启用")
            return
        await self.bot.reply(
            message,
            f"当前模型: {self.provider.name} / {self.provider.model}",
        )

    @on_command("usage", help_text="查看今日 Token 使用情况")
    async def handle_usage(self, message, args: list[str]) -> None:
        if not self.limiter.enabled:
            await self.bot.reply(message, "今日 Token 限流未开启，无限畅聊～")
            return
        used = self.limiter.used
        total = self.limiter.daily_limit
        remain = self.limiter.remaining
        pct = (used / total * 100) if total else 0
        await self.bot.reply(
            message,
            f"📊 今日 Token 使用情况\n"
            f"已用: {used} / {total} ({pct:.1f}%)\n"
            f"剩余: {remain}",
        )

    # ---------------- 消息钩子：@机器人自动触发 ----------------
    @on_message()
    async def handle_at_message(self, message) -> None:
        if not self.enabled or not self.auto_reply:
            return
        content = (getattr(message, "content", "") or "").strip()
        if not content:
            return

        # 如果是指令就不走 AI，交给指令分发器
        prefix = self.bot.config.get("bot.command_prefix", "/")
        if parse_command(content, prefix=prefix) is not None:
            return

        # 去掉 @机器人 的 mention 前缀
        text = content
        if text.startswith("<@"):
            idx = text.find(">")
            if idx != -1:
                text = text[idx + 1 :].strip()
        if not text:
            return

        await self._do_chat(message, text)

    # ---------------- 核心调用 ----------------
    async def _do_chat(self, message, user_text: str) -> None:
        if not self.enabled or self.provider is None:
            await self.bot.reply(message, "AI 对话未启用或初始化失败")
            return

        # 限流前置检查
        if not self.limiter.check():
            logger.info(f"触发每日限流: used={self.limiter.used}")
            await self.bot.reply(message, self.exhausted_message)
            return

        scope_id, user_id = self._ids(message)
        session = self.sessions.get(scope_id, user_id)

        # 同一用户串行，避免上下文错乱
        async with session.lock:
            self.sessions.append(session, "user", user_text)
            try:
                result = await asyncio.wait_for(
                    self.provider.chat(
                        messages=session.messages,
                        system=self.system_prompt or None,
                    ),
                    timeout=self.timeout + 2,
                )
            except asyncio.TimeoutError:
                session.messages.pop()
                logger.warning("LLM 调用超时")
                await self.bot.reply(message, "⏰ 呜～小桃想太久啦，请再问我一次嘛")
                return
            except LLMError as exc:
                session.messages.pop()
                logger.exception(f"LLM 调用失败: {exc}")
                await self.bot.reply(message, f"❌ AI 调用失败: {exc}")
                return
            except Exception as exc:
                session.messages.pop()
                logger.exception(f"LLM 未知异常: {exc}")
                await self.bot.reply(message, "❌ 出了点小问题，待会儿再试试嘛")
                return

            # 记录用量 & 会话
            self.limiter.add(result.total_tokens)
            self.sessions.append(session, "assistant", result.text)
            logger.debug(
                f"LLM 用量: in={result.input_tokens} out={result.output_tokens} "
                f"today_used={self.limiter.used}"
            )

        # 超长回复分段发送
        for chunk in _chunk(result.text):
            await self.bot.reply(message, chunk)

    # ---------------- 工具 ----------------
    @staticmethod
    def _ids(message) -> tuple[str, str]:
        """提取 (会话域id, 用户id)，尽量兼容频道/群/私信。"""
        scope = (
            getattr(message, "channel_id", None)
            or getattr(message, "group_openid", None)
            or getattr(message, "guild_id", None)
            or "dm"
        )
        author = getattr(message, "author", None)
        user_id = (
            getattr(author, "id", None)
            or getattr(author, "member_openid", None)
            or getattr(author, "user_openid", None)
            or "anonymous"
        )
        return str(scope), str(user_id)
