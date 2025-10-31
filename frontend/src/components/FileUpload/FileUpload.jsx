import { useState } from 'react'
import { Upload, Button, message, Progress, Card, Space, Radio, Tag } from 'antd'
import { 
  InboxOutlined, 
  FileExcelOutlined, 
  FilePdfOutlined,
  CheckCircleOutlined,
  AppstoreAddOutlined
} from '@ant-design/icons'
import { uploadFile, uploadMultipleFiles } from '@/services/api'
import useAppStore from '@/store/useAppStore'
import './FileUpload.css'

const { Dragger } = Upload

function FileUpload() {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const { 
    uploadMode, 
    setUploadMode, 
    setUploadedFile, 
    setFileData, 
    setColumns,
    setFileGroup 
  } = useAppStore()

  const handleUpload = async (file) => {
    // 验证文件类型
    const validTypes = [
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/csv',
    ]
    
    if (!validTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls|csv)$/i)) {
      message.error('只支持上传 Excel (.xlsx, .xls) 或 CSV (.csv) 文件')
      return false
    }

    // 验证文件大小（限制 100MB）
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

      console.log('✅ 上传成功，响应数据:', response)
      console.log('📊 工作表数量:', response.data.sheets?.length)
      
      // 更新状态
      setUploadedFile(file)
      setFileData(response.data)
      
      // 设置第一个工作表的字段列表
      const firstSheet = response.data.sheets?.[0]
      if (firstSheet) {
        console.log('📋 当前工作表:', firstSheet.sheet_name)
        console.log('🔢 字段数量:', firstSheet.columns?.length)
        console.log('📝 字段列表:', firstSheet.columns?.map(c => c.name))
        setColumns(firstSheet.columns || [])
      } else {
        console.error('❌ 没有找到工作表数据')
      }
      
      message.success('文件上传成功！')
    } catch (error) {
      console.error('上传失败:', error)
      message.error('文件上传失败，请重试')
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }

    return false // 阻止自动上传
  }

  // 处理多文件上传
  const handleMultipleUpload = async ({ fileList }) => {
    if (fileList.length === 0) {
      message.warning('请选择至少一个文件')
      return
    }

    if (fileList.length > 10) {
      message.error('最多只能同时上传10个文件')
      return
    }

    // 验证所有文件
    for (const fileObj of fileList) {
      const file = fileObj.originFileObj || fileObj
      const validTypes = [
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv',
      ]
      
      if (!validTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls|csv)$/i)) {
        message.error(`文件 "${file.name}" 格式不支持，只支持 Excel 和 CSV 文件`)
        return
      }

      const maxSize = 100 * 1024 * 1024
      if (file.size > maxSize) {
        message.error(`文件 "${file.name}" 大小超过 100MB`)
        return
      }
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      const files = fileList.map(f => f.originFileObj || f)
      const response = await uploadMultipleFiles(files, (progress) => {
        setUploadProgress(progress)
      })

      console.log('✅ 多文件上传成功，响应数据:', response)
      console.log('📊 文件数量:', response.data.files?.length)
      
      // 更新状态
      setFileGroup(response.data)
      
      message.success(`成功上传 ${fileList.length} 个文件！`)
    } catch (error) {
      console.error('多文件上传失败:', error)
      message.error('文件上传失败，请重试')
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  return (
    <div className="file-upload-container">
      {/* 模式切换 */}
      <div style={{ marginBottom: 16, textAlign: 'center' }}>
        <Radio.Group 
          value={uploadMode} 
          onChange={(e) => setUploadMode(e.target.value)}
          buttonStyle="solid"
        >
          <Radio.Button value="single">
            <FileExcelOutlined /> 单文件分析
          </Radio.Button>
          <Radio.Button value="multiple">
            <AppstoreAddOutlined /> 多文件对比
          </Radio.Button>
        </Radio.Group>
      </div>

      <div className="upload-content">
        <Card className="upload-card" bordered={false}>
          {uploadMode === 'single' ? (
            // 单文件上传
            <Dragger
              name="file"
              multiple={false}
              beforeUpload={handleUpload}
              showUploadList={false}
              disabled={uploading}
              className="upload-dragger"
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">
                点击或拖拽文件到此区域上传
              </p>
              <p className="ant-upload-hint">
                支持 Excel (.xlsx, .xls) 和 CSV (.csv) 格式，文件大小不超过 100MB
              </p>
            </Dragger>
          ) : (
            // 多文件上传
            <Dragger
              name="files"
              multiple={true}
              beforeUpload={() => false}
              onChange={handleMultipleUpload}
              disabled={uploading}
              className="upload-dragger"
              maxCount={10}
            >
              <p className="ant-upload-drag-icon">
                <AppstoreAddOutlined style={{ fontSize: 48 }} />
              </p>
              <p className="ant-upload-text" style={{ marginBottom: 8 }}>
                点击或拖拽多个文件到此区域上传
              </p>
              <div className="ant-upload-hint" style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
                <Tag color="blue" style={{ margin: 0 }}>最多10个文件</Tag>
                <Tag color="green" style={{ margin: 0 }}>支持 Excel 和 CSV</Tag>
                <Tag color="orange" style={{ margin: 0 }}>单个文件≤100MB</Tag>
              </div>
            </Dragger>
          )}

          {uploading && (
            <div className="upload-progress-wrapper">
              <Progress
                percent={uploadProgress}
                status="active"
                strokeColor={{
                  from: '#108ee9',
                  to: '#87d068',
                }}
              />
              <p className="progress-text">
                {uploadMode === 'single' ? '正在上传并解析文件...' : '正在上传多个文件...'}
              </p>
            </div>
          )}
        </Card>

        <div className="upload-tips">
          <h3>💡 使用提示</h3>
          <Space direction="vertical" size="small">
            <div className="tip-item">
              <FileExcelOutlined /> 支持的文件格式：Excel (.xlsx, .xls)、CSV (.csv)
            </div>
            {uploadMode === 'multiple' ? (
              <>
                <div className="tip-item">
                  <CheckCircleOutlined /> 上传后勾选要对比分析的表格
                </div>
                <div className="tip-item">
                  <CheckCircleOutlined /> 系统自动分配变量名（df1, df2, df3...）
                </div>
                <div className="tip-item">
                  <CheckCircleOutlined /> AI 生成代码进行跨表格一致性分析
                </div>
              </>
            ) : (
              <>
                <div className="tip-item">
                  <CheckCircleOutlined /> 上传后可以选择需要分析的字段
                </div>
                <div className="tip-item">
                  <CheckCircleOutlined /> 通过自然语言描述分析需求
                </div>
                <div className="tip-item">
                  <CheckCircleOutlined /> AI 自动生成代码并执行分析
                </div>
              </>
            )}
          </Space>
        </div>
      </div>
    </div>
  )
}

export default FileUpload

