import { useState } from 'react'
import { Button, Card, Alert, Space, message, Spin } from 'antd'
import { PlayCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, DownloadOutlined } from '@ant-design/icons'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { executeCode } from '@/services/api'
import './CodeExecutor.css'

/**
 * 可执行的代码块组件
 * @param {string} code - Python 代码
 * @param {string} sessionId - Jupyter Session ID
 * @param {string} stepTitle - 步骤标题（可选）
 */
function CodeExecutor({ code, sessionId, stepTitle }) {
  const [executing, setExecuting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  // 下载图表
  const downloadChart = (base64Data, fileName = 'chart.png') => {
    try {
      const link = document.createElement('a')
      link.href = `data:image/png;base64,${base64Data}`
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      message.success('图表下载成功')
    } catch (err) {
      console.error('图表下载失败:', err)
      message.error('图表下载失败')
    }
  }

  const handleExecute = async () => {
    if (!sessionId) {
      message.error('Session 未创建，请先上传数据')
      return
    }

    setExecuting(true)
    setError(null)
    
    try {
      const response = await executeCode(sessionId, code, 60)
      const execResult = response.data.data
      
      setResult(execResult)
      
      if (execResult.error) {
        message.error('代码执行失败')
      } else {
        message.success('代码执行成功')
      }
    } catch (err) {
      console.error('代码执行失败:', err)
      setError(err.message || '执行失败')
      message.error('代码执行失败')
    } finally {
      setExecuting(false)
    }
  }

  return (
    <Card
      size="small"
      className="code-executor-card"
      title={
        <Space>
          <PlayCircleOutlined />
          <span>{stepTitle || '生成的代码'}</span>
        </Space>
      }
      extra={
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={handleExecute}
          loading={executing}
          disabled={!sessionId}
          size="small"
        >
          运行代码
        </Button>
      }
    >
      {/* 代码显示 */}
      <SyntaxHighlighter
        language="python"
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          borderRadius: 4,
          fontSize: 13,
          maxHeight: 400,
          overflow: 'auto',
        }}
      >
        {code}
      </SyntaxHighlighter>

      {/* 执行中提示 */}
      {executing && (
        <div style={{ marginTop: 12, textAlign: 'center' }}>
          <Spin tip="代码执行中..." />
        </div>
      )}

      {/* 执行结果 */}
      {result && !executing && (
        <div style={{ marginTop: 12 }}>
          {/* 错误信息 */}
          {result.error && (
            <Alert
              type="error"
              message={
                <Space>
                  <CloseCircleOutlined />
                  <span>执行错误: {result.error.ename}</span>
                </Space>
              }
              description={
                <div>
                  <div><strong>{result.error.evalue}</strong></div>
                  {result.error.traceback && result.error.traceback.length > 0 && (
                    <pre style={{ 
                      marginTop: 8,
                      padding: 8,
                      background: '#f5f5f5',
                      borderRadius: 4,
                      fontSize: 12,
                      overflow: 'auto',
                      maxHeight: 200,
                    }}>
                      {result.error.traceback.join('\n')}
                    </pre>
                  )}
                </div>
              }
              showIcon
              style={{ marginBottom: 12 }}
            />
          )}

          {/* 成功信息 */}
          {!result.error && (
            <Alert
              type="success"
              message={
                <Space>
                  <CheckCircleOutlined />
                  <span>执行成功</span>
                </Space>
              }
              showIcon
              style={{ marginBottom: 12 }}
            />
          )}

          {/* 标准输出 */}
          {result.stdout && result.stdout.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontWeight: 'bold', marginBottom: 4 }}>📝 标准输出：</div>
              <pre style={{
                background: '#f5f5f5',
                padding: 12,
                borderRadius: 4,
                margin: 0,
                whiteSpace: 'pre-wrap',
                fontSize: 13,
                maxHeight: 300,
                overflow: 'auto',
              }}>
                {result.stdout.join('')}
              </pre>
            </div>
          )}

          {/* 错误输出 */}
          {result.stderr && result.stderr.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontWeight: 'bold', marginBottom: 4 }}>⚠️ 错误输出：</div>
              <pre style={{
                background: '#fff2f0',
                padding: 12,
                borderRadius: 4,
                margin: 0,
                whiteSpace: 'pre-wrap',
                fontSize: 13,
                color: '#cf1322',
                maxHeight: 300,
                overflow: 'auto',
              }}>
                {result.stderr.join('')}
              </pre>
            </div>
          )}

          {/* 数据输出（图表、表格等） */}
          {result.data && result.data.length > 0 && (
            <div>
              <div style={{ fontWeight: 'bold', marginBottom: 4 }}>📊 可视化输出：</div>
              {result.data.map((item, idx) => (
                <div key={idx} style={{ marginBottom: 12 }}>
                  {/* HTML 表格 */}
                  {item.data['text/html'] && (
                    <div
                      dangerouslySetInnerHTML={{ __html: item.data['text/html'] }}
                      style={{
                        overflow: 'auto',
                        border: '1px solid #d9d9d9',
                        borderRadius: 4,
                        padding: 8,
                      }}
                    />
                  )}
                  
                  {/* PNG 图片 */}
                  {item.data['image/png'] && (
                    <div>
                      <img
                        src={`data:image/png;base64,${item.data['image/png']}`}
                        alt={`输出 ${idx + 1}`}
                        style={{ 
                          maxWidth: '100%', 
                          borderRadius: 4,
                          border: '1px solid #d9d9d9',
                          marginBottom: 8,
                        }}
                      />
                      <Button
                        type="primary"
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => downloadChart(item.data['image/png'], `chart-${idx + 1}.png`)}
                      >
                        下载图表
                      </Button>
                    </div>
                  )}
                  
                  {/* 纯文本 */}
                  {item.data['text/plain'] && !item.data['text/html'] && !item.data['image/png'] && (
                    <pre style={{
                      background: '#f5f5f5',
                      padding: 12,
                      borderRadius: 4,
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      fontSize: 13,
                    }}>
                      {item.data['text/plain']}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 错误信息 */}
      {error && !executing && (
        <Alert
          type="error"
          message="执行失败"
          description={error}
          showIcon
          style={{ marginTop: 12 }}
        />
      )}
    </Card>
  )
}

export default CodeExecutor

