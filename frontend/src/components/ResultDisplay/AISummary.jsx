import { Card, Typography, Space, Button } from 'antd'
import { 
  BulbOutlined, 
  CopyOutlined,
  CheckOutlined 
} from '@ant-design/icons'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import './AISummary.css'

const { Title, Paragraph } = Typography

function AISummary({ summary }) {
  const [copied, setCopied] = useState(false)

  // 复制总结内容
  const handleCopy = () => {
    navigator.clipboard.writeText(summary)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card className="ai-summary-card" bordered={false}>
      <div className="summary-header">
        <Space>
          <BulbOutlined className="summary-icon" />
          <Title level={4} style={{ margin: 0 }}>分析总结</Title>
        </Space>
        <Button
          icon={copied ? <CheckOutlined /> : <CopyOutlined />}
          onClick={handleCopy}
          size="small"
        >
          {copied ? '已复制' : '复制'}
        </Button>
      </div>

      <div className="summary-content">
        <ReactMarkdown>{summary}</ReactMarkdown>
      </div>

      <div className="summary-footer">
        <Space>
          <span className="footer-icon">🤖</span>
          <span className="footer-text">由 AI 自动生成</span>
        </Space>
      </div>
    </Card>
  )
}

export default AISummary


