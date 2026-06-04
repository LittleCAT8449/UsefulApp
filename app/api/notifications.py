"""通知 REST API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_client
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["通知"])


@router.get("", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    page: int = 1,
    page_size: int = 20,
    is_read: bool | None = None,
    type: str | None = None,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """获取通知列表（分页、筛选）。"""
    items, total = await notification_service.list_notifications(db, page, page_size, is_read, type)
    total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 0

    return {
        "items": [NotificationResponse.model_validate(n) for n in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """获取未读通知数量。"""
    count = await notification_service.get_unread_count(db)
    return {"count": count}


@router.put("/{notification_id}/read", response_model=MessageResponse)
async def mark_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """标记单条通知为已读。"""
    success = await notification_service.mark_as_read(db, notification_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")
    return {"message": "已标记为已读"}


@router.put("/read-all", response_model=MessageResponse)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """全部标为已读。"""
    count = await notification_service.mark_all_as_read(db)
    return {"message": f"已将 {count} 条通知标记为已读"}
