"""UP主 业务逻辑。"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UpUser, Video
from app.crawler.up_crawler import fetch_up_info
from app.crawler.cover_downloader import download_cover, get_cover_filename


async def add_up_user(db: AsyncSession, bilibili_uid: int) -> UpUser:
    """添加 UP主追踪 —— 获取基本信息并保存。"""
    # 检查是否已存在
    result = await db.execute(
        select(UpUser).where(UpUser.bilibili_uid == bilibili_uid)
    )
    existing = result.scalar_one_or_none()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            await db.flush()
        return existing

    # 获取 UP主信息
    data = await fetch_up_info(bilibili_uid)
    if not data:
        raise ValueError(f"无法获取 UP主信息 (uid={bilibili_uid})")

    up_user = UpUser(
        bilibili_uid=bilibili_uid,
        name=data.get("name", ""),
        face_url=data.get("face", ""),
        sign=data.get("sign", ""),
        level=data.get("level", 0),
        sex=data.get("sex", ""),
        follower_count=data.get("follower", 0) or data.get("follower_count", 0),
        following_count=data.get("following", 0) or data.get("following_count", 0),
    )
    db.add(up_user)
    await db.flush()
    return up_user


async def get_up_user(db: AsyncSession, uid: int) -> UpUser | None:
    """通过 bilibili_uid 获取 UP主。"""
    result = await db.execute(
        select(UpUser).where(UpUser.bilibili_uid == uid)
    )
    return result.scalar_one_or_none()


async def get_up_user_by_id(db: AsyncSession, db_id: int) -> UpUser | None:
    """通过数据库 ID 获取 UP主。"""
    return await db.get(UpUser, db_id)


async def list_up_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str = "",
) -> tuple[list[UpUser], int]:
    """获取 UP主列表（分页 + 搜索）。"""
    query = select(UpUser)
    count_query = select(func.count(UpUser.id))

    if search:
        filter_clause = UpUser.name.contains(search)
        query = query.where(filter_clause)
        count_query = count_query.where(filter_clause)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(UpUser.name).offset((page - 1) * page_size).limit(page_size)
    )
    items = list(result.scalars().all())

    return items, total


async def remove_up_user(db: AsyncSession, uid: int) -> bool:
    """移除 UP主追踪（软删除 —— 设 is_active=False）。"""
    up_user = await get_up_user(db, uid)
    if not up_user:
        return False
    up_user.is_active = False
    await db.flush()
    return True


async def delete_up_user_hard(db: AsyncSession, uid: int) -> bool:
    """硬删除 UP主及其所有关联数据。"""
    up_user = await get_up_user(db, uid)
    if not up_user:
        return False
    await db.delete(up_user)
    await db.flush()
    return True
