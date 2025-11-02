import { useState } from 'react'
import { Select, Switch, Space, Tooltip, Typography, Divider } from 'antd'
import { 
  ExperimentOutlined, 
  BarChartOutlined, 
  PictureOutlined, 
  GlobalOutlined,
  InfoCircleOutlined 
} from '@ant-design/icons'
import ChartTypeSelector from './ChartTypeSelector'
import './ChartStyleSelector.css'

const { Text } = Typography

const CHART_STYLES = [
  {
    value: 'publication',
    label: '出版级',
    icon: <ExperimentOutlined />,
    description: '符合Nature/Science等期刊标准，300 DPI高清输出',
    features: ['300 DPI', '无衬线字体', '黑白打印友好']
  },
  {
    value: 'presentation',
    label: '演示风格',
    icon: <BarChartOutlined />,
    description: '适合会议展示和PPT，大字体、高对比度',
    features: ['大字体', '高对比度', '适合投影']
  },
  {
    value: 'web',
    label: 'Web风格',
    icon: <GlobalOutlined />,
    description: '适合网页展示，支持交互式图表',
    features: ['交互式', '彩色', '适合屏幕']
  }
]

function ChartStyleSelector({ 
  value, 
  onChange, 
  enableResearchMode, 
  onResearchModeChange,
  selectedChartTypes,
  onChartTypesChange,
  agentMode  // 新增：Agent 模式
}) {
  const selectedStyle = CHART_STYLES.find(s => s.value === value) || CHART_STYLES[0]

  return (
    <div className="chart-style-selector">
      <Space direction="vertical" style={{ width: '100%' }} size={4}>
        {/* 科研模式开关和图表类型选择器 */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', justifyContent: 'space-between' }}>
          <Space>
            <Switch 
              checked={enableResearchMode}
              onChange={onResearchModeChange}
              checkedChildren={<ExperimentOutlined />}
              unCheckedChildren={<PictureOutlined />}
            />
            <Text strong>科研模式</Text>
            <Tooltip title="启用科研模式后，将生成符合学术标准的图表和统计分析">
              <InfoCircleOutlined style={{ color: '#1890ff', cursor: 'pointer' }} />
            </Tooltip>
          </Space>
          
          {/* 图表类型选择器（仅在经典模式下可用） */}
          {agentMode === 'classic' && (
            <ChartTypeSelector 
              value={selectedChartTypes || []}
              onChange={onChartTypesChange}
            />
          )}
        </div>

        {/* 图表样式选择（仅在科研模式启用时显示） */}
        {enableResearchMode && (
          <>
            <Divider style={{ margin: '4px 0' }} />
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {/* 图表样式选择器 */}
              <Select
                value={value}
                onChange={onChange}
                style={{ flex: 1, minWidth: 120 }}
                size="small"
                placeholder="选择图表样式"
                options={CHART_STYLES.map(style => ({
                  value: style.value,
                  label: (
                    <Space size={4}>
                      {style.icon}
                      <span>{style.label}</span>
                    </Space>
                  )
                }))}
              />
            </div>

            {/* 选中样式的说明 - 紧凑显示 */}
            <div className="style-description">
              <Text type="secondary" style={{ fontSize: 11 }}>
                {selectedStyle.description}
              </Text>
            </div>
          </>
        )}
      </Space>
    </div>
  )
}

export default ChartStyleSelector

