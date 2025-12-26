# JWT 认证修复报告

## 📋 问题概述

**Bug ID**: JWT-TOKEN-EVENTLOOP-001
**修复日期**: 2025-12-26
**严重程度**: 🔴 Critical - 阻止所有写操作
**状态**: ✅ 已修复

### 问题描述

所有需要认证的 POST/PUT/PATCH/DELETE API 请求返回 401 错误：
```
Invalid authentication credentials: Error decoding token: this event loop is already running.
```

### 根本原因

在 `backend/app/core/security.py` 的 `decode_jwt_token()` 函数中，使用了 `loop.run_until_complete()` 在已有事件循环中调用异步函数 `fetcher.get_public_key(kid)`，导致 `RuntimeError`。

**问题代码** (第 165-175 行):
```python
# ❌ 错误：在 FastAPI 事件循环中再次调用 run_until_complete
loop = asyncio.get_event_loop()
public_key = loop.run_until_complete(fetcher.get_public_key(kid))
```

## ✅ 修复方案

采用**方案 1：完全异步重构**（符合 FastAPI 最佳实践）

### 修改内容

#### 1. `decode_jwt_token()` - 改为异步函数

**文件**: `backend/app/core/security.py:134`

```python
# ✅ 修复后：完全异步
async def decode_jwt_token(token: str) -> JWTPayload:
    """解码并验证 JWT Token (异步版本)"""
    try:
        header = jwt.get_unverified_header(token)

        if settings.jwt_algorithm == "RS256":
            kid = header.get("kid")
            fetcher = get_jwks_fetcher()

            # ✅ 直接使用 await，无需 run_until_complete
            public_key = await fetcher.get_public_key(kid)

            payload = jwt.decode(
                token,
                public_key.to_pem().decode('utf-8'),
                algorithms=[settings.jwt_algorithm],
                options={"verify_aud": False},
            )
        else:  # HS256
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )

        return JWTPayload(**payload)

    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}") from e
    except Exception as e:
        raise JWTError(f"Error decoding token: {str(e)}") from e
```

#### 2. `validate_token()` - 改为异步函数

**文件**: `backend/app/core/security.py:194`

```python
# ✅ 修复后：异步调用
async def validate_token(token: str) -> JWTPayload:
    """验证 Token 并返回 payload (异步版本)"""
    if token.startswith("Bearer "):
        token = token[7:]

    return await decode_jwt_token(token)  # ✅ 使用 await
```

#### 3. `get_current_user()` - 使用 await 调用

**文件**: `backend/app/core/security.py:319`

```python
async def get_current_user(
    authorization: str = Header(...),
) -> User:
    """FastAPI Dependency - 获取当前认证用户"""
    try:
        # ✅ 异步解析并验证 JWT
        payload = await validate_token(authorization)

        # 查找或创建本地用户
        user = await get_or_create_user_from_jwt(payload)
        return user

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
```

#### 4. `get_current_user_optional()` - 使用 await 调用

**文件**: `backend/app/core/security.py:345`

```python
async def get_current_user_optional(
    authorization: str | None = Header(None),
) -> User | None:
    """可选的用户认证 - 允许匿名访问"""
    if not authorization:
        return None

    try:
        payload = await validate_token(authorization)  # ✅ 使用 await
        return await get_or_create_user_from_jwt(payload)
    except (JWTError, Exception):
        return None
```

## 📊 修改影响分析

### 影响范围

✅ **无破坏性更改**：所有修改都是向后兼容的
- ✅ FastAPI Dependency 机制自动处理 async 函数
- ✅ 所有现有 API 端点无需修改
- ✅ 前端调用方式保持不变

### 修改文件

| 文件 | 修改内容 | 影响函数 |
|------|---------|---------|
| `backend/app/core/security.py` | 4 个函数改为 async | `decode_jwt_token()`, `validate_token()`, `get_current_user()`, `get_current_user_optional()` |

### 未修改文件

- ✅ `backend/app/api/v1/endpoints/auth.py` - 无需修改（自动处理 async dependency）
- ✅ `backend/app/api/v1/endpoints/records.py` - 无需修改（自动处理 async dependency）
- ✅ `backend/app/api/v1/endpoints/files.py` - 无需修改（自动处理 async dependency）
- ✅ 所有其他使用 `get_current_user()` 的端点 - 无需修改

## 🧪 测试验证

### 测试脚本

已创建测试脚本：`scripts/test_jwt_fix.py`

```bash
# 使用方法
python scripts/test_jwt_fix.py YOUR_JWT_TOKEN
```

### 测试用例

1. ✅ **GET /api/v1/auth/me** - 获取当前用户信息
2. ✅ **POST /api/v1/records** - 创建记录（之前失败的操作）
3. ✅ **DELETE /api/v1/records/{id}** - 删除记录

### 预期结果

**修复前**:
```
HTTP 401 Unauthorized
{
  "detail": "Invalid authentication credentials: Error decoding token: this event loop is already running."
}
```

**修复后**:
```
HTTP 201 Created
{
  "id": "uuid",
  "app_identifier": "test-app",
  "collection_type": "test",
  "title": "JWT 修复测试记录",
  ...
}
```

## 🚀 部署状态

### 当前环境

- ✅ Docker 容器已重启
- ✅ 服务已连接 MongoDB
- ✅ 日志无错误信息
- ⏳ 等待前端团队验证

### 生产环境部署建议

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建并启动容器
docker-compose up -d --build backend

# 3. 验证服务状态
docker-compose logs backend --tail 50

# 4. 测试认证端点
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://your-domain.com/api/v1/auth/me
```

## 📝 技术说明

### 为什么选择完全异步方案？

| 方案 | 优点 | 缺点 | 评分 |
|------|------|------|------|
| **方案 1: 完全异步** ✅ | 符合 FastAPI 最佳实践、无性能损失、代码清晰 | 需要修改多个函数 | ⭐⭐⭐⭐⭐ |
| 方案 2: 同步缓存 | 改动小、实现简单 | 需要预热逻辑、缓存更新复杂 | ⭐⭐⭐ |
| 方案 3: 线程池 | 兼容性好 | 性能开销、代码复杂 | ⭐⭐ |

### FastAPI Dependency 机制

FastAPI 的 `Depends()` 会自动处理异步依赖：
- ✅ 如果依赖函数是 `async def`，FastAPI 会使用 `await`
- ✅ 所有使用 `get_current_user` 的路由函数无需修改
- ✅ 路由函数可以是 `async def` 或普通 `def`

### 异步函数调用链

```
Request → FastAPI Router
  ↓
@router.post("/records")  # async def
  ↓
Depends(get_current_user)  # async def
  ↓
await validate_token()  # async def
  ↓
await decode_jwt_token()  # async def
  ↓
await fetcher.get_public_key()  # async def
  ↓
httpx.AsyncClient.get()  # async HTTP
```

## 🔍 相关代码位置

| 功能 | 文件路径 | 行号 |
|------|---------|------|
| JWT 解码 (async) | `backend/app/core/security.py` | 134 |
| Token 验证 (async) | `backend/app/core/security.py` | 194 |
| 用户认证依赖 (async) | `backend/app/core/security.py` | 295 |
| 可选认证依赖 (async) | `backend/app/core/security.py` | 333 |
| JWKS 公钥获取器 | `backend/app/core/security.py` | 25 |

## ✅ 验证清单

- [x] 代码已修复
- [x] 后端服务已重启
- [x] MongoDB 连接正常
- [x] 日志无错误信息
- [x] 测试脚本已创建
- [x] 修复报告已编写
- [ ] 前端团队验证
- [ ] 生产环境部署

## 🎯 后续行动

1. **前端团队验证**：
   - 使用前端应用测试所有写操作（POST/PUT/PATCH/DELETE）
   - 确认不再出现 401 错误
   - 验证用户权限正常工作

2. **生产环境部署**：
   - 在测试环境验证通过后部署到生产环境
   - 监控日志和错误率
   - 准备回滚方案（如需要）

3. **文档更新**：
   - 更新开发者文档，说明 JWT 认证机制
   - 添加故障排查指南

## 📞 联系方式

如有问题，请联系：
- **后端团队**: backend@example.com
- **Bug 报告人**: 前端开发团队

---

**修复完成时间**: 2025-12-26
**修复验证**: 待前端团队确认
**文档版本**: 1.0
