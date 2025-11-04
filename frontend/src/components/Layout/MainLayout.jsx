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
import FeishuUserNav from '../Feishu/FeishuUserNav'  // ⭐ 新增
import FeishuLoading from '../Feishu/FeishuLoading'  // ⭐ 新增
import FeishuLoginButton from '../Feishu/FeishuLoginButton'  // ⭐ 新增
import { useFeishuAuth } from '@/hooks/useFeishuAuth'  // ⭐ 新增
import { useEffect } from 'react'  // ⭐ 新增
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

  // ⭐ 新增：飞书认证
  const { user, loading, login, logout, isFeishuEnv } = useFeishuAuth()

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

  // ⭐ 新增：检查登录状态，未登录跳转到 /login
  useEffect(() => {
    if (!loading && !user) {
      console.log('⚠️ 未登录，跳转到登录页');
      window.location.href = '/login';
    }
  }, [loading, user]);

  // 加载中
  if (loading) {
    return <FeishuLoading />;
  }

  // 未登录（等待跳转）
  if (!user) {
    return <FeishuLoading />;
  }

  // 已登录，显示主应用
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
          
          {/* ⭐ 新增：飞书登录/用户导航 */}
          {user ? (
            <FeishuUserNav user={user} onLogout={logout} />
          ) : isFeishuEnv ? (
            <FeishuLoginButton onClick={login} />
          ) : (
            <Tooltip title="请在飞书客户端中打开">
              <FeishuLoginButton onClick={() => alert('请在飞书客户端中打开此应用')} />
            </Tooltip>
          )}
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


