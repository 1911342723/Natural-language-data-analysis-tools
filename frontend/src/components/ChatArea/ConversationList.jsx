import { useState, useEffect, useRef } from 'react'
import { Empty, Avatar, Space, Tag, Collapse, Typography, Alert, Card, Button } from 'antd'
import { 
  UserOutlined, 
  RobotOutlined, 
  CodeOutlined, 
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  BugOutlined,
  DownloadOutlined,
  LoadingOutlined,
} from '@ant-design/icons'
import useAppStore from '@/store/useAppStore'
import ReactMarkdown from 'react-markdown'
import CodeExecutor from '@/components/CodeExecutor/CodeExecutor'
import ResultFormatter from '@/components/ResultFormatter/ResultFormatter'
import dayjs from 'dayjs'
import './ConversationList.css'

const { Panel } = Collapse
const { Text, Paragraph } = Typography

function ConversationList({ agentExecuting = false }) {
  const conversations = useAppStore((state) => state.conversations)
  const sessionId = useAppStore((state) => state.sessionId)
  const agentSteps = useAppStore((state) => state.agentSteps)
  const [, forceUpdate] = useState(0)
  const listEndRef = useRef(null)  // 用于滚动到底部
  
  // 监听 agentSteps 变化，强制重新渲染并滚动到底部
  useEffect(() => {
    console.log('🔔 [ConversationList] agentSteps 变化:', {
      agentExecuting,
      stepCount: agentSteps.length,
      steps: agentSteps.map((s, i) => ({
        index: i,
        title: s.title,
        status: s.status,
        outputLength: s.output?.length || 0
      }))
    })
    
    if (agentExecuting && agentSteps.length > 0) {
      forceUpdate(prev => prev + 1)
      // 自动滚动到底部
      setTimeout(() => {
        listEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
      }, 100)
    }
  }, [agentSteps, agentExecuting])
  
  // 实时轮询强制刷新（确保流式输出立即显示）
  useEffect(() => {
    if (!agentExecuting) return
    
    const intervalId = setInterval(() => {
      forceUpdate(prev => prev + 1)
    }, 100)  // 每100ms强制刷新一次
    
    return () => clearInterval(intervalId)
  }, [agentExecuting])

  // 渲染步骤图标
  const getStepIcon = (step) => {
    if (step.status === 'success') return <CheckCircleOutlined style={{ color: '#52c41a' }} />
    if (step.status === 'failed') return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
    return <PlayCircleOutlined />
  }

  // 下载图表
  const downloadChart = (base64Data, fileName = 'chart.png') => {
    try {
      // 创建下载链接
      const link = document.createElement('a')
      link.href = `data:image/png;base64,${base64Data}`
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (error) {
      console.error('图表下载失败:', error)
    }
  }

  // 渲染 Agent 消息（包含步骤和结果）
  const renderAgentMessage = (conv) => {
    const hasSteps = conv.steps && conv.steps.length > 0
    const hasResult = conv.result && Object.keys(conv.result).length > 0

    return (
      <div>
        {/* 基本消息 */}
        <div className="message-body" style={{ marginBottom: hasSteps ? 12 : 0 }}>
          <ReactMarkdown>{conv.content}</ReactMarkdown>
        </div>

        {/* 执行步骤 */}
        {hasSteps && (
          <Collapse 
            defaultActiveKey={['steps']}
            style={{ marginBottom: 12 }}
          >
            <Panel 
              header={
                <Space>
                  <CodeOutlined />
                  <Text strong>执行过程 ({conv.steps.length} 步)</Text>
                </Space>
              } 
              key="steps"
            >
              <Collapse 
                defaultActiveKey={[]}
                ghost
                style={{ marginTop: 12 }}
              >
                {conv.steps.map((step, idx) => (
                  <Panel
                    key={`step-${idx}`}
                    header={
                      <Space>
                        {getStepIcon(step)}
                        <Text strong>{step.title}</Text>
                        <Tag color={step.status === 'success' ? 'success' : 'error'}>
                          {step.status}
                        </Tag>
                      </Space>
                    }
                  >
                  {/* 步骤描述 */}
                  {step.description && (
                    <Paragraph style={{ marginBottom: 12, color: '#8c8c8c' }}>
                      {step.description}
                    </Paragraph>
                  )}

                  {/* 代码 - 使用可交互的 CodeExecutor */}
                  {step.code && (
                    <div style={{ marginBottom: 12 }}>
                      <CodeExecutor 
                        code={step.code}
                        sessionId={sessionId}
                        stepTitle={step.title}
                      />
                    </div>
                  )}

                  {/* 输出（兼容 output 和 result.stdout）- 使用 Markdown 渲染 */}
                  {(step.output || (step.result?.stdout && step.result.stdout.length > 0)) && (
                    <div style={{ marginBottom: 12 }}>
                      <Text strong style={{ display: 'block', marginBottom: 8 }}>
                        <PlayCircleOutlined /> 执行输出：
                      </Text>
                      <div style={{ 
                        background: '#fafafa', 
                        padding: 16, 
                        borderRadius: 6,
                        border: '1px solid #f0f0f0',
                        fontSize: 14,
                        lineHeight: 1.6
                      }}>
                        {/* 优先显示 result.stdout，否则显示 output */}
                        {step.result?.stdout && step.result.stdout.length > 0 ? (
                          step.result.stdout.map((line, lineIdx) => (
                            <div key={lineIdx} className="markdown-content">
                              <ReactMarkdown>{line}</ReactMarkdown>
                            </div>
                          ))
                        ) : (
                          <div className="markdown-content">
                            <ReactMarkdown>{step.output || ''}</ReactMarkdown>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* 错误信息 */}
                  {step.error && (
                    <Alert
                      type="error"
                      message="执行错误"
                      description={step.error.message || JSON.stringify(step.error)}
                      icon={<BugOutlined />}
                      showIcon
                      style={{ marginBottom: 12 }}
                    />
                  )}

                  {/* 执行结果 - 图表 */}
                  {step.result?.data && step.result.data.length > 0 && (
                    <div style={{ marginBottom: 12 }}>
                      <Text strong style={{ display: 'block', marginBottom: 8 }}>
                        📊 生成的图表：
                      </Text>
                      {step.result.data.map((item, dataIdx) => {
                        // Jupyter 原始格式：item.data 包含 'image/png', 'text/html' 等
                        const dataContent = item.data || item
                        
                        // 判断是图表还是 HTML 表格
                        if (dataContent['image/png']) {
                          return (
                            <div key={dataIdx} style={{ marginBottom: 12, position: 'relative' }}>
                              <img 
                                src={`data:image/png;base64,${dataContent['image/png']}`}
                                alt={`图表 ${dataIdx + 1}`}
                                style={{ 
                                  maxWidth: '100%', 
                                  borderRadius: 4,
                                  border: '1px solid #d9d9d9',
                                }}
                              />
                              <Button
                                type="primary"
                                size="small"
                                icon={<DownloadOutlined />}
                                onClick={() => downloadChart(dataContent['image/png'], `step-${idx + 1}-chart-${dataIdx + 1}.png`)}
                                style={{ marginTop: 8 }}
                              >
                                下载图表
                              </Button>
                            </div>
                          )
                        } else if (dataContent['text/html']) {
                          return (
                            <div 
                              key={dataIdx}
                              dangerouslySetInnerHTML={{ __html: dataContent['text/html'] }}
                              style={{ marginBottom: 8, overflow: 'auto' }}
                            />
                          )
                        } else if (item.type === 'image/png') {
                          // 兼容处理后的格式
                          return (
                            <div key={dataIdx} style={{ marginBottom: 12, position: 'relative' }}>
                              <img 
                                src={`data:image/png;base64,${item.content}`}
                                alt={`图表 ${dataIdx + 1}`}
                                style={{ 
                                  maxWidth: '100%', 
                                  borderRadius: 4,
                                  border: '1px solid #d9d9d9',
                                }}
                              />
                              <Button
                                type="primary"
                                size="small"
                                icon={<DownloadOutlined />}
                                onClick={() => downloadChart(item.content, `step-${idx + 1}-chart-${dataIdx + 1}.png`)}
                                style={{ marginTop: 8 }}
                              >
                                下载图表
                              </Button>
                            </div>
                          )
                        } else if (item.type === 'text/html') {
                          // 兼容处理后的格式
                          return (
                            <div 
                              key={dataIdx}
                              dangerouslySetInnerHTML={{ __html: item.content }}
                              style={{ marginBottom: 8, overflow: 'auto' }}
                            />
                          )
                        }
                        return null
                      })}
                    </div>
                  )}

                  {/* 执行状态提示 */}
                  {step.status === 'success' && !step.error && (
                    <div style={{ 
                      padding: '8px 12px', 
                      background: '#f6ffed', 
                      border: '1px solid #b7eb8f',
                      borderRadius: 4,
                      color: '#52c41a'
                    }}>
                      <CheckCircleOutlined /> 执行成功
                    </div>
                  )}
                </Panel>
              ))}
              </Collapse>
            </Panel>
          </Collapse>
        )}

        {/* 分析结果 */}
        {hasResult && (
          <Card 
            size="small" 
            title={<Text strong>📊 分析结果</Text>}
            style={{ marginBottom: 12 }}
          >
            {/* 1. 图表（最先显示）*/}
            {conv.result.charts && conv.result.charts.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Text strong style={{ display: 'block', marginBottom: 12, fontSize: 16 }}>
                  📊 数据可视化
                </Text>
                {conv.result.charts.map((chart, idx) => (
                  <div key={idx} style={{ marginBottom: 16, position: 'relative' }}>
                    <img 
                      src={`data:image/png;base64,${chart.data}`}
                      alt={`图表 ${idx + 1}`}
                      style={{ 
                        maxWidth: '100%', 
                        borderRadius: 4,
                        border: '1px solid #d9d9d9',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                      }}
                    />
                    <Button
                      type="primary"
                      size="small"
                      icon={<DownloadOutlined />}
                      onClick={() => downloadChart(chart.data, `chart-${idx + 1}.png`)}
                      style={{ marginTop: 8 }}
                    >
                      下载图表
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* 2. 图表解释（文字分析）- 使用 Markdown 渲染 */}
            {conv.result.text && conv.result.text.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Text strong style={{ display: 'block', marginBottom: 12, fontSize: 16 }}>
                  📋 数据分析
                </Text>
                <div style={{ 
                  background: '#fafafa', 
                  padding: 20, 
                  borderRadius: 8,
                  border: '1px solid #f0f0f0',
                  fontSize: 14,
                  lineHeight: 1.8
                }}>
                  {conv.result.text.map((text, idx) => (
                    <div key={idx} className="markdown-content">
                      <ReactMarkdown>{text}</ReactMarkdown>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* HTML 表格 */}
            {conv.result.data && conv.result.data.length > 0 && (
              <div>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>📋 数据表格：</Text>
                {conv.result.data.map((item, idx) => (
                  <div 
                    key={idx}
                    dangerouslySetInnerHTML={{ __html: item.content }}
                    style={{ marginBottom: 8, overflow: 'auto' }}
                  />
                ))}
              </div>
            )}
          </Card>
        )}

        {/* 3. AI 总结（最后显示）*/}
        {conv.summary && (
          <Card 
            size="small" 
            title={
              <Text strong style={{ fontSize: 16 }}>
                💡 智能洞察
              </Text>
            }
            style={{ 
              background: '#f6ffed', 
              borderColor: '#b7eb8f',
              marginBottom: 12 
            }}
            headStyle={{ background: '#f6ffed', borderBottom: '1px solid #b7eb8f' }}
          >
            <div className="markdown-content" style={{ fontSize: 14, lineHeight: 1.8 }}>
              <ReactMarkdown>{conv.summary}</ReactMarkdown>
            </div>
          </Card>
        )}
      </div>
    )
  }

  if (conversations.length === 0) {
    return (
      <div className="empty-conversation">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <div>
              <p>还没有对话记录</p>
              <p style={{ fontSize: '13px', color: '#8c8c8c' }}>
                👇 在下方输入框描述你的数据分析需求开始吧！
              </p>
            </div>
          }
        />
      </div>
    )
  }

  return (
    <div className="conversation-list">
      {conversations.map((conv, index) => (
        <div
          key={index}
          className={`conversation-item ${conv.type === 'user' ? 'user-message' : 'agent-message'}`}
        >
          <div className="message-avatar">
            <Avatar
              icon={conv.type === 'user' ? <UserOutlined /> : <RobotOutlined />}
              style={{
                backgroundColor: conv.type === 'user' ? '#1677ff' : '#52c41a',
              }}
            />
          </div>

          <div className="message-content">
            <div className="message-header">
              <Space>
                <span className="message-sender">
                  {conv.type === 'user' ? '你' : 'AI Agent'}
                </span>
                <span className="message-time">
                  {dayjs(conv.timestamp).format('HH:mm:ss')}
                </span>
                {conv.selectedColumns && conv.selectedColumns.length > 0 && (
                  <Tag color="blue" style={{ fontSize: '11px' }}>
                    使用 {conv.selectedColumns.length} 个字段
                  </Tag>
                )}
              </Space>
            </div>

            {conv.type === 'user' ? (
              <div className="message-body">
                <p>{conv.content}</p>
              </div>
            ) : (
              renderAgentMessage(conv)
            )}
          </div>
        </div>
      ))}

      {/* Agent 思考中（执行过程）*/}
      {agentExecuting && (
        <div className="conversation-item agent-message agent-thinking">
          <div className="message-avatar">
            <Avatar
              icon={<RobotOutlined />}
              style={{ backgroundColor: '#52c41a' }}
            />
          </div>

          <div className="message-content">
            <div className="message-header">
              <Space>
                <span className="message-sender">AI Agent</span>
                <Tag color="processing" icon={<LoadingOutlined />}>
                  思考中...
                </Tag>
              </Space>
            </div>

            <div className="agent-thinking-content">
              {/* 调试信息 */}
              {agentSteps.length === 0 && (
                <div style={{ padding: '20px', background: '#fff3cd', border: '1px solid #ffc107', borderRadius: 4, marginBottom: 12 }}>
                  <Text style={{ fontSize: 14 }}>
                    ⏳ 等待后端响应... (agentSteps: {agentSteps.length} 个)
                  </Text>
                </div>
              )}
              
              <Collapse
                activeKey={agentSteps.map((_, idx) => `step-${idx}`)}
                ghost
                style={{ background: 'transparent' }}
              >
                {agentSteps.map((step, idx) => {
                  console.log(`🔍 [渲染步骤 ${idx}]:`, {
                    title: step.title,
                    status: step.status,
                    hasOutput: !!step.output,
                    outputLength: step.output?.length || 0,
                    hasCode: !!step.code
                  })
                  return (
                  <Panel
                    key={`step-${idx}-${step.output?.length || 0}-${step.code?.length || 0}`}
                    header={
                      <Space>
                        {getStepIcon(step)}
                        <Text strong>{step.title || `步骤 ${idx + 1}`}</Text>
                        {step.status === 'running' && (
                          <Tag color="processing" size="small">执行中</Tag>
                        )}
                        {step.status === 'success' && (
                          <Tag color="success" size="small">完成</Tag>
                        )}
                        {step.status === 'failed' && (
                          <Tag color="error" size="small">失败</Tag>
                        )}
                      </Space>
                    }
                    style={{ marginBottom: 8 }}
                  >
                    {/* AI 思考过程（流式输出） - 修改条件：running 状态下总是显示 output */}
                    {step.output && step.status === 'running' && (
                      <div style={{ marginBottom: 12 }}>
                        <Text strong style={{ display: 'block', marginBottom: 8 }}>
                          <LoadingOutlined style={{ marginRight: 6 }} />
                          AI 思考过程：
                        </Text>
                        <Alert
                          type="info"
                          message={
                            <div style={{ whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.6, fontFamily: 'monospace' }}>
                              {step.output}
                            </div>
                          }
                          style={{ background: '#f0f5ff', border: '1px solid #adc6ff' }}
                          showIcon={false}
                        />
                      </div>
                    )}
                    
                    {/* 代码 */}
                    {step.code && (
                      <div style={{ marginBottom: 12 }}>
                        <Text strong style={{ display: 'block', marginBottom: 4 }}>
                          <CodeOutlined /> 生成的代码：
                        </Text>
                        <CodeExecutor
                          code={step.code}
                          sessionId={sessionId}
                          stepTitle={step.title}
                        />
                      </div>
                    )}

                    {/* 执行输出 */}
                    {((step.output && step.code) || (step.result?.stdout && step.result.stdout.length > 0)) && (
                      <div style={{ marginBottom: 12 }}>
                        <Text strong style={{ display: 'block', marginBottom: 8 }}>
                          <PlayCircleOutlined /> 执行输出：
                        </Text>
                        <div style={{ 
                          background: '#fafafa', 
                          padding: 16, 
                          borderRadius: 6,
                          border: '1px solid #f0f0f0',
                          fontSize: 14,
                          lineHeight: 1.6
                        }}>
                          {step.result?.stdout && step.result.stdout.length > 0 ? (
                            step.result.stdout.map((line, lineIdx) => (
                              <div key={lineIdx} className="markdown-content">
                                <ReactMarkdown>{line}</ReactMarkdown>
                              </div>
                            ))
                          ) : (
                            <div className="markdown-content">
                              <ReactMarkdown>{step.output || ''}</ReactMarkdown>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* 图表渲染状态 */}
                    {step.status === 'running' && step.code && step.code.includes('plt.') && (
                      <Alert
                        type="info"
                        message={
                          <Space>
                            <LoadingOutlined />
                            <span>图表渲染中...</span>
                          </Space>
                        }
                        style={{ marginBottom: 12 }}
                        showIcon={false}
                      />
                    )}

                    {/* 错误 */}
                    {step.error && (
                      <Alert
                        type="error"
                        message="执行错误"
                        description={
                          <div>
                            <Paragraph style={{ marginBottom: 8 }}>
                              <Text strong>错误类型：</Text>
                              {step.error.ename || '未知错误'}
                            </Paragraph>
                            <Paragraph>
                              <Text strong>错误信息：</Text>
                              <pre style={{ margin: 0, fontSize: '12px' }}>
                                {step.error.evalue || step.error.message || '无详细信息'}
                              </pre>
                            </Paragraph>
                          </div>
                        }
                        style={{ marginBottom: 12 }}
                      />
                    )}
                  </Panel>
                  )
                })}
              </Collapse>
            </div>
          </div>
        </div>
      )}
      
      {/* 滚动锚点 */}
      <div ref={listEndRef} style={{ height: '1px' }} />
    </div>
  )
}

export default ConversationList

