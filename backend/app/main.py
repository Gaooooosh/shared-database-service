"""
Unified Backend Platform - Main Entry Point

FastAPI 应用入口
"""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints import auth, files, permissions, records
from app.core.config import get_settings
from app.db.mongodb import mongodb

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时连接 MongoDB
    await mongodb.connect()
    print(f"✅ MongoDB connected: {settings.mongodb_url}")

    yield

    # 关闭时断开连接
    await mongodb.disconnect()
    print("✅ MongoDB disconnected")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="模块化单体统一后端服务 - 支持多应用共享数据",
    lifespan=lifespan,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)


# ============================================================================
# CORS 中间件
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# 健康检查
# ============================================================================
@app.get("/health", tags=["System"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/api/health/services", tags=["System"])
async def services_health_check():
    """所有服务健康检查代理"""
    import httpx

    services_status = []

    # Backend API
    services_status.append({
        "id": "backend",
        "name": "Backend API",
        "status": "healthy",
        "statusCode": 200,
        "responseTime": 0,
        "message": "运行中",
        "statusId": "status-Backend API",
        "cardId": "card-backend"
    })

    # Casdoor SSO
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://casdoor:8000")
            response_time = 0  # 简化
            services_status.append({
                "id": "casdoor",
                "name": "Casdoor SSO",
                "status": "healthy" if response.status_code in [200, 401] else "error",
                "statusCode": response.status_code,
                "responseTime": response_time,
                "message": "运行中" if response.status_code in [200, 401] else "不可用",
                "statusId": "status-Casdoor SSO",
                "cardId": "card-casdoor"
            })
    except Exception as e:
        services_status.append({
            "id": "casdoor",
            "name": "Casdoor SSO",
            "status": "error",
            "statusCode": None,
            "responseTime": None,
            "message": "连接失败",
            "statusId": "status-Casdoor SSO",
            "cardId": "card-casdoor"
        })

    # Mongo Express
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://mongo-express:8081")
            response_time = 0  # 简化
            services_status.append({
                "id": "mongo",
                "name": "Mongo Express",
                "status": "healthy" if response.status_code in [200, 401] else "error",
                "statusCode": response.status_code,
                "responseTime": response_time,
                "message": "运行中" if response.status_code in [200, 401] else "不可用",
                "statusId": "status-Mongo Express",
                "cardId": "card-mongo"
            })
    except Exception as e:
        services_status.append({
            "id": "mongo",
            "name": "Mongo Express",
            "status": "error",
            "statusCode": None,
            "responseTime": None,
            "message": "连接失败",
            "statusId": "status-Mongo Express",
            "cardId": "card-mongo"
        })

    # MinIO Console
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://minio:9001")  # MinIO Console 内部端口
            response_time = 0  # 简化
            services_status.append({
                "id": "minio",
                "name": "MinIO Console",
                "status": "healthy" if response.status_code in [200, 403, 401] else "error",
                "statusCode": response.status_code,
                "responseTime": response_time,
                "message": "运行中" if response.status_code in [200, 403, 401] else "不可用",
                "statusId": "status-MinIO Console",
                "cardId": "card-minio"
            })
    except Exception as e:
        services_status.append({
            "id": "minio",
            "name": "MinIO Console",
            "status": "error",
            "statusCode": None,
            "responseTime": None,
            "message": "连接失败",
            "statusId": "status-MinIO Console",
            "cardId": "card-minio"
        })

    return {"services": services_status}


# ============================================================================
# API 路由
# ============================================================================
app.include_router(
    auth.router,
    prefix=settings.api_prefix,
    tags=["Authentication"],
)

app.include_router(
    permissions.router,
    prefix=settings.api_prefix,
    tags=["Permissions"],
)

app.include_router(
    records.router,
    prefix=settings.api_prefix,
    tags=["Records"],
)

app.include_router(
    files.router,
    prefix=settings.api_prefix,
    tags=["Files"],
)


# ============================================================================
# 静态文件和文档路由配置
# ============================================================================
# 使用绝对路径，避免工作目录变化导致的问题
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/app
static_dir = Path("/app/static").resolve()  # 使用绝对路径
docs_dir = Path("/docs")  # Docker 挂载点


# ============================================================================
# 文档服务路由 - 必须在静态文件挂载之前定义
# ============================================================================
@app.get("/docs/{file_path:path}", response_class=FileResponse)
async def serve_docs(file_path: str):
    """提供文档文件访问"""
    if not docs_dir.exists():
        return {"error": "Documentation directory not found", "path": file_path}

    doc_file = docs_dir / file_path
    if doc_file.exists() and doc_file.is_file():
        return FileResponse(str(doc_file))
    # 返回 404
    return FileResponse(str(static_dir / "index.html"), status_code=404)


# ============================================================================
# 主页路由
# ============================================================================
@app.get("/", response_class=HTMLResponse)
async def root():
    """主页 - 开发者中心"""
    if static_dir.exists():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
    return {"message": "Welcome to Unified Backend Platform", "docs": "/docs/README.md"}


# ============================================================================
# 静态文件挂载 - 必须放在最后
# ============================================================================
if static_dir.exists():
    print(f"📂 挂载静态文件目录: {static_dir.resolve()}")
    app.mount("/static", StaticFiles(directory=str(static_dir.resolve())), name="static")
else:
    print(f"⚠️  静态文件目录不存在: {static_dir}")
