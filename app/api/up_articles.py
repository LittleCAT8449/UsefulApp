"""按 UP主查询专栏文章的子路由。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_client
from app.schemas.common import PaginatedResponse
from app.schemas.article import ArticleListResponse
from app.services import article_service
from app.services.up_user_service import get_up_user

router = APIRouter()


@router.get("/{uid}/articles", response_model=PaginatedResponse[ArticleListResponse])
async def get_up_articles(
    uid: int,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """获取某 UP主的专栏文章列表。"""
    up_user = await get_up_user(db, uid)
    if not up_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UP主不存在")

    items, total = await article_service.list_articles(
        db, page=page, page_size=page_size, up_user_id=up_user.id
    )
    total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 0

    return {
        "items": [ArticleListResponse.model_validate(a) for a in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
