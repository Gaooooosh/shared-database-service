"""
Unified Backend Platform - Security & Authentication

实现 JWT 验证和 Casdoor 集成
支持 RS256 (证书模式) 和 HS256 (共享密钥模式)
"""
from datetime import datetime
from typing import Any
from uuid import UUID

import httpx
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models.user import User

settings = get_settings()


# =============================================================================
# JWKS 公钥获取器 (RS256 模式)
# =============================================================================
class JWKSFetcher:
    """
    从 Casdoor JWKS 端点获取公钥

    JWKS (JSON Web Key Set) 是一种存储公钥的标准格式
    Casdoor 通过 /.well-known/jwks 端点暴露公钥
    """

    def __init__(self, jwks_url: str):
        self.jwks_url = jwks_url
        self._public_keys: dict[str, Any] = {}  # kid -> 公钥缓存
        self._last_fetch: float = 0
        self._cache_ttl: int = 3600  # 缓存1小时

    async def get_public_key(self, kid: str | None = None) -> Any:
        """
        获取 RSA 公钥

        Args:
            kid: Key ID (JWT header中的kid字段)

        Returns:
            RSA 公钥对象 (jwk.RSAKey)

        Raises:
            JWTError: 无法获取公钥
        """
        # 检查缓存
        if kid and kid in self._public_keys:
            return self._public_keys[kid]

        # 检查是否需要刷新缓存
        import time

        current_time = time.time()
        if self._public_keys and (current_time - self._last_fetch) < self._cache_ttl:
            # 缓存有效，返回第一个公钥（如果没有指定kid）
            if not kid:
                return next(iter(self._public_keys.values()))

        # 从 Casdoor 获取最新公钥
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
                jwks_data = response.json()

                # 解析并缓存公钥
                for key_data in jwks_data.get("keys", []):
                    # 构建 RSA 公钥
                    rsa_key = jwk.construct(key_data)
                    kid_value = key_data.get("kid")
                    if kid_value:
                        self._public_keys[kid_value] = rsa_key

                self._last_fetch = current_time

                # 返回请求的公钥
                if kid:
                    if kid not in self._public_keys:
                        raise JWTError(f"Public key with kid '{kid}' not found")
                    return self._public_keys[kid]

                # 返回第一个公钥
                if self._public_keys:
                    return next(iter(self._public_keys.values()))

                raise JWTError("No public keys found in JWKS")

        except httpx.HTTPError as e:
            raise JWTError(f"Failed to fetch JWKS: {str(e)}") from e
        except Exception as e:
            raise JWTError(f"Error parsing JWKS: {str(e)}") from e

    def clear_cache(self):
        """清除公钥缓存"""
        self._public_keys.clear()
        self._last_fetch = 0


# 全局 JWKS 获取器实例
_jwks_fetcher: JWKSFetcher | None = None


def get_jwks_fetcher() -> JWKSFetcher:
    """获取 JWKS 获取器单例"""
    global _jwks_fetcher
    if _jwks_fetcher is None:
        _jwks_fetcher = JWKSFetcher(settings.casdoor_jwks_url)
    return _jwks_fetcher


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
# JWT 验证 (支持 RS256 和 HS256)
# =============================================================================
async def decode_jwt_token(token: str) -> JWTPayload:
    """
    解码并验证 JWT Token (异步版本)

    支持:
    - RS256: 从 Casdoor JWKS 获取公钥验证
    - HS256: 使用共享密钥验证

    Args:
        token: Bearer Token (不含 "Bearer " 前缀)

    Returns:
        JWTPayload: 解码后的 payload

    Raises:
        JWTError: Token 无效或过期

    注意:
        此函数是异步的，避免事件循环冲突
    """
    try:
        # 获取 JWT header（不含验证）以确定算法和kid
        header = jwt.get_unverified_header(token)

        # 根据配置的算法选择验证方式
        if settings.jwt_algorithm == "RS256":
            # RS256 模式：使用公钥验证
            kid = header.get("kid")

            # ✅ 异步从 JWKS 获取公钥
            fetcher = get_jwks_fetcher()
            public_key = await fetcher.get_public_key(kid)

            if not public_key:
                raise JWTError(f"Public key not found for kid: {kid}")

            # 使用公钥验证 JWT
            payload = jwt.decode(
                token,
                public_key.to_pem().decode('utf-8') if hasattr(public_key.to_pem(), 'decode') else public_key.to_pem(),
                algorithms=[settings.jwt_algorithm],
                options={"verify_aud": False},  # Casdoor JWT 可能不包含 aud
            )

        else:  # HS256
            # HS256 模式：使用共享密钥验证
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )

        return JWTPayload(**payload)

    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}") from e
    except Exception as e:
        raise JWTError(f"Error decoding token: {str(e)}") from e


async def validate_token(token: str) -> JWTPayload:
    """
    验证 Token 并返回 payload (异步版本)

    这是 FastAPI Dependency 的核心函数

    Args:
        token: Authorization header 值 (可能包含 "Bearer " 前缀)

    Returns:
        JWTPayload: 解码后的 payload

    Raises:
        JWTError: Token 无效或过期
    """
    # 移除可能的 "Bearer " 前缀
    if token.startswith("Bearer "):
        token = token[7:]

    return await decode_jwt_token(token)


# =============================================================================
# 用户同步逻辑 - 完全基于 Casdoor
# =============================================================================
async def sync_user_from_casdoor(payload: JWTPayload) -> User:
    """
    从 Casdoor 同步用户信息（每次登录都更新）

    Args:
        payload: 解码后的 JWT payload

    Returns:
        User: 本地用户实例（信息完全同步自 Casdoor）

    说明：
        - 用户信息完全由 Casdoor 管理
        - 本地数据库仅存储映射关系和缓存
        - 每次登录都从 Casdoor 同步最新信息
    """
    # 根据 casdoor_id 查找本地用户记录
    user = await User.find_one(User.casdoor_id == payload.sub)

    if user:
        # 🔥 更新用户信息（从 Casdoor JWT 获取最新数据）
        user.email = payload.email or f"{payload.sub}@casdoor"
        user.display_name = payload.name
        user.avatar = payload.avatar
        user.update_last_login()
        await user.save()
    else:
        # 首次登录，创建本地用户记录
        user = User(
            casdoor_id=payload.sub,
            email=payload.email or f"{payload.sub}@casdoor",
            display_name=payload.name,
            avatar=payload.avatar,
            is_superuser=False,  # 超级管理员由 Casdoor 管理
            last_login_at=datetime.utcnow(),
        )
        await user.insert()

    # ===== 同步 Casdoor 权限组到本地角色 =====
    try:
        from app.services.casdoor_sync_service import CasdoorSyncService
        from app.services.permission_service import PermissionService

        sync_service = CasdoorSyncService()
        perm_service = PermissionService()

        # 从 Casdoor 获取用户的权限组并同步到本地
        sync_result = await sync_service.sync_groups_to_local_roles(
            user_id=user.id,
            casdoor_user_id=payload.sub,
            app_identifier=None,  # 全局权限
            email=payload.email,  # 传入邮箱用于 UUID 查询
        )

        # 清除用户权限缓存，确保使用最新权限
        await perm_service.invalidate_user_cache(user.id)

        print(f"✅ User synced from Casdoor: {payload.name} | Roles: {sync_result.get('groups', [])}")

    except Exception as e:
        # 权限同步失败不应阻止用户登录
        print(f"⚠️  Error syncing Casdoor permissions: {e}")

    return user


# 兼容旧代码的别名
async def get_or_create_user_from_jwt(payload: JWTPayload) -> User:
    """兼容函数 - 实际调用 sync_user_from_casdoor"""
    return await sync_user_from_casdoor(payload)


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
        # ✅ 异步解析并验证 JWT
        payload = await validate_token(authorization)

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
        payload = await validate_token(authorization)
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
