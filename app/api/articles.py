"""专栏文章 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_client
from app.schemas.common import PaginatedResponse
from app.schemas.article import ArticleResponse, ArticleListResponse
from app.services import article_service
from app.services.up_user_service import get_up_user

router = APIRouter(prefix="/articles", tags=["专栏文章"])


@router.get("", response_model=PaginatedResponse[ArticleListResponse])
async def list_articles(
    page: int = 1,
    page_size: int = 20,
    up_uid: int | None = None,
    sort_by: str = "pubdate",
    order: str = "desc",
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """获取文章列表（分页、筛选、排序）。"""
    up_user_id = None
    if up_uid is not None:
        up_user = await get_up_user(db, up_uid)
        if up_user:
            up_user_id = up_user.id

    items, total = await article_service.list_articles(db, page, page_size, up_user_id, sort_by, order)
    total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 0

    return {
        "items": [ArticleListResponse.model_validate(a) for a in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{cv_id}", response_model=ArticleResponse)
async def get_article(
    cv_id: int,
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> ArticleResponse:
    """获取专栏文章详情（含正文）。"""
    article = await article_service.get_article_by_cv_id(db, cv_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    return ArticleResponse.model_validate(article)
