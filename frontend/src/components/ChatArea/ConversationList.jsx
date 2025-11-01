import { useState, useEffect, useRef } from 'react'
import { Empty, Avatar, Space, Tag, Collapse, Typography, Alert, Card, Button, Dropdown, message, Input, Modal } from 'antd'
import html2pdf from 'html2pdf.js'
import JSZip from 'jszip'
import { saveAs } from 'file-saver'
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
  BarChartOutlined,
  FileTextOutlined,
  TableOutlined,
  BulbOutlined,
  ClockCircleOutlined,
  FileMarkdownOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  CopyOutlined,
  EditOutlined,
  CheckOutlined,
} from '@ant-design/icons'
import useAppStore from '@/store/useAppStore'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
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
  const [activeStepKeys, setActiveStepKeys] = useState([])  // 控制步骤展开/收缩
  const [executingCode, setExecutingCode] = useState({})  // 正在执行的代码状态
  const [showResultCode, setShowResultCode] = useState({})  // 显示结果代码：{ convId: true/false }
  const [editingResultCode, setEditingResultCode] = useState({})  // 编辑结果代码：{ convId: code }
  
  // 监听 agentSteps 变化，强制重新渲染（不再处理滚动，由 ChatArea 处理）
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

  // 导出分析结果为 Markdown（打包图表）
  const exportAsMarkdown = async (conv) => {
    try {
      message.loading({ content: '正在打包报告和图表...', key: 'md-export', duration: 0 })

      const zip = new JSZip()
      
      // 生成 Markdown 内容
      let markdown = `# 数据分析报告\n\n`
      markdown += `**生成时间**: ${dayjs(conv.timestamp).format('YYYY-MM-DD HH:mm:ss')}\n\n`
      markdown += `---\n\n`

      // 添加图表（引用图片文件）
      if (conv.result?.charts && conv.result.charts.length > 0) {
        markdown += `## 数据可视化\n\n`
        conv.result.charts.forEach((chart, idx) => {
          const chartFileName = `chart-${idx + 1}.png`
          markdown += `![图表 ${idx + 1}](./charts/${chartFileName})\n\n`
          
          // 将图表添加到 ZIP 的 charts 文件夹
          const base64Data = chart.data.replace(/^data:image\/\w+;base64,/, '')
          zip.folder('charts').file(chartFileName, base64Data, { base64: true })
        })
      }

      // 添加数据分析内容
      if (conv.result?.text && conv.result.text.length > 0) {
        markdown += `## 数据分析\n\n`
        conv.result.text.forEach(text => {
          markdown += `${text}\n\n`
        })
      }

      // 添加 AI 总结
      if (conv.summary) {
        markdown += `## 智能洞察\n\n`
        markdown += `${conv.summary}\n\n`
      }

      markdown += `---\n\n*此报告由 AI 数据分析系统自动生成*\n`

      // 添加 Markdown 文件到 ZIP
      zip.file('数据分析报告.md', markdown)

      // 生成 ZIP 并下载
      const content = await zip.generateAsync({ type: 'blob' })
      saveAs(content, `数据分析报告_${dayjs().format('YYYYMMDD_HHmmss')}.zip`)
      
      message.success({ content: '报告导出成功！', key: 'md-export', duration: 2 })
    } catch (error) {
      console.error('Markdown 导出失败:', error)
      message.error({ content: 'Markdown 导出失败，请重试', key: 'md-export', duration: 2 })
    }
  }

  // 导出分析结果为 HTML
  const exportAsHTML = (conv) => {
    let html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>数据分析报告</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; line-height: 1.6; color: #333; }
    h1 { color: #1890ff; border-bottom: 3px solid #1890ff; padding-bottom: 10px; }
    h2 { color: #52c41a; margin-top: 30px; border-left: 4px solid #52c41a; padding-left: 10px; }
    img { max-width: 100%; height: auto; border: 1px solid #d9d9d9; border-radius: 4px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .metadata { color: #8c8c8c; font-size: 14px; margin-bottom: 30px; }
    .content { background: #fafafa; padding: 20px; border-radius: 8px; margin: 20px 0; }
    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
    th, td { border: 1px solid #d9d9d9; padding: 12px; text-align: left; }
    th { background: #fafafa; font-weight: 600; }
    .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #d9d9d9; color: #8c8c8c; font-size: 14px; text-align: center; }
  </style>
</head>
<body>
  <h1>数据分析报告</h1>
  <div class="metadata">生成时间: ${dayjs(conv.timestamp).format('YYYY-MM-DD HH:mm:ss')}</div>
  <hr>`

    // 添加图表
    if (conv.result?.charts && conv.result.charts.length > 0) {
      html += `<h2>数据可视化</h2>`
      conv.result.charts.forEach((chart, idx) => {
        html += `<img src="data:image/png;base64,${chart.data}" alt="图表 ${idx + 1}" />`
      })
    }

    // 添加数据分析内容
    if (conv.result?.text && conv.result.text.length > 0) {
      html += `<h2>数据分析</h2><div class="content">`
      conv.result.text.forEach(text => {
        // 简单的 Markdown 转 HTML（换行）
        const htmlText = text.replace(/\n/g, '<br>')
        html += `<p>${htmlText}</p>`
      })
      html += `</div>`
    }

    // 添加数据表格
    if (conv.result?.data && conv.result.data.length > 0) {
      html += `<h2>数据表格</h2>`
      conv.result.data.forEach(item => {
        html += item.content
      })
    }

    // 添加 AI 总结
    if (conv.summary) {
      html += `<h2>智能洞察</h2><div class="content">`
      // 简单的 Markdown 转 HTML
      const htmlSummary = conv.summary
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
      html += htmlSummary
      html += `</div>`
    }

    html += `<div class="footer">此报告由 AI 数据分析系统自动生成</div>
</body>
</html>`

    // 创建下载
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `数据分析报告_${dayjs().format('YYYYMMDD_HHmmss')}.html`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // 导出分析结果为 PDF
  const exportAsPDF = async (conv) => {
    try {
      message.loading({ content: '正在生成 PDF，请稍候...', key: 'pdf-export', duration: 0 })

      // 创建 HTML 内容
      let htmlContent = `<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 30px; color: #333; background: white;">
<h1 style="color: #1890ff; border-bottom: 3px solid #1890ff; padding-bottom: 10px; margin-bottom: 10px;">数据分析报告</h1>
<p style="color: #8c8c8c; font-size: 14px; margin-bottom: 30px;">生成时间: ${dayjs(conv.timestamp).format('YYYY-MM-DD HH:mm:ss')}</p>`

      // 添加图表
      if (conv.result?.charts && conv.result.charts.length > 0) {
        htmlContent += `<h2 style="color: #52c41a; margin-top: 30px; border-left: 4px solid #52c41a; padding-left: 10px; margin-bottom: 15px;">数据可视化</h2>`
        conv.result.charts.forEach((chart, idx) => {
          htmlContent += `<div style="margin: 20px 0; page-break-inside: avoid;"><img src="data:image/png;base64,${chart.data}" style="max-width: 700px; width: 100%; height: auto; border: 1px solid #d9d9d9;" /></div>`
        })
      }

      // 添加数据分析内容
      if (conv.result?.text && conv.result.text.length > 0) {
        htmlContent += `<h2 style="color: #52c41a; margin-top: 30px; border-left: 4px solid #52c41a; padding-left: 10px; margin-bottom: 15px;">数据分析</h2>`
        htmlContent += `<div style="background: #fafafa; padding: 20px; border-radius: 4px; margin: 20px 0; line-height: 1.6;">`
        conv.result.text.forEach(text => {
          const htmlText = text.replace(/\n/g, '<br>')
          htmlContent += `<p style="margin: 10px 0;">${htmlText}</p>`
        })
        htmlContent += `</div>`
      }

      // 添加 AI 总结
      if (conv.summary) {
        htmlContent += `<h2 style="color: #52c41a; margin-top: 30px; border-left: 4px solid #52c41a; padding-left: 10px; margin-bottom: 15px;">智能洞察</h2>`
        htmlContent += `<div style="background: #f6ffed; padding: 20px; border-radius: 4px; margin: 20px 0; line-height: 1.6;">`
        const htmlSummary = conv.summary
          .replace(/\n/g, '<br>')
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.*?)\*/g, '<em>$1</em>')
        htmlContent += htmlSummary
        htmlContent += `</div>`
      }

      htmlContent += `<div style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #d9d9d9; color: #8c8c8c; font-size: 12px; text-align: center;">此报告由 AI 数据分析系统自动生成</div></div>`

      // 创建临时 div
      const tempDiv = document.createElement('div')
      tempDiv.innerHTML = htmlContent
      tempDiv.style.position = 'fixed'
      tempDiv.style.top = '0'
      tempDiv.style.left = '0'
      tempDiv.style.width = '210mm'  // A4 宽度
      tempDiv.style.background = 'white'
      tempDiv.style.zIndex = '-1000'
      tempDiv.style.opacity = '0'
      document.body.appendChild(tempDiv)

      // 等待图片加载
      await new Promise(resolve => setTimeout(resolve, 500))

      // 配置 PDF 选项
      const opt = {
        margin: [10, 10, 10, 10],
        filename: `数据分析报告_${dayjs().format('YYYYMMDD_HHmmss')}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { 
          scale: 2, 
          useCORS: true,
          logging: false,
          letterRendering: true,
          allowTaint: true
        },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
      }

      // 生成 PDF
      await html2pdf().set(opt).from(tempDiv).save()

      // 清理
      document.body.removeChild(tempDiv)
      message.success({ content: 'PDF 导出成功！', key: 'pdf-export', duration: 2 })
    } catch (error) {
      console.error('PDF 导出失败:', error)
      message.error({ content: 'PDF 导出失败，请重试', key: 'pdf-export', duration: 2 })
    }
  }

  // 复制代码
  const copyCode = (code) => {
    navigator.clipboard.writeText(code).then(() => {
      message.success('代码已复制到剪贴板')
    }).catch(() => {
      message.error('复制失败，请重试')
    })
  }

  // 获取生成图表的代码（从 steps 中找到执行代码的步骤）
  const getChartGenerationCode = (conv) => {
    if (!conv.steps || conv.steps.length === 0) return null
    
    // 找到包含代码的步骤（通常是"执行代码"或"生成代码"步骤）
    const codeStep = conv.steps.find(step => 
      step.code && (step.title?.includes('代码') || step.title?.includes('执行'))
    )
    
    return codeStep?.code || null
  }

  // 执行结果中的代码（重新生成图表）
  const executeResultCode = async (convId, code) => {
    if (!sessionId) {
      message.error('会话未初始化')
      return
    }

    try {
      setExecutingCode({ ...executingCode, [`result-${convId}`]: true })
      message.loading({ content: '正在重新生成图表...', key: `execute-result-${convId}`, duration: 0 })

      const response = await fetch('http://localhost:8000/api/jupyter/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, code })
      })

      const result = await response.json()
      
      if (result.success) {
        // 更新对话中的图表
        const updatedConvs = conversations.map(c => {
          if (c.id === convId) {
            return {
              ...c,
              result: {
                ...c.result,
                charts: result.result?.charts || [],
                text: result.result?.text || c.result.text
              }
            }
          }
          return c
        })
        
        useAppStore.setState({ conversations: updatedConvs })
        
        message.success({ content: '图表重新生成成功！', key: `execute-result-${convId}`, duration: 2 })
        
        // 退出编辑模式
        const newEditingResultCode = { ...editingResultCode }
        delete newEditingResultCode[convId]
        setEditingResultCode(newEditingResultCode)
      } else {
        message.error({ content: `执行失败: ${result.error}`, key: `execute-result-${convId}`, duration: 3 })
      }
    } catch (error) {
      console.error('执行代码失败:', error)
      message.error({ content: '执行失败，请检查网络连接', key: `execute-result-${convId}`, duration: 3 })
    } finally {
      setExecutingCode({ ...executingCode, [`result-${convId}`]: false })
    }
  }

  // 渲染 Agent 消息（包含步骤和结果）
  const renderAgentMessage = (conv) => {
    const hasSteps = conv.steps && conv.steps.length > 0
    const hasResult = conv.result && Object.keys(conv.result).length > 0

    return (
      <div>
        {/* 基本消息 */}
        <div className="message-body markdown-container" style={{ marginBottom: hasSteps ? 12 : 0 }}>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
          >
            {conv.content}
          </ReactMarkdown>
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
                            <div key={lineIdx} className="markdown-content markdown-container">
                              <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                                {line}
                              </ReactMarkdown>
                            </div>
                          ))
                        ) : (
                          <div className="markdown-content markdown-container">
                            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                              {step.output || ''}
                            </ReactMarkdown>
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
                        <BarChartOutlined /> 生成的图表
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
            title={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text strong><BarChartOutlined /> 分析结果</Text>
                <Dropdown
                  menu={{
                    items: [
                      {
                        key: 'pdf',
                        label: '导出为 PDF',
                        icon: <FilePdfOutlined />,
                        onClick: () => exportAsPDF(conv)
                      },
                      {
                        key: 'html',
                        label: '导出为 HTML',
                        icon: <FileWordOutlined />,
                        onClick: () => exportAsHTML(conv)
                      },
                      {
                        key: 'markdown',
                        label: '导出为 Markdown',
                        icon: <FileMarkdownOutlined />,
                        onClick: () => exportAsMarkdown(conv)
                      }
                    ]
                  }}
                  placement="bottomRight"
                >
                  <Button
                    type="primary"
                    size="small"
                    icon={<DownloadOutlined />}
                  >
                    导出报告
                  </Button>
                </Dropdown>
              </div>
            }
            style={{ marginBottom: 12 }}
          >
            {/* 1. 图表（最先显示）*/}
            {conv.result.charts && conv.result.charts.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <Text strong style={{ fontSize: 16 }}>
                    <BarChartOutlined /> 数据可视化
                  </Text>
                  <Space>
                    {getChartGenerationCode(conv) && (
                      <Button
                        size="small"
                        icon={<CodeOutlined />}
                        onClick={() => setShowResultCode({ ...showResultCode, [conv.id]: !showResultCode[conv.id] })}
                      >
                        {showResultCode[conv.id] ? '隐藏代码' : '查看代码'}
                      </Button>
                    )}
                    {conv.result.charts.map((chart, idx) => (
                      <Button
                        key={idx}
                        type="primary"
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => downloadChart(chart.data, `chart-${idx + 1}.png`)}
                      >
                        下载图表 {conv.result.charts.length > 1 ? idx + 1 : ''}
                      </Button>
                    ))}
                  </Space>
                </div>
                
                {/* 代码编辑区域 */}
                {showResultCode[conv.id] && getChartGenerationCode(conv) && (
                  <div style={{ marginBottom: 16, padding: 12, background: '#fafafa', border: '1px solid #d9d9d9', borderRadius: 4 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <Text strong>
                        <CodeOutlined /> 图表生成代码
                      </Text>
                      <Space>
                        <Button
                          size="small"
                          icon={<CopyOutlined />}
                          onClick={() => copyCode(editingResultCode[conv.id] || getChartGenerationCode(conv))}
                        >
                          复制
                        </Button>
                        {!editingResultCode[conv.id] ? (
                          <Button
                            size="small"
                            icon={<EditOutlined />}
                            onClick={() => setEditingResultCode({ ...editingResultCode, [conv.id]: getChartGenerationCode(conv) })}
                          >
                            编辑
                          </Button>
                        ) : (
                          <>
                            <Button
                              size="small"
                              type="primary"
                              icon={<PlayCircleOutlined />}
                              loading={executingCode[`result-${conv.id}`]}
                              onClick={() => executeResultCode(conv.id, editingResultCode[conv.id])}
                            >
                              重新生成
                            </Button>
                            <Button
                              size="small"
                              onClick={() => {
                                const newEditingResultCode = { ...editingResultCode }
                                delete newEditingResultCode[conv.id]
                                setEditingResultCode(newEditingResultCode)
                              }}
                            >
                              取消
                            </Button>
                          </>
                        )}
                      </Space>
                    </div>
                    {editingResultCode[conv.id] ? (
                      <Input.TextArea
                        value={editingResultCode[conv.id]}
                        onChange={(e) => setEditingResultCode({ ...editingResultCode, [conv.id]: e.target.value })}
                        autoSize={{ minRows: 10, maxRows: 30 }}
                        style={{ 
                          fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                          fontSize: 13,
                          background: 'white'
                        }}
                      />
                    ) : (
                      <pre style={{ 
                        margin: 0, 
                        padding: 12,
                        background: 'white',
                        border: '1px solid #e8e8e8',
                        borderRadius: 4,
                        overflow: 'auto',
                        fontSize: 13,
                        lineHeight: 1.6,
                        fontFamily: 'Monaco, Consolas, "Courier New", monospace'
                      }}>
                        {getChartGenerationCode(conv)}
                      </pre>
                    )}
                  </div>
                )}
                
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
                  </div>
                ))}
              </div>
            )}

            {/* 2. 图表解释（文字分析）- 使用 Markdown 渲染 */}
            {conv.result.text && conv.result.text.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Text strong style={{ display: 'block', marginBottom: 12, fontSize: 16 }}>
                  <FileTextOutlined /> 数据分析
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
                    <div key={idx} className="markdown-content markdown-container">
                      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                        {text}
                      </ReactMarkdown>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* HTML 表格 */}
            {conv.result.data && conv.result.data.length > 0 && (
              <div>
                <Text strong style={{ display: 'block', marginBottom: 8 }}><TableOutlined /> 数据表格</Text>
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
                <BulbOutlined /> 智能洞察
              </Text>
            }
            style={{ 
              background: '#f6ffed', 
              borderColor: '#b7eb8f',
              marginBottom: 12 
            }}
            headStyle={{ background: '#f6ffed', borderBottom: '1px solid #b7eb8f' }}
          >
            <div className="markdown-content markdown-container" style={{ fontSize: 14, lineHeight: 1.8 }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                {conv.summary}
              </ReactMarkdown>
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
                在下方输入框描述你的数据分析需求开始吧！
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
              {/* 调试信息
              {agentSteps.length === 0 && (
                // <div style={{ padding: '20px', background: '#fff3cd', border: '1px solid #ffc107', borderRadius: 4, marginBottom: 12 }}>
                //   <Text style={{ fontSize: 14 }}>
                //     <ClockCircleOutlined spin /> 等待后端响应... (agentSteps: {agentSteps.length} 个)
                //   </Text>
                // </div>
              )}
               */}
              <Collapse
                activeKey={activeStepKeys}
                onChange={(keys) => {
                  console.log('👆 [ConversationList] 用户切换步骤面板:', keys)
                  setActiveStepKeys(keys)
                }}
                ghost
                style={{ background: 'transparent' }}
              >
                {agentSteps.map((step, idx) => {
                  console.log(`[渲染步骤 ${idx}]:`, {
                    title: step.title,
                    status: step.status,
                    hasOutput: !!step.output,
                    outputLength: step.output?.length || 0,
                    hasCode: !!step.code
                  })
                  return (
                  <Panel
                    key={`step-${idx}`}
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
                          <CodeOutlined /> 生成的代码
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
                              <div key={lineIdx} className="markdown-content markdown-container">
                                <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                                  {line}
                                </ReactMarkdown>
                              </div>
                            ))
                          ) : (
                            <div className="markdown-content markdown-container">
                              <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                                {step.output || ''}
                              </ReactMarkdown>
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
      
    </div>
  )
}

export default ConversationList

