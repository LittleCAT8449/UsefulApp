"""下载任务 Pydantic 模型。"""

from datetime import datetime

from pydantic import BaseModel


class DownloadTaskResponse(BaseModel):
    id: int
    video_id: int
    status: str
    quality: int
    file_size: int | None
    progress: float
    error_message: str
    retry_count: int
    merged_file_path: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
