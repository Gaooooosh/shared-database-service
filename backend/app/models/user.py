"""
Unified Backend Platform - User Model

本地用户映射模型，与 Casdoor 用户建立关联
"""
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import Field, field_validator


class UserRole:
    """用户角色常量"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class User(Document):
    """
    本地用户映射模型

    存储从 Casdoor 同步的用户信息，用于业务关联
    """

    # ==========================================================================
    # 主键与标识
    # ==========================================================================
    id: UUID = Field(default_factory=uuid4, description="本地用户 ID")

    casdoor_id: str = Indexed(unique=True, description="Casdoor 用户 ID")

    email: str = Indexed(unique=True, description="用户邮箱")

    # ==========================================================================
    # 用户属性
    # ==========================================================================
    display_name: str | None = Field(default=None, description="显示名称")
    avatar: str | None = Field(default=None, description="头像 URL")
    phone: str | None = Field(default=None, description="手机号")

    role: Literal["admin", "user", "guest"] = Field(
        default=UserRole.USER,
        description="用户角色",
    )

    is_active: bool = Field(default=True, description="是否激活")

    # ==========================================================================
    # 元数据
    # ==========================================================================
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    last_login_at: datetime | None = Field(default=None, description="最后登录时间")

    # ==========================================================================
    # Beanie 配置
    # ==========================================================================
    class Settings:
        name = "users"
        indexes = [
            "casdoor_id",
            "email",
            "role",
            "created_at",
        ]

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        """邮箱转小写"""
        return v.lower().strip()

    def update_last_login(self) -> None:
        """更新最后登录时间"""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
