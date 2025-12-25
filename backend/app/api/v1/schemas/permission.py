"""
Unified Backend Platform - Permission Schemas

权限管理相关的 Pydantic 模型
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Permission Schemas
# =============================================================================

class PermissionBase(BaseModel):
    """权限基础模型"""
    name: str = Field(..., pattern=r"^[a-z_]+:[a-z\*]+$", description="权限名称 (格式: resource:action)")
    display_name: str = Field(..., min_length=1, max_length=100, description="权限显示名称")
    description: str | None = Field(default=None, max_length=500, description="权限描述")
    resource_type: str = Field(..., min_length=1, max_length=50, description="资源类型")
    action: str = Field(..., min_length=1, max_length=50, description="操作类型")
    app_identifier: str | None = Field(default=None, max_length=100, description="应用标识符")


class PermissionCreate(PermissionBase):
    """创建权限请求"""
    pass


class PermissionUpdate(BaseModel):
    """更新权限请求"""
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class PermissionResponse(PermissionBase):
    """权限响应"""
    id: UUID
    is_system: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Role Schemas
# =============================================================================

class RoleBase(BaseModel):
    """角色基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="角色标识符")
    display_name: str = Field(..., min_length=1, max_length=100, description="角色显示名称")
    description: str | None = Field(default=None, max_length=500, description="角色描述")
    app_identifier: str | None = Field(default=None, max_length=100, description="应用标识符")
    is_default: bool = Field(default=False, description="是否为新用户默认角色")


class RoleCreate(RoleBase):
    """创建角色请求"""
    permission_ids: list[UUID] = Field(default_factory=list, description="关联的权限 ID 列表")
    casdoor_group_name: str | None = Field(default=None, max_length=100, description="对应的 Casdoor 权限组名称")


class RoleUpdate(BaseModel):
    """更新角色请求"""
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    permission_ids: list[UUID] | None = Field(default=None, description="关联的权限 ID 列表")
    is_default: bool | None = Field(default=None)


class RoleResponse(RoleBase):
    """角色响应"""
    id: UUID
    permission_ids: list[UUID]
    casdoor_group_name: str | None
    is_system: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RolePermissionUpdate(BaseModel):
    """更新角色权限请求"""
    permission_ids: list[UUID] = Field(..., description="权限 ID 列表")


# =============================================================================
# UserRoleAssignment Schemas
# =============================================================================

class AssignRoleRequest(BaseModel):
    """分配角色请求"""
    role_id: UUID = Field(..., description="角色 ID")
    app_identifier: str | None = Field(default=None, max_length=100, description="应用标识符")
    expires_at: datetime | None = Field(default=None, description="过期时间")


class UserRoleAssignmentResponse(BaseModel):
    """用户角色分配响应"""
    id: UUID
    user_id: UUID
    role_id: UUID
    app_identifier: str | None
    assigned_by: UUID | None
    assigned_at: datetime
    expires_at: datetime | None
    is_active: bool

    class Config:
        from_attributes = True


# =============================================================================
# User Permissions Schemas
# =============================================================================

class UserPermissionsResponse(BaseModel):
    """用户权限响应"""
    permissions: list[str] = Field(..., description="权限名称列表")
    roles: list[str] = Field(..., description="角色显示名称列表")
    cached_at: str | None = Field(..., description="缓存时间")
    is_superuser: bool = Field(..., description="是否超级管理员")


class PermissionCheckRequest(BaseModel):
    """权限检查请求"""
    permissions: list[str] = Field(..., description="需要检查的权限列表")
    app_identifier: str | None = Field(default=None, description="应用标识符")


class PermissionCheckResponse(BaseModel):
    """权限检查响应"""
    results: dict[str, bool] = Field(..., description="权限检查结果")


# =============================================================================
# Bulk Operations
# =============================================================================

class BulkPermissionCreate(BaseModel):
    """批量创建权限请求"""
    permissions: list[PermissionCreate] = Field(..., min_items=1, description="权限列表")


class BulkRoleCreate(BaseModel):
    """批量创建角色请求"""
    roles: list[RoleCreate] = Field(..., min_items=1, description="角色列表")


# =============================================================================
# Filters
# =============================================================================

class PermissionFilter(BaseModel):
    """权限查询过滤器"""
    app_identifier: str | None = None
    resource_type: str | None = None
    is_system: bool | None = None


class RoleFilter(BaseModel):
    """角色查询过滤器"""
    app_identifier: str | None = None
    is_system: bool | None = None
    is_default: bool | None = None
