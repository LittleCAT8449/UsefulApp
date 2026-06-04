"""FastAPI 应用入口 —— 启动/关闭事件、CORS、总路由注册。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.database import init_db, close_db
from app.api.router import api_router
from app.api.websocket import router as ws_router
from app.crawler.engine import crawler_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    # 启动
    logger.info("正在启动 B站追踪服务器...")
    await init_db()
    logger.info("数据库初始化完成")

    # 启动爬虫引擎
    await crawler_engine.start()

    logger.info(f"服务器已启动: http://{settings.host}:{settings.port}")
    logger.info(f"API 文档: http://{settings.host}:{settings.port}/docs")

    yield

    # 关闭
    logger.info("正在关闭服务器...")
    await crawler_engine.stop()
    await close_db()
    logger.info("服务器已关闭")


app = FastAPI(
    title="B站 UP主追踪服务器",
    description="订阅B站UP主更新、爬取视频/文章数据、下载视频，为手机App提供API。",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS —— 允许手机 App 和前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为 App 域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router)
app.include_router(ws_router)


@app.get("/")
async def root():
    """根路径 —— 健康检查。"""
    return {
        "service": "B站 UP主追踪服务器",
        "version": "0.1.0",
        "docs": "/docs",
        "api": "/api/v1",
    }
