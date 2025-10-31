import { useState } from 'react'
import { 
  Checkbox, 
  Button, 
  Input, 
  Tag, 
  Space, 
  Divider, 
  Card,
  Table,
  Typography 
} from 'antd'
import { 
  SearchOutlined, 
  CheckSquareOutlined, 
  BorderOutlined,
  InfoCircleOutlined 
} from '@ant-design/icons'
import useAppStore from '@/store/useAppStore'
import './FieldSelector.css'

const { Text } = Typography

function FieldSelector() {
  const {
    selectedColumns,
    toggleColumn,
    clearSelectedColumns,
    getCurrentSheet,
    currentSheetName,
    setSelectedColumns,
  } = useAppStore()

  const [searchText, setSearchText] = useState('')
  
  // 获取当前工作表的数据
  const currentSheet = getCurrentSheet()
  const columns = currentSheet?.columns || []
  const dataPreview = currentSheet?.preview || []
  
  // 调试日志
  console.log('🎯 FieldSelector - 当前工作表:', currentSheetName)
  console.log('🎯 FieldSelector - 可用字段数量:', columns.length)
  console.log('🎯 FieldSelector - 已选字段数量:', selectedColumns.length)

  // 过滤字段
  const filteredColumns = columns.filter(col =>
    col.name.toLowerCase().includes(searchText.toLowerCase())
  )

  // 是否全选
  const isAllSelected = columns.length > 0 && selectedColumns.length === columns.length
  
  // 全选当前工作表的所有字段
  const selectAllColumns = () => {
    const allColumnNames = columns.map(col => col.name)
    setSelectedColumns(allColumnNames)
  }

  // 获取字段类型颜色
  const getTypeColor = (type) => {
    const typeMap = {
      'int': 'blue',
      'float': 'cyan',
      'string': 'green',
      'datetime': 'orange',
      'bool': 'purple',
      'object': 'default',
    }
    return typeMap[type?.toLowerCase()] || 'default'
  }

  // 获取选中字段的数据预览
  const previewColumns = selectedColumns.map(colName => ({
    title: colName,
    dataIndex: colName,
    key: colName,
    ellipsis: true,
    width: 120,
    render: (text) => (
      <span title={text} style={{ fontSize: '12px' }}>
        {text === null || text === undefined || text === '' ? '-' : String(text)}
      </span>
    ),
  }))

  const previewData = dataPreview.slice(0, 5).map((row, index) => ({
    ...row,
    key: index,
  }))

  return (
    <div className="field-selector-container">
      {/* 顶部操作栏 */}
      <div className="selector-header">
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <div className="header-title">
            <InfoCircleOutlined style={{ color: '#1677ff' }} />
            <Text strong>选择分析字段</Text>
          </div>
          
          <Input
            placeholder="搜索字段名称..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            allowClear
            size="small"
          />

          <Space size="small" style={{ width: '100%', justifyContent: 'space-between' }}>
            <Button
              type="link"
              size="small"
              icon={isAllSelected ? <BorderOutlined /> : <CheckSquareOutlined />}
              onClick={isAllSelected ? clearSelectedColumns : selectAllColumns}
            >
              {isAllSelected ? '取消全选' : '全选'}
            </Button>
            <Tag color="blue">{selectedColumns.length} / {columns.length}</Tag>
          </Space>
        </Space>
      </div>

      <Divider style={{ margin: '12px 0' }} />

      {/* 字段列表 */}
      <div className="field-list">
        {filteredColumns.length === 0 ? (
          <div className="empty-state">
            <Text type="secondary">未找到匹配的字段</Text>
          </div>
        ) : (
          filteredColumns.map(col => (
            <div
              key={col.name}
              className={`field-item ${selectedColumns.includes(col.name) ? 'selected' : ''}`}
              onClick={() => toggleColumn(col.name)}
            >
              <Checkbox
                checked={selectedColumns.includes(col.name)}
                onChange={() => toggleColumn(col.name)}
              >
                <Space direction="vertical" size={0}>
                  <Text strong style={{ fontSize: '13px' }}>{col.name}</Text>
                  <Space size={4}>
                    <Tag color={getTypeColor(col.type)} style={{ fontSize: '11px', margin: 0 }}>
                      {col.type}
                    </Tag>
                    {col.nullable && (
                      <Tag style={{ fontSize: '10px', margin: 0 }}>可空</Tag>
                    )}
                  </Space>
                </Space>
              </Checkbox>
            </div>
          ))
        )}
      </div>

      {/* 已选字段预览 */}
      {selectedColumns.length > 0 && (
        <>
          <Divider style={{ margin: '12px 0' }} />
          <div className="field-preview-section">
            <Card
              size="small"
              title={<Text style={{ fontSize: '13px' }}>已选字段数据预览</Text>}
              bordered={false}
              className="preview-card"
            >
              <Table
                columns={previewColumns}
                dataSource={previewData}
                scroll={{ x: 'max-content' }}
                pagination={false}
                size="small"
                bordered
              />
              <div className="preview-hint">
                显示前 5 行数据
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}

export default FieldSelector

