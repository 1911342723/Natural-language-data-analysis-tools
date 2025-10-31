import { useState } from 'react'
import { Button, Space, Modal, Typography } from 'antd'
import { 
  DownloadOutlined, 
  ExpandOutlined,
  ZoomInOutlined 
} from '@ant-design/icons'
import './ChartResult.css'

const { Title } = Typography

function ChartResult({ chartBase64, chartTitle }) {
  const [previewVisible, setPreviewVisible] = useState(false)

  // 下载图表
  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = `data:image/png;base64,${chartBase64}`
    link.download = `图表_${new Date().getTime()}.png`
    link.click()
  }

  return (
    <div className="chart-result-container">
      {chartTitle && (
        <Title level={5} className="chart-title">
          {chartTitle}
        </Title>
      )}

      <div className="chart-actions">
        <Space>
          <Button
            icon={<ZoomInOutlined />}
            onClick={() => setPreviewVisible(true)}
            size="small"
          >
            查看大图
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={handleDownload}
            size="small"
          >
            下载图表
          </Button>
        </Space>
      </div>

      <div className="chart-wrapper">
        <img
          src={`data:image/png;base64,${chartBase64}`}
          alt={chartTitle || '分析图表'}
          className="chart-image"
          onClick={() => setPreviewVisible(true)}
        />
      </div>

      {/* 大图预览 Modal */}
      <Modal
        title={chartTitle || '图表预览'}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width="90%"
        centered
        className="chart-preview-modal"
      >
        <img
          src={`data:image/png;base64,${chartBase64}`}
          alt={chartTitle || '分析图表'}
          style={{ width: '100%', height: 'auto' }}
        />
      </Modal>
    </div>
  )
}

export default ChartResult


