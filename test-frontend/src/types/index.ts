/**
 * 类型定义
 */

// 用户信息
export interface User {
  id: string
  email: string
  display_name: string
  avatar?: string
  is_superuser: boolean
  created_at: string
  last_login_at: string
}

// 统一记录
export interface UnifiedRecord {
  id: string
  app_identifier: string
  collection_type: string
  owner_id?: string
  payload: Record<string, any>
  title?: string
  description?: string
  is_deleted: boolean
  is_published: boolean
  version: number
  view_count: number
  created_at: string
  updated_at: string
}

// 文件信息
export interface FileInfo {
  id: string
  owner_id?: string
  app_identifier: string
  filename: string
  file_size: number
  content_type: string
  file_extension: string
  category: 'image' | 'video' | 'document' | 'audio' | 'archive' | 'other'
  storage_path: string
  bucket_name: string
  public_url?: string
  thumbnail_id?: string
  width?: number
  height?: number
  title?: string
  description?: string
  alt_text?: string
  status: 'uploading' | 'processing' | 'completed' | 'error'
  is_public: boolean
  is_deleted: boolean
  download_count: number
  view_count: number
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

// 权限
export interface Permission {
  id: string
  name: string
  description?: string
  app_identifier?: string
  resource: string
  action: string
  created_at: string
}

// 角色
export interface Role {
  id: string
  name: string
  description?: string
  app_identifier?: string
  is_system_role: boolean
  permissions: Permission[]
  created_at: string
}

// API 响应
export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  error?: string
}

// 测试结果
export interface TestResult {
  name: string
  status: 'pending' | 'running' | 'passed' | 'failed'
  duration?: number
  error?: string
  details?: any
}

// 测试套件
export interface TestSuite {
  name: string
  tests: TestResult[]
  status: 'pending' | 'running' | 'passed' | 'failed'
  duration: number
}
