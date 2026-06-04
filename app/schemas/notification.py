"""通知 Pydantic 模型。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: str
    reference_type: str
    reference_id: int | None
    up_user_id: int | None
    is_read: bool
    is_pushed: bool
    metadata_: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    count: int
