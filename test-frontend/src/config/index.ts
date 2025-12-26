/**
 * 应用配置
 */
export const config = {
  // Casdoor 配置
  casdoor: {
    origin: import.meta.env.VITE_CASDOOR_ORIGIN || 'http://localhost:8000',
    clientId: import.meta.env.VITE_CASDOOR_CLIENT_ID || 'test-client-id',
    clientSecret: import.meta.env.VITE_CASDOOR_CLIENT_SECRET || 'test-client-secret',
    appName: import.meta.env.VITE_CASDOOR_APP_NAME || 'test-app',
    organization: import.meta.env.VITE_CASDOOR_ORGANIZATION || 'test-org',
  },

  // 后端 API 配置
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:9000/api/v1',
  },

  // 应用配置
  app: {
    name: import.meta.env.VITE_APP_NAME || '后端测试前端',
    identifier: import.meta.env.VITE_APP_IDENTIFIER || 'test-app',
  },
}

export default config
