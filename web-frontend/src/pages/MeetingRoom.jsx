import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Card, Button, Input, Space, message, Tag, Badge, 
  Spin, Empty, Popconfirm, Select, Divider, Switch, Modal, Form, List, Checkbox 
} from 'antd'
import { 
  SendOutlined, PlayCircleOutlined, PauseCircleOutlined, 
  StopOutlined, DownloadOutlined, ArrowLeftOutlined, PlusOutlined, 
  DeleteOutlined, CheckCircleOutlined, EditOutlined, HistoryOutlined 
} from '@ant-design/icons'
import { meetingsAPI } from '../api/client'
import MarkdownMessage from '../components/MarkdownMessage'

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
  const [markdownEnabled, setMarkdownEnabled] = useState(true)
  const [agentColors, setAgentColors] = useState({})
  const [agendaModalVisible, setAgendaModalVisible] = useState(false)
  const [agendaForm] = Form.useForm()
  const [minutesModalVisible, setMinutesModalVisible] = useState(false)
  const [minutesEditModalVisible, setMinutesEditModalVisible] = useState(false)
  const [minutesHistoryModalVisible, setMinutesHistoryModalVisible] = useState(false)
  const [minutesForm] = Form.useForm()
  const [minutesHistory, setMinutesHistory] = useState([])
  const [generatingMinutes, setGeneratingMinutes] = useState(false)
  const [showMentionSuggestions, setShowMentionSuggestions] = useState(false)
  const [mentionSuggestions, setMentionSuggestions] = useState([])
  const [mentionSearchText, setMentionSearchText] = useState('')
  const [autoResponseEnabled, setAutoResponseEnabled] = useState(false)
  const [streamingEnabled, setStreamingEnabled] = useState(true)  // 默认打开流式输出
  const [streamingMessage, setStreamingMessage] = useState(null)
  const messagesEndRef = useRef(null)
  const wsRef = useRef(null)
  const textAreaRef = useRef(null)
  
  // 为代理分配颜色的调色板（柔和的颜色）
  const colorPalette = [
    { bg: '#e3f2fd', border: '#2196f3', tag: 'blue' },      // 蓝色
    { bg: '#f3e5f5', border: '#9c27b0', tag: 'purple' },    // 紫色
    { bg: '#e8f5e9', border: '#4caf50', tag: 'green' },     // 绿色
    { bg: '#fff3e0', border: '#ff9800', tag: 'orange' },    // 橙色
    { bg: '#fce4ec', border: '#e91e63', tag: 'magenta' },   // 品红
    { bg: '#e0f2f1', border: '#009688', tag: 'cyan' },      // 青色
    { bg: '#f1f8e9', border: '#8bc34a', tag: 'lime' },      // 青柠
    { bg: '#fff9c4', border: '#fbc02d', tag: 'gold' },      // 金色
    { bg: '#ede7f6', border: '#673ab7', tag: 'geekblue' },  // 极客蓝
    { bg: '#fbe9e7', border: '#ff5722', tag: 'volcano' },   // 火山红
  ]
  
  // 为代理分配颜色
  const getAgentColor = (agentId) => {
    if (!agentColors[agentId] && meeting) {
      const newColors = { ...agentColors }
      meeting.participants.forEach((participant, index) => {
        if (!newColors[participant.id]) {
          newColors[participant.id] = colorPalette[index % colorPalette.length]
        }
      })
      setAgentColors(newColors)
      return newColors[agentId] || colorPalette[0]
    }
    return agentColors[agentId] || colorPalette[0]
  }

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

  useEffect(() => {
    // 流式消息更新时也滚动到底部
    if (streamingMessage) {
      scrollToBottom()
    }
  }, [streamingMessage])

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
      } else if (data.type === 'minutes_generated') {
        message.success('✅ 会议纪要已自动生成')
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
  
  const handleRequestAgentById = async (agentId, useAutoResponse = false) => {
    console.log(`[Meeting Room] Requesting agent response: agentId=${agentId}, meetingId=${meetingId}`)
    console.log(`[Meeting Room] autoResponse=${useAutoResponse}, autoResponseEnabled=${autoResponseEnabled}, streamingEnabled=${streamingEnabled}`)
    const startTime = Date.now()
    const hideLoading = message.loading('正在请求 AI 响应，请稍候...', 0)
    
    try {
      console.log('[Meeting Room] Sending request to API...')
      
      // 优先级：流式输出 > 自动响应 > 普通
      // 这样用户可以看到流式效果
      if (streamingEnabled) {
        // 使用流式响应
        console.log('[Meeting Room] Using streaming endpoint')
        await handleStreamingResponse(agentId)
        hideLoading()
        
        // 如果同时启用了自动响应，在流式完成后检查是否有 @ 提及
        if (autoResponseEnabled) {
          const meeting = await meetingsAPI.get(meetingId)
          const lastMessage = meeting.data.messages[meeting.data.messages.length - 1]
          if (lastMessage && lastMessage.mentions && lastMessage.mentions.length > 0) {
            console.log('[Meeting Room] Auto-response enabled, checking mentions...')
            for (const mention of lastMessage.mentions) {
              const mentionedAgent = meeting.data.participants.find(p => p.id === mention.mentioned_participant_id)
              if (mentionedAgent) {
                console.log(`[Meeting Room] Auto-requesting mentioned agent: ${mentionedAgent.name}`)
                await handleRequestAgentById(mentionedAgent.id)
              }
            }
          }
        }
      } else if (useAutoResponse || autoResponseEnabled) {
        // 使用自动响应端点
        console.log('[Meeting Room] Using auto-response endpoint')
        await meetingsAPI.requestAgentWithAutoResponse(meetingId, agentId)
        const duration = ((Date.now() - startTime) / 1000).toFixed(2)
        console.log(`[Meeting Room] ✅ Auto-response chain completed in ${duration}s`)
        
        hideLoading()
        message.success(`自动响应链已完成 (${duration}秒)`)
      } else {
        // 普通响应
        console.log('[Meeting Room] Using normal endpoint')
        await meetingsAPI.requestAgent(meetingId, agentId)
        const duration = ((Date.now() - startTime) / 1000).toFixed(2)
        console.log(`[Meeting Room] ✅ Agent response received in ${duration}s`)
        
        hideLoading()
        message.success(`代理响应已接收 (${duration}秒)`)
      }
      
      // 立即刷新会议数据
      console.log('[Meeting Room] Reloading meeting data...')
      await loadMeeting()
    } catch (error) {
      const duration = ((Date.now() - startTime) / 1000).toFixed(2)
      console.error(`[Meeting Room] ❌ Request failed after ${duration}s:`, error)
      
      hideLoading()
      const errorMsg = error.response?.data?.detail || error.message || String(error)
      if (errorMsg && (errorMsg.includes('timeout') || errorMsg.includes('超时'))) {
        message.error(`请求超时 (${duration}秒)，AI 服务响应较慢，请稍后重试`, 5)
      } else {
        message.error('请求失败: ' + (errorMsg || '未知错误'), 5)
      }
    }
  }

  const handleStreamingResponse = async (agentId) => {
    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(
        `/api/meetings/${meetingId}/request-stream/${agentId}`
      )
      
      let streamedContent = ''
      let streamedReasoning = ''
      
      // 找到代理信息
      const agent = meeting.participants.find(p => p.id === agentId)
      const agentName = agent ? agent.name : 'AI'
      
      // 创建临时流式消息
      setStreamingMessage({
        id: 'streaming-temp',
        speaker_name: agentName,
        speaker_type: 'agent',
        content: '',
        reasoning_content: '',
        timestamp: new Date().toISOString(),
        isStreaming: true
      })
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'reasoning') {
            // 思考过程
            streamedReasoning += data.content
            setStreamingMessage(prev => ({
              ...prev,
              reasoning_content: streamedReasoning
            }))
            console.log('Streaming reasoning:', data.content)
          } else if (data.type === 'content') {
            // 正文内容
            streamedContent += data.content
            setStreamingMessage(prev => ({
              ...prev,
              content: streamedContent
            }))
            console.log('Streaming content:', data.content)
          } else if (data.type === 'complete') {
            console.log('Streaming complete')
            // 清除临时消息
            setStreamingMessage(null)
            eventSource.close()
            resolve()
          } else if (data.type === 'error') {
            console.error('Streaming error:', data.error)
            setStreamingMessage(null)
            eventSource.close()
            reject(new Error(data.error))
          }
        } catch (error) {
          console.error('Failed to parse streaming data:', error)
        }
      }
      
      eventSource.onerror = (error) => {
        console.error('EventSource error:', error)
        eventSource.close()
        reject(error)
      }
    })
  }

  const handleRequestAgent = async () => {
    if (!selectedAgent) {
      message.warning('请选择一个代理')
      return
    }

    setSending(true)
    try {
      // 使用 handleRequestAgentById 以支持流式输出和自动响应
      await handleRequestAgentById(selectedAgent)
      message.success('代理响应已接收')
      setSelectedAgent(null)
    } catch (error) {
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
        
        // 使用 handleRequestAgentById 以支持流式输出和自动响应
        await handleRequestAgentById(participant.id)
        
        const agentDuration = ((Date.now() - agentStartTime) / 1000).toFixed(2)
        console.log(`[Meeting Room] ${participant.name} completed in ${agentDuration}s`)
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

  const handleAddAgenda = async (values) => {
    try {
      await meetingsAPI.addAgenda(meetingId, {
        title: values.title,
        description: values.description || '',
      })
      message.success('议题已添加')
      setAgendaModalVisible(false)
      agendaForm.resetFields()
      loadMeeting()
    } catch (error) {
      message.error('添加失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleCompleteAgenda = async (itemId) => {
    try {
      await meetingsAPI.completeAgenda(meetingId, itemId)
      message.success('议题已标记为完成')
      loadMeeting()
    } catch (error) {
      message.error('操作失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleRemoveAgenda = async (itemId) => {
    try {
      await meetingsAPI.removeAgenda(meetingId, itemId)
      message.success('议题已删除')
      loadMeeting()
    } catch (error) {
      message.error('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const isUserModerator = () => {
    return meeting?.moderator_type === 'user'
  }

  const highlightMentions = (content) => {
    if (!content) return content
    
    // Replace @mentions with highlighted spans
    const mentionPattern = /@(\S+)/g
    const parts = []
    let lastIndex = 0
    let match
    
    while ((match = mentionPattern.exec(content)) !== null) {
      // Add text before mention
      if (match.index > lastIndex) {
        parts.push(content.substring(lastIndex, match.index))
      }
      
      // Add highlighted mention
      parts.push(
        <span 
          key={match.index}
          style={{ 
            backgroundColor: '#fff3cd',
            color: '#856404',
            padding: '2px 4px',
            borderRadius: '3px',
            fontWeight: 'bold'
          }}
        >
          {match[0]}
        </span>
      )
      
      lastIndex = match.index + match[0].length
    }
    
    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(content.substring(lastIndex))
    }
    
    return parts.length > 0 ? parts : content
  }

  const handleMessageChange = (e) => {
    const value = e.target.value
    setUserMessage(value)
    
    // Check for @ mention trigger
    const cursorPos = e.target.selectionStart
    const textBeforeCursor = value.substring(0, cursorPos)
    const lastAtIndex = textBeforeCursor.lastIndexOf('@')
    
    if (lastAtIndex !== -1) {
      const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1)
      
      // Check if we're still in a mention (no space after @)
      if (!textAfterAt.includes(' ') && textAfterAt.length >= 0) {
        const searchText = textAfterAt.toLowerCase()
        setMentionSearchText(searchText)
        
        // Filter participants
        const filtered = meeting.participants.filter(p => 
          p.name.toLowerCase().includes(searchText) || 
          p.role_name.toLowerCase().includes(searchText)
        )
        
        setMentionSuggestions(filtered)
        setShowMentionSuggestions(filtered.length > 0)
        return
      }
    }
    
    setShowMentionSuggestions(false)
  }

  const handleSelectMention = (participant) => {
    const cursorPos = textAreaRef.current.resizableTextArea.textArea.selectionStart
    const textBeforeCursor = userMessage.substring(0, cursorPos)
    const textAfterCursor = userMessage.substring(cursorPos)
    const lastAtIndex = textBeforeCursor.lastIndexOf('@')
    
    const newMessage = 
      userMessage.substring(0, lastAtIndex) + 
      `@${participant.name} ` + 
      textAfterCursor
    
    setUserMessage(newMessage)
    setShowMentionSuggestions(false)
    
    // Focus back on textarea
    setTimeout(() => {
      textAreaRef.current.resizableTextArea.textArea.focus()
    }, 0)
  }

  const handleGenerateMinutes = async (agentId = null) => {
    setGeneratingMinutes(true)
    const hideLoading = message.loading('正在生成会议纪要...', 0)
    try {
      await meetingsAPI.generateMinutes(meetingId, agentId)
      hideLoading()
      message.success('会议纪要已生成')
      loadMeeting()
      setMinutesModalVisible(false)
    } catch (error) {
      hideLoading()
      message.error('生成失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setGeneratingMinutes(false)
    }
  }

  const handleViewMinutes = () => {
    if (meeting.current_minutes) {
      minutesForm.setFieldsValue({
        content: meeting.current_minutes.content
      })
      setMinutesEditModalVisible(true)
    }
  }

  const handleUpdateMinutes = async (values) => {
    try {
      await meetingsAPI.updateMinutes(meetingId, values.content, 'user')
      message.success('会议纪要已更新')
      setMinutesEditModalVisible(false)
      loadMeeting()
    } catch (error) {
      message.error('更新失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleViewMinutesHistory = async () => {
    try {
      const response = await meetingsAPI.getMinutesHistory(meetingId)
      setMinutesHistory(response.data)
      setMinutesHistoryModalVisible(true)
    } catch (error) {
      message.error('加载历史失败: ' + (error.response?.data?.detail || error.message))
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

      </Card>

      <Card title="会议信息" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div>
            <strong>主持人：</strong>
            <Tag color="gold" style={{ marginLeft: 8 }}>
              {meeting.moderator_type === 'user' 
                ? '用户' 
                : meeting.participants.find(p => p.id === meeting.moderator_id)?.name || '未知'}
            </Tag>
          </div>

          <div>
            <strong>参与者：</strong>
            <div style={{ marginTop: 8 }}>
              {meeting.participants.map(p => {
                const color = getAgentColor(p.id)
                const isModerator = meeting.moderator_type === 'agent' && p.id === meeting.moderator_id
                return (
                  <div 
                    key={p.id}
                    style={{ 
                      marginBottom: '8px',
                      padding: '8px 12px',
                      background: color?.bg || '#f5f5f5',
                      borderLeft: `4px solid ${color?.border}`,
                      borderRadius: '4px'
                    }}
                  >
                    <Space>
                      <span style={{ 
                        display: 'inline-block',
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        backgroundColor: color?.border
                      }} />
                      <span style={{ fontWeight: 'bold' }}>{p.name}</span>
                      {isModerator && <Tag color="gold">主持人 👑</Tag>}
                    </Space>
                    <div style={{ marginTop: 4, fontSize: '12px', color: '#666' }}>
                      角色: {p.role_name}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {meeting.discussion_style && (
            <div>
              <strong>讨论风格：</strong>
              <Tag color="blue" style={{ marginLeft: 8 }}>
                {meeting.discussion_style === 'formal' && '正式'}
                {meeting.discussion_style === 'casual' && '轻松'}
                {meeting.discussion_style === 'debate' && '辩论式'}
              </Tag>
            </div>
          )}

          <Divider style={{ margin: '12px 0' }} />

          <div>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>
                  <strong>🔄 自动持续对话</strong>
                  <span style={{ marginLeft: 8, fontSize: '12px', color: '#666' }}>
                    (AI @ AI 时自动触发响应)
                  </span>
                </span>
                <Switch 
                  checked={autoResponseEnabled} 
                  onChange={setAutoResponseEnabled}
                  checkedChildren="开启"
                  unCheckedChildren="关闭"
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>
                  <strong>⚡ 流式输出</strong>
                  <span style={{ marginLeft: 8, fontSize: '12px', color: '#666' }}>
                    (实时显示 AI 回复)
                  </span>
                </span>
                <Switch 
                  checked={streamingEnabled} 
                  onChange={setStreamingEnabled}
                  checkedChildren="开启"
                  unCheckedChildren="关闭"
                />
              </div>
              {autoResponseEnabled && streamingEnabled && (
                <div style={{ 
                  padding: '8px 12px', 
                  background: '#e6f7ff', 
                  borderLeft: '3px solid #1890ff',
                  borderRadius: '4px',
                  fontSize: '12px',
                  color: '#666'
                }}>
                  💡 提示：两个功能都已开启，将优先使用流式输出，并在完成后自动触发被 @ 的代理
                </div>
              )}
            </Space>
          </div>

          {meeting.speaking_length_preferences && Object.keys(meeting.speaking_length_preferences).length > 0 && (
            <div>
              <strong>发言长度偏好：</strong>
              <div style={{ marginTop: 8 }}>
                {Object.entries(meeting.speaking_length_preferences).map(([participantId, preference]) => {
                  const participant = meeting.participants.find(p => p.id === participantId)
                  if (!participant) return null
                  
                  const preferenceText = {
                    brief: '简短',
                    moderate: '中等',
                    detailed: '详细'
                  }[preference] || preference
                  
                  return (
                    <Tag key={participantId} style={{ marginBottom: '4px' }}>
                      {participant.name}: {preferenceText}
                    </Tag>
                  )
                })}
              </div>
            </div>
          )}

          {meeting.agenda && meeting.agenda.length > 0 && (
            <div>
              <strong>当前议题：</strong>
              <div style={{ marginTop: 8 }}>
                {meeting.agenda.filter(a => !a.completed).map(item => (
                  <Tag key={item.id} color="orange" style={{ marginBottom: '4px' }}>
                    {item.title}
                  </Tag>
                ))}
                {meeting.agenda.filter(a => !a.completed).length === 0 && (
                  <span style={{ color: '#999', fontSize: '12px' }}>所有议题已完成</span>
                )}
              </div>
            </div>
          )}

          <div>
            <strong>会议配置：</strong>
            <div style={{ marginTop: 8 }}>
              <Space wrap>
                <Tag>发言顺序: {meeting.speaking_order === 'sequential' ? '顺序' : '随机'}</Tag>
                {meeting.max_rounds && <Tag>最大轮次: {meeting.max_rounds}</Tag>}
                {meeting.max_message_length && <Tag>最大消息长度: {meeting.max_message_length}</Tag>}
              </Space>
            </div>
          </div>
        </Space>
      </Card>

      {meeting.agenda && meeting.agenda.length > 0 && (
        <Card 
          title={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>会议议题 ({meeting.agenda.filter(a => !a.completed).length}/{meeting.agenda.length})</span>
              {isUserModerator() && meeting.status !== 'ended' && (
                <Button 
                  type="primary" 
                  size="small" 
                  icon={<PlusOutlined />}
                  onClick={() => setAgendaModalVisible(true)}
                >
                  添加议题
                </Button>
              )}
            </div>
          }
          style={{ marginBottom: 16 }}
        >
          <List
            dataSource={meeting.agenda}
            renderItem={(item) => (
              <List.Item
                actions={
                  isUserModerator() && meeting.status !== 'ended' ? [
                    !item.completed && (
                      <Button
                        type="link"
                        size="small"
                        icon={<CheckCircleOutlined />}
                        onClick={() => handleCompleteAgenda(item.id)}
                      >
                        完成
                      </Button>
                    ),
                    <Popconfirm
                      title="确定要删除这个议题吗？"
                      onConfirm={() => handleRemoveAgenda(item.id)}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Button
                        type="link"
                        danger
                        size="small"
                        icon={<DeleteOutlined />}
                      >
                        删除
                      </Button>
                    </Popconfirm>
                  ] : []
                }
              >
                <List.Item.Meta
                  avatar={
                    <Checkbox checked={item.completed} disabled />
                  }
                  title={
                    <span style={{ textDecoration: item.completed ? 'line-through' : 'none' }}>
                      {item.title}
                    </span>
                  }
                  description={item.description}
                />
              </List.Item>
            )}
          />
        </Card>
      )}

      {(!meeting.agenda || meeting.agenda.length === 0) && isUserModerator() && meeting.status !== 'ended' && (
        <Card style={{ marginBottom: 16, textAlign: 'center' }}>
          <Empty 
            description="暂无议题"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => setAgendaModalVisible(true)}
            >
              添加第一个议题
            </Button>
          </Empty>
        </Card>
      )}

      {meeting.current_minutes && (
        <Card 
          title={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>会议纪要</span>
              <Space>
                <Button 
                  size="small" 
                  icon={<EditOutlined />}
                  onClick={handleViewMinutes}
                >
                  查看/编辑
                </Button>
                <Button 
                  size="small" 
                  icon={<HistoryOutlined />}
                  onClick={handleViewMinutesHistory}
                >
                  历史版本
                </Button>
                {meeting.status !== 'ended' && (
                  <Button 
                    size="small" 
                    type="primary"
                    onClick={() => setMinutesModalVisible(true)}
                  >
                    重新生成
                  </Button>
                )}
              </Space>
            </div>
          }
          style={{ marginBottom: 16 }}
        >
          <div style={{ 
            padding: '12px', 
            background: '#f9f9f9',
            borderRadius: '4px',
            whiteSpace: 'pre-wrap'
          }}>
            <div style={{ marginBottom: 8, color: '#666', fontSize: '12px' }}>
              版本 {meeting.current_minutes.version} · 
              创建于 {new Date(meeting.current_minutes.created_at).toLocaleString('zh-CN')} · 
              创建者: {meeting.current_minutes.created_by === 'user' ? '用户' : 
                meeting.participants.find(p => p.id === meeting.current_minutes.created_by)?.name || '未知'}
            </div>
            <MarkdownMessage content={meeting.current_minutes.summary || meeting.current_minutes.content} />
          </div>
        </Card>
      )}

      {!meeting.current_minutes && meeting.messages.length > 0 && meeting.status !== 'ended' && (
        <Card style={{ marginBottom: 16, textAlign: 'center' }}>
          <Empty 
            description="暂无会议纪要"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => setMinutesModalVisible(true)}
            >
              生成会议纪要
            </Button>
          </Empty>
        </Card>
      )}

      <Card 
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>会议消息 ({meeting.messages?.length || 0})</span>
            <Space>
              <span style={{ fontSize: '14px', fontWeight: 'normal' }}>Markdown 渲染</span>
              <Switch 
                checked={markdownEnabled} 
                onChange={setMarkdownEnabled}
                size="small"
              />
            </Space>
          </div>
        }
        style={{ marginBottom: 16 }}
        bodyStyle={{ maxHeight: '500px', overflowY: 'auto' }}
      >
        {!meeting.messages || meeting.messages.length === 0 ? (
          <Empty description="暂无消息" />
        ) : (
          <div>
            {meeting.messages.map((msg, index) => {
              const isUser = msg.speaker_type === 'user'
              const agentColor = isUser ? null : getAgentColor(msg.speaker_id)
              const isModerator = !isUser && meeting.moderator_type === 'agent' && msg.speaker_id === meeting.moderator_id
              
              return (
                <div key={msg.id || index} style={{ marginBottom: 16 }}>
                  <div style={{ marginBottom: 4 }}>
                    <Tag color={isUser ? 'green' : agentColor?.tag}>
                      {msg.speaker_name}
                      {isModerator && ' 👑'}
                    </Tag>
                    <span style={{ color: '#999', fontSize: '12px' }}>
                      轮次 {msg.round_number} · {new Date(msg.timestamp).toLocaleString('zh-CN')}
                    </span>
                    {msg.mentions && msg.mentions.length > 0 && (
                      <span style={{ marginLeft: 8 }}>
                        {msg.mentions.map((mention, i) => (
                          <Tag key={i} color="orange" style={{ fontSize: '11px' }}>
                            @{mention.mentioned_participant_name}
                          </Tag>
                        ))}
                      </span>
                    )}
                  </div>
                  <div style={{ 
                    padding: '12px', 
                    background: isUser ? '#f0f9ff' : agentColor?.bg || '#f5f5f5',
                    borderLeft: isUser ? '4px solid #52c41a' : `4px solid ${agentColor?.border || '#999'}`,
                    borderRadius: '4px',
                    whiteSpace: markdownEnabled ? 'normal' : 'pre-wrap'
                  }}>
                    {markdownEnabled ? (
                      <MarkdownMessage 
                        content={msg.content} 
                        reasoningContent={msg.reasoning_content}
                      />
                    ) : (
                      <div>{highlightMentions(msg.content)}</div>
                    )}
                  </div>
                </div>
              )
            })}
            
            {/* 显示流式消息 */}
            {streamingMessage && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ marginBottom: 4 }}>
                  <Tag color="processing">
                    {streamingMessage.speaker_name} ⚡
                  </Tag>
                  <span style={{ color: '#999', fontSize: '12px' }}>
                    正在输入...
                  </span>
                </div>
                <div style={{ 
                  padding: '12px', 
                  background: '#e6f7ff',
                  borderLeft: '4px solid #1890ff',
                  borderRadius: '4px',
                  animation: 'pulse 1.5s ease-in-out infinite'
                }}>
                  {markdownEnabled ? (
                    <MarkdownMessage 
                      content={streamingMessage.content} 
                      reasoningContent={streamingMessage.reasoning_content}
                    />
                  ) : (
                    <>
                      {streamingMessage.reasoning_content && (
                        <div style={{ 
                          marginBottom: '8px', 
                          padding: '8px', 
                          background: '#f8f9fa',
                          borderRadius: '4px',
                          color: '#666',
                          fontSize: '13px'
                        }}>
                          💭 {streamingMessage.reasoning_content}
                        </div>
                      )}
                      <div style={{ whiteSpace: 'pre-wrap' }}>
                        {streamingMessage.content}
                      </div>
                    </>
                  )}
                  <span style={{ 
                    display: 'inline-block',
                    width: '8px',
                    height: '16px',
                    background: '#1890ff',
                    marginLeft: '2px',
                    animation: 'blink 1s step-end infinite'
                  }} />
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </Card>

      {meeting.status !== 'ended' && (
        <Card title="发送消息">
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ marginBottom: '8px' }}>
              <span style={{ color: '#666', fontSize: '12px' }}>快速 @: </span>
              {meeting.participants.map(p => {
                const color = getAgentColor(p.id)
                return (
                  <Tag 
                    key={p.id}
                    color={color?.tag}
                    style={{ 
                      cursor: 'pointer', 
                      marginBottom: '4px',
                      borderLeft: `3px solid ${color?.border}`,
                      paddingLeft: '8px'
                    }}
                    onClick={() => setUserMessage(prev => prev + `@${p.name} `)}
                  >
                    @{p.name}
                  </Tag>
                )
              })}
            </div>
            <div style={{ position: 'relative' }}>
              <TextArea
                ref={textAreaRef}
                rows={4}
                value={userMessage}
                onChange={handleMessageChange}
                placeholder="输入你的消息... (输入 @ 可以提及代理)"
                disabled={meeting.status !== 'active'}
                onPressEnter={(e) => {
                  if (e.ctrlKey || e.metaKey) {
                    handleSendMessage('none')
                  }
                }}
              />
              {showMentionSuggestions && (
                <div style={{
                  position: 'absolute',
                  bottom: '100%',
                  left: 0,
                  right: 0,
                  backgroundColor: 'white',
                  border: '1px solid #d9d9d9',
                  borderRadius: '4px',
                  maxHeight: '200px',
                  overflowY: 'auto',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                  zIndex: 1000,
                  marginBottom: '4px'
                }}>
                  {mentionSuggestions.map(p => {
                    const color = getAgentColor(p.id)
                    return (
                      <div
                        key={p.id}
                        onClick={() => handleSelectMention(p)}
                        style={{
                          padding: '8px 12px',
                          cursor: 'pointer',
                          borderBottom: '1px solid #f0f0f0',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
                      >
                        <span style={{ 
                          display: 'inline-block',
                          width: '8px',
                          height: '8px',
                          borderRadius: '50%',
                          backgroundColor: color?.border
                        }} />
                        <span style={{ fontWeight: 'bold' }}>{p.name}</span>
                        <span style={{ color: '#999', fontSize: '12px' }}>({p.role_name})</span>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
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

      <Modal
        title="添加议题"
        open={agendaModalVisible}
        onCancel={() => {
          setAgendaModalVisible(false)
          agendaForm.resetFields()
        }}
        onOk={() => agendaForm.submit()}
      >
        <Form form={agendaForm} layout="vertical" onFinish={handleAddAgenda}>
          <Form.Item
            name="title"
            label="议题标题"
            rules={[{ required: true, message: '请输入议题标题' }]}
          >
            <Input placeholder="例如：讨论产品定位" />
          </Form.Item>
          <Form.Item
            name="description"
            label="议题描述（可选）"
          >
            <Input.TextArea 
              rows={3} 
              placeholder="详细描述这个议题的内容和目标"
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="生成会议纪要"
        open={minutesModalVisible}
        onCancel={() => setMinutesModalVisible(false)}
        footer={null}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button
            type="primary"
            block
            loading={generatingMinutes}
            onClick={() => handleGenerateMinutes(null)}
          >
            使用系统默认方式生成
          </Button>
          <Divider>或选择特定代理生成</Divider>
          <Select
            style={{ width: '100%' }}
            placeholder="选择一个代理来生成纪要"
            onChange={(agentId) => handleGenerateMinutes(agentId)}
            disabled={generatingMinutes}
          >
            {meeting?.participants.map(p => (
              <Option key={p.id} value={p.id}>
                {p.name} ({p.role_name})
              </Option>
            ))}
          </Select>
        </Space>
      </Modal>

      <Modal
        title="编辑会议纪要"
        open={minutesEditModalVisible}
        onCancel={() => {
          setMinutesEditModalVisible(false)
          minutesForm.resetFields()
        }}
        onOk={() => minutesForm.submit()}
        width={800}
      >
        <Form form={minutesForm} layout="vertical" onFinish={handleUpdateMinutes}>
          <Form.Item
            name="content"
            label="纪要内容"
            rules={[{ required: true, message: '请输入纪要内容' }]}
          >
            <Input.TextArea 
              rows={15} 
              placeholder="编辑会议纪要内容..."
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="会议纪要历史"
        open={minutesHistoryModalVisible}
        onCancel={() => setMinutesHistoryModalVisible(false)}
        footer={null}
        width={800}
      >
        <List
          dataSource={minutesHistory}
          renderItem={(item) => (
            <List.Item>
              <List.Item.Meta
                title={
                  <Space>
                    <Tag color="blue">版本 {item.version}</Tag>
                    <span style={{ fontSize: '12px', color: '#666' }}>
                      {new Date(item.created_at).toLocaleString('zh-CN')}
                    </span>
                    <span style={{ fontSize: '12px', color: '#666' }}>
                      创建者: {item.created_by === 'user' ? '用户' : 
                        meeting?.participants.find(p => p.id === item.created_by)?.name || '未知'}
                    </span>
                  </Space>
                }
                description={
                  <div style={{ 
                    marginTop: 8,
                    padding: '12px', 
                    background: '#f9f9f9',
                    borderRadius: '4px',
                    whiteSpace: 'pre-wrap'
                  }}>
                    <MarkdownMessage content={item.summary || item.content} />
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </Modal>
    </div>
  )
}

export default MeetingRoom
