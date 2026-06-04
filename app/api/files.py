"""文件服务路由 —— 封面图片 & 下载视频。"""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from starlette.requests import Request
from starlette.responses import StreamingResponse

from app.config import settings

router = APIRouter()


@router.get("/covers/{filename}")
async def get_cover(filename: str) -> FileResponse:
    """获取封面图片。"""
    filepath = Path(settings.cover_path) / filename
    if not filepath.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="封面不存在")

    return FileResponse(
        str(filepath),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/downloads/{filename:path}")
async def get_download_file(request: Request, filename: str) -> StreamingResponse:
    """流式传输已下载的视频文件（支持 Range 请求）。"""
    filepath = Path(settings.download_path) / filename

    # 安全检查：防止路径遍历
    try:
        filepath = filepath.resolve()
        download_root = Path(settings.download_path).resolve()
        if not str(filepath).startswith(str(download_root)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="禁止访问")
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的文件路径")

    if not filepath.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    file_size = filepath.stat().st_size

    # 支持 Range 请求（移动端视频播放需要）
    range_header = request.headers.get("Range")
    if range_header:
        start, end = 0, file_size - 1
        range_str = range_header.replace("bytes=", "")
        parts = range_str.split("-")
        if parts[0]:
            start = int(parts[0])
        if len(parts) > 1 and parts[1]:
            end = int(parts[1])

        if start >= file_size:
            raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)

        chunk_size = min(end - start + 1, file_size - start)

        async def ranged_file():
            with open(filepath, "rb") as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    chunk = f.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    yield chunk
                    remaining -= len(chunk)

        return StreamingResponse(
            ranged_file(),
            status_code=206,
            media_type="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{start + chunk_size - 1}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
            },
        )

    # 完整文件响应
    return StreamingResponse(
        _file_iterator(filepath),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
        },
    )


async def _file_iterator(filepath: Path, chunk_size: int = 1024 * 1024):
    """按块读取文件（异步友好）。"""
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk
