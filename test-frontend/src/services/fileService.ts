/**
 * 文件服务
 */
import apiClient from './api'
import type { FileInfo, ApiResponse } from '../types'

/**
 * 上传文件（直接上传）
 */
export async function uploadFile(
  file: File,
  metadata: {
    app_identifier: string
    title?: string
    description?: string
    is_public?: boolean
  }
): Promise<FileInfo> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('app_identifier', metadata.app_identifier)
  if (metadata.title) formData.append('title', metadata.title)
  if (metadata.description) formData.append('description', metadata.description)
  if (metadata.is_public !== undefined)
    formData.append('is_public', String(metadata.is_public))

  const response = await apiClient.post<FileInfo>('/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

/**
 * 获取预签名上传 URL
 */
export async function getPresignedUploadUrl(params: {
  filename: string
  content_type: string
  file_size: number
  app_identifier: string
}): Promise<{ file_id: string; upload_url: string; headers: Record<string, string> }> {
  const response = await apiClient.post('/files/upload/presigned', params)
  return response.data
}

/**
 * 确认预签名上传完成
 */
export async function confirmPresignedUpload(fileId: string): Promise<FileInfo> {
  const response = await apiClient.post(`/files/upload/confirm`, { file_id: fileId })
  return response.data
}

/**
 * 查询文件列表
 */
export async function getFiles(params?: {
  app_identifier?: string
  category?: string
  is_public?: boolean
  page?: number
  page_size?: number
}): Promise<{ items: FileInfo[]; total: number }> {
  const response = await apiClient.get('/files', { params })
  return response.data
}

/**
 * 获取文件详情
 */
export async function getFile(fileId: string): Promise<FileInfo> {
  const response = await apiClient.get(`/files/${fileId}`)
  return response.data
}

/**
 * 获取文件下载 URL
 */
export async function getFileDownloadUrl(fileId: string): Promise<{ download_url: string }> {
  const response = await apiClient.get(`/files/${fileId}/download`)
  return response.data
}

/**
 * 更新文件元数据
 */
export async function updateFile(
  fileId: string,
  data: Partial<FileInfo>
): Promise<FileInfo> {
  const response = await apiClient.patch(`/files/${fileId}`, data)
  return response.data
}

/**
 * 删除文件
 */
export async function deleteFile(fileId: string, deleteFromStorage: boolean = false): Promise<void> {
  await apiClient.delete(`/files/${fileId}`, {
    params: { delete_from_storage: deleteFromStorage },
  })
}

export default {
  uploadFile,
  getPresignedUploadUrl,
  confirmPresignedUpload,
  getFiles,
  getFile,
  getFileDownloadUrl,
  updateFile,
  deleteFile,
}
