import { useState, useEffect } from 'react'
import { 
  Checkbox, 
  Button, 
  Input, 
  Tag, 
  Space, 
  Divider,
  Typography,
  Select 
} from 'antd'
import { 
  SearchOutlined, 
  CheckSquareOutlined, 
  BorderOutlined,
  DatabaseOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  FileExcelOutlined
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
    showPreview,
    togglePreview,
    sheets,
    setCurrentSheet,
    setSessionId,
  } = useAppStore()

  const [searchText, setSearchText] = useState('')
  
  // 获取当前工作表的数据
  const currentSheet = getCurrentSheet()
  const columns = currentSheet?.columns || []
  
  // 监听工作表切换，清空搜索框
  useEffect(() => {
    setSearchText('')
  }, [currentSheetName])
  
  // 处理工作表切换
  const handleSheetChange = (sheetName) => {
    setCurrentSheet(sheetName)
    clearSelectedColumns()  // 清空字段选择
    setSessionId(null)  // 清空 session，下次分析时会重新创建
  }
  
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

  return (
    <div className="field-selector-container">
      {/* 顶部操作栏 */}
      <div className="selector-header">
        <Space direction="vertical" size="medium" style={{ width: '100%' }}>
          <div className="header-title">
            <DatabaseOutlined style={{ fontSize: 16, color: '#262626' }} />
            <Text strong style={{ fontSize: 14, color: '#262626' }}>选择分析字段</Text>
          </div>
          
          {/* 工作表选择器（多工作表时显示） */}
          {sheets.length > 1 && (
            <Select
              value={currentSheetName}
              onChange={handleSheetChange}
              style={{ width: '100%' }}
              placeholder="选择工作表"
              suffixIcon={<FileExcelOutlined />}
            >
              {sheets.map(sheet => (
                <Select.Option key={sheet.sheet_name} value={sheet.sheet_name}>
                  <Space>
                    <FileExcelOutlined style={{ color: '#1890ff' }} />
                    <span>{sheet.sheet_name}</span>
                    <Tag color="blue" style={{ fontSize: 11 }}>
                      {sheet.total_rows?.toLocaleString() || 0} 行
                    </Tag>
                  </Space>
                </Select.Option>
              ))}
            </Select>
          )}
          
          <Input
            placeholder="搜索字段名称..."
            prefix={<SearchOutlined style={{ color: '#8c8c8c' }} />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            allowClear
            className="field-search-input"
          />

          <Space size="small" style={{ width: '100%', justifyContent: 'space-between', marginTop: 12 }}>
            <Space size="small">
              <Button
                type="text"
                size="small"
                icon={isAllSelected ? <BorderOutlined /> : <CheckSquareOutlined />}
                onClick={isAllSelected ? clearSelectedColumns : selectAllColumns}
                style={{ color: '#595959', fontSize: 13 }}
              >
                {isAllSelected ? '取消全选' : '全选'}
              </Button>
              <Button
                type="text"
                size="small"
                icon={showPreview ? <EyeInvisibleOutlined /> : <EyeOutlined />}
                onClick={togglePreview}
                style={{ color: '#595959', fontSize: 13 }}
              >
                {showPreview ? '隐藏数据' : '查看数据'}
              </Button>
            </Space>
            <Tag style={{ 
              background: '#fafafa', 
              border: '1px solid #d9d9d9', 
              color: '#262626',
              fontWeight: 500
            }}>
              {selectedColumns.length} / {columns.length}
            </Tag>
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
            >
              <Checkbox
                checked={selectedColumns.includes(col.name)}
                onChange={(e) => {
                  e.stopPropagation()  // 阻止事件冒泡
                  toggleColumn(col.name)
                }}
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
    </div>
  )
}

export default FieldSelector

