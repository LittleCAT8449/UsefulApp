"""FastAPI 依赖注入 —— DB session, auth。"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings

# Bearer Token 安全方案
security = HTTPBearer(auto_error=False)

# 是否启用认证（可在 .env 中设置 AUTH_ENABLED=true 开启）
AUTH_ENABLED: bool = settings.auth_enabled


async def get_current_client(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """验证客户端身份，返回 client_id。

    当 AUTH_ENABLED=False 时免认证（开发模式）。
    当 AUTH_ENABLED=True 时需要有效的 JWT Bearer Token。
    """
    if not AUTH_ENABLED:
        return "anonymous"

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    from app.api.auth import verify_access_token
    return verify_access_token(credentials.credentials)


# 导出 get_db 方便路由使用
get_db = get_db
