import React, { useState } from 'react'
import { Modal, Upload, Button, Table, Input, Space, Card, message, Radio, Checkbox } from 'antd'
import { UploadOutlined, DownloadOutlined, CopyOutlined, FileExcelOutlined } from '@ant-design/icons'
import * as XLSX from 'xlsx'
import './TableToJsonConverter.css'

const { TextArea } = Input

const TableToJsonConverter = ({ visible, onClose }) => {
  const [fileData, setFileData] = useState(null)
  const [tableData, setTableData] = useState([])
  const [columns, setColumns] = useState([])
  const [jsonOutput, setJsonOutput] = useState('')
  const [outputFormat, setOutputFormat] = useState('array') // 'array' | 'object'
  const [prettyPrint, setPrettyPrint] = useState(true)
  const [includeEmptyFields, setIncludeEmptyFields] = useState(false)

  // 处理文件上传
  const handleFileUpload = (file) => {
    const reader = new FileReader()
    
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result)
        const workbook = XLSX.read(data, { type: 'array' })
        
        // 读取第一个工作表
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
        const jsonData = XLSX.utils.sheet_to_json(firstSheet)
        
        if (jsonData.length === 0) {
          message.error('表格为空，请上传包含数据的文件')
          return
        }
        
        // 设置表格数据
        const dataWithKeys = jsonData.map((row, index) => ({
          ...row,
          _key: index
        }))
        setTableData(dataWithKeys)
        
        // 生成列配置
        const cols = Object.keys(jsonData[0]).map(key => ({
          title: key,
          dataIndex: key,
          key: key,
          ellipsis: true,
          width: 150
        }))
        setColumns(cols)
        
        setFileData(file.name)
        message.success('文件解析成功！')
      } catch (error) {
        console.error('文件解析错误:', error)
        message.error('文件解析失败，请确保是有效的Excel或CSV文件')
      }
    }
    
    reader.readAsArrayBuffer(file)
    return false // 阻止默认上传行为
  }

  // 生成JSON
  const generateJson = () => {
    if (tableData.length === 0) {
      message.warning('请先上传表格文件')
      return
    }

    try {
      // 移除内部的 _key 字段
      const cleanData = tableData.map(({ _key, ...rest }) => rest)
      
      // 处理空字段
      const processedData = includeEmptyFields ? cleanData : cleanData.map(row => {
        const newRow = {}
        Object.entries(row).forEach(([key, value]) => {
          if (value !== null && value !== undefined && value !== '') {
            newRow[key] = value
          }
        })
        return newRow
      })
      
      let output
      if (outputFormat === 'array') {
        output = processedData
      } else {
        // 对象格式：以第一列为key
        output = {}
        const keyField = columns[0]?.dataIndex
        processedData.forEach(row => {
          const key = row[keyField]
          output[key] = row
        })
      }
      
      const jsonString = prettyPrint 
        ? JSON.stringify(output, null, 2)
        : JSON.stringify(output)
      
      setJsonOutput(jsonString)
      message.success('JSON生成成功！')
    } catch (error) {
      console.error('JSON生成错误:', error)
      message.error('JSON生成失败')
    }
  }

  // 复制JSON
  const copyJson = () => {
    if (!jsonOutput) {
      message.warning('请先生成JSON')
      return
    }
    
    navigator.clipboard.writeText(jsonOutput).then(() => {
      message.success('已复制到剪贴板')
    }).catch(() => {
      message.error('复制失败')
    })
  }

  // 下载JSON
  const downloadJson = () => {
    if (!jsonOutput) {
      message.warning('请先生成JSON')
      return
    }
    
    const blob = new Blob([jsonOutput], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileData ? `${fileData.replace(/\.[^/.]+$/, '')}.json` : 'table_data.json'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    message.success('JSON文件已下载')
  }

  // 重置
  const handleReset = () => {
    setFileData(null)
    setTableData([])
    setColumns([])
    setJsonOutput('')
  }

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileExcelOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
          <span>表格转 JSON</span>
        </div>
      }
      open={visible}
      onCancel={onClose}
      width={1400}
      footer={null}
      className="table-to-json-modal"
      destroyOnClose
    >
      <div className="table-to-json-container">
        {/* 左侧：上传和配置 */}
        <div className="converter-left-panel">
          {/* 上传区域 */}
          <Card title="上传表格" size="small" className="upload-section">
            <Upload
              accept=".xlsx,.xls,.csv"
              beforeUpload={handleFileUpload}
              showUploadList={false}
              maxCount={1}
            >
              <Button icon={<UploadOutlined />} block>
                选择文件（Excel/CSV）
              </Button>
            </Upload>
            {fileData && (
              <div style={{ marginTop: '12px', color: '#52c41a', fontSize: '13px' }}>
                ✓ 已加载：{fileData}
              </div>
            )}
          </Card>

          {/* 配置选项 */}
          <Card title="输出配置" size="small" className="config-section">
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <div style={{ marginBottom: '8px', fontWeight: 500 }}>输出格式：</div>
                <Radio.Group 
                  value={outputFormat} 
                  onChange={(e) => setOutputFormat(e.target.value)}
                  style={{ width: '100%' }}
                >
                  <Space direction="vertical">
                    <Radio value="array">数组格式 {'[{...}, {...}]'}</Radio>
                    <Radio value="object">对象格式 {'{key: {...}}'}</Radio>
                  </Space>
                </Radio.Group>
              </div>
              
              <div>
                <Checkbox 
                  checked={prettyPrint} 
                  onChange={(e) => setPrettyPrint(e.target.checked)}
                >
                  格式化输出（美化）
                </Checkbox>
              </div>
              
              <div>
                <Checkbox 
                  checked={includeEmptyFields} 
                  onChange={(e) => setIncludeEmptyFields(e.target.checked)}
                >
                  包含空字段
                </Checkbox>
              </div>
            </Space>
          </Card>

          {/* 操作按钮 */}
          <Card size="small" className="action-section">
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <Button 
                type="primary" 
                block 
                onClick={generateJson}
                disabled={tableData.length === 0}
              >
                生成 JSON
              </Button>
              <Button 
                icon={<CopyOutlined />} 
                block 
                onClick={copyJson}
                disabled={!jsonOutput}
              >
                复制 JSON
              </Button>
              <Button 
                icon={<DownloadOutlined />} 
                block 
                onClick={downloadJson}
                disabled={!jsonOutput}
              >
                下载 JSON
              </Button>
              <Button block onClick={handleReset}>
                重置
              </Button>
            </Space>
          </Card>
        </div>

        {/* 右侧：预览 */}
        <div className="converter-right-panel">
          {/* 表格预览 */}
          <Card 
            title={`表格预览 ${tableData.length > 0 ? `(${tableData.length} 行)` : ''}`}
            size="small" 
            className="preview-section"
          >
            {tableData.length > 0 ? (
              <Table
                dataSource={tableData}
                columns={columns}
                rowKey="_key"
                pagination={{ pageSize: 10, showSizeChanger: true }}
                scroll={{ x: 'max-content', y: 300 }}
                size="small"
              />
            ) : (
              <div className="empty-preview">
                请上传表格文件
              </div>
            )}
          </Card>

          {/* JSON输出 */}
          <Card 
            title="JSON 输出" 
            size="small" 
            className="output-section"
          >
            {jsonOutput ? (
              <TextArea
                value={jsonOutput}
                readOnly
                className="json-output"
                autoSize={{ minRows: 10, maxRows: 20 }}
              />
            ) : (
              <div className="empty-preview">
                点击"生成 JSON"按钮查看结果
              </div>
            )}
          </Card>
        </div>
      </div>
    </Modal>
  )
}

export default TableToJsonConverter

