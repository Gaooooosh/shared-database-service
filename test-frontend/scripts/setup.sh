#!/bin/bash
# =============================================================================
# 测试前端环境一键设置脚本
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "测试前端环境设置"
echo "=========================================="

# 1. 生成 JWT 密钥
echo ""
echo "[1/4] 生成 JWT 密钥..."
python3 "$SCRIPT_DIR/generate-jwt-keys.py"

# 2. 等待 Casdoor 就绪
echo ""
echo "[2/4] 等待 Casdoor 就绪..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/login > /dev/null 2>&1; then
        echo "✅ Casdoor 已就绪"
        break
    fi
    echo "等待中... ($i/30)"
    sleep 1
done

# 3. 配置 Casdoor 测试环境
echo ""
echo "[3/4] 配置 Casdoor 测试环境..."
python3 "$SCRIPT_DIR/setup-casdoor.py"

# 4. 安装前端依赖
echo ""
echo "[4/4] 安装前端依赖..."
cd "$PROJECT_ROOT"
if [ ! -d "node_modules" ]; then
    echo "安装 npm 依赖..."
    npm install
else
    echo "依赖已安装"
fi

echo ""
echo "=========================================="
echo "✅ 环境设置完成!"
echo "=========================================="
echo ""
echo "启动服务:"
echo "  cd $PROJECT_ROOT"
echo "  npm run dev"
echo ""
echo "访问地址:"
echo "  前端: http://localhost:3002"
echo "  后端: http://localhost:9000/api/v1/docs"
echo "  Casdoor: http://localhost:8000"
echo ""
