"""
Unified Backend Platform - UnifiedRecord Schemas

Pydantic 模型用于请求验证和响应序列化
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# 请求 Schemas
# =============================================================================
class UnifiedRecordCreate(BaseModel):
    """创建 UnifiedRecord 请求"""

    app_identifier: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="应用标识符 (如: blog-app)",
    )

    collection_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="数据类型 (如: post, comment)",
    )

    title: str | None = Field(None, max_length=200, description="记录标题")

    description: str | None = Field(None, max_length=500, description="记录描述")

    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="业务数据负载 (任意 JSON 结构)",
    )

    is_published: bool = Field(default=True, description="是否发布")


class UnifiedRecordUpdate(BaseModel):
    """更新 UnifiedRecord 请求"""

    title: str | None = Field(None, max_length=200, description="记录标题")

    description: str | None = Field(None, max_length=500, description="记录描述")

    payload: dict[str, Any] | None = Field(None, description="业务数据负载")

    is_published: bool | None = Field(None, description="是否发布")


class UnifiedRecordPatch(BaseModel):
    """部分更新 payload (Patch 操作)"""

    payload: dict[str, Any] = Field(
        ...,
        description="要合并到现有 payload 的数据",
    )


# =============================================================================
# 响应 Schemas
# =============================================================================
class UnifiedRecordResponse(BaseModel):
    """UnifiedRecord 响应"""

    id: UUID = Field(..., description="记录 ID")
    app_identifier: str = Field(..., description="应用标识符")
    collection_type: str = Field(..., description="数据类型")
    owner_id: UUID | None = Field(None, description="所有者 ID")
    title: str | None = Field(None, description="标题")
    description: str | None = Field(None, description="描述")
    payload: dict[str, Any] = Field(..., description="业务数据")
    is_deleted: bool = Field(..., description="是否已删除")
    is_published: bool = Field(..., description="是否已发布")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    published_at: datetime | None = Field(None, description="发布时间")
    version: int = Field(..., description="版本号")
    view_count: int = Field(..., description="查看次数")

    class Config:
        from_attributes = True


class UnifiedRecordListResponse(BaseModel):
    """UnifiedRecord 列表响应"""

    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    items: list[UnifiedRecordResponse] = Field(..., description="记录列表")


# =============================================================================
# 查询参数 Schemas
# =============================================================================
class UnifiedRecordQuery(BaseModel):
    """UnifiedRecord 查询参数"""

    app_identifier: str | None = Field(None, description="筛选应用")
    collection_type: str | None = Field(None, description="筛选数据类型")
    owner_id: UUID | None = Field(None, description="筛选所有者")
    is_published: bool | None = Field(None, description="筛选发布状态")
    search: str | None = Field(None, description="搜索标题/描述")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")


# =============================================================================
# 批量操作 Schemas
# =============================================================================
class BatchOperationResult(BaseModel):
    """单个操作结果"""

    id: UUID | None = Field(default=None, description="成功时返回记录 ID")
    index: int = Field(..., description="在请求中的索引位置")
    success: bool = Field(..., description="是否成功")
    error: str | None = Field(default=None, description="失败时的错误信息")


class BatchCreateRequest(BaseModel):
    """批量创建请求"""

    items: list[UnifiedRecordCreate] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="要创建的记录列表 (最多 100 条)",
    )

    stop_on_error: bool = Field(
        default=False,
        description="遇到错误时是否停止 (默认继续处理剩余项目)",
    )


class BatchCreateResponse(BaseModel):
    """批量创建响应"""

    total: int = Field(..., description="请求数量")
    succeeded: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    results: list[BatchOperationResult] = Field(..., description="详细结果")


class BatchUpdateRequest(BaseModel):
    """批量更新请求 (通过 ID 列表)"""

    ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="要更新的记录 ID 列表 (最多 100 条)",
    )

    updates: UnifiedRecordUpdate = Field(
        ...,
        description="要应用到此所有记录的更新",
    )

    stop_on_error: bool = Field(
        default=False,
        description="遇到错误时是否停止",
    )


class BatchUpdateResponse(BaseModel):
    """批量更新响应"""

    total: int = Field(..., description="请求数量")
    succeeded: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    results: list[BatchOperationResult] = Field(..., description="详细结果")


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""

    ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="要删除的记录 ID 列表 (最多 100 条)",
    )

    stop_on_error: bool = Field(
        default=False,
        description="遇到错误时是否停止",
    )


class BatchDeleteResponse(BaseModel):
    """批量删除响应"""

    total: int = Field(..., description="请求数量")
    succeeded: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    results: list[BatchOperationResult] = Field(..., description="详细结果")
