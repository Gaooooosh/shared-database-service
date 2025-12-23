"""
Unified Backend Platform - Security & Authentication

实现 JWT 验证和 Casdoor 集成
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models.user import User

settings = get_settings()


# =============================================================================
# JWT 数据模型
# =============================================================================
class JWTPayload(BaseModel):
    """JWT Token 负载数据 (Casdoor 标准格式)"""

    sub: str = Field(..., description="Subject - 通常是 Casdoor 用户 ID")
    name: str | None = Field(default=None, description="用户名称")
    email: str | None = Field(default=None, description="用户邮箱")
    avatar: str | None = Field(default=None, description="头像 URL")
    exp: int = Field(..., description="过期时间 (Unix timestamp)")
    iss: str = Field(..., description="签发者 (Casdoor)")


# =============================================================================
# JWT 验证
# =============================================================================
def decode_jwt_token(token: str) -> JWTPayload:
    """
    解码并验证 JWT Token

    Args:
        token: Bearer Token (不含 "Bearer " 前缀)

    Returns:
        JWTPayload: 解码后的 payload

    Raises:
        JWTError: Token 无效或过期
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return JWTPayload(**payload)
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}") from e


def validate_token(token: str) -> JWTPayload:
    """
    验证 Token 并返回 payload

    这是 FastAPI Dependency 的核心函数
    """
    # 移除可能的 "Bearer " 前缀
    if token.startswith("Bearer "):
        token = token[7:]

    return decode_jwt_token(token)


# =============================================================================
# 用户同步逻辑
# =============================================================================
async def get_or_create_user_from_jwt(payload: JWTPayload) -> User:
    """
    根据 JWT payload 查找或创建本地用户

    Args:
        payload: 解码后的 JWT payload

    Returns:
        User: 本地用户实例
    """
    # 根据 casdoor_id 查找
    user = await User.find_one(User.casdoor_id == payload.sub)

    if user:
        # 更新最后登录时间
        user.update_last_login()
        await user.save()
        return user

    # 用户不存在，创建新用户
    new_user = User(
        casdoor_id=payload.sub,
        email=payload.email or f"{payload.sub}@casdoor",
        display_name=payload.name,
        avatar=payload.avatar,
        role="user",  # 默认角色，后续可通过管理后台调整
        last_login_at=datetime.utcnow(),
    )
    await new_user.insert()
    return new_user


# =============================================================================
# FastAPI Dependencies
# =============================================================================
from fastapi import Depends, Header, HTTPException, status


async def get_current_user(
    authorization: str = Header(..., description="Authorization header (Bearer token)"),
) -> User:
    """
    FastAPI Dependency - 获取当前认证用户

    Usage:
        from app.core.security import get_current_user

        @app.get("/api/v1/profile")
        async def get_profile(current_user: User = Depends(get_current_user)):
            return current_user

    Args:
        authorization: HTTP Authorization Header

    Returns:
        User: 当前认证用户

    Raises:
        HTTPException 401: Token 无效或用户未找到
    """
    try:
        # 解析并验证 JWT
        payload = validate_token(authorization)

        # 查找或创建本地用户
        user = await get_or_create_user_from_jwt(payload)
        return user

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user_optional(
    authorization: str | None = Header(None, description="Authorization header (optional)"),
) -> User | None:
    """
    可选的用户认证 - 允许匿名访问

    如果提供有效 Token 则返回用户，否则返回 None
    """
    if not authorization:
        return None

    try:
        payload = validate_token(authorization)
        return await get_or_create_user_from_jwt(payload)
    except (JWTError, Exception):
        return None


# =============================================================================
# 角色检查辅助函数
# =============================================================================
class RoleChecker:
    """角色检查器 - FastAPI Dependency"""

    def __init__(self, required_roles: list[str]) -> None:
        self.required_roles = required_roles

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """检查用户是否拥有所需角色"""
        if current_user.role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required roles: {self.required_roles}",
            )
        return current_user


# 预定义角色检查器
require_admin = RoleChecker(required_roles=["admin"])
require_admin_or_user = RoleChecker(required_roles=["admin", "user"])
