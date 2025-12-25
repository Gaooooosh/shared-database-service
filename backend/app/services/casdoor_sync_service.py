"""
Unified Backend Platform - Casdoor Sync Service

Casdoor 权限组同步服务，将 Casdoor 权限组映射到本地角色
"""
from __future__ import annotations

import httpx
from uuid import UUID

from app.core.config import get_settings
from app.models.permission import Role, UserRoleAssignment

settings = get_settings()


class CasdoorSyncService:
    """
    Casdoor 权限同步服务

    职责:
    1. 从 Casdoor API 获取用户权限组
    2. 将 Casdoor 权限组映射到本地 Role
    3. 创建 UserRoleAssignment 关联
    """

    def __init__(self) -> None:
        self.casdoor_api_base = f"{settings.casdoor_origin}/api"
        self.timeout = 10.0  # API 请求超时时间（秒）

    # ==============================================================================
    # Casdoor API 调用
    # ==============================================================================

    async def get_user_casdoor_groups(
        self,
        casdoor_user_id: str,
    ) -> list[str]:
        """
        从 Casdoor 获取用户的权限组列表

        Args:
            casdoor_user_id: Casdoor 用户 ID

        Returns:
            权限组名称列表 (如 ["admin", "editor", "author"])

        注意:
            此方法需要 Casdoor 配置了权限组功能
            如果 Casdoor 未配置权限组，返回空列表
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 调用 Casdoor API 获取用户信息
                # 注意: 需要配置 Casdoor 的客户端凭据
                response = await client.get(
                    f"{self.casdoor_api_base}/get-user",
                    params={"id": casdoor_user_id},
                )

                if response.status_code == 200:
                    user_data = response.json()
                    # Casdoor 用户数据中的权限组字段
                    # 根据实际 Casdoor API 响应调整字段名
                    groups = user_data.get("permissions") or user_data.get("groups") or []
                    return groups
                else:
                    print(f"Casdoor API error: {response.status_code}")
                    return []

        except httpx.TimeoutException:
            print("Casdoor API timeout")
            return []
        except httpx.HTTPError as e:
            print(f"Casdoor API error: {e}")
            return []
        except Exception as e:
            print(f"Error fetching Casdoor groups: {e}")
            return []

    # ==============================================================================
    # 权限组同步
    # ==============================================================================

    async def sync_groups_to_local_roles(
        self,
        user_id: UUID,
        casdoor_user_id: str,
        app_identifier: str | None = None,
    ) -> dict[str, Any]:
        """
        将 Casdoor 权限组同步到本地角色

        Args:
            user_id: 本地用户 ID
            casdoor_user_id: Casdoor 用户 ID
            app_identifier: 应用标识符 (None 表示全局权限)

        Returns:
            {
                "synced": True,
                "groups": ["admin", "editor"],
                "roles_created": 0,
                "assignments_created": 0
            }
        """
        # 1. 获取 Casdoor 权限组
        casdoor_groups = await self.get_user_casdoor_groups(casdoor_user_id)

        if not casdoor_groups:
            return {
                "synced": False,
                "groups": [],
                "roles_created": 0,
                "assignments_created": 0,
                "message": "No Casdoor groups found",
            }

        # 2. 同步每个权限组
        roles_created = 0
        assignments_created = 0

        for group_name in casdoor_groups:
            # 查找或创建角色
            role = await self.get_or_create_role_from_group(group_name, app_identifier)
            if not role:
                continue

            if getattr(role, "is_new", False):
                roles_created += 1

            # 创建角色分配
            assignment = await self.create_user_role_assignment(
                user_id=user_id,
                role_id=role.id,
                app_identifier=app_identifier,
            )

            if assignment and getattr(assignment, "is_new", False):
                assignments_created += 1

        return {
            "synced": True,
            "groups": casdoor_groups,
            "roles_created": roles_created,
            "assignments_created": assignments_created,
        }

    async def get_or_create_role_from_group(
        self,
        group_name: str,
        app_identifier: str | None = None,
    ) -> Role | None:
        """
        根据 Casdoor 权限组名称查找或创建本地角色

        Args:
            group_name: Casdoor 权限组名称
            app_identifier: 应用标识符

        Returns:
            Role 对象 (带有 is_new 属性标记是否新创建)
        """
        # 查找现有角色
        existing_role = await Role.find_one(
            Role.casdoor_group_name == group_name,
            Role.app_identifier == app_identifier if app_identifier else True,
        )

        if existing_role:
            existing_role.is_new = False  # type: ignore
            return existing_role

        # 创建新角色
        try:
            new_role = Role(
                name=group_name,
                display_name=group_name.replace("_", " ").title(),
                description=f"Role synced from Casdoor group: {group_name}",
                casdoor_group_name=group_name,
                app_identifier=app_identifier,
                permission_ids=[],  # 权限需要后续手动分配
                is_system=False,
            )
            await new_role.insert()
            new_role.is_new = True  # type: ignore
            return new_role
        except Exception as e:
            print(f"Error creating role from group {group_name}: {e}")
            return None

    async def create_user_role_assignment(
        self,
        user_id: UUID,
        role_id: UUID,
        app_identifier: str | None = None,
    ) -> UserRoleAssignment | None:
        """
        创建用户角色分配（如果不存在）

        Args:
            user_id: 用户 ID
            role_id: 角色 ID
            app_identifier: 应用标识符

        Returns:
            UserRoleAssignment 对象 (带有 is_new 属性标记是否新创建)
        """
        # 检查是否已存在
        existing = await UserRoleAssignment.find_one(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.role_id == role_id,
            UserRoleAssignment.app_identifier == app_identifier if app_identifier else True,
        )

        if existing:
            existing.is_new = False  # type: ignore
            return existing

        # 创建新分配
        try:
            new_assignment = UserRoleAssignment(
                user_id=user_id,
                role_id=role_id,
                app_identifier=app_identifier,
                is_active=True,
            )
            await new_assignment.insert()
            new_assignment.is_new = True  # type: ignore
            return new_assignment
        except Exception as e:
            print(f"Error creating role assignment: {e}")
            return None

    # ==============================================================================
    # 手动同步触发
    # ==============================================================================

    async def force_sync_user(
        self,
        user_id: UUID,
        casdoor_user_id: str,
        app_identifier: str | None = None,
    ) -> dict[str, Any]:
        """
        强制同步用户权限（清除现有分配后重新同步）

        Args:
            user_id: 本地用户 ID
            casdoor_user_id: Casdoor 用户 ID
            app_identifier: 应用标识符

        Returns:
            同步结果
        """
        # 1. 删除现有角色分配
        await UserRoleAssignment.find(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.app_identifier == app_identifier if app_identifier else True,
        ).delete_many()

        # 2. 重新同步
        result = await self.sync_groups_to_local_roles(
            user_id=user_id,
            casdoor_user_id=casdoor_user_id,
            app_identifier=app_identifier,
        )

        result["force_synced"] = True
        return result
