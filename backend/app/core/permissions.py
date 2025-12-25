"""
Unified Backend Platform - Permission Checkers

FastAPI 权限验证装饰器，提供细粒度的权限检查
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User
from app.services.permission_service import PermissionService


# =============================================================================
# 权限检查器
# =============================================================================

class PermissionChecker:
    """
    权限检查器 - FastAPI Dependency

    检查用户是否拥有指定的权限
    """

    def __init__(
        self,
        required_permission: str,
        app_identifier: str | None = None,
    ) -> None:
        """
        初始化权限检查器

        Args:
            required_permission: 所需权限 (如 "posts:create", "posts:*")
            app_identifier: 应用标识符 (用于应用级隔离)
        """
        self.required_permission = required_permission
        self.app_identifier = app_identifier

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        检查用户是否拥有所需权限

        Args:
            current_user: 当前认证用户

        Returns:
            User: 用户对象

        Raises:
            HTTPException 403: 权限不足
        """
        # 超级管理员直接通过
        if current_user.is_superuser:
            return current_user

        # 获取权限服务实例
        permission_service = PermissionService()

        # 加载用户权限
        user_permissions = await permission_service.get_user_permissions(
            user_id=current_user.id,
            app_identifier=self.app_identifier,
        )

        # 检查权限
        has_permission = permission_service.check_permission(
            user_permissions=user_permissions,
            required_permission=self.required_permission,
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {self.required_permission}",
            )

        return current_user


class AnyPermissionChecker:
    """
    多权限检查器 - 满足任一权限即可

    检查用户是否拥有列表中的任一权限
    """

    def __init__(
        self,
        permissions: list[str],
        app_identifier: str | None = None,
    ) -> None:
        """
        初始化多权限检查器

        Args:
            permissions: 权限列表 (满足任一即可)
            app_identifier: 应用标识符
        """
        self.permissions = permissions
        self.app_identifier = app_identifier

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        检查用户是否拥有列表中的任一权限

        Args:
            current_user: 当前认证用户

        Returns:
            User: 用户对象

        Raises:
            HTTPException 403: 权限不足
        """
        # 超级管理员直接通过
        if current_user.is_superuser:
            return current_user

        permission_service = PermissionService()
        user_permissions = await permission_service.get_user_permissions(
            user_id=current_user.id,
            app_identifier=self.app_identifier,
        )

        # 检查是否拥有任一权限
        has_any = any(
            permission_service.check_permission(user_permissions, perm)
            for perm in self.permissions
        )

        if not has_any:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires one of {self.permissions}",
            )

        return current_user


class AllPermissionChecker:
    """
    多权限检查器 - 需要拥有所有权限

    检查用户是否拥有列表中的所有权限
    """

    def __init__(
        self,
        permissions: list[str],
        app_identifier: str | None = None,
    ) -> None:
        """
        初始化多权限检查器

        Args:
            permissions: 权限列表 (需要全部满足)
            app_identifier: 应用标识符
        """
        self.permissions = permissions
        self.app_identifier = app_identifier

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        检查用户是否拥有列表中的所有权限

        Args:
            current_user: 当前认证用户

        Returns:
            User: 用户对象

        Raises:
            HTTPException 403: 权限不足
        """
        # 超级管理员直接通过
        if current_user.is_superuser:
            return current_user

        permission_service = PermissionService()
        user_permissions = await permission_service.get_user_permissions(
            user_id=current_user.id,
            app_identifier=self.app_identifier,
        )

        # 检查是否拥有所有权限
        has_all = all(
            permission_service.check_permission(user_permissions, perm)
            for perm in self.permissions
        )

        if not has_all:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires all of {self.permissions}",
            )

        return current_user


# =============================================================================
# 便捷权限依赖工厂函数
# =============================================================================

def require_permission(
    permission: str,
    app_identifier: str | None = None,
) -> PermissionChecker:
    """
    要求特定权限

    Usage:
        @router.post("/posts")
        async def create_post(
            user: User = Depends(require_permission("posts:create", "blog-app"))
        ):
            ...

    Args:
        permission: 所需权限 (如 "posts:create")
        app_identifier: 应用标识符 (可选)

    Returns:
        PermissionChecker: 权限检查器实例
    """
    return PermissionChecker(
        required_permission=permission,
        app_identifier=app_identifier,
    )


def require_any_permission(
    permissions: list[str],
    app_identifier: str | None = None,
) -> AnyPermissionChecker:
    """
    要求任一权限

    Usage:
        @router.put("/posts/{id}")
        async def update_post(
            user: User = Depends(require_any_permission(
                ["posts:update", "posts:edit"], "blog-app"
            ))
        ):
            ...

    Args:
        permissions: 权限列表
        app_identifier: 应用标识符 (可选)

    Returns:
        AnyPermissionChecker: 权限检查器实例
    """
    return AnyPermissionChecker(
        permissions=permissions,
        app_identifier=app_identifier,
    )


def require_all_permissions(
    permissions: list[str],
    app_identifier: str | None = None,
) -> AllPermissionChecker:
    """
    要求所有权限

    Usage:
        @router.delete("/posts/{id}")
        async def delete_post(
            user: User = Depends(require_all_permissions(
                ["posts:delete", "posts:manage"], "blog-app"
            ))
        ):
            ...

    Args:
        permissions: 权限列表
        app_identifier: 应用标识符 (可选)

    Returns:
        AllPermissionChecker: 权限检查器实例
    """
    return AllPermissionChecker(
        permissions=permissions,
        app_identifier=app_identifier,
    )


# =============================================================================
# 特殊权限检查器
# =============================================================================

def require_superuser() -> PermissionChecker:
    """
    要求超级管理员权限

    Usage:
        @router.get("/admin/stats")
        async def get_admin_stats(
            user: User = Depends(require_superuser())
        ):
            ...

    Returns:
        PermissionChecker: 权限检查器实例
    """
    return require_permission("*:*")


# =============================================================================
# 类型别名
# =============================================================================

# 常用权限类型别名
RequireAuth = Annotated[User, Depends(get_current_user)]
RequireSuperuser = Annotated[User, Depends(require_superuser())]
