"""全局配置 —— 使用 pydantic-settings 从 .env 加载。"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./data/bilibili_tracker.db"

    # 安全
    secret_key: str = "change-me-to-a-random-secret-key"
    device_pair_code: str = "123456"
    auth_enabled: bool = False  # 设为 true 启用 JWT 认证
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 30  # 30 天

    # 爬虫
    check_interval_minutes: int = 30
    rate_limit_per_second: int = 3
    rate_limit_burst: int = 5

    # 下载
    download_path: str = "./data/downloads"
    cover_path: str = "./data/covers"
    max_concurrent_downloads: int = 2
    auto_download_new_videos: bool = False
    max_retry_count: int = 3

    # 日志
    log_level: str = "INFO"

    # B站 Cookie（可选，用于高画质下载）
    bilibili_sessdata: str = ""
    bilibili_bili_jct: str = ""

    # 服务器
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()

# 确保数据目录存在
Path(settings.download_path).mkdir(parents=True, exist_ok=True)
Path(settings.cover_path).mkdir(parents=True, exist_ok=True)
