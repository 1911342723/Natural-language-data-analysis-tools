import { useState } from 'react'
import { Modal, Checkbox, Space, Tag, Typography, Row, Col, Button, message } from 'antd'
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  DotChartOutlined,
  HeatMapOutlined,
  FundOutlined,
  BoxPlotOutlined,
  RadarChartOutlined,
  AppstoreOutlined
} from '@ant-design/icons'

const { Text, Title } = Typography

// 图表类型配置
export const CHART_TYPES = [
  {
    id: 'boxplot',
    name: '箱线图',
    icon: <BoxPlotOutlined style={{ fontSize: 18, color: '#1890ff' }} />,
    category: '分布分析',
    description: '展示数据分布、中位数、四分位数和异常值',
    适用场景: ['组间对比', '异常值检测', '分布差异'],
    数据类型: ['连续型数值 + 分类型'],
    示例: '比较不同专业的薪资分布'
  },
  {
    id: 'violinplot',
    name: '小提琴图',
    icon: <FundOutlined style={{ fontSize: 18, color: '#52c41a' }} />,
    category: '分布分析',
    description: '结合箱线图和核密度图，更详细展示数据分布',
    适用场景: ['分布形态对比', '多峰分布识别'],
    数据类型: ['连续型数值 + 分类型'],
    示例: '比较不同院系的成绩分布形态'
  },
  {
    id: 'histogram',
    name: '直方图',
    icon: <BarChartOutlined style={{ fontSize: 18, color: '#faad14' }} />,
    category: '分布分析',
    description: '展示数据的频率分布',
    适用场景: ['单变量分布', '正态性检验'],
    数据类型: ['连续型数值'],
    示例: '年龄分布、薪资分布'
  },
  {
    id: 'scatter',
    name: '散点图',
    icon: <DotChartOutlined style={{ fontSize: 18, color: '#13c2c2' }} />,
    category: '相关性分析',
    description: '展示两个连续变量之间的关系',
    适用场景: ['相关性分析', '趋势识别', '异常点检测'],
    数据类型: ['两个连续型数值'],
    示例: '身高与体重的关系'
  },
  {
    id: 'heatmap',
    name: '热力图',
    icon: <HeatMapOutlined style={{ fontSize: 18, color: '#f5222d' }} />,
    category: '相关性分析',
    description: '展示多变量之间的相关系数矩阵',
    适用场景: ['多变量相关性', '特征选择'],
    数据类型: ['多个连续型数值'],
    示例: '各科成绩之间的相关性'
  },
  {
    id: 'pairplot',
    name: '散点矩阵图',
    icon: <AppstoreOutlined style={{ fontSize: 18, color: '#722ed1' }} />,
    category: '相关性分析',
    description: '多变量两两散点图矩阵',
    适用场景: ['多变量关系探索', '数据预览'],
    数据类型: ['多个连续型数值'],
    示例: '探索身高、体重、年龄之间的关系'
  },
  {
    id: 'barplot',
    name: '柱状图',
    icon: <BarChartOutlined style={{ fontSize: 18, color: '#1890ff' }} />,
    category: '对比分析',
    description: '展示分类数据的数值对比',
    适用场景: ['类别对比', '排名展示', '计数统计'],
    数据类型: ['分类型 + 数值型'],
    示例: '各部门销售额对比'
  },
  {
    id: 'lineplot',
    name: '折线图',
    icon: <LineChartOutlined style={{ fontSize: 18, color: '#52c41a' }} />,
    category: '趋势分析',
    description: '展示数据随时间或有序变量的变化趋势',
    适用场景: ['时间序列', '趋势分析', '增长率'],
    数据类型: ['有序变量 + 数值型'],
    示例: '月度销售额趋势'
  },
  {
    id: 'pieplot',
    name: '饼图',
    icon: <PieChartOutlined style={{ fontSize: 18, color: '#faad14' }} />,
    category: '占比分析',
    description: '展示各部分占总体的比例',
    适用场景: ['比例展示', '构成分析'],
    数据类型: ['分类型（< 7个类别）'],
    示例: '市场份额分布'
  },
  {
    id: 'radarplot',
    name: '雷达图',
    icon: <RadarChartOutlined style={{ fontSize: 18, color: '#13c2c2' }} />,
    category: '多维对比',
    description: '展示多个维度的综合对比',
    适用场景: ['多维度评估', '能力对比', '产品对比'],
    数据类型: ['多个数值型维度'],
    示例: '学生综合能力评估'
  },
  {
    id: 'qqplot',
    name: 'QQ图',
    icon: <LineChartOutlined style={{ fontSize: 18, color: '#722ed1' }} />,
    category: '统计诊断',
    description: '检验数据是否符合正态分布',
    适用场景: ['正态性检验', '数据预处理'],
    数据类型: ['连续型数值'],
    示例: '检验薪资数据是否正态分布'
  },
  {
    id: 'residualplot',
    name: '残差图',
    icon: <DotChartOutlined style={{ fontSize: 18, color: '#f5222d' }} />,
    category: '统计诊断',
    description: '检验回归模型的拟合质量',
    适用场景: ['回归诊断', '模型评估'],
    数据类型: ['回归模型结果'],
    示例: '检验线性回归的假设'
  }
]

// 按类别分组
const groupChartsByCategory = () => {
  const grouped = {}
  CHART_TYPES.forEach(chart => {
    if (!grouped[chart.category]) {
      grouped[chart.category] = []
    }
    grouped[chart.category].push(chart)
  })
  return grouped
}

function ChartTypeSelector({ value = [], onChange }) {
  const [visible, setVisible] = useState(false)
  const [selectedTypes, setSelectedTypes] = useState(value)
  
  const groupedCharts = groupChartsByCategory()
  
  const handleOk = () => {
    if (selectedTypes.length === 0) {
      message.warning('请至少选择一种图表类型')
      return
    }
    onChange(selectedTypes)
    setVisible(false)
  }
  
  const handleCancel = () => {
    setSelectedTypes(value) // 恢复到原来的选择
    setVisible(false)
  }
  
  const handleCheckboxChange = (chartId, checked) => {
    if (checked) {
      setSelectedTypes([...selectedTypes, chartId])
    } else {
      setSelectedTypes(selectedTypes.filter(id => id !== chartId))
    }
  }
  
  const handleSelectAll = () => {
    setSelectedTypes(CHART_TYPES.map(c => c.id))
  }
  
  const handleClearAll = () => {
    setSelectedTypes([])
  }
  
  return (
    <>
      <Button 
        size="small" 
        icon={<AppstoreOutlined />}
        onClick={() => setVisible(true)}
      >
        选择图表类型 {value.length > 0 && `(${value.length})`}
      </Button>
      
      <Modal
        title={
          <Space>
            <AppstoreOutlined style={{ color: '#1890ff' }} />
            <span>选择图表类型</span>
          </Space>
        }
        open={visible}
        onOk={handleOk}
        onCancel={handleCancel}
        width={900}
        styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
        okText="确定"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Text type="secondary">已选择 {selectedTypes.length} 种图表类型</Text>
            <Button size="small" type="link" onClick={handleSelectAll}>全选</Button>
            <Button size="small" type="link" onClick={handleClearAll}>清空</Button>
          </Space>
          {selectedTypes.length > 0 && (
            <div style={{ marginTop: 8 }}>
              {selectedTypes.map(id => {
                const chart = CHART_TYPES.find(c => c.id === id)
                return chart ? (
                  <Tag key={id} closable onClose={() => handleCheckboxChange(id, false)}>
                    {chart.name}
                  </Tag>
                ) : null
              })}
            </div>
          )}
        </div>
        
        {Object.entries(groupedCharts).map(([category, charts]) => (
          <div key={category} style={{ marginBottom: 24 }}>
            <Title level={5} style={{ marginBottom: 12 }}>
              📊 {category}
            </Title>
            <Row gutter={[16, 16]}>
              {charts.map(chart => (
                <Col span={12} key={chart.id}>
                  <div style={{
                    padding: 12,
                    border: selectedTypes.includes(chart.id) ? '2px solid #1890ff' : '1px solid #d9d9d9',
                    borderRadius: 8,
                    background: selectedTypes.includes(chart.id) ? '#f0f5ff' : 'white',
                    cursor: 'pointer',
                    transition: 'all 0.3s'
                  }}
                  onClick={() => handleCheckboxChange(chart.id, !selectedTypes.includes(chart.id))}
                  >
                    <Space direction="vertical" style={{ width: '100%' }} size={8}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Space>
                          {chart.icon}
                          <Text strong>{chart.name}</Text>
                        </Space>
                        <Checkbox 
                          checked={selectedTypes.includes(chart.id)}
                          onChange={(e) => handleCheckboxChange(chart.id, e.target.checked)}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </div>
                      
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {chart.description}
                      </Text>
                      
                      <div>
                        <Text style={{ fontSize: 11, color: '#8c8c8c' }}>
                          <strong>适用场景：</strong>{chart.适用场景.join('、')}
                        </Text>
                      </div>
                      
                      <div>
                        <Tag color="blue" style={{ fontSize: 11 }}>{chart.数据类型}</Tag>
                      </div>
                      
                      <div style={{ fontSize: 11, color: '#595959', fontStyle: 'italic' }}>
                        💡 示例：{chart.示例}
                      </div>
                    </Space>
                  </div>
                </Col>
              ))}
            </Row>
          </div>
        ))}
        
        <div style={{ 
          marginTop: 16, 
          padding: 12, 
          background: '#e6f7ff', 
          border: '1px solid #91d5ff',
          borderRadius: 4 
        }}>
          <Space direction="vertical" size={4}>
            <Text style={{ fontSize: 12 }}>
              💡 <strong>经典模式专属功能：</strong>
            </Text>
            <Text style={{ fontSize: 12 }}>
              • 选择多个图表类型后，AI 会依次绘制每种图表并进行分析
            </Text>
            <Text style={{ fontSize: 12 }}>
              • 最后汇总所有图表的分析结果
            </Text>
            <Text style={{ fontSize: 12 }}>
              • 如果选择的图表类型不适合当前数据，AI 会提示并建议更合适的类型
            </Text>
            <Text type="secondary" style={{ fontSize: 11, fontStyle: 'italic' }}>
              注意：智能模式会自主决策，自动选择最合适的图表类型
            </Text>
          </Space>
        </div>
      </Modal>
    </>
  )
}

export default ChartTypeSelector

