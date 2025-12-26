/**
 * 仪表盘页面
 */
import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Spin } from 'antd'
import {
  DatabaseOutlined,
  FileOutlined,
  UserOutlined,
  SafetyOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../store/authStore'
import { getRecords } from '../services/recordService'
import { getFiles } from '../services/fileService'
import { getMyPermissions } from '../services/permissionService'

interface DashboardStats {
  totalRecords: number
  totalFiles: number
  totalPermissions: number
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<DashboardStats>({
    totalRecords: 0,
    totalFiles: 0,
    totalPermissions: 0,
  })

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      setLoading(true)
      const [recordsRes, filesRes, permissions] = await Promise.all([
        getRecords({ page: 1, page_size: 1 }),
        getFiles({ page: 1, page_size: 1 }),
        getMyPermissions(),
      ])

      setStats({
        totalRecords: recordsRes.total,
        totalFiles: filesRes.total,
        totalPermissions: permissions.length,
      })
    } catch (error) {
      console.error('加载统计数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>仪表盘</h2>
      <p>欢迎回来, {user?.display_name || user?.email}</p>

      <Spin spinning={loading}>
        <Row gutter={16} style={{ marginTop: 24 }}>
          <Col span={8}>
            <Card>
              <Statistic
                title="总记录数"
                value={stats.totalRecords}
                prefix={<DatabaseOutlined />}
                valueStyle={{ color: '#1677ff' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="总文件数"
                value={stats.totalFiles}
                prefix={<FileOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="我的权限"
                value={stats.totalPermissions}
                prefix={<SafetyOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
        </Row>
      </Spin>

      <Card style={{ marginTop: 24 }} title="快速测试">
        <p>点击左侧菜单进行详细测试:</p>
        <ul>
          <li>
            <strong>记录管理</strong>: 测试 CRUD 和批量操作
          </li>
          <li>
            <strong>文件管理</strong>: 测试文件上传和管理
          </li>
          <li>
            <strong>权限系统</strong>: 测试 RBAC 权限控制
          </li>
          <li>
            <strong>测试报告</strong>: 查看自动化测试结果
          </li>
        </ul>
      </Card>
    </div>
  )
}
