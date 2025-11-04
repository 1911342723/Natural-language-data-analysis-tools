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
  FileTextOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
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
      console.log('📋 历史记录数据:', response)
      const items = response.data?.items || response.data || []
      setHistoryList(items)
      console.log('✅ 历史记录加载成功，共', items.length, '条')
    } catch (error) {
      console.error('❌ 加载历史记录失败:', error)
      message.error('加载历史记录失败')
      setHistoryList([])
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
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Space direction="vertical" size="middle">
              <ClockCircleOutlined style={{ fontSize: 48, color: '#1677ff' }} spin />
              <p style={{ color: '#8c8c8c' }}>加载中...</p>
            </Space>
          </div>
        ) : filteredHistory.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <Space direction="vertical" size="small">
                <span>{searchText ? '没有找到相关记录' : '暂无历史记录'}</span>
                {!searchText && (
                  <span style={{ fontSize: '12px', color: '#8c8c8c' }}>
                    开始你的第一次数据分析吧
                  </span>
                )}
              </Space>
            }
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
                    {item.user_request?.substring(0, 150)}
                    {item.user_request?.length > 150 && '...'}
                  </p>
                  
                  <Space size={4} wrap>
                    {item.success ? (
                      <Tag color="success" icon={<CheckCircleOutlined />} style={{ fontSize: '11px' }}>
                        成功
                      </Tag>
                    ) : (
                      <Tag color="error" icon={<CloseCircleOutlined />} style={{ fontSize: '11px' }}>
                        失败
                      </Tag>
                    )}
                    {item.execution_time && (
                      <Tag color="default" style={{ fontSize: '11px' }}>
                        {item.execution_time.toFixed(2)}s
                      </Tag>
                    )}
                    {item.session_id && (
                      <Tag color="blue" style={{ fontSize: '11px' }}>
                        Session: {item.session_id.substring(0, 8)}
                      </Tag>
                    )}
                  </Space>
                </div>

                <div className="history-card-footer">
                  <Space size={4}>
                    <ClockCircleOutlined style={{ fontSize: '12px', color: '#8c8c8c' }} />
                    <span className="time-text">
                      {dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss')}
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


