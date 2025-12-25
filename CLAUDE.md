# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Unified Backend Platform 是一个**模块化单体**架构的统一后端服务，基于 FastAPI + MongoDB + Casdoor 构建，支持多个独立应用共享同一套后端基础设施。

核心设计理念：通过 `UnifiedRecord` 模型的 `payload` 字段存储任意 JSON 结构的业务数据，实现单一数据模型支持多种应用场景。

## 常用命令

### Docker 容器管理
```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看实时日志
docker compose logs -f backend
docker compose logs -f mongo

# 重启特定服务
docker compose restart backend

# 停止所有服务
docker compose down

# 重新构建并启动
docker compose up -d --build
```

### 本地开发
```bash
# 进入后端目录
cd backend

# 安装依赖 (推荐使用 uv)
uv pip install -r requirements.txt

# 启动开发服务器 (连接 Docker 中的 MongoDB)
uvicorn app.main:app --reload --host 0.0.0.0 --port 3002

# 类型检查
mypy backend/app

# 代码格式化
black backend/app

# Lint 检查
ruff check backend/app
```

### 数据库备份
```bash
# 备份 MongoDB
./scripts/backup-mongodb.sh

# 恢复 MongoDB
./scripts/restore-mongodb.sh <backup-file>
```

### 服务访问地址
| 服务 | URL | 说明 |
|------|-----|------|
| Backend API | http://localhost:9000 | FastAPI 后端 |
| API 文档 | http://localhost:9000/api/v1/docs | Swagger UI |
| Mongo Express | http://localhost:8081 | 数据库管理界面 |
| Casdoor | http://localhost:8000 | SSO 管理界面 |
| MinIO Console | http://localhost:9101 | 对象存储管理界面 |
| MinIO API | http://localhost:9100 | S3 兼容 API |
| Redis | localhost:6379 | 缓存服务 |
| MongoDB | localhost:27017 | 业务数据库 |
| PostgreSQL | localhost:5432 | Casdoor 数据库 |

## 核心架构

### 数据模型设计

项目采用"统一记录"模式，所有业务数据通过 `UnifiedRecord` 模型存储：

```python
class UnifiedRecord(Document):
    id: UUID                              # 记录 ID
    app_identifier: str                   # 应用标识 (如: blog-app)
    collection_type: str                  # 数据类型 (如: post)
    owner_id: UUID | None                 # 所有者用户 ID
    payload: dict[str, Any]               # 🔥 任意 JSON 业务数据
    title: str | None                     # 标题
    description: str | None               # 描述
    is_deleted: bool                      # 软删除标记
    is_published: bool                    # 发布状态
    version: int                          # 版本号
    view_count: int                       # 查看次数
    created_at: datetime
    updated_at: datetime
```

**关键特性**：
- `app_identifier` + `collection_type` 组合实现数据隔离
- `payload` 字段使用 `dict[str, Any]` 支持任意业务结构
- 软删除通过 `is_deleted` 标记实现
- 复合索引优化查询性能：`(app_identifier, collection_type, owner_id)`

### 认证架构

项目使用 **Casdoor SSO** + **JWT** 实现统一认证，并集成完整的 **RBAC 权限系统**：

1. 用户在 Casdoor 登录，获取 JWT Token
2. 后端验证 JWT 并同步/创建本地 `User` 记录
3. 后端自动同步 Casdoor 权限组到本地角色
4. 后续请求通过 `Authorization: Bearer <token>` 认证
5. 权限检查基于用户角色和权限列表

```python
# 路由中使用认证依赖
from app.core.security import get_current_user
from app.core.permissions import require_permission

@router.post("/api/v1/records")
async def create_record(
    data: UnifiedRecordCreate,
    current_user: User = Depends(get_current_user),  # 必须认证
): ...

# 权限检查
@router.delete("/api/v1/records/{id}")
async def delete_record(
    id: UUID,
    current_user: User = Depends(require_permission("posts:delete")),  # 需要 posts:delete 权限
): ...

# 超级管理员检查
from app.core.security import require_superuser

@router.delete("/api/v1/admin/users/{id}")
async def admin_delete_user(
    id: UUID,
    current_user: User = Depends(require_superuser),  # 需要超级管理员
): ...
```

**权限系统特性**：
- **RBAC 架构**: 用户 → 角色 → 权限三层结构
- **Casdoor 同步**: 自动同步 Casdoor 权限组到本地角色
- **通配符支持**: `posts:*` 匹配所有文章操作，`*:*` 匹配所有操作
- **Redis 缓存**: 用户权限缓存 1 小时，提升性能
- **应用级隔离**: 通过 `app_identifier` 实现多应用权限隔离

### 项目目录结构

```
shared-database-service/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/      # API 路由
│   │   │   │   ├── auth.py         # 认证端点
│   │   │   │   ├── records.py      # 记录 CRUD (含批量操作)
│   │   │   │   ├── files.py        # 文件管理 API
│   │   │   │   └── permissions.py  # 权限管理 API ✨
│   │   │   └── schemas/        # Pydantic 请求/响应模型
│   │   │       ├── record.py       # 记录相关 Schema
│   │   │       ├── file.py         # 文件相关 Schema
│   │   │       └── permission.py   # 权限相关 Schema ✨
│   │   ├── core/
│   │   │   ├── config.py           # 配置管理 (Pydantic Settings)
│   │   │   ├── security.py         # JWT 验证、用户同步
│   │   │   └── permissions.py      # 权限检查装饰器 ✨
│   │   ├── db/
│   │   │   └── mongodb.py          # MongoDB 连接管理
│   │   ├── models/
│   │   │   ├── user.py             # 用户模型
│   │   │   ├── unified_record.py   # 统一记录模型
│   │   │   ├── file.py             # 文件元数据模型
│   │   │   └── permission.py       # 权限模型 (Permission, Role, UserRoleAssignment) ✨
│   │   ├── services/
│   │   │   ├── minio_service.py        # MinIO/S3 对象存储服务
│   │   │   ├── permission_service.py   # 权限服务 ✨
│   │   │   └── casdoor_sync_service.py # Casdoor 权限组同步 ✨
│   │   └── main.py                 # FastAPI 应用入口
│   ├── Dockerfile
│   └── requirements.txt
├── scripts/
│   ├── backup-mongodb.sh
│   ├── restore-mongodb.sh
│   └── migrate_to_rbac.py       # 权限系统迁移脚本 ✨
├── docker-compose.yml
├── .env.example
└── README.md
```

## 开发指南

### 添加新的 API 端点

1. **创建 Pydantic Schema** (`backend/app/api/v1/schemas/xxx.py`)：
```python
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    value: int

class ItemResponse(BaseModel):
    id: UUID
    name: str
    value: int

    class Config:
        from_attributes = True
```

2. **创建路由** (`backend/app/api/v1/endpoints/xxx.py`)：
```python
from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/items", tags=["Items"])

@router.post("", response_model=ItemResponse)
async def create_item(
    data: ItemCreate,
    current_user: User = Depends(get_current_user),
) -> ItemResponse:
    # 实现逻辑
    pass
```

3. **注册路由** (`backend/app/main.py`)：
```python
from app.api.v1.endpoints import xxx

app.include_router(
    xxx.router,
    prefix=settings.api_prefix,
    tags=["XXX"],
)
```

### 数据库查询 (Beanie ODM)

```python
from app.models.unified_record import UnifiedRecord
from uuid import UUID

# 查询单条记录
record = await UnifiedRecord.find_one(UnifiedRecord.id == record_id)

# 条件查询
records = await UnifiedRecord.find(
    UnifiedRecord.app_identifier == "blog-app",
    UnifiedRecord.collection_type == "post",
    UnifiedRecord.is_published == True,
).to_list()

# 分页查询
records = await UnifiedRecord.find(
    UnifiedRecord.is_deleted == False,
).sort(-UnifiedRecord.created_at).skip(0).limit(20).to_list()

# 创建记录
new_record = UnifiedRecord(
    app_identifier="blog-app",
    collection_type="post",
    payload={"title": "Hello", "content": "..."},
)
await new_record.insert()

# 更新记录
record.title = "New Title"
await record.save()

# 软删除
record.is_deleted = True
await record.save()
```

### 环境变量配置

所有配置通过 `.env` 文件管理，关键配置项：

```bash
# MongoDB 连接字符串 (后端容器内使用)
MONGODB_URL=mongodb://admin:PASSWORD@mongo:27017/unified_backend?authSource=admin

# JWT 密钥 (必须 ≥32 字符)
JWT_SECRET=your-super-secret-jwt-key-change-in-production-32characters

# Casdoor 地址
CASDOOR_ORIGIN=http://localhost:3000

# CORS 源 (逗号分隔)
CORS_ORIGINS=http://localhost:3000,http://localhost:3002
```

## 技术栈说明

| 组件 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| Web 框架 | FastAPI | 0.115 | 异步 Python 框架 |
| 数据库 | MongoDB | 6 | Schema-less 文档数据库 |
| ODM | Beanie | 1.27 | 异步 MongoDB ODM，基于 Pydantic |
| 驱动 | Motor | 3.6 | 异步 MongoDB 驱动 |
| 缓存 | Redis | 7 | 内存缓存 |
| 认证 | Casdoor | latest | SSO 单点登录 |
| 配置管理 | Pydantic Settings | 2.6 | 类型安全的环境变量 |

## 关键注意事项

1. **异步操作**：所有数据库操作必须使用 `async/await`
2. **软删除**：删除记录时设置 `is_deleted=True`，而非物理删除
3. **用户同步**：首次 JWT 认证时会自动创建本地 User 记录
4. **Payload 灵活性**：payload 可存储任意 JSON，但前端应负责结构验证
5. **索引优化**：复合索引 `(app_identifier, collection_type, owner_id)` 已配置

## 容器网络

- Docker 网络名称：`unified-network`
- 服务间通过容器名通信：`mongo`, `redis`, `postgres`, `casdoor`, `minio`
- 后端连接数据库使用容器名：`mongodb://admin:pass@mongo:27017/...`

## 新增功能 (2024-12)

### 1. 批量操作 API

支持批量创建、更新、删除 UnifiedRecord：

```bash
# 批量创建记录
POST /api/v1/records/batch
{
  "items": [
    {"app_identifier": "blog-app", "collection_type": "post", "payload": {...}},
    {"app_identifier": "blog-app", "collection_type": "post", "payload": {...}}
  ],
  "stop_on_error": false
}

# 批量更新记录
PUT /api/v1/records/batch
{
  "ids": ["uuid1", "uuid2"],
  "updates": {"is_published": true},
  "stop_on_error": false
}

# 批量删除记录
DELETE /api/v1/records/batch
{
  "ids": ["uuid1", "uuid2"],
  "stop_on_error": false
}
```

**响应格式**：
```json
{
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "results": [
    {"id": "uuid1", "index": 0, "success": true, "error": null},
    {"id": "uuid2", "index": 1, "success": true, "error": null}
  ]
}
```

### 2. 文件管理系统

基于 MinIO/S3 的对象存储服务，支持图片、视频、PDF、音频等多种文件类型。

#### 核心特性

- **文件分类**：image, video, document, audio, archive, other
- **文件大小限制**：图片 50MB，视频/文档 500MB
- **存储路径**：`{app_identifier}/{year}/{month}/{file_id}-{filename}`
- **软删除**：支持标记删除和彻底删除
- **权限控制**：公开/私有文件访问控制

#### API 端点

```bash
# 直接上传文件 (小文件)
POST /api/v1/files/upload
Content-Type: multipart/form-data
file: <binary>
app_identifier: "blog-app"
title: "My Photo"
is_public: true

# 获取预签名上传 URL (大文件/前端直传)
POST /api/v1/files/upload/presigned
{
  "filename": "large-video.mp4",
  "content_type": "video/mp4",
  "file_size": 104857600,
  "app_identifier": "forum-app"
}

# 确认预签名上传完成
POST /api/v1/files/upload/confirm
{
  "file_id": "uuid"
}

# 查询文件列表
GET /api/v1/files?category=image&page=1&page_size=20

# 获取文件详情
GET /api/v1/files/{file_id}

# 下载文件 (返回预签名 URL)
GET /api/v1/files/{file_id}/download

# 更新文件元数据
PATCH /api/v1/files/{file_id}
{
  "title": "New Title",
  "is_public": false
}

# 删除文件
DELETE /api/v1/files/{file_id}?delete_from_storage=false
```

#### File 模型

```python
class File(Document):
    id: UUID                              # 文件 ID
    owner_id: UUID | None                 # 所有者用户 ID
    app_identifier: str                   # 应用标识符

    # 文件信息
    filename: str                         # 原始文件名
    file_size: int                         # 文件大小 (字节)
    content_type: str                      # MIME 类型
    file_extension: str                    # 文件扩展名
    category: FileCategory                 # 文件分类

    # 存储信息
    storage_path: str                      # 对象存储路径
    bucket_name: str                       # 存储桶名称
    public_url: str | None                 # 公共访问 URL

    # 图片信息
    thumbnail_id: UUID | None              # 缩略图文件 ID
    width: int | None                      # 图片宽度
    height: int | None                     # 图片高度

    # 元数据
    title: str | None                      # 文件标题
    description: str | None                # 文件描述
    alt_text: str | None                   # 图片 alt 文本
    status: FileStatus                     # 文件状态
    is_public: bool                        # 是否公开
    is_deleted: bool                       # 是否已删除

    # 统计
    download_count: int                    # 下载次数
    view_count: int                        # 查看次数

    # 自定义元数据
    metadata: dict[str, Any]              # 任意 JSON 数据
```

### 3. MinIO 对象存储

MinIO 服务配置：

| 配置项 | 值 |
|--------|-----|
| 端口 | API: 9100, Console: 9101 |
| 访问密钥 | minioadmin / minioadmin123 |
| 主存储桶 | unified-files |
| 缩略图存储桶 | unified-thumbnails |

**存储路径规则**：
- 主文件：`{app_identifier}/{year}/{month}/{file_id}-{filename}`
- 缩略图：`{app_identifier}/{year}/{month}/thumbnails/{file_id}.webp`

### 环境变量配置 (新增)

```bash
# MinIO / S3 配置
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=unified-files
MINIO_THUMBNAIL_BUCKET=unified-thumbnails
MINIO_PUBLIC_URL=http://localhost:9100

# 文件大小限制
MAX_FILE_SIZE=524288000        # 500MB
MAX_IMAGE_SIZE=52428800         # 50MB
MAX_VIDEO_SIZE=524288000        # 500MB
```
