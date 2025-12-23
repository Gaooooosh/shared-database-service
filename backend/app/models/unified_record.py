"""
Unified Backend Platform - UnifiedRecord Model

通用业务数据模型 - 核心特性是 payload 字段支持任意 JSON 结构
"""
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import Field, field_validator


class UnifiedRecord(Document):
    """
    通用业务数据模型

    这是本项目的核心设计：
    - 通过 app_identifier 区分不同应用
    - 通过 collection_type 区分同一应用内的不同数据类型
    - 通过 payload 字段存储任意结构的 JSON 业务数据

    示例：
        # 应用 A 存储文章
        UnifiedRecord(
            app_identifier="blog-app",
            collection_type="post",
            owner_id=user_uuid,
            payload={"title": "Hello", "content": "...", "tags": ["tech"]}
        )

        # 应用 B 存储订单
        UnifiedRecord(
            app_identifier="shop-app",
            collection_type="order",
            owner_id=user_uuid,
            payload={"items": [...], "total": 99.99, "status": "paid"}
        )
    """

    # ==========================================================================
    # 主键与关联
    # ==========================================================================
    id: UUID = Field(default_factory=uuid4, description="记录 ID")

    app_identifier: str = Indexed(
        description="应用标识符 (如: blog-app, shop-app)"
    )

    collection_type: str = Indexed(
        description="数据类型 (如: post, comment, order)"
    )

    owner_id: UUID | None = Indexed(
        description="所有者用户 ID (User.id)，匿名数据为 None"
    )

    # ==========================================================================
    # 核心业务数据 (任意 JSON 结构)
    # ==========================================================================
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="业务数据负载，可存储任意 JSON 结构",
    )

    # ==========================================================================
    # 元数据与软删除
    # ==========================================================================
    title: str | None = Field(default=None, description="记录标题 (便于搜索)")
    description: str | None = Field(default=None, description="记录描述")

    is_deleted: bool = Field(default=False, description="是否已删除 (软删除)")
    is_published: bool = Field(default=True, description="是否已发布")

    # ==========================================================================
    # 时间戳
    # ==========================================================================
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    published_at: datetime | None = Field(default=None, description="发布时间")

    # ==========================================================================
    # 扩展字段 (可选的版本控制和统计)
    # ==========================================================================
    version: int = Field(default=1, description="版本号")
    view_count: int = Field(default=0, description="查看次数")

    # ==========================================================================
    # Beanie 配置
    # ==========================================================================
    class Settings:
        name = "unified_records"
        indexes = [
            "app_identifier",
            "collection_type",
            "owner_id",
            ("app_identifier", "collection_type"),  # 复合索引
            ("app_identifier", "collection_type", "owner_id"),  # 复合索引
            "created_at",
            "is_deleted",
        ]
        use_state_management = True  # 启用变更追踪

    @field_validator("app_identifier", "collection_type")
    @classmethod
    def lowercase_identifier(cls, v: str) -> str:
        """标识符转小写并规范化"""
        return v.lower().strip().replace("_", "-")

    def touch(self) -> None:
        """更新 updated_at 时间戳"""
        self.updated_at = datetime.utcnow()

    def increment_view(self) -> None:
        """增加查看次数"""
        self.view_count += 1
