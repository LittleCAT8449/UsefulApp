"""专栏文章 Pydantic 模型。"""

from datetime import datetime

from pydantic import BaseModel


class ArticleResponse(BaseModel):
    id: int
    cv_id: int
    up_user_id: int
    title: str
    summary: str
    cover_url: str
    cover_local_path: str
    content: str
    view_count: int
    like_count: int
    coin_count: int
    reply_count: int
    favorite_count: int
    share_count: int
    words_count: int
    pubdate: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ArticleListResponse(BaseModel):
    """文章列表项（精简）。"""
    id: int
    cv_id: int
    title: str
    summary: str
    cover_url: str
    cover_local_path: str
    view_count: int
    like_count: int
    words_count: int
    pubdate: datetime | None

    model_config = {"from_attributes": True}
