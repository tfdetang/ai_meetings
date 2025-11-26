import { useState, useEffect } from 'react'
import { Card, Button, Space, Modal, Form, Input, Select, message, Popconfirm, Tag, Typography, Row, Col, Empty } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ApiOutlined } from '@ant-design/icons'
import { agentsAPI, templatesAPI } from '../api/client'

const { Option } = Select
const { Text, Paragraph } = Typography

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

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>代理管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          创建代理
        </Button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Text>加载中...</Text>
        </div>
      ) : agents.length === 0 ? (
        <Empty
          description="还没有创建任何代理"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            创建第一个代理
          </Button>
        </Empty>
      ) : (
        <Row gutter={[16, 16]}>
          {agents.map(agent => (
            <Col xs={24} sm={24} md={12} lg={8} xl={6} key={agent.id}>
              <Card
                hoverable
                actions={[
                  <Button
                    type="text"
                    icon={<ApiOutlined />}
                    onClick={() => handleTest(agent.id)}
                  >
                    测试
                  </Button>,
                  <Button
                    type="text"
                    icon={<EditOutlined />}
                    onClick={() => handleEdit(agent)}
                  >
                    编辑
                  </Button>,
                  <Popconfirm
                    title="确定要删除这个代理吗？"
                    onConfirm={() => handleDelete(agent.id)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button type="text" danger icon={<DeleteOutlined />}>
                      删除
                    </Button>
                  </Popconfirm>
                ]}
              >
                <Card.Meta
                  title={
                    <Space direction="vertical" size={4} style={{ width: '100%' }}>
                      <Text strong style={{ fontSize: '18px' }}>
                        {agent.name}
                      </Text>
                      <Tag color="blue">{agent.role.name}</Tag>
                    </Space>
                  }
                  description={
                    <Space direction="vertical" style={{ width: '100%', marginTop: 12 }} size={12}>
                      {/* 角色描述 - 可展开/收起 */}
                      {agent.role.description && (
                        <div>
                          <Text strong style={{ fontSize: '12px', color: '#666' }}>角色描述：</Text>
                          <Paragraph
                            ellipsis={{
                              rows: 2,
                              expandable: true,
                              symbol: '展开'
                            }}
                            style={{ marginBottom: 0, marginTop: 4 }}
                          >
                            {agent.role.description}
                          </Paragraph>
                        </div>
                      )}
                      
                      {/* 模型信息 */}
                      <div>
                        <Text strong style={{ fontSize: '12px', color: '#666' }}>模型：</Text>
                        <div style={{ marginTop: 4 }}>
                          <Space size={4}>
                            <Tag color="green">{agent.provider}</Tag>
                            <Tag>{agent.model}</Tag>
                          </Space>
                        </div>
                      </div>
                    </Space>
                  }
                />
              </Card>
            </Col>
          ))}
        </Row>
      )}

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
