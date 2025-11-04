import { useEffect } from 'react'
import MainLayout from './components/Layout/MainLayout'
import Login from './pages/Login'
import useAppStore from './store/useAppStore'
import './styles/animations.css'

function App() {
  // 检查当前路径
  const pathname = window.location.pathname
  
  // 根据路径渲染不同组件
  if (pathname === '/login') {
    // 登录页面（用于飞书认证）
    return <Login />
  } else if (pathname === '/') {
    // 主应用（需要登录保护）
    return <MainLayout />
  } else {
    // 其他路径重定向到登录
    useEffect(() => {
      window.location.href = '/login'
    }, [])
    return null
  }
}

export default App
