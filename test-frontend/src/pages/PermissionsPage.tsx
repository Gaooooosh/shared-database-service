/**
 * 权限系统测试页面
 */
import { useState, useEffect } from 'react'
import { Card, Table, Tag, Space, Button, Form, Input, Modal, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type { Permission, Role } from '../types'
import { getMyPermissions, getRoles, getPermissions, createRole } from '../services/permissionService'
import { config } from '../config'

export default function PermissionsPage() {
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [loading, setLoading] = useState(false)
  const [roleModalVisible, setRoleModalVisible] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [permsData, rolesData] = await Promise.all([
        getMyPermissions(),
        getRoles({ app_identifier: config.app.identifier, include_permissions: true }),
      ])
      setPermissions(permsData)
      setRoles(rolesData.items)
    } catch (error) {
      console.error('加载权限数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateRole = async () => {
    try {
      const values = await form.validateFields()
      await createRole({
        ...values,
        app_identifier: config.app.identifier,
        permission_ids: [],
      })
      message.success('角色创建成功')
      setRoleModalVisible(false)
      form.resetFields()
      loadData()
    } catch (error) {
      console.error('创建角色失败:', error)
    }
  }

  const permissionColumns: ColumnsType<Permission> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      ellipsis: true,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '应用',
      dataIndex: 'app_identifier',
      key: 'app_identifier',
      render: (app) => app || <Tag color="default">全局</Tag>,
    },
    {
      title: '资源',
      dataIndex: 'resource',
      key: 'resource',
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
    },
    {
      title: '格式',
      key: 'format',
      render: (_, record) => `${record.resource}:${record.action}`,
    },
  ]

  const roleColumns: ColumnsType<Role> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      ellipsis: true,
    },
    {
      title: '角色名',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '权限数量',
      key: 'permissions_count',
      render: (_, record) => record.permissions?.length || 0,
    },
    {
      title: '系统角色',
      dataIndex: 'is_system_role',
      key: 'is_system_role',
      render: (isSystem) => (isSystem ? <Tag color="blue">是</Tag> : <Tag>否</Tag>),
    },
  ]

  return (
    <div>
      <h2>权限系统测试</h2>

      <Card
        title="我的权限"
        style={{ marginBottom: 16 }}
        extra={<Tag color="blue">共 {permissions.length} 条</Tag>}
      >
        <Table
          columns={permissionColumns}
          dataSource={permissions}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Card
        title="角色列表"
        extra={
          <Button type="primary" onClick={() => setRoleModalVisible(true)}>
            创建角色
          </Button>
        }
      >
        <Table
          columns={roleColumns}
          dataSource={roles}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="创建角色"
        open={roleModalVisible}
        onOk={handleCreateRole}
        onCancel={() => setRoleModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="角色名称"
            name="name"
            rules={[{ required: true, message: '请输入角色名称' }]}
          >
            <Input placeholder="例如: test-editor" />
          </Form.Item>

          <Form.Item label="描述" name="description">
            <Input.TextArea rows={3} placeholder="角色描述..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
