# Casdoor 快速参考指南

本文档提供 Casdoor SSO 的快速参考信息，帮助开发者快速集成和使用。

---

## 目录

- [快速开始](#快速开始)
- [默认账户](#默认账户)
- [用户标识格式](#用户标识格式)
- [应用配置](#应用配置)
- [权限组配置 ✨](#权限组配置)
- [OAuth 2.0 认证流程](#oauth-20-认证流程)
- [密码管理](#密码管理)
- [常见问题](#常见问题)

---

## 快速开始

### 访问 Casdoor 管理界面

```bash
# 本地开发环境
http://localhost:8000

# 生产环境
https://casdoor.yourdomain.com
```

### 服务地址

| 环境 | 访问地址 | 说明 |
|------|----------|------|
| 开发 | `http://localhost:8000` | Casdoor 管理界面 |
| 生产 | `https://casdoor.yourdomain.com` | 需配置域名 |

---

## 默认账户

### 管理员账户

| 项目 | 值 |
|------|-----|
| **用户名** | `built-in/admin` |
| **密码** | `admin` |
| **组织** | `built-in` |
| **Email** | `admin@example.com` |

**⚠️ 重要提示**：
- 首次登录后请立即修改默认密码
- 生产环境必须使用强密码
- 保存好管理员账户信息

---

## 用户标识格式

### Casdoor 用户 ID 格式

Casdoor 中的用户以 **`<organization>/<username>`** 格式标识：

```
built-in/admin          → 默认管理员
built-in/user1          → built-in 组织下的 user1
my-org/alice            → my-org 组织下的 alice
```

### API 中的用户 ID

在 API 调用和 JWT Token 中，`sub` 字段包含完整的用户 ID：

```json
{
  "sub": "built-in/admin",
  "name": "admin",
  "displayName": "Administrator",
  "email": "admin@example.com",
  "owner": "built-in"
}
```

---

## 应用配置

### 创建新应用

1. **登录 Casdoor 管理界面**
   - 访问 `http://localhost:8000`
   - 使用管理员账户登录

2. **添加应用**
   - 点击左侧菜单 `Applications`
   - 点击 `Add Application` 按钮

3. **配置应用**
   ```
   名称:           my-app
   显示名称:       我的应用
   组织:           built-in
   认证方式:       OAuth 2.0 + JWT
   回调 URL:       http://localhost:3000/callback
   ```

4. **记录应用信息**
   - `Client ID` - 客户端标识符
   - `Client Secret` - 客户端密钥
   - `Redirect URL` - 回调地址
   - `Certificate` - JWT 验证证书

---

## 权限组配置 ✨

### 概述

Casdoor 权限组（Permission Groups）可以同步到本地角色系统，实现统一的权限管理。

### 创建权限组

1. **登录 Casdoor 管理界面**
   - 访问 `http://localhost:8000`
   - 使用管理员账户登录

2. **添加权限组**
   - 点击左侧菜单 `Permission groups`
   - 点击 `Add Permission Group` 按钮

3. **配置权限组**
   ```
   名称:           editors
   显示名称:       编辑员组
   组织:           built-in
   描述:           允许管理文章和评论
   ```

4. **添加权限**
   - 在权限组详情页，点击 `Add Permission`
   - 配置权限规则：
     ```
     资源类型:       posts
     操作类型:       create,read,update
     资源所有者:     * (所有)
     效果:           Allow
     ```

### 常见权限组配置

#### 编辑员权限组

**组名**: `editors`

**权限**:
| 资源 | 操作 | 说明 |
|------|------|------|
| posts | create, read, update | 文章管理（不含删除） |
| comments | create, read | 评论管理 |
| files | upload, read | 文件上传 |

#### 版主权限组

**组名**: `moderators`

**权限**:
| 资源 | 操作 | 说明 |
|------|------|------|
| threads | read, update | 主题管理 |
| posts | create, read, update | 帖子管理 |
| comments | create, read, delete | 评论管理（含删除） |

### 同步到本地角色

当用户登录时，后端会自动：

1. 读取用户的 Casdoor 权限组
2. 同步权限组到本地 `Role` 表
3. 创建 `UserRoleAssignment` 关联
4. 缓存用户权限到 Redis

**配置要求**：
- 权限组名称 (`name`) 必须与本地角色名称一致
- 或在本地角色中设置 `casdoor_group_name` 字段匹配

### 权限组 API 管理

后端提供完整的 API 管理权限和角色：

```bash
# 获取当前用户权限
GET /api/v1/permissions/me

# 创建角色（关联 Casdoor 权限组）
POST /api/v1/permissions/roles
{
  "name": "editors",
  "display_name": "编辑员",
  "permission_ids": ["perm-1", "perm-2"],
  "casdoor_group_name": "editors"
}

# 分配用户角色
POST /api/v1/permissions/users/{user_id}/roles
{
  "role_id": "role-uuid"
}
```

---

## OAuth 2.0 认证流程

### 认证流程图

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   前端应用   │         │   Casdoor    │         │   后端API   │
└─────────────┘         └──────────────┘         └─────────────┘
       │                        │                        │
       │  1. 点击登录           │                        │
       ├──────────────────────>│                        │
       │  /login/oauth/authorize                         │
       │                        │                        │
       │  2. 用户登录           │                        │
       │                        │                        │
       │  3. 返回 authorization code                     │
       │<──────────────────────┤                        │
       │                        │                        │
       │  4. 用 code 换取 token                          │
       ├──────────────────────>│                        │
       │  /api/login/oauth/access_token                 │
       │                        │                        │
       │  5. 返回 JWT Token     │                        │
       │<──────────────────────┤                        │
       │                        │                        │
       │  6. 携带 Token 调用 API                         │
       ├──────────────────────────────────────────────>│
       │                        │                        │
       │  7. 验证 Token，返回用户信息                     │
       │<──────────────────────────────────────────────┤
```

### 前端集成代码

```typescript
// 配置
const CASDOOR_ORIGIN = 'http://localhost:8000';
const CLIENT_ID = 'your-client-id';
const REDIRECT_URI = 'http://localhost:3000/callback';

// 1. 登录跳转
function login() {
  const authUrl = `${CASDOOR_ORIGIN}/login/oauth/authorize?` +
    `client_id=${CLIENT_ID}&` +
    `redirect_uri=${encodeURIComponent(REDIRECT_URI)}&` +
    `response_type=code&` +
    `scope=openid profile email`;

  window.location.href = authUrl;
}

// 2. 处理回调
async function handleCallback(code: string) {
  const response = await fetch(`${CASDOOR_ORIGIN}/api/login/oauth/access_token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      client_id: CLIENT_ID,
      client_secret: 'your-client-secret',
      code: code,
      grant_type: 'authorization_code'
    })
  });

  const data = await response.json();
  const token = data.access_token;

  // 保存 Token
  localStorage.setItem('jwt_token', token);

  return token;
}

// 3. 调用后端 API
async function callBackendAPI() {
  const token = localStorage.getItem('jwt_token');

  const response = await fetch('http://localhost:9000/api/v1/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return response.json();
}
```

---

## 密码管理

### 生成密码哈希

```bash
# 方法1: 使用 Python
python3 -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode())"

# 方法2: 使用 Node.js
node -e "const bcrypt = require('bcrypt'); console.log(bcrypt.hashSync('your_password', 10));"

# 方法3: 在线工具
# https://bcrypt-generator.com/
```

### 重置管理员密码

#### 方法1: 通过 Casdoor 界面

```
1. 登录 Casdoor 管理界面
2. 进入 Users → built-in/admin
3. 点击修改密码
4. 输入新密码并保存
```

#### 方法2: 通过 PostgreSQL 数据库

```bash
# 1. 生成密码哈希
HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw(b'new_password', bcrypt.gensalt()).decode())")

# 2. 更新数据库
docker compose exec postgres psql -U casdoor -d casdoor \
  -c "UPDATE \"user\" SET password='$HASH' WHERE owner='built-in' AND name='admin';"
```

#### 方法3: 查询当前用户

```bash
# 查看所有用户
docker compose exec postgres psql -U casdoor -d casdoor \
  -c "SELECT owner, name, email, created_at FROM \"user\" WHERE owner='built-in';"
```

---

## 常见问题

### Q1: 登录提示 "User does not exist"

**可能原因**：
- 用户名格式错误
- 输入了 `admin` 而不是 `built-in/admin`

**解决方案**：
- 使用正确的用户名格式：`built-in/admin`
- 检查组织名称是否为 `built-in`

### Q2: Token 验证失败

**可能原因**：
- JWT_SECRET 不一致
- Token 已过期
- 签名算法不匹配

**解决方案**：
```bash
# 检查 JWT_SECRET 是否一致
# docker-compose.yml 中的 casdoor 服务
# 和 backend 服务的 JWT_SECRET 必须相同

# 查看当前配置
docker compose exec backend env | grep JWT_SECRET
docker compose exec casdoor env | grep jwtSecret
```

### Q3: 回调 URL 不匹配

**可能原因**：
- Casdoor 应用配置的回调 URL 与实际不符
- 前端地址或端口变化

**解决方案**：
1. 登录 Casdoor 管理界面
2. 进入 Applications → 选择应用
3. 修改 Redirect URLs，添加当前前端地址

### Q4: 如何创建新用户

**方法1: 通过 Casdoor 界面**
```
1. 登录 Casdoor 管理界面
2. 进入 Users
3. 点击 Add User
4. 填写用户信息并保存
```

**方法2: 通过 API**
```bash
# 需要管理员 Token
curl -X POST http://localhost:8000/api/add-user \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "built-in",
    "name": "newuser",
    "displayName": "New User",
    "email": "newuser@example.com",
    "password": "user_password"
  }'
```

### Q5: 如何查看 JWT Token 内容

```bash
# 使用 jwt.io 在线解码
# https://jwt.io/

# 或使用命令行
echo "YOUR_JWT_TOKEN" | jq -R 'split(".") | .[1] | @base64d | fromjson'
```

---

## 配置参考

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CASDOOR_ORIGIN` | Casdoor 服务地址 | `http://localhost:8000` |
| `CASDOOR_PORT` | Casdoor 端口 | `8000` |
| `JWT_SECRET` | JWT 签名密钥 | - (必须配置) |
| `JWT_ALGORITHM` | 加密算法 | `HS256` |

### Docker Compose 配置

```yaml
casdoor:
  image: casbin/casdoor:latest
  environment:
    driverName: "postgres"
    dataSourceName: "postgres://casdoor:password@postgres:5432/casdoor?sslmode=disable"
    origin: "${CASDOOR_ORIGIN}"
    jwtSecret: "${JWT_SECRET}"
  ports:
    - "8000:8000"
  depends_on:
    - postgres
```

---

## 相关链接

- [Casdoor 官方文档](https://casdoor.github.io/docs/)
- [Casdoor GitHub](https://github.com/casdoor/casdoor)
- [OAuth 2.0 规范](https://oauth.net/2/)
- [JWT 说明](https://jwt.io/)

---

**更新时间**: 2024-12-24
**适用版本**: Casdoor latest
