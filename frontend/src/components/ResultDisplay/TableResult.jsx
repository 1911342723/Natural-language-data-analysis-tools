import { useState } from 'react'
import { Table, Button, Space } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'
import './TableResult.css'

function TableResult({ data, columns: columnNames }) {
  const [pageSize, setPageSize] = useState(10)

  // 构建表格列配置
  const columns = columnNames?.map(col => ({
    title: col,
    dataIndex: col,
    key: col,
    ellipsis: true,
    sorter: (a, b) => {
      const valA = a[col]
      const valB = b[col]
      
      // 数值排序
      if (typeof valA === 'number' && typeof valB === 'number') {
        return valA - valB
      }
      
      // 字符串排序
      return String(valA).localeCompare(String(valB))
    },
    render: (text) => {
      if (text === null || text === undefined) {
        return <span style={{ color: '#bfbfbf' }}>-</span>
      }
      if (typeof text === 'number') {
        return text.toFixed(2)
      }
      return String(text)
    },
  })) || []

  // 构建数据源
  const dataSource = data?.map((row, index) => ({
    ...row,
    key: index,
  })) || []

  // 导出为 CSV
  const handleExport = () => {
    if (!data || data.length === 0) return

    // 构建 CSV 内容
    const headers = columnNames.join(',')
    const rows = data.map(row =>
      columnNames.map(col => {
        const value = row[col]
        if (value === null || value === undefined) return ''
        return `"${String(value).replace(/"/g, '""')}"`
      }).join(',')
    )
    
    const csvContent = [headers, ...rows].join('\n')
    
    // 下载
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `分析结果_${new Date().getTime()}.csv`
    link.click()
  }

  return (
    <div className="table-result-container">
      <div className="table-actions">
        <Space>
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExport}
            size="small"
          >
            导出 CSV
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={dataSource}
        scroll={{ x: 'max-content', y: 400 }}
        pagination={{
          pageSize,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
          pageSizeOptions: ['10', '20', '50', '100'],
          onShowSizeChange: (current, size) => setPageSize(size),
        }}
        bordered
        size="small"
        className="result-table"
      />
    </div>
  )
}

export default TableResult


