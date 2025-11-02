import { useState } from 'react'
import { Upload, Button, message, Progress, Card, Space, Radio, Tag, List, Typography } from 'antd'
import { 
  InboxOutlined, 
  FileExcelOutlined,
  CheckCircleOutlined,
  AppstoreAddOutlined,
  DeleteOutlined,
  CheckOutlined,
  CloudUploadOutlined,
  FileTextOutlined
} from '@ant-design/icons'
import { uploadFile, uploadMultipleFiles } from '@/services/api'
import useAppStore from '@/store/useAppStore'
import './FileUpload.css'

const { Dragger } = Upload
const { Text, Title } = Typography

function FileUpload() {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [currentBatchFiles, setCurrentBatchFiles] = useState([])
  const [currentGroupId, setCurrentGroupId] = useState(null) // 保存后端返回的真实 group_id
  const { 
    uploadMode, 
    setUploadMode, 
    setUploadedFile, 
    setFileData, 
    setColumns,
    setFileGroup 
  } = useAppStore()

  const handleUpload = async (file) => {
    const validTypes = [
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/csv',
    ]
    
    if (!validTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls|csv)$/i)) {
      message.error('仅支持 Excel (.xlsx, .xls) 或 CSV (.csv) 文件')
      return false
    }

    const maxSize = 100 * 1024 * 1024
    if (file.size > maxSize) {
      message.error('文件大小不能超过 100MB')
      return false
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      const response = await uploadFile(file, (progress) => {
        setUploadProgress(progress)
      })

      
      setUploadedFile(file)
      setFileData(response.data)
      
      const firstSheet = response.data.sheets?.[0]
      if (firstSheet) {
        setColumns(firstSheet.columns || [])
      }
      
      message.success('文件上传成功')
    } catch (error) {
      console.error('上传失败:', error)
      message.error('文件上传失败，请重试')
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }

    return false
  }

  const handleFileChange = ({ fileList }) => {
    setCurrentBatchFiles(fileList)
  }

  const validateFile = (file) => {
    const validTypes = [
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/csv',
    ]
    
    if (!validTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls|csv)$/i)) {
      return '格式不支持'
    }

    const maxSize = 100 * 1024 * 1024
    if (file.size > maxSize) {
      return '文件过大'
    }

    return null
  }

  const handleBatchUpload = async () => {
    if (currentBatchFiles.length === 0) {
      message.warning('请选择要上传的文件')
      return
    }

    if (uploadedFiles.length + currentBatchFiles.length > 10) {
      message.error(`最多只能上传10个文件，当前已上传 ${uploadedFiles.length} 个`)
      return
    }

    for (const fileObj of currentBatchFiles) {
      const file = fileObj.originFileObj || fileObj
      const error = validateFile(file)
      if (error) {
        message.error(`文件 "${file.name}" ${error}`)
        return
      }
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      const files = currentBatchFiles.map(f => f.originFileObj || f)
      const response = await uploadMultipleFiles(files, (progress) => {
        setUploadProgress(progress)
      })
      
      // 保存后端返回的真实 group_id
      if (response.data.group_id) {
        setCurrentGroupId(response.data.group_id)
      }
      
      const newFiles = response.data.files.map((file, index) => ({
        ...file,
        localFile: files[index]
      }))
      setUploadedFiles([...uploadedFiles, ...newFiles])
      setCurrentBatchFiles([])
      
      message.success(`成功上传 ${files.length} 个文件`)
    } catch (error) {
      console.error('批次上传失败:', error)
      message.error('文件上传失败，请重试')
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const handleRemoveFile = (fileId) => {
    const newFiles = uploadedFiles.filter(f => f.file_id !== fileId)
    setUploadedFiles(newFiles)
    
    // 如果所有文件都被移除，清理 group_id
    if (newFiles.length === 0) {
      setCurrentGroupId(null)
    }
    
    message.info('已移除文件')
  }

  const handleFinishUpload = async () => {
    if (uploadedFiles.length === 0) {
      message.warning('请至少上传一个文件')
      return
    }

    if (!currentGroupId) {
      message.error('文件组 ID 未找到，请重新上传')
      return
    }

    try {
      const fileGroupData = {
        group_id: currentGroupId,  // 使用后端返回的真实 group_id
        files: uploadedFiles
      }
      
      setFileGroup(fileGroupData)
      message.success(`已准备 ${uploadedFiles.length} 个文件，可以开始分析`)
    } catch (error) {
      console.error('完成上传失败:', error)
      message.error('操作失败，请重试')
    }
  }

  const handleModeChange = (mode) => {
    setUploadMode(mode)
    setUploadedFiles([])
    setCurrentBatchFiles([])
    setCurrentGroupId(null)  // 清理 group_id
  }

  return (
    <div className="modern-file-upload-container">
      {/* 顶部标题区 */}
      <div className="upload-header">
        <div className="header-content">
          <Title level={2} className="header-title">
            <CloudUploadOutlined className="header-icon" />
            数据文件上传
          </Title>
          <Text className="header-subtitle">
            支持 Excel 和 CSV 格式，开启智能数据分析之旅
          </Text>
        </div>
      </div>

      {/* 模式切换 */}
      <div className="mode-selector">
        <Radio.Group 
          value={uploadMode} 
          onChange={(e) => handleModeChange(e.target.value)}
          size="large"
          className="mode-radio-group"
        >
          <Radio.Button value="single" className="mode-radio-button">
            <FileTextOutlined className="mode-icon" />
            <span>单文件分析</span>
          </Radio.Button>
          <Radio.Button value="multiple" className="mode-radio-button">
            <AppstoreAddOutlined className="mode-icon" />
            <span>多文件对比</span>
          </Radio.Button>
        </Radio.Group>
      </div>

      {/* 上传区域 */}
      <div className="upload-main-content">
        <div className="upload-section">
          <Card className="upload-card" variant="borderless">
            {uploadMode === 'single' ? (
              // 单文件上传
              <Dragger
                name="file"
                multiple={false}
                beforeUpload={handleUpload}
                showUploadList={false}
                disabled={uploading}
                className="modern-dragger"
              >
                <div className="dragger-content">
                  <CloudUploadOutlined className="upload-icon" />
                  <Title level={4} className="upload-title">
                    点击或拖拽文件到此处
                  </Title>
                  <Text className="upload-hint">
                    支持 .xlsx, .xls, .csv 格式，单个文件最大 100MB
                  </Text>
                </div>
              </Dragger>
            ) : (
              // 多文件上传
              <>
                <Dragger
                  name="files"
                  multiple={true}
                  beforeUpload={() => false}
                  onChange={handleFileChange}
                  disabled={uploading}
                  className="modern-dragger"
                  fileList={currentBatchFiles}
                >
                  <div className="dragger-content">
                    <AppstoreAddOutlined className="upload-icon multi" />
                    <Title level={4} className="upload-title">
                      选择多个文件进行对比分析
                    </Title>
                    <Text className="upload-hint">
                      最多支持 10 个文件，每个文件最大 100MB
                    </Text>
                  </div>
                </Dragger>
                
                {currentBatchFiles.length > 0 && (
                  <div className="batch-actions">
                    <Button
                      type="primary"
                      size="large"
                      onClick={handleBatchUpload}
                      loading={uploading}
                      disabled={uploading}
                      icon={<CloudUploadOutlined />}
                      className="primary-button"
                    >
                      上传 {currentBatchFiles.length} 个文件
                    </Button>
                    <Button
                      size="large"
                      onClick={() => setCurrentBatchFiles([])}
                      disabled={uploading}
                      className="secondary-button"
                    >
                      取消
                    </Button>
                  </div>
                )}

                {uploadedFiles.length > 0 && (
                  <div className="uploaded-files-section">
                    <Card
                      className="uploaded-card"
                      title={
                        <Space>
                          <CheckCircleOutlined className="success-icon" />
                          <Text strong>已上传的文件 ({uploadedFiles.length}/10)</Text>
                        </Space>
                      }
                      extra={
                        <Button
                          type="primary"
                          icon={<CheckOutlined />}
                          onClick={handleFinishUpload}
                          disabled={uploading}
                          className="finish-button"
                        >
                          完成上传
                        </Button>
                      }
                    >
                      <List
                        dataSource={uploadedFiles}
                        renderItem={(file) => (
                          <List.Item
                            className="file-list-item"
                            actions={[
                              <Button
                                key="delete"
                                type="text"
                                danger
                                size="small"
                                icon={<DeleteOutlined />}
                                onClick={() => handleRemoveFile(file.file_id)}
                                disabled={uploading}
                              >
                                移除
                              </Button>
                            ]}
                          >
                            <List.Item.Meta
                              avatar={
                                <div className="file-avatar">
                                  <FileExcelOutlined />
                                </div>
                              }
                              title={<Text strong>{file.file_name}</Text>}
                              description={
                                <Space size={4}>
                                  <Tag color="blue">{file.sheets?.length || 0} 个工作表</Tag>
                                  <Tag color="green" className="file-id-tag">
                                    {file.file_id.slice(0, 8)}
                                  </Tag>
                                </Space>
                              }
                            />
                          </List.Item>
                        )}
                      />
                    </Card>
                  </div>
                )}
              </>
            )}

            {uploading && (
              <div className="upload-progress-section">
                <Progress
                  percent={uploadProgress}
                  status="active"
                  strokeColor="#000000"
                  size={[undefined, 12]}
                  className="modern-progress"
                />
                <Text className="progress-text">
                  {uploadMode === 'single' ? '正在上传并解析文件...' : `正在上传 ${currentBatchFiles.length} 个文件...`}
                </Text>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}

export default FileUpload
