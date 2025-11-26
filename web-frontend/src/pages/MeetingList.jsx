import { useState, useEffect } from 'react'
import { Table, Button, Space, Modal, Form, Input, Select, message, Popconfirm, Tag, Badge } from 'antd'
import { PlusOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { meetingsAPI, agentsAPI } from '../api/client'

const { Option } = Select

function MeetingList() {
  const navigate = useNavigate()
  const [meetings, setMeetings] = useState([])
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadMeetings()
    loadAgents()
  }, [])

  const loadMeetings = async () => {
    setLoading(true)
    try {
      const response = await meetingsAPI.list()
      setMeetings(response.data)
    } catch (error) {
      message.error('加载会议列表失败')
    } finally {
      setLoading(false)
    }
  }

  const loadAgents = async () => {
    try {
      const response = await agentsAPI.list()
      setAgents(response.data)
    } catch (error) {
      console.error('Failed to load agents:', error)
    }
  }

  const handleCreate = () => {
    form.resetFields()
    setModalVisible(true)
  }

  const handleDelete = async (id) => {
    try {
      await meetingsAPI.delete(id)
      message.success('删除成功')
      loadMeetings()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values) => {
    try {
      // Format the data for the API
      const payload = {
        topic: values.topic,
        agent_ids: values.agent_ids,
        moderator_type: values.moderator_type,
        moderator_id: values.moderator_type === 'agent' ? values.moderator_id : 'user',
        speaking_order: values.speaking_order,
        discussion_style: values.discussion_style,
      }

      // Add optional fields
      if (values.max_rounds) {
        payload.max_rounds = parseInt(values.max_rounds)
      }
      if (values.max_message_length) {
        payload.max_message_length = parseInt(values.max_message_length)
      }

      // Format agenda items
      if (values.agenda && values.agenda.length > 0) {
        payload.agenda = values.agenda.map(title => ({
          title: title,
          description: '',
        }))
      }

      await meetingsAPI.create(payload)
      message.success('创建成功')
      setModalVisible(false)
      loadMeetings()
    } catch (error) {
      message.error('创建失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const getStatusBadge = (status) => {
    const statusMap = {
      active: { status: 'processing', text: '进行中' },
      paused: { status: 'warning', text: '已暂停' },
      ended: { status: 'default', text: '已结束' },
    }
    const config = statusMap[status] || { status: 'default', text: status }
    return <Badge status={config.status} text={config.text} />
  }

  const columns = [
    {
      title: '主题',
      dataIndex: 'topic',
      key: 'topic',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => getStatusBadge(status),
    },
    {
      title: '参与者',
      dataIndex: 'participants',
      key: 'participants',
      render: (participants) => (
        <Space>
          {participants.slice(0, 3).map(p => (
            <Tag key={p.id}>{p.name}</Tag>
          ))}
          {participants.length > 3 && <Tag>+{participants.length - 3}</Tag>}
        </Space>
      ),
    },
    {
      title: '轮次',
      dataIndex: 'current_round',
      key: 'current_round',
      render: (round, record) => 
        record.max_rounds ? `${round}/${record.max_rounds}` : round,
    },
    {
      title: '消息数',
      dataIndex: 'messages',
      key: 'messages',
      render: (messages) => messages.length,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/meetings/${record.id}`)}
          >
            查看
          </Button>
          <Popconfirm
            title="确定要删除这个会议吗？"
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
        <h2>会议管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          创建会议
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={meetings}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title="创建会议"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={700}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="topic"
            label="会议主题"
            rules={[{ required: true, message: '请输入会议主题' }]}
          >
            <Input placeholder="例如：产品规划讨论" />
          </Form.Item>

          <Form.Item
            name="agent_ids"
            label="参与代理"
            rules={[{ required: true, message: '请选择至少一个代理' }]}
          >
            <Select
              mode="multiple"
              placeholder="选择参与会议的代理"
              optionFilterProp="children"
            >
              {agents.map(agent => (
                <Option key={agent.id} value={agent.id}>
                  {agent.name} ({agent.role.name})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="moderator_type"
            label="主持人类型"
            initialValue="user"
            rules={[{ required: true, message: '请选择主持人类型' }]}
          >
            <Select>
              <Option value="user">用户本人</Option>
              <Option value="agent">AI 代理</Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => 
              prevValues.moderator_type !== currentValues.moderator_type
            }
          >
            {({ getFieldValue }) =>
              getFieldValue('moderator_type') === 'agent' ? (
                <Form.Item
                  name="moderator_id"
                  label="主持人代理"
                  rules={[{ required: true, message: '请选择主持人代理' }]}
                >
                  <Select placeholder="选择一个代理作为主持人">
                    {agents.map(agent => (
                      <Option key={agent.id} value={agent.id}>
                        {agent.name} ({agent.role.name})
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              ) : null
            }
          </Form.Item>

          <Form.Item
            name="discussion_style"
            label="讨论风格"
            initialValue="formal"
          >
            <Select>
              <Option value="formal">正式</Option>
              <Option value="casual">轻松</Option>
              <Option value="debate">辩论式</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="agenda"
            label="初始议题（可选）"
          >
            <Select
              mode="tags"
              placeholder="输入议题并按回车添加"
              tokenSeparators={[',']}
            />
          </Form.Item>

          <Form.Item
            name="speaking_order"
            label="发言顺序"
            initialValue="sequential"
          >
            <Select>
              <Option value="sequential">顺序发言</Option>
              <Option value="random">随机发言</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="max_rounds"
            label="最大轮次（可选）"
          >
            <Input type="number" placeholder="不限制轮次" />
          </Form.Item>

          <Form.Item
            name="max_message_length"
            label="最大消息长度（可选）"
          >
            <Input type="number" placeholder="不限制长度" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default MeetingList
