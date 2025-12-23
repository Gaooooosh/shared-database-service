"""
Unified Backend Platform - File Management Model

文件元数据模型 - 支持 MinIO/S3 对象存储
"""
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import Field, field_validator


class FileCategory(str, Enum):
    """文件分类"""

    IMAGE = "image"          # 图片: jpg, png, gif, webp, svg
    VIDEO = "video"          # 视频: mp4, mov, avi, mkv
    DOCUMENT = "document"    # 文档: pdf, doc, docx, xls, xlsx, ppt, pptx
    AUDIO = "audio"          # 音频: mp3, wav, flac, aac
    ARCHIVE = "archive"      # 压缩包: zip, rar, 7z, tar
    OTHER = "other"          # 其他


class FileStatus(str, Enum):
    """文件状态"""

    UPLOADING = "uploading"  # 上传中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"        # 失败
    PROCESSING = "processing"  # 处理中 (如生成缩略图)


class File(Document):
    """
    文件元数据模型

    存储文件的元信息，实际文件内容存储在 MinIO/S3

    工作流程：
        1. 用户上传文件 → 创建 File 记录 (status=uploading)
        2. 文件上传到 MinIO → 更新 File 记录 (status=completed)
        3. 图片自动生成缩略图 (可选)
        4. 返回文件 URL 给前端
    """

    # ==========================================================================
    # 主键与关联
    # ==========================================================================
    id: UUID = Field(default_factory=uuid4, description="文件 ID")

    owner_id: UUID | None = Indexed(
        description="所有者用户 ID，匿名上传为 None"
    )

    app_identifier: str = Indexed(
        description="应用标识符 (如: blog-app, forum-app)"
    )

    # ==========================================================================
    # 文件基本信息
    # ==========================================================================
    filename: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小 (字节)")
    content_type: str = Field(..., description="MIME 类型 (如: image/jpeg)")
    file_extension: str = Field(..., description="文件扩展名 (如: jpg, pdf)")

    category: FileCategory = Field(
        default=FileCategory.OTHER,
        description="文件分类",
    )

    # ==========================================================================
    # 存储信息
    # ==========================================================================
    storage_path: str = Field(
        ...,
        description="对象存储路径 (如: blog-app/2024/12/uuid.jpg)",
    )

    bucket_name: str = Field(
        default="unified-files",
        description="MinIO/S3 存储桶名称",
    )

    # 公共访问 URL (可选，如果启用了 CDN 或公共访问)
    public_url: str | None = Field(
        default=None,
        description="公共访问 URL",
    )

    # ==========================================================================
    # 缩略图 (仅图片)
    # ==========================================================================
    thumbnail_id: UUID | None = Field(
        default=None,
        description="缩略图文件 ID (仅图片)",
    )

    thumbnail_path: str | None = Field(
        default=None,
        description="缩略图存储路径",
    )

    # 图片额外信息
    width: int | None = Field(default=None, description="图片宽度 (像素)")
    height: int | None = Field(default=None, description="图片高度 (像素)")

    # 视频/音频额外信息
    duration: int | None = Field(default=None, description="时长 (秒)")

    # ==========================================================================
    # 元数据与状态
    # ==========================================================================
    title: str | None = Field(default=None, description="文件标题 (可自定义)")
    description: str | None = Field(default=None, description="文件描述")
    alt_text: str | None = Field(default=None, description="图片 alt 文本 (SEO)")

    status: FileStatus = Field(
        default=FileStatus.UPLOADING,
        description="文件状态",
    )

    error_message: str | None = Field(
        default=None,
        description="上传失败时的错误信息",
    )

    # 文件哈希 (用于去重)
    file_hash: str | None = Field(
        default=None,
        description="文件 SHA256 哈希 (去重用)",
    )

    # ==========================================================================
    # 访问控制
    # ==========================================================================
    is_public: bool = Field(
        default=False,
        description="是否公开访问",
    )

    is_deleted: bool = Field(
        default=False,
        description="是否已删除 (软删除)",
    )

    # ==========================================================================
    # 统计信息
    # ==========================================================================
    download_count: int = Field(
        default=0,
        description="下载次数",
    )

    view_count: int = Field(
        default=0,
        description="查看次数",
    )

    # ==========================================================================
    # 时间戳
    # ==========================================================================
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="创建时间",
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="更新时间",
    )

    expires_at: datetime | None = Field(
        default=None,
        description="过期时间 (临时文件)",
    )

    # ==========================================================================
    # 自定义元数据 (可存储任意 JSON)
    # ==========================================================================
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="自定义元数据 (如: EXIF 信息、作者、版权等)",
    )

    # ==========================================================================
    # Beanie 配置
    # ==========================================================================
    class Settings:
        name = "files"
        indexes = [
            "owner_id",
            "app_identifier",
            "category",
            "status",
            "is_deleted",
            "is_public",
            "file_hash",
            "created_at",
            ("owner_id", "app_identifier"),
            ("app_identifier", "category"),
        ]
        use_state_management = True

    @field_validator("app_identifier")
    @classmethod
    def lowercase_identifier(cls, v: str) -> str:
        """标识符转小写"""
        return v.lower().strip().replace("_", "-")

    @field_validator("file_extension")
    @classmethod
    def normalize_extension(cls, v: str) -> str:
        """扩展名转小写并去点"""
        return v.lower().lstrip(".")

    def touch(self) -> None:
        """更新 updated_at 时间戳"""
        self.updated_at = datetime.utcnow()

    def increment_download(self) -> None:
        """增加下载次数"""
        self.download_count += 1

    def increment_view(self) -> None:
        """增加查看次数"""
        self.view_count += 1

    def get_file_size_human(self) -> str:
        """获取人类可读的文件大小"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if self.file_size < 1024.0:
                return f"{self.file_size:.2f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.2f} PB"
