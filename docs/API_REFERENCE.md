# API 参考手册

统一后端平台完整 API 参考。

---

## 📋 目录

- [认证相关 API](#认证相关-api)
- [记录管理 API](#记录管理-api)
- [文件管理 API](#文件管理-api)
- [错误处理](#错误处理)

---

## 认证相关 API

### 基础信息

所有需要认证的 API 都需要在请求头中携带 JWT Token：

```
Authorization: Bearer <your-jwt-token>
```

### 1. 获取当前用户信息

**端点**: `GET /api/v1/auth/me`

**请求头**:
```
Authorization: Bearer <token>
```

**响应**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "casdoor_id": "casdoor-user-id",
  "email": "user@example.com",
  "display_name": "张三",
  "avatar": "http://localhost:8000/avatar.png",
  "role": "user",
  "is_active": true,
  "created_at": "2024-12-23T12:00:00Z",
  "last_login_at": "2024-12-23T14:30:00Z"
}
```

---

## 记录管理 API

### 1. 创建记录

**端点**: `POST /api/v1/records`

**请求头**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体**:
```json
{
  "app_identifier": "blog-app",
  "collection_type": "post",
  "payload": {
    "任意": "JSON 数据",
    "number": 123,
    "array": ["a", "b"]
  },
  "title": "记录标题（可选）",
  "description": "记录描述（可选）",
  "is_published": true,
  "owner_id": "user-id（可选，默认为当前用户）"
}
```

**响应**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "app_identifier": "blog-app",
  "collection_type": "post",
  "owner_id": "user-id",
  "payload": { /* 你的数据 */ },
  "title": "记录标题",
  "description": "记录描述",
  "is_deleted": false,
  "is_published": true,
  "version": 1,
  "view_count": 0,
  "created_at": "2024-12-23T12:00:00Z",
  "updated_at": "2024-12-23T12:00:00Z"
}
```

---

### 2. 查询记录列表

**端点**: `GET /api/v1/records`

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| app_identifier | string | ✅ | 应用标识符 |
| collection_type | string | ✅ | 数据类型 |
| owner_id | string | ❌ | 过滤所有者（使用 `current` 表示当前用户） |
| is_published | boolean | ❌ | 过滤发布状态 |
| is_deleted | boolean | ❌ | 是否包含已删除记录（默认 false） |
| page | number | ❌ | 页码（默认 1） |
| page_size | number | ❌ | 每页数量（默认 20，最大 100） |
| search | string | ❌ | 全文搜索关键词 |
| sort_by | string | ❌ | 排序字段（created_at, updated_at, title 等） |
| sort_order | string | ❌ | 排序方向（asc, desc，默认 desc） |

**请求示例**:
```
GET /api/v1/records?app_identifier=blog-app&collection_type=post&page=1&page_size=20&is_published=true
```

**响应**:
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "app_identifier": "blog-app",
      "collection_type": "post",
      "payload": { /* 你的数据 */ },
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

---

### 3. 获取单条记录

**端点**: `GET /api/v1/records/{id}`

**路径参数**:
- `id`: 记录 ID (UUID)

**响应**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "app_identifier": "blog-app",
  "collection_type": "post",
  "payload": { /* 你的数据 */ },
  "created_at": "2024-12-23T12:00:00Z"
}
```

---

### 4. 更新记录

**端点**: `PATCH /api/v1/records/{id}`

**路径参数**:
- `id`: 记录 ID (UUID)

**请求体**:
```json
{
  "payload": {
    "更新后的": "数据"
  },
  "title": "新标题",
  "description": "新描述",
  "is_published": false
}
```

**注意**:
- `payload` 完全替换原数据，不是合并
- `version` 会自动递增

**响应**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "version": 2,
  "updated_at": "2024-12-23T13:00:00Z"
}
```

---

### 5. 删除记录

**端点**: `DELETE /api/v1/records/{id}`

**路径参数**:
- `id`: 记录 ID (UUID)

**查询参数**:
- `permanent`: 是否永久删除（默认 false，软删除）

**请求示例**:
```
DELETE /api/v1/records/550e8400-e29b-41d4-a716-446655440000
DELETE /api/v1/records/550e8400-e29b-41d4-a716-446655440000?permanent=true
```

**响应**:
```
204 No Content
```

---

### 6. 批量创建记录

**端点**: `POST /api/v1/records/batch`

**请求体**:
```json
{
  "items": [
    {
      "app_identifier": "blog-app",
      "collection_type": "post",
      "payload": { "title": "文章1" }
    },
    {
      "app_identifier": "blog-app",
      "collection_type": "post",
      "payload": { "title": "文章2" }
    }
  ],
  "stop_on_error": false
}
```

**响应**:
```json
{
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "results": [
    {
      "id": "uuid-1",
      "index": 0,
      "success": true,
      "error": null
    },
    {
      "id": "uuid-2",
      "index": 1,
      "success": true,
      "error": null
    }
  ]
}
```

---

### 7. 批量更新记录

**端点**: `PUT /api/v1/records/batch`

**请求体**:
```json
{
  "ids": ["uuid-1", "uuid-2", "uuid-3"],
  "updates": {
    "is_published": true
  },
  "stop_on_error": false
}
```

**响应**:
```json
{
  "total": 3,
  "succeeded": 3,
  "failed": 0,
  "results": [...]
}
```

---

### 8. 批量删除记录

**端点**: `DELETE /api/v1/records/batch`

**请求体**:
```json
{
  "ids": ["uuid-1", "uuid-2"],
  "stop_on_error": false
}
```

**响应**:
```json
{
  "total": 2,
  "succeeded": 2,
  "failed": 0
}
```

---

## 文件管理 API

### 1. 上传文件（直接上传）

**端点**: `POST /api/v1/files/upload`

**请求头**:
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**表单参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | ✅ | 文件对象 |
| app_identifier | string | ✅ | 应用标识符 |
| title | string | ❌ | 文件标题 |
| description | string | ❌ | 文件描述 |
| alt_text | string | ❌ | 图片 alt 文本 |
| is_public | boolean | ❌ | 是否公开访问（默认 false） |

**请求示例** (JavaScript):
```javascript
const formData = new FormData();
formData.append('file', fileObject);
formData.append('app_identifier', 'blog-app');
formData.append('title', '我的图片');
formData.append('is_public', true);

await fetch('/api/v1/files/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

**响应**:
```json
{
  "id": "file-uuid",
  "filename": "photo.jpg",
  "file_size": 1024000,
  "content_type": "image/jpeg",
  "file_extension": "jpg",
  "category": "image",
  "public_url": "http://localhost:9100/unified-files/blog-app/2024/12/file-uuid-photo.jpg",
  "storage_path": "blog-app/2024/12/file-uuid-photo.jpg",
  "title": "我的图片",
  "status": "uploaded",
  "is_public": true,
  "created_at": "2024-12-23T12:00:00Z"
}
```

---

### 2. 获取预签名上传 URL（大文件）

**端点**: `POST /api/v1/files/upload/presigned`

**请求体**:
```json
{
  "filename": "large-video.mp4",
  "content_type": "video/mp4",
  "file_size": 104857600,
  "app_identifier": "blog-app"
}
```

**响应**:
```json
{
  "file_id": "file-uuid",
  "upload_url": "https://minio...?signature=...",
  "headers": {
    "Content-Type": "video/mp4"
  },
  "expires_in": 3600
}
```

**上传步骤**:
1. 调用此接口获取预签名 URL
2. 使用返回的 URL 直接 PUT 文件到 MinIO
3. 调用 `/api/v1/files/upload/confirm` 确认上传完成

---

### 3. 确认上传完成

**端点**: `POST /api/v1/files/upload/confirm`

**请求体**:
```json
{
  "file_id": "file-uuid"
}
```

**响应**:
```json
{
  "id": "file-uuid",
  "status": "uploaded",
  "public_url": "http://localhost:9100/..."
}
```

---

### 4. 查询文件列表

**端点**: `GET /api/v1/files`

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| app_identifier | string | ❌ | 过滤应用 |
| owner_id | string | ❌ | 过滤所有者（`current` 表示当前用户） |
| category | string | ❌ | 文件分类（image, video, document, audio） |
| content_type | string | ❌ | MIME 类型过滤 |
| is_public | boolean | ❌ | 过滤公开状态 |
| is_deleted | boolean | ❌ | 是否包含已删除（默认 false） |
| page | number | ❌ | 页码（默认 1） |
| page_size | number | ❌ | 每页数量（默认 20） |

**响应**:
```json
{
  "items": [
    {
      "id": "file-uuid",
      "filename": "photo.jpg",
      "file_size": 1024000,
      "content_type": "image/jpeg",
      "category": "image",
      "public_url": "http://localhost:9100/...",
      "created_at": "2024-12-23T12:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

---

### 5. 获取文件详情

**端点**: `GET /api/v1/files/{file_id}`

**路径参数**:
- `file_id`: 文件 ID (UUID)

**响应**:
```json
{
  "id": "file-uuid",
  "filename": "photo.jpg",
  "file_size": 1024000,
  "content_type": "image/jpeg",
  "file_extension": "jpg",
  "category": "image",
  "width": 1920,
  "height": 1080,
  "thumbnail_id": "thumbnail-uuid",
  "public_url": "http://localhost:9100/...",
  "title": "图片标题",
  "description": "图片描述",
  "alt_text": "图片 alt 文本",
  "status": "uploaded",
  "is_public": true,
  "download_count": 10,
  "view_count": 50,
  "created_at": "2024-12-23T12:00:00Z"
}
```

---

### 6. 获取下载链接

**端点**: `GET /api/v1/files/{file_id}/download`

**路径参数**:
- `file_id`: 文件 ID (UUID)

**响应**:
```json
{
  "url": "http://localhost:9100/unified-files/...?signature=...",
  "expires_in": 604800
}
```

**说明**: 返回的 URL 有效期 7 天

---

### 7. 更新文件元数据

**端点**: `PATCH /api/v1/files/{file_id}`

**路径参数**:
- `file_id`: 文件 ID (UUID)

**请求体**:
```json
{
  "title": "新标题",
  "description": "新描述",
  "alt_text": "新的 alt 文本",
  "is_public": false,
  "metadata": {
    "custom": "自定义数据"
  }
}
```

**响应**:
```json
{
  "id": "file-uuid",
  "title": "新标题",
  "updated_at": "2024-12-23T13:00:00Z"
}
```

---

### 8. 删除文件

**端点**: `DELETE /api/v1/files/{file_id}`

**路径参数**:
- `file_id`: 文件 ID (UUID)

**查询参数**:
- `delete_from_storage`: 是否从存储中删除（默认 false）

**请求示例**:
```
DELETE /api/v1/files/file-uuid
DELETE /api/v1/files/file-uuid?delete_from_storage=true
```

**响应**:
```
204 No Content
```

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 成功（无返回内容） |
| 400 | 请求参数错误 |
| 401 | 未认证（Token 无效或过期） |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 413 | 文件过大 |
| 422 | 数据验证失败 |
| 500 | 服务器错误 |

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 验证错误示例

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 数据限制

### 记录限制

- 单次查询最多返回 100 条记录
- `payload` 最大大小：16MB

### 文件限制

| 文件类型 | 最大大小 |
|----------|----------|
| 图片 | 50MB |
| 视频 | 500MB |
| 文档 | 500MB |
| 音频 | 500MB |

### 支持的文件类型

**图片**: jpg, jpeg, png, gif, webp, svg, bmp, tiff

**视频**: mp4, mpeg, quicktime, avi, wmv, webm

**文档**: pdf, doc, docx, xls, xlsx, ppt, pptx, txt, csv

**音频**: mp3, wav, flac, aac, ogg

---

## 示例代码

### cURL 示例

```bash
# 创建记录
curl -X POST http://localhost:9000/api/v1/records \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "app_identifier": "blog-app",
    "collection_type": "post",
    "payload": {"title": "Hello"},
    "is_published": true
  }'

# 查询记录
curl http://localhost:9000/api/v1/records \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -G \
  --data-urlencode "app_identifier=blog-app" \
  --data-urlencode "collection_type=post"

# 上传文件
curl -X POST http://localhost:9000/api/v1/files/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@photo.jpg" \
  -F "app_identifier=blog-app" \
  -F "title=我的图片"
```

---

**更新时间**: 2024-12-23
