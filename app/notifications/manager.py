"""WebSocket 连接管理器 —— 连接生命周期、心跳、广播。"""

import asyncio
import json
from typing import Any

from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    """管理所有活跃的 WebSocket 连接。"""

    def __init__(self, max_connections: int = 100) -> None:
        self._connections: dict[str, WebSocket] = {}
        self._queues: dict[str, asyncio.Queue[dict[str, Any]]] = {}
        self._max_connections = max_connections
        self._lock = asyncio.Lock()

    async def connect(self, client_id: str, websocket: WebSocket) -> bool:
        """接受新连接。

        Args:
            client_id: 客户端唯一标识。
            websocket: WebSocket 连接。

        Returns:
            是否成功连接。
        """
        async with self._lock:
            if len(self._connections) >= self._max_connections:
                await websocket.close(code=1013, reason="Too many connections")
                return False

            if client_id in self._connections:
                # 同一客户端已有连接，关闭旧的
                await self._disconnect_client(client_id)

            await websocket.accept()
            self._connections[client_id] = websocket
            self._queues[client_id] = asyncio.Queue(maxsize=500)
            logger.info(f"WebSocket 连接: {client_id} (total={len(self._connections)})")
            return True

    async def disconnect(self, client_id: str) -> None:
        """断开连接。"""
        async with self._lock:
            await self._disconnect_client(client_id)

    async def _disconnect_client(self, client_id: str) -> None:
        """内部：清理单个客户端连接。"""
        ws = self._connections.pop(client_id, None)
        self._queues.pop(client_id, None)
        if ws:
            try:
                await ws.close()
            except Exception:
                pass

    async def broadcast(self, message: dict[str, Any]) -> None:
        """广播消息到所有已连接客户端。"""
        for client_id, queue in list(self._queues.items()):
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning(f"客户端 {client_id[:8]}... 消息队列已满，丢弃消息")

    async def send_personal(self, client_id: str, message: dict[str, Any]) -> None:
        """发送消息到指定客户端。"""
        queue = self._queues.get(client_id)
        if queue:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning(f"客户端 {client_id[:8]}... 消息队列已满")

    async def sender_loop(self, client_id: str) -> None:
        """每个连接的发送循环 —— 从队列取消息并发送。"""
        queue = self._queues.get(client_id)
        ws = self._connections.get(client_id)
        if not queue or not ws:
            return

        try:
            while True:
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                try:
                    await ws.send_json(message)
                except Exception:
                    break
        except asyncio.TimeoutError:
            pass  # 30s 无消息，继续下一轮
        except Exception:
            pass

    async def heartbeat_loop(self, client_id: str) -> None:
        """心跳循环 —— 每 30 秒发送 ping。"""
        ws = self._connections.get(client_id)
        if not ws:
            return

        try:
            while True:
                await asyncio.sleep(30.0)
                try:
                    await ws.send_json({"type": "ping"})
                except Exception:
                    break
        except Exception:
            pass

    @property
    def active_count(self) -> int:
        return len(self._connections)


# 全局单例
ws_manager = ConnectionManager()
