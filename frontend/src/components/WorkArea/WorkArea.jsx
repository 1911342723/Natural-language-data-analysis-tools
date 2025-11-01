import { useState } from 'react'
import useAppStore from '@/store/useAppStore'
import FileUpload from '../FileUpload/FileUpload'
import DataPreview from '../DataPreview/DataPreview'
import ChatArea from '../ChatArea/ChatArea'
import './WorkArea.css'

function WorkArea() {
  const { fileData, fileGroup, uploadMode } = useAppStore()
  const [showPreview, setShowPreview] = useState(true)

  // 判断是否有数据（单文件或多文件）
  const hasData = uploadMode === 'multiple' ? fileGroup : fileData

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
            <div className="preview-section">
              <DataPreview onClose={() => setShowPreview(false)} />
            </div>
          )}
          
          {/* 对话交互区 */}
          <div className="chat-section">
            <ChatArea 
              showPreview={showPreview}
              onTogglePreview={() => setShowPreview(!showPreview)} 
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default WorkArea


