/**
 * 文件上传API服务
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * 上传文件到科学家团队
 * @param {File} file - 要上传的文件
 * @returns {Promise} 上传结果
 */
export const uploadTeamFile = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/team/upload_file`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 60000 // 60秒超时
      }
    )

    return response.data
  } catch (error) {
    console.error('文件上传失败:', error)
    throw error
  }
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化的大小
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}

/**
 * 获取文件图标
 * @param {string} filename - 文件名
 * @returns {string} 图标名称
 */
export const getFileIcon = (filename) => {
  const ext = filename.split('.').pop().toLowerCase()
  
  const iconMap = {
    'csv': 'FileTextOutlined',
    'xlsx': 'FileExcelOutlined',
    'xls': 'FileExcelOutlined',
    'pdf': 'FilePdfOutlined',
    'docx': 'FileWordOutlined',
    'txt': 'FileTextOutlined',
    'md': 'FileMarkdownOutlined'
  }
  
  return iconMap[ext] || 'FileOutlined'
}

