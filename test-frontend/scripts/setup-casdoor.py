#!/usr/bin/env python3
"""
Casdoor 测试环境配置脚本

功能:
1. 创建测试组织
2. 创建测试应用
3. 配置JWT证书
4. 创建测试用户
5. 创建权限组
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

# =============================================================================
# 配置
# =============================================================================
CASDOOR_ORIGIN = os.environ.get("CASDOOR_ORIGIN", "http://localhost:8000")
CASDOOR_ADMIN = "admin"
CASDOOR_PASSWORD = "admin"

# 测试配置
TEST_ORG_NAME = "test-org"
TEST_ORG_DISPLAY_NAME = "测试组织"
TEST_APP_NAME = "test-app"
TEST_APP_DISPLAY_NAME = "测试应用"

# 测试用户
TEST_USERS = [
    {
        "name": "test-admin",
        "display_name": "测试管理员",
        "email": "admin@test.com",
        "password": "Admin123!",
        "is_admin": True,
    },
    {
        "name": "test-user",
        "display_name": "测试用户",
        "email": "user@test.com",
        "password": "User123!",
        "is_admin": False,
    },
    {
        "name": "test-editor",
        "display_name": "测试编辑",
        "email": "editor@test.com",
        "password": "Editor123!",
        "is_admin": False,
    },
]

# 权限组
TEST_PERMISSIONS = [
    {
        "name": "test-admin-group",
        "display_name": "管理员组",
        "permissions": ["*:*"],
    },
    {
        "name": "test-editor-group",
        "display_name": "编辑组",
        "permissions": ["records:*", "files:read", "files:upload"],
    },
    {
        "name": "test-user-group",
        "display_name": "用户组",
        "permissions": ["records:read", "files:read"],
    },
]

# =============================================================================
# Casdoor API 客户端
# =============================================================================
class CasdoorClient:
    def __init__(self, origin: str):
        self.origin = origin
        self.session = requests.Session()
        self.token = None

    def login(self, username: str, password: str) -> bool:
        """登录获取Token"""
        url = f"{self.origin}/api/login"
        data = {
            "organization": "built-in",
            "username": username,
            "password": password,
            "type": "code",
            "application": "app-built-in",
        }
        response = self.session.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            self.token = result.get("data")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print(f"✅ 登录成功: {username}")
            return True
        print(f"❌ 登录失败: {response.text}")
        return False

    def create_organization(self, name: str, display_name: str) -> dict:
        """创建组织"""
        url = f"{self.origin}/api/save-organization"
        data = {
            "owner": "built-in",
            "name": name,
            "displayName": display_name,
            "websiteUrl": "http://localhost:3002",
            "favicon": "",
            "passwordType": "plain",
            "phonePrefix": "86",
            "defaultAvatar": "https://cdn.casbin.com/img/casdoor_icon_256.png",
        }
        response = self.session.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ 组织创建成功: {name}")
            return response.json()["data"]
        print(f"⚠️ 组织创建失败(可能已存在): {response.text}")
        return {"name": name}

    def create_application(self, org_name: str, name: str, display_name: str) -> dict:
        """创建应用"""
        url = f"{self.origin}/api/save-application"
        data = {
            "owner": org_name,
            "name": name,
            "displayName": display_name,
            "logo": "https://cdn.casbin.com/img/casdoor-icon_256.png",
            "homepageUrl": "http://localhost:3002",
            "description": "测试应用",
            "organization": org_name,
            "cert": "cert-built-in",
            "enablePassword": True,
            "enableSignUp": True,
            "enableCodeSignin": True,
            "enableSms": False,
            "enableEmail": False,
            "providers": [],
            "redirectUris": ["http://localhost:3002/login/callback"],
            "tokenFormat": "JWT",
            "expireInHours": 24 * 7,
            "refreshExpireInHours": 24 * 30,
        }
        response = self.session.post(url, json=data)
        if response.status_code == 200:
            app_data = response.json()["data"]
            print(f"✅ 应用创建成功: {name}")
            return app_data
        print(f"⚠️ 应用创建失败(可能已存在): {response.text}")
        return {"name": name}

    def create_user(self, org_name: str, user_data: dict) -> dict:
        """创建用户"""
        url = f"{self.origin}/api/save-user"
        data = {
            "owner": org_name,
            "name": user_data["name"],
            "displayName": user_data["display_name"],
            "email": user_data["email"],
            "password": user_data["password"],
            "type": "normal-user",
            "phone": "",
            "affiliation": "",
            "idCard": "",
            "region": "",
            "language": "zh",
            "avatar": "https://cdn.casbin.com/img/casdoor-icon_256.png",
            "address": [],
        }
        response = self.session.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ 用户创建成功: {user_data['name']}")
            return response.json()["data"]
        print(f"⚠️ 用户创建失败(可能已存在): {response.text}")
        return {"name": user_data["name"]}

    def create_group(self, org_name: str, group_data: dict) -> dict:
        """创建权限组"""
        url = f"{self.origin}/api/save-group"
        data = {
            "owner": org_name,
            "name": group_data["name"],
            "displayName": group_data["display_name"],
            "type": "permission",
            "policies": group_data.get("permissions", []),
        }
        response = self.session.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ 权限组创建成功: {group_data['name']}")
            return response.json()["data"]
        print(f"⚠️ 权限组创建失败(可能已存在): {response.text}")
        return {"name": group_data["name"]}

    def add_user_to_group(self, org_name: str, username: str, group_name: str) -> bool:
        """将用户添加到权限组"""
        url = f"{self.origin}/api/add-user-to-group"
        data = {
            "organization": org_name,
            "userName": username,
            "groupName": group_name,
        }
        response = self.session.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ 用户 {username} 已添加到组 {group_name}")
            return True
        print(f"❌ 添加用户到组失败: {response.text}")
        return False


# =============================================================================
# 主函数
# =============================================================================
def main():
    print("=" * 50)
    print("Casdoor 测试环境配置")
    print("=" * 50)
    print(f"Casdoor地址: {CASDOOR_ORIGIN}")
    print()

    # 等待 Casdoor 启动
    print("等待 Casdoor 启动...")
    for i in range(30):
        try:
            response = requests.get(f"{CASDOOR_ORIGIN}/api/login")
            if response.status_code == 200:
                break
        except:
            pass
        time.sleep(1)
    else:
        print("❌ Casdoor 启动超时")
        sys.exit(1)

    print("✅ Casdoor 已就绪")

    # 创建客户端并登录
    client = CasdoorClient(CASDOOR_ORIGIN)
    if not client.login(CASDOOR_ADMIN, CASDOOR_PASSWORD):
        print("❌ 登录失败")
        sys.exit(1)

    # 创建组织
    print("\n创建测试组织...")
    org = client.create_organization(TEST_ORG_NAME, TEST_ORG_DISPLAY_NAME)

    # 创建应用
    print("\n创建测试应用...")
    app = client.create_application(org["name"], TEST_APP_NAME, TEST_APP_DISPLAY_NAME)

    # 创建用户
    print("\n创建测试用户...")
    created_users = []
    for user_data in TEST_USERS:
        user = client.create_user(org["name"], user_data)
        created_users.append(user)

    # 创建权限组
    print("\n创建权限组...")
    created_groups = []
    for group_data in TEST_PERMISSIONS:
        group = client.create_group(org["name"], group_data)
        created_groups.append(group)

    # 分配用户到权限组
    print("\n分配用户到权限组...")
    # admin -> admin group
    client.add_user_to_group(org["name"], "test-admin", "test-admin-group")
    # editor -> editor group
    client.add_user_to_group(org["name"], "test-editor", "test-editor-group")
    # user -> user group
    client.add_user_to_group(org["name"], "test-user", "test-user-group")

    print("\n" + "=" * 50)
    print("✅ Casdoor 测试环境配置完成!")
    print("=" * 50)
    print(f"组织: {TEST_ORG_NAME}")
    print(f"应用: {TEST_APP_NAME}")
    print(f"测试用户:")
    for user in TEST_USERS:
        print(f"  - {user['name']} ({user['email']}): {user['password']}")


if __name__ == "__main__":
    main()
