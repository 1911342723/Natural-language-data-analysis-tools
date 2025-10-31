import { useEffect } from 'react'
import MainLayout from './components/Layout/MainLayout'
import useAppStore from './store/useAppStore'
import './styles/animations.css'

function App() {
  const resetAll = useAppStore(state => state.resetAll)

  useEffect(() => {
    // 组件挂载时的初始化逻辑
    console.log('🚀 数据分析工具启动')
    
    // 页面关闭时清理
    return () => {
      console.log('👋 应用卸载')
    }
  }, [])

  return <MainLayout />
}

export default App


