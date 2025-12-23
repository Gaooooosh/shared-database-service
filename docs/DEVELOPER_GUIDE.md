# Unified Backend Platform - 开发者接入指南

本文档面向前端/移动端开发者，详细说明如何将你的应用接入统一后端平台，实现用户认证、数据存储和文件管理。

---

## 📋 目录

- [快速开始](#快速开始)
- [一、用户认证接入](#一用户认证接入)
- [二、数据库 CRUD 操作](#二数据库-crud-操作)
- [三、文件管理](#三文件管理)
- [四、完整示例](#四完整示例)
- [五、常见问题](#五常见问题)

---

## 快速开始

### 环境准备

确保你的后端服务已经启动：

```bash
# 启动所有服务
docker compose up -d

# 验证服务状态
curl http://localhost:9000/health
```

### 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| Backend API | http://localhost:9000 | 主 API 服务 |
| API 文档 | http://localhost:9000/api/v1/docs | Swagger 文档 |
| Casdoor SSO | http://localhost:8000 | 用户认证 |

### 识别你的应用

每个应用需要一个唯一的 `app_identifier`，用于数据隔离：

```javascript
// 示例应用标识符
const APP_IDENTIFIER = 'blog-app';        // 博客应用
const APP_IDENTIFIER = 'forum-app';       // 论坛应用
const APP_IDENTIFIER = 'shop-app';        // 电商应用
const APP_IDENTIFIER = 'task-app';        // 任务管理应用
```

---

## 一、用户认证接入

### 1.1 认证流程概述

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   前端应用   │         │   Casdoor    │         │   后端API   │
└─────────────┘         └──────────────┘         └─────────────┘
       │                        │                        │
       │  1. 点击登录           │                        │
       ├──────────────────────>│                        │
       │                        │                        │
       │  2. 用户登录           │                        │
       │                        │                        │
       │  3. 返回 JWT Token     │                        │
       │<──────────────────────┤                        │
       │                        │                        │
       │  4. 携带 Token 调用 API                         │
       ├───────────────────────────────────────────────>│
       │                        │                        │
       │  5. 验证 Token，返回用户信息                     │
       │<───────────────────────────────────────────────┤
```

### 1.2 配置 Casdoor 应用

**步骤 1**: 登录 Casdoor 管理后台

```
访问地址: http://localhost:8000
默认用户: 首次访问需要创建管理员账户
```

**步骤 2**: 创建新应用

1. 点击左侧菜单 `Applications`
2. 点击 `Add Application` 按钮
3. 填写应用信息：

```
名称: blog-app (你的应用名)
显示名称: 我的博客应用
组织: built-in (默认)
认证方式: OAuth + JWT
回调 URL: http://localhost:3000/callback (你的前端地址)
```

4. 保存后，记录以下信息：
   - `Client ID`
   - `Client Secret`
   - `Redirect URL`

**步骤 3**: 配置 JWT 密钥

Casdoor 会使用与后端相同的 `JWT_SECRET` 签发 Token，确保后端可以验证。

### 1.3 前端集成示例

#### React + TypeScript 示例

```typescript
// src/services/auth.ts
import axios from 'axios';

const CASDOOR_ORIGIN = 'http://localhost:8000';
const API_BASE = 'http://localhost:9000/api/v1';

// Casdoor 配置
const casdoorConfig = {
  clientId: 'your-client-id',      // 从 Casdoor 后台获取
  redirectUri: 'http://localhost:3000/callback',
  scope: 'openid profile email',
};

// 登录跳转
export function login() {
  const authUrl = `${CASDOOR_ORIGIN}/login/oauth/authorize?` +
    `client_id=${casdoorConfig.clientId}&` +
    `redirect_uri=${encodeURIComponent(casdoorConfig.redirectUri)}&` +
    `response_type=code&` +
    `scope=${encodeURIComponent(casdoorConfig.scope)}`;

  window.location.href = authUrl;
}

// 处理登录回调
export async function handleCallback(code: string) {
  const response = await axios.get(`${CASDOOR_ORIGIN}/api/login/oauth/access_token`, {
    params: {
      client_id: casdoorConfig.clientId,
      client_secret: 'your-client-secret',
      code,
      grant_type: 'authorization_code',
    }
  });

  const token = response.data.access_token;

  // 保存 Token 到 localStorage
  localStorage.setItem('jwt_token', token);

  // 同步用户信息到后端
  await syncUser(token);

  return token;
}

// 同步用户信息到后端
async function syncUser(token: string) {
  const response = await axios.get(`${API_BASE}/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return response.data;
}

// 获取当前用户信息
export async function getCurrentUser() {
  const token = localStorage.getItem('jwt_token');

  if (!token) {
    throw new Error('未登录');
  }

  const response = await axios.get(`${API_BASE}/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return response.data;
}

// 退出登录
export function logout() {
  localStorage.removeItem('jwt_token');
  window.location.href = `${CASDOOR_ORIGIN}/logout`;
}

// API 请求拦截器（自动添加 Token）
const apiClient = axios.create({
  baseURL: API_BASE,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('jwt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;
```

#### 使用示例

```typescript
// src/App.tsx
import { login, handleCallback, getCurrentUser, apiClient } from './services/auth';

function App() {
  useEffect(() => {
    // 检查是否是回调
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    if (code) {
      handleCallback(code).then(() => {
        window.location.href = '/dashboard';
      });
    }
  }, []);

  return (
    <div>
      <button onClick={login}>登录</button>
    </div>
  );
}

// 数据获取示例
function Dashboard() {
  const [user, setUser] = useState(null);
  const [records, setRecords] = useState([]);

  useEffect(() => {
    // 获取当前用户
    getCurrentUser().then(setUser);

    // 获取数据记录
    apiClient.get('/records?app_identifier=blog-app&collection_type=post')
      .then(res => setRecords(res.data.items));
  }, []);

  return (
    <div>
      <h1>欢迎, {user?.display_name}</h1>
      <ul>
        {records.map(record => (
          <li key={record.id}>{record.title}</li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 二、数据库 CRUD 操作

### 2.1 数据模型说明

统一后端使用 `UnifiedRecord` 模型存储所有业务数据：

```typescript
interface UnifiedRecord {
  id: string;                    // 记录 ID (UUID)
  app_identifier: string;        // 应用标识符
  collection_type: string;       // 数据类型
  owner_id?: string;             // 所有者用户 ID
  payload: any;                  // 🔥 业务数据（任意 JSON）
  title?: string;                // 标题
  description?: string;          // 描述
  is_deleted: boolean;           // 是否已删除
  is_published: boolean;         // 是否已发布
  version: number;               // 版本号
  view_count: number;            // 查看次数
  created_at: string;            // 创建时间
  updated_at: string;            // 更新时间
}
```

### 2.2 创建数据记录

**API 端点**: `POST /api/v1/records`

**请求示例**:

```javascript
// 创建博客文章
const response = await apiClient.post('/records', {
  app_identifier: 'blog-app',
  collection_type: 'post',
  payload: {
    // 🔥 你的业务数据（任意结构）
    content: '这是文章内容...',
    category: '技术',
    tags: ['编程', '后端'],
    metadata: {
      wordCount: 1500,
      readTime: 5
    }
  },
  title: '我的第一篇文章',
  description: '文章简介',
  is_published: true
});

console.log(response.data);
// {
//   "id": "550e8400-e29b-41d4-a716-446655440000",
//   "app_identifier": "blog-app",
//   "collection_type": "post",
//   "owner_id": "user-uuid",
//   "payload": { ... },
//   "created_at": "2024-12-23T12:00:00Z"
// }
```

### 2.3 查询数据记录

**API 端点**: `GET /api/v1/records`

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| app_identifier | string | 应用标识符（必填） |
| collection_type | string | 数据类型（必填） |
| owner_id | string | 过滤所有者 |
| is_published | boolean | 过滤发布状态 |
| page | number | 页码（默认 1） |
| page_size | number | 每页数量（默认 20） |
| search | string | 全文搜索 |
| sort_by | string | 排序字段 |
| sort_order | asc/desc | 排序方向 |

**查询示例**:

```javascript
// 1. 查询所有文章
const posts = await apiClient.get('/records', {
  params: {
    app_identifier: 'blog-app',
    collection_type: 'post',
    page: 1,
    page_size: 20
  }
});

// 2. 查询已发布的文章
const publishedPosts = await apiClient.get('/records', {
  params: {
    app_identifier: 'blog-app',
    collection_type: 'post',
    is_published: true,
    sort_by: 'created_at',
    sort_order: 'desc'
  }
});

// 3. 查询当前用户的文章
const myPosts = await apiClient.get('/records', {
  params: {
    app_identifier: 'blog-app',
    collection_type: 'post',
    owner_id: 'current'  // 自动使用当前用户 ID
  }
});

// 4. 全文搜索
const searchResults = await apiClient.get('/records', {
  params: {
    app_identifier: 'blog-app',
    collection_type: 'post',
    search: '关键词'
  }
});
```

**响应格式**:

```javascript
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "app_identifier": "blog-app",
      "collection_type": "post",
      "payload": { /* 业务数据 */ },
      "title": "文章标题",
      "created_at": "2024-12-23T12:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

### 2.4 获取单条记录

**API 端点**: `GET /api/v1/records/{id}`

```javascript
const post = await apiClient.get('/records/550e8400-e29b-41d4-a716-446655440000');
```

### 2.5 更新数据记录

**API 端点**: `PATCH /api/v1/records/{id}`

```javascript
const updated = await apiClient.patch('/records/550e8400-e29b-41d4-a716-446655440000', {
  payload: {
    content: '更新后的内容...',
    tags: ['编程', '后端', '更新']
  },
  title: '新的标题',
  is_published: false
});

// 版本号会自动递增
console.log(updated.data.version);  // 2
```

### 2.6 删除数据记录

**API 端点**: `DELETE /api/v1/records/{id}`

```javascript
// 软删除（推荐）
await apiClient.delete('/records/550e8400-e29b-41d4-a716-446655440000');

// 永久删除
await apiClient.delete('/records/550e8400-e29b-41d4-a716-446655440000?permanent=true');
```

### 2.7 批量操作

**批量创建**:

```javascript
const response = await apiClient.post('/records/batch', {
  items: [
    { app_identifier: 'blog-app', collection_type: 'post', payload: {...} },
    { app_identifier: 'blog-app', collection_type: 'post', payload: {...} }
  ],
  stop_on_error: false  // 遇到错误是否停止
});

// {
//   "total": 2,
//   "succeeded": 2,
//   "failed": 0,
//   "results": [...]
// }
```

**批量更新**:

```javascript
await apiClient.put('/records/batch', {
  ids: ['id1', 'id2', 'id3'],
  updates: { is_published: true },
  stop_on_error: false
});
```

**批量删除**:

```javascript
await apiClient.delete('/records/batch', {
  ids: ['id1', 'id2', 'id3']
});
```

---

## 三、文件管理

### 3.1 文件上传流程

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   前端应用   │         │   后端API    │         │    MinIO    │
└─────────────┘         └──────────────┘         └─────────────┘
       │                        │                        │
       │  1. 上传文件           │                        │
       ├──────────────────────>│                        │
       │                        │                        │
       │  2. 返回文件 URL       │                        │
       │<──────────────────────┤                        │
       │                        │                        │
       │  3. 使用 URL 访问文件                          │
       ├───────────────────────────────────────────────>│
```

### 3.2 直接上传（小文件）

**API 端点**: `POST /api/v1/files/upload`

**示例代码**:

```javascript
// React 上传示例
async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('app_identifier', 'blog-app');
  formData.append('title', '我的图片');
  formData.append('is_public', true);

  const response = await apiClient.post('/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });

  return response.data;
}

// 使用示例
const input = document.querySelector('input[type="file"]');
input.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  const fileInfo = await uploadFile(file);

  console.log('文件上传成功:', fileInfo);
  // {
  //   "id": "file-uuid",
  //   "filename": "photo.jpg",
  //   "public_url": "http://localhost:9100/unified-files/blog-app/2024/12/file-uuid-photo.jpg",
  //   "content_type": "image/jpeg",
  //   "file_size": 1024000
  // }
});
```

### 3.3 预签名上传（大文件）

适用于大文件或前端直传场景：

```javascript
// 步骤 1: 获取预签名上传 URL
async function getPresignedUploadUrl(filename, fileSize) {
  const response = await apiClient.post('/files/upload/presigned', {
    filename: filename,
    content_type: 'video/mp4',
    file_size: fileSize,
    app_identifier: 'blog-app'
  });

  return response.data;
  // {
  //   "file_id": "file-uuid",
  //   "upload_url": "https://minio...",
  //   "headers": {...}
  // }
}

// 步骤 2: 直接上传到 MinIO
async function uploadToMinIO(url, file) {
  await fetch(url, {
    method: 'PUT',
    body: file,
    headers: {
      'Content-Type': file.type
    }
  });
}

// 步骤 3: 确认上传完成
async function confirmUpload(fileId) {
  await apiClient.post('/files/upload/confirm', {
    file_id: fileId
  });
}

// 完整流程
async function uploadLargeFile(file) {
  // 1. 获取预签名 URL
  const { upload_url, file_id } = await getPresignedUploadUrl(
    file.name,
    file.size
  );

  // 2. 上传文件
  await uploadToMinIO(upload_url, file);

  // 3. 确认上传
  await confirmUpload(file_id);

  console.log('大文件上传完成!');
}
```

### 3.4 文件下载

**获取下载链接**:

```javascript
// 获取预签名下载 URL（带签名，有时效性）
const response = await apiClient.get(`/files/${fileId}/download`);

const downloadUrl = response.data.url;
// 7 天有效的下载链接

// 直接下载
window.location.href = downloadUrl;
```

**公开文件直接访问**:

```javascript
// 如果文件设置为 is_public=true，可以直接访问
const file = await apiClient.get(`/files/${fileId}`);

const publicUrl = file.data.public_url;
// http://localhost:9100/unified-files/blog-app/2024/12/...

// 在 img 标签中使用
<img src={publicUrl} alt="图片" />
```

### 3.5 查询文件列表

```javascript
// 查询应用的所有图片
const images = await apiClient.get('/files', {
  params: {
    app_identifier: 'blog-app',
    category: 'image',  // image, video, document, audio
    page: 1,
    page_size: 50
  }
});

// 查询当前用户上传的文件
const myFiles = await apiClient.get('/files', {
  params: {
    app_identifier: 'blog-app',
    owner_id: 'current'
  }
});
```

### 3.6 更新文件元数据

```javascript
await apiClient.patch(`/files/${fileId}`, {
  title: '新标题',
  description: '文件描述',
  is_public: false,
  metadata: {
    alt_text: '图片描述',
    copyright: '版权信息'
  }
});
```

### 3.7 删除文件

```javascript
// 软删除（标记删除）
await apiClient.delete(`/files/${fileId}`);

// 永久删除（从存储中删除）
await apiClient.delete(`/files/${fileId}?delete_from_storage=true`);
```

---

## 四、完整示例

### 4.1 博客应用完整示例

```typescript
// src/services/blog.ts
import apiClient from './auth';

export interface Post {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  coverImage?: string;
  isPublished: boolean;
  createdAt: string;
}

// 文章服务
export const blogService = {
  // 获取文章列表
  async getPosts(page = 1, pageSize = 20) {
    const response = await apiClient.get('/records', {
      params: {
        app_identifier: 'blog-app',
        collection_type: 'post',
        is_published: true,
        page,
        page_size: pageSize,
        sort_by: 'created_at',
        sort_order: 'desc'
      }
    });

    return {
      posts: response.data.items.map(transformPost),
      total: response.data.total,
      page: response.data.page
    };
  },

  // 获取单篇文章
  async getPost(id: string) {
    const response = await apiClient.get(`/records/${id}`);

    // 增加浏览次数
    apiClient.patch(`/records/${id}`, {
      view_count: (response.data.view_count || 0) + 1
    }).catch(() => {});

    return transformPost(response.data);
  },

  // 创建文章
  async createPost(data: {
    title: string;
    content: string;
    category: string;
    tags: string[];
    coverImage?: string;
  }) {
    const response = await apiClient.post('/records', {
      app_identifier: 'blog-app',
      collection_type: 'post',
      payload: {
        content: data.content,
        category: data.category,
        tags: data.tags,
        coverImage: data.coverImage
      },
      title: data.title,
      is_published: true
    });

    return transformPost(response.data);
  },

  // 更新文章
  async updatePost(id: string, data: Partial<Post>) {
    const response = await apiClient.patch(`/records/${id}`, {
      payload: {
        content: data.content,
        category: data.category,
        tags: data.tags,
        coverImage: data.coverImage
      },
      title: data.title,
      is_published: data.isPublished
    });

    return transformPost(response.data);
  },

  // 删除文章
  async deletePost(id: string) {
    await apiClient.delete(`/records/${id}`);
  },

  // 上传封面图
  async uploadCover(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('app_identifier', 'blog-app');
    formData.append('title', '封面图');
    formData.append('is_public', true);

    const response = await apiClient.post('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    return response.data.public_url;
  }
};

// 转换数据格式
function transformPost(record: any): Post {
  return {
    id: record.id,
    title: record.title,
    content: record.payload.content,
    category: record.payload.category,
    tags: record.payload.tags || [],
    coverImage: record.payload.coverImage,
    isPublished: record.is_published,
    createdAt: record.created_at
  };
}
```

### 4.2 React 组件示例

```typescript
// src/components/PostList.tsx
import { useEffect, useState } from 'react';
import { blogService } from '../services/blog';

export function PostList() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    blogService.getPosts().then(data => {
      setPosts(data.posts);
      setLoading(false);
    });
  }, []);

  if (loading) return <div>加载中...</div>;

  return (
    <div className="post-list">
      {posts.map(post => (
        <article key={post.id} className="post-card">
          {post.coverImage && (
            <img src={post.coverImage} alt={post.title} />
          )}
          <h2>{post.title}</h2>
          <p className="category">{post.category}</p>
          <div className="tags">
            {post.tags.map(tag => (
              <span key={tag} className="tag">{tag}</span>
            ))}
          </div>
          <p>{post.content.substring(0, 200)}...</p>
        </article>
      ))}
    </div>
  );
}
```

```typescript
// src/components/CreatePost.tsx
import { useState } from 'react';
import { blogService } from '../services/blog';

export function CreatePost() {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('');
  const [tags, setTags] = useState([]);
  const [coverFile, setCoverFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setUploading(true);

    try {
      // 上传封面图
      let coverUrl;
      if (coverFile) {
        coverUrl = await blogService.uploadCover(coverFile);
      }

      // 创建文章
      await blogService.createPost({
        title,
        content,
        category,
        tags,
        coverImage: coverUrl
      });

      alert('发布成功!');
      // 跳转到文章列表
      window.location.href = '/posts';
    } catch (error) {
      console.error('发布失败:', error);
      alert('发布失败，请重试');
    } finally {
      setUploading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="标题"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        required
      />

      <textarea
        placeholder="内容"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        required
      />

      <input
        type="text"
        placeholder="分类"
        value={category}
        onChange={(e) => setCategory(e.target.value)}
      />

      <input
        type="file"
        accept="image/*"
        onChange={(e) => setCoverFile(e.target.files[0])}
      />

      <button type="submit" disabled={uploading}>
        {uploading ? '发布中...' : '发布'}
      </button>
    </form>
  );
}
```

---

## 五、常见问题

### Q1: 如何处理 Token 过期？

```javascript
apiClient.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Token 过期，跳转到登录
      localStorage.removeItem('jwt_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### Q2: 如何实现分页加载？

```javascript
function useInfiniteScroll() {
  const [posts, setPosts] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const loadMore = async () => {
    const data = await blogService.getPosts(page + 1);
    setPosts([...posts, ...data.posts]);
    setPage(page + 1);
    setHasMore(posts.length + data.posts.length < data.total);
  };

  return { posts, loadMore, hasMore };
}
```

### Q3: 如何优化大文件上传？

```javascript
// 分片上传
async function uploadChunkedFile(file) {
  const chunkSize = 5 * 1024 * 1024; // 5MB
  const chunks = Math.ceil(file.size / chunkSize);

  for (let i = 0; i < chunks; i++) {
    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, file.size);
    const chunk = file.slice(start, end);

    await apiClient.post('/files/upload-chunk', {
      file_id: 'file-uuid',
      chunk_index: i,
      total_chunks: chunks,
      chunk: chunk
    });
  }

  // 合并分片
  await apiClient.post('/files/complete-chunked-upload', {
    file_id: 'file-uuid'
  });
}
```

### Q4: 如何缓存数据？

```javascript
// 使用 React Query 或 SWR
import { useQuery } from '@tanstack/react-query';

function usePosts() {
  return useQuery({
    queryKey: ['posts'],
    queryFn: () => blogService.getPosts(),
    staleTime: 5 * 60 * 1000, // 5 分钟内不重新获取
    cacheTime: 10 * 60 * 1000 // 缓存 10 分钟
  });
}
```

### Q5: 如何处理错误？

```javascript
try {
  const post = await blogService.getPost(id);
} catch (error) {
  if (error.response?.status === 404) {
    alert('文章不存在');
  } else if (error.response?.status === 403) {
    alert('无权访问');
  } else {
    alert('加载失败，请重试');
  }
}
```

---

## 附录

### A. API 响应码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

### B. 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### C. 相关文档

- [API Swagger 文档](http://localhost:9000/api/v1/docs)
- [Casdoor 文档](https://casdoor.org/)
- [项目架构文档](../CLAUDE.md)

---

**更新时间**: 2024-12-23
**文档版本**: v1.0.0
