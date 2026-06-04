"""B站 API 客户端 —— 基于 bilibili-api-python 库，提供限流和重试。

所有对外 API 调用都通过此模块进行。
"""

import asyncio
import time
from typing import Any

from loguru import logger

from app.config import settings
from app.crawler.rate_limiter import RateLimiter

# 直接使用 bilibili-api-python 库处理 WBI 签名和 API 调用
# 此模块提供限流和重试等横切关注点

# ── 限流器 ────────────────────────────────────────────────
_rate_limiter = RateLimiter(
    rate=settings.rate_limit_per_second,
    burst=settings.rate_limit_burst,
)


async def rate_limit() -> None:
    """获取请求许可（限流）。"""
    await _rate_limiter.acquire()
