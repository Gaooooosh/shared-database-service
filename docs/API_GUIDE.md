# Unified Backend Platform - API 使用指南

> 详细的 API 端点说明和使用示例

## 目录

- [认证机制](#认证机制)
- [认证 API](#认证-api)
- [记录管理 API](#记录管理-api)
- [批量操作 API](#批量操作-api)
- [文件管理 API](#文件管理-api)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)

---

## 认证机制

### 概述

Unified Backend Platform 使用 **Casdoor** 作为认证服务，后端通过验证 JWT Token 来识别用户身份。

### 认证流程

```
┌─────────┐         ┌──────────┐         ┌─────────┐
│  客户端  │  ──1──> │ Casdoor  │ ──2──>  │  客户端  │
│         │         │  (SSO)   │         │         │
│         │ <────────          │         │         │
│         │    登录页面         │         │         │
└─────────┘         └──────────┘         └─────────┘
                           │
                           │ 3. 返回 JWT Token
                           ▼
                    ┌──────────┐
                    │  客户端   │ ──4. Bearer Token──> ┌─────────┐
                    │         │                        │ Backend │
                    └──────────┘ <──────── 5. 用户数据 ─┤         │
                                                      └─────────┘
```

### 获取 JWT Token

1. **前端集成 Casdoor SDK** (推荐)

```javascript
// 使用 Casdoor JS SDK
import { Sdk } from 'casdoor-js-sdk'

const sdk = new Sdk({
  serverUrl: "http://localhost:3000",
  clientId: "your_client_id",
  appName: "unified-backend",
  redirectPath: "/callback",
})

// 登录
sdk.signIn()

// 获取 Token
const token = sdk.getToken()
```

2. **手动获取**

```bash
# 访问登录页面
open http://localhost:3000/login/oauth/authorize

# 登录成功后从回调 URL 中获取 code
# 用 code 换取 token (需要在后端实现 OAuth 回调)
```

### 使用 Token

所有需要认证的 API 请求都需要在 HTTP Header 中携带 Token：

```bash
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## 认证 API

### 1. 获取当前用户信息

获取当前登录用户的详细信息，自动从 MongoDB 同最新数据。

**端点**: `GET /api/v1/auth/me`

**认证**: 必须

**请求示例**:

```bash
curl -X GET "http://localhost:3002/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**响应示例**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "casdoor_id": "4f2e1234-5678-90ab-cdef-1234567890ab",
  "email": "user@example.com",
  "display_name": "张三",
  "avatar": "http://cdn.example.com/avatar.jpg",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-15T08:30:00Z",
  "last_login_at": "2024-01-20T10:15:30Z"
}
```

### 2. 刷新用户信息

从 Casdoor 同步最新的用户信息到本地数据库。

**端点**: `POST /api/v1/auth/refresh`

**认证**: 必须

**请求示例**:

```bash
curl -X POST "http://localhost:3002/api/v1/auth/refresh" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**响应示例**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "casdoor_id": "4f2e1234-5678-90ab-cdef-1234567890ab",
  "email": "new-email@example.com",
  "display_name": "张三 (已更新)",
  "avatar": "http://cdn.example.com/new-avatar.jpg",
  "role": "user",
  "last_login_at": "2024-01-20T10:20:00Z"
}
```

---

## 记录管理 API

### 核心概念

**UnifiedRecord** 是通用的业务数据模型，通过三个核心字段区分不同数据：

- `app_identifier`: 应用标识符 (如: `blog-app`, `shop-app`)
- `collection_type`: 数据类型 (如: `post`, `order`, `comment`)
- `payload`: 任意 JSON 业务数据

### 1. 创建记录

创建新的业务数据记录。

**端点**: `POST /api/v1/records`

**认证**: 必须

**请求体**:

```json
{
  "app_identifier": "string (required, 1-50 chars)",
  "collection_type": "string (required, 1-50 chars)",
  "title": "string (optional, max 200 chars)",
  "description": "string (optional, max 500 chars)",
  "payload": "object (optional, any JSON data)",
  "is_published": "boolean (optional, default: true)"
}
```

**示例 1: 创建博客文章**

```bash
curl -X POST "http://localhost:3002/api/v1/records" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "app_identifier": "blog-app",
    "collection_type": "post",
    "title": "FastAPI 入门教程",
    "description": "从零开始学习 FastAPI",
    "payload": {
      "content": "# FastAPI 入门\n\n这是文章正文...",
      "markdown": true,
      "tags": ["python", "fastapi", "web"],
      "category": "编程",
      "reading_time": 15,
      "featured_image": "https://example.com/cover.jpg"
    },
    "is_published": true
  }'
```

**示例 2: 创建电商订单**

```bash
curl -X POST "http://localhost:3002/api/v1/records" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "app_identifier": "shop-app",
    "collection_type": "order",
    "title": "订单 #20240115001",
    "payload": {
      "order_number": "20240115001",
      "items": [
        {"product_id": "p1", "name": "商品A", "qty": 2, "price": 99.99},
        {"product_id": "p2", "name": "商品B", "qty": 1, "price": 49.99}
      ],
      "subtotal": 249.97,
      "tax": 25.00,
      "total": 274.97,
      "currency": "CNY",
      "status": "paid",
      "payment_method": "wechat_pay",
      "shipping_address": {
        "name": "张三",
        "phone": "13800138000",
        "province": "北京市",
        "city": "北京市",
        "district": "朝阳区",
        "detail": "xx街道xx号"
      }
    },
    "is_published": false
  }'
```

**示例 3: 创建评论**

```bash
curl -X POST "http://localhost:3002/api/v1/records" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "app_identifier": "blog-app",
    "collection_type": "comment",
    "payload": {
      "post_id": "post-uuid-here",
      "content": "这篇文章写得很好！",
      "parent_id": null,
      "likes": 0
    }
  }'
```

**响应示例**:

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "app_identifier": "blog-app",
  "collection_type": "post",
  "owner_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "FastAPI 入门教程",
  "description": "从零开始学习 FastAPI",
  "payload": {
    "content": "# FastAPI 入门\n\n这是文章正文...",
    "markdown": true,
    "tags": ["python", "fastapi", "web"],
    "category": "编程"
  },
  "is_deleted": false,
  "is_published": true,
  "created_at": "2024-01-20T10:30:00Z",
  "updated_at": "2024-01-20T10:30:00Z",
  "published_at": "2024-01-20T10:30:00Z",
  "version": 1,
  "view_count": 0
}
```

### 2. 查询记录列表

支持多维度筛选、分页、排序、搜索。

**端点**: `GET /api/v1/records`

**认证**: 可选 (未登录只能看到已发布内容)

**查询参数**:

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `app_identifier` | string | 否 | 筛选应用 | `blog-app` |
| `collection_type` | string | 否 | 筛选数据类型 | `post` |
| `is_published` | boolean | 否 | 发布状态 | `true` |
| `owner_id` | UUID | 否 | 所有者 ID | `550e8400-...` |
| `search` | string | 否 | 搜索标题/描述 | `FastAPI` |
| `page` | integer | 否 | 页码 (默认 1) | `1` |
| `page_size` | integer | 否 | 每页大小 (1-100) | `20` |
| `sort_by` | string | 否 | 排序字段 | `created_at` |
| `sort_order` | string | 否 | 排序方向 (asc/desc) | `desc` |

**示例 1: 查询所有博客文章**

```bash
curl "http://localhost:3002/api/v1/records?app_identifier=blog-app&collection_type=post"
```

**示例 2: 搜索包含关键词的记录**

```bash
curl "http://localhost:3002/api/v1/records?search=FastAPI"
```

**示例 3: 分页查询，按创建时间倒序**

```bash
curl "http://localhost:3002/api/v1/records?page=1&page_size=10&sort_by=created_at&sort_order=desc"
```

**示例 4: 查询特定用户的已发布内容**

```bash
curl "http://localhost:3002/api/v1/records?owner_id=550e8400-e29b-41d4-a716-446655440000&is_published=true"
```

**响应示例**:

```json
{
  "total": 45,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "app_identifier": "blog-app",
      "collection_type": "post",
      "owner_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "FastAPI 入门教程",
      "description": "从零开始学习 FastAPI",
      "payload": {...},
      "is_deleted": false,
      "is_published": true,
      "created_at": "2024-01-20T10:30:00Z",
      "updated_at": "2024-01-20T10:30:00Z",
      "published_at": "2024-01-20T10:30:00Z",
      "version": 1,
      "view_count": 150
    },
    ...
  ]
}
```

### 3. 获取记录详情

获取单条记录的完整信息，自动增加查看次数。

**端点**: `GET /api/v1/records/{record_id}`

**认证**: 可选 (未认证用户只能访问已发布内容)

**权限**:
- 已发布内容：所有人可访问
- 未发布内容：仅所有者和管理员可访问

**请求示例**:

```bash
curl -X GET "http://localhost:3002/api/v1/records/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**响应示例**:

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "app_identifier": "blog-app",
  "collection_type": "post",
  "owner_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "FastAPI 入门教程",
  "description": "从零开始学习 FastAPI",
  "payload": {
    "content": "完整的文章内容...",
    "markdown": true,
    "tags": ["python", "fastapi", "web"],
    "category": "编程",
    "reading_time": 15
  },
  "is_deleted": false,
  "is_published": true,
  "created_at": "2024-01-20T10:30:00Z",
  "updated_at": "2024-01-20T10:30:00Z",
  "published_at": "2024-01-20T10:30:00Z",
  "version": 1,
  "view_count": 151
}
```

### 4. 完整更新记录

更新记录的所有字段，未提供的字段会被清空。

**端点**: `PUT /api/v1/records/{record_id}`

**认证**: 必须 (仅所有者和管理员)

**请求体**:

```json
{
  "title": "string (optional)",
  "description": "string (optional)",
  "payload": "object (optional)",
  "is_published": "boolean (optional)"
}
```

**请求示例**:

```bash
curl -X PUT "http://localhost:3002/api/v1/records/a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "FastAPI 完全指南 (已更新)",
    "description": "全面的 FastAPI 学习资料",
    "payload": {
      "content": "更新后的内容...",
      "tags": ["python", "fastapi", "web", "高级"],
      "version": "2.0"
    },
    "is_published": true
  }'
```

**响应示例**:

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "app_identifier": "blog-app",
  "collection_type": "post",
  "owner_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "FastAPI 完全指南 (已更新)",
  "description": "全面的 FastAPI 学习资料",
  "payload": {
    "content": "更新后的内容...",
    "tags": ["python", "fastapi", "web", "高级"],
    "version": "2.0"
  },
  "is_deleted": false,
  "is_published": true,
  "created_at": "2024-01-20T10:30:00Z",
  "updated_at": "2024-01-20T11:00:00Z",
  "published_at": "2024-01-20T10:30:00Z",
  "version": 2,
  "view_count": 151
}
```

### 5. 部分更新记录 (PATCH)

只更新 `payload` 中的指定字段，其他字段保持不变 (合并操作)。

**端点**: `PATCH /api/v1/records/{record_id}`

**认证**: 必须 (仅所有者和管理员)

**请求体**:

```json
{
  "payload": "object (required, 要合并的数据)"
}
```

**场景示例**: 给文章添加一个 `views` 字段

```bash
curl -X PATCH "http://localhost:3002/api/v1/records/a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "views": 1000,
      "featured": true,
      "last_viewed_at": "2024-01-20T12:00:00Z"
    }
  }'
```

**结果**: `payload` 会合并为：

```json
{
  "content": "原始内容...",
  "tags": ["python", "fastapi", "web"],
  "views": 1000,
  "featured": true,
  "last_viewed_at": "2024-01-20T12:00:00Z"
}
```

### 6. 删除记录

软删除记录，数据不会真正删除，只是标记 `is_deleted=true`。

**端点**: `DELETE /api/v1/records/{record_id}`

**认证**: 必须 (仅所有者和管理员)

**请求示例**:

```bash
curl -X DELETE "http://localhost:3002/api/v1/records/a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**响应**: `204 No Content`

---

## 批量操作 API

### 概述

批量操作 API 允许一次性处理多条记录，提高效率。支持批量创建、更新和删除操作。

**限制**：
- 每次最多处理 100 条记录
- 所有操作支持事务控制 (`stop_on_error`)

### 1. 批量创建记录

一次性创建多条记录。

**端点**: `POST /api/v1/records/batch`

**认证**: 必须

**请求体**:

```json
{
  "items": "array (1-100 items)",
  "stop_on_error": "boolean (default: false)"
}
```

**参数说明**:
- `items`: 要创建的记录数组
- `stop_on_error`: 遇到错误时是否停止（false 则继续处理剩余记录）

**请求示例**:

```bash
curl -X POST "http://localhost:9000/api/v1/records/batch" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "app_identifier": "blog-app",
        "collection_type": "post",
        "title": "FastAPI 入门",
        "payload": {"content": "...", "category": "教程"}
      },
      {
        "app_identifier": "blog-app",
        "collection_type": "post",
        "title": "MongoDB 指南",
        "payload": {"content": "...", "category": "数据库"}
      },
      {
        "app_identifier": "blog-app",
        "collection_type": "post",
        "title": "Python 最佳实践",
        "payload": {"content": "...", "category": "编程"}
      }
    ],
    "stop_on_error": false
  }'
```

**响应示例**:

```json
{
  "total": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "index": 0,
      "success": true,
      "error": null
    },
    {
      "id": "b2c3d4e5-f6g7-8901-bcde-f12345678901",
      "index": 1,
      "success": true,
      "error": null
    },
    {
      "id": "c3d4e5f6-g7h8-9012-cdef-123456789012",
      "index": 2,
      "success": true,
      "error": null
    }
  ]
}
```

**部分失败示例** (`stop_on_error: false`):

```json
{
  "total": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "id": "uuid-1",
      "index": 0,
      "success": true,
      "error": null
    },
    {
      "id": null,
      "index": 1,
      "success": false,
      "error": "Validation error: title is required"
    },
    {
      "id": "uuid-3",
      "index": 2,
      "success": true,
      "error": null
    }
  ]
}
```

### 2. 批量更新记录

使用相同的更新内容批量更新多条记录。

**端点**: `PUT /api/v1/records/batch`

**认证**: 必须

**请求体**:

```json
{
  "ids": "array (1-100 UUIDs)",
  "updates": "UnifiedRecordUpdate object",
  "stop_on_error": "boolean (default: false)"
}
```

**请求示例**:

```bash
curl -X PUT "http://localhost:9000/api/v1/records/batch" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": [
      "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "b2c3d4e5-f6g7-8901-bcde-f12345678901"
    ],
    "updates": {
      "is_published": true,
      "payload": {"status": "published", "published_at": "2024-01-20"}
    },
    "stop_on_error": false
  }'
```

**响应示例**:

```json
{
  "total": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "index": 0,
      "success": true,
      "error": null
    },
    {
      "id": "b2c3d4e5-f6g7-8901-bcde-f12345678901",
      "index": 1,
      "success": true,
      "error": null
    }
  ]
}
```

### 3. 批量删除记录

软删除多条记录（设置 `is_deleted=true`）。

**端点**: `DELETE /api/v1/records/batch`

**认证**: 必须

**请求体**:

```json
{
  "ids": "array (1-100 UUIDs)",
  "stop_on_error": "boolean (default: false)"
}
```

**请求示例**:

```bash
curl -X DELETE "http://localhost:9000/api/v1/records/batch" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": [
      "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "b2c3d4e5-f6g7-8901-bcde-f12345678901"
    ],
    "stop_on_error": false
  }'
```

**响应示例**:

```json
{
  "total": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "index": 0,
      "success": true,
      "error": null
    },
    {
      "id": "b2c3d4e5-f6g7-8901-bcde-f12345678901",
      "index": 1,
      "success": true,
      "error": null
    }
  ]
}
```

---

## 文件管理 API

### 概述

文件管理 API 提供完整的文件上传、下载、管理功能，基于 MinIO/S3 对象存储。

**支持的功能**:
- 小文件直接上传（< 10MB）
- 大文件预签名 URL 上传（≥ 10MB）
- 文件元数据管理
- 公开/私有访问控制
- 多种文件类型分类（图片、视频、PDF、音频等）

### 1. 上传文件

直接上传小文件到服务器。

**端点**: `POST /api/v1/files/upload`

**认证**: 必须

**请求类型**: `multipart/form-data`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | File | 是 | 要上传的文件 |
| `app_identifier` | string | 是 | 应用标识符 |
| `is_public` | boolean | 否 | 是否公开（默认 false） |

**请求示例**:

```bash
curl -X POST "http://localhost:9000/api/v1/files/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/image.jpg" \
  -F "app_identifier=blog-app" \
  -F "is_public=true"
```

**响应示例**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "image.jpg",
  "file_size": 1024000,
  "content_type": "image/jpeg",
  "storage_path": "blog-app/2024/01/20/uuid-image.jpg",
  "bucket_name": "unified-files",
  "category": "image",
  "is_public": true,
  "public_url": "http://localhost:9100/unified-files/blog-app/2024/01/20/uuid-image.jpg",
  "created_at": "2024-01-20T10:30:00Z"
}
```

### 2. 获取预签名 URL

获取用于直接上传到 MinIO 的预签名 URL（适用于大文件）。

**端点**: `POST /api/v1/files/presign`

**认证**: 必须

**请求体**:

```json
{
  "filename": "string (required)",
  "content_type": "string (required)",
  "file_size": "integer (required)",
  "app_identifier": "string (required)",
  "is_public": "boolean (optional)"
}
```

**请求示例**:

```bash
curl -X POST "http://localhost:9000/api/v1/files/presign" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "presentation.mp4",
    "content_type": "video/mp4",
    "file_size": 52428800,
    "app_identifier": "blog-app",
    "is_public": false
  }'
```

**响应示例**:

```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "presigned_url": "https://minio.example.com/unified-files/path?X-Amz-Algorithm=...",
  "public_url": "http://localhost:9100/unified-files/blog-app/2024/01/20/presentation.mp4",
  "storage_path": "blog-app/2024/01/20/presentation.mp4",
  "upload_method": "PUT",
  "expires_at": "2024-01-20T11:30:00Z"
}
```

**使用预签名 URL 上传**:

```bash
# 使用返回的 presigned_url 直接上传到 MinIO
curl -X PUT "<presigned_url>" \
  -H "Content-Type: video/mp4" \
  --upload-file /path/to/presentation.mp4

# 上传完成后确认
POST /api/v1/files/{file_id}/confirm
```

### 3. 查询文件列表

查询已上传的文件列表。

**端点**: `GET /api/v1/files`

**认证**: 可选

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `app_identifier` | string | 筛选应用 |
| `category` | string | 文件类型 (image, video, pdf, audio, document, other) |
| `is_public` | boolean | 公开状态 |
| `owner_id` | UUID | 所有者 ID |
| `page` | integer | 页码 (默认 1) |
| `page_size` | integer | 每页大小 (1-100) |

**请求示例**:

```bash
# 查询所有图片
curl "http://localhost:9000/api/v1/files?category=image&page=1&page_size=20"

# 查询特定应用的文件
curl "http://localhost:9000/api/v1/files?app_identifier=blog-app"
```

**响应示例**:

```json
{
  "total": 45,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "photo1.jpg",
      "file_size": 1024000,
      "content_type": "image/jpeg",
      "category": "image",
      "is_public": true,
      "public_url": "http://localhost:9100/unified-files/...",
      "created_at": "2024-01-20T10:30:00Z"
    }
  ]
}
```

### 4. 获取文件详情

获取单个文件的详细信息。

**端点**: `GET /api/v1/files/{file_id}`

**认证**: 可选

**请求示例**:

```bash
curl -X GET "http://localhost:9000/api/v1/files/550e8400-e29b-41d4-a716-446655440000"
```

**响应示例**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "owner_id": "3acc5483-9897-4f15-bd3b-62c77551f9cb",
  "app_identifier": "blog-app",
  "filename": "document.pdf",
  "file_size": 2048000,
  "content_type": "application/pdf",
  "storage_path": "blog-app/2024/01/20/document.pdf",
  "bucket_name": "unified-files",
  "category": "pdf",
  "is_public": false,
  "is_deleted": false,
  "public_url": "http://localhost:9100/unified-files/blog-app/2024/01/20/document.pdf",
  "created_at": "2024-01-20T10:30:00Z"
}
```

### 5. 下载文件

获取文件的下载 URL 或重定向。

**端点**: `GET /api/v1/files/{file_id}/download`

**认证**: 取决于文件访问权限

**请求示例**:

```bash
curl -X GET "http://localhost:9000/api/v1/files/550e8400-e29b-41d4-a716-446655440000/download" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -O -J
```

**响应**:
- 公开文件：重定向到 MinIO 直接下载
- 私有文件：重定向到预签名下载 URL

### 6. 删除文件

删除文件（软删除）。

**端点**: `DELETE /api/v1/files/{file_id}`

**认证**: 必须（仅所有者和管理员）

**请求示例**:

```bash
curl -X DELETE "http://localhost:9000/api/v1/files/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**响应**: `204 No Content`

### 文件分类

系统会根据 `content_type` 自动分类文件：

| Content-Type | Category |
|--------------|----------|
| `image/*` | `image` |
| `video/*` | `video` |
| `audio/*` | `audio` |
| `application/pdf` | `pdf` |
| `application/msword`, `application/vnd.openxmlformats-officedocument.*` | `document` |
| 其他 | `other` |

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 | 示例 |
|--------|------|------|
| 200 | 成功 | GET 请求成功 |
| 201 | 已创建 | POST 创建成功 |
| 204 | 无内容 | DELETE 成功 |
| 400 | 请求错误 | 参数验证失败 |
| 401 | 未认证 | Token 无效或过期 |
| 403 | 禁止访问 | 权限不足 |
| 404 | 未找到 | 记录不存在 |
| 422 | 验证错误 | 请求体格式错误 |
| 500 | 服务器错误 | 内部错误 |

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误示例

#### 1. Token 无效

```bash
curl "http://localhost:3002/api/v1/auth/me" \
  -H "Authorization: Bearer INVALID_TOKEN"
```

**响应** (401):

```json
{
  "detail": "Invalid authentication credentials: Signature verification failed"
}
```

#### 2. 记录不存在

```bash
curl "http://localhost:3002/api/v1/records/non-existent-id"
```

**响应** (404):

```json
{
  "detail": "Record not found: non-existent-id"
}
```

#### 3. 权限不足

```bash
# 用户 A 尝试修改用户 B 的记录
curl -X PUT "http://localhost:3002/api/v1/records/RECORD_ID" \
  -H "Authorization: Bearer USER_A_TOKEN"
```

**响应** (403):

```json
{
  "detail": "Access denied: not the owner"
}
```

#### 4. 参数验证错误

```bash
curl -X POST "http://localhost:3002/api/v1/records" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "app_identifier": "",
    "collection_type": "post"
  }'
```

**响应** (422):

```json
{
  "detail": [
    {
      "loc": ["body", "app_identifier"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

---

## 最佳实践

### 1. 应用标识符命名规范

```python
# ✅ 推荐：使用小写字母和连字符
app_identifier = "blog-app"
app_identifier = "e-commerce-store"
app_identifier = "task-manager"

# ❌ 避免：使用下划线或大写
app_identifier = "blog_app"  # 会被转换为 blog-app
app_identifier = "BlogApp"   # 会被转换为 blogapp
```

### 2. Collection Type 设计

```python
# ✅ 推荐：使用单数形式，具体描述数据类型
collection_type = "post"
collection_type = "comment"
collection_type = "order"
collection_type = "product"

# ❌ 避免：复数形式或模糊名称
collection_type = "posts"   # 应该用 post
collection_type = "data"    # 太模糊
```

### 3. Payload 结构设计

```python
# ✅ 推荐：结构清晰，包含必要元数据
payload = {
  "content": "主要内容",
  "author": "张三",
  "tags": ["tag1", "tag2"],
  "metadata": {
    "word_count": 1500,
    "language": "zh-CN"
  }
}

# ❌ 避免：扁平结构，难以扩展
payload = {
  "content": "内容",
  "author_name": "张三",
  "tag1": "tag1",
  "tag2": "tag2"
}
```

### 4. 分页查询优化

```bash
# ✅ 推荐：合理设置 page_size
curl "http://localhost:3002/api/v1/records?page_size=20"

# ❌ 避免：page_size 过大
curl "http://localhost:3002/api/v1/records?page_size=1000"
```

### 5. Token 管理

```javascript
// ✅ 推荐：Token 过期前刷新
if (tokenExpiringSoon()) {
  await refreshToken()
}

// ✅ 推荐：存储在安全位置 (httpOnly cookie 或 secure storage)
localStorage.setItem('token', token)  // 仅用于开发
// 生产环境使用 httpOnly cookie
```

### 6. 错误处理

```python
# ✅ 推荐：客户端妥善处理错误
try {
  const response = await fetch('/api/v1/records', {...})
  if (!response.ok) {
    const error = await response.json()
    // 显示用户友好的错误信息
    showError(error.detail)
  }
} catch (error) {
  // 处理网络错误
}
```

### 7. 版本控制

```bash
# 每次更新都会递增 version 字段
# 可以用于实现乐观锁
PUT /api/v1/records/{id}?version=2
```

---

## 示例代码

### Python 客户端

```python
import requests
from typing import Any, Dict

class UnifiedBackendClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def create_record(self, app: str, collection_type: str, payload: Dict[str, Any]) -> Dict:
        """创建记录"""
        response = requests.post(
            f"{self.base_url}/api/v1/records",
            json={
                "app_identifier": app,
                "collection_type": collection_type,
                "payload": payload,
            },
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def list_records(self, **params) -> Dict:
        """查询记录"""
        response = requests.get(
            f"{self.base_url}/api/v1/records",
            params=params,
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_record(self, record_id: str) -> Dict:
        """获取详情"""
        response = requests.get(
            f"{self.base_url}/api/v1/records/{record_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

# 使用示例
client = UnifiedBackendClient(
    base_url="http://localhost:3002",
    token="your_jwt_token"
)

# 创建文章
post = client.create_record(
    app="blog-app",
    collection_type="post",
    payload={
        "title": "Python 异步编程",
        "content": "...",
    }
)

# 查询文章
posts = client.list_records(
    app_identifier="blog-app",
    collection_type="post",
    page=1,
    page_size=10
)
```

### JavaScript 客户端

```javascript
class UnifiedBackendClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  async createRecord(app, collectionType, payload) {
    const response = await fetch(`${this.baseUrl}/api/v1/records`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        app_identifier: app,
        collection_type: collectionType,
        payload,
      }),
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json();
  }

  async listRecords(params = {}) {
    const url = new URL(`${this.baseUrl}/api/v1/records`);
    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));

    const response = await fetch(url, { headers: this.headers });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json();
  }
}

// 使用示例
const client = new UnifiedBackendClient(
  'http://localhost:3002',
  'your_jwt_token'
);

// 创建记录
const post = await client.createRecord('blog-app', 'post', {
  title: 'JavaScript 异步编程',
  content: '...',
});

// 查询记录
const posts = await client.listRecords({
  app_identifier: 'blog-app',
  collection_type: 'post',
  page: 1,
  page_size: 10,
});
```

---

## 更多资源

- [Swagger UI](http://localhost:3002/api/v1/docs) - 交互式 API 文档
- [ReDoc](http://localhost:3002/api/v1/redoc) - 备用 API 文档
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
