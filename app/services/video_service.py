"""视频 业务逻辑。"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Video


async def list_videos(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    up_user_id: int | None = None,
    sort_by: str = "pubdate",
    order: str = "desc",
) -> tuple[list[Video], int]:
    """获取视频列表（分页、筛选、排序）。"""
    query = select(Video)
    count_query = select(func.count(Video.id))

    if up_user_id is not None:
        query = query.where(Video.up_user_id == up_user_id)
        count_query = count_query.where(Video.up_user_id == up_user_id)

    # 排序
    sort_col = getattr(Video, sort_by, Video.pubdate)
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


async def get_video_by_bvid(db: AsyncSession, bvid: str) -> Video | None:
    """通过 BVID 获取视频。"""
    result = await db.execute(
        select(Video).where(Video.bvid == bvid)
    )
    return result.scalar_one_or_none()


async def get_videos_by_up_user(
    db: AsyncSession, up_user_id: int, page: int = 1, page_size: int = 20
) -> tuple[list[Video], int]:
    """获取某 UP主的所有视频。"""
    return await list_videos(db, page=page, page_size=page_size, up_user_id=up_user_id)
