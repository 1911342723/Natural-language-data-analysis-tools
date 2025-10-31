import { Layout, Button, Tooltip } from 'antd'
import { 
  MenuFoldOutlined, 
  MenuUnfoldOutlined,
  HistoryOutlined,
  FileTextOutlined 
} from '@ant-design/icons'
import useAppStore from '@/store/useAppStore'
import FieldSelector from '../FieldSelector/FieldSelector'
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
  } = useAppStore()

  // 判断是否有数据（单文件或多文件）
  const hasData = uploadMode === 'multiple' ? fileGroup : fileData

  return (
    <Layout className="main-layout">
      {/* 顶部导航栏 */}
      <Header className="main-header">
        <div className="header-left">
          <FileTextOutlined className="logo-icon" />
          <h1 className="app-title">智能数据分析工具</h1>
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
        {/* 左侧字段选择侧边栏（单文件模式才显示）*/}
        {fileData && uploadMode === 'single' && (
          <Sider
            width={300}
            collapsedWidth={0}
            collapsed={sidebarCollapsed}
            theme="light"
            className="field-sidebar"
          >
            <FieldSelector />
          </Sider>
        )}

        {/* 主工作区 */}
        <Layout className="work-area-layout">
          <Content className="work-area-content">
            {/* 侧边栏折叠按钮（仅单文件模式）*/}
            {fileData && uploadMode === 'single' && (
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


