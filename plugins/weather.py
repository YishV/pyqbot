"""天气查询插件：默认走 wttr.in（免费免 Key，支持中文城市）。

用法: /weather <城市>
例如: /weather 北京
      /weather 上海
      /weather tokyo
"""
from __future__ import annotations

from urllib.parse import quote

import httpx
from loguru import logger

from bot import Plugin, on_command


class WeatherPlugin(Plugin):
    name = "weather"
    description = "查询天气"

    def __init__(self, bot) -> None:
        super().__init__(bot)
        cfg = bot.config.get("weather", {}) or {}
        self.enabled: bool = bool(cfg.get("enabled", True))
        self.provider: str = (cfg.get("provider") or "wttr").lower()
        self.timeout: float = float(cfg.get("timeout", 10))
        self.lang: str = cfg.get("lang", "zh-cn")

    @on_command("weather", help_text="查询城市天气，用法: /weather <城市>")
    async def handle_weather(self, message, args: list[str]) -> None:
        if not self.enabled:
            await self.bot.reply(message, "天气插件未启用")
            return
        if not args:
            await self.bot.reply(message, "用法: /weather <城市>\n例如: /weather 北京")
            return

        city = " ".join(args).strip()
        try:
            text = await self._query(city)
        except WeatherError as exc:
            await self.bot.reply(message, f"😿 查询天气失败: {exc}")
            return
        except Exception as exc:
            logger.exception(f"weather 异常: {exc}")
            await self.bot.reply(message, "😿 小桃打翻了天气盒子，再试一次嘛～")
            return

        await self.bot.reply(message, text)

    async def _query(self, city: str) -> str:
        if self.provider == "wttr":
            return await self._query_wttr(city)
        raise WeatherError(f"未知的天气 provider: {self.provider}")

    async def _query_wttr(self, city: str) -> str:
        # wttr.in 支持 URL path 传中文城市
        url = f"https://wttr.in/{quote(city)}"
        params = {"format": "j1", "lang": self.lang}
        headers = {"User-Agent": "pyqbot/1.0"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params, headers=headers)
        except httpx.HTTPError as exc:
            raise WeatherError(f"网络错误: {exc}") from exc

        if resp.status_code != 200:
            raise WeatherError(f"上游返回 {resp.status_code}")

        try:
            data = resp.json()
        except ValueError as exc:
            raise WeatherError("解析失败，城市名可能无效") from exc

        return self._format_wttr(city, data)

    @staticmethod
    def _format_wttr(city: str, data: dict) -> str:
        try:
            current = (data.get("current_condition") or [{}])[0]
            area = (data.get("nearest_area") or [{}])[0]
            weather_days = data.get("weather") or []
        except (AttributeError, IndexError) as exc:
            raise WeatherError("数据结构异常") from exc

        # 地点名（优先中文）
        area_name = city
        zh_area = area.get("areaName") or []
        if zh_area:
            area_name = zh_area[0].get("value", city)

        # 当前天气描述（中文字段 key：lang_zh-cn）
        desc_nodes = current.get("lang_zh-cn") or current.get("weatherDesc") or []
        desc = desc_nodes[0].get("value", "未知") if desc_nodes else "未知"

        temp_c = current.get("temp_C", "?")
        feels_c = current.get("FeelsLikeC", "?")
        humidity = current.get("humidity", "?")
        wind_kmph = current.get("windspeedKmph", "?")
        wind_dir = current.get("winddir16Point", "")

        lines = [
            f"🌤 {area_name} 当前天气",
            f"  天气: {desc}",
            f"  气温: {temp_c}°C（体感 {feels_c}°C）",
            f"  湿度: {humidity}%",
            f"  风速: {wind_dir} {wind_kmph} km/h",
        ]

        # 未来 2 天预报
        if len(weather_days) >= 2:
            lines.append("📅 未来预报")
            for day in weather_days[1:3]:
                date_str = day.get("date", "")
                max_c = day.get("maxtempC", "?")
                min_c = day.get("mintempC", "?")
                # 取中午那段的描述
                hours = day.get("hourly") or []
                noon_desc = "—"
                if hours:
                    mid = hours[len(hours) // 2]
                    nodes = mid.get("lang_zh-cn") or mid.get("weatherDesc") or []
                    if nodes:
                        noon_desc = nodes[0].get("value", "—")
                lines.append(f"  {date_str}: {noon_desc}  {min_c}~{max_c}°C")

        lines.append("\n数据源: wttr.in")
        return "\n".join(lines)


class WeatherError(Exception):
    """天气查询失败。"""
