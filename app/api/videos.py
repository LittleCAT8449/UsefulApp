"""视频 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_client
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.video import VideoResponse, VideoListResponse, DownloadRequest
from app.services import video_service
from app.services import download_service
from app.services.up_user_service import get_up_user, get_up_user_by_id

router = APIRouter(prefix="/videos", tags=["视频"])


@router.get("", response_model=PaginatedResponse[VideoListResponse])
async def list_videos(
    page: int = 1,
    page_size: int = 20,
    up_uid: int | None = None,
    sort_by: str = "pubdate",
    order: str = "desc",
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """获取视频列表（分页、筛选、排序）。"""
    up_user_id = None
    if up_uid is not None:
        up_user = await get_up_user(db, up_uid)
        if up_user:
            up_user_id = up_user.id

    items, total = await video_service.list_videos(db, page, page_size, up_user_id, sort_by, order)
    total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 0

    return {
        "items": [VideoListResponse.model_validate(v) for v in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{bvid}", response_model=VideoResponse)
async def get_video(
    bvid: str,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> VideoResponse:
    """获取视频详情。"""
    video = await video_service.get_video_by_bvid(db, bvid)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="视频不存在")
    return VideoResponse.model_validate(video)


@router.post("/{bvid}/download", status_code=status.HTTP_202_ACCEPTED)
async def request_download(
    bvid: str,
    body: DownloadRequest = DownloadRequest(),
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """请求下载视频。返回下载任务 ID。"""
    video = await video_service.get_video_by_bvid(db, bvid)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="视频不存在")

    try:
        task = await download_service.create_download_task(db, video.id, body.quality)
        return {
            "message": "下载任务已创建",
            "task_id": task.id,
            "bvid": bvid,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{bvid}", response_model=MessageResponse)
async def delete_video(
    bvid: str,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """删除视频数据（含下载文件）。"""
    video = await video_service.get_video_by_bvid(db, bvid)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="视频不存在")

    # 删除本地文件
    import os
    if video.cover_local_path and os.path.exists(video.cover_local_path):
        os.remove(video.cover_local_path)

    await db.delete(video)
    await db.flush()
    return {"message": f"视频 {bvid} 已删除"}
