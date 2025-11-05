import { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import MainLayout from './components/Layout/MainLayout'
import ScientistTeamPage from './pages/ScientistTeamPage'
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

  return (
    <Routes>
      <Route path="/" element={<MainLayout />} />
      <Route path="/scientist-team" element={<ScientistTeamPage />} />
    </Routes>
  )
}

export default App


