"""Token 每日限流器：按本地日期自动重置。"""
from __future__ import annotations

from datetime import date


class DailyTokenLimiter:
    """
    全局每日 token 配额。
    - daily_limit <= 0 表示不限流。
    - check() 判断当前是否还有额度（未超出即可继续请求）。
    - add(n) 累加实际消耗。
    - 日期切换时自动归零。
    """

    def __init__(self, daily_limit: int) -> None:
        self.daily_limit = int(daily_limit)
        self._date: date | None = None
        self._used: int = 0

    def _roll_if_new_day(self) -> None:
        today = date.today()
        if today != self._date:
            self._date = today
            self._used = 0

    @property
    def enabled(self) -> bool:
        return self.daily_limit > 0

    @property
    def used(self) -> int:
        self._roll_if_new_day()
        return self._used

    @property
    def remaining(self) -> int:
        if not self.enabled:
            return -1
        self._roll_if_new_day()
        return max(0, self.daily_limit - self._used)

    def check(self) -> bool:
        if not self.enabled:
            return True
        self._roll_if_new_day()
        return self._used < self.daily_limit

    def add(self, tokens: int) -> None:
        if tokens <= 0:
            return
        self._roll_if_new_day()
        self._used += int(tokens)
