"""
Unified Backend Platform - Permission Service

权限管理服务，提供权限验证、缓存和加载功能
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

import redis.asyncio as redis

from app.core.config import get_settings
from app.models.permission import Permission, Role, UserRoleAssignment
from app.models.user import User

settings = get_settings()


class PermissionService:
    """
    权限管理服务

    职责:
    1. 加载和缓存用户权限
    2. 权限检查逻辑
    3. Redis 缓存管理
    """

    def __init__(self) -> None:
        self._redis_client: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        """获取 Redis 客户端"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis_client

    # ==============================================================================
    # 权限加载
    # ==============================================================================

    async def get_user_permissions(
        self,
        user_id: UUID,
        app_identifier: str | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """
        获取用户权限列表 (带缓存)

        Args:
            user_id: 用户 ID
            app_identifier: 应用标识符 (None 表示全局权限)
            force_refresh: 是否强制刷新缓存

        Returns:
            {
                "permissions": ["posts:create", "posts:read", ...],
                "roles": ["editor", "author"],
                "cached_at": "2024-12-24T10:00:00Z",
                "is_superuser": false
            }
        """
        # 检查缓存
        if not force_refresh:
            cached = await self._get_from_cache(user_id, app_identifier)
            if cached:
                return cached

        # 从数据库加载
        permissions = await self._load_permissions_from_db(user_id, app_identifier)

        # 写入缓存
        await self._save_to_cache(user_id, app_identifier, permissions)

        return permissions

    async def _load_permissions_from_db(
        self,
        user_id: UUID,
        app_identifier: str | None = None,
    ) -> dict[str, Any]:
        """从数据库加载用户权限"""
        # 1. 获取用户信息
        user = await User.find_one(User.id == user_id)
        if not user:
            return {
                "permissions": [],
                "roles": [],
                "cached_at": None,
                "is_superuser": False,
            }

        # 超级管理员返回所有权限
        if user.is_superuser:
            all_permissions = await Permission.find_all().to_list()
            return {
                "permissions": [p.name for p in all_permissions],
                "roles": ["superuser"],
                "cached_at": datetime.utcnow().isoformat(),
                "is_superuser": True,
            }

        # 2. 获取用户角色分配（包含全局和应用级角色）
        global_role_filters = [
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.app_identifier == None,
            UserRoleAssignment.is_active == True,
        ]

        app_role_filters = [
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.is_active == True,
        ]

        if app_identifier:
            app_role_filters.append(
                (UserRoleAssignment.app_identifier == None) |
                (UserRoleAssignment.app_identifier == app_identifier)
            )

        # 查询全局和应用级角色
        global_assignments = await UserRoleAssignment.find(
            *global_role_filters
        ).to_list()

        app_assignments = await UserRoleAssignment.find(
            *app_role_filters
        ).to_list()

        # 合并角色分配，去重
        all_assignments = list({a.id: a for a in global_assignments + app_assignments}.values())
        role_ids = list({a.role_id for a in all_assignments})

        if not role_ids:
            return {
                "permissions": [],
                "roles": [],
                "cached_at": datetime.utcnow().isoformat(),
                "is_superuser": False,
            }

        # 3. 获取角色关联的权限
        roles = await Role.find(Role.id.in_(role_ids)).to_list()
        permission_ids = set()
        for role in roles:
            permission_ids.update(role.permission_ids)

        if not permission_ids:
            return {
                "permissions": [],
                "roles": [r.display_name for r in roles],
                "cached_at": datetime.utcnow().isoformat(),
                "is_superuser": False,
            }

        # 4. 解析权限名称
        permissions = await Permission.find(Permission.id.in_(list(permission_ids))).to_list()
        permission_names = [p.name for p in permissions]

        # 5. 添加通配符权限扩展
        permission_names.extend(self._expand_wildcard_permissions(permission_names))

        return {
            "permissions": list(set(permission_names)),
            "roles": [r.display_name for r in roles],
            "cached_at": datetime.utcnow().isoformat(),
            "is_superuser": False,
        }

    def _expand_wildcard_permissions(self, permissions: list[str]) -> list[str]:
        """
        扩展通配符权限

        例如: "posts:*" 会添加 "posts:create", "posts:read", "posts:update", "posts:delete"
        """
        wildcard_actions = ["create", "read", "update", "delete", "list"]
        expanded = []

        for perm in permissions:
            if perm == "*:*":
                # 全局通配符，返回所有常见权限 (必须先检查)
                resources = ["posts", "records", "files", "users", "permissions", "roles"]
                for resource in resources:
                    expanded.extend([f"{resource}:{action}" for action in wildcard_actions])
            elif perm.endswith(":*"):
                resource = perm[:-2]
                expanded.extend([f"{resource}:{action}" for action in wildcard_actions])

        return expanded

    # ==============================================================================
    # 权限检查
    # ==============================================================================

    def check_permission(
        self,
        user_permissions: dict[str, Any],
        required_permission: str,
        resource_type: str | None = None,
    ) -> bool:
        """
        检查用户是否拥有所需权限

        Args:
            user_permissions: 用户权限字典
            required_permission: 所需权限 (如 "posts:create")
            resource_type: 资源类型限制 (保留参数，暂未使用)

        Returns:
            bool: 是否拥有权限
        """
        # 超级管理员
        if user_permissions.get("is_superuser"):
            return True

        permissions = user_permissions.get("permissions", [])

        # 1. 精确匹配
        if required_permission in permissions:
            return True

        # 2. 通配符匹配
        if ":" in required_permission:
            resource, action = required_permission.split(":", 1)

            # 检查资源级通配符 (如 posts:*)
            if f"{resource}:*" in permissions:
                return True

            # 检查全局通配符
            if "*:*" in permissions:
                return True

        return False

    async def check_multiple_permissions(
        self,
        user_id: UUID,
        required_permissions: list[str],
        app_identifier: str | None = None,
    ) -> dict[str, bool]:
        """
        批量检查多个权限

        Args:
            user_id: 用户 ID
            required_permissions: 需要检查的权限列表
            app_identifier: 应用标识符

        Returns:
            {"posts:create": True, "posts:delete": False}
        """
        user_perms = await self.get_user_permissions(user_id, app_identifier)

        return {
            perm: self.check_permission(user_perms, perm)
            for perm in required_permissions
        }

    # ==============================================================================
    # Redis 缓存管理
    # ==============================================================================

    async def _get_from_cache(
        self,
        user_id: UUID,
        app_identifier: str | None = None,
    ) -> dict[str, Any] | None:
        """从 Redis 获取缓存"""
        try:
            r = await self._get_redis()
            key = self._make_cache_key(user_id, app_identifier)
            data = await r.get(key)

            if data:
                return json.loads(data)
        except Exception as e:
            # Redis 连接失败时降级，直接从数据库加载
            print(f"Redis cache error: {e}")

        return None

    async def _save_to_cache(
        self,
        user_id: UUID,
        app_identifier: str | None = None,
        permissions: dict[str, Any] | None = None,
    ) -> None:
        """保存到 Redis 缓存"""
        try:
            r = await self._get_redis()
            key = self._make_cache_key(user_id, app_identifier)

            if permissions:
                await r.setex(
                    key,
                    settings.redis_cache_ttl,
                    json.dumps(permissions),
                )
        except Exception as e:
            print(f"Redis cache save error: {e}")

    async def invalidate_user_cache(
        self,
        user_id: UUID,
        app_identifier: str | None = None,
    ) -> None:
        """
        使用户权限缓存失效

        Args:
            user_id: 用户 ID
            app_identifier: 应用标识符 (None 表示清除所有缓存)
        """
        try:
            r = await self._get_redis()

            if app_identifier is None:
                # 清除用户所有缓存
                pattern = self._make_cache_key(user_id, None)
                # 将 {user_id} 替换为通配符模式
                pattern = pattern.replace(f":{user_id}", f":{user_id}*")
                keys = await r.keys(pattern)
                if keys:
                    await r.delete(*keys)
            else:
                # 清除特定应用的缓存
                key = self._make_cache_key(user_id, app_identifier)
                await r.delete(key)
        except Exception as e:
            print(f"Redis cache invalidation error: {e}")

    def _make_cache_key(self, user_id: UUID, app_identifier: str | None = None) -> str:
        """生成缓存键"""
        app_suffix = f":{app_identifier}" if app_identifier else ""
        return f"permissions:{user_id}{app_suffix}"

    async def close(self) -> None:
        """关闭 Redis 连接"""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
