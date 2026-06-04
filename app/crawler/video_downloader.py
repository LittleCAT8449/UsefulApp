"""DASH 视频下载器 —— 分块下载 + ffmpeg 合并。"""

import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Awaitable

import httpx
from loguru import logger

from app.config import settings
from app.crawler.bilibili_client import bilibili_client
from app.crawler.video_crawler import fetch_video_playurl, fetch_video_pagelist

# 画质代码对照
QUALITY_MAP = {
    16: "360P",
    32: "480P",
    64: "720P",
    80: "1080P",
    112: "1080P+",
    116: "1080P60",
    120: "4K",
}


async def download_video(
    bvid: str,
    quality: int = 80,
    progress_callback: Callable[[float, str], Awaitable[None]] | None = None,
) -> dict:
    """下载 B站 视频（DASH 流 + ffmpeg 合并）。

    Args:
        bvid: 视频 BV 号。
        quality: 目标画质代码，默认 80 (1080P)。
        progress_callback: 进度回调 (progress, status)。

    Returns:
        {
            "success": bool,
            "file_path": str | None,
            "file_size": int | None,
            "error": str | None,
        }
    """
    async def report(progress: float, status: str) -> None:
        if progress_callback:
            await progress_callback(progress, status)

    await report(0.0, "fetching_info")

    # 1. 获取分P信息
    pages = await fetch_video_pagelist(bvid)
    if not pages:
        return {"success": False, "file_path": None, "file_size": None, "error": "无法获取分P信息"}

    cid = pages[0].get("cid", 0)
    if not cid:
        return {"success": False, "file_path": None, "file_size": None, "error": "无法获取 cid"}

    # 2. 获取播放地址
    play_data = await fetch_video_playurl(bvid, cid, quality)
    if not play_data:
        return {"success": False, "file_path": None, "file_size": None, "error": "无法获取播放地址"}

    dash = play_data.get("dash", {})
    video_streams = dash.get("video", [])
    audio_streams = dash.get("audio", [])

    if not video_streams or not audio_streams:
        return {"success": False, "file_path": None, "file_size": None, "error": "未找到 DASH 流"}

    # 选择目标画质视频流 + 最高音质音频流
    video_stream = video_streams[0]
    audio_stream = max(audio_streams, key=lambda x: x.get("bandwidth", 0))

    video_url = video_stream.get("baseUrl") or video_stream.get("base_url", "")
    audio_url = audio_stream.get("baseUrl") or audio_stream.get("base_url", "")

    if not video_url or not audio_url:
        return {"success": False, "file_path": None, "file_size": None, "error": "视频/音频 URL 为空"}

    # 3. 准备下载目录
    download_dir = Path(settings.download_path) / bvid
    download_dir.mkdir(parents=True, exist_ok=True)

    video_path = download_dir / f"{bvid}_video.m4s"
    audio_path = download_dir / f"{bvid}_audio.m4s"
    output_path = download_dir / f"{bvid}.mp4"

    # 如果已合并完成，直接返回
    if output_path.exists() and output_path.stat().st_size > 0:
        await report(1.0, "completed")
        return {
            "success": True,
            "file_path": str(output_path),
            "file_size": output_path.stat().st_size,
            "error": None,
        }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com",
    }

    try:
        # 4. 下载视频流
        await report(0.05, "downloading_video")
        await _download_file(video_url, video_path, headers,
                             lambda p: report(0.05 + p * 0.45, "downloading_video"))

        # 5. 下载音频流
        await report(0.50, "downloading_audio")
        await _download_file(audio_url, audio_path, headers,
                             lambda p: report(0.50 + p * 0.30, "downloading_audio"))

        # 6. ffmpeg 合并
        await report(0.80, "merging")
        await _merge_with_ffmpeg(video_path, audio_path, output_path)

        # 7. 清理临时文件
        video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)

        file_size = output_path.stat().st_size
        await report(1.0, "completed")
        logger.info(f"视频下载完成: {bvid} -> {output_path} ({file_size} bytes)")

        return {
            "success": True,
            "file_path": str(output_path),
            "file_size": file_size,
            "error": None,
        }

    except Exception as e:
        logger.error(f"视频下载失败: {bvid} -> {e}")
        return {"success": False, "file_path": None, "file_size": None, "error": str(e)}


async def _download_file(
    url: str,
    filepath: Path,
    headers: dict,
    progress_callback: Callable[[float], Awaitable[None]] | None = None,
    chunk_size: int = 1024 * 1024,  # 1MB
) -> None:
    """分块下载文件，支持进度回调。"""
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
        async with client.stream("GET", url, headers=headers) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length", 0))

            downloaded = 0
            with open(filepath, "wb") as f:
                async for chunk in resp.aiter_bytes(chunk_size):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total > 0:
                        await progress_callback(downloaded / total)


async def _merge_with_ffmpeg(
    video_path: Path, audio_path: Path, output_path: Path
) -> None:
    """使用 ffmpeg 无损合并视频和音频。"""
    cmd = [
        "ffmpeg",
        "-y",  # 覆盖已存在文件
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c", "copy",
        "-movflags", "+faststart",
        str(output_path),
    ]

    logger.debug(f"执行 ffmpeg: {' '.join(cmd)}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode("utf-8", errors="replace")[-500:]
        raise RuntimeError(f"ffmpeg 合并失败 (exit={process.returncode}): {error_msg}")

    logger.debug("ffmpeg 合并完成")
