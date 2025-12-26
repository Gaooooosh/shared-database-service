#!/bin/bash

# 前端权限验证测试脚本
# 用于验证后端权限修复是否生效

echo "======================================"
echo "前端权限验证测试"
echo "======================================"
echo ""

# 1. 检查后端服务状态
echo "📌 1. 检查后端服务状态..."
if curl -s http://localhost:9000/health > /dev/null 2>&1; then
    echo "✅ 后端服务正常运行"
else
    echo "❌ 后端服务未响应"
    exit 1
fi

echo ""
echo "======================================"
echo "📋 测试说明"
echo "======================================"
echo ""
echo "请按以下步骤测试权限修复："
echo ""
echo "1️⃣  重新登录"
echo "   - 打开浏览器访问前端应用"
echo "   - 点击退出登录"
echo "   - 重新通过 Casdoor 登录"
echo ""
echo "2️⃣  检查用户权限"
echo "   - 打开浏览器开发者工具 (F12)"
echo "   - 切换到 Console 标签"
echo "   - 执行以下命令："
echo ""
echo "     // 获取当前用户信息"
echo "     JSON.parse(localStorage.getItem('auth-storage'))"
echo ""
echo "   - 检查返回的 user.permissions 和 user.roles"
echo ""
echo "3️⃣  测试创建记录"
echo "   - 尝试创建一个新的曲目或编曲"
echo "   - 应该可以正常创建，不会出现权限错误"
echo ""
echo "4️⃣  验证 API 返回"
echo "   - 在 Network 标签中找到 /api/v1/auth/me 请求"
echo "   - 检查响应中的 permissions 和 roles 字段"
echo ""
echo "======================================"
echo "📊 预期结果"
echo "======================================"
echo ""
echo "✅ /api/v1/auth/me 应该返回："
echo '{'
echo '  "id": "...",'
echo '  "email": "your@email.com",'
echo '  "display_name": "你的名字",'
echo '  "permissions": ["*:*"] 或其他权限列表,'
echo '  "roles": ["Aiyueaijia/group_perf"] 或其他角色'
echo '}'
echo ""
echo "❌ 如果返回："
echo '{'
echo '  "permissions": [],'
echo '  "roles": []'
echo '}'
echo "说明权限同步还有问题，请联系后端团队。"
echo ""
echo "======================================"
echo "🔧 手动测试 API"
echo "======================================"
echo ""
echo "如果需要在命令行测试，请先获取 JWT token："
echo ""
echo "1. 在浏览器登录后，在 Console 执行："
echo "   localStorage.getItem('access_token')"
echo ""
echo "2. 复制返回的 token（不含引号）"
echo ""
echo "3. 执行以下命令（替换 YOUR_TOKEN）："
echo ""
echo '   curl -X GET "http://localhost:9000/api/v1/auth/me" \\'
echo '     -H "Authorization: Bearer YOUR_TOKEN"'
echo ""
echo "======================================"
