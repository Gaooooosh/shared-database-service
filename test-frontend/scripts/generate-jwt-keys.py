#!/usr/bin/env python3
"""
JWT RSA 密钥对生成脚本

生成用于 Casdoor RS256 JWT 签名的 RSA 密钥对
"""

import os
import sys
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

# 密钥目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KEYS_DIR = os.path.join(SCRIPT_DIR, "../keys")

# 生成密钥
def generate_rsa_keypair():
    """生成 RSA 密钥对"""
    print("=" * 50)
    print("生成 JWT RSA 密钥对")
    print("=" * 50)

    # 创建密钥目录
    os.makedirs(KEYS_DIR, exist_ok=True)

    # 生成私钥
    print("生成私钥...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )

    # 保存私钥 (PEM格式)
    private_pem_path = os.path.join(KEYS_DIR, "private.pem")
    with open(private_pem_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    os.chmod(private_pem_path, 0o600)
    print(f"✅ 私钥已保存: {private_pem_path}")

    # 生成公钥
    public_key = private_key.public_key()

    # 保存公钥 (PEM格式)
    public_pem_path = os.path.join(KEYS_DIR, "public.pem")
    with open(public_pem_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    print(f"✅ 公钥已保存: {public_pem_path}")

    # 输出公钥内容
    print("\n" + "=" * 50)
    print("公钥内容 (复制到Casdoor应用配置):")
    print("=" * 50)
    with open(public_pem_path, "r") as f:
        public_key_content = f.read()
        print(public_key_content)

    # 输出配置说明
    print("\n" + "=" * 50)
    print("配置说明")
    print("=" * 50)
    print("1. 登录 Casdoor 管理后台")
    print("2. 进入 Applications -> test-app")
    print("3. 点击 'Edit'")
    print("4. 找到 'Cert' 字段")
    print("5. 创建新的 Certificate 或使用内置证书")
    print("6. 将公钥内容粘贴到证书配置中")
    print("7. 设置 Token 算法为 RS256")
    print("\n⚠️  请妥善保管私钥，不要泄露!")
    print(f"私钥路径: {private_pem_path}")

    return private_pem_path, public_pem_path


if __name__ == "__main__":
    try:
        generate_rsa_keypair()
        print("\n✅ 密钥生成完成!")
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        sys.exit(1)
