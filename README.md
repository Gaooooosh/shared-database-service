# Unified Backend Platform

> **模块化单体统一后端服务** - 支持多应用共享数据的灵活后端平台

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-green.svg)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 目录

- [项目概述](#项目概述)
- [核心特性](#核心特性)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [API 文档](#api-文档)
- [配置说明](#配置说明)
- [开发指南](#开发指南)
- [部署指南](#部署指南)
- [开发进度](#开发进度)

---

## 项目概述

Unified Backend Platform 是一个**模块化单体**架构的统一后端服务，旨在支持未来孵化出的多个独立应用（App）共享同一套基础设施。

### 设计理念

- **统一认证**: 集成 Casdoor SSO，实现多应用单点登录
- **灵活存储**: 利用 MongoDB 的 Schema-less 特性，通过 `UnifiedRecord` 模型支持多变的业务需求
- **对象存储**: 集成 MinIO S3 兼容存储，支持大文件上传
- **容器化部署**: 基于 Docker Compose，适合单机部署约 100 名用户的场景
- **企业级**: 完整的权限控制、批量操作、文件管理、软删除等特性

### 适用场景

- 需要快速孵化多个相关应用的团队
- 业务模式不固定，需要灵活数据结构的场景
- 内容管理系统（博客、CMS）
- 论坛和社区系统
- 中小型 SaaS 产品后端
- 内部工具平台

---

## 核心特性

### 1. 统一认证 (SSO)

- 集成 **Casdoor** 提供企业级 SSO
- JWT Token 验证，自动同步用户信息
- 基于角色的访问控制 (RBAC)
- 用户权限管理

### 2. 灵活数据模型

核心的 `UnifiedRecord` 模型支持任意 JSON 业务数据：

```python
# 博客应用存储文章
UnifiedRecord(
    app_identifier="blog-app",
    collection_type="post",
    payload={"title": "Hello", "content": "...", "tags": ["tech"]}
)

# 商店应用存储订单
UnifiedRecord(
    app_identifier="shop-app",
    collection_type="order",
    payload={"items": [...], "total": 99.99}
)

# 论坛应用存储主题
UnifiedRecord(
    app_identifier="forum-app",
    collection_type="thread",
    payload={"board_id": "...", "content": "...", "reply_count": 0}
)
```

### 3. 批量操作 API ✨ 新功能

- 批量创建记录（最多 100 条）
- 批量更新记录
- 批量删除记录
- 详细的错误报告和事务控制

### 4. 文件管理系统 ✨ 新功能

- **MinIO/S3 对象存储集成**
- 支持多种文件类型：图片、视频、PDF、音频
- 直接上传和预签名 URL 上传两种模式
- 文件元数据管理
- 公开/私有访问控制
- 文件分类和搜索

### 5. 完整 CRUD API

- RESTful API 设计
- 支持分页、排序、搜索
- 软删除机制
- 版本控制
- 查看计数

### 6. 企业级特性

- 完整的 CORS 配置
- 健康检查端点
- 环境变量管理
- Docker 容器化部署
- 数据备份和恢复脚本

---

## 技术架构

### 技术栈

| 组件 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| 语言 | Python | 3.11+ | 类型提示、性能优化 |
| Web 框架 | FastAPI | 0.115 | 异步、自动文档生成 |
| 数据库 | MongoDB | 6.0+ | Schema-less 灵活存储 |
| ODM | Beanie | 1.27 | 异步 MongoDB ODM |
| 驱动 | Motor | 3.6 | 异步 MongoDB 驱动 |
| 缓存 | Redis | 7 | Session 和缓存 |
| 认证 | Casdoor | latest | SSO 单点登录 |
| 对象存储 | MinIO | latest | S3 兼容存储 |
| 容器化 | Docker Compose | 2.0+ | 单机部署 |
| 配置管理 | Pydantic Settings | 2.6 | 类型安全的环境变量 |

### 服务架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose 环境                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Casdoor  │  │  Redis   │  │PostgreSQL│  │  MinIO   │       │
│  │  :8000   │  │  :6379   │  │  :5432   │  │ :9100/91 │       │
│  │ (SSO)    │  │ (缓存)   │  │ (Casdoor)│  │ (存储)   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│       │                                                    │
│       │ JWT                                               │
│       ▼                                                    │
│  ┌──────────┐  ┌──────────┐                               │
│  │ Backend  │──│  Mongo   │                               │
│  │  :9000   │  │  :27017  │                               │
│  │ (FastAPI)│  │ (业务数据)│                               │
│  └──────────┘  └──────────┘                               │
│       │                                                    │
│       └──> Mongo Express :8081 (管理界面)                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 数据模型

#### User (本地用户映射)

```python
class User(Document):
    id: UUID                    # 本地用户 ID
    casdoor_id: str             # Casdoor 关联 ID
    email: str
    display_name: str | None
    role: Literal["admin", "user", "guest"]
    last_login_at: datetime
```

#### UnifiedRecord (通用业务数据)

```python
class UnifiedRecord(Document):
    id: UUID
    app_identifier: str         # 应用标识 (如: blog-app)
    collection_type: str        # 数据类型 (如: post)
    owner_id: UUID | None       # 所有者
    payload: dict[str, Any]     # 🔥 任意 JSON 业务数据
    title: str | None
    description: str | None
    is_published: bool
    is_deleted: bool
    version: int
    view_count: int
    created_at: datetime
    updated_at: datetime
```

#### File (文件元数据)

```python
class File(Document):
    id: UUID
    owner_id: UUID | None
    app_identifier: str
    filename: str
    file_size: int
    content_type: str
    storage_path: str
    bucket_name: str
    category: FileCategory      # image, video, pdf, audio, document, other
    is_public: bool
    is_deleted: bool
    created_at: datetime
```

---

## 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- (可选) Python 3.11+ (本地开发)

### 1. 克隆项目

```bash
git clone <repository-url>
cd shared-database-service
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，修改敏感密码
nano .env
```

**必须修改的配置**：
```bash
# MongoDB 密码
MONGO_ROOT_PASSWORD=your_secure_password

# PostgreSQL 密码
POSTGRES_PASSWORD=your_secure_password

# MinIO 密码
MINIO_ROOT_PASSWORD=your_secure_password

# JWT 密钥 (至少 32 字符)
JWT_SECRET=your_super_secret_jwt_key_at_least_32_characters
```

### 3. 启动所有服务

```bash
# 启动所有容器
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend
```

### 4. 验证部署

```bash
# 健康检查
curl http://localhost:9000/health

# 访问 API 文档
open http://localhost:9000/api/v1/docs

# 访问 MongoDB 管理界面
open http://localhost:8081
```

### 5. 初始化 Casdoor

```bash
# 访问 Casdoor 管理界面
open http://localhost:8000

# 首次访问需要创建管理员账户
```

---

## API 文档

### 服务端点

| 服务 | URL | 说明 |
|------|-----|------|
| Backend API | http://localhost:9000 | FastAPI 后端 |
| API 文档 | http://localhost:9000/api/v1/docs | Swagger UI |
| Casdoor | http://localhost:8000 | SSO 管理界面 |
| Mongo Express | http://localhost:8081 | 数据库管理 |
| MinIO Console | http://localhost:9101 | 存储管理界面 |

### 核心 API 端点

#### 认证相关

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/auth/me` | 获取当前用户信息 |
| POST | `/api/v1/auth/refresh` | 刷新用户信息 |

#### 记录管理 (UnifiedRecord)

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/records` | 创建记录 | 必须 |
| GET | `/api/v1/records` | 查询列表 | 可选 |
| GET | `/api/v1/records/{id}` | 获取详情 | 可选 |
| PUT | `/api/v1/records/{id}` | 完整更新 | 必须 |
| PATCH | `/api/v1/records/{id}` | 部分更新 | 必须 |
| DELETE | `/api/v1/records/{id}` | 软删除 | 必须 |

#### 批量操作 (UnifiedRecord) ✨

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/records/batch` | 批量创建 (最多100条) | 必须 |
| PUT | `/api/v1/records/batch` | 批量更新 | 必须 |
| DELETE | `/api/v1/records/batch` | 批量删除 | 必须 |

#### 文件管理 (File) ✨

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/files/upload` | 上传文件 | 必须 |
| POST | `/api/v1/files/presign` | 获取预签名 URL | 必须 |
| GET | `/api/v1/files` | 查询文件列表 | 可选 |
| GET | `/api/v1/files/{file_id}` | 获取文件详情 | 可选 |
| GET | `/api/v1/files/{file_id}/download` | 下载文件 | 可选 |
| DELETE | `/api/v1/files/{file_id}` | 删除文件 | 必须 |

### API 使用示例

#### 1. 获取当前用户信息

```bash
curl -X GET "http://localhost:9000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_CASDOOR_JWT_TOKEN"
```

**响应**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "casdoor_id": "user_id_from_casdoor",
  "email": "user@example.com",
  "display_name": "张三",
  "role": "user",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### 2. 创建记录

```bash
curl -X POST "http://localhost:9000/api/v1/records" \
  -H "Authorization: Bearer YOUR_CASDOOR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "app_identifier": "blog-app",
    "collection_type": "post",
    "title": "我的第一篇文章",
    "description": "这是一篇关于 FastAPI 的文章",
    "payload": {
      "content": "文章正文内容...",
      "tags": ["python", "fastapi"],
      "category": "技术"
    },
    "is_published": true
  }'
```

#### 3. 批量创建记录 ✨

```bash
curl -X POST "http://localhost:9000/api/v1/records/batch" \
  -H "Authorization: Bearer YOUR_CASDOOR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "app_identifier": "blog-app",
        "collection_type": "post",
        "title": "文章 1",
        "payload": {"content": "内容 1"}
      },
      {
        "app_identifier": "blog-app",
        "collection_type": "post",
        "title": "文章 2",
        "payload": {"content": "内容 2"}
      }
    ],
    "stop_on_error": false
  }'
```

#### 4. 上传文件 ✨

```bash
# 小文件直接上传
curl -X POST "http://localhost:9000/api/v1/files/upload" \
  -H "Authorization: Bearer YOUR_CASDOOR_JWT_TOKEN" \
  -F "file=@/path/to/file.jpg" \
  -F "app_identifier=blog-app"

# 大文件使用预签名 URL
curl -X POST "http://localhost:9000/api/v1/files/presign" \
  -H "Authorization: Bearer YOUR_CASDOOR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "large-video.mp4",
    "content_type": "video/mp4",
    "file_size": 104857600,
    "app_identifier": "blog-app"
  }'

# 使用返回的 presigned_url 直接上传到 MinIO
curl -X PUT "<presigned_url>" \
  -H "Content-Type: video/mp4" \
  --upload-file /path/to/large-video.mp4
```

#### 5. 查询记录列表

```bash
# 查询所有博客文章
curl "http://localhost:9000/api/v1/records?app_identifier=blog-app&collection_type=post"

# 搜索包含关键词的记录
curl "http://localhost:9000/api/v1/records?search=FastAPI"

# 分页查询
curl "http://localhost:9000/api/v1/records?page=1&page_size=10&sort_by=created_at&sort_order=desc"
```

### 查询参数说明

**GET /api/v1/records** 支持的查询参数：

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `app_identifier` | string | 筛选应用 | `blog-app` |
| `collection_type` | string | 筛选数据类型 | `post` |
| `is_published` | boolean | 发布状态 | `true` |
| `owner_id` | UUID | 所有者 ID | `550e8400-...` |
| `search` | string | 搜索标题/描述 | `关键词` |
| `page` | integer | 页码 (默认 1) | `1` |
| `page_size` | integer | 每页大小 (1-100) | `20` |
| `sort_by` | string | 排序字段 | `created_at` |
| `sort_order` | string | 排序方向 (asc/desc) | `desc` |

---

## 配置说明

### 端口配置

| 服务 | 默认端口 | 环境变量 |
|------|----------|----------|
| Backend API | 9000 | `BACKEND_PORT` |
| MongoDB | 27017 | `MONGO_PORT` |
| Mongo Express | 8081 | `MONGO_EXPR_PORT` |
| Redis | 6379 | `REDIS_PORT` |
| Casdoor | 8000 | `CASDOOR_PORT` |
| MinIO API | 9100 | `MINIO_API_PORT` |
| MinIO Console | 9101 | `MINIO_CONSOLE_PORT` |
| PostgreSQL | 5432 | `POSTGRES_PORT` |

### 环境变量

#### 应用配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENVIRONMENT` | `development` | 运行环境 |
| `BACKEND_PORT` | `9000` | 后端端口 |
| `CORS_ORIGINS` | - | 允许的跨域源 (逗号分隔) |

#### MongoDB

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MONGO_ROOT_USERNAME` | `admin` | MongoDB 管理员用户名 |
| `MONGO_ROOT_PASSWORD` | - | MongoDB 密码 |
| `MONGO_DATABASE` | `unified_backend` | 数据库名称 |
| `MONGO_PORT` | `27017` | 对外端口 |

#### Redis

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `REDIS_PASSWORD` | - | Redis 密码（可选） |
| `REDIS_PORT` | `6379` | 对外端口 |

#### Casdoor / JWT

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CASDOOR_ORIGIN` | `http://localhost:8000` | Casdoor 服务地址 |
| `JWT_SECRET` | - | JWT 签名密钥 (≥32 字符) |
| `JWT_ALGORITHM` | `HS256` | 加密算法 |

#### MinIO / S3

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MINIO_ROOT_USER` | `minioadmin` | MinIO 管理员用户名 |
| `MINIO_ROOT_PASSWORD` | - | MinIO 密码 |
| `MINIO_PUBLIC_URL` | `http://localhost:9100` | MinIO 公共访问 URL |
| `MINIO_BUCKET` | `unified-files` | 默认存储桶 |
| `MINIO_THUMBNAIL_BUCKET` | `unified-thumbnails` | 缩略图存储桶 |

---

## 开发指南

### 📚 文档导航

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| [5分钟快速接入指南](docs/QUICKSTART.md) | 快速接入指南，5分钟上手 | 前端/移动端开发者 |
| [开发者接入指南](docs/DEVELOPER_GUIDE.md) | 完整的接入文档，包含认证、数据、文件管理 | 前端/移动端开发者 |
| [API 参考手册](docs/API_REFERENCE.md) | 完整的 API 接口文档 | 所有开发者 |
| [部署文档](DEPLOYMENT.md) | 生产环境部署指南 | 运维/后端开发者 |
| [项目架构文档](CLAUDE.md) | 详细的项目架构和开发说明 | 后端开发者 |

### 前端/移动端开发者

如果你想将你的应用接入统一后端：

1. **5 分钟快速开始**: 阅读 [快速接入指南](docs/QUICKSTART.md)
2. **完整功能集成**: 参考 [开发者接入指南](docs/DEVELOPER_GUIDE.md)
3. **API 接口查询**: 查看 [API 参考手册](docs/API_REFERENCE.md)

### 后端开发者

如果你想参与后端开发：

#### 本地开发环境

#### 1. 安装依赖

```bash
cd backend

# 使用 pip
pip install -r requirements.txt

# 或使用 uv (推荐)
uv pip install -r requirements.txt
```

#### 2. 配置本地环境

```bash
# 复制环境变量
cp ../.env.example ../.env

# 确保 MONGODB_URL 指向本地或 Docker
# 本地 MongoDB: mongodb://localhost:27017/unified_backend
# Docker MongoDB: mongodb://admin:password@localhost:27017/unified_backend?authSource=admin
```

#### 3. 启动开发服务器

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 3002
```

### 项目结构

```
shared-database-service/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/      # API 路由
│   │   │       │   ├── auth.py     # 认证端点
│   │   │       │   ├── records.py  # 记录管理端点
│   │   │       │   └── files.py    # 文件管理端点
│   │   │       └── schemas/        # Pydantic 模型
│   │   ├── core/
│   │   │   ├── config.py           # 配置管理
│   │   │   └── security.py         # JWT 验证
│   │   ├── db/
│   │   │   └── mongodb.py          # 数据库连接
│   │   ├── models/
│   │   │   ├── user.py             # 用户模型
│   │   │   ├── unified_record.py   # 通用记录模型
│   │   │   └── file.py             # 文件模型
│   │   ├── services/
│   │   │   └── minio_service.py    # MinIO 服务
│   │   └── main.py                 # FastAPI 入口
│   ├── Dockerfile
│   └── requirements.txt
├── scripts/
│   ├── backup-mongodb.sh           # MongoDB 备份脚本
│   └── restore-mongodb.sh          # MongoDB 恢复脚本
├── mongodb-init/                   # MongoDB 初始化脚本
├── docker-compose.yml              # 容器编排配置
├── .env.example                    # 环境变量模板
├── README.md                       # 本文档
├── DEPLOYMENT.md                   # 部署指南
├── APP_DEVELOPMENT.md              # 应用开发指南
└── CLAUDE.md                       # AI 开发辅助指南
```

### 代码规范

#### 类型提示

```python
from typing import Any
from uuid import UUID

async def create_record(
    data: UnifiedRecordCreate,
    current_user: User = Depends(get_current_user),
) -> UnifiedRecord:
    ...
```

#### 异步操作

```python
# 使用 Motor (异步 MongoDB)
user = await User.find_one(User.email == email)

# 使用 Beanie (异步 ODM)
record = UnifiedRecord(...)
await record.insert()
```

#### 错误处理

```python
from fastapi import HTTPException, status

if not record:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Record not found",
    )
```

### 添加新的 API 端点

1. **创建 Schema** (`app/api/v1/schemas/xxx.py`):

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

2. **创建路由** (`app/api/v1/endpoints/xxx.py`):

```python
from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
from app.api.v1.schemas.xxx import ItemCreate, ItemResponse

router = APIRouter(prefix="/items", tags=["Items"])

@router.post("", response_model=ItemResponse)
async def create_item(
    data: ItemCreate,
    current_user: User = Depends(get_current_user),
) -> ItemResponse:
    return ItemResponse(id=uuid4(), **data.dict())
```

3. **注册路由** (`app/main.py`):

```python
from app.api.v1.endpoints import xxx

app.include_router(
    xxx.router,
    prefix=settings.api_prefix,
    tags=["XXX"],
)
```

### 测试

```bash
# 类型检查
mypy backend/app

# 代码格式化
black backend/app

# Lint
ruff check backend/app
```

---

## 部署指南

完整的部署指南请参考 [DEPLOYMENT.md](./DEPLOYMENT.md)，包含：

- 环境要求详解
- 生产环境配置
- 安全设置检查清单
- 性能优化建议
- 数据备份和恢复
- 故障排查指南
- Nginx 反向代理配置
- SSL/HTTPS 配置

### 快速备份命令

```bash
# MongoDB 备份
./scripts/backup-mongodb.sh

# MongoDB 恢复
./scripts/restore-mongodb.sh <backup-file>
```

---

## 开发进度

### ✅ 已完成功能 (100%)

#### 核心基础架构
- [x] FastAPI 后端框架搭建
- [x] MongoDB 数据库集成和认证
- [x] Beanie ODM 数据模型设计
- [x] Redis 缓存集成
- [x] Docker Compose 容器化部署
- [x] 环境变量标准化配置

#### 认证系统
- [x] Casdoor SSO 集成
- [x] JWT Token 验证
- [x] 用户自动同步机制
- [x] 基于角色的访问控制 (RBAC)
- [x] 用户权限管理

#### 数据管理
- [x] UnifiedRecord 灵活数据模型
- [x] 完整 CRUD API
- [x] 分页、排序、搜索功能
- [x] 软删除机制
- [x] 版本控制
- [x] 查看计数

#### 批量操作 ✨
- [x] 批量创建记录 API
- [x] 批量更新记录 API
- [x] 批量删除记录 API
- [x] 详细错误报告
- [x] 事务控制 (stop_on_error)

#### 文件管理 ✨
- [x] MinIO/S3 对象存储集成
- [x] 文件上传 API
- [x] 预签名 URL 上传
- [x] 文件元数据管理
- [x] 文件分类（图片、视频、PDF、音频等）
- [x] 公开/私有访问控制
- [x] 文件下载和删除

#### 开发者体验
- [x] Swagger API 文档
- [x] 环境变量模板 (.env.example)
- [x] MongoDB 管理界面 (Mongo Express)
- [x] MinIO 管理界面
- [x] 数据备份脚本
- [x] 完整项目文档

### 📊 功能测试状态

所有核心 API 已通过测试：

- ✅ 用户认证和授权
- ✅ 记录 CRUD 操作
- ✅ 批量操作（创建/更新/删除）
- ✅ 文件上传和管理
- ✅ 查询和搜索
- ✅ 软删除和版本控制

### 📚 可用文档

| 文档 | 说明 |
|------|------|
| `README.md` | 项目概述和快速开始 |
| `DEPLOYMENT.md` | 部署和运维指南 |
| `APP_DEVELOPMENT.md` | 应用开发教程 |
| `CLAUDE.md` | AI 辅助开发指南 |

### 🎯 待扩展功能 (可选)

以下功能可根据实际需求添加：

- [ ] WebSocket 实时推送
- [ ] 全文搜索 (Elasticsearch)
- [ ] 消息队列 (Celery/RabbitMQ)
- [ ] API 限流和防滥用
- [ ] 数据分析和统计
- [ ] Webhook 通知
- [ ] 多语言支持 (i18n)
- [ ] GraphQL API

---

## 常见问题

### Q: 如何基于这个后端开发应用？

A: 请参考 [APP_DEVELOPMENT.md](./APP_DEVELOPMENT.md)，其中包含：
- UnifiedRecord 模式详解
- 数据模型设计步骤
- 完整的 TypeScript/React 示例
- 实际应用场景（博客、论坛、电商）

### Q: 如何重置 Casdoor 管理员密码？

A: 访问 http://localhost:8000，首次访问会提示创建管理员账户。

### Q: MongoDB 数据存储在哪里？

A: 数据存储在 `./data/mongodb` 目录，通过 Docker Volume 持久化。

### Q: 如何添加新的应用？

A: 只需在创建 `UnifiedRecord` 时使用不同的 `app_identifier`，无需修改代码：

```python
UnifiedRecord(app_identifier="your-new-app", ...)
```

### Q: 如何登录 MinIO Console？

A: 访问 http://localhost:9101，使用凭据：
- 用户名: `minioadmin`
- 密码: 见 `.env` 中的 `MINIO_ROOT_PASSWORD`

### Q: 支持 HTTPS 吗？

A: 需要配置反向代理 (如 Nginx)，参考 [DEPLOYMENT.md](./DEPLOYMENT.md) 中的 SSL 配置。

### Q: 如何扩展存储容量？

A: 编辑 `docker-compose.yml`，为 MongoDB 和 MinIO 服务添加卷映射或使用外部存储。

---

## 许可证

MIT License

---

## 贡献

欢迎提交 Issue 和 Pull Request！

---

## 联系方式

- 项目地址: [GitHub Repository]
- 问题反馈: [Issues]

**最后更新**: 2024-12-23
