/**
 * 科学家团队工作流API
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * 启动科学家团队研究
 */
export const startResearch = async (sessionId, userInput, dataInfo) => {
  const response = await axios.post(`${API_BASE_URL}/api/workflow/start_research`, {
    session_id: sessionId,
    user_input: userInput,
    data_info: dataInfo
  })
  return response.data
}

/**
 * 提交用户决策
 */
export const submitUserDecision = async (decisionId, choice, feedback = null) => {
  const response = await axios.post(`${API_BASE_URL}/api/workflow/user_decision`, {
    decision_id: decisionId,
    choice,
    feedback
  })
  return response.data
}

/**
 * 获取所有Agent信息
 */
export const getAgents = async () => {
  const response = await axios.get(`${API_BASE_URL}/api/workflow/agents`)
  return response.data
}

/**
 * 获取消息历史
 */
export const getMessages = async (agentId = null, limit = 100) => {
  const params = { limit }
  if (agentId) {
    params.agent_id = agentId
  }
  const response = await axios.get(`${API_BASE_URL}/api/workflow/messages`, { params })
  return response.data
}

/**
 * 获取系统统计信息
 */
export const getStatistics = async () => {
  const response = await axios.get(`${API_BASE_URL}/api/workflow/statistics`)
  return response.data
}

/**
 * 创建WebSocket连接
 */
export const createWorkflowWebSocket = (onMessage, onClose, onError) => {
  const wsUrl = API_BASE_URL.replace('http', 'ws') + '/api/workflow/ws'
  const ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    console.log('✅ WebSocket连接已建立')
  }
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      onMessage && onMessage(data)
    } catch (error) {
      console.error('解析WebSocket消息失败:', error)
    }
  }
  
  ws.onclose = () => {
    console.log('WebSocket连接已关闭')
    onClose && onClose()
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket错误:', error)
    onError && onError(error)
  }
  
  return ws
}

