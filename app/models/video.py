"""视频 模型。"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bvid: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    aid: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    up_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("up_users.id"), nullable=False, index=True)

    # 基本信息
    title: Mapped[str] = mapped_column(String(256), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    cover_url: Mapped[str] = mapped_column(String(512), default="")
    cover_local_path: Mapped[str] = mapped_column(String(512), default="")
    duration: Mapped[int] = mapped_column(Integer, default=0)

    # 统计数据
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    danmaku_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0)
    coin_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)

    # 分P信息
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    cid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    pages: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

    # 画质
    quality: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 时间戳
    pubdate: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    up_user = relationship("UpUser", back_populates="videos")
    download_tasks = relationship("DownloadTask", back_populates="video", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Video(id={self.id}, bvid='{self.bvid}', title='{self.title}')>"
