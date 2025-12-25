"""
Unified Backend Platform - Permission Management Endpoints

权限管理 API 端点
"""
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.schemas.permission import (
    AssignRoleRequest,
    BulkPermissionCreate,
    BulkRoleCreate,
    PermissionCheckRequest,
    PermissionCheckResponse,
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    RoleCreate,
    PermissionFilter,
    RoleFilter,
    RolePermissionUpdate,
    RoleResponse,
    RoleUpdate,
    UserPermissionsResponse,
)
from app.core.permissions import require_permission, require_superuser, RequireSuperuser
from app.models.permission import Permission, Role, UserRoleAssignment
from app.models.user import User
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["Permissions"])


# =============================================================================
# Permission Endpoints - 权限定义管理
# =============================================================================

@router.post(
    "",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建权限",
)
async def create_permission(
    data: PermissionCreate,
    current_user: RequireSuperuser,
) -> Permission:
    """
    创建新权限

    需要超级管理员权限
    """
    # 检查权限名称是否已存在
    existing = await Permission.find_one(Permission.name == data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permission with name '{data.name}' already exists",
        )

    permission = Permission(
        **data.model_dump(),
        is_system=False,
    )
    await permission.insert()
    return permission


@router.get("", response_model=list[PermissionResponse], summary="查询权限列表")
async def list_permissions(
    app_identifier: str | None = Query(None, description="应用标识符"),
    resource_type: str | None = Query(None, description="资源类型"),
    is_system: bool | None = Query(None, description="是否系统权限"),
    current_user: User = Depends(require_permission("permissions:read")),
) -> list[Permission]:
    """
    查询权限列表

    支持按应用标识符、资源类型、系统权限过滤
    """
    filters = []
    if app_identifier:
        filters.append(Permission.app_identifier == app_identifier)
    if resource_type:
        filters.append(Permission.resource_type == resource_type)
    if is_system is not None:
        filters.append(Permission.is_system == is_system)

    if filters:
        return await Permission.find_many(*filters).sort("+name").to_list()
    return await Permission.find_all().sort("+name").to_list()


@router.get("/{permission_id}", response_model=PermissionResponse, summary="获取权限详情")
async def get_permission(
    permission_id: UUID,
    current_user: User = Depends(require_permission("permissions:read")),
) -> Permission:
    """获取权限详情"""
    permission = await Permission.find_one(Permission.id == permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    return permission


@router.put("/{permission_id}", response_model=PermissionResponse, summary="更新权限")
async def update_permission(
    permission_id: UUID,
    data: PermissionUpdate,
    current_user: RequireSuperuser,
) -> Permission:
    """
    更新权限

    系统权限不可修改
    """
    permission = await Permission.find_one(Permission.id == permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )

    if permission.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System permissions cannot be modified",
        )

    # 更新字段
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(permission, field, value)

    await permission.save()
    return permission


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除权限")
async def delete_permission(
    permission_id: UUID,
    current_user: RequireSuperuser,
) -> None:
    """
    删除权限

    系统权限不可删除
    """
    permission = await Permission.find_one(Permission.id == permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )

    if permission.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System permissions cannot be deleted",
        )

    await permission.delete()


@router.post("/bulk", response_model=list[PermissionResponse], summary="批量创建权限")
async def bulk_create_permissions(
    data: BulkPermissionCreate,
    current_user: RequireSuperuser,
) -> list[Permission]:
    """批量创建权限"""
    permissions = []
    for perm_data in data.permissions:
        # 检查是否已存在
        existing = await Permission.find_one(Permission.name == perm_data.name)
        if existing:
            continue

        permission = Permission(
            **perm_data.model_dump(),
            is_system=False,
        )
        await permission.insert()
        permissions.append(permission)

    return permissions


# =============================================================================
# Role Endpoints - 角色管理
# =============================================================================

@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建角色",
)
async def create_role(
    data: RoleCreate,
    current_user: User = Depends(require_permission("roles:create")),
) -> Role:
    """创建新角色"""
    # 检查角色名称是否已存在
    existing = await Role.find_one(Role.name == data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with name '{data.name}' already exists",
        )

    role = Role(
        **data.model_dump(exclude={"permission_ids"}),
        permission_ids=data.permission_ids,
        is_system=False,
    )
    await role.insert()
    return role


@router.get("/roles", response_model=list[RoleResponse], summary="查询角色列表")
async def list_roles(
    app_identifier: str | None = Query(None, description="应用标识符"),
    is_system: bool | None = Query(None, description="是否系统角色"),
    is_default: bool | None = Query(None, description="是否默认角色"),
    current_user: User = Depends(require_permission("roles:read")),
) -> list[Role]:
    """
    查询角色列表

    支持按应用标识符、系统角色、默认角色过滤
    """
    filters = []
    if app_identifier:
        filters.append(Role.app_identifier == app_identifier)
    if is_system is not None:
        filters.append(Role.is_system == is_system)
    if is_default is not None:
        filters.append(Role.is_default == is_default)

    if filters:
        return await Role.find_many(*filters).sort("+name").to_list()
    return await Role.find_all().sort("+name").to_list()


@router.get("/roles/{role_id}", response_model=RoleResponse, summary="获取角色详情")
async def get_role(
    role_id: UUID,
    current_user: User = Depends(require_permission("roles:read")),
) -> Role:
    """获取角色详情"""
    role = await Role.find_one(Role.id == role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return role


@router.put("/roles/{role_id}", response_model=RoleResponse, summary="更新角色")
async def update_role(
    role_id: UUID,
    data: RoleUpdate,
    current_user: User = Depends(require_permission("roles:update")),
) -> Role:
    """
    更新角色

    系统角色的部分字段不可修改
    """
    role = await Role.find_one(Role.id == role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # 系统角色只能修改部分字段
    update_data = data.model_dump(exclude_unset=True)
    if role.is_system:
        allowed_fields = {"display_name", "description", "permission_ids", "is_default"}
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}

    for field, value in update_data.items():
        setattr(role, field, value)

    role.updated_at = datetime.utcnow()
    await role.save()
    return role


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除角色")
async def delete_role(
    role_id: UUID,
    current_user: RequireSuperuser,
) -> None:
    """
    删除角色

    系统角色不可删除
    """
    role = await Role.find_one(Role.id == role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System roles cannot be deleted",
        )

    # 删除关联的用户角色分配
    await UserRoleAssignment.find(UserRoleAssignment.role_id == role_id).delete_many()

    await role.delete()


@router.post("/roles/{role_id}/permissions", response_model=RoleResponse, summary="为角色分配权限")
async def assign_permissions_to_role(
    role_id: UUID,
    data: RolePermissionUpdate,
    current_user: User = Depends(require_permission("roles:update")),
) -> Role:
    """为角色分配权限"""
    role = await Role.find_one(Role.id == role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    role.permission_ids = data.permission_ids
    role.updated_at = datetime.utcnow()
    await role.save()
    return role


@router.post("/roles/bulk", response_model=list[RoleResponse], summary="批量创建角色")
async def bulk_create_roles(
    data: BulkRoleCreate,
    current_user: RequireSuperuser,
) -> list[Role]:
    """批量创建角色"""
    roles = []
    for role_data in data.roles:
        # 检查是否已存在
        existing = await Role.find_one(Role.name == role_data.name)
        if existing:
            continue

        role = Role(
            **role_data.model_dump(exclude={"permission_ids"}),
            permission_ids=role_data.permission_ids,
            is_system=False,
        )
        await role.insert()
        roles.append(role)

    return roles


# =============================================================================
# User Role Assignment Endpoints - 用户角色管理
# =============================================================================

@router.post(
    "/users/{user_id}/roles",
    response_model=dict[str, Any],
    summary="分配角色给用户",
)
async def assign_role_to_user(
    user_id: UUID,
    data: AssignRoleRequest,
    current_user: User = Depends(require_permission("users:roles:assign")),
) -> dict[str, Any]:
    """为用户分配角色"""
    # 验证用户存在
    user = await User.find_one(User.id == user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 验证角色存在
    role = await Role.find_one(Role.id == data.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # 检查是否已分配
    existing = await UserRoleAssignment.find_one(
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.role_id == data.role_id,
        UserRoleAssignment.app_identifier == data.app_identifier if data.app_identifier else True,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has this role",
        )

    # 创建分配
    assignment = UserRoleAssignment(
        user_id=user_id,
        role_id=data.role_id,
        app_identifier=data.app_identifier,
        assigned_by=current_user.id,
        expires_at=data.expires_at,
        is_active=True,
    )
    await assignment.insert()

    # 清除用户权限缓存
    perm_service = PermissionService()
    await perm_service.invalidate_user_cache(user_id, data.app_identifier)

    return {"message": "Role assigned successfully", "assignment_id": str(assignment.id)}


@router.get("/users/{user_id}/roles", response_model=list[UUID], summary="获取用户角色列表")
async def get_user_roles(
    user_id: UUID,
    app_identifier: str | None = Query(None, description="应用标识符"),
    current_user: User = Depends(require_permission("users:roles:read")),
) -> list[UUID]:
    """获取用户的角色 ID 列表"""
    filters = [
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.is_active == True,
    ]
    if app_identifier:
        filters.append(
            (UserRoleAssignment.app_identifier == None) |
            (UserRoleAssignment.app_identifier == app_identifier)
        )

    assignments = await UserRoleAssignment.find_many(*filters).to_list()
    return list({a.role_id for a in assignments})


@router.get("/users/{user_id}", response_model=UserPermissionsResponse, summary="获取用户所有权限")
async def get_user_permissions(
    user_id: UUID,
    app_identifier: str | None = Query(None, description="应用标识符"),
    current_user: User = Depends(require_permission("users:permissions:read")),
) -> dict[str, Any]:
    """查询用户的所有权限"""
    perm_service = PermissionService()
    permissions = await perm_service.get_user_permissions(
        user_id=user_id,
        app_identifier=app_identifier,
    )

    return permissions


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    response_model=dict[str, str],
    summary="移除用户角色",
)
async def remove_role_from_user(
    user_id: UUID,
    role_id: UUID,
    app_identifier: str | None = Query(None, description="应用标识符"),
    current_user: User = Depends(require_permission("users:roles:remove")),
) -> dict[str, str]:
    """移除用户的角色"""
    assignment = await UserRoleAssignment.find_one(
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.role_id == role_id,
        UserRoleAssignment.app_identifier == app_identifier if app_identifier else True,
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role assignment not found",
        )

    await assignment.delete()

    # 清除用户权限缓存
    perm_service = PermissionService()
    await perm_service.invalidate_user_cache(user_id, app_identifier)

    return {"message": "Role removed successfully"}


@router.post(
    "/users/{user_id}/check",
    response_model=PermissionCheckResponse,
    summary="检查用户权限",
)
async def check_user_permissions(
    user_id: UUID,
    data: PermissionCheckRequest,
    current_user: User = Depends(require_permission("users:permissions:read")),
) -> dict[str, Any]:
    """批量检查用户的权限"""
    perm_service = PermissionService()
    results = await perm_service.check_multiple_permissions(
        user_id=user_id,
        required_permissions=data.permissions,
        app_identifier=data.app_identifier,
    )

    return {"results": results}


@router.post(
    "/users/{user_id}/cache/clear",
    response_model=dict[str, str],
    summary="清除用户权限缓存",
)
async def clear_user_permission_cache(
    user_id: UUID,
    current_user: RequireSuperuser,
    app_identifier: str | None = Query(None, description="应用标识符"),
) -> dict[str, str]:
    """清除用户的权限缓存（强制重新加载权限）"""
    perm_service = PermissionService()
    await perm_service.invalidate_user_cache(user_id, app_identifier)

    return {"message": "User permission cache cleared"}
