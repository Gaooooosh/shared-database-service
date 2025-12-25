#!/usr/bin/env python3
"""测试权限检查功能"""
import asyncio
import motor.motor_asyncio
from datetime import datetime

MONGO_URL = "mongodb://yonggaoxiao:233e619e96476734ef033d757fefedd4768a13e8d9e1667e@mongo:27017/unified_backend?authSource=admin"

async def test_permissions():
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    db = client.unified_backend
    print("✅ 数据库已连接\n")

    # 1. 查询权限数量
    perm_count = await db.permissions.count_documents({})
    print(f"📊 权限总数: {perm_count}")

    # 2. 查询角色数量
    role_count = await db.roles.count_documents({})
    print(f"📊 角色总数: {role_count}")

    # 3. 查询用户数量
    user_count = await db.users.count_documents({})
    print(f"📊 用户总数: {user_count}")

    # 4. 查询超级管理员数量
    superuser_count = await db.users.count_documents({"is_superuser": True})
    print(f"📊 超级管理员数: {superuser_count}")

    # 5. 查询权限详情
    print("\n📋 权限列表:")
    async for perm in db.permissions.find({}).sort("name"):
        print(f"  - {perm['name']}: {perm['display_name']}")

    # 6. 查询角色详情
    print("\n👥 角色详情:")
    async for role in db.roles.find({}):
        perm_count = len(role.get("permission_ids", []))
        print(f"  - {role['name']}: {role['display_name']} ({perm_count} 个权限)")

    # 7. 查询用户详情
    print("\n👤 用户详情:")
    async for user in db.users.find({}):
        role = user.get("role", "N/A")
        is_super = user.get("is_superuser", False)
        primary_role = user.get("primary_role_id")
        print(f"  - {user['email']}: role={role}, is_superuser={is_super}, primary_role_id={primary_role}")

    # 8. 验证权限完整性
    print("\n🔍 验证数据完整性:")

    # 检查角色引用的权限是否存在
    roles = await db.roles.find({}).to_list()
    for role in roles:
        perm_ids = role.get("permission_ids", [])
        for pid in perm_ids:
            perm = await db.permissions.find_one({"_id": pid})
            if not perm:
                print(f"  ⚠️  角色 {role['name']} 引用了不存在的权限 ID: {pid}")

    # 检查用户引用的角色是否存在
    users = await db.users.find({}).to_list()
    for user in users:
        primary_role_id = user.get("primary_role_id")
        if primary_role_id:
            role = await db.roles.find_one({"_id": primary_role_id})
            if not role:
                print(f"  ⚠️  用户 {user['email']} 引用了不存在的角色 ID: {primary_role_id}")

    print("\n✅ 测试完成!")
    client.close()

if __name__ == "__main__":
    asyncio.run(test_permissions())
