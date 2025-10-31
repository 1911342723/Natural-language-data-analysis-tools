import { useState, useEffect } from 'react'
import { 
  Drawer, 
  List, 
  Card, 
  Button, 
  Space, 
  Tag, 
  Input,
  Popconfirm,
  Empty,
  message 
} from 'antd'
import { 
  DeleteOutlined, 
  SearchOutlined,
  ClockCircleOutlined,
  FileTextOutlined 
} from '@ant-design/icons'
import { getHistoryList, deleteHistory } from '@/services/api'
import dayjs from 'dayjs'
import './HistorySidebar.css'

const { Search } = Input

function HistorySidebar({ visible, onClose }) {
  const [historyList, setHistoryList] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')

  // 加载历史记录
  const loadHistory = async () => {
    setLoading(true)
    try {
      const response = await getHistoryList()
      setHistoryList(response.data || [])
    } catch (error) {
      console.error('加载历史记录失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (visible) {
      loadHistory()
    }
  }, [visible])

  // 删除历史记录
  const handleDelete = async (id) => {
    try {
      await deleteHistory(id)
      message.success('删除成功')
      loadHistory()
    } catch (error) {
      message.error('删除失败')
    }
  }

  // 过滤历史记录
  const filteredHistory = historyList.filter(item =>
    item.file_name?.toLowerCase().includes(searchText.toLowerCase()) ||
    item.user_request?.toLowerCase().includes(searchText.toLowerCase())
  )

  return (
    <Drawer
      title="历史记录"
      placement="right"
      width={400}
      onClose={onClose}
      open={visible}
      className="history-drawer"
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* 搜索框 */}
        <Search
          placeholder="搜索历史记录..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          allowClear
        />

        {/* 历史记录列表 */}
        {filteredHistory.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无历史记录"
          />
        ) : (
          <List
            loading={loading}
            dataSource={filteredHistory}
            renderItem={(item) => (
              <Card
                size="small"
                className="history-card"
                hoverable
              >
                <div className="history-card-header">
                  <Space>
                    <FileTextOutlined style={{ color: '#1677ff' }} />
                    <span className="file-name">{item.file_name}</span>
                  </Space>
                  <Popconfirm
                    title="确定删除此记录？"
                    onConfirm={() => handleDelete(item.id)}
                    okText="删除"
                    cancelText="取消"
                  >
                    <Button
                      type="text"
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                    />
                  </Popconfirm>
                </div>

                <div className="history-card-content">
                  <p className="request-text">
                    {item.user_request?.substring(0, 100)}
                    {item.user_request?.length > 100 && '...'}
                  </p>
                  
                  <Space size={4} wrap>
                    <Tag color="blue" style={{ fontSize: '11px' }}>
                      {item.selected_columns?.length || 0} 个字段
                    </Tag>
                    {item.success && (
                      <Tag color="success" style={{ fontSize: '11px' }}>
                        成功
                      </Tag>
                    )}
                  </Space>
                </div>

                <div className="history-card-footer">
                  <Space size={4}>
                    <ClockCircleOutlined style={{ fontSize: '12px', color: '#8c8c8c' }} />
                    <span className="time-text">
                      {dayjs(item.created_at).format('MM-DD HH:mm')}
                    </span>
                  </Space>
                </div>
              </Card>
            )}
          />
        )}
      </Space>
    </Drawer>
  )
}

export default HistorySidebar


