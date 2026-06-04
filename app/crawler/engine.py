"""爬虫调度引擎 —— 定时检查所有活跃 UP主的更新。"""

import asyncio
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_factory
from app.models import UpUser, Video, Article, Notification
from app.crawler.up_crawler import fetch_up_info
from app.crawler.video_crawler import (
    fetch_video_list,
    fetch_video_detail,
    parse_video_list_item,
    parse_video_detail,
)
from app.crawler.article_crawler import (
    fetch_article_list,
    parse_article_list_item,
)
from app.crawler.cover_downloader import download_cover, get_cover_filename, get_article_cover_filename


class CrawlerEngine:
    """爬虫引擎 —— 负责定时遍历所有 UP主并检查更新。"""

    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """启动爬虫循环。"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("爬虫引擎已启动")

    async def stop(self) -> None:
        """停止爬虫循环。"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("爬虫引擎已停止")

    async def _loop(self) -> None:
        """主循环 —— 每 N 分钟执行一次检查。"""
        while self._running:
            try:
                await self._check_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"爬虫循环异常: {e}")

            # 等待下一次检查
            interval = settings.check_interval_minutes * 60
            logger.info(f"下次检查将在 {settings.check_interval_minutes} 分钟后")
            try:
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break

    async def _check_all(self) -> None:
        """检查所有活跃 UP主。"""
        async with async_session_factory() as db:
            result = await db.execute(
                select(UpUser)
                .where(UpUser.is_active == True)
                .order_by(UpUser.last_checked_at.asc().nullsfirst())
            )
            up_users = result.scalars().all()

        if not up_users:
            logger.info("没有活跃的 UP主需要检查")
            return

        logger.info(f"开始检查 {len(up_users)} 个 UP主")
        stats = {"up_updated": 0, "new_videos": 0, "updated_videos": 0, "new_articles": 0, "errors": 0}

        for up_user in up_users:
            try:
                counts = await self._check_up_user(up_user.id, up_user.bilibili_uid)
                if counts["up_updated"]:
                    stats["up_updated"] += 1
                stats["new_videos"] += counts["new_videos"]
                stats["updated_videos"] += counts["updated_videos"]
                stats["new_articles"] += counts["new_articles"]
            except Exception as e:
                logger.exception(f"检查 UP主失败 (uid={up_user.bilibili_uid}): {e}")
                stats["errors"] += 1

            # UP主之间的间隔
            await asyncio.sleep(1.0)

        logger.info(
            f"检查完成: UP更新={stats['up_updated']}, "
            f"新视频={stats['new_videos']}, 视频更新={stats['updated_videos']}, "
            f"新文章={stats['new_articles']}, 错误={stats['errors']}"
        )

    async def _check_up_user(self, db_id: int, bilibili_uid: int) -> dict:
        """检查单个 UP主。

        Returns:
            统计数据字典。
        """
        counts = {"up_updated": 0, "new_videos": 0, "updated_videos": 0, "new_articles": 0}

        async with async_session_factory() as db:
            up_user = await db.get(UpUser, db_id)
            if not up_user:
                return counts

            now = datetime.now(timezone.utc).replace(tzinfo=None)

            # 1. 更新 UP主基本信息
            up_data = await fetch_up_info(bilibili_uid)
            if up_data:
                up_user.name = up_data.get("name", up_user.name)
                up_user.face_url = up_data.get("face", up_user.face_url)
                up_user.sign = up_data.get("sign", up_user.sign)
                up_user.level = up_data.get("level", up_user.level)
                up_user.sex = up_data.get("sex", up_user.sex)
                up_user.follower_count = up_data.get("follower", 0) or up_data.get("follower_count", 0)
                up_user.following_count = up_data.get("following", 0) or up_data.get("following_count", 0)
                up_user.video_count = up_data.get("video_count", up_user.video_count)
                counts["up_updated"] = 1

            # 2. 检查新视频
            existing_bvids = await self._get_existing_bvids(db, db_id)

            page = 1
            while True:
                vlist = await fetch_video_list(bilibili_uid, page=page, page_size=50)
                if not vlist:
                    break

                all_old = True
                for item in vlist:
                    bvid = item.get("bvid", "")
                    if not bvid:
                        continue

                    if bvid in existing_bvids:
                        continue  # 已存在的视频
                    all_old = False

                    # 新视频 —— 获取详情 + 下载封面
                    detail = await fetch_video_detail(bvid)
                    video_data = parse_video_list_item(item)
                    if detail:
                        video_data.update(parse_video_detail(detail))

                    video = Video(
                        up_user_id=db_id,
                        bvid=bvid,
                        **{k: v for k, v in video_data.items() if k != "bvid"},
                    )
                    db.add(video)
                    existing_bvids.add(bvid)

                    # 下载封面
                    if video_data.get("cover_url"):
                        cover_path = await download_cover(
                            video_data["cover_url"],
                            get_cover_filename(bvid),
                        )
                        video.cover_local_path = cover_path or ""

                    # 创建通知
                    if up_user.notify_new_video:
                        db.add(Notification(
                            type="new_video",
                            title=f"新视频: {video_data.get('title', '')}",
                            message=f"UP主 {up_user.name} 发布了新视频「{video_data.get('title', '')}」",
                            reference_type="video",
                            up_user_id=db_id,
                            metadata_={
                                "bvid": bvid,
                                "cover_url": video_data.get("cover_url", ""),
                                "up_name": up_user.name,
                            },
                        ))

                    counts["new_videos"] += 1
                    logger.info(f"发现新视频: {bvid} - {video_data.get('title', '')}")

                if all_old or len(vlist) < 50:
                    break
                page += 1
                await asyncio.sleep(0.5)

            # 3. 检查新文章
            existing_cvids = await self._get_existing_cvids(db, db_id)

            page = 1
            while True:
                alist = await fetch_article_list(bilibili_uid, page=page, page_size=12)
                if not alist:
                    break

                all_old = True
                for item in alist:
                    cv_id = item.get("id", 0)
                    if not cv_id or cv_id in existing_cvids:
                        continue
                    all_old = False

                    article_data = parse_article_list_item(item)
                    article = Article(
                        up_user_id=db_id,
                        cv_id=cv_id,
                        **{k: v for k, v in article_data.items() if k != "cv_id"},
                    )
                    db.add(article)
                    existing_cvids.add(cv_id)

                    # 下载封面
                    if article_data.get("cover_url"):
                        cover_path = await download_cover(
                            article_data["cover_url"],
                            get_article_cover_filename(cv_id),
                        )
                        article.cover_local_path = cover_path or ""

                    # 创建通知
                    if up_user.notify_new_article:
                        db.add(Notification(
                            type="new_article",
                            title=f"新文章: {article_data.get('title', '')}",
                            message=f"UP主 {up_user.name} 发布了新文章「{article_data.get('title', '')}」",
                            reference_type="article",
                            up_user_id=db_id,
                            metadata_={
                                "cv_id": cv_id,
                                "cover_url": article_data.get("cover_url", ""),
                                "up_name": up_user.name,
                            },
                        ))

                    counts["new_articles"] += 1
                    logger.info(f"发现新文章: cv{cv_id} - {article_data.get('title', '')}")

                if all_old or len(alist) < 12:
                    break
                page += 1
                await asyncio.sleep(0.5)

            # 更新最后检查时间
            up_user.last_checked_at = now
            await db.commit()

        return counts

    @staticmethod
    async def _get_existing_bvids(db: AsyncSession, up_user_id: int) -> set[str]:
        result = await db.execute(
            select(Video.bvid).where(Video.up_user_id == up_user_id)
        )
        return set(result.scalars().all())

    @staticmethod
    async def _get_existing_cvids(db: AsyncSession, up_user_id: int) -> set[int]:
        result = await db.execute(
            select(Article.cv_id).where(Article.up_user_id == up_user_id)
        )
        return set(result.scalars().all())


# 全局单例
crawler_engine = CrawlerEngine()
