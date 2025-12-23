# Unified Backend Platform - 故障排除指南

> 常见问题和解决方案

## 目录

- [部署问题](#部署问题)
- [依赖问题](#依赖问题)
- [配置问题](#配置问题)
- [数据库问题](#数据库问题)
- [API 问题](#api-问题)
- [调试技巧](#调试技巧)

---

## 部署问题

### 问题: 端口已被占用

**错误信息**:
```
Error: Bind for 0.0.0.0:PORT failed: port is already allocated
```

**原因**: 端口被其他服务占用

**解决方案**:

1. 查看端口占用:
```bash
ss -tlnp | grep PORT
# 或
lsof -i :PORT
```

2. 停止占用端口的进程:
```bash
# 如果是 Docker 容器
docker stop CONTAINER_NAME
docker rm CONTAINER_NAME

# 如果是系统进程
kill -9 PID
```

3. 修改 `.env` 使用不同端口:
```bash
# .env
BACKEND_PORT=9000      # 改为其他端口
CASDOOR_PORT=8000
MONGO_EXPR_PORT=8081
```

4. 重启服务:
```bash
docker compose down
docker compose up -d
```

---

### 问题: Docker 构建失败

**错误信息**:
```
ERROR [builder] failed to solve...
```

**解决方案**:

1. 清理 Docker 缓存:
```bash
docker system prune -a
docker compose build --no-cache
```

2. 检查 Docker 磁盘空间:
```bash
docker system df
docker system prune
```

3. 查看详细日志:
```bash
docker compose build --progress=plain
```

---

### 问题: 容器持续重启

**错误信息**:
```
Container xxx Restarting (1) Less than a second ago
```

**解决方案**:

1. 查看容器日志:
```bash
docker compose logs SERVICE_NAME
docker compose logs SERVICE_NAME --tail 100
```

2. 进入容器检查:
```bash
docker compose exec SERVICE_NAME bash
# 或
docker run -it IMAGE_NAME bash
```

3. 检查健康状态:
```bash
docker inspect --format='{{.State.Health.Status}}' CONTAINER_NAME
```

---

## 依赖问题

### 问题: pip 依赖冲突

**错误信息**:
```
ERROR: Cannot install X and Y because these package versions have conflicting dependencies
```

**解决方案**:

1. 查看依赖树:
```bash
pip install pipdeptree
pipdeptree
```

2. 使用兼容版本:
```bash
# 检查包要求
pip show PACKAGE_NAME | grep Requires
```

3. 更新 `requirements.txt`:
```txt
# 修复后的版本
pymongo==4.9.2  # motor 3.6.0 要求 pymongo<4.10
motor==3.6.0
```

4. 清理并重新安装:
```bash
pip cache purge
pip install -r requirements.txt --force-reinstall
```

---

### 问题: Pydantic v2 迁移错误

**错误信息**:
```
PydanticUserError: `regex` is removed. use `pattern` instead
```

**解决方案**:

| v1 (旧) | v2 (新) |
|---------|---------|
| `regex="..."` | `pattern="..."` |
| `@validator` | `@field_validator` |
| `Config` | `model_config` |
| `Schema` | 不再需要 |

**修复示例**:
```python
# 旧代码
class Query(BaseModel):
    sort_order: str = Field("desc", regex="^(asc|desc)$")

# 新代码
class Query(BaseModel):
    sort_order: str = Field("desc", pattern="^(asc|desc)$")
```

---

### 问题: CORS 配置错误

**错误信息**:
```
ValidationError: cors_origins - Input should be a valid string
```

**解决方案**:

1. 修改 `config.py`:
```python
# 错误写法
cors_origins: List[str] = Field(...)

# 正确写法
cors_origins: str = Field(default="http://localhost:3000,http://localhost:9000")

@property
def cors_origins_list(self) -> List[str]:
    return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
```

2. 修改 `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # 使用列表属性
    ...
)
```

---

## 配置问题

### 问题: JWT Secret 长度不足

**错误信息**:
```
ValidationError: jwt_secret - Input should be at least 32 characters
```

**解决方案**:

生成安全密钥:
```bash
# 生成 64 字符随机密钥
openssl rand -base64 64
# 或
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

更新 `.env`:
```bash
JWT_SECRET=<生成的64字符密钥>
```

---

### 问题: MongoDB 连接失败

**错误信息**:
```
pymongo.errors.ServerSelectionTimeoutError: No servers found
```

**解决方案**:

1. 检查 MongoDB 是否运行:
```bash
docker compose ps mongo
docker compose logs mongo --tail 50
```

2. 检查网络连接:
```bash
docker network ls
docker network inspect shared-database-service_unified-network
```

3. 验证连接字符串:
```bash
# 格式
mongodb://USERNAME:PASSWORD@HOST:27017/DATABASE?authSource=admin

# 示例
mongodb://admin:admin123@mongo:27017/unified_backend?authSource=admin
```

4. 测试连接:
```bash
docker compose exec mongo mongosh \
  -u admin -p PASSWORD \
  --authenticationDatabase admin \
  --eval "db.stats()"
```

---

### 问题: 环境变量未生效

**症状**: 修改 `.env` 后服务仍使用旧配置

**解决方案**:

1. 完全重启服务:
```bash
docker compose down
docker compose up -d
```

2. 检查环境变量是否传递:
```bash
docker compose exec backend env | grep VAR_NAME
```

3. 验证配置格式:
```bash
# 正确格式
KEY=value
KEY2=value2

# 错误格式
KEY = value  # 不要有空格
KEY 'value'   # 不要用引号
```

---

## 数据库问题

### 问题: Beanie 初始化失败

**错误信息**:
```
AttributeError: 'Document' object has no attribute 'find'
```

**解决方案**:

1. 确保 Beanie 正确初始化:
```python
# db/mongodb.py
from beanie import init_beanie
from app.models.user import User
from app.models.unified_record import UnifiedRecord

await init_beanie(
    database=client.get_database(settings.mongodb_database),
    document_models=[User, UnifiedRecord],  # 必须传入模型列表
)
```

2. 检查模型继承:
```python
from beanie import Document  # 不是 Pydantic BaseModel

class User(Document):
    ...
```

---

### 问题: UUID 类型错误

**错误信息**:
```
ValidationError: value is not a valid UUID
```

**解决方案**:

1. 确保使用正确的 UUID 类型:
```python
from uuid import UUID
from beanie import PydanticObjectId

# 查询时使用
record = await UnifiedRecord.find_one(
    UnifiedRecord.id == UUID(record_id)  # 转换为 UUID
)

# 或使用字符串
record_id = str(uuid_obj)
```

2. 路由参数处理:
```python
@router.get("/records/{record_id}")
async def get_record(record_id: str):  # 接收字符串
    # 内部转换为 UUID
    record = await UnifiedRecord.get(UUID(record_id))
```

---

### 问题: 软删除查询仍然返回已删除数据

**症状**: 查询结果中包含 `is_deleted: true` 的记录

**解决方案**:

1. 确保查询中包含软删除过滤:
```python
# 正确
query_filters = [UnifiedRecord.is_deleted == False]
records = await UnifiedRecord.find_many(*query_filters).to_list()

# 错误
records = await UnifiedRecord.find_all().to_list()
```

2. 或使用默认查询:
```python
class UnifiedRecord(Document):
    class Settings:
        name = "unified_records"
        # 添加默认过滤器
        use_state_management = True
```

---

## API 问题

### 问题: CORS 错误

**症状**: 浏览器控制台显示 CORS 错误

**解决方案**:

1. 检查请求来源是否在允许列表:
```python
# .env
CORS_ORIGINS=http://localhost:3000,http://localhost:9000
```

2. 验证 CORS 中间件顺序:
```python
# main.py - CORSMiddleware 必须在路由之前
app.add_middleware(CORSMiddleware, ...)
app.include_router(...)  # 在中间件之后
```

3. 测试 CORS:
```bash
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS http://localhost:9000/api/v1/records \
  -v
```

---

### 问题: 401 Unauthorized

**症状**: API 返回 401 错误

**解决方案**:

1. 验证 Token 格式:
```bash
# 正确
Authorization: Bearer eyJhbGci...

# 错误
Authorization: eyJhbGci...  # 缺少 "Bearer "
authorization: Bearer...    # 小写不起作用
```

2. 检查 JWT Secret 一致:
```bash
# .env 中的 JWT_SECRET 必须与签发 Token 时的密钥一致
JWT_SECRET=your-super-secret-jwt-key...
```

3. 验证 Token 有效期:
```python
import jwt

token = "your-token"
payload = jwt.decode(token, options={"verify_signature": False})
print(payload.get("exp"))  # 检查过期时间
```

---

### 问题: 403 Forbidden

**症状**: 用户有权限但返回 403

**解决方案**:

1. 检查用户角色:
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:9000/api/v1/auth/me | jq .role
```

2. 验证资源所有权:
```python
# records.py
if record.owner_id != current_user.id and current_user.role != "admin":
    raise HTTPException(status_code=403)
```

3. 检查权限检查器:
```python
# 确保使用正确的依赖
require_admin = RoleChecker(["admin"])

@app.delete("/records/{id}")
async def delete_record(
    user: User = Depends(require_admin)  # 管理员权限
):
    ...
```

---

## 调试技巧

### 查看 Docker 日志

```bash
# 所有服务日志
docker compose logs -f

# 特定服务
docker compose logs -f backend

# 最近 100 行
docker compose logs --tail 100 backend

# 带时间戳
docker compose logs -t backend
```

### 进入容器调试

```bash
# 进入运行中的容器
docker compose exec backend bash
docker compose exec mongo mongosh

# 临时运行命令
docker compose run --rm backend python -m pytest
```

### Python 调试

1. 使用 pdb:
```python
import pdb; pdb.set_trace()

# 或在代码中
breakpoint()
```

2. 打印调试:
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Variable value: {variable}")
```

3. FastAPI 调试模式:
```bash
uvicorn app.main:app --reload --log-level debug
```

### MongoDB 调试

```bash
# 进入 MongoDB Shell
docker compose exec mongo mongosh \
  -u admin -p PASSWORD \
  --authenticationDatabase admin

# 列出数据库
show dbs

# 切换数据库
use unified_backend

# 列出集合
show collections

# 查询数据
db.users.find().pretty()
db.unified_records.find().pretty()

# 统计
db.unified_records.countDocuments({app_identifier: "test-app"})
```

### API 测试

```bash
# 使用 curl 测试
curl -v http://localhost:9000/health

# 使用 jq 格式化输出
curl -s http://localhost:9000/api/v1/records | jq

# 测试 POST 请求
curl -X POST http://localhost:9000/api/v1/records \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}' | jq
```

### 性能分析

```bash
# Docker 资源使用
docker stats

# 容器内部进程
docker compose exec backend top

# MongoDB 性能
docker compose exec mongo mongosh \
  --eval "db.currentOp({ns: 'unified_backend.unified_records'})"
```

---

## 预防措施

### 1. 依赖版本锁定

```txt
# requirements.txt - 使用精确版本
fastapi==0.115.0
uvicorn==0.32.0
beanie==1.27.0
motor==3.6.0
pymongo==4.9.2
```

### 2. 环境变量验证

```python
# config.py - 添加验证
class Settings(BaseSettings):
    jwt_secret: str = Field(..., min_length=32)
    mongodb_url: str = Field(..., pattern="^mongodb://")
```

### 3. 健康检查

```python
# main.py
@app.get("/health/db")
async def health_db():
    try:
        await mongodb.get_database().command("ping")
        return {"database": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
```

### 4. 日志记录

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logger.info("API request received")
logger.error(f"Error occurred: {e}")
```

---

## 获取帮助

### 查看文档

- [API 文档](http://localhost:9000/api/v1/docs)
- [ReDoc](http://localhost:9000/api/v1/redoc)
- [MongoDB 文档](https://www.mongodb.com/docs/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

### 日志收集

```bash
# 导出所有日志
docker compose logs > debug.log 2>&1

# 导出特定时间范围
docker compose logs --since 1h backend > backend.log
```

### 问题报告

收集以下信息后提交 Issue:

1. 错误信息
2. Docker 日志
3. 环境信息 (`docker compose version`, `docker version`)
4. 复现步骤

---

**最后更新**: 2024-12-23
**文档版本**: 1.0
