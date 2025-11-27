import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Card, Button, Input, Space, message, Tag, Badge, 
  Spin, Empty, Popconfirm, Select, Divider, Switch, Modal, Form, List, Checkbox,
  FloatButton, Drawer 
} from 'antd'
import { 
  SendOutlined, PlayCircleOutlined, PauseCircleOutlined, 
  StopOutlined, DownloadOutlined, ArrowLeftOutlined, PlusOutlined, 
  DeleteOutlined, CheckCircleOutlined, EditOutlined, HistoryOutlined,
  DownOutlined, UpOutlined, FileTextOutlined, MenuUnfoldOutlined, 
  MenuFoldOutlined, UnorderedListOutlined, BranchesOutlined 
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
  const [meetingInfoCollapsed, setMeetingInfoCollapsed] = useState(() => {
    // 从 localStorage 读取折叠状态，默认为 false（展开）
    const saved = localStorage.getItem('meetingInfoCollapsed')
    return saved === 'true'
  })
  const [minutesDrawerVisible, setMinutesDrawerVisible] = useState(false)
  const [minutesPromptModalVisible, setMinutesPromptModalVisible] = useState(false)
  const [minutesPromptForm] = Form.useForm()
  const [agendaSidebarCollapsed, setAgendaSidebarCollapsed] = useState(() => {
    // 从 localStorage 读取侧边栏折叠状态，默认为 false（展开）
    const saved = localStorage.getItem('agendaSidebarCollapsed')
    return saved === 'true'
  })
  const [settingsSidebarCollapsed, setSettingsSidebarCollapsed] = useState(() => {
    // 从 localStorage 读取设置侧边栏折叠状态，默认为 true（收起）
    const saved = localStorage.getItem('settingsSidebarCollapsed')
    return saved !== 'false' // 默认收起
  })
  const [generateMindMapWithMinutes, setGenerateMindMapWithMinutes] = useState(false)
  const messagesEndRef = useRef(null)
  const wsRef = useRef(null)
  const textAreaRef = useRef(null)
  const cancelRequestRef = useRef(false) // 用于取消当前请求
  const eventSourceRef = useRef(null) // 用于存储 EventSource 实例
  
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

  useEffect(() => {
    // 持久化折叠状态到 localStorage
    localStorage.setItem('meetingInfoCollapsed', meetingInfoCollapsed)
  }, [meetingInfoCollapsed])

  useEffect(() => {
    // 持久化侧边栏折叠状态到 localStorage
    localStorage.setItem('agendaSidebarCollapsed', agendaSidebarCollapsed)
  }, [agendaSidebarCollapsed])

  useEffect(() => {
    // 持久化设置侧边栏折叠状态到 localStorage
    localStorage.setItem('settingsSidebarCollapsed', settingsSidebarCollapsed)
  }, [settingsSidebarCollapsed])

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
    // 检查是否被取消
    if (cancelRequestRef.current) {
      console.log('[Meeting Room] Request cancelled by user')
      return
    }
    
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
        
        // 检查是否被取消
        if (cancelRequestRef.current) {
          console.log('[Meeting Room] Request cancelled after streaming')
          return
        }
        
        // 如果同时启用了自动响应，在流式完成后检查是否有 @ 提及
        if (autoResponseEnabled) {
          const meeting = await meetingsAPI.get(meetingId)
          const lastMessage = meeting.data.messages[meeting.data.messages.length - 1]
          if (lastMessage && lastMessage.mentions && lastMessage.mentions.length > 0) {
            console.log('[Meeting Room] Auto-response enabled, checking mentions...')
            for (const mention of lastMessage.mentions) {
              // 检查是否被取消
              if (cancelRequestRef.current) {
                console.log('[Meeting Room] Auto-response chain cancelled')
                break
              }
              
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
      
      // 如果是用户取消，不显示错误
      if (error.message === 'Request cancelled by user') {
        message.info('已停止输出')
        return
      }
      
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
      
      // 保存 EventSource 实例以便取消
      eventSourceRef.current = eventSource
      
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
        // 检查是否被取消
        if (cancelRequestRef.current) {
          console.log('Streaming cancelled by user')
          setStreamingMessage(null)
          eventSource.close()
          eventSourceRef.current = null
          reject(new Error('Request cancelled by user'))
          return
        }
        
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
            eventSourceRef.current = null
            resolve()
          } else if (data.type === 'error') {
            console.error('Streaming error:', data.error)
            setStreamingMessage(null)
            eventSource.close()
            eventSourceRef.current = null
            reject(new Error(data.error))
          }
        } catch (error) {
          console.error('Failed to parse streaming data:', error)
        }
      }
      
      eventSource.onerror = (error) => {
        console.error('EventSource error:', error)
        setStreamingMessage(null)
        eventSource.close()
        eventSourceRef.current = null
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
    
    // 重置取消标志
    cancelRequestRef.current = false
    
    setSending(true)
    const hideLoading = message.loading(`正在运行一轮讨论 (${meeting.participants.length} 个代理)...`, 0)
    
    try {
      for (let i = 0; i < meeting.participants.length; i++) {
        // 检查是否被取消
        if (cancelRequestRef.current) {
          console.log('[Meeting Room] Round cancelled by user')
          hideLoading()
          message.info('已停止运行')
          break
        }
        
        const participant = meeting.participants[i]
        console.log(`[Meeting Room] Agent ${i + 1}/${meeting.participants.length}: ${participant.name}`)
        
        message.info(`${participant.name} 正在发言... (${i + 1}/${meeting.participants.length})`)
        const agentStartTime = Date.now()
        
        // 使用 handleRequestAgentById 以支持流式输出和自动响应
        await handleRequestAgentById(participant.id)
        
        const agentDuration = ((Date.now() - agentStartTime) / 1000).toFixed(2)
        console.log(`[Meeting Room] ${participant.name} completed in ${agentDuration}s`)
      }
      
      if (!cancelRequestRef.current) {
        const totalDuration = ((Date.now() - roundStartTime) / 1000).toFixed(2)
        console.log(`[Meeting Room] ✅ Round completed in ${totalDuration}s`)
        
        hideLoading()
        message.success(`一轮讨论完成！(总计 ${totalDuration}秒)`)
      }
    } catch (error) {
      const totalDuration = ((Date.now() - roundStartTime) / 1000).toFixed(2)
      console.error(`[Meeting Room] ❌ Round failed after ${totalDuration}s:`, error)
      
      hideLoading()
      
      // 如果是用户取消，不显示错误
      if (error.message === 'Request cancelled by user') {
        return
      }
      
      const errorMsg = error.response?.data?.detail || error.message
      message.error('运行失败: ' + errorMsg, 5)
    } finally {
      setSending(false)
      cancelRequestRef.current = false
    }
  }
  
  const handleStopOutput = () => {
    console.log('[Meeting Room] Stopping current output...')
    
    // 设置取消标志
    cancelRequestRef.current = true
    
    // 关闭流式连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    
    // 清除流式消息
    setStreamingMessage(null)
    
    // 重置发送状态
    setSending(false)
    
    message.info('正在停止输出...')
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
      
      // 如果选择了同时生成思维导图
      if (generateMindMapWithMinutes) {
        const hideMindMapLoading = message.loading('正在生成思维导图...', 0)
        try {
          await meetingsAPI.generateMindMap(meetingId, agentId)
          hideMindMapLoading()
          message.success('思维导图已生成')
        } catch (mindMapError) {
          hideMindMapLoading()
          message.warning('思维导图生成失败: ' + (mindMapError.response?.data?.detail || mindMapError.message))
        }
      }
      
      loadMeeting()
      setMinutesModalVisible(false)
      setGenerateMindMapWithMinutes(false) // 重置选项
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

  const handleEditMinutesPrompt = () => {
    minutesPromptForm.setFieldsValue({
      minutes_prompt: meeting.config?.minutes_prompt || ''
    })
    setMinutesPromptModalVisible(true)
  }

  const handleUpdateMinutesPrompt = async (values) => {
    try {
      await meetingsAPI.updateConfig(meetingId, {
        minutes_prompt: values.minutes_prompt || null
      })
      message.success('会议纪要提示词已更新')
      setMinutesPromptModalVisible(false)
      loadMeeting()
    } catch (error) {
      message.error('更新失败: ' + (error.response?.data?.detail || error.message))
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

  // 计算未完成议题数量
  const incompleteAgendaCount = meeting?.agenda?.filter(a => !a.completed).length || 0

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* 左侧边栏 - 议题 */}
      {meeting?.agenda && meeting.agenda.length > 0 && (
        <div
          style={{
            width: agendaSidebarCollapsed ? '50px' : '260px',
            transition: 'width 0.3s ease',
            borderRight: '1px solid #e8e8e8',
            padding: agendaSidebarCollapsed ? '12px 8px' : '12px',
            height: '100vh',
            overflowY: 'auto',
            flexShrink: 0,
            backgroundColor: '#fafafa'
          }}
        >
          <div style={{ 
            display: 'flex', 
            justifyContent: agendaSidebarCollapsed ? 'center' : 'space-between', 
            alignItems: 'center',
            marginBottom: 16
          }}>
            {!agendaSidebarCollapsed && (
              <span style={{ fontWeight: 'bold', fontSize: '16px' }}>
                议题列表
              </span>
            )}
            <Button
              type="text"
              icon={agendaSidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setAgendaSidebarCollapsed(!agendaSidebarCollapsed)}
              title={agendaSidebarCollapsed ? '展开侧边栏' : '收起侧边栏'}
            />
          </div>
          
          {agendaSidebarCollapsed ? (
            // 收起状态：显示图标和徽章
            <div style={{ textAlign: 'center' }}>
              <Badge count={incompleteAgendaCount} offset={[5, 0]}>
                <UnorderedListOutlined style={{ fontSize: 28, color: '#1890ff' }} />
              </Badge>
              <div style={{ 
                marginTop: 8, 
                fontSize: '12px', 
                color: '#666',
                textAlign: 'center'
              }}>
                {incompleteAgendaCount}/{meeting.agenda.length}
              </div>
            </div>
          ) : (
            // 展开状态：显示完整议题列表
            <div>
              <div style={{ 
                marginBottom: 12, 
                fontSize: '12px', 
                color: '#666',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <span>进度: {meeting.agenda.length - incompleteAgendaCount}/{meeting.agenda.length}</span>
                {isUserModerator() && meeting.status !== 'ended' && (
                  <Button 
                    type="link" 
                    size="small" 
                    icon={<PlusOutlined />}
                    onClick={() => setAgendaModalVisible(true)}
                    style={{ padding: 0 }}
                  >
                    添加
                  </Button>
                )}
              </div>
              
              <List
                dataSource={meeting.agenda}
                renderItem={(item) => (
                  <div
                    key={item.id}
                    style={{
                      marginBottom: 12,
                      padding: '12px',
                      background: 'white',
                      borderRadius: '6px',
                      border: item.completed ? '1px solid #d9d9d9' : '1px solid #1890ff',
                      boxShadow: item.completed ? 'none' : '0 2px 4px rgba(24, 144, 255, 0.1)',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'flex-start',
                      gap: '8px'
                    }}>
                      <Checkbox 
                        checked={item.completed} 
                        disabled={!isUserModerator() || meeting.status === 'ended'}
                        onChange={() => !item.completed && handleCompleteAgenda(item.id)}
                        style={{ marginTop: '2px' }}
                      />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ 
                          fontWeight: item.completed ? 'normal' : 'bold',
                          textDecoration: item.completed ? 'line-through' : 'none',
                          color: item.completed ? '#999' : '#333',
                          marginBottom: item.description ? '4px' : 0,
                          wordBreak: 'break-word'
                        }}>
                          {item.title}
                        </div>
                        {item.description && (
                          <div style={{ 
                            fontSize: '12px', 
                            color: '#666',
                            marginTop: '4px',
                            wordBreak: 'break-word'
                          }}>
                            {item.description}
                          </div>
                        )}
                        {isUserModerator() && meeting.status !== 'ended' && (
                          <div style={{ marginTop: '8px' }}>
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
                                style={{ padding: 0, height: 'auto' }}
                              >
                                删除
                              </Button>
                            </Popconfirm>
                          </div>
                        )}
                      </div>
                    </div>
                    {item.completed && (
                      <div style={{ 
                        marginTop: '8px',
                        paddingTop: '8px',
                        borderTop: '1px solid #f0f0f0',
                        fontSize: '11px',
                        color: '#52c41a',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        <CheckCircleOutlined />
                        已完成
                      </div>
                    )}
                  </div>
                )}
              />
            </div>
          )}
        </div>
      )}

      {/* 主内容区 - 对话界面 */}
      <div style={{ 
        flex: 1, 
        minWidth: 0, 
        display: 'flex', 
        flexDirection: 'column',
        height: '100vh',
        overflow: 'hidden',
        backgroundColor: '#fff'
      }}>
        {/* 顶部导航栏 - 简洁设计 */}
        <div style={{ 
          flexShrink: 0, 
          padding: '12px 20px',
          borderBottom: '1px solid #e8e8e8',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#fff'
        }}>
          <Space>
            <Button 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate('/meetings')}
              type="text"
            />
            <div>
              <div style={{ fontWeight: 600, fontSize: '16px' }}>{meeting.topic}</div>
              <Space size="small" style={{ fontSize: '12px', color: '#666' }}>
                {getStatusBadge(meeting.status)}
                <span>轮次 {meeting.current_round}{meeting.max_rounds ? `/${meeting.max_rounds}` : ''}</span>
                <span>消息 {meeting.messages.length}</span>
              </Space>
            </div>
          </Space>
          
          <Space>
            {/* 停止输出按钮 - 当正在发送或有流式消息时显示 */}
            {(sending || streamingMessage) && (
              <Button 
                danger 
                icon={<StopOutlined />} 
                onClick={handleStopOutput} 
                size="small"
                type="primary"
              >
                停止输出
              </Button>
            )}
            {meeting.status === 'active' && (
              <Button icon={<PauseCircleOutlined />} onClick={handlePause} size="small">
                暂停
              </Button>
            )}
            {meeting.status === 'paused' && (
              <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleStart} size="small">
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
                <Button danger icon={<StopOutlined />} size="small">
                  结束
                </Button>
              </Popconfirm>
            )}
            <Button 
              icon={settingsSidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setSettingsSidebarCollapsed(!settingsSidebarCollapsed)}
              type="text"
            />
          </Space>
        </div>

        {/* 消息列表区域 - 占据主体 */}
        <div style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '20px',
          backgroundColor: '#f9f9f9'
        }}>
          {!meeting.messages || meeting.messages.length === 0 ? (
            <div style={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center', 
              height: '100%' 
            }}>
              <Empty description="暂无消息，开始对话吧" />
            </div>
          ) : (
            <div style={{ maxWidth: '900px', margin: '0 auto' }}>
              {meeting.messages.map((msg, index) => {
                const isUser = msg.speaker_type === 'user'
                const agentColor = isUser ? null : getAgentColor(msg.speaker_id)
                const isModerator = !isUser && meeting.moderator_type === 'agent' && msg.speaker_id === meeting.moderator_id
                
                return (
                  <div key={msg.id || index} style={{ marginBottom: 24 }}>
                    <div style={{ marginBottom: 8 }}>
                      <Space size="small">
                        <Tag color={isUser ? 'green' : agentColor?.tag}>
                          {msg.speaker_name}
                          {isModerator && ' 👑'}
                        </Tag>
                        <span style={{ color: '#999', fontSize: '12px' }}>
                          {new Date(msg.timestamp).toLocaleString('zh-CN')}
                        </span>
                        {msg.mentions && msg.mentions.length > 0 && (
                          <>
                            {msg.mentions.map((mention, i) => (
                              <Tag key={i} color="orange" style={{ fontSize: '11px' }}>
                                @{mention.mentioned_participant_name}
                              </Tag>
                            ))}
                          </>
                        )}
                      </Space>
                    </div>
                    <div style={{ 
                      padding: '16px', 
                      background: '#fff',
                      borderRadius: '8px',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                      border: isUser ? '1px solid #d9f7be' : `1px solid ${agentColor?.border || '#e8e8e8'}`,
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
                <div style={{ marginBottom: 24 }}>
                  <div style={{ marginBottom: 8 }}>
                    <Tag color="processing">
                      {streamingMessage.speaker_name} ⚡
                    </Tag>
                    <span style={{ color: '#999', fontSize: '12px' }}>
                      正在输入...
                    </span>
                  </div>
                  <div style={{ 
                    padding: '16px', 
                    background: '#fff',
                    borderRadius: '8px',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                    border: '1px solid #1890ff',
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
        </div>

        {/* 底部输入区域 - 固定在底部 */}
        {meeting.status !== 'ended' && (
          <div style={{ 
            flexShrink: 0, 
            borderTop: '1px solid #e8e8e8',
            padding: '16px 20px',
            backgroundColor: '#fff'
          }}>
            <div style={{ maxWidth: '900px', margin: '0 auto' }}>
              <div style={{ marginBottom: '12px' }}>
                <Space size="small" wrap>
                  <span style={{ color: '#666', fontSize: '12px' }}>快速 @: </span>
                  {meeting.participants.map(p => {
                    const color = getAgentColor(p.id)
                    return (
                      <Tag 
                        key={p.id}
                        color={color?.tag}
                        style={{ 
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                        onClick={() => setUserMessage(prev => prev + `@${p.name} `)}
                      >
                        @{p.name}
                      </Tag>
                    )
                  })}
                </Space>
              </div>
              
              <div style={{ position: 'relative' }}>
                <TextArea
                  ref={textAreaRef}
                  rows={3}
                  value={userMessage}
                  onChange={handleMessageChange}
                  placeholder="输入你的消息... (输入 @ 可以提及代理，Ctrl+Enter 发送)"
                  disabled={meeting.status !== 'active'}
                  style={{ 
                    resize: 'none',
                    borderRadius: '8px',
                    fontSize: '14px'
                  }}
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
                    borderRadius: '8px',
                    maxHeight: '200px',
                    overflowY: 'auto',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                    zIndex: 1000,
                    marginBottom: '8px'
                  }}>
                    {mentionSuggestions.map(p => {
                      const color = getAgentColor(p.id)
                      return (
                        <div
                          key={p.id}
                          onClick={() => handleSelectMention(p)}
                          style={{
                            padding: '10px 12px',
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
              
              <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Space size="small">
                  {/* 如果正在发送或有流式消息，显示停止按钮 */}
                  {(sending || streamingMessage) ? (
                    <Button
                      danger
                      type="primary"
                      icon={<StopOutlined />}
                      onClick={handleStopOutput}
                    >
                      停止输出
                    </Button>
                  ) : (
                    <>
                      <Button
                        type="primary"
                        icon={<SendOutlined />}
                        onClick={() => handleSendMessage('mention')}
                        disabled={meeting.status !== 'active'}
                      >
                        发送并 @ 代理响应
                      </Button>
                      <Button
                        icon={<SendOutlined />}
                        onClick={() => handleSendMessage('all')}
                        disabled={meeting.status !== 'active'}
                      >
                        请求所有代理
                      </Button>
                      <Button
                        onClick={handleRunRound}
                        disabled={meeting.status !== 'active'}
                      >
                        🔄 运行一轮
                      </Button>
                    </>
                  )}
                </Space>
                
                <Space size="small">
                  <span style={{ fontSize: '12px', color: '#666' }}>Markdown</span>
                  <Switch 
                    checked={markdownEnabled} 
                    onChange={setMarkdownEnabled}
                    size="small"
                  />
                </Space>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 右侧边栏 - 设置和信息 */}
      <div
        style={{
          width: settingsSidebarCollapsed ? '0' : '320px',
          transition: 'width 0.3s ease',
          borderLeft: settingsSidebarCollapsed ? 'none' : '1px solid #e8e8e8',
          height: '100vh',
          overflowY: 'auto',
          flexShrink: 0,
          backgroundColor: '#fafafa',
          overflow: settingsSidebarCollapsed ? 'hidden' : 'auto'
        }}
      >
        {!settingsSidebarCollapsed && (
          <div style={{ padding: '16px' }}>
            {/* 会议控制 */}
            <div style={{ marginBottom: '16px' }}>
              <h4 style={{ marginBottom: '12px', fontSize: '14px', fontWeight: 600 }}>会议控制</h4>
              <Space direction="vertical" style={{ width: '100%' }} size="small">
                {/* 思维导图入口 - 根据是否有思维导图显示不同状态 */}
                {meeting.mind_map ? (
                  <Button 
                    icon={<BranchesOutlined />} 
                    onClick={() => navigate(`/meetings/${meetingId}/mind-map`)}
                    style={{ width: '100%' }}
                    type="primary"
                    ghost
                  >
                    查看思维导图
                  </Button>
                ) : (
                  <Button 
                    icon={<PlusOutlined />} 
                    onClick={() => navigate(`/meetings/${meetingId}/mind-map`)}
                    style={{ width: '100%' }}
                    type="dashed"
                  >
                    生成思维导图
                  </Button>
                )}
                <Button.Group style={{ width: '100%' }}>
                  <Button 
                    icon={<DownloadOutlined />} 
                    onClick={() => handleExport('markdown')}
                    style={{ flex: 1 }}
                  >
                    导出 MD
                  </Button>
                  <Button 
                    icon={<DownloadOutlined />} 
                    onClick={() => handleExport('json')}
                    style={{ flex: 1 }}
                  >
                    导出 JSON
                  </Button>
                </Button.Group>
              </Space>
            </div>

            <Divider style={{ margin: '16px 0' }} />

            {/* 功能开关 */}
            <div style={{ marginBottom: '16px' }}>
              <h4 style={{ marginBottom: '12px', fontSize: '14px', fontWeight: 600 }}>功能设置</h4>
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 500, fontSize: '13px' }}>🔄 自动持续对话</div>
                    <div style={{ fontSize: '11px', color: '#666', marginTop: '2px' }}>
                      AI @ AI 时自动触发
                    </div>
                  </div>
                  <Switch 
                    checked={autoResponseEnabled} 
                    onChange={setAutoResponseEnabled}
                    size="small"
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 500, fontSize: '13px' }}>⚡ 流式输出</div>
                    <div style={{ fontSize: '11px', color: '#666', marginTop: '2px' }}>
                      实时显示 AI 回复
                    </div>
                  </div>
                  <Switch 
                    checked={streamingEnabled} 
                    onChange={setStreamingEnabled}
                    size="small"
                  />
                </div>
              </Space>
            </div>

            <Divider style={{ margin: '16px 0' }} />

            {/* 参与者列表 */}
            <div style={{ marginBottom: '16px' }}>
              <h4 style={{ marginBottom: '12px', fontSize: '14px', fontWeight: 600 }}>
                参与者 ({meeting.participants.length})
              </h4>
              <div>
                {meeting.participants.map(p => {
                  const color = getAgentColor(p.id)
                  const isModerator = meeting.moderator_type === 'agent' && p.id === meeting.moderator_id
                  return (
                    <div 
                      key={p.id}
                      style={{ 
                        marginBottom: '8px',
                        padding: '10px',
                        background: '#fff',
                        borderLeft: `3px solid ${color?.border}`,
                        borderRadius: '4px',
                        fontSize: '13px'
                      }}
                    >
                      <div style={{ fontWeight: 600, marginBottom: '4px' }}>
                        {p.name}
                        {isModerator && <Tag color="gold" style={{ marginLeft: '4px', fontSize: '11px' }}>主持人</Tag>}
                      </div>
                      <div style={{ fontSize: '11px', color: '#666' }}>
                        {p.role_name}
                      </div>
                      {meeting.status !== 'ended' && (
                        <Button
                          size="small"
                          type="link"
                          style={{ padding: '4px 0', height: 'auto', fontSize: '11px' }}
                          onClick={() => handleRequestAgentById(p.id)}
                          loading={sending}
                        >
                          请求发言
                        </Button>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            <Divider style={{ margin: '16px 0' }} />

            {/* 会议信息 */}
            <div>
              <h4 style={{ marginBottom: '12px', fontSize: '14px', fontWeight: 600 }}>会议信息</h4>
              <Space direction="vertical" style={{ width: '100%' }} size="small">
                <div style={{ fontSize: '12px' }}>
                  <span style={{ color: '#666' }}>主持人：</span>
                  <Tag color="gold" size="small" style={{ marginLeft: '4px' }}>
                    {meeting.moderator_type === 'user' 
                      ? '用户' 
                      : meeting.participants.find(p => p.id === meeting.moderator_id)?.name || '未知'}
                  </Tag>
                </div>
                {meeting.discussion_style && (
                  <div style={{ fontSize: '12px' }}>
                    <span style={{ color: '#666' }}>讨论风格：</span>
                    <Tag size="small" style={{ marginLeft: '4px' }}>
                      {meeting.discussion_style === 'formal' && '正式'}
                      {meeting.discussion_style === 'casual' && '轻松'}
                      {meeting.discussion_style === 'debate' && '辩论式'}
                    </Tag>
                  </div>
                )}
                <div style={{ fontSize: '12px' }}>
                  <span style={{ color: '#666' }}>发言顺序：</span>
                  <Tag size="small" style={{ marginLeft: '4px' }}>
                    {meeting.speaking_order === 'sequential' ? '顺序' : '随机'}
                  </Tag>
                </div>
                {meeting.max_rounds && (
                  <div style={{ fontSize: '12px' }}>
                    <span style={{ color: '#666' }}>最大轮次：</span>
                    <span style={{ marginLeft: '4px' }}>{meeting.max_rounds}</span>
                  </div>
                )}
                <div style={{ fontSize: '12px' }}>
                  <span style={{ color: '#666' }}>纪要提示词：</span>
                  <Button 
                    type="link" 
                    size="small" 
                    onClick={handleEditMinutesPrompt}
                    style={{ padding: '0 4px', height: 'auto' }}
                  >
                    {meeting.config?.minutes_prompt ? '已自定义' : '使用默认'}
                  </Button>
                </div>
              </Space>
            </div>
          </div>
        )}
      </div>

      {/* 模态框 */}
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
          <div style={{ 
            padding: '12px', 
            background: '#f0f5ff', 
            borderRadius: '4px',
            marginBottom: '8px'
          }}>
            <Checkbox
              checked={generateMindMapWithMinutes}
              onChange={(e) => setGenerateMindMapWithMinutes(e.target.checked)}
            >
              同时生成思维导图
            </Checkbox>
            <div style={{ 
              fontSize: '12px', 
              color: '#666', 
              marginTop: '4px',
              marginLeft: '24px'
            }}>
              思维导图将基于会议内容和纪要关键决策生成
            </div>
          </div>
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
        title="编辑会议纪要提示词"
        open={minutesPromptModalVisible}
        onCancel={() => {
          setMinutesPromptModalVisible(false)
          minutesPromptForm.resetFields()
        }}
        onOk={() => minutesPromptForm.submit()}
        width={700}
      >
        <Form form={minutesPromptForm} layout="vertical" onFinish={handleUpdateMinutesPrompt}>
          <Form.Item
            name="minutes_prompt"
            label="自定义提示词"
            tooltip="留空则使用系统默认提示词"
          >
            <Input.TextArea 
              rows={10} 
              placeholder="你是一名专业的会议纪要助理，请根据以下会议内容，生成清晰、准确、可执行的会议纪要。&#10;&#10;要求：&#10;- 结构化输出（会议背景、参会人员、讨论要点、决策事项、待办任务、风险与关注点）&#10;- 用词客观中立，不评价人员&#10;- 不遗漏关键数字、日期、负责人、截止时间&#10;- 可自动识别隐含的任务和风险&#10;- 所有待办事项以 To-Do 列表总结"
            />
          </Form.Item>
          <div style={{ 
            padding: '12px', 
            background: '#f0f5ff', 
            borderRadius: '4px',
            fontSize: '12px',
            color: '#666'
          }}>
            💡 提示：自定义提示词将作为 AI 的系统提示（system prompt），用于指导会议纪要的生成方式和格式。
          </div>
        </Form>
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

      {/* 浮动按钮组 */}
      <FloatButton.Group
        trigger="hover"
        type="primary"
        style={{ 
          position: 'fixed', 
          left: '24px', 
          right: 'auto',
          insetInlineEnd: 'auto',
          insetInlineStart: '24px'
        }}
        icon={<FileTextOutlined />}
        tooltip="会议工具"
      >
        {/* 会议纪要浮动按钮 */}
        <FloatButton
          icon={meeting.current_minutes ? <FileTextOutlined /> : <PlusOutlined />}
          tooltip={meeting.current_minutes ? '查看会议纪要' : '生成会议纪要'}
          onClick={() => {
            if (meeting.current_minutes) {
              setMinutesDrawerVisible(true)
            } else {
              setMinutesModalVisible(true)
            }
          }}
          badge={meeting.current_minutes ? { dot: true, color: 'green' } : null}
        />
        {/* 思维导图浮动按钮 */}
        <FloatButton
          icon={meeting.mind_map ? <BranchesOutlined /> : <PlusOutlined />}
          tooltip={meeting.mind_map ? '查看思维导图' : '生成思维导图'}
          onClick={() => navigate(`/meetings/${meetingId}/mind-map`)}
          badge={meeting.mind_map ? { dot: true, color: 'blue' } : null}
        />
      </FloatButton.Group>

      {/* 会议纪要抽屉 */}
      <Drawer
        title={
          <Space>
            <span>会议纪要</span>
            {meeting.mind_map && (
              <Button 
                type="link" 
                size="small"
                icon={<BranchesOutlined />}
                onClick={() => {
                  setMinutesDrawerVisible(false)
                  navigate(`/meetings/${meetingId}/mind-map`)
                }}
                style={{ padding: 0 }}
              >
                切换到思维导图
              </Button>
            )}
          </Space>
        }
        placement="right"
        width={600}
        open={minutesDrawerVisible}
        onClose={() => setMinutesDrawerVisible(false)}
        extra={
          <Space>
            <Button 
              icon={<EditOutlined />} 
              onClick={() => {
                setMinutesDrawerVisible(false)
                handleViewMinutes()
              }}
            >
              编辑
            </Button>
            <Button 
              icon={<HistoryOutlined />} 
              onClick={() => {
                setMinutesDrawerVisible(false)
                handleViewMinutesHistory()
              }}
            >
              历史
            </Button>
            {meeting.status !== 'ended' && (
              <Button 
                type="primary" 
                onClick={() => {
                  setMinutesDrawerVisible(false)
                  setMinutesModalVisible(true)
                }}
              >
                重新生成
              </Button>
            )}
          </Space>
        }
      >
        {meeting.current_minutes ? (
          <div>
            <div style={{ marginBottom: 16, color: '#666', fontSize: '12px' }}>
              版本 {meeting.current_minutes.version} · 
              创建于 {new Date(meeting.current_minutes.created_at).toLocaleString('zh-CN')} · 
              创建者: {meeting.current_minutes.created_by === 'user' ? '用户' : 
                meeting.participants.find(p => p.id === meeting.current_minutes.created_by)?.name || '未知'}
            </div>
            <div style={{ 
              padding: '12px', 
              background: '#f9f9f9',
              borderRadius: '4px',
              whiteSpace: 'pre-wrap'
            }}>
              <MarkdownMessage content={meeting.current_minutes.summary || meeting.current_minutes.content} />
            </div>
          </div>
        ) : (
          <Empty description="暂无会议纪要">
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => {
                setMinutesDrawerVisible(false)
                setMinutesModalVisible(true)
              }}
            >
              生成会议纪要
            </Button>
          </Empty>
        )}
      </Drawer>
    </div>
  )
}

export default MeetingRoom
