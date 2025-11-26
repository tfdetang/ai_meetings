import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Card, Button, Input, Space, message, Tag, Badge, 
  Spin, Empty, Popconfirm, Select, Divider 
} from 'antd'
import { 
  SendOutlined, PlayCircleOutlined, PauseCircleOutlined, 
  StopOutlined, DownloadOutlined, ArrowLeftOutlined 
} from '@ant-design/icons'
import { meetingsAPI } from '../api/client'

const { TextArea } = Input
const { Option } = Select

function MeetingRoom() {
  const { meetingId } = useParams()
  const navigate = useNavigate()
  const [meeting, setMeeting] = useState(null)
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [userMessage, setUserMessage] = useState('')
  const [selectedAgent, setSelectedAgent] = useState(null)
  const messagesEndRef = useRef(null)
  const wsRef = useRef(null)

  useEffect(() => {
    loadMeeting()
    connectWebSocket()
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [meetingId])

  useEffect(() => {
    scrollToBottom()
  }, [meeting?.messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/meetings/${meetingId}`)
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'new_message' || data.type === 'status_change') {
        loadMeeting()
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    wsRef.current = ws
  }

  const loadMeeting = async () => {
    try {
      const response = await meetingsAPI.get(meetingId)
      console.log('Loaded meeting data:', response.data)
      console.log('Messages count:', response.data.messages?.length || 0)
      setMeeting(response.data)
    } catch (error) {
      console.error('Failed to load meeting:', error)
      message.error('加载会议失败')
      navigate('/meetings')
    } finally {
      setLoading(false)
    }
  }

  const handleStart = async () => {
    try {
      await meetingsAPI.start(meetingId)
      message.success('会议已开始')
      loadMeeting()
    } catch (error) {
      message.error('操作失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handlePause = async () => {
    try {
      await meetingsAPI.pause(meetingId)
      message.success('会议已暂停')
      loadMeeting()
    } catch (error) {
      message.error('操作失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleEnd = async () => {
    try {
      await meetingsAPI.end(meetingId)
      message.success('会议已结束')
      loadMeeting()
    } catch (error) {
      message.error('操作失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleSendMessage = async (mode = 'none') => {
    if (!userMessage.trim()) {
      message.warning('请输入消息内容')
      return
    }

    console.log(`[Meeting Room] Sending user message (mode=${mode}):`, userMessage.substring(0, 50) + '...')
    setSending(true)
    
    try {
      await meetingsAPI.sendMessage(meetingId, userMessage)
      console.log('[Meeting Room] ✅ User message sent')
      
      const messageContent = userMessage
      setUserMessage('')
      message.success('消息已发送')
      
      // 立即刷新会议数据
      await loadMeeting()
      
      // 根据模式处理 AI 响应
      if (mode === 'mention') {
        // 检查消息中是否有 @提及
        const mentionedAgents = findMentionedAgents(messageContent, meeting.participants)
        
        if (mentionedAgents.length > 0) {
          console.log(`[Meeting Room] Found ${mentionedAgents.length} mentioned agents`)
          message.info(`正在请求被 @ 的代理响应 (${mentionedAgents.length} 个)...`)
          
          for (const agent of mentionedAgents) {
            console.log(`[Meeting Room] Requesting mentioned agent: ${agent.name}`)
            await handleRequestAgentById(agent.id)
          }
        } else {
          message.warning('未检测到 @提及，请使用 @代理名 来指定发言者')
        }
      } else if (mode === 'all') {
        // 让所有代理响应
        console.log(`[Meeting Room] Requesting all ${meeting.participants.length} agents`)
        message.info(`正在请求所有代理响应 (${meeting.participants.length} 个)...`)
        
        for (const participant of meeting.participants) {
          await handleRequestAgentById(participant.id)
        }
      }
    } catch (error) {
      console.error('[Meeting Room] ❌ Failed to send message:', error)
      message.error('发送失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSending(false)
    }
  }
  
  const findMentionedAgents = (messageContent, participants) => {
    const mentioned = []
    
    for (const participant of participants) {
      // 检查是否有 @代理名 或 @角色名
      const patterns = [
        `@${participant.name}`,
        `@ ${participant.name}`,
        `@${participant.role_name}`,
        `@ ${participant.role_name}`,
      ]
      
      for (const pattern of patterns) {
        if (messageContent.includes(pattern)) {
          if (!mentioned.find(a => a.id === participant.id)) {
            mentioned.push(participant)
          }
          break
        }
      }
    }
    
    return mentioned
  }
  
  const handleRequestAgentById = async (agentId) => {
    console.log(`[Meeting Room] Requesting agent response: agentId=${agentId}, meetingId=${meetingId}`)
    const startTime = Date.now()
    const hideLoading = message.loading('正在请求 AI 响应，请稍候...', 0)
    
    try {
      console.log('[Meeting Room] Sending request to API...')
      await meetingsAPI.requestAgent(meetingId, agentId)
      const duration = ((Date.now() - startTime) / 1000).toFixed(2)
      console.log(`[Meeting Room] ✅ Agent response received in ${duration}s`)
      
      hideLoading()
      message.success(`代理响应已接收 (${duration}秒)`)
      
      // 立即刷新会议数据
      console.log('[Meeting Room] Reloading meeting data...')
      await loadMeeting()
    } catch (error) {
      const duration = ((Date.now() - startTime) / 1000).toFixed(2)
      console.error(`[Meeting Room] ❌ Request failed after ${duration}s:`, error)
      
      hideLoading()
      const errorMsg = error.response?.data?.detail || error.message
      if (errorMsg.includes('timeout') || errorMsg.includes('超时')) {
        message.error(`请求超时 (${duration}秒)，AI 服务响应较慢，请稍后重试`, 5)
      } else {
        message.error('请求失败: ' + errorMsg, 5)
      }
    }
  }

  const handleRequestAgent = async () => {
    if (!selectedAgent) {
      message.warning('请选择一个代理')
      return
    }

    setSending(true)
    const hideLoading = message.loading('正在请求 AI 响应，请稍候...', 0)
    try {
      await meetingsAPI.requestAgent(meetingId, selectedAgent)
      hideLoading()
      message.success('代理响应已接收')
      setSelectedAgent(null)
      // 立即刷新会议数据
      await loadMeeting()
    } catch (error) {
      hideLoading()
      const errorMsg = error.response?.data?.detail || error.message
      if (errorMsg.includes('timeout') || errorMsg.includes('超时')) {
        message.error('请求超时，AI 服务响应较慢，请稍后重试', 5)
      } else {
        message.error('请求失败: ' + errorMsg, 5)
      }
    } finally {
      setSending(false)
    }
  }
  
  const handleRunRound = async () => {
    if (meeting.participants.length === 0) {
      message.warning('没有参与的代理')
      return
    }
    
    console.log(`[Meeting Room] Starting round with ${meeting.participants.length} participants`)
    const roundStartTime = Date.now()
    
    setSending(true)
    const hideLoading = message.loading(`正在运行一轮讨论 (${meeting.participants.length} 个代理)...`, 0)
    
    try {
      for (let i = 0; i < meeting.participants.length; i++) {
        const participant = meeting.participants[i]
        console.log(`[Meeting Room] Agent ${i + 1}/${meeting.participants.length}: ${participant.name}`)
        
        message.info(`${participant.name} 正在发言... (${i + 1}/${meeting.participants.length})`)
        const agentStartTime = Date.now()
        
        await meetingsAPI.requestAgent(meetingId, participant.id)
        
        const agentDuration = ((Date.now() - agentStartTime) / 1000).toFixed(2)
        console.log(`[Meeting Room] ${participant.name} completed in ${agentDuration}s`)
        
        await loadMeeting()
      }
      
      const totalDuration = ((Date.now() - roundStartTime) / 1000).toFixed(2)
      console.log(`[Meeting Room] ✅ Round completed in ${totalDuration}s`)
      
      hideLoading()
      message.success(`一轮讨论完成！(总计 ${totalDuration}秒)`)
    } catch (error) {
      const totalDuration = ((Date.now() - roundStartTime) / 1000).toFixed(2)
      console.error(`[Meeting Room] ❌ Round failed after ${totalDuration}s:`, error)
      
      hideLoading()
      const errorMsg = error.response?.data?.detail || error.message
      message.error('运行失败: ' + errorMsg, 5)
    } finally {
      setSending(false)
    }
  }

  const handleExport = async (format) => {
    try {
      const response = format === 'markdown' 
        ? await meetingsAPI.exportMarkdown(meetingId)
        : await meetingsAPI.exportJson(meetingId)
      
      const content = response.data.content
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `meeting_${meetingId}.${format === 'markdown' ? 'md' : 'json'}`
      a.click()
      URL.revokeObjectURL(url)
      message.success('导出成功')
    } catch (error) {
      message.error('导出失败')
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

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!meeting) {
    return <Empty description="会议不存在" />
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Button 
        icon={<ArrowLeftOutlined />} 
        onClick={() => navigate('/meetings')}
        style={{ marginBottom: 16 }}
      >
        返回列表
      </Button>

      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: 0 }}>{meeting.topic}</h2>
            <Space style={{ marginTop: 8 }}>
              {getStatusBadge(meeting.status)}
              <Tag>轮次: {meeting.current_round}{meeting.max_rounds ? `/${meeting.max_rounds}` : ''}</Tag>
              <Tag>消息: {meeting.messages.length}</Tag>
            </Space>
          </div>
          <Space>
            {meeting.status === 'active' && (
              <Button icon={<PauseCircleOutlined />} onClick={handlePause}>
                暂停
              </Button>
            )}
            {meeting.status === 'paused' && (
              <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleStart}>
                继续
              </Button>
            )}
            {meeting.status !== 'ended' && (
              <Popconfirm
                title="确定要结束会议吗？"
                onConfirm={handleEnd}
                okText="确定"
                cancelText="取消"
              >
                <Button danger icon={<StopOutlined />}>
                  结束
                </Button>
              </Popconfirm>
            )}
            <Button.Group>
              <Button icon={<DownloadOutlined />} onClick={() => handleExport('markdown')}>
                导出 MD
              </Button>
              <Button icon={<DownloadOutlined />} onClick={() => handleExport('json')}>
                导出 JSON
              </Button>
            </Button.Group>
          </Space>
        </div>

        <Divider />

        <div>
          <strong>参与者：</strong>
          <Space style={{ marginLeft: 8 }}>
            {meeting.participants.map(p => (
              <Tag key={p.id} color="blue">{p.name} ({p.role_name})</Tag>
            ))}
          </Space>
        </div>
      </Card>

      <Card 
        title={`会议消息 (${meeting.messages?.length || 0})`}
        style={{ marginBottom: 16 }}
        bodyStyle={{ maxHeight: '500px', overflowY: 'auto' }}
      >
        {!meeting.messages || meeting.messages.length === 0 ? (
          <Empty description="暂无消息" />
        ) : (
          <div>
            {meeting.messages.map((msg, index) => (
              <div key={msg.id || index} style={{ marginBottom: 16 }}>
                <div style={{ marginBottom: 4 }}>
                  <Tag color={msg.speaker_type === 'user' ? 'green' : 'blue'}>
                    {msg.speaker_name}
                  </Tag>
                  <span style={{ color: '#999', fontSize: '12px' }}>
                    轮次 {msg.round_number} · {new Date(msg.timestamp).toLocaleString('zh-CN')}
                  </span>
                </div>
                <div style={{ 
                  padding: '12px', 
                  background: msg.speaker_type === 'user' ? '#f0f9ff' : '#f5f5f5',
                  borderRadius: '4px',
                  whiteSpace: 'pre-wrap'
                }}>
                  {msg.content}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </Card>

      {meeting.status !== 'ended' && (
        <Card title="发送消息">
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ marginBottom: '8px' }}>
              <span style={{ color: '#666', fontSize: '12px' }}>快速 @: </span>
              {meeting.participants.map(p => (
                <Tag 
                  key={p.id}
                  style={{ cursor: 'pointer', marginBottom: '4px' }}
                  onClick={() => setUserMessage(prev => prev + `@${p.name} `)}
                >
                  @{p.name}
                </Tag>
              ))}
            </div>
            <TextArea
              rows={4}
              value={userMessage}
              onChange={(e) => setUserMessage(e.target.value)}
              placeholder="输入你的消息... (可以使用 @代理名 来指定发言者)"
              disabled={meeting.status !== 'active'}
              onPressEnter={(e) => {
                if (e.ctrlKey || e.metaKey) {
                  handleSendMessage('none')
                }
              }}
            />
            <Space wrap>
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={() => handleSendMessage('mention')}
                loading={sending}
                disabled={meeting.status !== 'active'}
              >
                发送并 @ 代理响应
              </Button>
              <Button
                icon={<SendOutlined />}
                onClick={() => handleSendMessage('all')}
                loading={sending}
                disabled={meeting.status !== 'active'}
              >
                发送并请求所有代理
              </Button>
              <Button
                icon={<SendOutlined />}
                onClick={() => handleSendMessage('none')}
                loading={sending}
                disabled={meeting.status !== 'active'}
              >
                仅发送消息
              </Button>
            </Space>
            <div style={{ color: '#999', fontSize: '12px', marginTop: '8px' }}>
              💡 提示：
              <br />
              • 使用 <code>@代理名</code> 在消息中提及代理，然后点击"发送并 @ 代理响应"
              <br />
              • 例如：<code>@游戏策划师 你觉得这个想法怎么样？</code>
              <br />
              • 可以同时 @ 多个代理：<code>@Alice @Bob 你们怎么看？</code>
            </div>

            <Divider>手动控制代理发言</Divider>

            <Space style={{ width: '100%', marginBottom: 16 }}>
              <Button
                type="primary"
                onClick={handleRunRound}
                loading={sending}
                disabled={meeting.status !== 'active'}
                style={{ flex: 1 }}
              >
                🔄 运行一轮 (所有代理依次发言)
              </Button>
            </Space>

            <Space style={{ width: '100%' }}>
              <Select
                style={{ flex: 1, minWidth: 200 }}
                placeholder="选择特定代理发言"
                value={selectedAgent}
                onChange={setSelectedAgent}
                disabled={meeting.status !== 'active'}
              >
                {meeting.participants.map(p => (
                  <Option key={p.id} value={p.id}>
                    {p.name} ({p.role_name})
                  </Option>
                ))}
              </Select>
              <Button
                onClick={handleRequestAgent}
                loading={sending}
                disabled={meeting.status !== 'active'}
              >
                请求发言
              </Button>
            </Space>
          </Space>
        </Card>
      )}
    </div>
  )
}

export default MeetingRoom
