# Unified Backend Platform - 部署指南

> 生产环境部署和运维完整指南

## 目录

- [部署前准备](#部署前准备)
- [本地部署](#本地部署)
- [生产环境部署](#生产环境部署)
- [监控和日志](#监控和日志)
- [备份和恢复](#备份和恢复)
- [故障排查](#故障排查)
- [性能优化](#性能优化)

---

## 部署前准备

### 系统要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 20 GB | 50 GB+ (SSD) |
| 操作系统 | Linux/macOS | Ubuntu 22.04 LTS |
| Docker | 20.10+ | 24.0+ |
| Docker Compose | 2.0+ | 2.20+ |

### 网络端口

确保以下端口未被占用：

| 端口 | 服务 | 说明 |
|------|------|------|
| 3000 | Casdoor | SSO 管理界面 |
| 3001 | Mongo Express | 数据库管理界面 |
| 3002 | Backend | FastAPI 后端 |
| 27017 | MongoDB | 数据库 (建议不对外暴露) |
| 5432 | PostgreSQL | Casdoor 数据库 (建议不对外暴露) |
| 6379 | Redis | 缓存 (建议不对外暴露) |

### 安全检查清单

- [ ] 修改所有默认密码
- [ ] 设置强随机 JWT_SECRET (≥32 字符)
- [ ] 配置防火墙规则
- [ ] 限制数据库端口对外访问
- [ ] 配置 HTTPS (生产环境必须)
- [ ] 设置日志保留策略
- [ ] 配置自动备份

---

## 本地部署

### 快速启动 (开发环境)

```bash
# 1. 克隆项目
git clone <repository-url>
cd unified-backend-platform

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，修改必要配置

# 3. 启动所有服务
docker compose up -d

# 4. 验证部署
docker compose ps
curl http://localhost:3002/health
```

### 启动特定服务

```bash
# 仅启动基础设施 (数据库 + 缓存)
docker compose up -d mongo postgres redis

# 仅启动后端
docker compose up -d backend

# 查看日志
docker compose logs -f backend
```

### 停止服务

```bash
# 停止所有服务
docker compose down

# 停止并删除数据卷 (⚠️ 会删除所有数据)
docker compose down -v
```

---

## 生产环境部署

### 1. 环境变量配置

创建生产环境配置文件：

```bash
cp .env.example .env.production
nano .env.production
```

**生产环境关键配置**：

```bash
# =============================================================================
# 应用配置
# =============================================================================
ENVIRONMENT=production
BACKEND_PORT=3002
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# =============================================================================
# MongoDB 配置
# =============================================================================
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=CHANGE_ME_TO_STRONG_PASSWORD_32chars
MONGO_DATABASE=unified_backend
MONGO_PORT=27017

# Mongo Express (生产环境建议禁用或限制访问)
MONGO_EXPR_PORT=3001
MONGO_EXPR_USERNAME=admin
MONGO_EXPR_PASSWORD=CHANGE_ME_TO_STRONG_PASSWORD_32chars

# =============================================================================
# PostgreSQL 配置
# =============================================================================
POSTGRES_USER=casdoor
POSTGRES_PASSWORD=CHANGE_ME_TO_STRONG_PASSWORD_32chars
POSTGRES_DB=casdoor
POSTGRES_PORT=5432

# =============================================================================
# Redis 配置
# =============================================================================
REDIS_PASSWORD=CHANGE_ME_TO_STRONG_PASSWORD_32chars
REDIS_PORT=6379

# =============================================================================
# Casdoor 配置
# =============================================================================
CASDOOR_PORT=3000
CASDOOR_ORIGIN=https://casdoor.yourdomain.com

# =============================================================================
# JWT 配置
# =============================================================================
# ⚠️ 生产环境必须使用强随机密钥 (至少 32 字符)
JWT_SECRET=CHANGE_ME_TO_RANDOM_64_CHARACTER_STRING_FOR_PRODUCTION_SECURITY
JWT_ALGORITHM=HS256
```

### 2. 生成安全密钥

```bash
# 生成随机 JWT_SECRET
openssl rand -base64 64

# 生成随机密码
openssl rand -base64 32
```

### 4. 启动生产环境

```bash
# 使用生产配置启动
docker compose --env-file .env.production up -d

# 查看服务状态
docker compose --env-file .env.production ps

# 查看日志
docker compose --env-file .env.production logs -f
```

### 5. 配置防火墙

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# 限制数据库端口仅本地访问
sudo ufw deny 27017/tcp  # MongoDB
sudo ufw deny 5432/tcp   # PostgreSQL
sudo ufw deny 6379/tcp   # Redis
```

### 6. 配置系统服务 (可选)

创建 systemd 服务：

```ini
# /etc/systemd/system/unified-backend.service
[Unit]
Description=Unified Backend Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/unified-backend-platform
ExecStart=/usr/bin/docker compose --env-file .env.production up -d
ExecStop=/usr/bin/docker compose --env-file .env.production down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl enable unified-backend
sudo systemctl start unified-backend
sudo systemctl status unified-backend
```

---

## 监控和日志

### 健康检查

```bash
# 后端健康检查
curl http://localhost:3002/health

# 预期响应
{
  "status": "healthy",
  "app": "Unified Backend Platform",
  "version": "1.0.0",
  "environment": "production"
}
```

### 容器状态监控

```bash
# 实时查看容器状态
watch -n 2 'docker compose ps'

# 查看资源使用情况
docker stats

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f mongo
docker compose logs -f casdoor
```

### 日志管理

#### 配置日志轮转

创建 `/etc/logrotate.d/unified-backend`：

```
/opt/unified-backend-platform/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        docker compose restart backend > /dev/null
    endscript
}
```

#### 集中日志收集 (可选)

使用 ELK Stack 或 Loki：

```yaml
# 添加到 docker-compose.yml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yaml

  promtail:
    image: grafana/promtail:latest
    volumes:
      - ./promtail-config.yml:/etc/promtail/config.yml
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
```

---

## 备份和恢复

### MongoDB 备份

#### 自动备份脚本

创建 `scripts/backup-mongodb.sh`：

```bash
#!/bin/bash
# MongoDB 自动备份脚本

BACKUP_DIR="/opt/backups/mongodb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="mongodb_backup_${TIMESTAMP}"

# 从环境变量读取配置
source /opt/unified-backend-platform/.env.production

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 执行备份
docker compose exec -T mongo mongodump \
  --uri="mongodb://${MONGO_ROOT_USERNAME}:${MONGO_ROOT_PASSWORD}@localhost:27017/?authSource=admin" \
  --archive=/data/backup/${BACKUP_NAME}.tar

# 从容器复制出来
docker compose cp mongo:/data/backup/${BACKUP_NAME}.tar "${BACKUP_DIR}/"

# 压缩备份
gzip "${BACKUP_DIR}/${BACKUP_NAME}.tar"

# 删除 30 天前的备份
find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_NAME}.tar.gz"
```

#### 配置定时任务

```bash
# 编辑 crontab
crontab -e

# 每天凌晨 2 点执行备份
0 2 * * * /opt/unified-backend-platform/scripts/backup-mongodb.sh >> /var/log/mongodb-backup.log 2>&1
```

### MongoDB 恢复

```bash
#!/bin/bash
# MongoDB 恢复脚本

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup_file.tar.gz>"
  exit 1
fi

source /opt/unified-backend-platform/.env.production

# 解压备份
gunzip "${BACKUP_FILE}"

# 复制到容器
docker compose cp "${BACKUP_FILE%.gz}" mongo:/data/backup/restore.tar

# 执行恢复
docker compose exec mongo mongorestore \
  --uri="mongodb://${MONGO_ROOT_USERNAME}:${MONGO_ROOT_PASSWORD}@localhost:27017/?authSource=admin" \
  --archive=/data/backup/restore.tar

echo "Restore completed"
```

### PostgreSQL 备份 (Casdoor)

```bash
# 备份
docker compose exec postgres pg_dump \
  -U casdoor \
  -d casdoor \
  > backup_casdoor_$(date +%Y%m%d).sql

# 恢复
docker compose exec -T postgres psql \
  -U casdoor \
  -d casdoor \
  < backup_casdoor_20240101.sql
```

---

## 故障排查

### 常见问题

#### 1. 容器无法启动

```bash
# 查看详细日志
docker compose logs backend

# 检查容器状态
docker compose ps

# 检查网络连接
docker network inspect unified-network
```

#### 2. MongoDB 连接失败

```bash
# 检查 MongoDB 是否运行
docker compose exec mongo mongosh --eval "db.adminCommand('ping')"

# 检查认证
docker compose exec mongo mongosh \
  -u admin -p YOUR_PASSWORD \
  --authenticationDatabase admin \
  --eval "db.stats()"
```

#### 3. 内存不足

```bash
# 查看容器资源使用
docker stats

# 限制容器内存 (修改 docker-compose.yml)
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
```

#### 4. 磁盘空间不足

```bash
# 查看磁盘使用
df -h

# 清理 Docker 未使用的资源
docker system prune -a

# 清理 MongoDB 日志
docker compose exec mongo mongosh \
  --eval "db.runCommand({logRotate: 1})"
```

#### 5. Casdoor 登录失败

```bash
# 重置 Casdoor 管理员密码
docker compose exec postgres psql \
  -U casdoor -d casdoor \
  -c "UPDATE user SET password='$2a$10$...', salt='...' WHERE name='admin'"
```

### 日志级别调整

```python
# backend/app/core/config.py
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
```

---

## 性能优化

### MongoDB 优化

#### 1. 创建索引

```bash
docker compose exec mongo mongosh \
  -u admin -p PASSWORD --authenticationDatabase admin

# 在 unified_backend 数据库中创建索引
use unified_backend
db.unified_records.createIndex({ app_identifier: 1, collection_type: 1 })
db.unified_records.createIndex({ owner_id: 1, created_at: -1 })
db.users.createIndex({ email: 1 })
```

#### 2. 配置 WiredTiger

```yaml
# docker-compose.yml
services:
  mongo:
    command:
      - mongod
      - --wiredTigerCacheSizeGB=2
      - --wiredTigerCollectionBlockCompressor=snappy
```

### Redis 优化

```yaml
services:
  redis:
    command:
      - redis-server
      - --maxmemory=512mb
      - --maxmemory-policy=allkeys-lru
      - --save=900 1
      - --save=300 10
```

### 后端优化

```python
# backend/app/main.py

# 添加响应压缩
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 添加请求限流
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

### 数据库连接池

```python
# backend/app/db/mongodb.py

# 增加 MongoDB 连接池
motor.motor_asyncio.AsyncIOMotorClient(
    settings.mongodb_url,
    maxPoolSize=50,
    minPoolSize=10,
)
```

---

## 扩展部署

### 水平扩展后端

```yaml
# docker-compose.yml
services:
  backend:
    # ... 其他配置
    deploy:
      replicas: 3  # 运行 3 个实例
    environment:
      - INSTANCE_ID=@@INSTANCE_ID@@
```

### 使用 Nginx 负载均衡

```nginx
upstream backend {
    least_conn;
    server backend-1:3002;
    server backend-2:3002;
    server backend-3:3002;
}

server {
    location / {
        proxy_pass http://backend;
    }
}
```

### MongoDB 副本集 (高可用)

```yaml
# docker-compose.yml
services:
  mongo-primary:
    image: mongo:6
    command: mongod --replSet rs0

  mongo-secondary:
    image: mongo:6
    command: mongod --replSet rs0

  mongo-arbiter:
    image: mongo:6
    command: mongod --replSet rs0
```

初始化副本集：

```bash
docker compose exec mongo-primary mongosh --eval "
rs.initiate({
  _id: 'rs0',
  members: [
    {_id: 0, host: 'mongo-primary:27017'},
    {_id: 1, host: 'mongo-secondary:27017'},
    {_id: 2, host: 'mongo-arbiter:27017', arbiterOnly: true}
  ]
})
"
```

---

## 维护任务

### 定期维护清单

- [ ] 每周检查磁盘空间
- [ ] 每周审查访问日志
- [ ] 每月更新 Docker 镜像
- [ ] 每月审查用户权限
- [ ] 每月测试备份恢复
- [ ] 每季度审查安全策略
- [ ] 每季度性能测试

### 更新部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 备份数据
./scripts/backup-mongodb.sh

# 3. 重新构建镜像
docker compose build

# 4. 重启服务
docker compose --env-file .env.production up -d

# 5. 清理旧镜像
docker image prune -a
```

---

## 监控指标

### 关键指标

| 指标 | 阈值 | 说明 |
|------|------|------|
| CPU 使用率 | < 80% | 容器平均 CPU |
| 内存使用率 | < 85% | 容器平均内存 |
| 磁盘使用率 | < 80% | 数据卷使用率 |
| API 响应时间 | < 500ms | P95 响应时间 |
| 错误率 | < 1% | HTTP 5xx 比率 |
| MongoDB 连接数 | < 80% | 最大连接数的 80% |

### Prometheus 监控 (可选)

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3003:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=changeme
```

---

## 安全加固

### 1. 限制容器权限

```yaml
# docker-compose.yml
services:
  backend:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
```

### 2. 扫描漏洞

```bash
# 使用 Trivy 扫描镜像
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image unified-backend-backend:latest
```

### 3. 配置 SELinux (CentOS/RHEL)

```bash
# 设置 SELinux 为 enforcing
sudo setenforce 1

# 允许 Docker 访问挂载目录
sudo chcon -Rt svirt_sandbox_file_t /opt/unified-backend-platform
```

---

## 应急预案

### 数据恢复流程

1. **停止应用服务**
   ```bash
   docker compose stop backend
   ```

2. **评估损坏程度**
   ```bash
   docker compose exec mongo mongosh --eval "db.stats()"
   ```

3. **从最新备份恢复**
   ```bash
   ./scripts/restore-mongodb.sh /opt/backups/mongodb/latest.tar.gz
   ```

4. **验证数据完整性**
   ```bash
   curl http://localhost:3002/api/v1/records
   ```

5. **重启服务**
   ```bash
   docker compose start backend
   ```

### 回滚部署

```bash
# 1. 切换到上一个稳定版本
git checkout <previous-stable-tag>

# 2. 重新构建
docker compose build

# 3. 重启
docker compose --env-file .env.production up -d
```

---

## 联系支持

- 问题反馈: [GitHub Issues]
- 技术讨论: [Discussions]
- 紧急联系: support@example.com
