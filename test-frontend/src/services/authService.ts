/**
 * 认证服务
 */
import CasdoorSDK from 'casdoor-js-sdk'
import { config } from '../config'
import apiClient from './api'
import type { User } from '../types'

// 初始化 Casdoor SDK
export const casdoorSdk = new CasdoorSDK({
  serverUrl: config.casdoor.origin,
  clientId: config.casdoor.clientId,
  appName: config.casdoor.appName,
  organization: config.casdoor.organization,
  redirectPath: '/login/callback',
})

/**
 * 获取 Casdoor 登录 URL
 */
export function getLoginUrl(): string {
  return casdoorSdk.getSigninUrl()
}

/**
 * 处理登录回调 - 交换 code 获取 token
 */
export async function handleLoginCallback(code: string): Promise<string> {
  const response = await apiClient.post('/auth/login', { code })
  return response.data.access_token
}

/**
 * 获取当前用户信息
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/auth/me')
  return response.data
}

/**
 * 登出
 */
export function logout(): void {
  // 清除本地存储
  localStorage.removeItem('token')
  localStorage.removeItem('user')

  // 跳转到 Casdoor 登出页面
  window.location.href = casdoorSdk.getSignoutUrl()
}

export default {
  getLoginUrl,
  handleLoginCallback,
  getCurrentUser,
  logout,
}
