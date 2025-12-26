#!/bin/bash
# =============================================================================
# JWT 证书生成脚本 - 为 Casdoor 测试应用生成 RSA 密钥对
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEYS_DIR="$SCRIPT_DIR/../keys"
ORGANIZATION="test-org"
APPLICATION="test-app"

# 创建密钥目录
mkdir -p "$KEYS_DIR"

echo "=========================================="
echo "生成 JWT RSA 密钥对"
echo "=========================================="

# 生成私钥 (RSA 2048位)
openssl genrsa -out "$KEYS_DIR/private.pem" 2048

# 生成公钥
openssl rsa -in "$KEYS_DIR/private.pem" -pubout -out "$KEYS_DIR/public.pem"

# 设置权限
chmod 600 "$KEYS_DIR/private.pem"
chmod 644 "$KEYS_DIR/public.pem"

echo "✅ 私钥: $KEYS_DIR/private.pem"
echo "✅ 公钥: $KEYS_DIR/public.pem"

# 输出公钥内容（用于配置到Casdoor）
echo ""
echo "=========================================="
echo "公钥内容 (复制到Casdoor应用配置):"
echo "=========================================="
cat "$KEYS_DIR/public.pem"

echo ""
echo "=========================================="
echo "密钥生成完成!"
echo "=========================================="
echo "私钥路径: $KEYS_DIR/private.pem"
echo "请妥善保管私钥，不要泄露!"
