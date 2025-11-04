import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0', // 允许外部访问（监听所有网络接口）
    strictPort: false,
    allowedHosts: [
      '0a431d28c27a.ngrok-free.app',  // ngrok 域名
      '.ngrok-free.app',               // 所有 ngrok-free.app 子域名
      '.ngrok.io',                     // 旧版 ngrok 域名
    ],
    hmr: {
      clientPort: 3000, // HMR 客户端端口
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

