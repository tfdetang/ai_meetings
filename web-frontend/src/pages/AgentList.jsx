import { useState, useEffect } from 'react'
import { Table, Button, Space, Modal, Form, Input, Select, message, Popconfirm, Tag } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ApiOutlined } from '@ant-design/icons'
import { agentsAPI, templatesAPI } from '../api/client'

const { Option } = Select

function AgentList() {
  const [agents, setAgents] = useState([])
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingAgent, setEditingAgent] = useState(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadAgents()
    loadTemplates()
  }, [])

  const loadAgents = async () => {
    setLoading(true)
    try {
      const response = await agentsAPI.list()
      setAgents(response.data)
    } catch (error) {
      message.error('加载代理列表失败')
    } finally {
      setLoading(false)
    }
  }

  const loadTemplates = async () => {
    try {
      const response = await templatesAPI.list()
      setTemplates(response.data)
    } catch (error) {
      console.error('Failed to load templates:', error)
    }
  }

  const handleCreate = () => {
    setEditingAgent(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (agent) => {
    setEditingAgent(agent)
    form.setFieldsValue({
      name: agent.name,
      role_name: agent.role.name,
      role_description: agent.role.description,
      role_prompt: agent.role.prompt,
    })
    setModalVisible(true)
  }

  const handleDelete = async (id) => {
    try {
      await agentsAPI.delete(id)
      message.success('删除成功')
      loadAgents()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleTest = async (id) => {
    try {
      const response = await agentsAPI.test(id)
      if (response.data.success) {
        message.success('连接测试成功')
      } else {
        message.error(`连接测试失败: ${response.data.message}`)
      }
    } catch (error) {
      message.error('连接测试失败')
    }
  }

  const handleSubmit = async (values) => {
    try {
      if (editingAgent) {
        await agentsAPI.update(editingAgent.id, values)
        message.success('更新成功')
      } else {
        await agentsAPI.create(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      loadAgents()
    } catch (error) {
      message.error(editingAgent ? '更新失败' : '创建失败')
    }
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '角色',
      dataIndex: ['role', 'name'],
      key: 'role',
    },
    {
      title: '供应商',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider) => <Tag color="blue">{provider}</Tag>
    },
    {
      title: '模型',
      dataIndex: 'model',
      key: 'model',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<ApiOutlined />}
            onClick={() => handleTest(record.id)}
          >
            测试
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个代理吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
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
        <h2>代理管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          创建代理
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={agents}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title={editingAgent ? '编辑代理' : '创建代理'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入代理名称' }]}
          >
            <Input placeholder="例如：Alice" />
          </Form.Item>

          {!editingAgent && (
            <>
              <Form.Item
                name="provider"
                label="供应商"
                rules={[{ required: true, message: '请选择供应商' }]}
              >
                <Select placeholder="选择 AI 供应商">
                  <Option value="openai">OpenAI</Option>
                  <Option value="anthropic">Anthropic</Option>
                  <Option value="google">Google</Option>
                  <Option value="glm">GLM (智谱AI)</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="model"
                label="模型"
                rules={[{ required: true, message: '请输入模型名称' }]}
              >
                <Input placeholder="例如：gpt-4" />
              </Form.Item>

              <Form.Item
                name="api_key"
                label="API Key"
                rules={[{ required: true, message: '请输入 API Key' }]}
              >
                <Input.Password placeholder="输入 API Key" />
              </Form.Item>

              <Form.Item
                name="template_name"
                label="角色模板（可选）"
              >
                <Select placeholder="选择预设角色模板" allowClear>
                  {templates.map(t => (
                    <Option key={t.name} value={t.name}>
                      {t.role_name} - {t.description}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </>
          )}

          <Form.Item
            name="role_name"
            label="角色名称"
            rules={[{ required: !editingAgent, message: '请输入角色名称' }]}
          >
            <Input placeholder="例如：产品经理" />
          </Form.Item>

          <Form.Item
            name="role_description"
            label="角色描述"
          >
            <Input.TextArea rows={2} placeholder="简短描述这个角色" />
          </Form.Item>

          <Form.Item
            name="role_prompt"
            label="角色提示词"
          >
            <Input.TextArea rows={4} placeholder="定义代理的行为和特征" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default AgentList
