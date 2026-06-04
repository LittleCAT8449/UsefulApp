"""封面图下载 —— 异步下载视频/文章封面到本地。"""

import asyncio
import os
from pathlib import Path

import httpx
from loguru import logger

from app.config import settings


async def download_cover(url: str, filename: str) -> str | None:
    """下载封面图到本地。

    Args:
        url: 封面图 URL。
        filename: 本地文件名（不含路径）。

    Returns:
        本地相对路径，失败返回 None。
    """
    if not url:
        return None

    cover_dir = Path(settings.cover_path)
    cover_dir.mkdir(parents=True, exist_ok=True)
    filepath = cover_dir / filename

    # 如果已存在且非空，跳过
    if filepath.exists() and filepath.stat().st_size > 0:
        logger.debug(f"封面已存在，跳过: {filename}")
        return str(filepath)

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.bilibili.com",
            }
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()

            filepath.write_bytes(resp.content)
            logger.info(f"封面下载完成: {filename} ({len(resp.content)} bytes)")
            return str(filepath)

    except Exception as e:
        logger.error(f"封面下载失败: {url} -> {e}")
        # 删除可能的不完整文件
        if filepath.exists():
            filepath.unlink()
        return None


def get_cover_filename(bvid: str) -> str:
    """根据 BVID 生成封面文件名。"""
    return f"{bvid}.jpg"


def get_article_cover_filename(cv_id: int) -> str:
    """根据 CV ID 生成文章封面文件名。"""
    return f"cv{cv_id}.jpg"
