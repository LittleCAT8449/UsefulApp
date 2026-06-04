"""令牌桶限流器。"""

import asyncio
import time


class RateLimiter:
    """异步令牌桶算法实现。"""

    def __init__(self, rate: float, burst: int | None = None) -> None:
        """
        Args:
            rate: 每秒允许的请求数。
            burst: 突发容量，默认等于 rate。
        """
        self.rate = rate
        self.burst = burst or int(rate)
        self._tokens = float(self.burst)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """获取一个令牌，若无可用令牌则等待。"""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
            self._last_refill = now

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return

            # 需要等待
            wait_time = (1.0 - self._tokens) / self.rate
            self._tokens = 0.0

        await asyncio.sleep(wait_time)
        # 等待后重新记录时间
        self._last_refill = time.monotonic()

    async def __aenter__(self) -> None:
        await self.acquire()

    async def __aexit__(self, *args: object) -> None:
        pass
