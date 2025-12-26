/**
 * 登录页面 - Casdoor SSO
 */
import { useEffect } from 'react'
import { Button, Card, Space } from 'antd'
import { GithubOutlined, GoogleOutlined, UserOutlined } from '@ant-design/icons'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { getLoginUrl, handleLoginCallback } from '../services/authService'
import { useAuthStore } from '../store/authStore'
import { message } from 'antd'

export default function LoginPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { setToken } = useAuthStore()

  useEffect(() => {
    // 处理登录回调
    const code = searchParams.get('code')
    const state = searchParams.get('state')

    if (code && state) {
      handleLoginCallback(code)
        .then((token) => {
          setToken(token)
          message.success('登录成功')
          navigate('/')
        })
        .catch((error) => {
          message.error('登录失败: ' + error.message)
          console.error(error)
        })
    }
  }, [searchParams, setToken, navigate])

  const handleLogin = (provider: string) => {
    const loginUrl = getLoginUrl()
    window.location.href = loginUrl
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card
        title="后端测试前端"
        style={{ width: 400, textAlign: 'center' }}
        extra={<div style={{ fontSize: 12, color: '#999' }}>SSO 登录</div>}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <p>请使用 Casdoor SSO 登录</p>
            <p style={{ fontSize: 12, color: '#999' }}>
              测试环境 - 仅用于开发和测试
            </p>
          </div>

          <Button
            type="primary"
            size="large"
            block
            icon={<UserOutlined />}
            onClick={() => handleLogin('casdoor')}
          >
            Casdoor 登录
          </Button>

          <div style={{ fontSize: 12, color: '#999' }}>
            <p>支持多种登录方式:</p>
            <Space>
              <GithubOutlined />
              <GoogleOutlined />
              <span>其他</span>
            </Space>
          </div>
        </Space>
      </Card>
    </div>
  )
}
