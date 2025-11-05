/**
 * 科学家团队工作区 - 团队协作群聊模式
 * 
 * 布局：
 * - 左侧：团队成员列表
 * - 右侧：群聊式对话区域（复用ChatArea样式）
 */
import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { 
  Card, 
  Button, 
  Space, 
  Tag, 
  Modal, 
  Radio, 
  Input, 
  Upload,
  message as antdMessage, 
  Alert, 
  Avatar,
  Checkbox,
  Divider
} from 'antd'
import { 
  TeamOutlined, 
  SendOutlined,
  PaperClipOutlined,
  UserOutlined,
  RobotOutlined,
  PlusOutlined,
  CheckCircleOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  LineChartOutlined,
  BgColorsOutlined,
  EditOutlined,
  SearchOutlined,
  MessageOutlined
} from '@ant-design/icons'
import useAppStore from '@/store/useAppStore'
import { startResearch, submitUserDecision, createWorkflowWebSocket } from '@/services/workflowApi'
import { uploadTeamFile, formatFileSize } from '@/services/fileUploadApi'
import './ScientistTeamWorkspace.css'

const { TextArea } = Input

// Agent角色定义
const AVAILABLE_AGENTS = [
  { id: 'pi_agent', name: '首席研究员', icon: ExperimentOutlined, color: '#722ed1', description: '统筹规划，协调团队' },
  { id: 'data_scientist_agent', name: '数据科学家', icon: BarChartOutlined, color: '#1890ff', description: '数据清洗和特征工程' },
  { id: 'statistician_agent', name: '统计学家', icon: LineChartOutlined, color: '#13c2c2', description: '统计分析和假设检验' },
  { id: 'visualizer_agent', name: '可视化专家', icon: BgColorsOutlined, color: '#52c41a', description: '数据可视化' },
  { id: 'writer_agent', name: '论文撰写者', icon: EditOutlined, color: '#fa8c16', description: '撰写研究报告' },
  { id: 'reviewer_agent', name: '审稿人', icon: SearchOutlined, color: '#eb2f96', description: '质量审核' }
]

// 团队成员卡片
const MemberCard = ({ agent, isActive }) => {
  const agentInfo = AVAILABLE_AGENTS.find(a => a.id === agent.id) || {}
  const IconComponent = agentInfo.icon || RobotOutlined
  
  return (
    <div className={`member-card ${isActive ? 'active' : ''}`}>
      <Avatar 
        size={40} 
        style={{ backgroundColor: agentInfo.color }} 
        icon={<IconComponent />}
      />
      <div className="member-info">
        <div className="member-name">
          <IconComponent style={{ marginRight: 4 }} />
          {agentInfo.name}
        </div>
        <div className="member-desc">{agentInfo.description}</div>
      </div>
      {isActive && <CheckCircleOutlined className="active-badge" />}
    </div>
  )
}

// 群聊消息组件（类似微信）- 支持Markdown渲染
const GroupChatMessage = ({ message }) => {
  const agentInfo = AVAILABLE_AGENTS.find(a => a.id === message.agent_id) || {}
  const isUser = message.isUser
  const IconComponent = agentInfo.icon || RobotOutlined
  const isStreaming = message.isStreaming
  
  return (
    <div className={`group-message ${isUser ? 'user-message' : 'agent-message'} ${isStreaming ? 'streaming' : ''}`}>
      <Avatar 
        size={40} 
        style={{ backgroundColor: isUser ? '#1890ff' : agentInfo.color }} 
        icon={isUser ? <UserOutlined /> : <IconComponent />}
      />
      <div className="message-content-wrapper">
        <div className="message-sender-name">
          {isUser ? '您' : (
            <>
              <IconComponent style={{ marginRight: 4, fontSize: 14 }} />
              {agentInfo.name}
              {isStreaming && <span className="streaming-indicator"> 正在思考...</span>}
            </>
          )}
        </div>
        <div className="message-bubble markdown-content">
          <ReactMarkdown
            components={{
              code({node, inline, className, children, ...props}) {
                const match = /language-(\w+)/.exec(className || '')
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={match[1]}
                    PreTag="div"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                )
              }
            }}
          >
            {message.content}
          </ReactMarkdown>
          {isStreaming && <span className="cursor-blink">▊</span>}
        </div>
        {message.attachments && message.attachments.length > 0 && (
          <div className="message-attachments">
            {message.attachments.map((file, idx) => (
              <Tag key={idx} color="blue">{file.name}</Tag>
            ))}
          </div>
        )}
        <div className="message-time">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}

// 决策对话框
const DecisionDialog = ({ visible, decision, onSubmit, onCancel }) => {
  const [selectedOption, setSelectedOption] = useState(null)
  const [feedback, setFeedback] = useState('')
  
  if (!decision) return null
  
  const handleSubmit = () => {
    if (!selectedOption) {
      antdMessage.warning('请选择一个选项')
      return
    }
    onSubmit({
      decisionId: decision.decision_id,
      choice: selectedOption,
      feedback: feedback || null
    })
  }
  
  return (
    <Modal
      title={`[${decision.agent_name}] 需要您的决策`}
      open={visible}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>取消</Button>,
        <Button key="submit" type="primary" onClick={handleSubmit}>确认</Button>
      ]}
      width={600}
    >
      <Alert
        message={decision.question}
        description={decision.context && JSON.stringify(decision.context, null, 2)}
        type="info"
        style={{ marginBottom: 16 }}
      />
      <Radio.Group value={selectedOption} onChange={(e) => setSelectedOption(e.target.value)} style={{ width: '100%' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          {decision.options && decision.options.map((opt) => (
            <Radio key={opt.value} value={opt.value}>
              <strong>{opt.label}</strong>
              {opt.explanation && <div style={{ fontSize: 12, color: '#666' }}>{opt.explanation}</div>}
            </Radio>
          ))}
        </Space>
      </Radio.Group>
      <Divider />
      <div>
        <div style={{ marginBottom: 8 }}>补充说明（可选）：</div>
        <TextArea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="您可以在这里输入额外的说明..."
          rows={3}
        />
      </div>
    </Modal>
  )
}

const ScientistTeamWorkspace = () => {
  const { sessionId, fileData } = useAppStore()
  const [selectedMembers, setSelectedMembers] = useState([
    'pi_agent',
    'data_scientist_agent',
    'statistician_agent'
  ]) // 默认选中的成员
  const [activeMembers, setActiveMembers] = useState([]) // 当前活跃的成员
  const [chatMessages, setChatMessages] = useState([])
  const [streamingMessages, setStreamingMessages] = useState({}) // 流式消息缓存
  const [userInput, setUserInput] = useState('')
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [isTeamWorking, setIsTeamWorking] = useState(false)
  const [showMemberSelector, setShowMemberSelector] = useState(false)
  const [currentDecision, setCurrentDecision] = useState(null)
  const [showDecisionDialog, setShowDecisionDialog] = useState(false)
  
  const messagesEndRef = useRef(null)
  const wsRef = useRef(null)
  
  // WebSocket连接
  useEffect(() => {
    const ws = createWorkflowWebSocket(
      (data) => handleWebSocketMessage(data),
      () => console.log('WebSocket closed'),
      (error) => console.error('WebSocket error:', error)
    )
    wsRef.current = ws
    return () => {
      if (ws) ws.close()
    }
  }, [])
  
  // 智能自动滚动到底部（只有用户在底部附近时才滚动）
  const [isNearBottom, setIsNearBottom] = useState(true)
  const [hasNewMessages, setHasNewMessages] = useState(false)
  const chatContainerRef = useRef(null)
  
  const scrollToBottom = (force = false) => {
    if (force || isNearBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      setHasNewMessages(false)
    } else {
      setHasNewMessages(true)
    }
  }
  
  // 检测用户是否在底部附近
  const handleScroll = () => {
    const container = chatContainerRef.current
    if (!container) return
    
    const { scrollTop, scrollHeight, clientHeight } = container
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight
    
    // 如果距离底部小于100px，认为用户在底部
    const nearBottom = distanceFromBottom < 100
    setIsNearBottom(nearBottom)
    
    if (nearBottom) {
      setHasNewMessages(false)
    }
  }
  
  useEffect(() => {
    scrollToBottom()
  }, [chatMessages, streamingMessages])
  
  // 处理WebSocket消息
  const handleWebSocketMessage = (data) => {
    console.log('收到WebSocket消息:', data)
    
    switch (data.type) {
      case 'agent_status_update':
        setActiveMembers(prev => {
          const existing = prev.find(m => m.id === data.data.agent_id)
          if (existing) {
            return prev.map(m => m.id === data.data.agent_id ? { id: data.data.agent_id, status: data.data.status } : m)
          } else {
            return [...prev, { id: data.data.agent_id, status: data.data.status }]
          }
        })
        break
        
      case 'agent_stream_start':
        // 开始流式输出 - 创建占位消息
        const streamMsgId = data.data.message_id
        setStreamingMessages(prev => ({
          ...prev,
          [streamMsgId]: {
            id: streamMsgId,
            agent_id: data.data.agent_id,
            content: '',
            timestamp: new Date().toISOString(),
            isUser: false,
            isStreaming: true
          }
        }))
        break
        
      case 'agent_stream_chunk':
        // 接收流式数据块
        const chunkMsgId = data.data.message_id
        setStreamingMessages(prev => {
          const existing = prev[chunkMsgId]
          if (!existing) return prev
          return {
            ...prev,
            [chunkMsgId]: {
              ...existing,
              content: existing.content + data.data.chunk
            }
          }
        })
        break
        
      case 'agent_stream_end':
        // 流式结束 - 移到正式消息列表
        const endMsgId = data.data.message_id
        setStreamingMessages(prev => {
          const streamMsg = prev[endMsgId]
          if (streamMsg) {
            // 添加到消息列表
            setChatMessages(prevMsgs => [...prevMsgs, { ...streamMsg, isStreaming: false }])
            // 从流式缓存移除
            const { [endMsgId]: removed, ...rest } = prev
            return rest
          }
          return prev
        })
        break
        
      case 'agent_message':
        const agentMsg = {
          id: Date.now() + Math.random(),
          agent_id: data.data.from_agent,
          content: data.data.content?.description || data.data.content?.message || JSON.stringify(data.data.content),
          timestamp: data.data.timestamp || new Date().toISOString(),
          isUser: false
        }
        setChatMessages(prev => [...prev, agentMsg])
        break
        
      case 'user_decision_required':
        setCurrentDecision(data.data)
        setShowDecisionDialog(true)
        break
        
      case 'research_completed':
        antdMessage.success('研究完成！')
        setIsTeamWorking(false)
        break
        
      case 'research_failed':
        antdMessage.error(`研究失败：${data.data.error}`)
        setIsTeamWorking(false)
        break
        
      default:
        console.log('未处理的消息类型:', data.type)
    }
  }
  
  const [uploadingFiles, setUploadingFiles] = useState(new Set())
  
  // 处理文件上传
  const handleFileUpload = async ({ file }) => {
    // 检查文件类型
    const allowedTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'text/markdown'
    ]
    
    const fileExt = file.name.split('.').pop().toLowerCase()
    const allowedExts = ['csv', 'xlsx', 'xls', 'pdf', 'docx', 'txt', 'md']
    
    if (!allowedExts.includes(fileExt)) {
      antdMessage.error(`不支持的文件类型。支持：${allowedExts.join(', ')}`)
      return false
    }
    
    // 检查文件大小（50MB）
    const maxSize = 50 * 1024 * 1024
    if (file.size > maxSize) {
      antdMessage.error(`文件过大（${formatFileSize(file.size)}），最大支持 50MB`)
      return false
    }
    
    // 开始上传
    setUploadingFiles(prev => new Set(prev).add(file.uid))
    antdMessage.loading({ content: `正在上传 ${file.name}...`, key: file.uid })
    
    try {
      const result = await uploadTeamFile(file)
      
      if (result.success) {
        antdMessage.success({ content: `${file.name} 上传成功`, key: file.uid })
        
        // 将解析后的数据添加到文件列表
        setUploadedFiles(prev => [...prev, {
          uid: file.uid,
          name: file.name,
          size: file.size,
          parsedData: result.data,
          file: file
        }])
      } else {
        throw new Error(result.message || '上传失败')
      }
    } catch (error) {
      console.error('文件上传失败:', error)
      antdMessage.error({ 
        content: `${file.name} 上传失败: ${error.response?.data?.detail || error.message}`, 
        key: file.uid 
      })
    } finally {
      setUploadingFiles(prev => {
        const newSet = new Set(prev)
        newSet.delete(file.uid)
        return newSet
      })
    }
    
    return false // 阻止默认上传
  }
  
  // 移除文件
  const handleRemoveFile = (fileItem) => {
    setUploadedFiles(prev => prev.filter(f => f.uid !== fileItem.uid))
    antdMessage.info(`已移除 ${fileItem.name}`)
  }
  
  // 发送消息
  const handleSendMessage = async () => {
    if (!userInput.trim() && uploadedFiles.length === 0) {
      antdMessage.warning('请输入研究课题或上传文件')
      return
    }
    
    try {
      // 构建文件摘要
      let filesContext = ''
      if (uploadedFiles.length > 0) {
        filesContext = '\n\n**附件文件**:\n'
        uploadedFiles.forEach(f => {
          const parsed = f.parsedData
          filesContext += `\n📎 ${f.name} (${formatFileSize(f.size)})\n`
          
          if (parsed.type === 'data') {
            filesContext += `- 数据文件: ${parsed.rows}行 × ${parsed.columns.length}列\n`
            filesContext += `- 字段: ${parsed.columns.slice(0, 5).join(', ')}${parsed.columns.length > 5 ? '...' : ''}\n`
          } else if (parsed.type === 'document') {
            filesContext += `- 文档: ${parsed.word_count || 0}词\n`
            filesContext += `- 预览: ${parsed.preview.substring(0, 100)}...\n`
          }
        })
      }
      
      // 添加用户消息
      const userMsg = {
        id: Date.now(),
        content: userInput + filesContext,
        timestamp: new Date().toISOString(),
        isUser: true,
        attachments: uploadedFiles.map(f => ({ 
          name: f.name, 
          size: f.size,
          type: f.parsedData?.type
        }))
      }
      setChatMessages(prev => [...prev, userMsg])
      
      const currentInput = userInput
      const currentFiles = uploadedFiles
      setUserInput('')
      setUploadedFiles([])
      
      // 启动团队协作
      setIsTeamWorking(true)
      
      // 构建 data_info（优先使用上传的数据文件）
      let dataInfo = null
      
      // 检查是否有数据文件
      const dataFile = currentFiles.find(f => f.parsedData?.type === 'data')
      if (dataFile) {
        const parsed = dataFile.parsedData
        dataInfo = {
          filename: dataFile.name,
          total_rows: parsed.rows,
          total_columns: parsed.columns.length,
          columns: parsed.columns,
          summary: parsed.summary,
          file_type: parsed.format
        }
      } else if (fileData) {
        // 使用全局的fileData（来自主页面上传）
        dataInfo = {
          total_rows: fileData?.total_rows || 0,
          total_columns: fileData?.total_columns || 0,
          columns: fileData?.columns?.map(c => c.name) || []
        }
      }
      
      await startResearch(sessionId || 'demo-session', currentInput, dataInfo)
      antdMessage.success('科学家团队已开始工作！')
      
    } catch (error) {
      console.error('启动失败:', error)
      antdMessage.error('启动失败：' + (error.response?.data?.detail || error.message))
      setIsTeamWorking(false)
    }
  }
  
  // 处理回车发送
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }
  
  // 提交决策
  const handleSubmitDecision = async (decisionData) => {
    try {
      await submitUserDecision(
        decisionData.decisionId,
        decisionData.choice,
        decisionData.feedback
      )
      antdMessage.success('决策已提交')
      setShowDecisionDialog(false)
      setCurrentDecision(null)
    } catch (error) {
      console.error('提交决策失败:', error)
      antdMessage.error('提交失败：' + (error.response?.data?.detail || error.message))
    }
  }
  
  // 切换成员选择
  const handleToggleMember = (memberId) => {
    setSelectedMembers(prev => {
      if (prev.includes(memberId)) {
        return prev.filter(id => id !== memberId)
      } else {
        return [...prev, memberId]
      }
    })
  }
  
  return (
    <div className="scientist-team-workspace-group">
      {/* 左侧：团队成员面板 */}
      <div className="team-members-panel">
        <div className="panel-header">
          <h3>
            <TeamOutlined /> 团队成员
          </h3>
          <Button 
            type="link" 
            size="small" 
            icon={<PlusOutlined />}
            onClick={() => setShowMemberSelector(true)}
          >
            管理
          </Button>
        </div>
        
        <div className="members-list">
          {selectedMembers.map(memberId => {
            const agent = AVAILABLE_AGENTS.find(a => a.id === memberId)
            const isActive = activeMembers.some(m => m.id === memberId)
            return agent ? (
              <MemberCard 
                key={agent.id} 
                agent={agent} 
                isActive={isActive}
              />
            ) : null
          })}
        </div>
        
        {selectedMembers.length === 0 && (
          <div className="empty-members">
            <p>还没有团队成员</p>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => setShowMemberSelector(true)}
            >
              添加成员
            </Button>
          </div>
        )}
      </div>
      
      {/* 右侧：群聊对话区域 */}
      <div className="team-chat-area">
        {/* 对话消息区域 */}
        <div 
          className="conversation-area" 
          ref={chatContainerRef}
          onScroll={handleScroll}
        >
          {chatMessages.length === 0 && (
            <div className="empty-chat">
              <MessageOutlined style={{ fontSize: 64, color: '#d9d9d9', marginBottom: 20 }} />
              <h3>开始团队协作</h3>
              <p>输入您的研究课题，团队将开始讨论和协作</p>
            </div>
          )}
          
          {chatMessages.map(msg => (
            <GroupChatMessage key={msg.id} message={msg} />
          ))}
          
          {/* 渲染流式消息 */}
          {Object.values(streamingMessages).map(msg => (
            <GroupChatMessage key={msg.id} message={msg} />
          ))}
          
          <div ref={messagesEndRef} />
        </div>
        
        {/* 新消息提示按钮 */}
        {hasNewMessages && !isNearBottom && (
          <div className="new-messages-indicator">
            <Button 
              type="primary" 
              size="small" 
              onClick={() => scrollToBottom(true)}
              icon={<MessageOutlined />}
            >
              新消息
            </Button>
          </div>
        )}
        
        {/* 输入区域（复用ChatArea样式） */}
        <div className="input-area-fixed">
          <div className="input-area-content">
            {uploadedFiles.length > 0 && (
              <div className="uploaded-files-tags">
                <Space wrap>
                  {uploadedFiles.map((fileItem) => {
                    const parsed = fileItem.parsedData
                    const color = parsed?.type === 'data' ? 'blue' : 'green'
                    const typeLabel = parsed?.type === 'data' ? '数据' : '文档'
                    
                    return (
                      <Tag 
                        key={fileItem.uid} 
                        closable 
                        onClose={() => handleRemoveFile(fileItem)}
                        color={color}
                        style={{ padding: '4px 12px', fontSize: '13px' }}
                      >
                        <PaperClipOutlined style={{ marginRight: 4 }} />
                        {fileItem.name}
                        <span style={{ marginLeft: 8, opacity: 0.7, fontSize: '12px' }}>
                          ({typeLabel}, {formatFileSize(fileItem.size)})
                        </span>
                      </Tag>
                    )
                  })}
                </Space>
              </div>
            )}
            
            <div className="input-controls">
              <div className="input-wrapper">
                <TextArea
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="输入研究课题... (Shift+Enter 换行，Enter 发送)"
                  autoSize={{ minRows: 1, maxRows: 4 }}
                  disabled={isTeamWorking}
                  className="message-textarea"
                />
                <div className="input-actions">
                  <Upload
                    beforeUpload={handleFileUpload}
                    showUploadList={false}
                    multiple
                  >
                    <Button 
                      icon={<PaperClipOutlined />} 
                      type="text"
                      disabled={isTeamWorking}
                    />
                  </Upload>
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    onClick={handleSendMessage}
                    loading={isTeamWorking}
                    disabled={isTeamWorking || (!userInput.trim() && uploadedFiles.length === 0)}
                  >
                    发送
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* 成员选择对话框 */}
      <Modal
        title="管理团队成员"
        open={showMemberSelector}
        onOk={() => setShowMemberSelector(false)}
        onCancel={() => setShowMemberSelector(false)}
        width={500}
      >
        <div className="member-selector">
          {AVAILABLE_AGENTS.map(agent => {
            const IconComponent = agent.icon
            return (
              <div key={agent.id} className="member-option">
                <Checkbox
                  checked={selectedMembers.includes(agent.id)}
                  onChange={() => handleToggleMember(agent.id)}
                >
                  <Space>
                    <Avatar size={32} style={{ backgroundColor: agent.color }} icon={<IconComponent />} />
                    <div>
                      <div>
                        <strong>
                          <IconComponent style={{ marginRight: 4, fontSize: 14 }} />
                          {agent.name}
                        </strong>
                      </div>
                      <div style={{ fontSize: 12, color: '#666' }}>{agent.description}</div>
                    </div>
                  </Space>
                </Checkbox>
              </div>
            )
          })}
        </div>
      </Modal>
      
      {/* 决策对话框 */}
      <DecisionDialog
        visible={showDecisionDialog}
        decision={currentDecision}
        onSubmit={handleSubmitDecision}
        onCancel={() => setShowDecisionDialog(false)}
      />
    </div>
  )
}

export default ScientistTeamWorkspace
