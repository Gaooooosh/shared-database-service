/**
 * 统一记录服务
 */
import apiClient from './api'
import type { UnifiedRecord, ApiResponse } from '../types'

/**
 * 查询记录列表
 */
export async function getRecords(params?: {
  app_identifier?: string
  collection_type?: string
  owner_id?: string
  is_published?: boolean
  page?: number
  page_size?: number
}): Promise<{ items: UnifiedRecord[]; total: number }> {
  const response = await apiClient.get('/records', { params })
  return response.data
}

/**
 * 获取单条记录
 */
export async function getRecord(id: string): Promise<UnifiedRecord> {
  const response = await apiClient.get(`/records/${id}`)
  return response.data
}

/**
 * 创建记录
 */
export async function createRecord(data: Partial<UnifiedRecord>): Promise<UnifiedRecord> {
  const response = await apiClient.post('/records', data)
  return response.data
}

/**
 * 更新记录
 */
export async function updateRecord(
  id: string,
  data: Partial<UnifiedRecord>
): Promise<UnifiedRecord> {
  const response = await apiClient.put(`/records/${id}`, data)
  return response.data
}

/**
 * 删除记录（软删除）
 */
export async function deleteRecord(id: string): Promise<void> {
  await apiClient.delete(`/records/${id}`)
}

/**
 * 批量创建记录
 */
export async function batchCreateRecords(
  items: Partial<UnifiedRecord>[],
  stopOnError: boolean = false
): Promise<ApiResponse> {
  const response = await apiClient.post('/records/batch', {
    items,
    stop_on_error: stopOnError,
  })
  return response.data
}

/**
 * 批量更新记录
 */
export async function batchUpdateRecords(
  ids: string[],
  updates: Partial<UnifiedRecord>,
  stopOnError: boolean = false
): Promise<ApiResponse> {
  const response = await apiClient.put('/records/batch', {
    ids,
    updates,
    stop_on_error: stopOnError,
  })
  return response.data
}

/**
 * 批量删除记录
 */
export async function batchDeleteRecords(
  ids: string[],
  stopOnError: boolean = false
): Promise<ApiResponse> {
  const response = await apiClient.delete('/records/batch', {
    data: { ids, stop_on_error: stopOnError },
  })
  return response.data
}

export default {
  getRecords,
  getRecord,
  createRecord,
  updateRecord,
  deleteRecord,
  batchCreateRecords,
  batchUpdateRecords,
  batchDeleteRecords,
}
