"""
Unified Backend Platform - File Management Endpoints

文件上传, 下载, 删除 API
"""
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File as FastAPIFile, Form, HTTPException, Query, UploadFile, status
from pydantic import ValidationError

from app.api.v1.schemas.file import (
    ConfirmUploadRequest,
    FileListResponse,
    FileMetadataUpdate,
    FileResponse,
    FileUploadResponse,
    PresignedUploadRequest,
    PresignedUploadResponse,
)
from app.core.config import get_settings
from app.core.security import get_current_user, get_current_user_optional
from app.models.file import File, FileCategory, FileStatus
from app.models.user import User
from app.services.minio_service import minio_service

router = APIRouter(prefix="/files", tags=["Files"])
settings = get_settings()


# =============================================================================
# Helper functions
# =============================================================================
async def get_file_or_404(file_id: UUID) -> File:
    """Get file or return 404"""
    file_record = await File.find_one(
        File.id == file_id,
        File.is_deleted == False,
    )

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}",
        )

    return file_record


def validate_file_type(content_type: str) -> FileCategory:
    """Validate file type and return category"""
    if content_type in settings.allowed_image_types:
        return FileCategory.IMAGE
    elif content_type in settings.allowed_video_types:
        return FileCategory.VIDEO
    elif content_type in settings.allowed_document_types:
        return FileCategory.DOCUMENT
    elif content_type in settings.allowed_audio_types:
        return FileCategory.AUDIO
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {content_type}",
        )


def validate_file_size(file_size: int, category: FileCategory) -> None:
    """Validate file size"""
    if category == FileCategory.IMAGE and file_size > settings.max_image_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image too large (max {settings.max_image_size // 1024 // 1024}MB)",
        )
    elif category == FileCategory.VIDEO and file_size > settings.max_video_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Video too large (max {settings.max_video_size // 1024 // 1024}MB)",
        )
    elif file_size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {settings.max_file_size // 1024 // 1024}MB)",
        )


# =============================================================================
# File upload API
# =============================================================================
@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file directly",
)
async def upload_file(
    file: UploadFile = FastAPIFile(..., description="File to upload"),
    app_identifier: str = Form(..., description="App identifier"),
    title: str | None = Form(None, description="File title"),
    description: str | None = Form(None, description="File description"),
    is_public: bool = Form(True, description="Is public"),
    current_user: User = Depends(get_current_user),
) -> File:
    """Upload file directly (for small files)"""
    if not minio_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MinIO service is not available",
        )

    # Read file content
    content = await file.read()

    # Validate file type
    category = validate_file_type(file.content_type or "")

    # Validate file size
    validate_file_size(len(content), category)

    # Generate storage path
    file_id = uuid4()
    storage_path = minio_service.generate_storage_path(
        app_identifier,
        file_id,
        file.filename or "unnamed",
    )

    # Create file record
    file_record = await minio_service.create_file_record(
        owner_id=current_user.id,
        app_identifier=app_identifier,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        storage_path=storage_path,
        file_id=file_id,
    )

    # Set metadata
    if title:
        file_record.title = title
    if description:
        file_record.description = description
    file_record.is_public = is_public

    try:
        # Upload to MinIO
        minio_service.s3_client.put_object(
            Bucket=settings.minio_bucket,
            Key=storage_path,
            Body=content,
            ContentType=file.content_type,
        )

        # Confirm upload
        file_record = await minio_service.confirm_upload(file_id)

    except Exception as e:
        # Mark as failed
        await minio_service.mark_upload_failed(file_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )

    return file_record


@router.post(
    "/upload/presigned",
    response_model=PresignedUploadResponse,
    summary="Get presigned upload URL",
)
async def get_presigned_upload_url(
    request: PresignedUploadRequest,
    current_user: User = Depends(get_current_user),
) -> PresignedUploadResponse:
    """Get presigned upload URL (for large files or frontend direct upload)"""
    if not minio_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MinIO service is not available",
        )

    # Validate file type
    category = validate_file_type(request.content_type)

    # Validate file size
    validate_file_size(request.file_size, category)

    # Generate file ID and storage path
    file_id = uuid4()
    storage_path = minio_service.generate_storage_path(
        request.app_identifier,
        file_id,
        request.filename,
    )

    # Create file record
    file_record = await minio_service.create_file_record(
        owner_id=current_user.id,
        app_identifier=request.app_identifier,
        filename=request.filename,
        content_type=request.content_type,
        file_size=request.file_size,
        storage_path=storage_path,
    )

    # Generate presigned URL
    upload_url = minio_service.generate_presigned_url(
        bucket=settings.minio_bucket,
        object_name=storage_path,
        expiration=3600,
        method="put_object",
    )

    return PresignedUploadResponse(
        upload_id=file_id,
        upload_url=upload_url,
        file_id=file_record.id,
        storage_path=storage_path,
        bucket=settings.minio_bucket,
        headers={
            "Content-Type": request.content_type,
        },
    )


@router.post(
    "/upload/confirm",
    response_model=FileResponse,
    summary="Confirm upload completion",
)
async def confirm_upload(
    request: ConfirmUploadRequest,
    current_user: User = Depends(get_current_user),
) -> File:
    """Confirm presigned upload completion"""
    file_record = await minio_service.confirm_upload(
        file_id=request.file_id,
        file_hash=request.file_hash,
    )

    return file_record


# =============================================================================
# File query API
# =============================================================================
@router.get(
    "",
    response_model=FileListResponse,
    summary="List files",
)
async def list_files(
    app_identifier: str | None = Query(None, description="Filter by app"),
    category: FileCategory | None = Query(None, description="Filter by category"),
    owner_id: UUID | None = Query(None, description="Filter by owner"),
    is_public: bool | None = Query(None, description="Filter by public status"),
    search: str | None = Query(None, description="Search filename/title"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """List files with filters and pagination"""
    # Build query filters
    query_filters = [File.is_deleted == False]

    # Non-authenticated users can only see public files
    if not current_user:
        query_filters.append(File.is_public == True)

    # Apply filters
    if app_identifier:
        query_filters.append(File.app_identifier == app_identifier)

    if category:
        query_filters.append(File.category == category)

    if owner_id:
        query_filters.append(File.owner_id == owner_id)

    if is_public is not None:
        query_filters.append(File.is_public == is_public)

    # Search
    if search:
        search_pattern = f".*{search}.*"
        query_filters.append(
            {
                "$or": [
                    {"filename": {"$regex": search_pattern, "$options": "i"}},
                    {"title": {"$regex": search_pattern, "$options": "i"}},
                ]
            }
        )

    # Execute query
    skip = (page - 1) * page_size
    sort_direction = 1 if sort_order == "asc" else -1

    cursor = File.find_many(*query_filters).sort([(sort_by, sort_direction)])

    total = await cursor.count()
    items = await cursor.skip(skip).limit(page_size).to_list()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get(
    "/{file_id}",
    response_model=FileResponse,
    summary="Get file details",
)
async def get_file(
    file_id: UUID,
    current_user: User | None = Depends(get_current_user_optional),
) -> File:
    """Get file details"""
    file_record = await get_file_or_404(file_id)

    # Permission check
    if not file_record.is_public:
        if not current_user or (
            file_record.owner_id != current_user.id and current_user.role != "admin"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: private file",
            )

    # Increment view count
    file_record.increment_view()
    await file_record.save()

    return file_record


@router.get(
    "/{file_id}/download",
    summary="Download file",
)
async def download_file(
    file_id: UUID,
    current_user: User | None = Depends(get_current_user_optional),
):
    """Get presigned download URL"""
    file_record = await get_file_or_404(file_id)

    # Permission check
    if not file_record.is_public:
        if not current_user or (
            file_record.owner_id != current_user.id and current_user.role != "admin"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: private file",
            )

    # Check if file exists
    exists = await minio_service.file_exists(
        file_record.bucket_name,
        file_record.storage_path,
    )

    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage",
        )

    # Generate presigned download URL
    download_url = minio_service.generate_presigned_url(
        bucket=file_record.bucket_name,
        object_name=file_record.storage_path,
        expiration=3600,
        method="get_object",
    )

    # Increment download count
    file_record.increment_download()
    await file_record.save()

    return {
        "download_url": download_url,
        "filename": file_record.filename,
        "content_type": file_record.content_type,
        "expires_in": 3600,
    }


# =============================================================================
# File management API
# =============================================================================
@router.patch(
    "/{file_id}",
    response_model=FileResponse,
    summary="Update file metadata",
)
async def update_file_metadata(
    file_id: UUID,
    data: FileMetadataUpdate,
    current_user: User = Depends(get_current_user),
) -> File:
    """Update file metadata"""
    file_record = await get_file_or_404(file_id)

    # Permission check
    if file_record.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: not the owner",
        )

    # Update fields
    if data.title is not None:
        file_record.title = data.title
    if data.description is not None:
        file_record.description = data.description
    if data.alt_text is not None:
        file_record.alt_text = data.alt_text
    if data.is_public is not None:
        file_record.is_public = data.is_public
    if data.metadata is not None:
        file_record.metadata.update(data.metadata)

    file_record.touch()
    await file_record.save()

    return file_record


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete file",
)
async def delete_file(
    file_id: UUID,
    delete_from_storage: bool = Query(False, description="Delete from storage too"),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete file (soft delete by default)"""
    file_record = await get_file_or_404(file_id)

    # Permission check
    if file_record.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: not the owner",
        )

    # Soft delete
    file_record.is_deleted = True
    file_record.touch()
    await file_record.save()

    # Delete from storage
    if delete_from_storage:
        await minio_service.delete_file(
            file_record.bucket_name,
            file_record.storage_path,
        )
