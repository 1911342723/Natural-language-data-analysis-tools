import { useState, useEffect } from 'react'
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

  // 监听步骤变化，自动更新当前步骤
  useEffect(() => {
    if (agentSteps.length > 0) {
      setCurrentStep(agentSteps.length - 1)
    }
  }, [agentSteps.length])

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
            defaultActiveKey={[currentStep]}
            activeKey={[currentStep]}
            className="execution-details"
          >
            {agentSteps.map((step, index) => (
              <Panel
                key={index}
                header={
                  <Space>
                    {getStepIcon(step)}
                    <Text strong>{step.title || `步骤 ${index + 1}`}</Text>
                    <Tag color={step.status === 'success' ? 'success' : step.status === 'failed' ? 'error' : 'processing'}>
                      {step.status}
                    </Tag>
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

