"""UP主 模型。"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UpUser(Base):
    __tablename__ = "up_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bilibili_uid: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)

    # 基本信息
    name: Mapped[str] = mapped_column(String(128), default="")
    face_url: Mapped[str] = mapped_column(String(512), default="")
    sign: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    level: Mapped[int] = mapped_column(Integer, default=0)
    sex: Mapped[str] = mapped_column(String(8), default="")

    # 统计数据
    follower_count: Mapped[int] = mapped_column(Integer, default=0)
    following_count: Mapped[int] = mapped_column(Integer, default=0)
    video_count: Mapped[int] = mapped_column(Integer, default=0)

    # 追踪设置
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_new_video: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_new_article: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_video_download: Mapped[bool] = mapped_column(Boolean, default=False)

    # 时间戳
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    videos = relationship("Video", back_populates="up_user", cascade="all, delete-orphan")
    articles = relationship("Article", back_populates="up_user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<UpUser(id={self.id}, uid={self.bilibili_uid}, name='{self.name}')>"
