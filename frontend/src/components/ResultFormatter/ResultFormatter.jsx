import { useState } from 'react'
import { Typography, Divider, Space, Tag, Button } from 'antd'
import { 
  CaretRightOutlined, 
  CaretDownOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import './ResultFormatter.css'

const { Text, Title, Paragraph } = Typography

/**
 * 结果格式化组件 - 美化分析输出
 * 自动识别：标题、数据、列表、分割线等
 */
function ResultFormatter({ text }) {
  const [expandedSections, setExpandedSections] = useState({})

  // 切换章节展开/折叠
  const toggleSection = (sectionIndex) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionIndex]: !prev[sectionIndex]
    }))
  }

  // 解析文本，识别不同类型的内容
  const parseContent = (text) => {
    if (!text) return []
    
    const lines = text.split('\n')
    const sections = []
    let currentSection = null
    let currentContent = []

    lines.forEach((line, idx) => {
      // 识别分隔线（= 或 -）
      if (/^[=\-]{10,}$/.test(line.trim())) {
        if (currentSection) {
          currentSection.content = currentContent
          sections.push(currentSection)
          currentSection = null
          currentContent = []
        }
        return
      }

      // 识别标题（第X步、数据XX等）
      if (/^(第\d+步|数据|字段|缺失值|关键|洞察|建议|总结)[:：]/.test(line.trim()) || 
          /^\d+\./.test(line.trim())) {
        if (currentSection) {
          currentSection.content = currentContent
          sections.push(currentSection)
        }
        currentSection = {
          type: 'section',
          title: line.trim(),
          content: []
        }
        currentContent = []
        return
      }

      // 普通内容
      if (line.trim()) {
        currentContent.push(line)
      }
    })

    // 添加最后一个 section
    if (currentSection) {
      currentSection.content = currentContent
      sections.push(currentSection)
    } else if (currentContent.length > 0) {
      sections.push({
        type: 'plain',
        content: currentContent
      })
    }

    return sections
  }

  // 渲染单行内容（识别键值对、列表等）
  const renderLine = (line, idx) => {
    const trimmedLine = line.trim()

    // 空行
    if (!trimmedLine) return <br key={idx} />

    // 键值对（如：平均值: 123）
    if (/^[-•\-]\s*(.+?)[:：]\s*(.+)$/.test(trimmedLine)) {
      const match = trimmedLine.match(/^[-•\-]\s*(.+?)[:：]\s*(.+)$/)
      return (
        <div key={idx} className="result-kv-item">
          <Text strong className="result-key">{match[1]}:</Text>
          <Text className="result-value">{match[2]}</Text>
        </div>
      )
    }

    // 普通键值对
    if (/^(.+?)[:：]\s*(.+)$/.test(trimmedLine) && trimmedLine.length < 100) {
      const match = trimmedLine.match(/^(.+?)[:：]\s*(.+)$/)
      return (
        <div key={idx} className="result-kv-item">
          <Text strong className="result-key">{match[1]}:</Text>
          <Text className="result-value">{match[2]}</Text>
        </div>
      )
    }

    // 数字开头的列表（1. 2. 3.）
    if (/^\d+\./.test(trimmedLine)) {
      const match = trimmedLine.match(/^(\d+)\.\s*(.+)$/)
      return (
        <div key={idx} className="result-list-item numbered">
          <span className="list-number">{match[1]}</span>
          <Text>{match[2]}</Text>
        </div>
      )
    }

    // 带圈数字（①②③）或带点列表（•）
    if (/^[•\-–—]/.test(trimmedLine)) {
      return (
        <div key={idx} className="result-list-item">
          <span className="list-bullet">•</span>
          <Text>{trimmedLine.replace(/^[•\-–—]\s*/, '')}</Text>
        </div>
      )
    }

    // 普通文本
    return (
      <Paragraph key={idx} className="result-text">
        {trimmedLine}
      </Paragraph>
    )
  }

  // 渲染章节
  const renderSection = (section, idx) => {
    const isExpanded = expandedSections[idx] !== false // 默认展开

    // 识别章节类型
    let sectionIcon = <InfoCircleOutlined />
    let sectionColor = '#1677ff'
    
    if (section.title.includes('第') && section.title.includes('步')) {
      sectionIcon = <CaretRightOutlined />
      sectionColor = '#52c41a'
    } else if (section.title.includes('洞察') || section.title.includes('总结')) {
      sectionIcon = <CheckCircleOutlined />
      sectionColor = '#faad14'
    } else if (section.title.includes('数据') || section.title.includes('字段')) {
      sectionIcon = <BarChartOutlined />
      sectionColor = '#1677ff'
    }

    return (
      <div key={idx} className="result-section">
        <div 
          className="section-header"
          onClick={() => toggleSection(idx)}
        >
          <Space>
            <span style={{ color: sectionColor }}>
              {isExpanded ? <CaretDownOutlined /> : <CaretRightOutlined />}
            </span>
            <span style={{ color: sectionColor }}>{sectionIcon}</span>
            <Text strong className="section-title">
              {section.title.replace(/[:：]$/, '')}
            </Text>
          </Space>
        </div>
        
        {isExpanded && (
          <div className="section-content">
            {section.content.map((line, lineIdx) => renderLine(line, lineIdx))}
          </div>
        )}
      </div>
    )
  }

  const sections = parseContent(text)

  // 如果只有一个纯文本段，直接渲染
  if (sections.length === 1 && sections[0].type === 'plain') {
    return (
      <div className="result-formatter plain">
        {sections[0].content.map((line, idx) => renderLine(line, idx))}
      </div>
    )
  }

  // 渲染多个章节
  return (
    <div className="result-formatter">
      {sections.map((section, idx) => {
        if (section.type === 'section') {
          return renderSection(section, idx)
        } else {
          return (
            <div key={idx} className="result-plain-content">
              {section.content.map((line, lineIdx) => renderLine(line, lineIdx))}
            </div>
          )
        }
      })}
    </div>
  )
}

export default ResultFormatter

