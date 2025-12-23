# Unified Backend Platform - 部署文档

本文档提供完整的部署指南，包括开发环境、生产环境配置。

---

## 📋 目录

- [快速开始](#快速开始)
- [环境要求](#环境要求)
- [配置说明](#配置说明)
- [部署步骤](#部署步骤)
- [服务访问](#服务访问)
- [数据备份](#数据备份)
- [生产环境配置](#生产环境配置)
- [故障排查](#故障排查)

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd shared-database-service
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，修改敏感配置
vim .env  # 或使用其他编辑器
```

**必须修改的配置**：
- `MONGO_ROOT_PASSWORD` - MongoDB root 密码
- `JWT_SECRET` - JWT 签名密钥（至少 32 字符）
- `MINIO_ROOT_PASSWORD` - MinIO 管理员密码
- `MONGO_EXPR_PASSWORD` - Mongo Express 密码

### 3. 启动服务

```bash
# 构建并启动所有服务
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
# 浏览器打开: http://localhost:9000/api/v1/docs
```

---

## 💻 环境要求

### 必需软件

| 软件 | 版本要求 | 用途 |
|------|----------|------|
| Docker | ≥ 20.10 | 容器运行 |
| Docker Compose | ≥ 2.0 | 服务编排 |

### 可选软件

| 软件 | 用途 |
|------|------|
| Git | 版本控制 |
| Python 3.11+ | 本地开发 |

### 系统要求

- **CPU**: 2 核心以上
- **内存**: 4GB 以上
- **磁盘**: 20GB 以上可用空间

---

## ⚙️ 配置说明

### 端口配置

| 服务 | 默认端口 | 环境变量 | 说明 |
|------|----------|----------|------|
| Backend API | 9000 | `BACKEND_PORT` | FastAPI 服务 |
| MongoDB | 27017 | `MONGO_PORT` | 业务数据库 |
| Mongo Express | 8081 | `MONGO_EXPR_PORT` | 数据库管理界面 |
| Redis | 6379 | `REDIS_PORT` | 缓存服务 |
| Casdoor | 8000 | `CASDOOR_PORT` | SSO 认证 |
| MinIO API | 9100 | `MINIO_API_PORT` | 对象存储 API |
| MinIO Console | 9101 | `MINIO_CONSOLE_PORT` | 存储管理界面 |
| PostgreSQL | 5432 | `POSTGRES_PORT` | Casdoor 数据库 |

### 数据持久化

数据存储在 `./data/` 目录下：

```
data/
├── mongodb/         # MongoDB 数据
├── postgres/        # PostgreSQL 数据
├── redis/           # Redis 持久化
└── minio/           # MinIO 对象存储
```

### 安全配置

#### 生成安全密码

```bash
# 方法 1: 使用 OpenSSL
openssl rand -base64 32

# 方法 2: 使用 Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 密码配置

在 `.env` 文件中修改：

```bash
# MongoDB
MONGO_ROOT_PASSWORD=<生成的安全密码>
MONGO_EXPR_PASSWORD=<生成的安全密码>

# PostgreSQL
POSTGRES_PASSWORD=<生成的安全密码>

# MinIO
MINIO_ROOT_PASSWORD=<生成的安全密码>

# JWT (至少 32 字符)
JWT_SECRET=<生成的安全密钥>
```

---

## 📦 部署步骤

### 开发环境部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 2. 启动服务
docker compose up -d

# 3. 等待服务就绪 (约 30 秒)
sleep 30

# 4. 验证服务
curl http://localhost:9000/health
```

### 生产环境部署

#### 1. 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. 配置防火墙

```bash
# 允许必要端口
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 9000/tcp  # Backend API
sudo ufw allow 8000/tcp  # Casdoor (可选)

# 启用防火墙
sudo ufw enable
```

#### 3. 配置反向代理 (Nginx)

创建 `/etc/nginx/sites-available/unified-backend`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Backend API
    location /api/ {
        proxy_pass http://localhost:9000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Casdoor
    location /casdoor/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # MinIO (可选)
    location /minio/ {
        proxy_pass http://localhost:9100/;
        proxy_set_header Host $host;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/unified-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 4. 配置 SSL (Let's Encrypt)

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

#### 5. 启动服务

```bash
# 使用生产配置启动
docker compose up -d

# 检查服务状态
docker compose ps
docker compose logs -f
```

---

## 🌐 服务访问

### 开发环境

| 服务 | URL | 说明 |
|------|-----|------|
| Backend API | http://localhost:9000 | API 服务 |
| API 文档 | http://localhost:9000/api/v1/docs | Swagger UI |
| Mongo Express | http://localhost:8081 | 数据库管理 |
| MinIO Console | http://localhost:9101 | 对象存储管理 |
| Casdoor | http://localhost:8000 | SSO 管理 |

### 默认登录凭据

**Mongo Express**
- 用户名: `admin`
- 密码: 见 `.env` 中的 `MONGO_EXPR_PASSWORD`

**MinIO Console**
- 用户名: `minioadmin`
- 密码: 见 `.env` 中的 `MINIO_ROOT_PASSWORD`

**Casdoor**
- 首次访问需要创建管理员账户

---

## 💾 数据备份

### MongoDB 备份

```bash
# 备份
./scripts/backup-mongodb.sh

# 恢复
./scripts/restore-mongodb.sh <backup-file>
```

### 手动备份

```bash
# MongoDB
docker exec unified-mongo mongodump --username=admin --password=<password> --archive=/data/backup-$(date +%Y%m%d).tar

# MinIO
docker exec unified-minio mc mirror minio/unified-files /backup/minio-$(date +%Y%m%d)/

# PostgreSQL (Casdoor)
docker exec unified-postgres pg_dump -U casdoor casdoor > casdoor-backup-$(date +%Y%m%d).sql
```

### 自动备份脚本

创建 cron 任务：

```bash
# 编辑 crontab
crontab -e

# 每天凌晨 2 点备份
0 2 * * * cd /path/to/shared-database-service && ./scripts/backup-mongodb.sh
```

---

## 🔒 生产环境配置

### 安全检查清单

- [ ] 修改所有默认密码
- [ ] 使用强随机 JWT_SECRET
- [ ] 配置 HTTPS/SSL
- [ ] 限制 CORS_ORIGINS
- [ ] 启用 Redis 密码
- [ ] 配置防火墙
- [ ] 设置日志轮转
- [ ] 配置监控告警
- [ ] 定期备份数据
- [ ] 使用专用的数据库用户

### 性能优化

```bash
# 1. 增加 MongoDB 内存限制
# 在 docker-compose.yml 中添加：
# mongo:
#   deploy:
#     resources:
#       limits:
#         memory: 2G

# 2. 启用 Redis 持久化
# 已在配置中启用: --appendonly yes

# 3. 配置日志轮转
# 在 docker-compose.yml 中添加：
# backend:
#   logging:
#     driver: "json-file"
#     options:
#       max-size: "10m"
#       max-file: "3"
```

---

## 🔍 故障排查

### 常见问题

#### 1. 服务无法启动

```bash
# 查看日志
docker compose logs <service-name>

# 检查端口占用
sudo netstat -tlnp | grep <port>

# 重启服务
docker compose restart <service-name>
```

#### 2. MongoDB 认证失败

```bash
# 重置 MongoDB
docker compose down -v
docker compose up -d
```

#### 3. MinIO 连接失败

```bash
# 检查 MinIO 健康状态
curl http://localhost:9100/minio/health/live

# 重新初始化存储桶
docker compose up -d --force-recreate minio-init
```

#### 4. 数据库连接失败

```bash
# 检查网络
docker network ls
docker network inspect shared-database-service_unified-network

# 检查容器状态
docker compose ps
```

### 日志查看

```bash
# 查看所有服务日志
docker compose logs

# 查看特定服务日志
docker compose logs -f backend

# 查看最近 100 行日志
docker compose logs --tail 100 backend
```

### 健康检查

```bash
# Backend 健康检查
curl http://localhost:9000/health

# MongoDB 健康检查
docker exec unified-mongo mongosh --eval "db.adminCommand('ping')"

# Redis 健康检查
docker exec unified-redis redis-cli ping

# MinIO 健康检查
curl http://localhost:9100/minio/health/live
```

---

## 📞 支持

如有问题，请：

1. 检查本文档的 [故障排查](#故障排查) 部分
2. 查看服务日志
3. 访问 API 文档: http://localhost:9000/api/v1/docs
4. 提交 Issue 到项目仓库

---

## 📚 相关文档

- [CLAUDE.md](./CLAUDE.md) - 项目开发指南
- [README.md](./README.md) - 项目概述
- [API 文档](http://localhost:9000/api/v1/docs) - Swagger UI

---

**最后更新**: 2024-12-23
