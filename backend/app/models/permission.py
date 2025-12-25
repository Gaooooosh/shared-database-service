"""
Unified Backend Platform - Permission Models

基于 Casdoor 的 RBAC 权限管理模型
"""
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import Field


# =============================================================================
# Permission - 权限定义模型
# =============================================================================

class Permission(Document):
    """
    权限定义模型

    定义系统中所有可能的操作权限
    权限命名格式: resource:action (如 posts:create, posts:read, posts:*)
    """

    # ==========================================================================
    # 主键与标识
    # ==========================================================================
    id: UUID = Field(default_factory=uuid4, description="权限 ID")

    name: str = Indexed(
        unique=True,
        description="权限名称 (格式: resource:action)"
    )

    # ==========================================================================
    # 显示信息
    # ==========================================================================
    display_name: str = Field(..., description="权限显示名称")
    description: str | None = Field(default=None, description="权限描述")

    # ==========================================================================
    # 权限分类
    # ==========================================================================
    resource_type: str = Indexed(
        description="资源类型 (如: posts, users, files, records)"
    )

    action: str = Indexed(
        description="操作类型 (如: create, read, update, delete, list, *)"
    )

    # ==========================================================================
    # 应用级隔离
    # ==========================================================================
    app_identifier: str | None = Indexed(
        default=None,
        description="应用标识符 (None 表示全局权限)"
    )

    # ==========================================================================
    # 元数据
    # ==========================================================================
    is_system: bool = Field(
        default=False,
        description="是否为系统权限 (系统权限不可删除)"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="创建时间"
    )

    # ==========================================================================
    # Beanie 配置
    # ==========================================================================
    class Settings:
        name = "permissions"
        indexes = [
            "name",
            "resource_type",
            "action",
            "app_identifier",
            ("app_identifier", "resource_type", "action"),
        ]


# =============================================================================
# Role - 角色模型
# =============================================================================

class Role(Document):
    """
    角色模型 - 权限的集合

    与 Casdoor 权限组映射，支持应用级隔离
    """

    # ==========================================================================
    # 主键与标识
    # ==========================================================================
    id: UUID = Field(default_factory=uuid4, description="角色 ID")

    name: str = Indexed(unique=True, description="角色标识符")

    # ==========================================================================
    # 显示信息
    # ==========================================================================
    display_name: str = Field(..., description="角色显示名称")
    description: str | None = Field(default=None, description="角色描述")

    # ==========================================================================
    # 权限列表
    # ==========================================================================
    permission_ids: list[UUID] = Field(
        default_factory=list,
        description="关联的权限 ID 列表"
    )

    # ==========================================================================
    # 应用级隔离
    # ==========================================================================
    app_identifier: str | None = Indexed(
        default=None,
        description="应用标识符 (None 表示全局角色)"
    )

    # ==========================================================================
    # Casdoor 集成
    # ==========================================================================
    casdoor_group_name: str | None = Field(
        default=None,
        description="对应的 Casdoor 权限组名称"
    )

    # ==========================================================================
    # 元数据
    # ==========================================================================
    is_system: bool = Field(
        default=False,
        description="是否为系统角色 (系统角色不可删除)"
    )

    is_default: bool = Field(
        default=False,
        description="是否为新用户默认角色"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="创建时间"
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="更新时间"
    )

    # ==========================================================================
    # Beanie 配置
    # ==========================================================================
    class Settings:
        name = "roles"
        indexes = [
            "name",
            "app_identifier",
            ("app_identifier", "is_default"),
            "casdoor_group_name",
        ]


# =============================================================================
# UserRoleAssignment - 用户角色关联模型
# =============================================================================

class UserRoleAssignment(Document):
    """
    用户角色分配模型

    记录用户与角色的关联关系，支持应用级角色分配和临时授权
    """

    # ==========================================================================
    # 主键
    # ==========================================================================
    id: UUID = Field(default_factory=uuid4, description="分配 ID")

    # ==========================================================================
    # 用户关联
    # ==========================================================================
    user_id: UUID = Indexed(description="用户 ID (User.id)")

    # ==========================================================================
    # 角色关联
    # ==========================================================================
    role_id: UUID = Indexed(description="角色 ID (Role.id)")

    # ==========================================================================
    # 应用级隔离
    # ==========================================================================
    app_identifier: str | None = Indexed(
        default=None,
        description="应用标识符 (None 表示全局角色)"
    )

    # ==========================================================================
    # 元数据
    # ==========================================================================
    assigned_by: UUID | None = Field(
        default=None,
        description="分配者用户 ID"
    )

    assigned_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="分配时间"
    )

    expires_at: datetime | None = Field(
        default=None,
        description="过期时间 (None 表示永不过期)"
    )

    is_active: bool = Field(
        default=True,
        description="是否激活"
    )

    # ==========================================================================
    # Beanie 配置
    # ==========================================================================
    class Settings:
        name = "user_role_assignments"
        indexes = [
            "user_id",
            "role_id",
            "app_identifier",
            ("user_id", "app_identifier", "is_active"),
            "expires_at",
        ]


# =============================================================================
# 辅助函数
# =============================================================================

async def get_user_permissions(
    user_id: UUID,
    app_identifier: str | None = None,
) -> list[str]:
    """
    辅助函数：获取用户的权限列表

    Args:
        user_id: 用户 ID
        app_identifier: 应用标识符 (None 表示全局)

    Returns:
        权限名称列表 (如 ["posts:create", "posts:read", ...])
    """
    # 获取用户活跃的角色分配
    assignments = await UserRoleAssignment.find(
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.app_identifier == app_identifier if app_identifier else True,
        UserRoleAssignment.is_active == True,
    ).to_list()

    if not assignments:
        return []

    # 获取角色 ID 列表
    role_ids = list({a.role_id for a in assignments})

    # 获取角色
    roles = await Role.find(Role.id.in_(role_ids)).to_list()

    # 获取权限 ID 列表
    permission_ids = set()
    for role in roles:
        permission_ids.update(role.permission_ids)

    # 获取权限
    permissions = await Permission.find(
        Permission.id.in_(list(permission_ids))
    ).to_list()

    return [p.name for p in permissions]
