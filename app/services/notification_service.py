"""通知 业务逻辑。"""

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification


async def list_notifications(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    is_read: bool | None = None,
    type: str | None = None,
) -> tuple[list[Notification], int]:
    """获取通知列表。"""
    query = select(Notification)
    count_query = select(func.count(Notification.id))

    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
        count_query = count_query.where(Notification.is_read == is_read)

    if type:
        query = query.where(Notification.type == type)
        count_query = count_query.where(Notification.type == type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(result.scalars().all())

    return items, total


async def get_unread_count(db: AsyncSession) -> int:
    """获取未读通知数。"""
    result = await db.execute(
        select(func.count(Notification.id)).where(Notification.is_read == False)
    )
    return result.scalar() or 0


async def mark_as_read(db: AsyncSession, notification_id: int) -> bool:
    """标记单条通知为已读。"""
    notif = await db.get(Notification, notification_id)
    if not notif:
        return False
    notif.is_read = True
    await db.flush()
    return True


async def mark_all_as_read(db: AsyncSession) -> int:
    """全部标为已读，返回更新的行数。"""
    result = await db.execute(
        update(Notification)
        .where(Notification.is_read == False)
        .values(is_read=True)
    )
    await db.flush()
    return result.rowcount or 0
