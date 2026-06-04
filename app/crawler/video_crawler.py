"""视频爬取 —— 基于 bilibili-api-python。"""

from datetime import datetime
from typing import Any

from bilibili_api.user import User
from bilibili_api.video import Video

from app.crawler.bilibili_client import rate_limit


async def fetch_video_list(
    uid: int, page: int = 1, page_size: int = 50
) -> list[dict[str, Any]]:
    """获取 UP主的视频列表。

    Returns:
        视频列表，每个元素为视频摘要信息。
    """
    await rate_limit()
    try:
        u = User(uid)
        data: dict = await u.get_videos(ps=page_size, pn=page)
        vlist = data.get("list", {}).get("vlist", [])
        return vlist
    except Exception as e:
        from loguru import logger
        logger.error(f"获取视频列表失败 (uid={uid}, pn={page}): {e}")
        return []


async def fetch_video_detail(bvid: str) -> dict[str, Any]:
    """获取视频详细信息。"""
    await rate_limit()
    try:
        v = Video(bvid=bvid)
        info: dict = await v.get_info()
        return info
    except Exception as e:
        from loguru import logger
        logger.error(f"获取视频详情失败 (bvid={bvid}): {e}")
        return {}


async def fetch_video_playurl(
    bvid: str, cid: int, quality: int = 80
) -> dict[str, Any]:
    """获取视频播放地址（DASH 流）。"""
    await rate_limit()
    try:
        v = Video(bvid=bvid)
        url_data: dict = await v.get_download_url(cid=cid)
        return url_data
    except Exception as e:
        from loguru import logger
        logger.error(f"获取播放地址失败 (bvid={bvid}, cid={cid}): {e}")
        return {}


async def fetch_video_pagelist(bvid: str) -> list[dict[str, Any]]:
    """获取视频分P列表。"""
    await rate_limit()
    try:
        v = Video(bvid=bvid)
        pages: dict = await v.get_pages()
        # get_pages 返回 {'pages': [...]} 或直接返回 list
        if isinstance(pages, dict):
            return pages.get("pages", [])
        return pages if isinstance(pages, list) else []
    except Exception as e:
        from loguru import logger
        logger.error(f"获取分P列表失败 (bvid={bvid}): {e}")
        return []


def parse_video_list_item(item: dict) -> dict[str, Any]:
    """将 API 返回的视频列表项转换为数据库字段。"""
    return {
        "bvid": item.get("bvid", ""),
        "aid": item.get("aid"),
        "title": item.get("title", ""),
        "description": item.get("description", ""),
        "cover_url": item.get("pic", ""),
        "duration": _parse_duration(item.get("length", "0:00")),
        "view_count": item.get("play", 0),
        "danmaku_count": item.get("video_review", 0),
        "reply_count": item.get("comment", 0),
        "favorite_count": item.get("favorites", 0),
        "pubdate": datetime.fromtimestamp(item.get("created", 0)) if item.get("created") else None,
    }


def parse_video_detail(data: dict) -> dict[str, Any]:
    """将 API 返回的视频详情转换为数据库字段。"""
    stat = data.get("stat", {})
    return {
        "aid": data.get("aid"),
        "title": data.get("title", ""),
        "description": data.get("desc", ""),
        "cover_url": data.get("pic", ""),
        "duration": data.get("duration", 0),
        "view_count": stat.get("view", 0),
        "danmaku_count": stat.get("danmaku", 0),
        "reply_count": stat.get("reply", 0),
        "favorite_count": stat.get("favorite", 0),
        "coin_count": stat.get("coin", 0),
        "share_count": stat.get("share", 0),
        "like_count": stat.get("like", 0),
        "cid": data.get("cid"),
        "page_count": data.get("videos", 1),
        "pages": data.get("pages", []),
        "pubdate": datetime.fromtimestamp(data.get("pubdate", 0)) if data.get("pubdate") else None,
        "tags": _extract_tags(data),
    }


def _extract_tags(data: dict) -> list[str]:
    """从视频详情中提取标签。"""
    tags = []
    for tag_info in data.get("tag", []) or []:
        if isinstance(tag_info, dict):
            tags.append(tag_info.get("tag_name", ""))
        else:
            tags.append(str(tag_info))
    return tags


def _parse_duration(length_str: str) -> int:
    """解析时长字符串，如 '3:45' 或 '1:23:45'。"""
    parts = length_str.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0
