import { useState, useRef, useEffect } from 'react'
import { 
  Input, 
  Button, 
  Space, 
  Empty, 
  message,
  Tooltip,
  Tag,
  Segmented 
} from 'antd'
import { 
  SendOutlined, 
  EyeOutlined,
  EyeInvisibleOutlined,
  RocketOutlined,
  StopOutlined,
  ThunderboltOutlined,
  BulbOutlined
} from '@ant-design/icons'
import useAppStore from '@/store/useAppStore'
import { submitAnalysisStream, createSession, createMultiSession } from '@/services/api'
import ConversationList from './ConversationList'
import './ChatArea.css'

const { TextArea } = Input

function ChatArea({ showPreview, onTogglePreview }) {
  const {
    uploadMode,
    selectedColumns,
    sessionId,
    setSessionId,
    agentExecuting,
    setAgentExecuting,
    setCurrentTaskId,
    addConversation,
    clearAgentSteps,
    addAgentStep,
    updateAgentStep,
    setCurrentResult,
    fileData,
    fileGroup,
    selectedTables,
    currentSheetName,
    agentMode,
    setAgentMode,
  } = useAppStore()

  const [userInput, setUserInput] = useState('')
  const [inputLoading, setInputLoading] = useState(false)
  const [isNearBottom, setIsNearBottom] = useState(true)  // 用户是否在底部附近
  const [inputAreaHeight, setInputAreaHeight] = useState(300)  // 输入区域高度
  const [isDragging, setIsDragging] = useState(false)  // 是否正在拖拽
  const chatEndRef = useRef(null)
  const conversationAreaRef = useRef(null)  // 对话区域容器
  const cancelStreamRef = useRef(null)  // 用于取消流式请求

  // 检测用户是否在底部附近（距离底部小于 150px）
  const checkIfNearBottom = () => {
    if (!conversationAreaRef.current) return true
    
    const container = conversationAreaRef.current
    const scrollTop = container.scrollTop
    const scrollHeight = container.scrollHeight
    const clientHeight = container.clientHeight
    
    const distanceToBottom = scrollHeight - scrollTop - clientHeight
    return distanceToBottom < 150
  }

  // 监听滚动事件
  useEffect(() => {
    const container = conversationAreaRef.current
    if (!container) return
    
    const handleScroll = () => {
      const nearBottom = checkIfNearBottom()
      setIsNearBottom(nearBottom)
      console.log('📜 [ChatArea] 滚动检测:', { nearBottom, distanceToBottom: container.scrollHeight - container.scrollTop - container.clientHeight })
    }
    
    container.addEventListener('scroll', handleScroll)
    return () => container.removeEventListener('scroll', handleScroll)
  }, [])

  // 监听 agentSteps 变化，在用户接近底部时自动滚动
  const agentSteps = useAppStore((state) => state.agentSteps)
  useEffect(() => {
    if (agentExecuting && agentSteps.length > 0 && isNearBottom) {
      // 使用 setTimeout 延迟滚动，让 DOM 先更新
      const timer = setTimeout(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [agentExecuting, agentSteps, isNearBottom])

  // 提交分析需求（使用流式 SSE）
  const handleSubmit = async () => {
    if (!userInput.trim()) {
      message.warning('请输入分析需求')
      return
    }

    // 多文件模式：检查是否选择了表格
    if (uploadMode === 'multiple') {
      if (!selectedTables || selectedTables.length === 0) {
        message.warning('请至少选择一个表格进行分析')
        return
      }
    } else {
      // 单文件模式：检查是否选择了字段
      if (selectedColumns.length === 0) {
        message.warning('请至少选择一个字段进行分析')
        return
      }
    }

    setInputLoading(true)

    try {
      // 1. 如果没有 session，先创建
      let currentSessionId = sessionId
      if (!currentSessionId) {
        if (uploadMode === 'multiple') {
          // 多文件模式：创建多文件 Session
          console.log('🔧 创建多文件 Session:', {
            group_id: fileGroup.group_id,
            tables: selectedTables
          })
          
          const tables = selectedTables.map(t => ({
            file_id: t.file_id,
            sheet_name: t.sheet_name,
            alias: t.alias,
            selected_columns: t.selected_columns || []  // 添加字段选择
          }))
          
          const sessionRes = await createMultiSession(fileGroup.group_id, tables)
          currentSessionId = sessionRes.data.session_id
          setSessionId(currentSessionId)
          console.log('✅ 多文件 Session 创建成功:', currentSessionId)
          console.log('✅ 已加载表格:', sessionRes.data.loaded_tables)
        } else {
          // 单文件模式：创建普通 Session
          const sessionRes = await createSession(fileData.file_id, currentSheetName, selectedColumns)
          currentSessionId = sessionRes.data.session_id
          setSessionId(currentSessionId)
          console.log('✅ Session 创建成功:', currentSessionId)
        }
      }

      // 2. 添加用户消息到对话历史
      addConversation({
        type: 'user',
        content: userInput,
        timestamp: new Date(),
        selectedColumns: [...selectedColumns],
      })

      // 3. 清空输入框
      const currentInput = userInput
      setUserInput('')

      // 4. 启动 Agent 分析（流式）
      setAgentExecuting(true)
      clearAgentSteps()
      setInputLoading(false)

      // 使用流式 SSE
      const cancelStream = submitAnalysisStream(
        currentSessionId,
        currentInput,
        uploadMode === 'multiple' ? [] : selectedColumns,  // 多文件模式不需要选择字段
        agentMode,  // Agent 模式
        // onStep: 每当有新步骤时调用
        (step, stepIndex) => {
          console.log('🔥 [ChatArea] onStep 回调触发:', {
            stepIndex,
            title: step.title,
            status: step.status,
            hasOutput: !!step.output,
            outputLength: step.output?.length || 0
          })
          
          // 如果提供了步骤索引，更新对应的步骤；否则添加新步骤
          if (typeof stepIndex === 'number') {
            const currentSteps = useAppStore.getState().agentSteps
            console.log(`  📊 当前步骤数: ${currentSteps.length}`)
            if (stepIndex < currentSteps.length) {
              // 更新现有步骤
              console.log(`  🔄 更新步骤 #${stepIndex}`)
              updateAgentStep(stepIndex, step)
            } else {
              // 添加新步骤
              console.log(`  ➕ 添加新步骤 #${stepIndex}`)
              addAgentStep(step)
            }
          } else {
            // 兼容：无索引时总是添加
            console.log('  ➕ 添加新步骤（无索引）')
            addAgentStep(step)
          }
          
          // 验证更新后的状态
          const updatedSteps = useAppStore.getState().agentSteps
          console.log(`  ✅ 更新后步骤数: ${updatedSteps.length}`)
        },
        // onComplete: Agent 执行完成
        (result) => {
          console.log('✅ Agent 执行完成:', result)
          console.log('📊 [调试] 结果详情:', {
            hasData: !!result.data,
            hasResult: !!result.data?.result,
            resultKeys: result.data?.result ? Object.keys(result.data.result) : [],
            resultText: result.data?.result?.text,
            resultCharts: result.data?.result?.charts?.length,
            steps: result.data?.steps?.length,
            summary: result.data?.summary?.substring(0, 100)
          })
          
          setAgentExecuting(false)
          
          // 保存最终结果
          if (result.data && result.data.result) {
            setCurrentResult(result.data.result)
          }
          
          // 添加完整的分析结果到对话历史（包含步骤和结果）
          addConversation({
            type: 'agent',
            content: '✅ 分析完成！',
            timestamp: new Date(),
            steps: result.data?.steps || [],  // 保存所有执行步骤
            result: result.data?.result,      // 保存分析结果
            summary: result.data?.summary,    // 保存 AI 总结
          })
          
          message.success('分析完成！')
        },
        // onError: 发生错误
        (error) => {
          console.error('❌ Agent 执行失败:', error)
          setAgentExecuting(false)
          
          addConversation({
            type: 'agent',
            content: `❌ 分析失败：${error.message}`,
            timestamp: new Date(),
          })
          
          message.error('分析失败')
        }
      )
      
      // 保存取消函数
      cancelStreamRef.current = cancelStream

    } catch (error) {
      console.error('提交失败:', error)
      message.error('提交失败，请重试')
      setAgentExecuting(false)
      setInputLoading(false)
    }
  }

  // 停止 Agent 执行
  const handleStop = () => {
    if (cancelStreamRef.current) {
      cancelStreamRef.current()  // 取消流式请求
      cancelStreamRef.current = null
    }
    setAgentExecuting(false)
    message.info('已停止执行')
  }

  // 处理拖拽开始
  const handleDragStart = (e) => {
    setIsDragging(true)
    const startY = e.clientY
    const startHeight = inputAreaHeight

    const handleDrag = (e) => {
      const deltaY = startY - e.clientY
      const newHeight = Math.max(200, Math.min(800, startHeight + deltaY))
      setInputAreaHeight(newHeight)
    }

    const handleDragEnd = () => {
      setIsDragging(false)
      document.removeEventListener('mousemove', handleDrag)
      document.removeEventListener('mouseup', handleDragEnd)
    }

    document.addEventListener('mousemove', handleDrag)
    document.addEventListener('mouseup', handleDragEnd)
  }

  // 示例需求（根据模式不同）
  const exampleRequests = uploadMode === 'multiple' ? [
    '对比这几个表格的数据质量（缺失值、重复值）',
    '检查相同字段在各表中的取值范围一致性',
    '找出各表格的共同字段并对比统计量',
    '分析哪个表格的数据最完整',
  ] : [
    '计算所选字段的基本统计信息（平均值、最大值、最小值）',
    '按某个字段分组，统计每组的数量',
    '绘制数值字段的分布直方图',
    '分析字段之间的相关性',
  ]

  return (
    <div className="chat-area-container">
      {/* 对话历史区域（包含Agent思考过程）*/}
      <div className="conversation-area" ref={conversationAreaRef}>
        <ConversationList agentExecuting={agentExecuting} />
        <div ref={chatEndRef} />
      </div>

      {/* 可拖拽分隔条 */}
      <div 
        className={`resize-handle ${isDragging ? 'dragging' : ''}`}
        onMouseDown={handleDragStart}
      />

      {/* 输入区域 */}
      <div className="input-area" style={{ height: `${inputAreaHeight}px`, minHeight: '200px', maxHeight: '800px' }}>
        {/* 顶部信息栏 + 模式切换 */}
        <div className="input-header">
          <Space>
            {uploadMode === 'multiple' ? (
              <Tag color="default" style={{ border: '1px solid #d9d9d9' }}>
                已选择 {selectedTables.length} 个表格
              </Tag>
            ) : (
              <Tag color="default" style={{ border: '1px solid #d9d9d9' }}>
                已选择 {selectedColumns.length} 个字段
              </Tag>
            )}
            <Button
              type="link"
              size="small"
              icon={showPreview ? <EyeInvisibleOutlined /> : <EyeOutlined />}
              onClick={onTogglePreview}
              style={{ color: '#595959' }}
            >
              {showPreview ? '关闭数据' : '查看数据'}
            </Button>
          </Space>
          
          {/* Agent 模式选择器（移到右侧） */}
          <Segmented
            value={agentMode}
            onChange={setAgentMode}
            disabled={agentExecuting}
            size="small"
            options={[
              {
                label: (
                  <Tooltip title="按固定步骤执行：生成代码 → 执行 → 提取结果 → 生成总结">
                    <Space size={4}>
                      <ThunderboltOutlined style={{ fontSize: 12 }} />
                      <span style={{ fontSize: 13 }}>经典</span>
                    </Space>
                  </Tooltip>
                ),
                value: 'classic',
              },
              {
                label: (
                  <Tooltip title="像人类分析师一样思考：规划 → 探索 → 迭代分析 → 自主决策何时停止">
                    <Space size={4}>
                      <BulbOutlined style={{ fontSize: 12 }} />
                      <span style={{ fontSize: 13 }}>智能</span>
                    </Space>
                  </Tooltip>
                ),
                value: 'smart',
              },
            ]}
          />
        </div>

        {/* 输入框 */}
        <div className="input-wrapper">
          <TextArea
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="描述你的数据分析需求，例如：计算销售额的平均值和总和..."
            autoSize={{ minRows: 2, maxRows: 6 }}
            disabled={agentExecuting}
            onPressEnter={(e) => {
              if (e.shiftKey) return // Shift+Enter 换行
              e.preventDefault()
              handleSubmit()
            }}
            className="chat-input"
          />
          <div className="input-actions">
            <div className="input-hint">
              {userInput.length > 0 && (
                <span className="char-count">{userInput.length} / 500</span>
              )}
            </div>
            <Space>
              {agentExecuting ? (
                <Button
                  type="primary"
                  danger
                  icon={<StopOutlined />}
                  onClick={handleStop}
                >
                  停止执行
                </Button>
              ) : (
                <Tooltip title="Shift+Enter 换行，Enter 发送">
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    onClick={handleSubmit}
                    loading={inputLoading}
                    disabled={!userInput.trim() || selectedColumns.length === 0}
                  >
                    发送
                  </Button>
                </Tooltip>
              )}
            </Space>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatArea

