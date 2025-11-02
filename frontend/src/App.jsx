import { useEffect } from 'react'
import MainLayout from './components/Layout/MainLayout'
import useAppStore from './store/useAppStore'
import './styles/animations.css'

function App() {
  const resetAll = useAppStore(state => state.resetAll)

  useEffect(() => {
    // 组件挂载时的初始化逻辑
    
    // 页面关闭时清理
    return () => {
    }
  }, [])

  return <MainLayout />
}

export default App


