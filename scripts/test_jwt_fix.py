#!/usr/bin/env python3
"""
测试 JWT 认证修复
验证 "this event loop is already running" 错误已修复
"""
import requests
import json
import sys

# 配置
API_BASE_URL = "http://localhost:9000"  # 或生产环境 URL

# 测试用的 JWT token（需要从 Casdoor 获取）
# 这是一个示例 token，实际使用时需要替换为真实的 token
TEST_TOKEN = "YOUR_JWT_TOKEN_HERE"


def test_jwt_authentication(token: str):
    """测试 JWT 认证是否正常工作"""
    print("=" * 60)
    print("🧪 测试 JWT 认证修复")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 测试 1: 获取当前用户信息 (GET /api/v1/auth/me)
    print("\n📋 测试 1: GET /api/v1/auth/me")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/auth/me",
            headers=headers,
            timeout=10
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ 成功获取用户信息")
            print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        elif response.status_code == 401:
            print(f"   ❌ 认证失败: {response.json()}")
            return False
        else:
            print(f"   ⚠️  意外状态码: {response.text}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        return False

    # 测试 2: 创建记录 (POST /api/v1/records) - 这是之前失败的操作
    print("\n📋 测试 2: POST /api/v1/records (创建记录)")
    test_data = {
        "app_identifier": "test-app",
        "collection_type": "test",
        "title": "JWT 修复测试记录",
        "payload": {
            "test_field": "test_value",
            "timestamp": "2025-12-26T00:00:00Z"
        }
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/records",
            headers=headers,
            json=test_data,
            timeout=10
        )
        print(f"   状态码: {response.status_code}")

        if response.status_code == 201:
            print("   ✅ 成功创建记录！")
            result = response.json()
            print(f"   记录 ID: {result.get('id')}")
            print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

            # 清理测试数据
            print(f"\n🗑️  清理测试数据...")
            delete_response = requests.delete(
                f"{API_BASE_URL}/api/v1/records/{result['id']}",
                headers=headers,
                timeout=10
            )
            if delete_response.status_code == 204:
                print("   ✅ 测试数据已清理")
            return True

        elif response.status_code == 401:
            error_detail = response.json()
            print(f"   ❌ 认证失败")
            print(f"   错误详情: {error_detail}")

            # 检查是否还是事件循环错误
            if "event loop" in str(error_detail).lower():
                print("\n🔴 仍然存在事件循环错误！修复失败！")
                return False
            else:
                print("\n⚠️  认证失败，但不是事件循环错误（可能是 token 无效）")
                return False
        else:
            print(f"   ⚠️  意外状态码: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    # 检查是否提供了 token
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        token = TEST_TOKEN

    if token == "YOUR_JWT_TOKEN_HERE":
        print("\n" + "=" * 60)
        print("❌ 错误: 请提供有效的 JWT Token")
        print("=" * 60)
        print("\n使用方法:")
        print("  python scripts/test_jwt_fix.py YOUR_JWT_TOKEN")
        print("\n或从 Casdoor 获取 Token:")
        print("  1. 访问 Casdoor 登录页面")
        print("  2. 登录后从浏览器 DevTools -> Application -> LocalStorage")
        print("  3. 复制 'token' 字段的值")
        print("=" * 60)
        sys.exit(1)

    # 运行测试
    success = test_jwt_authentication(token)

    print("\n" + "=" * 60)
    if success:
        print("✅ 所有测试通过！JWT 认证修复成功！")
        print("=" * 60)
        print("\n修复总结:")
        print("  • decode_jwt_token() 已改为 async 函数")
        print("  • validate_token() 已改为 async 函数")
        print("  • get_current_user() 正确使用 await")
        print("  • 不再出现 'event loop is already running' 错误")
        sys.exit(0)
    else:
        print("❌ 测试失败！请检查日志")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
