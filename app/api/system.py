"""系统状态 & 配置 API 路由。"""

import time
import platform

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_client
from app.schemas.common import MessageResponse
from app.models import UpUser, Video, Article, DownloadTask, SystemConfig
from app.notifications.manager import ws_manager

router = APIRouter(prefix="/system", tags=["系统"])

# 服务启动时间
_start_time = time.time()


@router.get("/status")
async def system_status(
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """获取服务器运行状态。"""
    # 统计数据
    up_count_result = await db.execute(select(func.count(UpUser.id)).where(UpUser.is_active == True))
    active_up_count = up_count_result.scalar() or 0

    video_count_result = await db.execute(select(func.count(Video.id)))
    video_count = video_count_result.scalar() or 0

    article_count_result = await db.execute(select(func.count(Article.id)))
    article_count = article_count_result.scalar() or 0

    download_pending_result = await db.execute(
        select(func.count(DownloadTask.id)).where(
            DownloadTask.status.in_(["pending", "downloading_video", "downloading_audio", "merging"])
        )
    )
    download_pending = download_pending_result.scalar() or 0

    download_completed_result = await db.execute(
        select(func.count(DownloadTask.id)).where(DownloadTask.status == "completed")
    )
    download_completed = download_completed_result.scalar() or 0

    uptime = int(time.time() - _start_time)

    return {
        "status": "running",
        "uptime_seconds": uptime,
        "uptime_display": f"{uptime // 3600}h {(uptime % 3600) // 60}m {uptime % 60}s",
        "active_up_count": active_up_count,
        "video_count": video_count,
        "article_count": article_count,
        "download_pending": download_pending,
        "download_completed": download_completed,
        "ws_connections": ws_manager.active_count,
        "python_version": platform.python_version(),
        "platform": platform.system(),
    }


@router.get("/config")
async def get_config(
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """获取当前系统配置。"""
    result = await db.execute(select(SystemConfig))
    configs = result.scalars().all()
    return {c.key: c.value for c in configs}


@router.put("/config", response_model=MessageResponse)
async def update_config(
    updates: dict[str, str],
    db: AsyncSession = Depends(get_db),
    client_id: str = Depends(get_current_client),
) -> dict:
    """更新系统配置（批量）。"""
    for key, value in updates.items():
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()
        if config:
            config.value = value
        else:
            db.add(SystemConfig(key=key, value=value))

    await db.flush()
    return {"message": f"已更新 {len(updates)} 项配置"}
