# 基于 Unified Backend Platform 开发应用指南

本文档说明如何基于统一后端平台设计数据模型和开发应用。

---

## 🎯 核心设计理念

### UnifiedRecord 模式

**核心思想**：使用 `payload` 字段存储任意 JSON 结构的业务数据，实现单一数据模型支持多种应用场景。

```python
UnifiedRecord {
    id: UUID                          # 记录 ID
    app_identifier: str               # 应用标识 (如: blog-app)
    collection_type: str              # 数据类型 (如: post, comment)
    owner_id: UUID | None             # 所有者用户 ID
    payload: dict[str, Any]           # 🔥 任意 JSON 业务数据
    title: str | None                 # 标题 (便于搜索)
    description: str | None           # 描述
    is_published: bool                # 发布状态
    is_deleted: bool                  # 软删除标记
    created_at: datetime
    updated_at: datetime
}
```

**优势**：
- ✅ **无需修改数据库 Schema** - 业务模型变更只需修改前端代码
- ✅ **快速迭代** - 新增字段、修改结构无需迁移
- ✅ **多应用共享** - 同一后端支持多个独立应用
- ✅ **统一 API** - 所有 CRUD 操作复用同一套接口

---

## 📐 数据模型设计步骤

### 步骤 1: 规划应用标识符

**app_identifier** - 应用唯一标识

```python
# 好的命名约定
"blog-app"           # 博客应用
"forum-app"          # 论坛应用
"shop-app"           # 电商应用
"task-app"           # 任务管理
"cms-app"            # 内容管理
```

**规则**：
- 使用小写字母
- 使用连字符 `-` 分隔单词
- 以 `-app` 结尾（可选但推荐）

### 步骤 2: 设计数据类型（collection_type）

**collection_type** - 区分同一应用内的不同数据类型

```python
# 博客应用示例
app_identifier = "blog-app"

collection_types = [
    "post",           # 文章
    "page",           # 页面
    "category",       # 分类
    "tag",            # 标签
    "comment",        # 评论
]

# 论坛应用示例
app_identifier = "forum-app"

collection_types = [
    "thread",         # 主题
    "post",           # 帖子
    "comment",        # 评论
    "board",          # 版块
    "user_profile",   # 用户资料
]
```

**命名建议**：
- 使用单数形式（`post` 而非 `posts`）
- 使用小写字母和下划线
- 保持简洁和描述性

### 步骤 3: 设计 Payload 结构

**payload** - 存储业务数据的 JSON 对象

#### 示例 1: 博客文章

```python
# 创建文章
POST /api/v1/records
{
    "app_identifier": "blog-app",
    "collection_type": "post",
    "title": "如何使用 Unified Backend Platform",
    "description": "介绍统一后端平台的使用方法",
    "is_published": true,
    "payload": {
        "content": "完整的文章内容...",
        "excerpt": "摘要文字",
        "featured_image": "uuid-of-image-file",
        "author": {
            "name": "张三",
            "avatar": "uuid-of-avatar"
        },
        "categories": ["技术", "教程"],
        "tags": ["python", "fastapi", "mongodb"],
        "reading_time": 10,
        "view_count": 0,
        "seo": {
            "keywords": ["fastapi", "后端", "api"],
            "description": "元描述"
        }
    }
}
```

#### 示例 2: 论坛主题

```python
POST /api/v1/records
{
    "app_identifier": "forum-app",
    "collection_type": "thread",
    "title": "关于 FastAPI 性能优化的讨论",
    "payload": {
        "content": "主题内容...",
        "board_id": "uuid-of-board",
        "author_id": "uuid-of-user",
        "is_pinned": false,
        "is_locked": false,
        "reply_count": 0,
        "last_reply_at": null,
        "attachments": ["uuid-of-file1", "uuid-of-file2"]
    }
}
```

#### 示例 3: 电商产品

```python
POST /api/v1/records
{
    "app_identifier": "shop-app",
    "collection_type": "product",
    "title": "无线机械键盘",
    "payload": {
        "price": 599.00,
        "currency": "CNY",
        "stock": 100,
        "sku": "KB-2024-001",
        "images": ["uuid1", "uuid2", "uuid3"],
        "variants": [
            {"name": "红轴", "stock": 50},
            {"name": "茶轴", "stock": 30},
            {"name": "青轴", "stock": 20}
        ],
        "specifications": {
            "brand": "Keychron",
            "switch": "Cherry MX",
            "layout": "75%"
        },
        "reviews": {
            "average": 4.5,
            "count": 128
        }
    }
}
```

---

## 🔧 完整开发流程

### 1. 创建应用

**步骤**：
```python
# 1. 确定 app_identifier
APP_IDENTIFIER = "my-app"

# 2. 设计数据类型
COLLECTION_TYPES = ["item", "category", "settings"]
```

### 2. 创建数据模型（TypeScript 示例）

```typescript
// types/models.ts

export interface BaseRecord {
  id: string;
  app_identifier: string;
  collection_type: string;
  owner_id?: string;
  title?: string;
  description?: string;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

// 文章模型
export interface Post extends BaseRecord {
  collection_type: "post";
  payload: {
    content: string;
    excerpt: string;
    featured_image?: string;
    categories: string[];
    tags: string[];
    author: {
      name: string;
      avatar?: string;
    };
    reading_time: number;
    seo?: {
      keywords?: string[];
      description?: string;
    };
  };
}

// 创建请求
export interface CreatePostRequest {
  title: string;
  content: string;
  excerpt: string;
  categories: string[];
  tags: string[];
  featured_image?: string;
  is_published: boolean;
}
```

### 3. 创建 API 服务

```typescript
// services/api.ts

const API_BASE = process.env.VITE_API_URL || 'http://localhost:9000/api/v1';

export class RecordService {
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  private get headers() {
    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json',
    };
  }

  // 创建记录
  async createRecord(data: any) {
    const response = await fetch(`${API_BASE}/records`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return response.json();
  }

  // 查询记录
  async queryRecords(params: {
    app_identifier: string;
    collection_type?: string;
    page?: number;
    page_size?: number;
    search?: string;
  }) {
    const queryString = new URLSearchParams(params as any);
    const response = await fetch(
      `${API_BASE}/records?${queryString}`,
      { headers: this.getHeaders() }
    );
    return response.json();
  }

  // 获取单条记录
  async getRecord(id: string) {
    const response = await fetch(
      `${API_BASE}/records/${id}`,
      { headers: this.getHeaders() }
    );
    return response.json();
  }

  // 更新记录
  async updateRecord(id: string, data: any) {
    const response = await fetch(`${API_BASE}/records/${id}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return response.json();
  }

  // 删除记录
  async deleteRecord(id: string) {
    const response = await fetch(`${API_BASE}/records/${id}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    return response.status === 204;
  }

  // 批量操作
  async batchCreate(items: any[]) {
    const response = await fetch(`${API_BASE}/records/batch`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ items, stop_on_error: false }),
    });
    return response.json();
  }
}
```

### 4. 使用示例

```typescript
// app.tsx

const API = new RecordService(jwtToken);

// 创建文章
const newPost = await API.createRecord({
    app_identifier: 'blog-app',
    collection_type: 'post',
    title: '我的第一篇文章',
    description: '这是文章摘要',
    is_published: true,
    payload: {
        content: '文章正文内容...',
        excerpt: '摘要',
        categories: ['技术'],
        tags: ['编程'],
        author: { name: '张三' },
        reading_time: 5
    }
});

// 查询所有文章
const posts = await API.queryRecords({
    app_identifier: 'blog-app',
    collection_type: 'post',
    page: 1,
    page_size: 20
});

console.log(posts.total);  // 总数
console.log(posts.items);  // 文章列表
```

---

## 🎨 前端应用开发示例

### React + TypeScript 示例

```typescript
// hooks/useRecords.ts

import { useState, useEffect } from 'react';
import { RecordService } from '../services/api';

export function useRecords(appIdentifier: string, collectionType: string) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const api = new RecordService(getToken());

    api.queryRecords({ app_identifier: appIdentifier, collection_type })
      .then(data => {
        setRecords(data.items);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, [appIdentifier, collectionType]);

  return { records, loading, error };
}

// components/PostList.tsx

export function PostList() {
  const { records, loading, error } = useRecords('blog-app', 'post');

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div className="post-list">
      {records.map((post: any) => (
        <article key={post.id}>
          <h2>{post.title}</h2>
          <p>{post.payload.excerpt}</p>
          <div>
            {post.payload.categories.map((cat: string) => (
              <span key={cat} className="category">{cat}</span>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}
```

---

## 📋 最佳实践

### 1. Payload 设计原则

#### ✅ 好的设计

```python
# 扁平结构，易于查询
{
    "payload": {
        "title": "文章标题",
        "content": "文章内容",
        "author": "作者ID",
        "tags": ["tag1", "tag2"],
        "stats": {
            "views": 100,
            "likes": 10
        }
    }
}
```

#### ❌ 避免

```python
# 过度嵌套，难以查询
{
    "payload": {
        "data": {
            "content": {
                "body": "文章内容"
            }
        }
    }
}
```

### 2. 常用字段提取到顶层

将经常查询或排序的字段提取到 `UnifiedRecord` 顶层：

```python
# ✅ 推荐
{
    "title": "文章标题",        # 顶层 - 便于搜索
    "description": "摘要",     # 顶层 - 便于列表展示
    "payload": {
        "content": "正文内容",   # payload - 详细数据
        "author": {...}
    }
}
```

### 3. 使用枚举和常量

```typescript
// constants/collections.ts
export const COLLECTION_TYPES = {
  BLOG_POST: 'post',
  BLOG_PAGE: 'page',
  FORUM_THREAD: 'thread',
  FORUM_REPLY: 'reply',
} as const;

export const APP_IDENTIFIERS = {
  BLOG: 'blog-app',
  FORUM: 'forum-app',
} as const;
```

### 4. 类型安全

```typescript
// types/payloads.ts

export interface PostPayload {
  content: string;
  excerpt: string;
  featured_image?: string;
  categories: string[];
  tags: string[];
  author: Author;
  reading_time: number;
}

export interface ProductPayload {
  price: number;
  currency: 'CNY' | 'USD';
  stock: number;
  sku: string;
  images: string[];
  variants: ProductVariant[];
}

// 使用泛型确保类型安全
export interface TypedRecord<TPayload> {
  id: string;
  app_identifier: string;
  collection_type: string;
  title?: string;
  payload: TPayload;
}

export type PostRecord = TypedRecord<PostPayload>;
export type ProductRecord = TypedRecord<ProductPayload>;
```

### 5. 数据验证

```typescript
// validators/post.ts

import { z } from 'zod';

export const PostPayloadSchema = z.object({
  content: z.string().min(1),
  excerpt: z.string().max(500),
  featured_image: z.string().uuid().optional(),
  categories: z.array(z.string()),
  tags: z.array(z.string()),
  author: z.object({
    name: z.string(),
    avatar: z.string().uuid().optional(),
  }),
  reading_time: z.number().int().positive(),
});

export const CreatePostSchema = z.object({
  app_identifier: z.literal('blog-app'),
  collection_type: z.literal('post'),
  title: z.string().min(1).max(200),
  description: z.string().max(500).optional(),
  is_published: z.boolean(),
  payload: PostPayloadSchema,
});
```

---

## 🚀 实际应用场景

### 场景 1: 博客系统

```python
# 文章
POST /api/v1/records
{
    "app_identifier": "blog-app",
    "collection_type": "post",
    "title": "FastAPI 入门教程",
    "payload": {
        "content": "完整教程内容...",
        "markdown": true,
        "featured_image": "uuid",
        "categories": ["技术", "教程"],
        "tags": ["python", "web"],
        "author": {"id": "uuid", "name": "张三"}
    }
}

# 分类
POST /api/v1/records
{
    "app_identifier": "blog-app",
    "collection_type": "category",
    "title": "技术文章",
    "payload": {
        "slug": "tech",
        "description": "技术相关文章",
        "parent_id": null
    }
}
```

### 场景 2: 论坛系统

```python
# 版块
POST /api/v1/records
{
    "app_identifier": "forum-app",
    "collection_type": "board",
    "title": "技术交流",
    "payload": {
        "description": "讨论技术话题",
        "icon": "💻",
        "thread_count": 0,
        "post_count": 0,
        "position": 1
    }
}

# 主题
POST /api/v1/records
{
    "app_identifier": "forum-app",
    "collection_type": "thread",
    "title": "如何优化 Python 代码？",
    "payload": {
        "content": "我想了解一些 Python 性能优化技巧...",
        "board_id": "board-uuid",
        "author_id": "user-uuid",
        "is_pinned": false,
        "reply_count": 0,
        "last_reply_at": null
    }
}

# 回复
POST /api/v1/records
{
    "app_identifier": "forum-app",
    "collection_type": "reply",
    "title": "Re: 如何优化 Python 代码？",  # 可选
    "payload": {
        "content": "使用 list comprehension 替代 for 循环...",
        "thread_id": "thread-uuid",
        "author_id": "user-uuid",
        "floor": 1,
        "reply_to_id": null
    }
}
```

### 场景 3: 电商系统

```python
# 商品
POST /api/v1/records
{
    "app_identifier": "shop-app",
    "collection_type": "product",
    "title": "机械键盘 K8",
    "payload": {
        "price": 899.00,
        "currency": "CNY",
        "stock": 50,
        "sku": "K8-2024-PRO",
        "images": ["uuid1", "uuid2"],
        "variants": [
            {"name": "红轴", "stock": 20},
            {"name": "茶轴", "stock": 30}
        ],
        "specs": {"brand": "Keychron", "switch": "Cherry MX"}
    }
}

# 订单
POST /api/v1/records
{
    "app_identifier": "shop-app",
    "collection_type": "order",
    "title": "订单 #20241223001",
    "payload": {
        "customer_id": "customer-uuid",
        "items": [
            {"product_id": "uuid", "quantity": 1, "price": 899}
        ],
        "total_amount": 899,
        "status": "pending",
        "shipping_address": {...}
    }
}
```

---

## 📚 总结

### 关键要点

1. **app_identifier** - 应用唯一标识
2. **collection_type** - 数据类型区分
3. **payload** - 灵活的 JSON 业务数据
4. **title** - 提取到顶层便于搜索
5. **is_published** - 控制发布状态

### 优势

- ✅ 无需后端迁移
- ✅ 快速迭代开发
- ✅ 多应用统一管理
- ✅ 类型安全（前端验证）
- ✅ 统一 API 接口

### 开发流程

1. 设计 `app_identifier` 和 `collection_type`
2. 定义 Payload 结构（TypeScript Interface）
3. 创建前端服务层（API 调用）
4. 实现业务逻辑和 UI
5. 测试和部署

---

**参考文档**：
- [CLAUDE.md](./CLAUDE.md) - 技术架构详情
- [DEPLOYMENT.md](./DEPLOYMENT.md) - 部署指南
- [API 文档](http://localhost:9000/api/v1/docs) - Swagger UI
