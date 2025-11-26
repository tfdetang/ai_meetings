import { Card, Row, Col, Statistic, Button, List, Empty, Tag, Space } from 'antd'
import { TeamOutlined, CommentOutlined, RocketOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { agentsAPI, meetingsAPI } from '../api/client'

function Home() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({ agents: 0, meetings: 0, activeMeetings: 0 })
  const [activeMeetings, setActiveMeetings] = useState([])

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const [agentsRes, meetingsRes] = await Promise.all([
        agentsAPI.list(),
        meetingsAPI.list()
      ])
      
      // Filter active meetings, sort by updated_at descending, and take top 5
      const activeMeetingsList = meetingsRes.data
        .filter(m => m.status === 'active')
        .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
        .slice(0, 5)
      
      setActiveMeetings(activeMeetingsList)
      setStats({
        agents: agentsRes.data.length,
        meetings: meetingsRes.data.length,
        activeMeetings: activeMeetingsList.length
      })
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const formatTime = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins} 分钟前`
    if (diffHours < 24) return `${diffHours} 小时前`
    if (diffDays < 7) return `${diffDays} 天前`
    return date.toLocaleDateString('zh-CN')
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Card style={{ marginBottom: 24 }}>
        <h1>欢迎使用 AI 代理会议系统</h1>
        <p style={{ fontSize: 16, color: '#666' }}>
          创建 AI 代理，组织虚拟会议，让不同角色的 AI 进行协作讨论
        </p>
      </Card>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="代理总数"
              value={stats.agents}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
            <Button 
              type="link" 
              onClick={() => navigate('/agents')}
              style={{ padding: 0, marginTop: 8 }}
            >
              管理代理 →
            </Button>
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="会议总数"
              value={stats.meetings}
              prefix={<CommentOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <Button 
              type="link" 
              onClick={() => navigate('/meetings')}
              style={{ padding: 0, marginTop: 8 }}
            >
              查看会议 →
            </Button>
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="进行中的会议"
              value={stats.activeMeetings}
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="进行中的会议" style={{ marginBottom: 24 }}>
        {activeMeetings.length === 0 ? (
          <Empty 
            description="暂无进行中的会议" 
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={() => navigate('/meetings')}>
              创建新会议
            </Button>
          </Empty>
        ) : (
          <List
            dataSource={activeMeetings}
            renderItem={(meeting) => (
              <List.Item
                onClick={() => navigate(`/meetings/${meeting.id}`)}
                style={{ cursor: 'pointer', transition: 'background-color 0.2s' }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <List.Item.Meta
                  title={
                    <span style={{ fontSize: '16px', fontWeight: 500 }}>
                      {meeting.topic}
                    </span>
                  }
                  description={
                    <Space size="middle" style={{ marginTop: 8 }}>
                      <Tag color="blue">
                        <TeamOutlined /> {meeting.participants.length} 个代理
                      </Tag>
                      <Tag color="green">
                        <CommentOutlined /> {meeting.messages.length} 条消息
                      </Tag>
                      <span style={{ color: '#999' }}>
                        最后更新: {formatTime(meeting.updated_at)}
                      </span>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      <Card title="快速开始" style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={12}>
            <h3>1. 创建代理</h3>
            <p>首先创建一些 AI 代理，可以使用预设的角色模板（如产品经理、工程师、设计师等）</p>
            <Button type="primary" onClick={() => navigate('/agents')}>
              创建代理
            </Button>
          </Col>
          <Col span={12}>
            <h3>2. 创建会议</h3>
            <p>选择代理参与会议，设置会议主题和规则，开始让 AI 代理们进行讨论</p>
            <Button type="primary" onClick={() => navigate('/meetings')}>
              创建会议
            </Button>
          </Col>
        </Row>
      </Card>

      <Card title="功能特性">
        <Row gutter={16}>
          <Col span={8}>
            <h4>🤖 多供应商支持</h4>
            <p>支持 OpenAI、Anthropic、Google、GLM 等多个 AI 模型供应商</p>
          </Col>
          <Col span={8}>
            <h4>🎭 角色模板</h4>
            <p>内置多种专业角色模板，也可以自定义角色和提示词</p>
          </Col>
          <Col span={8}>
            <h4>💬 实时交互</h4>
            <p>实时查看会议进展，随时加入讨论，请求特定代理发言</p>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default Home
