"""视频 Pydantic 模型。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class VideoResponse(BaseModel):
    id: int
    bvid: str
    aid: int | None
    up_user_id: int
    title: str
    description: str
    cover_url: str
    cover_local_path: str
    duration: int
    view_count: int
    danmaku_count: int
    reply_count: int
    favorite_count: int
    coin_count: int
    share_count: int
    like_count: int
    tags: list[str]
    cid: int | None
    page_count: int
    pages: list[dict[str, Any]]
    quality: int | None
    pubdate: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class VideoListResponse(BaseModel):
    """视频列表项（精简）。"""
    id: int
    bvid: str
    title: str
    cover_url: str
    cover_local_path: str
    duration: int
    view_count: int
    danmaku_count: int
    like_count: int
    pubdate: datetime | None

    model_config = {"from_attributes": True}


class DownloadRequest(BaseModel):
    quality: int = 80
