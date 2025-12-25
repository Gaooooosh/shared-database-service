#!/usr/bin/env python3
"""
Unified Backend Platform - RBAC Migration Script

数据迁移脚本：将现有的 role 字段迁移到新的 RBAC 权限系统

使用方法:
    cd /home/gaooooosh/shared-database-service
    python scripts/migrate_to_rbac.py
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import get_settings
from app.db.mongodb import mongodb
from app.models.permission import Permission, Role, UserRoleAssignment
from app.models.user import User

settings = get_settings()


# =============================================================================
# 权限定义
# =============================================================================

BASE_PERMISSIONS = [
    # Records 权限
    {
        "name": "records:create",
        "display_name": "创建记录",
        "description": "创建新的统一记录",
        "resource_type": "records",
        "action": "create",
        "app_identifier": None,
    },
    {
        "name": "records:read",
        "display_name": "读取记录",
        "description": "读取统一记录",
        "resource_type": "records",
        "action": "read",
        "app_identifier": None,
    },
    {
        "name": "records:update",
        "display_name": "更新记录",
        "description": "更新统一记录",
        "resource_type": "records",
        "action": "update",
        "app_identifier": None,
    },
    {
        "name": "records:delete",
        "display_name": "删除记录",
        "description": "删除统一记录",
        "resource_type": "records",
        "action": "delete",
        "app_identifier": None,
    },
    {
        "name": "records:batch",
        "display_name": "批量操作记录",
        "description": "批量操作统一记录",
        "resource_type": "records",
        "action": "batch",
        "app_identifier": None,
    },
    # Files 权限
    {
        "name": "files:upload",
        "display_name": "上传文件",
        "description": "上传新文件",
        "resource_type": "files",
        "action": "upload",
        "app_identifier": None,
    },
    {
        "name": "files:download",
        "display_name": "下载文件",
        "description": "下载文件",
        "resource_type": "files",
        "action": "download",
        "app_identifier": None,
    },
    {
        "name": "files:delete",
        "display_name": "删除文件",
        "description": "删除文件",
        "resource_type": "files",
        "action": "delete",
        "app_identifier": None,
    },
    # Users 权限
    {
        "name": "users:read",
        "display_name": "查看用户",
        "description": "查看用户信息",
        "resource_type": "users",
        "action": "read",
        "app_identifier": None,
    },
    {
        "name": "users:update",
        "display_name": "更新用户",
        "description": "更新用户信息",
        "resource_type": "users",
        "action": "update",
        "app_identifier": None,
    },
    {
        "name": "users:delete",
        "display_name": "删除用户",
        "description": "删除用户",
        "resource_type": "users",
        "action": "delete",
        "app_identifier": None,
    },
    # Permissions 权限
    {
        "name": "permissions:read",
        "display_name": "查看权限",
        "description": "查看权限列表",
        "resource_type": "permissions",
        "action": "read",
        "app_identifier": None,
    },
    {
        "name": "permissions:manage",
        "display_name": "管理权限",
        "description": "创建、编辑、删除权限",
        "resource_type": "permissions",
        "action": "manage",
        "app_identifier": None,
    },
    # Roles 权限
    {
        "name": "roles:read",
        "display_name": "查看角色",
        "description": "查看角色列表",
        "resource_type": "roles",
        "action": "read",
        "app_identifier": None,
    },
    {
        "name": "roles:create",
        "display_name": "创建角色",
        "description": "创建新角色",
        "resource_type": "roles",
        "action": "create",
        "app_identifier": None,
    },
    {
        "name": "roles:update",
        "display_name": "更新角色",
        "description": "更新角色",
        "resource_type": "roles",
        "action": "update",
        "app_identifier": None,
    },
    {
        "name": "roles:delete",
        "display_name": "删除角色",
        "description": "删除角色",
        "resource_type": "roles",
        "action": "delete",
        "app_identifier": None,
    },
    # User Roles 权限
    {
        "name": "users:roles:read",
        "display_name": "查看用户角色",
        "description": "查看用户角色分配",
        "resource_type": "users",
        "action": "roles:read",
        "app_identifier": None,
    },
    {
        "name": "users:roles:assign",
        "display_name": "分配角色",
        "description": "为用户分配角色",
        "resource_type": "users",
        "action": "roles:assign",
        "app_identifier": None,
    },
    {
        "name": "users:roles:remove",
        "display_name": "移除角色",
        "description": "移除用户角色",
        "resource_type": "users",
        "action": "roles:remove",
        "app_identifier": None,
    },
    {
        "name": "users:permissions:read",
        "display_name": "查看用户权限",
        "description": "查看用户所有权限",
        "resource_type": "users",
        "action": "permissions:read",
        "app_identifier": None,
    },
]


# =============================================================================
# 迁移函数
# =============================================================================

async def create_permissions() -> dict[str, Permission]:
    """创建基础权限"""
    print("📋 创建基础权限...")
    permissions = {}

    for perm_data in BASE_PERMISSIONS:
        existing = await Permission.find_one(Permission.name == perm_data["name"])
        if existing:
            print(f"  ✅ 权限已存在: {perm_data['name']}")
            permissions[perm_data["name"]] = existing
        else:
            permission = Permission(
                **perm_data,
                is_system=True,
            )
            await permission.insert()
            permissions[perm_data["name"]] = permission
            print(f"  ➕ 创建权限: {perm_data['name']}")

    print(f"✅ 权限创建完成，共 {len(permissions)} 个\n")
    return permissions


async def create_roles(permissions: dict[str, Permission]) -> dict[str, Role]:
    """创建默认角色"""
    print("👥 创建默认角色...")
    roles = {}

    # 定义角色及其权限
    role_definitions = {
        "superuser": {
            "display_name": "超级管理员",
            "description": "拥有所有权限的超级管理员",
            "is_default": False,
            "permissions": list(permissions.keys()),  # 所有权限
        },
        "admin": {
            "display_name": "管理员",
            "description": "系统管理员，拥有大部分权限",
            "is_default": False,
            "permissions": [
                "records:create", "records:read", "records:update", "records:delete", "records:batch",
                "files:upload", "files:download", "files:delete",
                "users:read", "users:update",
                "permissions:read",
                "roles:read", "roles:update",
                "users:roles:read", "users:roles:assign", "users:roles:remove",
                "users:permissions:read",
            ],
        },
        "user": {
            "display_name": "普通用户",
            "description": "普通用户，拥有基础权限",
            "is_default": True,
            "permissions": [
                "records:read",
                "files:upload", "files:download",
            ],
        },
        "guest": {
            "display_name": "访客",
            "description": "访客用户，只有只读权限",
            "is_default": False,
            "permissions": [
                "records:read",
            ],
        },
    }

    for role_name, role_def in role_definitions.items():
        existing = await Role.find_one(Role.name == role_name)
        if existing:
            print(f"  ✅ 角色已存在: {role_name}")
            roles[role_name] = existing
        else:
            # 获取权限 ID
            permission_ids = [
                permissions[perm_name].id
                for perm_name in role_def["permissions"]
                if perm_name in permissions
            ]

            role = Role(
                name=role_name,
                display_name=role_def["display_name"],
                description=role_def["description"],
                permission_ids=permission_ids,
                app_identifier=None,
                casdoor_group_name=None,
                is_system=True,
                is_default=role_def["is_default"],
            )
            await role.insert()
            roles[role_name] = role
            print(f"  ➕ 创建角色: {role_name} ({len(permission_ids)} 个权限)")

    print(f"✅ 角色创建完成，共 {len(roles)} 个\n")
    return roles


async def migrate_users(roles: dict[str, Role]) -> dict[str, int]:
    """迁移现有用户"""
    print("👤 迁移现有用户...")
    stats = {"migrated": 0, "skipped": 0, "errors": 0}

    # 获取所有用户
    users = await User.find_all().to_list()
    print(f"  找到 {len(users)} 个用户\n")

    for user in users:
        try:
            # 检查是否已有 is_superuser 字段
            if not hasattr(user, "is_superuser"):
                user.is_superuser = False

            # 根据 role 字段分配角色
            old_role = getattr(user, "role", None)

            if old_role == "admin":
                # admin 用户 -> admin 角色 + is_superuser=True
                user.is_superuser = True
                target_role_name = "admin"
            elif old_role == "user":
                # user 用户 -> user 角色
                target_role_name = "user"
            elif old_role == "guest":
                # guest 用户 -> guest 角色
                target_role_name = "guest"
            else:
                # 无角色或未知角色 -> user 角色（默认）
                target_role_name = "user"

            # 创建角色分配
            target_role = roles.get(target_role_name)
            if target_role:
                # 检查是否已分配
                existing = await UserRoleAssignment.find_one(
                    UserRoleAssignment.user_id == user.id,
                    UserRoleAssignment.role_id == target_role.id,
                )
                if not existing:
                    assignment = UserRoleAssignment(
                        user_id=user.id,
                        role_id=target_role.id,
                        app_identifier=None,
                        is_active=True,
                    )
                    await assignment.insert()

                # 设置主角色
                user.primary_role_id = target_role.id

            # 删除旧的 role 字段（通过设置为 None）
            if hasattr(user, "role"):
                delattr(user, "role")

            await user.save()
            print(f"  ✅ 迁移用户: {user.email} ({old_role} -> {target_role_name})")
            stats["migrated"] += 1

        except Exception as e:
            print(f"  ❌ 迁移失败: {user.email} - {e}")
            stats["errors"] += 1

    print(f"\n✅ 用户迁移完成: {stats['migrated']} 个成功, {stats['errors']} 个失败, {stats['skipped']} 个跳过\n")
    return stats


async def verify_migration() -> None:
    """验证迁移结果"""
    print("🔍 验证迁移结果...\n")

    # 统计权限
    permission_count = await Permission.count()
    print(f"  权限总数: {permission_count}")

    # 统计角色
    role_count = await Role.count()
    print(f"  角色总数: {role_count}")

    # 统计用户角色分配
    assignment_count = await UserRoleAssignment.count()
    print(f"  用户角色分配总数: {assignment_count}")

    # 统计用户
    user_count = await User.count()
    superuser_count = await User.count(User.is_superuser == True)
    print(f"  用户总数: {user_count}")
    print(f"  超级管理员数: {superuser_count}")

    print("\n✅ 验证完成\n")


async def main():
    """主函数"""
    print("=" * 70)
    print("Unified Backend Platform - RBAC 迁移脚本")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # 1. 连接数据库
        print("🔗 连接数据库...")
        await mongodb.connect()
        print(f"✅ 数据库已连接: {settings.mongodb_database}\n")

        # 2. 创建基础权限
        permissions = await create_permissions()

        # 3. 创建默认角色
        roles = await create_roles(permissions)

        # 4. 迁移现有用户
        await migrate_users(roles)

        # 5. 验证迁移结果
        await verify_migration()

        print("=" * 70)
        print("✅ 迁移完成!")
        print("=" * 70)
        print("\n⚠️  注意事项:")
        print("  1. 请检查迁移结果是否符合预期")
        print("  2. 建议在测试环境先验证迁移脚本")
        print("  3. 生产环境执行前请备份数据库")
        print("  4. 迁移后需要重新部署应用")

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # 关闭数据库连接
        await mongodb.disconnect()
        print("\n🔌 数据库已断开连接")


if __name__ == "__main__":
    asyncio.run(main())
