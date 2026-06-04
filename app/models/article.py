"""专栏文章 模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cv_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    up_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("up_users.id"), nullable=False, index=True)

    # 基本信息
    title: Mapped[str] = mapped_column(String(256), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    cover_url: Mapped[str] = mapped_column(String(512), default="")
    cover_local_path: Mapped[str] = mapped_column(String(512), default="")
    content: Mapped[str] = mapped_column(Text, default="")

    # 统计数据
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    coin_count: Mapped[int] = mapped_column(Integer, default=0)
    reply_count: Mapped[int] = mapped_column(Integer, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    words_count: Mapped[int] = mapped_column(Integer, default=0)

    # 时间戳
    pubdate: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    up_user = relationship("UpUser", back_populates="articles")

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, cv_id={self.cv_id}, title='{self.title}')>"
