/**
 * API 客户端
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { message } from 'antd'
import { useAuthStore } from '../store/authStore'

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:9000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加认证 Token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().token
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError<any>) => {
    const errorMessage = error.response?.data?.detail || error.message || '请求失败'

    // 401 未授权 - 清除 Token 并跳转登录
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      message.error('登录已过期，请重新登录')
      window.location.href = '/login'
      return Promise.reject(error)
    }

    // 403 权限不足
    if (error.response?.status === 403) {
      message.error('权限不足')
      return Promise.reject(error)
    }

    // 其他错误
    message.error(errorMessage)
    return Promise.reject(error)
  }
)

export default apiClient
