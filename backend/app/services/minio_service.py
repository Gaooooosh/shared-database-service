"""
Unified Backend Platform - MinIO Service

MinIO/S3 对象存储服务封装
"""
import hashlib
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.models.file import File, FileCategory, FileStatus

settings = get_settings()


class MinIOService:
    """MinIO 对象存储服务"""

    def __init__(self):
        """初始化 MinIO 客户端"""
        try:
            import boto3

            # 解析 endpoint 获取主机和端口
            endpoint = settings.minio_endpoint

            # 创建 S3 客户端
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=settings.minio_access_key,
                aws_secret_access_key=settings.minio_secret_key,
                region_name="us-east-1",
                use_ssl=settings.minio_secure,
            )
            self._initialized = True
        except ImportError:
            self._initialized = False
            self.s3_client = None
        except Exception as e:
            self._initialized = False
            self.s3_client = None
            print(f"❌ MinIO 初始化失败: {e}")

    def is_available(self) -> bool:
        """检查 MinIO 是否可用"""
        return self._initialized and self.s3_client is not None

    def generate_storage_path(
        self,
        app_identifier: str,
        file_id: UUID,
        filename: str,
    ) -> str:
        """
        生成存储路径

        格式: {app_identifier}/{year}/{month}/{file_id}-{filename}
        """
        now = datetime.utcnow()
        safe_filename = filename.replace(" ", "_").replace("/", "_")
        return f"{app_identifier}/{now.year}/{now.month:02d}/{file_id}-{safe_filename}"

    def generate_thumbnail_path(
        self,
        app_identifier: str,
        file_id: UUID,
    ) -> str:
        """生成缩略图存储路径"""
        now = datetime.utcnow()
        return f"{app_identifier}/{now.year}/{now.month:02d}/thumbnails/{file_id}.webp"

    async def create_file_record(
        self,
        owner_id: UUID | None,
        app_identifier: str,
        filename: str,
        content_type: str,
        file_size: int,
        storage_path: str,
        file_id: UUID | None = None,
    ) -> File:
        """
        创建文件记录 (上传前调用)

        Args:
            owner_id: 所有者 ID
            app_identifier: 应用标识符
            filename: 文件名
            content_type: MIME 类型
            file_size: 文件大小
            storage_path: 存储路径
            file_id: 文件 ID (可选，如果不提供则自动生成)

        Returns:
            File 记录
        """
        # 获取文件扩展名
        file_extension = filename.rsplit(".", 1)[-1] if "." in filename else ""

        # 确定文件分类
        category = self._determine_category(content_type)

        # 如果没有提供 file_id，生成一个
        if file_id is None:
            file_id = uuid4()

        # 创建文件记录
        file_record = File(
            id=file_id,
            owner_id=owner_id,
            app_identifier=app_identifier,
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            file_extension=file_extension,
            category=category,
            storage_path=storage_path,
            bucket_name=settings.minio_bucket,
            status=FileStatus.UPLOADING,
            is_public=True,  # 默认公开
        )

        await file_record.insert()
        return file_record

    async def confirm_upload(
        self,
        file_id: UUID,
        file_hash: str | None = None,
    ) -> File:
        """
        确认上传完成

        Args:
            file_id: 文件 ID
            file_hash: 文件 SHA256 哈希

        Returns:
            更新后的 File 记录
        """
        file_record = await File.find_one(File.id == file_id)

        if not file_record:
            raise ValueError(f"File not found: {file_id}")

        # 更新状态
        file_record.status = FileStatus.COMPLETED
        if file_hash:
            file_record.file_hash = file_hash

        # 生成公共 URL
        file_record.public_url = self.get_public_url(
            file_record.bucket_name,
            file_record.storage_path,
        )

        file_record.touch()
        await file_record.save()

        return file_record

    async def mark_upload_failed(
        self,
        file_id: UUID,
        error_message: str,
    ) -> File:
        """标记上传失败"""
        file_record = await File.find_one(File.id == file_id)

        if not file_record:
            raise ValueError(f"File not found: {file_id}")

        file_record.status = FileStatus.FAILED
        file_record.error_message = error_message
        file_record.touch()
        await file_record.save()

        return file_record

    def generate_presigned_url(
        self,
        bucket: str,
        object_name: str,
        expiration: int = 3600,
        method: str = "put_object",
    ) -> str:
        """
        生成预签名 URL

        Args:
            bucket: 存储桶名称
            object_name: 对象名称
            expiration: 过期时间 (秒)
            method: HTTP 方法 (put_object, get_object)

        Returns:
            预签名 URL
        """
        try:
            response = self.s3_client.generate_presigned_url(
                ClientMethod=method,
                Params={
                    "Bucket": bucket,
                    "Key": object_name,
                },
                ExpiresIn=expiration,
            )
            return response
        except ClientError as e:
            print(f"❌ 生成预签名 URL 失败: {e}")
            raise

    def generate_presigned_post(
        self,
        bucket: str,
        object_name: str,
        expiration: int = 3600,
    ) -> dict[str, Any]:
        """
        生成预签名 POST (用于表单上传)

        Args:
            bucket: 存储桶名称
            object_name: 对象名称
            expiration: 过期时间 (秒)

        Returns:
            包含 url 和 fields 的字典
        """
        try:
            response = self.s3_client.generate_presigned_post(
                Bucket=bucket,
                Key=object_name,
                Fields=None,
                Conditions=[
                    ["content-length-range", 1, settings.max_file_size],
                ],
                ExpiresIn=expiration,
            )
            return response
        except ClientError as e:
            print(f"❌ 生成预签名 POST 失败: {e}")
            raise

    def get_public_url(
        self,
        bucket: str,
        object_name: str,
    ) -> str:
        """获取公共访问 URL"""
        return f"{settings.minio_public_url}/{bucket}/{object_name}"

    async def delete_file(
        self,
        bucket: str,
        object_name: str,
    ) -> bool:
        """删除文件"""
        try:
            self.s3_client.delete_object(
                Bucket=bucket,
                Key=object_name,
            )
            return True
        except ClientError as e:
            print(f"❌ 删除文件失败: {e}")
            return False

    async def file_exists(
        self,
        bucket: str,
        object_name: str,
    ) -> bool:
        """检查文件是否存在"""
        try:
            self.s3_client.head_object(
                Bucket=bucket,
                Key=object_name,
            )
            return True
        except ClientError:
            return False

    async def get_file_size(
        self,
        bucket: str,
        object_name: str,
    ) -> int | None:
        """获取文件大小"""
        try:
            response = self.s3_client.head_object(
                Bucket=bucket,
                Key=object_name,
            )
            return response.get("ContentLength")
        except ClientError:
            return None

    async def copy_file(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> bool:
        """复制文件"""
        try:
            copy_source = {
                "Bucket": source_bucket,
                "Key": source_key,
            }
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key,
            )
            return True
        except ClientError as e:
            print(f"❌ 复制文件失败: {e}")
            return False

    def _determine_category(self, content_type: str) -> FileCategory:
        """根据 MIME 类型确定文件分类"""
        if content_type in settings.allowed_image_types:
            return FileCategory.IMAGE
        elif content_type in settings.allowed_video_types:
            return FileCategory.VIDEO
        elif content_type in settings.allowed_document_types:
            return FileCategory.DOCUMENT
        elif content_type in settings.allowed_audio_types:
            return FileCategory.AUDIO
        elif content_type in [
            "application/zip",
            "application/x-rar-compressed",
            "application/x-7z-compressed",
            "application/x-tar",
            "application/gzip",
        ]:
            return FileCategory.ARCHIVE
        else:
            return FileCategory.OTHER


# 全局单例
minio_service = MinIOService()
