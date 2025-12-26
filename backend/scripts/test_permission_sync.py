#!/usr/bin/env python3
"""
测试 Casdoor 权限同步功能
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from app.services.casdoor_sync_service import CasdoorSyncService
from app.models.user import User


async def test_sync():
    """测试权限同步"""
    print("=== 测试 Casdoor 权限同步 ===\n")

    # 查找用户
    user = await User.find_one(User.email == "yonggaoxiao@bupt.edu.cn")

    if not user:
        print("❌ 用户未找到")
        return

    print(f"✅ 找到用户: {user.display_name}")
    print(f"   邮箱: {user.email}")
    print(f"   Casdoor ID: {user.casdoor_id}")
    print(f"   超级管理员: {user.is_superuser}")
    print()

    # 测试 Casdoor 同步服务
    sync_service = CasdoorSyncService()

    print("=== 测试获取权限组 ===")
    groups = await sync_service.get_user_casdoor_groups(
        casdoor_user_id=user.casdoor_id,
        email=user.email
    )

    print(f"✅ 获取到权限组: {groups}")
    print()

    if groups:
        print("=== 测试权限同步 ===")
        result = await sync_service.sync_groups_to_local_roles(
            user_id=user.id,
            casdoor_user_id=user.casdoor_id,
            email=user.email,
            app_identifier=None
        )

        print(f"✅ 同步结果:")
        print(f"   - 同步状态: {result.get('synced')}")
        print(f"   - 权限组: {result.get('groups')}")
        print(f"   - 创建角色数: {result.get('roles_created')}")
        print(f"   - 创建分配数: {result.get('assignments_created')}")
    else:
        print("⚠️  未获取到权限组，跳过同步测试")

    print()
    print("=== 检查用户权限 ===")

    # 检查用户的角色分配
    from app.models.permission import UserRoleAssignment, Role

    assignments = await UserRoleAssignment.find(
        UserRoleAssignment.user_id == user.id
    ).to_list()

    if assignments:
        print(f"✅ 用户有 {len(assignments)} 个角色分配:")
        for assignment in assignments:
            role = await Role.find_one(Role.id == assignment.role_id)
            if role:
                print(f"   - {role.display_name} ({role.name})")
                print(f"     权限: {role.permission_ids}")
    else:
        print("⚠️  用户没有角色分配")


if __name__ == "__main__":
    import motor.motor_asyncio
    from app.core.config import get_settings

    settings = get_settings()

    async def main():
        # 初始化 MongoDB 连接
        from beanie import init_beanie
        from app.models.user import User
        from app.models.permission import Role, UserRoleAssignment, Permission
        from app.models.unified_record import UnifiedRecord
        from app.models.file import File

        client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)

        await init_beanie(
            database=client[settings.mongodb_database],
            document_models=[User, Role, UserRoleAssignment, Permission, UnifiedRecord, File]
        )

        await test_sync()

        client.close()

    asyncio.run(main())
