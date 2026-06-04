"""通知 模型。"""

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 类型: new_video, new_article, video_update, download_complete, download_failed, system
    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(256), default="")
    message: Mapped[str] = mapped_column(Text, default="")

    # 关联实体
    reference_type: Mapped[str] = mapped_column(String(32), default="")  # video / article / download_task
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    up_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("up_users.id"), nullable=True, index=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pushed: Mapped[bool] = mapped_column(Boolean, default=False)

    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系
    up_user = relationship("UpUser")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type='{self.type}', title='{self.title}')>"
