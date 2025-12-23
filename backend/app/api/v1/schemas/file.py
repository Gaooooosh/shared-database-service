"""
Unified Backend Platform - File Management Schemas

文件管理相关的 Pydantic 模型
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.file import FileCategory, FileStatus


# =============================================================================
# 请求 Schemas
# =============================================================================
class FileUploadResponse(BaseModel):
    """文件上传响应 (单次上传完成时返回)"""

    id: UUID = Field(..., description="文件 ID")
    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小 (字节)")
    content_type: str = Field(..., description="MIME 类型")
    category: FileCategory = Field(..., description="文件分类")
    public_url: str | None = Field(None, description="公共访问 URL")
    thumbnail_url: str | None = Field(None, description="缩略图 URL")
    status: FileStatus = Field(..., description="文件状态")


class FileMetadataUpdate(BaseModel):
    """更新文件元数据"""

    title: str | None = Field(None, max_length=200, description="文件标题")
    description: str | None = Field(None, max_length=1000, description="文件描述")
    alt_text: str | None = Field(None, max_length=200, description="图片 alt 文本")
    is_public: bool | None = Field(None, description="是否公开访问")
    metadata: dict[str, Any] | None = Field(None, description="自定义元数据")


# =============================================================================
# 响应 Schemas
# =============================================================================
class FileResponse(BaseModel):
    """文件详情响应"""

    id: UUID = Field(..., description="文件 ID")
    owner_id: UUID | None = Field(None, description="所有者 ID")
    app_identifier: str = Field(..., description="应用标识符")

    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    content_type: str = Field(..., description="MIME 类型")
    file_extension: str = Field(..., description="文件扩展名")
    category: FileCategory = Field(..., description="文件分类")

    storage_path: str = Field(..., description="存储路径")
    bucket_name: str = Field(..., description="存储桶名称")
    public_url: str | None = Field(None, description="公共访问 URL")

    # 图片信息
    thumbnail_id: UUID | None = Field(None, description="缩略图文件 ID")
    thumbnail_path: str | None = Field(None, description="缩略图路径")
    width: int | None = Field(None, description="图片宽度")
    height: int | None = Field(None, description="图片高度")

    # 视频/音频信息
    duration: int | None = Field(None, description="时长 (秒)")

    # 元数据
    title: str | None = Field(None, description="标题")
    description: str | None = Field(None, description="描述")
    alt_text: str | None = Field(None, description="alt 文本")
    status: FileStatus = Field(..., description="状态")
    is_public: bool = Field(..., description="是否公开")
    is_deleted: bool = Field(..., description="是否已删除")

    # 统计
    download_count: int = Field(..., description="下载次数")
    view_count: int = Field(..., description="查看次数")

    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    expires_at: datetime | None = Field(None, description="过期时间")

    metadata: dict[str, Any] = Field(..., description="自定义元数据")

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """文件列表响应"""

    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    items: list[FileResponse] = Field(..., description="文件列表")


class PresignedUploadRequest(BaseModel):
    """请求预签名上传 URL"""

    filename: str = Field(..., description="文件名")
    content_type: str = Field(..., description="MIME 类型")
    file_size: int = Field(..., description="文件大小 (字节)")
    app_identifier: str = Field(..., description="应用标识符")


class PresignedUploadResponse(BaseModel):
    """预签名上传 URL 响应"""

    upload_id: UUID = Field(..., description="上传 ID")
    upload_url: str = Field(..., description="预签名上传 URL")
    file_id: UUID = Field(..., description="文件 ID")
    storage_path: str = Field(..., description="存储路径")
    bucket: str = Field(..., description="存储桶名称")
    headers: dict[str, str] = Field(..., description="上传请求头")


class ConfirmUploadRequest(BaseModel):
    """确认上传完成请求"""

    file_id: UUID = Field(..., description="文件 ID")
    file_hash: str | None = Field(None, description="文件 SHA256 哈希 (可选)")
