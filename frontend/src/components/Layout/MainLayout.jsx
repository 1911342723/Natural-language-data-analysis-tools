import { Layout, Button, Tooltip, Modal } from 'antd'
import { 
  MenuFoldOutlined, 
  MenuUnfoldOutlined,
  HistoryOutlined,
  ExclamationCircleOutlined 
} from '@ant-design/icons'
import useAppStore from '@/store/useAppStore'
import FieldSelector from '../FieldSelector/FieldSelector'
import MultiFileTableSelector from '../MultiFileTableSelector/MultiFileTableSelector'
import WorkArea from '../WorkArea/WorkArea'
import HistorySidebar from '../History/HistorySidebar'
import './MainLayout.css'

const { Header, Sider, Content } = Layout

function MainLayout() {
  const {
    sidebarCollapsed,
    toggleSidebar,
    historySidebarVisible,
    setHistorySidebarVisible,
    fileData,
    fileGroup,
    uploadMode,
    resetAll,
  } = useAppStore()

  // 判断是否有数据（单文件或多文件）
  const hasData = uploadMode === 'multiple' ? fileGroup : fileData

  // 点击标题返回首页
  const handleBackToHome = () => {
    // 如果有数据，显示确认对话框
    if (hasData) {
      Modal.confirm({
        title: '返回首页',
        icon: <ExclamationCircleOutlined />,
        content: '返回首页将清空当前所有数据和分析记录，确定要继续吗？',
        okText: '确定',
        cancelText: '取消',
        onOk: () => {
          resetAll()
        },
      })
    } else {
      // 没有数据直接重置
      resetAll()
    }
  }

  return (
    <Layout className="main-layout">
      {/* 顶部导航栏 */}
      <Header className="main-header">
        <div className="header-left" onClick={handleBackToHome} style={{ cursor: 'pointer' }}>
          <h1 className="app-title">自然语言数据分析工具</h1>
        </div>
        
        <div className="header-right">
          <Tooltip title="历史记录">
            <Button
              type="text"
              icon={<HistoryOutlined />}
              onClick={() => setHistorySidebarVisible(true)}
            />
          </Tooltip>
        </div>
      </Header>

      <Layout className="main-content-layout">
        {/* 左侧侧边栏（单文件显示字段选择，多文件显示表格选择）*/}
        {hasData && (
          <Sider
            width={300}
            collapsedWidth={0}
            collapsed={sidebarCollapsed}
            theme="light"
            className="field-sidebar"
          >
            {uploadMode === 'single' ? (
              <FieldSelector />
            ) : (
              <MultiFileTableSelector />
            )}
          </Sider>
        )}

        {/* 主工作区 */}
        <Layout className="work-area-layout">
          <Content className="work-area-content">
            {/* 侧边栏折叠按钮 */}
            {hasData && (
              <Button
                type="text"
                icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                onClick={toggleSidebar}
                className="sidebar-toggle-btn"
              />
            )}
            
            <WorkArea />
          </Content>
        </Layout>
      </Layout>

      {/* 历史记录侧边栏（抽屉） */}
      <HistorySidebar
        visible={historySidebarVisible}
        onClose={() => setHistorySidebarVisible(false)}
      />
    </Layout>
  )
}

export default MainLayout


