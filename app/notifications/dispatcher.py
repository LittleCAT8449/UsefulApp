"""通知分发 —— 将数据库通知推送到 WebSocket。"""

from app.notifications.manager import ws_manager


async def dispatch_notification(notification_data: dict) -> None:
    """向所有已连接 WebSocket 客户端广播通知。

    Args:
        notification_data: 通知数据字典，需包含 type, title, message 等字段。
    """
    await ws_manager.broadcast({
        "type": "notification",
        "data": notification_data,
    })


async def dispatch_download_progress(
    task_id: int, video_id: int, progress: float, status: str, bvid: str = ""
) -> None:
    """广播下载进度。"""
    await ws_manager.broadcast({
        "type": "download_progress",
        "data": {
            "task_id": task_id,
            "video_id": video_id,
            "bvid": bvid,
            "progress": progress,
            "status": status,
        },
    })
