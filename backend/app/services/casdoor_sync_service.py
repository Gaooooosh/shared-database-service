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
        email: str | None = None,
    ) -> list[str]:
        """
        从 Casdoor 获取用户的权限组列表

        Args:
            casdoor_user_id: Casdoor 用户 ID (UUID 或 owner/username 格式)
            email: 用户邮箱 (可选，优先使用邮箱查询)

        Returns:
            权限组名称列表 (如 ["admin", "editor", "author"])

        注意:
            此方法需要 Casdoor 配置了权限组功能
            如果 Casdoor 未配置权限组，返回空列表
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 方案1: 如果有邮箱，优先使用邮箱查询
                if email:
                    response = await client.get(
                        f"{self.casdoor_api_base}/get-user",
                        params={
                            "email": email,
                            "client_id": settings.casdoor_client_id,
                            "client_secret": settings.casdoor_client_secret,
                        },
                    )

                    if response.status_code == 200:
                        api_data = response.json()
                        if api_data.get("status") == "ok" and api_data.get("data"):
                            user_data = api_data.get("data", {})
                            groups = user_data.get("groups") or user_data.get("permissions") or user_data.get("tags") or []
                            print(f"📋 Casdoor groups for {email}: {groups}")
                            return groups

                # 方案2: 使用用户 ID 查询 (owner/username 格式或 UUID)
                response = await client.get(
                    f"{self.casdoor_api_base}/get-user",
                    params={
                        "id": casdoor_user_id,
                        "owner": settings.casdoor_organization,
                        "client_id": settings.casdoor_client_id,
                        "client_secret": settings.casdoor_client_secret,
                    },
                )

                if response.status_code == 200:
                    api_data = response.json()
                    if api_data.get("status") == "ok" and api_data.get("data"):
                        user_data = api_data.get("data", {})
                        groups = user_data.get("groups") or user_data.get("permissions") or user_data.get("tags") or []
                        print(f"📋 Casdoor groups for {casdoor_user_id}: {groups}")
                        return groups

                print(f"⚠️  未找到用户或无权限组")
                return []

        except httpx.TimeoutException:
            print("⏱️  Casdoor API timeout")
            return []
        except httpx.HTTPError as e:
            print(f"❌ Casdoor API HTTP error: {e}")
            return []
        except Exception as e:
            print(f"❌ Error fetching Casdoor groups: {e}")
            return []

    # ==============================================================================
    # 权限组同步
    # ==============================================================================

    async def sync_groups_to_local_roles(
        self,
        user_id: UUID,
        casdoor_user_id: str,
        app_identifier: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any]:
        """
        将 Casdoor 权限组同步到本地角色

        Args:
            user_id: 本地用户 ID
            casdoor_user_id: Casdoor 用户 ID
            app_identifier: 应用标识符 (None 表示全局权限)
            email: 用户邮箱 (用于 UUID 查询时的辅助)

        Returns:
            {
                "synced": True,
                "groups": ["admin", "editor"],
                "roles_created": 0,
                "assignments_created": 0
            }
        """
        # 1. 获取 Casdoor 权限组
        casdoor_groups = await self.get_user_casdoor_groups(casdoor_user_id, email=email)

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
            role, is_new_role = await self.get_or_create_role_from_group(group_name, app_identifier)
            if not role:
                continue

            if is_new_role:
                roles_created += 1

            # 创建角色分配
            assignment, is_new_assignment = await self.create_user_role_assignment(
                user_id=user_id,
                role_id=role.id,
                app_identifier=app_identifier,
            )

            if assignment and is_new_assignment:
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
    ) -> tuple[Role | None, bool]:
        """
        根据 Casdoor 权限组名称查找或创建本地角色

        Args:
            group_name: Casdoor 权限组名称
            app_identifier: 应用标识符

        Returns:
            (Role对象, 是否新创建)
        """
        # 构造查询条件
        query_filters = [Role.casdoor_group_name == group_name]
        if app_identifier is not None:
            query_filters.append(Role.app_identifier == app_identifier)

        # 查找现有角色
        existing_role = await Role.find_one(*query_filters)

        if existing_role:
            return existing_role, False

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
            return new_role, True
        except Exception as e:
            print(f"Error creating role from group {group_name}: {e}")
            return None, False

    async def create_user_role_assignment(
        self,
        user_id: UUID,
        role_id: UUID,
        app_identifier: str | None = None,
    ) -> tuple[UserRoleAssignment | None, bool]:
        """
        创建用户角色分配（如果不存在）

        Args:
            user_id: 用户 ID
            role_id: 角色 ID
            app_identifier: 应用标识符

        Returns:
            (UserRoleAssignment对象, 是否新创建)
        """
        # 检查是否已存在
        query_filters = [
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.role_id == role_id,
        ]
        if app_identifier is not None:
            query_filters.append(UserRoleAssignment.app_identifier == app_identifier)

        existing = await UserRoleAssignment.find_one(*query_filters)

        if existing:
            return existing, False

        # 创建新分配
        try:
            new_assignment = UserRoleAssignment(
                user_id=user_id,
                role_id=role_id,
                app_identifier=app_identifier,
                is_active=True,
            )
            await new_assignment.insert()
            return new_assignment, True
        except Exception as e:
            print(f"Error creating role assignment: {e}")
            return None, False

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
        query_filters = [UserRoleAssignment.user_id == user_id]
        if app_identifier is not None:
            query_filters.append(UserRoleAssignment.app_identifier == app_identifier)

        await UserRoleAssignment.find(*query_filters).delete_many()

        # 2. 重新同步
        result = await self.sync_groups_to_local_roles(
            user_id=user_id,
            casdoor_user_id=casdoor_user_id,
            app_identifier=app_identifier,
        )

        result["force_synced"] = True
        return result
