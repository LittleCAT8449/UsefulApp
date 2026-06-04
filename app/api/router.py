"""总路由注册 —— 将所有子路由挂载到 /api/v1 下。"""

from fastapi import APIRouter

from app.api import up_users, videos, articles, downloads, notifications, system, websocket, auth
from app.api.up_videos import router as up_videos_router
from app.api.up_articles import router as up_articles_router
from app.api.files import router as files_router

api_router = APIRouter(prefix="/api/v1")

# 认证
api_router.include_router(auth.router)

# UP主管理
api_router.include_router(up_users.router)

# 视频
api_router.include_router(videos.router)
api_router.include_router(up_videos_router, prefix="/up")

# 专栏文章
api_router.include_router(articles.router)
api_router.include_router(up_articles_router, prefix="/up")

# 下载管理
api_router.include_router(downloads.router)

# 通知
api_router.include_router(notifications.router)

# 系统
api_router.include_router(system.router)

# 文件服务
api_router.include_router(files_router, prefix="/files")
