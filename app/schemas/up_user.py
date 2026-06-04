"""UP主 Pydantic 模型。"""

from datetime import datetime
from pydantic import BaseModel, Field


class UpUserBase(BaseModel):
    bilibili_uid: int = Field(..., gt=0, description="B站用户UID")


class UpUserCreate(UpUserBase):
    pass


class UpUserUpdate(BaseModel):
    is_active: bool | None = None
    notify_new_video: bool | None = None
    notify_new_article: bool | None = None
    notify_video_download: bool | None = None


class UpUserResponse(BaseModel):
    id: int
    bilibili_uid: int
    name: str
    face_url: str
    sign: str
    level: int
    sex: str
    follower_count: int
    following_count: int
    video_count: int
    is_active: bool
    notify_new_video: bool
    notify_new_article: bool
    notify_video_download: bool
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UpUserListResponse(BaseModel):
    """UP主列表项（精简）。"""
    id: int
    bilibili_uid: int
    name: str
    face_url: str
    follower_count: int
    video_count: int
    is_active: bool
    last_checked_at: datetime | None

    model_config = {"from_attributes": True}
