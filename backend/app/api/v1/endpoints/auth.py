"""
Unified Backend Platform - Authentication Endpoints

认证相关 API 端点
"""
from typing import Any

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    获取当前登录用户的信息

    需要 Bearer Token (从 Casdoor 获取)

    Returns:
        用户基本信息
    """
    # 获取用户的权限信息
    from app.services.permission_service import PermissionService
    perm_service = PermissionService()
    user_permissions = await perm_service.get_user_permissions(current_user.id)

    return {
        "id": str(current_user.id),
        "casdoor_id": current_user.casdoor_id,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "avatar": current_user.avatar,
        "is_superuser": current_user.is_superuser,
        "is_active": current_user.is_active,
        "primary_role_id": str(current_user.primary_role_id) if current_user.primary_role_id else None,
        "permissions": user_permissions.get("permissions", []),
        "roles": user_permissions.get("roles", []),
        "created_at": current_user.created_at,
        "last_login_at": current_user.last_login_at,
    }


@router.post("/refresh", summary="刷新用户信息")
async def refresh_user_info(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    刷新并同步当前用户信息

    通常在从 Casdoor 登录后调用，确保本地用户数据最新

    Returns:
        更新后的用户信息
    """
    # 更新最后登录时间
    current_user.update_last_login()
    await current_user.save()

    # 获取用户的权限信息
    from app.services.permission_service import PermissionService
    perm_service = PermissionService()
    user_permissions = await perm_service.get_user_permissions(current_user.id)

    return {
        "id": str(current_user.id),
        "casdoor_id": current_user.casdoor_id,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "avatar": current_user.avatar,
        "is_superuser": current_user.is_superuser,
        "last_login_at": current_user.last_login_at,
        "permissions": user_permissions.get("permissions", []),
        "roles": user_permissions.get("roles", []),
    }
