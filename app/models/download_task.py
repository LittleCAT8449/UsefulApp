"""下载任务 模型。"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DownloadTask(Base):
    __tablename__ = "download_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(Integer, ForeignKey("videos.id"), nullable=False, index=True)

    # 状态: pending, downloading_video, downloading_audio, merging, completed, failed
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)

    quality: Mapped[int] = mapped_column(Integer, default=80)

    # DASH 流 URL（临时）
    video_url: Mapped[str] = mapped_column(String(1024), default="")
    audio_url: Mapped[str] = mapped_column(String(1024), default="")

    # 本地文件路径
    video_file_path: Mapped[str] = mapped_column(String(512), default="")
    audio_file_path: Mapped[str] = mapped_column(String(512), default="")
    merged_file_path: Mapped[str] = mapped_column(String(512), default="")

    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # 时间戳
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系
    video = relationship("Video", back_populates="download_tasks")

    def __repr__(self) -> str:
        return f"<DownloadTask(id={self.id}, video_id={self.video_id}, status='{self.status}')>"
