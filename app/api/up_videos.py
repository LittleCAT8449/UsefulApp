"""按 UP主查询视频的子路由。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_client
from app.schemas.common import PaginatedResponse
from app.schemas.video import VideoListResponse
from app.services import video_service
from app.services.up_user_service import get_up_user

router = APIRouter()


@router.get("/{uid}/videos", response_model=PaginatedResponse[VideoListResponse])
async def get_up_videos(
    uid: int,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """获取某 UP主的视频列表。"""
    up_user = await get_up_user(db, uid)
    if not up_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UP主不存在")

    items, total = await video_service.get_videos_by_up_user(db, up_user.id, page, page_size)
    total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 0

    return {
        "items": [VideoListResponse.model_validate(v) for v in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
