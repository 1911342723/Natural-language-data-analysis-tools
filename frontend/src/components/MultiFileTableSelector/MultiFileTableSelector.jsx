import { useState } from 'react'
import { Space, Input, Button, Checkbox, Tag, Typography, Collapse, Empty } from 'antd'
import {
  DatabaseOutlined,
  SearchOutlined,
  FileExcelOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  CheckSquareOutlined,
  BorderOutlined
} from '@ant-design/icons'
import useAppStore from '@/store/useAppStore'
import './MultiFileTableSelector.css'

const { Text } = Typography
const { Panel } = Collapse

function MultiFileTableSelector() {
  const { 
    fileGroup, 
    selectedTables, 
    toggleTable,
    clearSelectedTables,
    showPreview,
    togglePreview
  } = useAppStore()
  
  const [searchText, setSearchText] = useState('')
  const [activeKeys, setActiveKeys] = useState([]) // 展开的文件

  if (!fileGroup || !fileGroup.files || fileGroup.files.length === 0) {
    return (
      <div className="multi-file-selector-container">
        <Empty 
          description="暂无上传文件"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </div>
    )
  }

  // 过滤文件和工作表
  const filteredFiles = fileGroup.files.filter(file => {
    if (!searchText) return true
    
    // 搜索文件名或工作表名
    const matchFileName = file.file_name.toLowerCase().includes(searchText.toLowerCase())
    const matchSheetName = file.sheets?.some(sheet => 
      sheet.sheet_name.toLowerCase().includes(searchText.toLowerCase())
    )
    
    return matchFileName || matchSheetName
  })

  // 检查某个表格是否被选中
  const isTableSelected = (fileId, sheetName) => {
    return selectedTables.some(
      t => t.file_id === fileId && t.sheet_name === sheetName
    )
  }

  // 切换表格选择
  const handleToggleTable = (file, sheet) => {
    toggleTable({
      file_id: file.file_id,
      file_name: file.file_name,
      sheet_name: sheet.sheet_name,
      columns: sheet.columns || []
    })
  }

  // 检查是否全部选中
  const totalTables = fileGroup.files.reduce((sum, file) => sum + (file.sheets?.length || 0), 0)
  const isAllSelected = selectedTables.length === totalTables && totalTables > 0

  // 全选/取消全选
  const handleToggleAll = () => {
    if (isAllSelected) {
      clearSelectedTables()
    } else {
      // 全选所有表格
      fileGroup.files.forEach(file => {
        file.sheets?.forEach(sheet => {
          if (!isTableSelected(file.file_id, sheet.sheet_name)) {
            handleToggleTable(file, sheet)
          }
        })
      })
    }
  }

  return (
    <div className="multi-file-selector-container">
      {/* 顶部操作栏 */}
      <div className="selector-header">
        <Space direction="vertical" size="medium" style={{ width: '100%' }}>
          <div className="header-title">
            <DatabaseOutlined style={{ fontSize: 16, color: '#262626' }} />
            <Text strong style={{ fontSize: 14, color: '#262626' }}>选择对比表格</Text>
          </div>
          
          <Input
            placeholder="搜索文件名或工作表..."
            prefix={<SearchOutlined style={{ color: '#8c8c8c' }} />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            allowClear
            className="table-search-input"
          />

          <Space size="small" style={{ width: '100%', justifyContent: 'space-between', marginTop: 12 }}>
            <Space size="small">
              <Button
                type="text"
                size="small"
                icon={isAllSelected ? <BorderOutlined /> : <CheckSquareOutlined />}
                onClick={handleToggleAll}
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
              {selectedTables.length} / {totalTables}
            </Tag>
          </Space>
        </Space>
      </div>

      {/* 文件和表格列表 */}
      <div className="tables-list">
        {filteredFiles.length === 0 ? (
          <Empty 
            description="没有匹配的文件"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            style={{ marginTop: 32 }}
          />
        ) : (
          <Collapse
            activeKey={activeKeys}
            onChange={setActiveKeys}
            ghost
            className="files-collapse"
          >
            {filteredFiles.map(file => (
              <Panel
                key={file.file_id}
                header={
                  <div className="file-header">
                    <FileExcelOutlined style={{ fontSize: 16, color: '#1890ff' }} />
                    <Text strong style={{ fontSize: 14 }}>{file.file_name}</Text>
                    <Tag color="blue" style={{ marginLeft: 'auto' }}>
                      {file.sheets?.length || 0} 个工作表
                    </Tag>
                  </div>
                }
                className="file-panel"
              >
                <div className="sheets-list">
                  {file.sheets && file.sheets.length > 0 ? (
                    file.sheets.map(sheet => {
                      const selected = isTableSelected(file.file_id, sheet.sheet_name)
                      const selectedTable = selectedTables.find(
                        t => t.file_id === file.file_id && t.sheet_name === sheet.sheet_name
                      )
                      
                      return (
                        <div
                          key={sheet.sheet_name}
                          className={`sheet-item ${selected ? 'selected' : ''}`}
                          onClick={() => handleToggleTable(file, sheet)}
                        >
                          <Checkbox 
                            checked={selected}
                            onChange={() => handleToggleTable(file, sheet)}
                            onClick={(e) => e.stopPropagation()}
                          />
                          <div className="sheet-info">
                            <Text strong>{sheet.sheet_name}</Text>
                            <Space size={4} style={{ marginTop: 4 }}>
                              <Tag color="green" style={{ fontSize: 11 }}>
                                {sheet.total_rows?.toLocaleString() || 0} 行
                              </Tag>
                              <Tag color="purple" style={{ fontSize: 11 }}>
                                {sheet.columns?.length || 0} 列
                              </Tag>
                              {selected && selectedTable && (
                                <Tag color="blue" style={{ fontSize: 11 }}>
                                  别名: {selectedTable.alias}
                                </Tag>
                              )}
                            </Space>
                          </div>
                        </div>
                      )
                    })
                  ) : (
                    <Empty description="无工作表" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                  )}
                </div>
              </Panel>
            ))}
          </Collapse>
        )}
      </div>
    </div>
  )
}

export default MultiFileTableSelector

