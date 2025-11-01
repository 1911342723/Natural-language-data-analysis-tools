import { useState } from 'react'
import { 
  Modal, 
  Input, 
  Button, 
  Table, 
  message, 
  Space, 
  Alert,
  Card,
  Typography,
  Tree,
  Divider,
  Tag,
  Tooltip,
  Tabs,
  Spin
} from 'antd'
import { 
  FileTextOutlined,
  TableOutlined,
  DownloadOutlined,
  ClearOutlined,
  ApiOutlined,
  RobotOutlined,
  CheckOutlined,
  InfoCircleOutlined,
  BranchesOutlined,
  SendOutlined
} from '@ant-design/icons'
import './JsonConverter.css'

const { TextArea } = Input
const { Title, Text } = Typography

function JsonConverter({ visible, onClose }) {
  const [jsonInput, setJsonInput] = useState('')
  const [parsedJson, setParsedJson] = useState(null)
  const [fieldTree, setFieldTree] = useState([])
  const [selectedFields, setSelectedFields] = useState([])
  const [tableData, setTableData] = useState([])
  const [columns, setColumns] = useState([])
  const [loading, setLoading] = useState(false)
  const [aiPrompt, setAiPrompt] = useState('')
  const [aiAnalyzing, setAiAnalyzing] = useState(false)

  // 递归构建字段树
  const buildFieldTree = (obj, path = '', parentKey = '') => {
    const result = []
    
    if (Array.isArray(obj)) {
      // 对于数组，分析第一个元素的结构
      if (obj.length > 0) {
        const firstItem = obj[0]
        if (typeof firstItem === 'object' && firstItem !== null) {
          const children = buildFieldTree(firstItem, path, parentKey)
          return [{
            title: `[数组 - ${obj.length} 项]`,
            key: path || 'root',
            path: path,
            type: 'array',
            children: children.length > 0 ? children : undefined,
            isLeaf: children.length === 0,
            checkable: false, // 数组节点不可选
            disabled: true, // 禁用选择
            disableCheckbox: true // 隐藏复选框
          }]
        } else {
          return [{
            title: `[基本类型数组 - ${obj.length} 项]`,
            key: path || 'root',
            path: path,
            type: 'primitive-array',
            isLeaf: true,
            checkable: false,
            disabled: true,
            disableCheckbox: true
          }]
        }
      } else {
        return [{
          title: '[空数组]',
          key: path || 'root',
          path: path,
          type: 'empty-array',
          isLeaf: true,
          checkable: false,
          disabled: true,
          disableCheckbox: true
        }]
      }
    } else if (typeof obj === 'object' && obj !== null) {
      Object.keys(obj).forEach((key) => {
        const value = obj[key]
        const currentPath = path ? `${path}.${key}` : key
        const nodeKey = parentKey ? `${parentKey}.${key}` : key
        
        let type = typeof value
        let children = []
        let isLeaf = true
        let isCheckable = true
        
        if (Array.isArray(value)) {
          type = 'array'
          if (value.length > 0 && typeof value[0] === 'object') {
            // 对象数组：不可选，需要展开
            isLeaf = false
            isCheckable = false
            children = buildFieldTree(value[0], currentPath, nodeKey)
          } else {
            // 基本类型数组：可选，显示为 JSON 字符串
            isLeaf = true
            isCheckable = true
          }
        } else if (value !== null && typeof value === 'object') {
          // 对象：不可选，需要展开
          type = 'object'
          isLeaf = false
          isCheckable = false
          children = buildFieldTree(value, currentPath, nodeKey)
        }
        
        result.push({
          title: (
            <span>
              <Text strong>{key}</Text>
              <Tag style={{ marginLeft: 8, fontSize: 11 }} color={getTypeColor(type)}>
                {type}
              </Tag>
            </span>
          ),
          key: nodeKey,
          path: currentPath,
          type: type,
          children: children.length > 0 ? children : undefined,
          isLeaf: isLeaf,
          checkable: isCheckable,
          disableCheckbox: !isCheckable
        })
      })
    }
    
    return result
  }

  // 获取类型颜色
  const getTypeColor = (type) => {
    const colorMap = {
      'string': 'green',
      'number': 'blue',
      'boolean': 'purple',
      'array': 'orange',
      'object': 'cyan',
      'null': 'default'
    }
    return colorMap[type] || 'default'
  }

  // 根据路径提取值
  const getValueByPath = (obj, path) => {
    if (!path) return obj
    const keys = path.split('.')
    let current = obj
    
    for (const key of keys) {
      if (current === null || current === undefined) return null
      current = current[key]
    }
    
    return current
  }

  // 查找数据中的数组位置（找最深层的对象数组，忽略基本类型数组，支持嵌套数组）
  const findArrayInPath = (data, paths) => {
    let deepestArrayPath = ''
    let deepestArrayData = null
    let maxDepth = -1
    
    // 遍历所有路径，找到最深层的对象数组
    for (const path of paths) {
      const keys = path.split('.')
      let current = data
      let currentPath = ''
      
      for (let i = 0; i < keys.length; i++) {
        const key = keys[i]
        currentPath = currentPath ? `${currentPath}.${key}` : key
        
        if (current === null || current === undefined) break
        
        // 如果当前是数组，进入第一个元素继续查找
        if (Array.isArray(current) && current.length > 0) {
          current = current[0]
        }
        
        current = current[key]
        
        if (Array.isArray(current) && current.length > 0) {
          // 只处理对象数组，忽略基本类型数组（如 ['Python', 'JavaScript']）
          const firstItem = current[0]
          if (typeof firstItem === 'object' && firstItem !== null) {
            // 这是对象数组，可以展开
            const depth = currentPath.split('.').length
            console.log(`🔍 findArrayInPath: 找到对象数组 ${currentPath}, depth=${depth}`)
            if (depth > maxDepth) {
              maxDepth = depth
              deepestArrayPath = currentPath
              deepestArrayData = current
            }
          }
        }
      }
    }
    
    console.log(`🔍 findArrayInPath: 最深数组=${deepestArrayPath}, maxDepth=${maxDepth}`)
    return { arrayPath: deepestArrayPath, arrayData: deepestArrayData }
  }

  // 扁平化数据（从选中的字段提取，支持嵌套数组）
  const flattenData = (data, selectedPaths) => {
    if (!data || selectedPaths.length === 0) return []
    
    console.log('🔍 开始提取数据:', { data, selectedPaths })
    
    // 查找最深层的对象数组（不包括基本类型数组）
    const { arrayPath, arrayData } = findArrayInPath(data, selectedPaths)
    
    console.log('🔍 找到数组:', { arrayPath, arrayData })
    
    // 如果没找到数组，或者数据本身就是数组
    if (!arrayPath && Array.isArray(data)) {
      console.log('🔍 处理根数组')
      return data.map((item, index) => {
        const row = { _index: index + 1 }
        selectedPaths.forEach(path => {
          const value = getValueByPath(item, path)
          row[path] = formatValue(value)
        })
        return row
      })
    }
    
    // 如果没有数组
    if (!arrayPath || !arrayData) {
      console.log('🔍 没有数组，提取单行')
      const row = {}
      selectedPaths.forEach(path => {
        const value = getValueByPath(data, path)
        row[path] = formatValue(value)
      })
      return [row]
    }
    
    // 有数组，需要展开
    console.log('🔍 展开数组:', arrayPath)
    const result = []
    let rowIndex = 0
    
    // 简化逻辑：找到目标数组并展开
    const arrayPathParts = arrayPath.split('.')
    const targetArrayValue = getValueByPath(data, arrayPath)
    
    if (!Array.isArray(targetArrayValue)) {
      console.error('🔍 目标不是数组:', targetArrayValue)
      return result
    }
    
    console.log('🔍 目标数组元素数:', targetArrayValue.length)
    
    // 递归函数：从根数据遍历到目标数组
    const expandFromRoot = (currentData, pathIndex, parentRow) => {
      console.log(`🔍 expandFromRoot pathIndex=${pathIndex}`)
      console.log(`🔍 currentData type:`, typeof currentData, Array.isArray(currentData) ? '(array)' : '')
      
      if (pathIndex >= arrayPathParts.length) {
        console.error(`🔍 错误：超出路径范围`)
        return
      }
      
      const currentKey = arrayPathParts[pathIndex]
      const currentPath = arrayPathParts.slice(0, pathIndex + 1).join('.')
      const nextData = currentData[currentKey]
      
      console.log(`🔍 访问路径[${pathIndex}]: ${currentKey}, currentPath=${currentPath}`)
      console.log(`🔍 nextData type:`, typeof nextData, Array.isArray(nextData) ? '(array)' : '')
      
      if (Array.isArray(nextData)) {
        // 当前层级是数组
        console.log(`🔍 遍历数组层级 ${pathIndex}: ${currentPath}, 元素数: ${nextData.length}`)
        
        // 检查是否为目标数组
        if (currentPath === arrayPath) {
          // 这就是目标数组！直接提取
          console.log(`🔍 到达目标数组！直接提取字段`)
          nextData.forEach((item, idx) => {
            rowIndex++
            const row = { ...parentRow, _index: rowIndex }
            console.log(`🔍 处理目标数组元素 ${idx}:`, item)
            
            // 提取目标数组内的字段
            selectedPaths.forEach(fieldPath => {
              if (fieldPath.startsWith(arrayPath + '.')) {
                const relativePath = fieldPath.substring(arrayPath.length + 1)
                console.log(`🔍 提取字段 ${fieldPath}, 相对路径: ${relativePath}`)
                const value = getValueByPath(item, relativePath)
                row[fieldPath] = formatValue(value)
                console.log(`🔍 提取值: ${fieldPath} = ${value}`)
              }
            })
            
            console.log(`🔍 生成行:`, row)
            result.push(row)
          })
        } else {
          // 不是目标数组，需要继续向下
          console.log(`🔍 不是目标数组，继续遍历`)
          nextData.forEach((item, idx) => {
            console.log(`🔍 数组元素[${idx}]:`, item)
            const newRow = { ...parentRow }
            
            // 提取当前层级的字段（不在目标数组内的）
            selectedPaths.forEach(fieldPath => {
              if (fieldPath.startsWith(currentPath + '.') && !fieldPath.startsWith(arrayPath + '.')) {
                const relativePath = fieldPath.substring(currentPath.length + 1)
                // 只提取简单字段，不提取对象和对象数组
                const value = getValueByPath(item, relativePath)
                if (value !== undefined && (typeof value !== 'object' || Array.isArray(value))) {
                  newRow[fieldPath] = formatValue(value)
                  console.log(`🔍 当前层提取 ${fieldPath} = ${value}`)
                }
              }
            })
            
            // 继续向下
            expandFromRoot(item, pathIndex + 1, newRow)
          })
        }
      } else if (nextData !== undefined) {
        // 不是数组，继续向下
        console.log(`🔍 非数组，继续向下`)
        expandFromRoot(nextData, pathIndex + 1, parentRow)
      } else {
        console.error(`🔍 错误：路径 ${currentKey} 不存在于当前数据`)
      }
    }
    
    // 初始行：提取数组外的字段
    const initialRow = {}
    selectedPaths.forEach(fieldPath => {
      if (!fieldPath.startsWith(arrayPathParts[0] + '.')) {
        // 字段完全在数组路径外
        const value = getValueByPath(data, fieldPath)
        initialRow[fieldPath] = formatValue(value)
        console.log(`🔍 数组外字段 ${fieldPath} = ${value}`)
      }
    })
    
    // 开始递归
    expandFromRoot(data, 0, initialRow)
    
    console.log('🔍 最终结果:', result)
    return result
  }

  // 格式化值
  const formatValue = (value) => {
    if (value === null || value === undefined) return null
    if (typeof value === 'object') return JSON.stringify(value)
    return value
  }

  // 解析JSON
  const handleParseJson = () => {
    if (!jsonInput.trim()) {
      message.warning('请输入JSON数据')
      return
    }

    setLoading(true)
    try {
      const parsed = JSON.parse(jsonInput)
      setParsedJson(parsed)
      
      // 构建字段树
      const tree = buildFieldTree(parsed)
      setFieldTree(tree)
      
      message.success('JSON解析成功！请在右侧选择需要提取的字段')
      
      // 清空之前的选择
      setSelectedFields([])
      setTableData([])
      setColumns([])
    } catch (error) {
      message.error(`JSON解析失败: ${error.message}`)
      console.error('JSON解析错误:', error)
    } finally {
      setLoading(false)
    }
  }

  // 字段选择变化
  const handleFieldSelect = (selectedKeys) => {
    setSelectedFields(selectedKeys)
  }

  // 生成表格
  const handleGenerateTable = () => {
    if (selectedFields.length === 0) {
      message.warning('请至少选择一个字段')
      return
    }

    try {
      console.log('📊 开始生成表格...')
      console.log('📊 选中的字段keys:', selectedFields)
      
      // 提取选中字段的路径
      const selectedPaths = selectedFields.map(key => {
        // 查找树节点获取路径
        const findPath = (nodes) => {
          for (const node of nodes) {
            if (node.key === key) return node.path
            if (node.children) {
              const found = findPath(node.children)
              if (found) return found
            }
          }
          return null
        }
        return findPath(fieldTree)
      }).filter(Boolean)

      console.log('📊 提取的路径:', selectedPaths)

      if (selectedPaths.length === 0) {
        message.error('无法获取字段路径，请重新选择')
        return
      }

      // 扁平化数据
      const flattened = flattenData(parsedJson, selectedPaths)
      
      console.log('📊 扁平化后的数据:', flattened)

      if (flattened.length === 0) {
        message.warning('没有提取到数据，请检查JSON结构')
        return
      }
      
      // 生成列配置
      const cols = selectedPaths.map(path => ({
        title: path.split('.').pop(), // 显示最后一级字段名
        dataIndex: path,
        key: path,
        ellipsis: true,
        width: 150,
        render: (value) => {
          if (value === null || value === undefined) {
            return <span style={{ color: '#bfbfbf' }}>-</span>
          }
          return <span title={String(value)}>{String(value)}</span>
        }
      }))

      // 如果有序号列，添加到最前面
      if (flattened[0] && flattened[0]._index !== undefined) {
        cols.unshift({
          title: '#',
          dataIndex: '_index',
          key: '_index',
          width: 60,
          fixed: 'left'
        })
      }

      // 添加key
      const dataWithKeys = flattened.map((item, index) => ({
        ...item,
        key: index
      }))

      console.log('📊 最终表格数据:', dataWithKeys)
      console.log('📊 列配置:', cols)

      setTableData(dataWithKeys)
      setColumns(cols)
      message.success(`已生成表格：${dataWithKeys.length} 行 × ${cols.length} 列`)
    } catch (error) {
      message.error(`生成表格失败: ${error.message}`)
      console.error('❌ 生成表格错误:', error)
    }
  }

  // AI辅助分析（模拟）
  const handleAiAnalyze = () => {
    if (!aiPrompt.trim()) {
      message.warning('请描述你需要提取的字段')
      return
    }
    
    if (!parsedJson) {
      message.warning('请先解析JSON')
      return
    }

    setAiAnalyzing(true)
    
    // 模拟AI分析（实际应该调用AI API）
    setTimeout(() => {
      message.info('AI辅助功能需要配置AI API。当前可以手动在左侧树中选择字段。')
      setAiAnalyzing(false)
      
      // TODO: 集成实际的AI API
      // 示例：根据用户描述，AI分析JSON结构并推荐字段
    }, 1000)
  }

  // 下载CSV
  const handleDownloadCSV = () => {
    if (tableData.length === 0) {
      message.warning('没有可下载的数据')
      return
    }

    try {
      const headers = columns.map(col => col.title).join(',')
      const rows = tableData.map(row => {
        return columns.map(col => {
          const value = row[col.dataIndex]
          if (value === null || value === undefined) return ''
          const str = String(value)
          if (str.includes(',') || str.includes('"') || str.includes('\n')) {
            return `"${str.replace(/"/g, '""')}"`
          }
          return str
        }).join(',')
      })

      const csv = [headers, ...rows].join('\n')
      const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      
      link.setAttribute('href', url)
      link.setAttribute('download', `json_extract_${Date.now()}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      message.success('CSV文件已下载')
    } catch (error) {
      message.error(`下载失败: ${error.message}`)
    }
  }

  // 清空
  const handleClear = () => {
    setJsonInput('')
    setParsedJson(null)
    setFieldTree([])
    setSelectedFields([])
    setTableData([])
    setColumns([])
    setAiPrompt('')
  }

  // 关闭
  const handleClose = () => {
    handleClear()
    onClose()
  }

  // 示例JSON（复杂嵌套结构）
  const exampleJson = JSON.stringify({
    status: 'success',
    data: {
      users: [
        {
          id: 1,
          name: '张三',
          profile: {
            age: 25,
            city: '北京',
            skills: ['Python', 'JavaScript']
          },
          orders: [
            { orderId: 'A001', amount: 299 },
            { orderId: 'A002', amount: 459 }
          ]
        },
        {
          id: 2,
          name: '李四',
          profile: {
            age: 30,
            city: '上海',
            skills: ['Java', 'Go']
          },
          orders: [
            { orderId: 'B001', amount: 599 }
          ]
        }
      ]
    }
  }, null, 2)

  return (
    <Modal
      title={
        <Space>
          <ApiOutlined />
          <span>智能 JSON 解析器</span>
          <Tag color="blue">支持复杂嵌套</Tag>
        </Space>
      }
      open={visible}
      onCancel={handleClose}
      width={1400}
      footer={null}
      className="json-converter-modal"
    >
      <div className="json-converter-container-v2">
        {/* 左侧：JSON输入和解析 */}
        <div className="json-left-panel">
          <Card
            size="small"
            title={<Space><FileTextOutlined /> JSON 数据</Space>}
            extra={
              <Space size="small">
                <Button
                  type="primary"
                  icon={<CheckOutlined />}
                  onClick={handleParseJson}
                  loading={loading}
                  size="small"
                >
                  解析结构
                </Button>
                <Button
                  icon={<ClearOutlined />}
                  onClick={handleClear}
                  size="small"
                >
                  清空
                </Button>
              </Space>
            }
          >
            <TextArea
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
              placeholder={`粘贴你的JSON数据...\n\n支持复杂嵌套结构，例如：\n${exampleJson.substring(0, 200)}...`}
              rows={12}
              className="json-input"
              style={{ fontFamily: 'Consolas, Monaco, monospace', fontSize: 12 }}
            />
            
            <Button
              type="link"
              onClick={() => setJsonInput(exampleJson)}
              size="small"
              style={{ marginTop: 8 }}
            >
              加载示例（嵌套JSON）
            </Button>
          </Card>

          {/* 字段结构树 */}
          {fieldTree.length > 0 && (
            <Card
              size="small"
              title={
                <Space>
                  <BranchesOutlined />
                  <Text strong>字段结构</Text>
                  <Tag color="orange">{selectedFields.length} 个已选</Tag>
                </Space>
              }
              extra={
                <Button
                  type="primary"
                  icon={<TableOutlined />}
                  onClick={handleGenerateTable}
                  size="small"
                  disabled={selectedFields.length === 0}
                >
                  生成表格
                </Button>
              }
              style={{ marginTop: 16 }}
            >
              <Alert
                message="在下方树中勾选你需要提取的字段"
                type="info"
                showIcon
                closable
                style={{ marginBottom: 12, fontSize: 12 }}
              />
              
              <div className="field-tree-container">
                <Tree
                  checkable
                  defaultExpandAll
                  onCheck={handleFieldSelect}
                  checkedKeys={selectedFields}
                  treeData={fieldTree}
                  className="field-tree"
                />
              </div>
            </Card>
          )}

          {/* AI辅助 */}
          {parsedJson && (
            <Card
              size="small"
              title={
                <Space>
                  <RobotOutlined />
                  <Text strong>AI 辅助提取</Text>
                  <Tag color="purple">实验性</Tag>
                </Space>
              }
              style={{ marginTop: 16 }}
            >
              <Space.Compact style={{ width: '100%' }}>
                <Input
                  placeholder="描述你需要的字段，例如：我需要所有用户的姓名、年龄和城市"
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  onPressEnter={handleAiAnalyze}
                  disabled={aiAnalyzing}
                />
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleAiAnalyze}
                  loading={aiAnalyzing}
                >
                  分析
                </Button>
              </Space.Compact>
            </Card>
          )}
        </div>

        {/* 右侧：表格预览 */}
        <div className="json-right-panel">
          <Card
            size="small"
            title={
              <Space>
                <TableOutlined />
                <Text strong>表格预览</Text>
                {tableData.length > 0 && (
                  <Text type="secondary">({tableData.length} 行 × {columns.length} 列)</Text>
                )}
              </Space>
            }
            extra={
              tableData.length > 0 && (
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  onClick={handleDownloadCSV}
                  size="small"
                >
                  下载 CSV
                </Button>
              )
            }
          >
            {tableData.length === 0 ? (
              <div className="empty-preview">
                <TableOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />
                <Text type="secondary" style={{ marginTop: 16, display: 'block' }}>
                  1. 在左侧粘贴JSON数据
                </Text>
                <Text type="secondary" style={{ display: 'block' }}>
                  2. 点击"解析结构"查看字段树
                </Text>
                <Text type="secondary" style={{ display: 'block' }}>
                  3. 勾选需要的字段
                </Text>
                <Text type="secondary" style={{ display: 'block' }}>
                  4. 点击"生成表格"
                </Text>
              </div>
            ) : (
              <>
                <Alert
                  message="提取成功"
                  description={`已从JSON中提取 ${tableData.length} 行数据，包含 ${columns.length} 个字段`}
                  type="success"
                  showIcon
                  closable
                  style={{ marginBottom: 12 }}
                />
                <Table
                  columns={columns}
                  dataSource={tableData}
                  scroll={{ x: 'max-content', y: 500 }}
                  pagination={{
                    pageSize: 20,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total) => `共 ${total} 条`,
                    pageSizeOptions: ['10', '20', '50', '100']
                  }}
                  size="small"
                  bordered
                  className="result-table"
                />
              </>
            )}
          </Card>
        </div>
      </div>

      {/* 底部说明 */}
      <Alert
        message={
          <Space>
            <InfoCircleOutlined />
            <Text strong>功能说明</Text>
          </Space>
        }
        description={
          <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12 }}>
            <li><strong>智能识别</strong>：自动解析多层嵌套JSON结构，以树形展示所有字段</li>
            <li><strong>字段选择</strong>：在树中勾选需要的字段，支持嵌套路径（如 data.users.profile.age）</li>
            <li><strong>数组展开</strong>：自动展开数组为多行数据</li>
            <li><strong>AI辅助</strong>：通过自然语言描述需求，AI帮你识别字段（需配置AI API）</li>
            <li><strong>CSV导出</strong>：一键下载为Excel可打开的CSV文件</li>
          </ul>
        }
        type="info"
        showIcon
        style={{ marginTop: 16 }}
      />
    </Modal>
  )
}

export default JsonConverter
