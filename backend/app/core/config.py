"""
Unified Backend Platform - Configuration

使用 Pydantic Settings 管理环境变量配置
"""
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # 应用基础配置
    # ==========================================================================
    app_name: str = Field(default="Unified Backend Platform", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    environment: str = Field(default="development", description="运行环境")
    api_prefix: str = Field(default="/api/v1", description="API 前缀")

    # ==========================================================================
    # MongoDB 配置
    # ==========================================================================
    mongodb_url: str = Field(..., description="MongoDB 连接 URL")
    mongodb_database: str = Field(default="unified_backend", description="数据库名称")

    # ==========================================================================
    # Redis 配置
    # ==========================================================================
    redis_url: str = Field(..., description="Redis 连接 URL")
    redis_cache_ttl: int = Field(default=3600, description="缓存默认 TTL (秒)")

    # ==========================================================================
    # Casdoor / JWT 配置
    # ==========================================================================
    casdoor_origin: str = Field(..., description="Casdoor 服务地址")
    jwt_secret: str = Field(..., min_length=32, description="JWT 签名密钥")
    jwt_algorithm: str = Field(default="HS256", description="JWT 加密算法")
    jwt_exp_seconds: int = Field(default=86400, description="JWT 过期时间 (秒)")

    # ==========================================================================
    # CORS 配置
    # ==========================================================================
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3002",
        description="允许的 CORS 源 (逗号分隔)",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """获取 CORS 源列表"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # ==========================================================================
    # MinIO / S3 配置
    # ==========================================================================
    minio_endpoint: str = Field(default="http://localhost:9100", description="MinIO API 端点")
    minio_access_key: str = Field(default="minioadmin", description="MinIO 访问密钥")
    minio_secret_key: str = Field(default="minioadmin123", description="MinIO 秘密密钥")
    minio_bucket: str = Field(default="unified-files", description="主存储桶名称")
    minio_thumbnail_bucket: str = Field(default="unified-thumbnails", description="缩略图存储桶名称")
    minio_public_url: str = Field(default="http://localhost:9100", description="MinIO 公共访问 URL")
    minio_secure: bool = Field(default=False, description="是否使用 HTTPS")

    # 文件上传限制
    max_file_size: int = Field(default=524288000, description="最大文件大小 (500MB)")
    max_image_size: int = Field(default=52428800, description="最大图片大小 (50MB)")
    max_video_size: int = Field(default=524288000, description="最大视频大小 (500MB)")

    # 允许的文件类型
    allowed_image_types: List[str] = Field(
        default=[
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
            "image/bmp",
            "image/tiff",
        ],
        description="允许的图片 MIME 类型",
    )

    allowed_video_types: List[str] = Field(
        default=[
            "video/mp4",
            "video/mpeg",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-ms-wmv",
            "video/webm",
        ],
        description="允许的视频 MIME 类型",
    )

    allowed_document_types: List[str] = Field(
        default=[
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/plain",
            "text/csv",
        ],
        description="允许的文档 MIME 类型",
    )

    allowed_audio_types: List[str] = Field(
        default=[
            "audio/mpeg",
            "audio/mp3",
            "audio/wav",
            "audio/flac",
            "audio/aac",
            "audio/ogg",
        ],
        description="允许的音频 MIME 类型",
    )

    # ==========================================================================
    # 其他配置
    # ==========================================================================
    debug: bool = Field(default=False, description="调试模式")


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
