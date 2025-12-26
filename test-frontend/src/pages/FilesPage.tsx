/**
 * 文件管理页面
 */
import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Upload,
  Space,
  Modal,
  Form,
  Input,
  message,
  Image,
  Tag,
} from 'antd'
import { PlusOutlined, UploadOutlined, DeleteOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { UploadFile } from 'antd/es/upload/interface'
import type { FileInfo } from '../types'
import {
  getFiles,
  uploadFile,
  updateFile,
  deleteFile,
  getFileDownloadUrl,
} from '../services/fileService'
import { config } from '../config'

export default function FilesPage() {
  const [loading, setLoading] = useState(false)
  const [files, setFiles] = useState<FileInfo[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editingFile, setEditingFile] = useState<FileInfo | null>(null)
  const [previewVisible, setPreviewVisible] = useState(false)
  const [previewImage, setPreviewImage] = useState('')
  const [form] = Form.useForm()

  useEffect(() => {
    loadFiles()
  }, [page, pageSize])

  const loadFiles = async () => {
    try {
      setLoading(true)
      const { items, total } = await getFiles({
        app_identifier: config.app.identifier,
        page,
        page_size: pageSize,
      })
      setFiles(items)
      setTotal(total)
    } catch (error) {
      console.error('加载文件失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (file: File) => {
    try {
      const result = await uploadFile(file, {
        app_identifier: config.app.identifier,
        is_public: true,
      })
      message.success('上传成功')
      loadFiles()
      return result
    } catch (error) {
      message.error('上传失败')
      throw error
    }
  }

  const handleEdit = (file: FileInfo) => {
    setEditingFile(file)
    form.setFieldsValue(file)
    setEditModalVisible(true)
  }

  const handleDelete = async (fileId: string) => {
    try {
      await deleteFile(fileId)
      message.success('删除成功')
      loadFiles()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields()
      if (editingFile) {
        await updateFile(editingFile.id, values)
        message.success('更新成功')
      }
      setEditModalVisible(false)
      loadFiles()
    } catch (error) {
      console.error('操作失败:', error)
    }
  }

  const handleDownload = async (file: FileInfo) => {
    try {
      const { download_url } = await getFileDownloadUrl(file.id)
      window.open(download_url, '_blank')
    } catch (error) {
      message.error('获取下载链接失败')
    }
  }

  const handlePreview = (file: FileInfo) => {
    setPreviewImage(file.public_url || '')
    setPreviewVisible(true)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const columns: ColumnsType<FileInfo> = [
    {
      title: '预览',
      key: 'preview',
      width: 80,
      render: (_, record) => {
        if (record.category === 'image' && record.public_url) {
          return (
            <Image
              src={record.public_url}
              alt={record.filename}
              width={50}
              height={50}
              style={{ objectFit: 'cover' }}
            />
          )
        }
        return <span>-</span>
      },
    },
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category) => {
        const colorMap: Record<string, string> = {
          image: 'green',
          video: 'blue',
          document: 'orange',
          audio: 'purple',
          archive: 'red',
          other: 'default',
        }
        return <Tag color={colorMap[category]}>{category}</Tag>
      },
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: formatFileSize,
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_, record) => {
        const statusMap = {
          uploading: 'processing',
          processing: 'processing',
          completed: 'success',
          error: 'error',
        } as const

        const textMap = {
          uploading: '上传中',
          processing: '处理中',
          completed: '已完成',
          error: '错误',
        }

        return <Tag status={statusMap[record.status]}>{textMap[record.status]}</Tag>
      },
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button size="small" onClick={() => handleDownload(record)}>
            下载
          </Button>
          <Button
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>文件管理</h2>
        <Upload
          customRequest={async ({ file, onSuccess, onError }) => {
            try {
              await handleUpload(file as File)
              onSuccess?.(null)
            } catch (error) {
              onError?.(error as Error)
            }
          }}
          showUploadList={false}
        >
          <Button type="primary" icon={<UploadOutlined />}>
            上传文件
          </Button>
        </Upload>
      </div>

      <Table
        columns={columns}
        dataSource={files}
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
        title="编辑文件"
        open={editModalVisible}
        onOk={handleModalOk}
        onCancel={() => setEditModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item label="标题" name="title">
            <Input />
          </Form.Item>

          <Form.Item label="描述" name="description">
            <Input.TextArea rows={3} />
          </Form.Item>

          <Form.Item label="Alt Text" name="alt_text">
            <Input />
          </Form.Item>

          <Form.Item label="是否公开" name="is_public" valuePropName="checked">
            <input type="checkbox" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        open={previewVisible}
        title="图片预览"
        footer={null}
        onCancel={() => setPreviewVisible(false)}
      >
        <Image src={previewImage} style={{ width: '100%' }} />
      </Modal>
    </div>
  )
}
