"""WebSocket 实时通知端点。"""

import asyncio
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger

from app.notifications.manager import ws_manager
from app.api.deps import AUTH_ENABLED

router = APIRouter()


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(default=""),
) -> None:
    """WebSocket 端点 —— 实时通知推送。

    客户端连接后自动接收：
    - notification: 新内容通知
    - download_progress: 下载进度更新
    - ping: 心跳（每30秒）

    当 AUTH_ENABLED=true 时，需要携带有效的 JWT token 参数。
    """
    # JWT 验证
    if AUTH_ENABLED:
        if not token:
            await websocket.close(code=4001, reason="Missing token")
            return
        try:
            from app.api.auth import verify_access_token
            verify_access_token(token)
        except Exception:
            await websocket.close(code=4001, reason="Invalid token")
            return

    client_id = str(uuid.uuid4())

    # 尝试连接
    if not await ws_manager.connect(client_id, websocket):
        return

    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "data": {"client_id": client_id, "message": "已连接到 B站追踪服务器"},
        })

        # 同时运行发送循环和心跳循环
        sender_task = asyncio.create_task(ws_manager.sender_loop(client_id))
        heartbeat_task = asyncio.create_task(ws_manager.heartbeat_loop(client_id))

        # 接收循环 —— 处理客户端消息（如 ping）
        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type", "")
                if msg_type == "pong":
                    pass  # 客户端响应心跳
                elif msg_type == "subscribe_up":
                    # 订阅特定 UP主的通知（可选功能）
                    up_uid = data.get("up_uid", 0)
                    logger.debug(f"客户端 {client_id[:8]} 订阅 UP主 {up_uid}")
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

        # 清理
        sender_task.cancel()
        heartbeat_task.cancel()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket 异常: {e}")
    finally:
        await ws_manager.disconnect(client_id)
        logger.info(f"WebSocket 断开: {client_id[:8]}...")
