import { Card, Row, Col, Statistic, Button } from 'antd'
import { TeamOutlined, CommentOutlined, RocketOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { agentsAPI, meetingsAPI } from '../api/client'

function Home() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({ agents: 0, meetings: 0, activeMeetings: 0 })

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const [agentsRes, meetingsRes] = await Promise.all([
        agentsAPI.list(),
        meetingsAPI.list()
      ])
      const activeMeetings = meetingsRes.data.filter(m => m.status === 'active').length
      setStats({
        agents: agentsRes.data.length,
        meetings: meetingsRes.data.length,
        activeMeetings
      })
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
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
