import axios from 'axios'
import { message } from 'antd'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 60000, // 60秒超时（大文件需要较长时间）
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const errorMessage = error.response?.data?.message || error.message || '请求失败'
    message.error(errorMessage)
    return Promise.reject(error)
  }
)

// ========== API 接口定义 ==========

/**
 * 上传文件并解析
 */
export const uploadFile = (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)
  
  return api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      onProgress?.(percentCompleted)
    },
  })
}

/**
 * 上传多个文件并解析
 */
export const uploadMultipleFiles = (files, onProgress) => {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })
  
  return api.post('/upload-multiple', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 120000, // 多文件上传需要更长时间，120秒
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      onProgress?.(percentCompleted)
    },
  })
}

/**
 * 创建 Jupyter Session（单文件模式）
 */
export const createSession = (fileId, sheetName, selectedColumns) => {
  return api.post('/session/create', {
    file_id: fileId,
    sheet_name: sheetName,
    selected_columns: selectedColumns,
  })
}

/**
 * 创建多文件 Jupyter Session
 */
export const createMultiSession = (groupId, tables) => {
  return api.post('/session/create-multi', {
    group_id: groupId,
    tables: tables,
    selected_columns: [],  // 兼容性保留，实际字段选择在每个 table 中
  })
}

/**
 * 在 Session 中执行代码
 */
export const executeCode = (sessionId, code, timeout = 60) => {
  return api.post('/session/execute', {
    session_id: sessionId,
    code: code,
    timeout: timeout,
  })
}

/**
 * 提交分析需求，启动 Agent（普通方式）
 */
export const submitAnalysisRequest = (sessionId, userRequest, selectedColumns) => {
  return api.post('/agent/analyze', {
    session_id: sessionId,
    user_request: userRequest,
    selected_columns: selectedColumns,
  })
}

/**
 * 提交分析需求，使用 SSE 流式接收（推荐）
 * @param {string} sessionId - Session ID
 * @param {string} userRequest - 用户需求
 * @param {Array} selectedColumns - 选中的字段
 * @param {string} agentMode - Agent 模式 ('classic' | 'smart')
 * @param {function} onStep - 步骤回调 (step) => void
 * @param {function} onComplete - 完成回调 (result) => void
 * @param {function} onError - 错误回调 (error) => void
 * @returns {function} 返回一个取消函数
 */
export const submitAnalysisStream = (
  sessionId,
  userRequest,
  selectedColumns,
  agentMode,
  onStep,
  onComplete,
  onError
) => {
  // 在开发环境，通过代理访问，直接使用相对路径
  const url = '/api/agent/analyze-stream'
  
  const controller = new AbortController()
  
  const fetchSSE = async () => {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          user_request: userRequest,
          selected_columns: selectedColumns,
          agent_mode: agentMode || 'smart', // 默认智能模式
        }),
        signal: controller.signal,
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = '' // 缓冲区，处理跨 chunk 的数据
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break
        
        // 将新数据添加到缓冲区
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        
        // 保留最后一行（可能不完整）
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.substring(6).trim()
              if (!jsonStr) continue // 跳过空行
              
              const data = JSON.parse(jsonStr)
              
              switch (data.event) {
                case 'start':
                  console.log('🚀 流式任务开始:', data.task_id)
                  break
                case 'step':
                  console.log('📝 步骤更新:', {
                    index: data.step_index,
                    title: data.data.title,
                    status: data.data.status,
                    outputLength: data.data.output?.length || 0,
                    outputPreview: data.data.output?.substring(0, 50) || '',
                    hasCode: !!data.data.code
                  })
                  if (onStep) onStep(data.data, data.step_index)
                  break
                case 'complete':
                  console.log('✅ 流式任务完成:', data.data)
                  if (onComplete) onComplete(data.data)
                  break
                case 'error':
                  console.error('❌ 流式任务错误:', data.message)
                  if (onError) onError(new Error(data.message))
                  break
              }
            } catch (parseError) {
              console.error('❌ JSON 解析失败:', parseError.message)
              console.error('原始数据:', line.substring(6))
              // 不中断流，继续处理下一行
            }
          }
        }
      }
      
      // 处理缓冲区中剩余的数据
      if (buffer.trim() && buffer.startsWith('data: ')) {
        try {
          const jsonStr = buffer.substring(6).trim()
          if (jsonStr) {
            const data = JSON.parse(jsonStr)
            if (data.event === 'complete' && onComplete) {
              onComplete(data.data)
            } else if (data.event === 'error' && onError) {
              onError(new Error(data.message))
            }
          }
        } catch (parseError) {
          console.error('❌ 最终缓冲区解析失败:', parseError.message)
        }
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('流式请求失败:', error)
        if (onError) onError(error)
      }
    }
  }
  
  fetchSSE()
  
  // 返回取消函数
  return () => controller.abort()
}

/**
 * 获取 Agent 执行状态（用于轮询）
 */
export const getAgentStatus = (taskId) => {
  return api.get(`/agent/status/${taskId}`)
}

/**
 * 停止 Agent 执行
 */
export const stopAgent = (taskId) => {
  return api.post(`/agent/stop/${taskId}`)
}

/**
 * 获取历史记录列表
 */
export const getHistoryList = (page = 1, pageSize = 20) => {
  return api.get('/history/list', {
    params: { page, page_size: pageSize },
  })
}

/**
 * 获取单条历史记录详情
 */
export const getHistoryDetail = (historyId) => {
  return api.get(`/history/${historyId}`)
}

/**
 * 删除历史记录
 */
export const deleteHistory = (historyId) => {
  return api.delete(`/history/${historyId}`)
}

/**
 * 导出结果
 */
export const exportResult = (sessionId, format) => {
  return api.post('/export', {
    session_id: sessionId,
    format: format, // 'md' | 'pdf' | 'docx'
  }, {
    responseType: 'blob',
  })
}

export default api

