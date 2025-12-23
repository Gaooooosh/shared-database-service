"""
Unified Backend Platform - UnifiedRecord CRUD Endpoints

通用业务数据 API - 核心功能
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError

from app.api.v1.schemas.record import (
    BatchCreateRequest,
    BatchCreateResponse,
    BatchDeleteRequest,
    BatchDeleteResponse,
    BatchOperationResult,
    BatchUpdateRequest,
    BatchUpdateResponse,
    UnifiedRecordCreate,
    UnifiedRecordListResponse,
    UnifiedRecordPatch,
    UnifiedRecordResponse,
    UnifiedRecordUpdate,
)
from app.core.security import get_current_user, get_current_user_optional
from app.models.unified_record import UnifiedRecord
from app.models.user import User

router = APIRouter(prefix="/records", tags=["Unified Records"])


# =============================================================================
# 辅助函数
# =============================================================================
async def get_record_or_404(record_id: UUID | str) -> UnifiedRecord:
    """
    获取记录，不存在则返回 404

    支持 UUID 或字符串 ID
    """
    try:
        # 尝试作为 UUID 查询
        if isinstance(record_id, str):
            try:
                record_uuid = UUID(record_id)
                record = await UnifiedRecord.find_one(
                    UnifiedRecord.id == record_uuid,
                    UnifiedRecord.is_deleted == False,
                )
            except ValueError:
                # 如果不是 UUID 格式，尝试作为 ObjectId 查询
                record = await UnifiedRecord.get(record_id)
        else:
            record = await UnifiedRecord.find_one(
                UnifiedRecord.id == record_id,
                UnifiedRecord.is_deleted == False,
            )

        if not record or record.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record not found: {record_id}",
            )
        return record

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record not found: {record_id}",
        ) from e


# =============================================================================
# CRUD 端点
# =============================================================================
@router.post(
    "",
    response_model=UnifiedRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建新记录",
)
async def create_record(
    data: UnifiedRecordCreate,
    current_user: User = Depends(get_current_user),
) -> UnifiedRecord:
    """
    创建新的 UnifiedRecord

    - 需要认证
    - 自动关联当前用户为所有者
    - payload 可存储任意 JSON 数据
    """
    record = UnifiedRecord(
        app_identifier=data.app_identifier,
        collection_type=data.collection_type,
        owner_id=current_user.id,
        title=data.title,
        description=data.description,
        payload=data.payload,
        is_published=data.is_published,
        published_at=datetime.utcnow() if data.is_published else None,
    )
    await record.insert()
    return record


@router.get(
    "",
    response_model=UnifiedRecordListResponse,
    summary="查询记录列表",
)
async def list_records(
    app_identifier: str | None = Query(None, description="应用标识符"),
    collection_type: str | None = Query(None, description="数据类型"),
    is_published: bool | None = Query(None, description="发布状态"),
    owner_id: UUID | None = Query(None, description="所有者 ID"),
    search: str | None = Query(None, description="搜索标题/描述"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """
    查询 UnifiedRecord 列表

    - 支持多维度筛选
    - 支持分页
    - 支持排序
    - 支持全文搜索 (标题/描述)
    - 未认证用户只能看到已发布的内容
    """
    # 构建查询条件
    query_filters = [UnifiedRecord.is_deleted == False]

    # 未认证用户只能看已发布内容
    if not current_user:
        query_filters.append(UnifiedRecord.is_published == True)

    # 应用筛选
    if app_identifier:
        query_filters.append(UnifiedRecord.app_identifier == app_identifier)

    if collection_type:
        query_filters.append(UnifiedRecord.collection_type == collection_type)

    if is_published is not None:
        query_filters.append(UnifiedRecord.is_published == is_published)

    if owner_id:
        query_filters.append(UnifiedRecord.owner_id == owner_id)

    # 搜索
    if search:
        search_pattern = f".*{search}.*"
        query_filters.append(
            {
                "$or": [
                    {"title": {"$regex": search_pattern, "$options": "i"}},
                    {"description": {"$regex": search_pattern, "$options": "i"}},
                ]
            }
        )

    # 执行查询
    skip = (page - 1) * page_size
    sort_direction = 1 if sort_order == "asc" else -1

    cursor = UnifiedRecord.find_many(*query_filters).sort(
        [(sort_by, sort_direction)]
    )

    total = await cursor.count()
    items = await cursor.skip(skip).limit(page_size).to_list()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


# =============================================================================
# 批量操作端点 (必须在 /{record_id} 之前定义)
# =============================================================================
@router.post(
    "/batch",
    response_model=BatchCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="批量创建记录",
)
async def batch_create_records(
    request: BatchCreateRequest,
    current_user: User = Depends(get_current_user),
) -> BatchCreateResponse:
    """
    批量创建 UnifiedRecord

    - 最多支持 100 条记录
    - 每条记录都会关联当前用户
    - 可选择遇到错误时是否停止

    返回创建结果统计，包含成功和失败的详细信息
    """
    results = []
    succeeded = 0
    failed = 0

    for index, item_data in enumerate(request.items):
        result = BatchOperationResult(index=index, success=False)

        try:
            record = UnifiedRecord(
                app_identifier=item_data.app_identifier,
                collection_type=item_data.collection_type,
                owner_id=current_user.id,
                title=item_data.title,
                description=item_data.description,
                payload=item_data.payload,
                is_published=item_data.is_published,
                published_at=datetime.utcnow() if item_data.is_published else None,
            )
            await record.insert()

            result.id = record.id
            result.success = True
            succeeded += 1

        except Exception as e:
            result.success = False
            result.error = str(e)
            failed += 1

            if request.stop_on_error:
                break

        results.append(result)

    return BatchCreateResponse(
        total=len(request.items),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )


@router.put(
    "/batch",
    response_model=BatchUpdateResponse,
    summary="批量更新记录",
)
async def batch_update_records(
    request: BatchUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> BatchUpdateResponse:
    """
    批量更新 UnifiedRecord

    - 通过 ID 列表指定要更新的记录
    - 对所有记录应用相同的更新
    - 只有所有者或管理员可以更新

    返回更新结果统计
    """
    results = []
    succeeded = 0
    failed = 0

    for index, record_id in enumerate(request.ids):
        result = BatchOperationResult(
            id=record_id, index=index, success=False
        )

        try:
            record = await UnifiedRecord.find_one(
                UnifiedRecord.id == record_id,
                UnifiedRecord.is_deleted == False,
            )

            if not record:
                result.success = False
                result.error = "Record not found"
                failed += 1
                if request.stop_on_error:
                    break
                results.append(result)
                continue

            # 权限检查
            if record.owner_id != current_user.id and current_user.role != "admin":
                result.success = False
                result.error = "Access denied: not the owner"
                failed += 1
                if request.stop_on_error:
                    break
                results.append(result)
                continue

            # 更新字段
            if request.updates.title is not None:
                record.title = request.updates.title
            if request.updates.description is not None:
                record.description = request.updates.description
            if request.updates.payload is not None:
                record.payload = request.updates.payload
            if request.updates.is_published is not None:
                record.is_published = request.updates.is_published
                if request.updates.is_published and not record.published_at:
                    record.published_at = datetime.utcnow()

            record.touch()
            record.version += 1
            await record.save()

            result.success = True
            succeeded += 1

        except Exception as e:
            result.success = False
            result.error = str(e)
            failed += 1

            if request.stop_on_error:
                break

        results.append(result)

    return BatchUpdateResponse(
        total=len(request.ids),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )


@router.delete(
    "/batch",
    response_model=BatchDeleteResponse,
    summary="批量删除记录",
)
async def batch_delete_records(
    request: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
) -> BatchDeleteResponse:
    """
    批量软删除 UnifiedRecord

    - 通过 ID 列表指定要删除的记录
    - 实际数据不删除，只标记 is_deleted=True
    - 只有所有者或管理员可以删除
    """
    results = []
    succeeded = 0
    failed = 0

    for index, record_id in enumerate(request.ids):
        result = BatchOperationResult(
            id=record_id, index=index, success=False
        )

        try:
            record = await UnifiedRecord.find_one(
                UnifiedRecord.id == record_id,
                UnifiedRecord.is_deleted == False,
            )

            if not record:
                result.success = False
                result.error = "Record not found"
                failed += 1
                if request.stop_on_error:
                    break
                results.append(result)
                continue

            # 权限检查
            if record.owner_id != current_user.id and current_user.role != "admin":
                result.success = False
                result.error = "Access denied: not the owner"
                failed += 1
                if request.stop_on_error:
                    break
                results.append(result)
                continue

            # 软删除
            record.is_deleted = True
            record.touch()
            await record.save()

            result.success = True
            succeeded += 1

        except Exception as e:
            result.success = False
            result.error = str(e)
            failed += 1

            if request.stop_on_error:
                break

        results.append(result)

    return BatchDeleteResponse(
        total=len(request.ids),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )


# =============================================================================
# 单记录操作端点 (必须在 /batch 之后定义)
# =============================================================================
@router.get(
    "/{record_id}",
    response_model=UnifiedRecordResponse,
    summary="获取记录详情",
)
async def get_record(
    record_id: str,
    current_user: User | None = Depends(get_current_user_optional),
) -> UnifiedRecord:
    """
    获取单条 UnifiedRecord 详情

    - 未认证用户只能访问已发布内容
    - 自动增加查看次数
    """
    record = await get_record_or_404(record_id)

    # 权限检查：未发布内容需要所有者或管理员
    if not record.is_published:
        if not current_user or (
            record.owner_id != current_user.id and current_user.role != "admin"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: unpublished content",
            )

    # 增加查看次数
    record.increment_view()
    await record.save()

    return record


@router.put(
    "/{record_id}",
    response_model=UnifiedRecordResponse,
    summary="更新记录",
)
async def update_record(
    record_id: str,
    data: UnifiedRecordUpdate,
    current_user: User = Depends(get_current_user),
) -> UnifiedRecord:
    """
    完整更新 UnifiedRecord

    - 只有所有者或管理员可以更新
    - 更新后 version 自动递增
    """
    record = await get_record_or_404(record_id)

    # 权限检查
    if record.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: not the owner",
        )

    # 更新字段
    if data.title is not None:
        record.title = data.title
    if data.description is not None:
        record.description = data.description
    if data.payload is not None:
        record.payload = data.payload
    if data.is_published is not None:
        record.is_published = data.is_published
        if data.is_published and not record.published_at:
            record.published_at = datetime.utcnow()

    # 更新时间戳和版本
    record.touch()
    record.version += 1

    await record.save()
    return record


@router.patch(
    "/{record_id}",
    response_model=UnifiedRecordResponse,
    summary="部分更新记录",
)
async def patch_record(
    record_id: str,
    data: UnifiedRecordPatch,
    current_user: User = Depends(get_current_user),
) -> UnifiedRecord:
    """
    部分更新 payload (合并操作)

    - 只更新 payload 中的指定字段
    - 其他字段保持不变
    """
    record = await get_record_or_404(record_id)

    # 权限检查
    if record.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: not the owner",
        )

    # 合并 payload
    record.payload.update(data.payload)
    record.touch()
    record.version += 1

    await record.save()
    return record


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除记录",
)
async def delete_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    软删除 UnifiedRecord

    - 实际数据不删除，只标记 is_deleted=True
    - 只有所有者或管理员可以删除
    """
    record = await get_record_or_404(record_id)

    # 权限检查
    if record.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: not the owner",
        )

    record.is_deleted = True
    record.touch()
    await record.save()
