"""通用 Pydantic 模型 —— 分页、错误响应。"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应。"""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """错误响应。"""
    detail: str
    code: int = 400


class MessageResponse(BaseModel):
    """消息响应。"""
    message: str
