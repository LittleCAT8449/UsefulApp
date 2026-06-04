"""专栏文章爬取 —— 基于 bilibili-api-python。"""

from datetime import datetime
from typing import Any

from bilibili_api.article import Article
from bilibili_api.user import User

from app.crawler.bilibili_client import rate_limit


async def fetch_article_list(
    uid: int, page: int = 1, page_size: int = 12
) -> list[dict[str, Any]]:
    """获取 UP主的专栏文章列表。"""
    await rate_limit()
    try:
        u = User(uid)
        data: dict = await u.get_articles(pn=page, ps=page_size)
        articles = data.get("articles", [])
        return articles
    except Exception as e:
        from loguru import logger
        logger.error(f"获取文章列表失败 (uid={uid}, pn={page}): {e}")
        return []


async def fetch_article_detail(cv_id: int) -> dict[str, Any]:
    """获取专栏文章详情。"""
    await rate_limit()
    try:
        a = Article(cvid=cv_id)
        info: dict = await a.get_info()
        return info
    except Exception as e:
        from loguru import logger
        logger.error(f"获取文章详情失败 (cv_id={cv_id}): {e}")
        return {}


def parse_article_list_item(item: dict) -> dict[str, Any]:
    """将 API 返回的文章列表项转换为数据库字段。"""
    stats = item.get("stats", {})
    return {
        "cv_id": item.get("id", 0),
        "title": item.get("title", ""),
        "summary": item.get("summary", ""),
        "cover_url": _get_article_cover(item),
        "view_count": stats.get("view", 0),
        "like_count": stats.get("like", 0),
        "coin_count": stats.get("coin", 0),
        "reply_count": stats.get("reply", 0),
        "favorite_count": stats.get("favorite", 0),
        "share_count": stats.get("share", 0),
        "words_count": item.get("words", 0),
        "pubdate": datetime.fromtimestamp(item.get("publish_time", 0)) if item.get("publish_time") else None,
    }


def parse_article_detail(data: dict) -> dict[str, Any]:
    """将 API 返回的文章详情转换为数据库字段。"""
    stat = data.get("stats", {})
    return {
        "title": data.get("title", ""),
        "summary": data.get("summary", ""),
        "cover_url": _get_article_cover(data),
        "content": data.get("content", ""),
        "view_count": stat.get("view", 0),
        "like_count": stat.get("like", 0),
        "coin_count": stat.get("coin", 0),
        "reply_count": stat.get("reply", 0),
        "favorite_count": stat.get("favorite", 0),
        "share_count": stat.get("share", 0),
        "words_count": data.get("words", 0),
        "pubdate": datetime.fromtimestamp(data.get("publish_time", 0)) if data.get("publish_time") else None,
    }


def _get_article_cover(item: dict) -> str:
    """提取文章封面 URL。"""
    image_urls = item.get("image_urls", [])
    if image_urls:
        return image_urls[0] if isinstance(image_urls[0], str) else str(image_urls[0])

    covers = item.get("covers", [])
    if covers:
        return covers[0] if isinstance(covers[0], str) else str(covers[0])

    return ""
