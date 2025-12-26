/**
 * 权限服务
 */
import apiClient from './api'
import type { Permission, Role, ApiResponse } from '../types'

/**
 * 获取当前用户的所有权限
 */
export async function getMyPermissions(): Promise<Permission[]> {
  const response = await apiClient.get<Permission[]>('/permissions/me')
  return response.data
}

/**
 * 检查是否有指定权限
 */
export async function checkPermission(
  appIdentifier: string,
  resource: string,
  action: string
): Promise<{ has_permission: boolean }> {
  const response = await apiClient.get('/permissions/check', {
    params: { app_identifier: appIdentifier, resource, action },
  })
  return response.data
}

/**
 * 获取角色列表
 */
export async function getRoles(params?: {
  app_identifier?: string
  include_permissions?: boolean
  page?: number
  page_size?: number
}): Promise<{ items: Role[]; total: number }> {
  const response = await apiClient.get('/permissions/roles', { params })
  return response.data
}

/**
 * 创建角色
 */
export async function createRole(data: {
  name: string
  description?: string
  app_identifier?: string
  permission_ids: string[]
}): Promise<Role> {
  const response = await apiClient.post('/permissions/roles', data)
  return response.data
}

/**
 * 获取权限列表
 */
export async function getPermissions(params?: {
  app_identifier?: string
  page?: number
  page_size?: number
}): Promise<{ items: Permission[]; total: number }> {
  const response = await apiClient.get('/permissions', { params })
  return response.data
}

export default {
  getMyPermissions,
  checkPermission,
  getRoles,
  createRole,
  getPermissions,
}
