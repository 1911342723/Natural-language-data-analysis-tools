import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App.jsx'
import './index.css'

// 配置 dayjs 中文
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
dayjs.locale('zh-cn')

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN} theme={{
      token: {
        colorPrimary: '#1677ff',
        borderRadius: 6,
      },
    }}>
      <App />
    </ConfigProvider>
  </React.StrictMode>,
)


