"""下载任务 业务逻辑。"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DownloadTask


async def list_download_tasks(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> tuple[list[DownloadTask], int]:
    """获取下载任务列表。"""
    query = select(DownloadTask)
    count_query = select(func.count(DownloadTask.id))

    if status:
        query = query.where(DownloadTask.status == status)
        count_query = count_query.where(DownloadTask.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(DownloadTask.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(result.scalars().all())

    return items, total


async def get_download_task(db: AsyncSession, task_id: int) -> DownloadTask | None:
    """获取下载任务详情。"""
    return await db.get(DownloadTask, task_id)


async def create_download_task(
    db: AsyncSession, video_id: int, quality: int = 80
) -> DownloadTask:
    """创建下载任务。"""
    # 检查是否有进行中的任务
    result = await db.execute(
        select(DownloadTask).where(
            DownloadTask.video_id == video_id,
            DownloadTask.status.in_(["pending", "downloading_video", "downloading_audio", "merging"]),
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise ValueError(f"该视频已有进行中的下载任务 (task_id={existing.id})")

    task = DownloadTask(video_id=video_id, quality=quality)
    db.add(task)
    await db.flush()
    return task
