# API 认证完整指南

## 问题诊断

你遇到的 **401 错误** 是因为：
1. POST/PUT/DELETE 等写操作 API **需要认证**
2. 必须在请求头中携带 Casdoor 签发的 JWT Token

---

## 正确的请求格式

### 1. 必需的 HTTP Header

所有需要认证的请求必须携带：

```http
Authorization: Bearer <your-casdoor-jwt-token>
Content-Type: application/json
```

### 2. 必需的请求体字段

创建记录时，以下字段**必填**：

```json
{
  "app_identifier": "...",      // 必填：应用标识符
  "collection_type": "...",          // 必填：数据类型
  "title": "...",                // 可选：标题
  "description": "...",              // 可选：描述
  "payload": {...},                   // 可选：业务数据（默认为 {}）
  "is_published": true                // 可选：是否发布（默认为 true）
}
```

**关键字段说明**：
- `app_identifier` - 应用标识符，用于多应用数据隔离
- `collection_type` - 数据类型，用于区分同一应用中的不同数据

### 2. 获取 JWT Token 的步骤

#### 步骤 1: 从 Casdoor 登录获取 Token

访问 Casdoor 登录页面：
```
http://localhost:8000/oauth/authorize?
  client_id=c7152acfa4e28bee5910
  response_type=token
  redirect_uri=http://localhost:3000/callback
  scope=openid profile email
```

登录成功后，Casdoor 会将 token 放在 URL fragment 中：
```
http://localhost:3000/callback#access_token=eyJhbGciOiJSUzI1NiI...
```

#### 步骤 2: 前端存储 Token

```javascript
// 从 URL 解析 token
const hash = window.location.hash.substring(1);
const params = new URLSearchParams(hash);
const accessToken = params.get('access_token');

// 存储到 localStorage
localStorage.setItem('access_token', accessToken);
```

#### 步骤 3: 在 API 请求中使用 Token

```javascript
// 正确的请求格式
const response = await fetch('http://localhost:9000/api/v1/records', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`  // ← 必须带 Bearer 前缀
  },
  body: JSON.stringify({
    app_identifier: 'choir-app',
    collection_type: 'song',
    payload: {
      title: '测试歌曲',
      artist: '测试艺人'
    }
  })
});
```

---

## 前端完整示例

### React 示例

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

// 配置 axios 拦截器自动添加 token
const api = axios.create({
  baseURL: 'http://localhost:9000/api/v1',
});

// 请求拦截器
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 - 处理 401 错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 失效，跳转到 Casdoor 登录
      const loginUrl = new URL('http://localhost:8000/oauth/authorize');
      loginUrl.searchParams.set('client_id', 'c7152acfa4e28bee5910');
      loginUrl.searchParams.set('response_type', 'token');
      loginUrl.searchParams.set('redirect_uri', window.location.origin + '/callback');
      loginUrl.searchParams.set('scope', 'openid profile email');
      window.location.href = loginUrl.toString();
    }
    return Promise.reject(error);
  }
);

function App() {
  const [user, setUser] = useState(null);

  // 获取当前用户信息
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await api.get('/auth/me');
        setUser(response.data);
      } catch (error) {
        console.error('获取用户信息失败:', error);
      }
    };
    fetchUser();
  }, []);

  // 创建记录
  const createRecord = async () => {
    try {
      const response = await api.post('/records', {
        app_identifier: 'choir-app',
        collection_type: 'song',
        payload: {
          title: '新歌曲',
          duration: 180
        }
      });
      console.log('创建成功:', response.data);
    } catch (error) {
      console.error('创建失败:', error.response?.data);
    }
  };

  return (
    <div>
      <h1>Unified Backend Platform</h1>
      {user ? (
        <div>
          <p>欢迎, {user.display_name}</p>
          <button onClick={createRecord}>创建记录</button>
        </div>
      ) : (
        <a href="http://localhost:8000/oauth/authorize?client_id=c7152acfa4e28bee5910&response_type=token&redirect_uri=http://localhost:3000/callback&scope=openid+profile+email">
          登录
        </a>
      )}
    </div>
  );
}

export default App;
```

### Vue 3 示例

```vue
<template>
  <div>
    <h1>Unified Backend Platform</h1>
    <div v-if="user">
      <p>欢迎, {{ user.display_name }}</p>
      <button @click="createRecord">创建记录</button>
    </div>
    <a v-else :href="loginUrl">登录</a>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:9000/api/v1',
});

// 添加 token 到请求
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const user = ref(null);
const loginUrl = 'http://localhost:8000/oauth/authorize?client_id=c7152acfa4e28bee5910&response_type=token&redirect_uri=http://localhost:3000/callback&scope=openid+profile+email';

const fetchUser = async () => {
  try {
    const response = await api.get('/auth/me');
    user.value = response.data;
  } catch (error) {
    console.error('获取用户信息失败:', error);
  }
};

const createRecord = async () => {
  try {
    const response = await api.post('/records', {
      app_identifier: 'choir-app',
      collection_type: 'song',
      payload: { title: '新歌曲' }
    });
    console.log('创建成功:', response.data);
  } catch (error) {
    console.error('创建失败:', error.response?.data);
  }
};

onMounted(fetchUser);

// 从 URL 解析 token (在 callback 页面使用)
const urlParams = new URLSearchParams(window.location.hash.substring(1));
const accessToken = urlParams.get('access_token');
if (accessToken) {
  localStorage.setItem('access_token', accessToken);
  window.location.href = '/';
}
</script>
```

---

## API 端点分类

### ✅ 不需要认证的端点

```http
GET  /api/v1/records           # 查询记录列表
GET  /api/v1/records/{id}      # 查询单条记录（仅已发布内容）
```

### 🔒 需要认证的端点

```http
# 认证相关
GET  /api/v1/auth/me           # 获取当前用户信息
POST /api/v1/auth/refresh      # 刷新用户信息

# 记录操作（写操作需要认证）
POST   /api/v1/records         # 创建记录
PUT    /api/v1/records/{id}    # 更新记录
PATCH  /api/v1/records/{id}    # 部分更新
DELETE /api/v1/records/{id}    # 删除记录

# 批量操作
POST /api/v1/records/batch     # 批量创建
PUT  /api/v1/records/batch     # 批量更新
DELETE /api/v1/records/batch   # 批量删除

# 文件管理
POST /api/v1/files/upload      # 上传文件
```

---

## 常见错误

### 错误 1: `Field required` - 缺少 Authorization header (400 Bad Request)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["header", "authorization"],
      "msg": "Field required"
    }
  ]
}
```

**原因**: 没有提供 `Authorization` header

**解决**: 添加 `Authorization: Bearer <token>`

---

### 错误 2: `Field required` - 缺少必填字段 (422 Unprocessable Entity)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "app_identifier"],
      "msg": "Field required"
    },
    {
      "type": "missing",
      "loc": ["body", "collection_type"],
      "msg": "Field required"
    }
  ]
}
```

**原因**: 请求体缺少必填字段 `app_identifier` 或 `collection_type`

**解决**: 确保请求体包含这两个必填字段
```json
{
  "app_identifier": "choir-app",
  "collection_type": "song",
  "payload": {...}
}
```

---

### 错误 3: `Invalid authentication credentials` (401 Unauthorized)

```json
{
  "detail": "Invalid authentication credentials: Invalid token: Error decoding token headers."
}
```

**原因**: Token 格式错误或已过期

**解决**:
1. 检查 token 是否从 Casdoor 获取
2. 检查 token 是否过期（默认 24 小时）
3. 重新从 Casdoor 登录获取新 token

---

### 错误 3: CORS 错误

```
Access to fetch at 'http://localhost:9000/api/v1/records' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**解决**: 确保 CORS 配置包含你的前端域名

```bash
# 检查 .env 文件
CORS_ORIGINS=http://localhost:3000,http://localhost:3002
```

---

## 测试命令

### 使用 curl 测试

```bash
# 1. GET 请求（不需要认证）
curl "http://localhost:9000/api/v1/records?app_identifier=choir-app&page_size=10"

# 2. POST 请求（需要 token - 替换 YOUR_TOKEN）
curl -X POST "http://localhost:9000/api/v1/records" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "app_identifier": "choir-app",
    "collection_type": "song",
    "payload": {"title": "测试歌曲"}
  }'

# 3. 获取用户信息（需要 token）
curl "http://localhost:9000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Casdoor 配置信息

| 配置项 | 值 |
|--------|-----|
| Casdoor 地址 | http://localhost:8000 |
| Client ID | c7152acfa4e28bee5910 |
| 授权端点 | /oauth/authorize |
| Token 类型 | Bearer (JWT RS256) |
| Token 有效期 | 24 小时（默认） |

---

## 下一步

1. **在你的前端集成 Casdoor SDK**:
   ```bash
   npm install casdoor-js-sdk
   ```

2. **配置 Casdoor SDK**:
   ```javascript
   import CasdoorSDK from 'casdoor-js-sdk';

   const sdk = new CasdoorSDK({
     serverUrl: 'http://localhost:8000',
     clientId: 'c7152acfa4e28bee5910',
     appName: 'app-unified-backend',
     redirectPath: '/callback',
   });
   ```

3. **参考文档**:
   - Casdoor 文档: http://localhost:8000/swagger
   - API 文档: http://localhost:9000/api/v1/docs
   - 开发者指南: `docs/DEVELOPER_GUIDE.md`
