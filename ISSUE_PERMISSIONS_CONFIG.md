# Bug Report: User Permissions Not Loaded - Casdoor API Connection Failed

## 🐛 Bug 描述

**影响范围**: 所有需要认证的用户，特别是管理员账户
**严重程度**: 🔴 Critical - 阻止用户执行需要权限的操作（创建/更新/删除）

用户通过 Casdoor 登录后，后端无法从 Casdoor API 获取用户的权限组信息，导致：
- 用户成功同步到数据库，但没有分配任何角色
- `permissions: []` 和 `roles: []` 为空
- 管理员账户无法执行管理操作
- 所有需要权限检查的 API 请求可能失败

## 📍 错误位置

**配置文件**: `/home/gaooooosh/shared-database-service/.env`
**具体行数**: 第 73 行
**相关文件**:
- `/home/gaooooosh/shared-database-service/docker-compose.yml` - 服务配置
- `/home/gaooooosh/shared-database-service/backend/app/services/casdoor_sync_service.py` - Casdoor 同步服务

## 🔍 复现步骤

### 1. 启动后端服务
```bash
cd /home/gaooooosh/shared-database-service
docker compose up -d
```

### 2. 使用 Casdoor 登录
访问前端应用，通过 Casdoor OAuth 登录

### 3. 检查后端日志
```bash
docker logs unified-backend -f
```

### 4. 观察错误信息

**预期结果**:
```
✅ User synced from Casdoor: username | Roles: ["admin", "editor"]
```

**实际结果**:
```
❌ Casdoor API HTTP error: All connection attempts failed
✅ User synced from Casdoor: yonggaoxiao | Roles: []
Redis cache invalidation error: AUTH <password> called without any password configured for the default user.
```

### 5. 调用 /auth/me API 验证权限
```bash
curl -X GET "https://uni.aiyueaijia.com/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**返回结果**:
```json
{
  "id": "...",
  "email": "user@example.com",
  "display_name": "用户名",
  "is_superuser": false,
  "permissions": [],
  "roles": []
}
```

## 📊 错误日志

### 后端日志 (docker logs unified-backend)
```
❌ Casdoor API HTTP error: All connection attempts failed
✅ User synced from Casdoor: yonggaoxiao | Roles: []
Redis cache invalidation error: AUTH <password> called without any password configured for the default user.
✅ User synced from Casdoor: yonggaoxiao | Roles: []
Redis cache error: AUTH <password> called without any password configured for the default user.
INFO:     172.20.0.1:48532 - "GET /api/v1/records/bd4027fd-4eab-4c62-aff8-281da756414c HTTP/1.1" 200 OK
INFO:     172.20.0.1:48526 - "GET /api/v1/records?app_identifier=choir-app&collection_type=arrangement&search=bd4027fd-4eab-4c62-aff8-281da756414c&page_size=100 HTTP/1.1" 200 OK
Redis cache save error: AUTH <password> called without any password configured for the default user.
INFO:     172.20.0.1:48536 - "GET /api/v1/auth/me HTTP/1.1" 200 OK
❌ Casdoor API HTTP error: All connection attempts failed
Redis cache invalidation error: AUTH <password> called without any password configured for the default user.
✅ User synced from Casdoor: yonggaoxiao | Roles: []
INFO:     172.20.0.1:48536 - "POST /api/v1/records HTTP/1.1" 201 Created
```

**关键错误**:
1. `❌ Casdoor API HTTP error: All connection attempts failed` - 无法连接 Casdoor API
2. `Roles: []` - 用户没有分配任何角色
3. Redis 密码配置错误

## 🔧 根本原因

### 问题 1: Casdoor Origin 配置错误

**错误配置** (`.env` 第 73 行):
```bash
CASDOOR_ORIGIN=http://localhost:8000
```

**问题分析**:
1. 在 Docker 容器网络内部，`localhost` 指向容器自己，而不是 Casdoor 容器
2. 后端服务无法通过 `localhost:8000` 访问 Casdoor API
3. 正确的服务名应该是 `casdoor` 或 `unified-casdoor`（取决于 docker-compose.yml 中的配置）

**Docker Compose 服务配置** (`docker-compose.yml`):
```yaml
casdoor:
  image: casbin/casdoor:latest
  container_name: unified-casdoor
  restart: unless-stopped
  # ... 其他配置
```

**后端环境变量** (`docker-compose.yml`):
```yaml
backend:
  environment:
    CASDOOR_ORIGIN: ${CASDOOR_ORIGIN:-http://localhost:8000}  # ❌ 错误
```

### 问题 2: Casdoor 同步服务连接失败

**文件**: `backend/app/services/casdoor_sync_service.py`

**第 28 行**:
```python
self.casdoor_api_base = f"{settings.casdoor_origin}/api"
```

**第 52-64 行** - 获取用户权限组:
```python
async with httpx.AsyncClient(timeout=self.timeout) as client:
    response = await client.get(
        f"{self.casdoor_api_base}/get-user",
        params={
            "id": casdoor_user_id,
            "owner": settings.casdoor_organization,
            "client_id": settings.casdoor_client_id,
            "client_secret": settings.casdoor_client_secret,
        },
    )
```

当 `casdoor_origin` 配置为 `http://localhost:8000` 时：
- 后端容器尝试连接 `http://localhost:8000/api/get-user`
- 实际上后端容器自己没有运行在 8000 端口
- 连接失败，返回 `All connection attempts failed`

### 问题 3: Redis 密码配置不一致

**Docker Compose Redis 配置**:
```yaml
redis:
  image: redis:7-alpine
  container_name: unified-redis
  restart: unless-stopped
  # 暂时禁用密码（Casdoor 对 Redis URL 密码格式支持有问题）
  command: redis-server --appendonly no
```

**环境变量** (`.env`):
```bash
REDIS_PASSWORD=a36806e9eb8c4774f93a85cd2c26a7648e55b5de85706067
```

**后端连接 URL** (`docker-compose.yml`):
```yaml
REDIS_URL: redis://:${REDIS_PASSWORD:-}@redis:6379/0
```

**问题**:
1. Redis 服务没有设置密码（`redis-server --appendonly no`）
2. 但后端尝试用密码连接（`redis://:PASSWORD@redis:6379/0`）
3. 导致 `AUTH called without any password configured` 错误
4. Redis 缓存功能失败，但不会阻塞用户登录

## ✅ 修复建议

### 方案 1: 修正 CASDOOR_ORIGIN 配置（推荐）

**修改文件**: `.env`

**第 73 行**:
```bash
# 修改前
CASDOOR_ORIGIN=http://localhost:8000

# 修改后（使用 Docker 服务名）
CASDOOR_ORIGIN=http://casdoor:8000
```

**验证步骤**:
1. 修改 `.env` 文件
2. 重启后端服务: `docker compose restart backend`
3. 重新登录
4. 查看日志，应该看到 `✅ User synced from Casdoor: username | Roles: ["admin"]`

### 方案 2: 修改 docker-compose.yml 默认值（备选）

**修改文件**: `docker-compose.yml`

**找到后端服务配置**:
```yaml
backend:
  environment:
    CASDOOR_ORIGIN: ${CASDOOR_ORIGIN:-http://casdoor:8000}  # 修改默认值
```

**优点**: 即使 `.env` 文件中没有配置，也会使用正确的默认值

### 方案 3: 修复 Redis 密码配置

**选项 A: 禁用 Redis 密码**（快速修复）

**修改文件**: `docker-compose.yml`

```yaml
backend:
  environment:
    # 不使用密码连接 Redis
    REDIS_URL: redis://redis:6379/0
```

**选项 B: 为 Redis 启用密码**（更安全）

**修改文件**: `docker-compose.yml`

```yaml
redis:
  image: redis:7-alpine
  container_name: unified-redis
  restart: unless-stopped
  # 启用密码认证
  command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly no
```

### 方案 4: 手动为用户分配管理员角色（临时方案）

如果 Casdoor API 连接问题暂时无法解决，可以通过以下方式手动设置用户权限：

**方式 1: 直接修改数据库**
```javascript
// 连接到 MongoDB
use unified_backend;

// 查找用户
db.users.findOne({ email: "yonggaoxiao@xxx.com" });

// 设置为超级管理员
db.users.updateOne(
  { email: "yonggaoxiao@xxx.com" },
  { $set: { is_superuser: true } }
);
```

**方式 2: 使用 Python 脚本**
```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def make_user_superuser():
    client = AsyncIOMotorClient("mongodb://username:password@localhost:27017")
    db = client.unified_backend

    result = await db.users.update_one(
        {"email": "user@example.com"},
        {"$set": {"is_superuser": True}}
    )

    print(f"Updated {result.modified_count} user(s)")
    client.close()

asyncio.run(make_user_superuser())
```

## 🎯 推荐修复优先级

**立即修复（Critical）**:
1. ✅ **修改 `CASDOOR_ORIGIN` 配置** - 从 `http://localhost:8000` 改为 `http://casdoor:8000`

**高优先级（High）**:
2. **修复 Redis 密码配置** - 要么禁用密码，要么为 Redis 启用密码

**中优先级（Medium）**:
3. **添加健康检查** - 检测 Casdoor API 连接状态
4. **添加降级策略** - 当 Casdoor API 不可用时，使用默认角色

**低优先级（Low）**:
5. **改进日志** - 区分"无法连接 Casdoor"和"用户没有权限组"
6. **添加监控** - 监控权限同步成功率

## 📝 环境信息

- **后端框架**: FastAPI
- **部署方式**: Docker Compose
- **Casdoor 版本**: casbin/casdoor:latest
- **Redis 版本**: 7-alpine
- **当前配置**: `.env` 中 `CASDOOR_ORIGIN=http://localhost:8000`
- **Docker 服务名**: `casdoor` (容器名: `unified-casdoor`)

## 🧪 测试验证

修复后，使用以下命令测试：

### 1. 重启后端服务
```bash
cd /home/gaooooosh/shared-database-service
docker compose restart backend
```

### 2. 清除 Redis 缓存（强制重新获取权限）
```bash
docker exec unified-redis redis-cli FLUSHALL
```

### 3. 重新登录
1. 打开前端应用
2. 退出登录
3. 重新登录

### 4. 检查后端日志
```bash
docker logs unified-backend --tail 50
```

**预期输出**:
```
✅ User synced from Casdoor: username | Roles: ["admin"]
```

**不应该看到**:
```
❌ Casdoor API HTTP error: All connection attempts failed
```

### 5. 验证用户权限
```bash
# 获取 JWT token
TOKEN="your_jwt_token_here"

# 调用 /auth/me API
curl -X GET "https://uni.aiyueaijia.com/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**预期返回**:
```json
{
  "id": "...",
  "email": "user@example.com",
  "display_name": "管理员",
  "is_superuser": true,
  "permissions": ["*:*"]  // 或具体权限列表
  "roles": ["admin"]
}
```

### 6. 测试创建操作
```bash
curl -X POST "https://uni.aiyueaijia.com/api/v1/records" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "app_identifier": "choir-app",
    "collection_type": "song",
    "title": "测试权限",
    "payload": {"title": "测试权限"}
  }'
```

**预期结果**: `201 Created`

## 🔗 相关文件

- `/home/gaooooosh/shared-database-service/.env` - 环境变量配置（第 73 行）
- `/home/gaooooosh/shared-database-service/docker-compose.yml` - Docker 编排配置
- `/home/gaooooosh/shared-database-service/backend/app/services/casdoor_sync_service.py` - Casdoor 同步服务
- `/home/gaooooosh/shared-database-service/backend/app/core/security.py` - 用户同步逻辑
- `/home/gaooooosh/shared-database-service/backend/app/core/config.py` - 配置读取

## 📞 联系方式

如有问题，请联系：
- **前端团队**: 确认权限问题已解决
- **DevOps 团队**: 协助修改 Docker 配置

---

**创建时间**: 2025-12-26
**优先级**: 🔴 Critical - 阻塞所有权限相关功能
**影响范围**: 所有需要认证的用户
**状态**: ⏳ 等待修复

## 附录: 快速修复命令

如需紧急修复，可以直接执行：

```bash
# 1. 备份配置
cp /home/gaooooosh/shared-database-service/.env /home/gaooooosh/shared-database-service/.env.backup

# 2. 修改配置
sed -i 's/CASDOOR_ORIGIN=http:\/\/localhost:8000/CASDOOR_ORIGIN=http:\/\/casdoor:8000/' /home/gaooooosh/shared-database-service/.env

# 3. 重启后端
cd /home/gaooooosh/shared-database-service
docker compose restart backend

# 4. 查看日志验证
docker logs unified-backend --tail 20
```

**回滚命令**（如果修复失败）:
```bash
# 恢复备份
cp /home/gaooooosh/shared-database-service/.env.backup /home/gaooooosh/shared-database-service/.env

# 重启后端
docker compose restart backend
```
