import { useState } from 'react'
import useAppStore from '@/store/useAppStore'
import FileUpload from '../FileUpload/FileUpload'
import DataPreview from '../DataPreview/DataPreview'
import ChatArea from '../ChatArea/ChatArea'
import './WorkArea.css'

function WorkArea() {
  const { fileData, fileGroup, uploadMode } = useAppStore()
  const [showPreview, setShowPreview] = useState(true)
  const [isClosing, setIsClosing] = useState(false)

  // 判断是否有数据（单文件或多文件）
  const hasData = uploadMode === 'multiple' ? fileGroup : fileData

  // 处理关闭预览（带动画）
  const handleClosePreview = () => {
    setIsClosing(true)
    setTimeout(() => {
      setShowPreview(false)
      setIsClosing(false)
    }, 300) // 等待动画完成
  }

  // 处理切换预览
  const handleTogglePreview = () => {
    if (showPreview) {
      handleClosePreview()
    } else {
      setShowPreview(true)
    }
  }

  return (
    <div className="work-area-container">
      {!hasData ? (
        // 未上传文件时显示上传界面
        <FileUpload />
      ) : (
        // 上传文件后显示对话区域
        <div className="work-area-with-data">
          {/* 数据预览区（可折叠） */}
          {showPreview && (
            <div className={`preview-section ${isClosing ? 'closing' : ''}`}>
              <DataPreview onClose={handleClosePreview} />
            </div>
          )}
          
          {/* 对话交互区 */}
          <div className="chat-section">
            <ChatArea 
              showPreview={showPreview}
              onTogglePreview={handleTogglePreview} 
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default WorkArea


