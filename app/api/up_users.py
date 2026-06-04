"""UP主管理 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_client
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.up_user import (
    UpUserCreate,
    UpUserResponse,
    UpUserListResponse,
    UpUserUpdate,
)
from app.services import up_user_service
from app.crawler.engine import crawler_engine

router = APIRouter(prefix="/up", tags=["UP主管理"])


@router.post("/add", response_model=UpUserResponse, status_code=status.HTTP_201_CREATED)
async def add_up_user(
    body: UpUserCreate,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> UpUserResponse:
    """添加 UP主追踪。

    输入 B站 UID，自动获取 UP主基本信息并开始追踪。
    """
    try:
        up_user = await up_user_service.add_up_user(db, body.bilibili_uid)
        return UpUserResponse.model_validate(up_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/list", response_model=PaginatedResponse[UpUserListResponse])
async def list_up_users(
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """获取 UP主追踪列表（分页 + 搜索）。"""
    items, total = await up_user_service.list_up_users(db, page, page_size, search)
    total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 0

    return {
        "items": [UpUserListResponse.model_validate(u) for u in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{uid}", response_model=UpUserResponse)
async def get_up_user(
    uid: int,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> UpUserResponse:
    """获取 UP主详情（通过 B站 UID）。"""
    up_user = await up_user_service.get_up_user(db, uid)
    if not up_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UP主不存在")
    return UpUserResponse.model_validate(up_user)


@router.put("/{uid}", response_model=UpUserResponse)
async def update_up_user(
    uid: int,
    body: UpUserUpdate,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> UpUserResponse:
    """更新 UP主追踪设置。"""
    up_user = await up_user_service.get_up_user(db, uid)
    if not up_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UP主不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(up_user, key, value)
    await db.flush()

    return UpUserResponse.model_validate(up_user)


@router.delete("/{uid}", response_model=MessageResponse)
async def remove_up_user(
    uid: int,
    hard: bool = False,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """移除 UP主追踪。

    - 默认软删除（is_active=False），数据保留。
    - hard=true 时硬删除所有关联数据。
    """
    if hard:
        success = await up_user_service.delete_up_user_hard(db, uid)
    else:
        success = await up_user_service.remove_up_user(db, uid)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UP主不存在")

    return {"message": f"UP主 {uid} 已移除"}


@router.post("/{uid}/refresh", response_model=MessageResponse)
async def refresh_up_user(
    uid: int,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """立即刷新某 UP主的数据。"""
    up_user = await up_user_service.get_up_user(db, uid)
    if not up_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UP主不存在")

    # 触发立即检查
    stats = await crawler_engine._check_up_user(up_user.id, up_user.bilibili_uid)
    return {
        "message": (
            f"刷新完成: UP信息={'已更新' if stats['up_updated'] else '无变化'}, "
            f"新视频={stats['new_videos']}, 新文章={stats['new_articles']}"
        ),
    }
