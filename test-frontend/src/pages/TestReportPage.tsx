/**
 * 测试报告页面 - 自动化测试
 */
import { useState } from 'react'
import { Card, Button, Space, Progress, Typography, Tag, Collapse, Descriptions } from 'antd'
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons'
import { testRunner, assert } from '../utils/testRunner'
import { createRecord, deleteRecord, batchCreateRecords } from '../services/recordService'
import { uploadFile } from '../services/fileService'
import { getMyPermissions } from '../services/permissionService'
import { getCurrentUser } from '../services/authService'
import type { TestSuite } from '../types'
import { config } from '../config'

const { Text, Title } = Typography
const { Panel } = Collapse

export default function TestReportPage() {
  const [suites, setSuites] = useState<TestSuite[]>([])
  const [running, setRunning] = useState(false)

  const runAllTests = async () => {
    try {
      setRunning(true)
      testRunner.clearSuites()
      setSuites([])

      // 1. 认证测试
      const authSuite = testRunner.createSuite('认证系统测试')
      await testRunner.runSuite(authSuite, [
        {
          name: '获取当前用户信息',
          fn: async () => {
            const user = await getCurrentUser()
            assert.truthy(user, '用户信息不能为空')
            assert.truthy(user.id, '用户ID不能为空')
            assert.truthy(user.email, '用户邮箱不能为空')
          },
        },
      ])

      // 2. 权限系统测试
      const permSuite = testRunner.createSuite('权限系统测试')
      await testRunner.runSuite(permSuite, [
        {
          name: '获取用户权限列表',
          fn: async () => {
            const permissions = await getMyPermissions()
            assert.truthy(Array.isArray(permissions), '权限应该是数组')
          },
        },
      ])

      // 3. 记录 CRUD 测试
      const recordSuite = testRunner.createSuite('记录 CRUD 测试')
      let testRecordId: string | undefined

      await testRunner.runSuite(recordSuite, [
        {
          name: '创建记录',
          fn: async () => {
            const record = await createRecord({
              app_identifier: config.app.identifier,
              collection_type: 'test-record',
              title: '测试记录',
              description: '这是自动化测试创建的记录',
              payload: { test: true, created_at: new Date().toISOString() },
              is_published: true,
            })
            assert.truthy(record, '记录不能为空')
            assert.truthy(record.id, '记录ID不能为空')
            testRecordId = record.id
          },
        },
        {
          name: '批量创建记录',
          fn: async () => {
            const result = await batchCreateRecords(
              [
                {
                  app_identifier: config.app.identifier,
                  collection_type: 'test-batch',
                  payload: { batch_index: 1 },
                },
                {
                  app_identifier: config.app.identifier,
                  collection_type: 'test-batch',
                  payload: { batch_index: 2 },
                },
              ],
              false
            )
            assert.equal(result.total, 2, '应该创建2条记录')
            assert.equal(result.succeeded, 2, '应该成功2条')
            assert.equal(result.failed, 0, '应该失败0条')
          },
        },
      ])

      // 清理测试数据
      if (testRecordId) {
        await deleteRecord(testRecordId)
      }

      // 4. 文件上传测试
      const fileSuite = testRunner.createSuite('文件上传测试')
      await testRunner.runSuite(fileSuite, [
        {
          name: '上传文本文件',
          fn: async () => {
            const testFile = new File(['test content'], 'test.txt', { type: 'text/plain' })
            const file = await uploadFile(testFile, {
              app_identifier: config.app.identifier,
              title: '测试文件',
              is_public: true,
            })
            assert.truthy(file, '文件不能为空')
            assert.truthy(file.id, '文件ID不能为空')
            assert.equal(file.category, 'document', '文件分类应该是document')
          },
        },
      ])

      setSuites(testRunner.getSuites())
    } catch (error) {
      console.error('测试运行失败:', error)
    } finally {
      setRunning(false)
    }
  }

  const getStats = () => {
    return testRunner.getStats()
  }

  const stats = getStats()
  const passRate =
    stats.totalTests > 0 ? Math.round((stats.passedTests / stats.totalTests) * 100) : 0

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Title level={3}>自动化测试报告</Title>
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={runAllTests}
          loading={running}
          size="large"
        >
          运行所有测试
        </Button>
      </div>

      {/* 统计概览 */}
      <Space direction="vertical" size="large" style={{ width: '100%', marginBottom: 24 }}>
        <Card>
          <Descriptions column={4}>
            <Descriptions.Item label="测试套件">{stats.totalSuites}</Descriptions.Item>
            <Descriptions.Item label="总测试数">{stats.totalTests}</Descriptions.Item>
            <Descriptions.Item label="通过">
              <Text type="success">{stats.passedTests}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="失败">
              <Text type="danger">{stats.failedTests}</Text>
            </Descriptions.Item>
          </Descriptions>
          <div style={{ marginTop: 16 }}>
            <Text>通过率: </Text>
            <Progress
              percent={passRate}
              status={passRate === 100 ? 'success' : passRate >= 50 ? 'normal' : 'exception'}
            />
          </div>
        </Card>
      </Space>

      {/* 测试套件详情 */}
      <Collapse>
        {suites.map((suite) => (
          <Panel
            header={
              <Space>
                <span>{suite.name}</span>
                {suite.status === 'passed' && (
                  <Tag color="success" icon={<CheckCircleOutlined />}>
                    通过
                  </Tag>
                )}
                {suite.status === 'failed' && (
                  <Tag color="error" icon={<CloseCircleOutlined />}>
                    失败
                  </Tag>
                )}
                {suite.status === 'running' && (
                  <Tag color="processing" icon={<LoadingOutlined />}>
                    运行中
                  </Tag>
                )}
                <Text type="secondary">{suite.duration}ms</Text>
              </Space>
            }
            key={suite.name}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {suite.tests.map((test) => (
                <Card key={test.name} size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Space>
                      {test.status === 'passed' && (
                        <CheckCircleOutlined style={{ color: '#52c41a' }} />
                      )}
                      {test.status === 'failed' && (
                        <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                      )}
                      {test.status === 'running' && (
                        <LoadingOutlined style={{ color: '#1677ff' }} />
                      )}
                      <Text strong>{test.name}</Text>
                      {test.duration && (
                        <Text type="secondary">{test.duration}ms</Text>
                      )}
                    </Space>
                    {test.error && (
                      <Text type="danger" style={{ marginTop: 8 }}>
                        错误: {test.error}
                      </Text>
                    )}
                  </Space>
                </Card>
              ))}
            </Space>
          </Panel>
        ))}
      </Collapse>
    </div>
  )
}
