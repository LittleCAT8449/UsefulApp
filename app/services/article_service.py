"""专栏文章 业务逻辑。"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Article


async def list_articles(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    up_user_id: int | None = None,
    sort_by: str = "pubdate",
    order: str = "desc",
) -> tuple[list[Article], int]:
    """获取文章列表（分页、筛选、排序）。"""
    query = select(Article)
    count_query = select(func.count(Article.id))

    if up_user_id is not None:
        query = query.where(Article.up_user_id == up_user_id)
        count_query = count_query.where(Article.up_user_id == up_user_id)

    sort_col = getattr(Article, sort_by, Article.pubdate)
    if order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc().nullslast())

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )
    items = list(result.scalars().all())

    return items, total


async def get_article_by_cv_id(db: AsyncSession, cv_id: int) -> Article | None:
    """通过 CV ID 获取文章。"""
    result = await db.execute(
        select(Article).where(Article.cv_id == cv_id)
    )
    return result.scalar_one_or_none()
