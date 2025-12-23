"""
Unified Backend Platform - MongoDB Connection

使用 Motor (异步 MongoDB 驱动) 和 Beanie (ODM) 管理数据库连接
"""
from typing import AsyncGenerator

import beanie
import motor.motor_asyncio
from beanie import init_beanie

from app.core.config import get_settings


settings = get_settings()


class MongoDB:
    """MongoDB 连接管理器"""

    client: motor.motor_asyncio.AsyncIOMotorClient | None = None

    async def connect(self) -> None:
        """建立 MongoDB 连接并初始化 Beanie ODM"""
        if self.client is not None:
            return

        self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)

        # 延迟导入模型，避免循环依赖
        from app.models.user import User
        from app.models.unified_record import UnifiedRecord
        from app.models.file import File

        await init_beanie(
            database=self.client.get_database(settings.mongodb_database),
            document_models=[User, UnifiedRecord, File],
        )

    async def disconnect(self) -> None:
        """关闭 MongoDB 连接"""
        if self.client:
            self.client.close()
            self.client = None

    async def get_database(self):
        """获取数据库实例"""
        if self.client is None:
            await self.connect()
        return self.client.get_database(settings.mongodb_database)


# 全局 MongoDB 实例
mongodb = MongoDB()


async def get_database() -> AsyncGenerator[motor.motor_asyncio.AsyncIOMotorDatabase, None]:
    """
    FastAPI 依赖注入 - 获取数据库实例

    Usage:
        @app.get("/")
        async def route(db: AsyncIOMotorDatabase = Depends(get_database)):
            ...
    """
    yield await mongodb.get_database()
