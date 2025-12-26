/**
 * 记录管理页面
 */
import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Switch,
  message,
  Popconfirm,
  Tag,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { UnifiedRecord } from '../types'
import { getRecords, createRecord, updateRecord, deleteRecord } from '../services/recordService'
import { config } from '../config'

export default function RecordsPage() {
  const [loading, setLoading] = useState(false)
  const [records, setRecords] = useState<UnifiedRecord[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRecord, setEditingRecord] = useState<UnifiedRecord | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadRecords()
  }, [page, pageSize])

  const loadRecords = async () => {
    try {
      setLoading(true)
      const { items, total } = await getRecords({
        app_identifier: config.app.identifier,
        page,
        page_size: pageSize,
      })
      setRecords(items)
      setTotal(total)
    } catch (error) {
      console.error('加载记录失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingRecord(null)
    form.resetFields()
    form.setFieldsValue({
      app_identifier: config.app.identifier,
      collection_type: 'test-record',
      is_published: true,
      payload: { test: true },
    })
    setModalVisible(true)
  }

  const handleEdit = (record: UnifiedRecord) => {
    setEditingRecord(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteRecord(id)
      message.success('删除成功')
      loadRecords()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields()

      if (editingRecord) {
        await updateRecord(editingRecord.id, values)
        message.success('更新成功')
      } else {
        await createRecord(values)
        message.success('创建成功')
      }

      setModalVisible(false)
      loadRecords()
    } catch (error) {
      console.error('操作失败:', error)
    }
  }

  const columns: ColumnsType<UnifiedRecord> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      ellipsis: true,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (title) => title || <span style={{ color: '#999' }}>(无标题)</span>,
    },
    {
      title: '类型',
      dataIndex: 'collection_type',
      key: 'collection_type',
      width: 150,
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_, record) => (
        <Space>
          {record.is_published && <Tag color="green">已发布</Tag>}
          {record.is_deleted && <Tag color="red">已删除</Tag>}
        </Space>
      ),
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 80,
    },
    {
      title: '浏览次数',
      dataIndex: 'view_count',
      key: 'view_count',
      width: 100,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除?"
            onConfirm={() => handleDelete(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>记录管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          创建记录
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={records}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (p, ps) => {
            setPage(p)
            setPageSize(ps || 10)
          },
        }}
      />

      <Modal
        title={editingRecord ? '编辑记录' : '创建记录'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="应用标识"
            name="app_identifier"
            rules={[{ required: true, message: '请输入应用标识' }]}
          >
            <Input disabled={!!editingRecord} />
          </Form.Item>

          <Form.Item
            label="数据类型"
            name="collection_type"
            rules={[{ required: true, message: '请输入数据类型' }]}
          >
            <Input disabled={!!editingRecord} />
          </Form.Item>

          <Form.Item label="标题" name="title">
            <Input />
          </Form.Item>

          <Form.Item label="描述" name="description">
            <Input.TextArea rows={3} />
          </Form.Item>

          <Form.Item label="Payload (JSON)" name="payload">
            <Input.TextArea rows={4} placeholder='{"key": "value"}' />
          </Form.Item>

          <Form.Item label="是否发布" name="is_published" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
