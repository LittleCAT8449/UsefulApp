"""下载管理 API 路由。"""

import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_client
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.download import DownloadTaskResponse
from app.services import download_service
from app.models import DownloadTask

router = APIRouter(prefix="/downloads", tags=["下载管理"])


@router.get("", response_model=PaginatedResponse[DownloadTaskResponse])
async def list_downloads(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """获取下载任务列表。"""
    items, total = await download_service.list_download_tasks(db, page, page_size, status)
    total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 0

    return {
        "items": [DownloadTaskResponse.model_validate(t) for t in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{task_id}", response_model=DownloadTaskResponse)
async def get_download(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> DownloadTaskResponse:
    """获取下载任务详情（含进度）。"""
    task = await download_service.get_download_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="下载任务不存在")
    return DownloadTaskResponse.model_validate(task)


@router.post("/{task_id}/retry", response_model=MessageResponse)
async def retry_download(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """重试失败的下载任务。"""
    task = await download_service.get_download_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="下载任务不存在")

    if task.status not in ("failed",):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能重试失败的任务")

    task.status = "pending"
    task.error_message = ""
    task.progress = 0.0
    await db.flush()
    return {"message": f"下载任务 {task_id} 已重新加入队列"}


@router.post("/{task_id}/cancel", response_model=MessageResponse)
async def cancel_download(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """取消下载任务。"""
    task = await download_service.get_download_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="下载任务不存在")

    if task.status in ("completed", "failed"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="任务已结束，无法取消")

    task.status = "failed"
    task.error_message = "用户取消"
    await db.flush()
    return {"message": f"下载任务 {task_id} 已取消"}


@router.delete("/{task_id}", response_model=MessageResponse)
async def delete_download(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """删除下载任务及文件。"""
    task = await download_service.get_download_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="下载任务不存在")

    # 删除关联文件
    for path_attr in ("merged_file_path", "video_file_path", "audio_file_path"):
        filepath = getattr(task, path_attr, "")
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

    await db.delete(task)
    await db.flush()
    return {"message": f"下载任务 {task_id} 已删除"}
