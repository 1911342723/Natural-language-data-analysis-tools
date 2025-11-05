import { useState } from 'react'
import { Tabs } from 'antd'
import { MessageOutlined, TeamOutlined } from '@ant-design/icons'
import useAppStore from '@/store/useAppStore'
import FileUpload from '../FileUpload/FileUpload'
import DataPreview from '../DataPreview/DataPreview'
import ChatArea from '../ChatArea/ChatArea'
import ScientistTeamWorkspace from '../ScientistTeam/ScientistTeamWorkspace'
import './WorkArea.css'

function WorkArea() {
  const { fileData, fileGroup, uploadMode, showPreview, setShowPreview } = useAppStore()
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
        // 上传文件后显示对话区域，带Tab切换
        <div className="work-area-with-data">
          {/* 数据预览区（可折叠） */}
          {showPreview && (
            <div className={`preview-section ${isClosing ? 'closing' : ''}`}>
              <DataPreview onClose={handleClosePreview} />
            </div>
          )}
          
          {/* Tab切换：常规分析 vs 科学家团队 */}
          <div className="work-area-tabs">
            <Tabs
              defaultActiveKey="classic"
              type="card"
              size="large"
              items={[
                {
                  key: 'classic',
                  label: (
                    <span>
                      <MessageOutlined />
                      <span style={{ marginLeft: 8 }}>常规分析</span>
                    </span>
                  ),
                  children: (
                    <div className="chat-section">
                      <ChatArea 
                        showPreview={showPreview}
                        onTogglePreview={handleTogglePreview} 
                      />
                    </div>
                  )
                },
                {
                  key: 'scientist-team',
                  label: (
                    <span>
                      <TeamOutlined />
                      <span style={{ marginLeft: 8 }}>科学家团队</span>
                    </span>
                  ),
                  children: (
                    <ScientistTeamWorkspace />
                  )
                }
              ]}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default WorkArea


