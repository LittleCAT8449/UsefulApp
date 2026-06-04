"""UP主信息爬取 —— 基于 bilibili-api-python。"""

from bilibili_api.user import User

from app.crawler.bilibili_client import rate_limit


async def fetch_up_info(uid: int) -> dict:
    """获取 UP主基本信息。

    Returns:
        UP主信息字典（get_user_info 的返回结果）。
    """
    await rate_limit()
    u = User(uid)
    try:
        info: dict = await u.get_user_info()
        return info
    except Exception as e:
        from loguru import logger
        logger.error(f"获取 UP主信息失败 (uid={uid}): {e}")
        return {}


async def fetch_up_video_count(uid: int) -> int:
    """快速获取 UP主的视频投稿数。"""
    info = await fetch_up_info(uid)
    return info.get("video_count", 0)
