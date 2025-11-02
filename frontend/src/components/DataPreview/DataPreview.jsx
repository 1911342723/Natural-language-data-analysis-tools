import { useState } from 'react'
import { Table, Button, Space, Tag, Card, Statistic, Row, Col, Tabs, Alert, Checkbox, Collapse } from 'antd'
import { 
  CloseOutlined, 
  FileTextOutlined,
  TableOutlined,
  ColumnHeightOutlined,
  FileExcelOutlined,
  InfoCircleOutlined,
  AppstoreAddOutlined,
  CheckCircleOutlined,
  DownOutlined,
  UpOutlined
} from '@ant-design/icons'
import useAppStore from '@/store/useAppStore'
import './DataPreview.css'

const { Panel } = Collapse

function DataPreview({ onClose }) {
  const { 
    uploadMode,
    fileData, 
    fileGroup,
    sheets, 
    currentSheetName, 
    setCurrentSheet, 
    uploadedFile, 
    getCurrentSheet,
    setColumns,
    clearSelectedColumns,
    setSessionId,
    selectedTables,
    toggleTable,
    toggleTableColumn,
    toggleAllTableColumns,
  } = useAppStore()
  const [pageSize, setPageSize] = useState(10)
  const [collapsedTables, setCollapsedTables] = useState({}) // 记录哪些表格收起了字段选择（默认展开）
  
  // 获取当前工作表
  const currentSheet = getCurrentSheet()
  const dataPreview = currentSheet?.preview || []
  const totalRows = currentSheet?.total_rows || 0
  const totalColumns = currentSheet?.total_columns || 0
  const isSampled = currentSheet?.is_sampled || false
  const sampleSize = currentSheet?.sample_size || 0

  // 处理工作表切换
  const handleSheetChange = (sheetName) => {
    setCurrentSheet(sheetName)
    
    // 更新字段列表
    const selectedSheet = sheets.find(s => s.sheet_name === sheetName)
    if (selectedSheet) {
      setColumns(selectedSheet.columns || [])
      // 清空之前选择的字段
      clearSelectedColumns()
      // 清空 session（切换工作表后需要重新创建 session）
      setSessionId(null)
    }
  }
  
  // 构建工作表选项卡
  const sheetTabs = sheets.map(sheet => ({
    key: sheet.sheet_name,
    label: (
      <Space>
        <FileExcelOutlined />
        <span>{sheet.sheet_name}</span>
        <Tag color="blue">{sheet.total_rows} 行</Tag>
      </Space>
    ),
  }))
  
  // 构建表格列
  const columns = currentSheet?.columns?.map(col => ({
    title: (
      <Space direction="vertical" size={0}>
        <span>{col.name}</span>
        <Tag color={getTypeColor(col.type)} style={{ fontSize: '11px' }}>
          {col.type}
        </Tag>
      </Space>
    ),
    dataIndex: col.name,
    key: col.name,
    width: 150,
    ellipsis: true,
    render: (text) => (
      <span title={text}>
        {text === null || text === undefined || text === '' ? (
          <span style={{ color: '#bfbfbf' }}>-</span>
        ) : (
          String(text)
        )}
      </span>
    ),
  })) || []

  // 构建表格数据
  const dataSource = dataPreview?.map((row, index) => ({
    ...row,
    key: index,
  })) || []

  function getTypeColor(type) {
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

  // 渲染多文件预览
  const renderMultiFilePreview = () => {
    if (!fileGroup || !fileGroup.files || fileGroup.files.length === 0) {
      return <Alert message="暂无文件" type="info" />
    }

    // 调试信息
    console.log('🔍 [DataPreview] fileGroup:', fileGroup)
    console.log('🔍 [DataPreview] 文件数量:', fileGroup.files.length)
    fileGroup.files.forEach((file, idx) => {
      console.log(`🔍 [DataPreview] 文件 ${idx + 1}:`, file.file_name)
      console.log(`  - sheets 数量:`, file.sheets?.length)
      file.sheets?.forEach((sheet, sIdx) => {
        console.log(`  - sheet ${sIdx + 1}:`, sheet.sheet_name)
        console.log(`    - columns:`, sheet.columns)
        console.log(`    - columns 是数组:`, Array.isArray(sheet.columns))
        console.log(`    - columns 长度:`, sheet.columns?.length)
      })
    })

    return (
      <div className="data-preview-container">
        <Card 
          className="preview-card"
          variant="borderless"
          title={
            <Space>
              <AppstoreAddOutlined />
              <span>多文件预览</span>
              <Tag color="blue">{fileGroup.files.length} 个文件</Tag>
              <Tag color="green">{selectedTables.length} 个表格已选</Tag>
            </Space>
          }
          extra={
            <Button 
              type="text" 
              icon={<CloseOutlined />} 
              onClick={onClose}
              size="small"
            />
          }
        >
          {/* 已选择的表格 */}
          {selectedTables.length > 0 && (
            <Alert
              message={
                <Space wrap>
                  <span>已选择的表格：</span>
                  {selectedTables.map(t => (
                    <Tag 
                      key={`${t.file_id}-${t.sheet_name}`} 
                      color="success"
                      closable
                      onClose={() => toggleTable(t)}
                    >
                      {t.alias}: {t.file_name} / {t.sheet_name}
                    </Tag>
                  ))}
                </Space>
              }
              type="success"
              style={{ marginBottom: 16 }}
            />
          )}

          {/* 文件列表 */}
          <Collapse defaultActiveKey={fileGroup.files.map((_, idx) => `file-${idx}`)}>
            {fileGroup.files.map((file, fileIdx) => (
              <Panel
                key={`file-${fileIdx}`}
                header={
                  <Space>
                    <FileExcelOutlined />
                    <strong>{file.file_name}</strong>
                    <Tag color="blue">{file.sheets.length} 个工作表</Tag>
                  </Space>
                }
              >
                {/* 工作表列表 */}
                {file.sheets.map((sheet, sheetIdx) => {
                  const isSelected = selectedTables.some(
                    t => t.file_id === file.file_id && t.sheet_name === sheet.sheet_name
                  )
                  const selectedTable = selectedTables.find(
                    t => t.file_id === file.file_id && t.sheet_name === sheet.sheet_name
                  )
                  const tableAlias = selectedTable?.alias
                  const selectedColumns = selectedTable?.selected_columns || []
                  const tableKey = `${file.file_id}-${sheet.sheet_name}`
                  const isFieldsExpanded = isSelected && !collapsedTables[tableKey] // 选中时默认展开，除非手动收起

                  return (
                    <Card
                      key={`${fileIdx}-${sheetIdx}`}
                      size="small"
                      style={{ marginBottom: 8 }}
                      className={isSelected ? 'selected-table' : ''}
                    >
                      {/* 表格基本信息 */}
                      <Row gutter={[16, 16]} align="middle" style={{ marginBottom: isSelected ? 12 : 0 }}>
                        <Col flex="none">
                          <Checkbox
                            checked={isSelected}
                            onChange={() => toggleTable({
                              file_id: file.file_id,
                              sheet_name: sheet.sheet_name,
                              file_name: file.file_name
                            })}
                          />
                        </Col>
                        <Col flex="auto">
                          <Space>
                            <TableOutlined />
                            <strong>{sheet.sheet_name}</strong>
                            {isSelected && <Tag color="success">{tableAlias}</Tag>}
                            {isSelected && selectedColumns.length > 0 && (
                              <Tag color="blue">{selectedColumns.length} 个字段</Tag>
                            )}
                          </Space>
                        </Col>
                        <Col>
                          <Space>
                            <Statistic 
                              title="行数" 
                              value={sheet.total_rows} 
                              valueStyle={{ fontSize: 14 }}
                            />
                            <Statistic 
                              title="列数" 
                              value={sheet.total_columns} 
                              valueStyle={{ fontSize: 14 }}
                            />
                          </Space>
                        </Col>
                      </Row>

                      {/* 字段选择（仅选中的表格显示）*/}
                      {isSelected && (
                        <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: 12 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                            <span 
                              className="field-selector-title"
                              style={{ 
                                fontWeight: 500, 
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px'
                              }}
                              onClick={() => setCollapsedTables(prev => ({
                                ...prev,
                                [tableKey]: !prev[tableKey]
                              }))}
                            >
                              {isFieldsExpanded ? <DownOutlined /> : <UpOutlined />}
                              <ColumnHeightOutlined /> 选择要分析的字段
                            </span>
                            <Space size="small">
                              <Button
                                type="link"
                                size="small"
                                onClick={() => toggleAllTableColumns(
                                  file.file_id, 
                                  sheet.sheet_name, 
                                  sheet.columns.map(c => c.name),
                                  selectedColumns.length !== sheet.columns.length
                                )}
                              >
                                {selectedColumns.length === sheet.columns.length ? '取消全选' : '全选'}
                              </Button>
                            </Space>
                          </div>

                          {isFieldsExpanded && (
                            <div style={{ 
                              maxHeight: 200, 
                              overflowY: 'auto',
                              padding: '8px 0',
                              display: 'grid',
                              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                              gap: '8px'
                            }}>
                              {sheet.columns && Array.isArray(sheet.columns) && sheet.columns.length > 0 ? (
                                sheet.columns.map(col => (
                                  <Checkbox
                                    key={col.name}
                                    checked={selectedColumns.includes(col.name)}
                                    onChange={() => toggleTableColumn(file.file_id, sheet.sheet_name, col.name)}
                                  >
                                    <Space size={4}>
                                      <span>{col.name}</span>
                                      <Tag color={getTypeColor(col.type)} style={{ margin: 0, fontSize: 11 }}>
                                        {col.type}
                                      </Tag>
                                    </Space>
                                  </Checkbox>
                                ))
                              ) : (
                                <div style={{ gridColumn: '1 / -1', color: '#999', textAlign: 'center' }}>
                                  暂无字段信息
                                </div>
                              )}
                            </div>
                          )}
                          
                          {!isFieldsExpanded && selectedColumns.length > 0 && (
                            <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>
                              已选: {selectedColumns.join(', ')}
                            </div>
                          )}
                        </div>
                      )}
                    </Card>
                  )
                })}
              </Panel>
            ))}
          </Collapse>

          {/* 提示 */}
          <Alert
            message="提示"
            description="选择要对比分析的表格，系统会自动分配变量名（df1, df2, df3...），用于多表格一致性分析。"
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        </Card>
      </div>
    )
  }

  // 根据模式渲染不同内容
  if (uploadMode === 'multiple') {
    return renderMultiFilePreview()
  }

  return (
    <div className="data-preview-container">
      <Card 
        className="preview-card"
        variant="borderless"
        title={
          <Space>
            <FileTextOutlined />
            <span>数据预览</span>
            <Tag color="blue">{uploadedFile?.name}</Tag>
            {sheets.length > 1 && (
              <Tag color="orange">{sheets.length} 个工作表</Tag>
            )}
          </Space>
        }
        extra={
          <Button 
            type="text" 
            icon={<CloseOutlined />} 
            onClick={onClose}
            size="small"
          >
            收起
          </Button>
        }
      >
        {/* 工作表选择器 (多工作表时显示) */}
        {sheets.length > 1 && (
          <Tabs
            activeKey={currentSheetName}
            items={sheetTabs}
            onChange={handleSheetChange}
            className="sheet-tabs"
            type="card"
            size="small"
          />
        )}
        
        {/* 采样提示 */}
        {isSampled && (
          <Alert
            message="大文件智能采样模式"
            description={
              <div>
                <InfoCircleOutlined /> 检测到大数据集（{totalRows.toLocaleString()} 行），系统已智能采样 {sampleSize.toLocaleString()} 行进行分析。
                <br />
                ✅ 统计信息（min/max/mean）基于全部数据计算，精确度 100%
                <br />
                📊 数据分析基于 {((sampleSize / totalRows) * 100).toFixed(1)}% 随机样本，结论仍具代表性
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        
        {/* 数据统计信息 */}
        <Row gutter={16} className="stats-row">
          <Col span={8}>
            <Statistic
              title="总行数"
              value={totalRows}
              prefix={<TableOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="总列数"
              value={totalColumns}
              prefix={<ColumnHeightOutlined />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="文件大小"
              value={(uploadedFile?.size / 1024).toFixed(2)}
              suffix="KB"
              valueStyle={{ color: '#cf1322' }}
            />
          </Col>
        </Row>

        {/* 数据表格 */}
        <Table
          columns={columns}
          dataSource={dataSource}
          scroll={{ x: 'max-content', y: 300 }}
          pagination={{
            pageSize,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条数据`,
            pageSizeOptions: ['5', '10', '20', '50'],
            onShowSizeChange: (current, size) => setPageSize(size),
          }}
          size="small"
          bordered
          className="preview-table"
        />

        <div className="preview-hint">
          前 {dataPreview?.length} 行数据
        </div>
      </Card>
    </div>
  )
}

export default DataPreview

