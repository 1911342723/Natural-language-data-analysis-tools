import { useState, useEffect, useMemo } from 'react'
import { 
  Card, 
  Steps, 
  Spin, 
  Alert, 
  Button, 
  Space,
  Tag,
  Collapse,
  Typography 
} from 'antd'
import { 
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CodeOutlined,
  PlayCircleOutlined,
  BugOutlined,
  SyncOutlined
} from '@ant-design/icons'
import useAppStore from '@/store/useAppStore'
import { Editor } from '@monaco-editor/react'
import ResultDisplay from '../ResultDisplay/ResultDisplay'
import './AgentExecution.css'

const { Step } = Steps
const { Panel } = Collapse
const { Text, Paragraph } = Typography

function AgentExecution() {
  const {
    agentSteps,
    agentExecuting,
  } = useAppStore()

  const [currentStep, setCurrentStep] = useState(0)
  const [activeKeys, setActiveKeys] = useState([])  // 控制展开的面板，默认收缩

  // 监听步骤变化，自动更新当前步骤
  useEffect(() => {
    if (agentSteps.length > 0) {
      setCurrentStep(agentSteps.length - 1)
    }
  }, [agentSteps.length])

  // 用户手动切换面板展开/收缩
  const handlePanelChange = (keys) => {
    console.log('👆 [AgentExecution] 用户切换面板:', keys)
    console.log('  当前 activeKeys:', activeKeys)
    console.log('  新的 keys:', keys)
    setActiveKeys(keys)
  }
  
  // 使用 useMemo 缓存稳定的 key，避免频繁重新渲染导致点击失效
  const stableActiveKeys = useMemo(() => activeKeys, [JSON.stringify(activeKeys)])

  // 获取步骤状态
  const getStepStatus = (step) => {
    if (step.status === 'success') return 'finish'
    if (step.status === 'failed') return 'error'
    if (step.status === 'running') return 'process'
    return 'wait'
  }

  // 获取步骤图标
  const getStepIcon = (step) => {
    if (step.status === 'success') return <CheckCircleOutlined />
    if (step.status === 'failed') return <CloseCircleOutlined />
    if (step.status === 'running') return <LoadingOutlined />
    return null
  }

  return (
    <div className="agent-execution-container">
      <Card
        title={
          <Space>
            <SyncOutlined spin={agentExecuting} />
            <span>Agent 执行过程（实时）</span>
            {agentExecuting && <Tag color="processing">执行中</Tag>}
            {!agentExecuting && agentSteps.length > 0 && <Tag color="success">已完成</Tag>}
          </Space>
        }
        className="execution-card"
        size="small"
      >
        {/* 步骤流程 */}
        <Steps
          current={currentStep}
          size="small"
          className="execution-steps"
        >
          {agentSteps.map((step, index) => (
            <Step
              key={index}
              title={step.title || `步骤 ${index + 1}`}
              status={getStepStatus(step)}
              icon={getStepIcon(step)}
              description={step.description}
            />
          ))}
        </Steps>

        {/* 详细信息 */}
        {agentSteps.length > 0 && (
          <Collapse
            activeKey={stableActiveKeys}
            onChange={handlePanelChange}
            className="execution-details"
            style={{ pointerEvents: 'auto' }}
            collapsible="header"
            destroyInactivePanel={false}
          >
            {agentSteps.map((step, index) => (
              <Panel
                key={`step-${index}`}
                header={
                  <Space 
                    onClick={(e) => {
                      e.stopPropagation()
                      console.log(`🖱️ [AgentExecution] header 被点击: 步骤 #${index}`)
                      const newKeys = activeKeys.includes(index.toString()) 
                        ? activeKeys.filter(k => k !== index.toString())
                        : [...activeKeys, index.toString()]
                      handlePanelChange(newKeys)
                    }}
                    style={{ cursor: 'pointer', width: '100%' }}
                  >
                    {getStepIcon(step)}
                    <Text strong>{step.title || `步骤 ${index + 1}`}</Text>
                    <Tag color={step.status === 'success' ? 'success' : step.status === 'failed' ? 'error' : 'processing'}>
                      {step.status === 'success' ? '✅ 成功' : step.status === 'failed' ? '❌ 失败' : step.status === 'running' ? '⏳ 执行中' : '⏸️ 等待'}
                    </Tag>
                    {/* 收缩时显示简短预览 */}
                    {step.output && !activeKeys.includes(index.toString()) && step.status === 'running' && (
                      <Text type="secondary" style={{ fontSize: '12px', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {step.output.split('\n')[0].substring(0, 50)}
                      </Text>
                    )}
                  </Space>
                }
              >
                {/* 步骤描述 */}
                {step.description && (
                  <Paragraph style={{ marginBottom: 12 }}>
                    {step.description}
                  </Paragraph>
                )}

                {/* 生成的代码 */}
                {step.code && (
                  <div className="code-section">
                    <Space style={{ marginBottom: 8 }}>
                      <CodeOutlined />
                      <Text strong>生成的代码</Text>
                    </Space>
                    <Editor
                      height="200px"
                      language="python"
                      value={step.code}
                      options={{
                        readOnly: true,
                        minimap: { enabled: false },
                        fontSize: 13,
                        lineNumbers: 'on',
                        scrollBeyondLastLine: false,
                      }}
                      theme="vs-light"
                    />
                  </div>
                )}

                {/* 执行输出 */}
                {step.output && (
                  <div className="output-section">
                    <Space style={{ marginBottom: 8 }}>
                      <PlayCircleOutlined />
                      <Text strong>执行输出</Text>
                    </Space>
                    <pre className="output-content">{step.output}</pre>
                  </div>
                )}

                {/* 错误信息 */}
                {step.error && (
                  <Alert
                    type="error"
                    message="执行错误"
                    description={step.error}
                    icon={<BugOutlined />}
                    style={{ marginTop: 12 }}
                  />
                )}

                {/* 结果展示 */}
                {step.result && (
                  <div className="result-section">
                    <ResultDisplay result={step.result} />
                  </div>
                )}
              </Panel>
            ))}
          </Collapse>
        )}
      </Card>
    </div>
  )
}

export default AgentExecution

