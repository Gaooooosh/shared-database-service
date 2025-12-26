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

---

## 前端集成最佳实践 ⭐

基于实际项目经验，以下是在前端集成 Casdoor OAuth 2.0 的最佳实践。

### 架构选择：标准 OAuth 2.0 vs PKCE

**✅ 推荐：标准 OAuth 2.0 Authorization Code Flow**

适用场景：
- 后端可以安全存储 `client_secret`
- 后端能够验证 JWT 签名（RS256）
- 机密客户端（Confidential Client）

**❌ 不推荐：PKCE Flow**

原因：
- PKCE 主要用于公共客户端（如原生 App、纯 SPA）
- 增加状态管理复杂度
- 容易出现 "Invalid State" 错误
- 本项目后端已有完整的 JWT 验证能力

### 使用 Casdoor JS SDK 的正确方式

**⚠️ 重要**：仅使用 SDK 生成 URL，手动处理 token 交换

#### 1. SDK 初始化（单例模式）

```typescript
// lib/casdoor.ts
import Sdk from "casdoor-js-sdk";
import { config } from "./config";

let sdkInstance: Sdk | null = null;

export function getCasdoorConfig() {
  return {
    serverUrl: config.casdoorUrl,
    clientId: config.clientId,
    appName: config.appName,
    organizationName: "Aiyueaijia",  // 替换为你的组织名
    redirectPath: "/auth/callback",
  };
}

export function getSdk(): Sdk | null {
  if (typeof window === "undefined") {
    return null;
  }

  if (sdkInstance) {
    return sdkInstance;
  }

  const sdkConfig = {
    ...getCasdoorConfig(),
    redirectPath: window.location.origin + getCasdoorConfig().redirectPath,
  };

  sdkInstance = new Sdk(sdkConfig);
  return sdkInstance;
}
```

#### 2. 登录实现（推荐方式）

```typescript
// ✅ 正确：生成 URL 后手动跳转
export function signIn() {
  const sdk = getSdk();
  if (!sdk) return;

  const signinUrl = sdk.getSigninUrl();  // 生成标准 OAuth URL
  window.location.href = signinUrl;       // 手动跳转
}

// ❌ 错误：使用 SDK 的 PKCE 方法（会导致 "Invalid State" 错误）
export function signInWrong() {
  const sdk = getSdk();
  sdk.signin_redirect();  // 不要使用！
}
```

#### 3. OAuth 回调处理（关键）

```typescript
// app/auth/callback/page.tsx (Next.js App Router)
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { config } from '@/lib/config';
import { setAuthToken } from '@/lib/config';
import { useAuthStore } from '@/stores/authStore';

export default function AuthCallbackPage() {
  const router = useRouter();
  const setUser = useAuthStore((state) => state.setUser);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // 1. 获取 authorization code
        const params = new URLSearchParams(window.location.search);
        const code = params.get('code');

        if (!code) {
          router.push('/login?error=no_code');
          return;
        }

        // 2. 交换 token（手动调用 Casdoor token endpoint）
        const tokenResponse = await fetch(
          `${config.casdoorUrl}/api/login/oauth/access_token`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              grant_type: 'authorization_code',
              client_id: config.clientId,
              client_secret: config.clientSecret,  // 使用 client_secret
              code: code,
            }),
          }
        );

        if (!tokenResponse.ok) {
          router.push('/login?error=token_exchange_failed');
          return;
        }

        const tokenData = await tokenResponse.json();

        if (!tokenData.access_token) {
          router.push('/login?error=no_token_in_response');
          return;
        }

        // 3. 保存 token 到 localStorage
        setAuthToken(tokenData.access_token);

        // 4. 解析 JWT payload 获取用户信息
        const tokenParts = tokenData.access_token.split('.');
        if (tokenParts.length === 3) {
          const payload = JSON.parse(atob(tokenParts[1]));

          // 5. 🔥 关键：更新 authStore（状态管理）
          const userData = {
            id: payload.sub,
            casdoor_id: payload.sub,
            display_name: payload.displayName || payload.name,
            email: payload.email,
            avatar: payload.avatar || null,
            is_superuser: payload.isAdmin || false,
            permissions: payload.permissions || [],
            roles: payload.roles || [],
            created_at: payload.createdTime,
            updated_at: payload.updatedTime,
          };

          setUser(userData);  // ⚠️ 必须调用！否则登录状态不同步
        }

        // 6. 跳转到首页
        router.push('/');
      } catch (error) {
        console.error('❌ Callback 处理失败:', error);
        router.push('/login?error=callback_failed');
      }
    };

    handleCallback();
  }, [router, setUser]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto" />
        <p className="text-muted-foreground">正在登录...</p>
      </div>
    </div>
  );
}
```

#### 4. 认证状态管理（Zustand 示例）

```typescript
// stores/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AuthUser } from '@/types/api';

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  setUser: (user: AuthUser | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      setUser: (user) => set({ user, isAuthenticated: !!user, error: null }),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_token');
        }
        set({ user: null, isAuthenticated: false, error: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
```

### 环境变量配置

#### 前端环境变量（.env.local）

```env
# Casdoor 配置
NEXT_PUBLIC_CASDOOR_URL=https://auth.aiyueaijia.com
NEXT_PUBLIC_CASDOOR_APP_NAME=aiyueaijia_main_page
NEXT_PUBLIC_CASDOOR_CLIENT_ID=c7152acfa4e28bee5910
CASDOOR_CLIENT_SECRET=40314734dc3b413cd5fe97e37ebc71bb14f7d206

# ⚠️ 重要：回调 URL 必须与 Casdoor 后台配置一致
NEXT_PUBLIC_CASDOOR_REDIRECT_URI=http://localhost:3000/auth/callback

# Casdoor 证书配置（用于验证 JWT）
CASDOOR_CERT=Aiyueaijia/aiyueaijia-jwt
```

#### Docker Compose 配置

```yaml
services:
  frontend:
    build:
      context: ./frontend
      args:
        # 构建时参数
        NEXT_PUBLIC_CASDOOR_URL: ${CASDOOR_URL}
        NEXT_PUBLIC_CASDOOR_CLIENT_ID: ${CASDOOR_CLIENT_ID}
    environment:
      # 运行时参数（必须重复）
      NEXT_PUBLIC_CASDOOR_URL: ${CASDOOR_URL}
      NEXT_PUBLIC_CASDOOR_CLIENT_ID: ${CASDOOR_CLIENT_ID}
      CASDOOR_CLIENT_SECRET: ${CASDOOR_CLIENT_SECRET}
```

**⚠️ 注意**：
- `NEXT_PUBLIC_*` 变量在构建时和运行时都需要
- `CASDOOR_CLIENT_SECRET` 仅在服务端可用，不要暴露到客户端
- 修改环境变量后必须重新构建 Docker 镜像

---

## 常见问题诊断与解决 ⭐

### 问题 1：登录后"闪回"到登录页

**症状**：
- 用户登录成功
- Token 保存成功
- 但页面立即跳转回登录页
- Header 显示"登录"按钮而非用户信息

**根本原因**：authStore 状态未更新

**诊断步骤**：

```javascript
// 1. 在浏览器控制台运行
const store = JSON.parse(localStorage.getItem('auth-storage'));
console.log('isAuthenticated:', store?.state?.isAuthenticated);
console.log('user:', store?.state?.user);

// 2. 如果 isAuthenticated = false，说明 authStore 未更新
```

**解决方案**：

```typescript
// ❌ 错误：只保存 localStorage
setAuthToken(tokenData.access_token);
localStorage.setItem('user', JSON.stringify(payload));
// 问题：authStore.user 仍然是 null

// ✅ 正确：同步更新 authStore
const userData = {
  id: payload.sub,
  display_name: payload.displayName,
  email: payload.email,
  // ... 其他字段
};
setUser(userData);  // 🔥 关键：更新 Zustand store
```

### 问题 2："Invalid State" 错误

**症状**：
- 使用 `sdk.signin_redirect()` 后报错
- 或回调时提示 state 参数不匹配

**根本原因**：使用了 PKCE Flow，但 SDK 在每次页面加载时生成新的 state

**解决方案**：

```typescript
// ❌ 不要使用
sdk.signin_redirect();

// ✅ 使用手动跳转
const signinUrl = sdk.getSigninUrl();
window.location.href = signinUrl;
```

### 问题 3：chrome-error://chromewebdata/

**症状**：
- 点击登录后浏览器跳转到错误页面
- 控制台显示 `chrome-error://chromewebdata/`

**根本原因**：使用了 `sdk.signin_redirect()` 的导航方法

**解决方案**：同问题 2，改用手动跳转

### 问题 4：Token 交换失败

**症状**：
- 回调处理时 `/api/login/oauth/access_token` 返回错误
- 控制台显示 400 或 401 错误

**诊断步骤**：

```javascript
// 1. 检查环境变量
console.log('Client ID:', process.env.NEXT_PUBLIC_CASDOOR_CLIENT_ID);
console.log('Client Secret:', process.env.CASDOOR_CLIENT_SECRET);
console.log('Casdoor URL:', process.env.NEXT_PUBLIC_CASDOOR_URL);

// 2. 检查 code 参数
const code = new URLSearchParams(window.location.search).get('code');
console.log('Code:', code?.substring(0, 20) + '...');
```

**常见原因**：
- Client ID 或 Secret 配置错误
- Casdoor 服务地址错误
- Code 已过期或已使用

**解决方案**：
1. 检查 `.env.local` 文件配置
2. 确认 Casdoor 应用配置的 Client ID 和 Secret
3. 重新构建 Docker 容器（如果使用 Docker）

### 问题 5：回调 URL 不匹配

**症状**：
- 登录后跳转到错误页面
- Casdoor 提示 "redirect_uri_mismatch"

**解决方案**：

1. **检查 Casdoor 应用配置**：
   - 登录 Casdoor 管理界面
   - 进入 Applications → 选择应用
   - 查看 Redirect URLs 配置

2. **添加当前前端地址**：
   ```
   开发环境: http://localhost:3000/auth/callback
   生产环境: https://yourdomain.com/auth/callback
   ```

3. **确认前端配置一致**：
   ```env
   NEXT_PUBLIC_CASDOOR_REDIRECT_URI=http://localhost:3000/auth/callback
   ```

---

## 调试技巧 ⭐

### 1. 添加详细日志

在 OAuth 流程的关键步骤添加日志（使用 emoji 标记）：

```typescript
// 登录流程
console.log('🔄 OAuth callback triggered');
console.log('✅ 获取到 code:', code.substring(0, 20) + '...');
console.log('🔄 正在交换 access token...');
console.log('✅ Token 交换成功');
console.log('📝 Token payload:', payload);
console.log('✅ 更新 authStore 用户信息:', userData);
console.log('🔄 跳转到首页...');
```

### 2. 验证 URL 参数

```typescript
// 检查必需的 OAuth 参数
const requiredParams = ['client_id', 'redirect_uri', 'response_type', 'scope', 'state'];
const missingParams = requiredParams.filter(param => !signinUrl.includes(param + '='));

if (missingParams.length > 0) {
  console.error('❌ Missing required parameters:', missingParams);
  console.error('Generated URL:', signinUrl);
  return;
}

console.log('✅ 所有必需参数存在');
```

### 3. 检查 Store 状态

```typescript
// 在浏览器控制台
localStorage.getItem('auth-storage');  // 查看 Zustand 持久化数据
localStorage.getItem('auth_token');    // 查看 token

// 解码 JWT
const token = localStorage.getItem('auth_token');
const payload = JSON.parse(atob(token.split('.')[1]));
console.log('JWT Payload:', payload);
```

### 4. 测试清单

**开发环境测试**：
- [ ] 点击登录按钮，正确跳转到 Casdoor
- [ ] Casdoor 授权页面显示正确的应用名称
- [ ] 登录后正确跳转回 callback URL
- [ ] Token 交换成功（控制台无错误）
- [ ] 用户信息正确解析
- [ ] authStore 状态正确更新
- [ ] Header 显示用户头像和名称
- [ ] 刷新页面后登录状态保持

**生产环境测试**：
- [ ] HTTPS 配置正确
- [ ] 环境变量配置正确（无硬编码）
- [ ] Docker 容器正常启动
- [ ] 回调 URL 配置正确（内外网）
- [ ] 日志输出正常（无敏感信息）

---

## 前端集成代码示例

### 基础集成（不使用 SDK）

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
