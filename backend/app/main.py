"""
Unified Backend Platform - Main Entry Point

FastAPI 应用入口
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import auth, files, records
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


# ============================================================================
# API 路由
# ============================================================================
app.include_router(
    auth.router,
    prefix=settings.api_prefix,
    tags=["Authentication"],
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
# 根路径
# ============================================================================
@app.get("/", tags=["System"])
async def root():
    """根路径"""
    return {
        "message": "Welcome to Unified Backend Platform",
        "docs": f"{settings.api_prefix}/docs",
        "health": "/health",
    }
