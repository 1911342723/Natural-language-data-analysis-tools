# 前端架构设计文档

## 🎯 设计目标

基于 **Jupyter Notebook 执行模式** 的智能数据分析前端，核心特点：
1. **Agent 执行过程可视化**：实时展示 AI 生成代码 → 执行 → 判断 → 修复的完整流程
2. **交互式数据分析**：类似 Jupyter 的单元格执行模式
3. **自然语言驱动**：用户通过自然语言描述需求，AI 生成并执行代码

---

## 🏗️ 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         用户界面层                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  文件上传    │  │  字段选择    │  │  对话交互    │     │
│  │  组件        │  │  组件        │  │  组件        │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Agent 执行过程可视化组件 ⭐                  │   │
│  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                │   │
│  │  │Step1│→│Step2│→│Step3│→│Step4│                   │   │
│  │  └─────┘  └─────┘  └─────┘  └─────┘                │   │
│  │  每个步骤包含：                                       │   │
│  │  - 生成的代码（Monaco Editor）                       │   │
│  │  - 执行输出（stdout/stderr）                        │   │
│  │  - 错误信息（如果有）                                │   │
│  │  - 修复建议（AI生成）                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              结果展示组件                             │   │
│  │  - AI 总结（Markdown）                               │   │
│  │  - 表格数据（支持排序/筛选/导出）                    │   │
│  │  - 图表（支持查看大图/下载）                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                        状态管理层                             │
│                      (Zustand Store)                         │
├─────────────────────────────────────────────────────────────┤
│  - fileData: 上传的文件数据                                  │
│  - selectedColumns: 用户选择的字段                           │
│  - sessionId: Jupyter Session ID                            │
│  - agentSteps: Agent 执行步骤数组                            │
│  - conversations: 对话历史                                   │
│  - currentResult: 当前分析结果                               │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                        API 服务层                             │
├─────────────────────────────────────────────────────────────┤
│  - uploadFile(): 上传文件                                    │
│  - createSession(): 创建 Jupyter Session                    │
│  - submitAnalysisRequest(): 提交分析需求                     │
│  - getAgentStatus(): 轮询 Agent 状态                         │
│  - exportResult(): 导出结果                                  │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    后端 API (FastAPI)                         │
│                  Jupyter Kernel Manager                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 核心交互流程

### 1. 文件上传流程

```
用户选择文件
    ↓
FileUpload 组件触发上传
    ↓
调用 uploadFile() API
    ↓
显示上传进度条
    ↓
后端解析文件并返回：
  - columns: 字段列表（含类型）
  - preview: 前100行数据
  - statistics: 统计信息
    ↓
更新 Store：setFileData()
    ↓
自动展示数据预览 + 字段选择侧边栏
```

### 2. Agent 执行流程 ⭐

```
用户输入自然语言需求 + 选择字段
    ↓
点击"发送"按钮
    ↓
ChatArea 组件处理：
  1. 创建/获取 Session ID
  2. 调用 submitAnalysisRequest()
  3. 获取 task_id
    ↓
启动轮询：每2秒调用 getAgentStatus(task_id)
    ↓
AgentExecution 组件展示实时步骤：

Step 1: 生成代码（第1次尝试）
  - AI 根据需求生成 Python 代码
  - 展示代码（Monaco Editor）
  - 状态: running
    ↓
Step 2: 执行代码
  - 在 Jupyter Kernel 中执行
  - 展示执行输出（stdout）
  - 状态: running
    ↓
Step 3: 判断结果
  - 检查是否有错误
  - 如果成功 → Step 5
  - 如果失败 → Step 4
    ↓
Step 4: 错误分析 + 修复（如果需要）
  - AI 分析错误信息
  - 生成修复后的代码
  - 重新执行（回到 Step 2）
  - 状态: failed → running
    ↓
Step 5: 成功 ✅
  - 展示分析结果
  - AI 生成总结
  - 状态: success
    ↓
停止轮询
更新 currentResult
添加到对话历史
```

### 3. 轮询机制

```javascript
// AgentExecution.jsx
useEffect(() => {
  if (!currentTaskId || !polling) return

  const pollInterval = setInterval(async () => {
    const response = await getAgentStatus(currentTaskId)
    
    // 更新步骤
    if (response.data.steps) {
      response.data.steps.forEach((step, index) => {
        if (index >= agentSteps.length) {
          addAgentStep(step)  // 新步骤
        } else {
          updateAgentStep(index, step)  // 更新已有步骤
        }
      })
    }
    
    // 完成或失败时停止轮询
    if (response.status === 'completed' || response.status === 'failed') {
      setPolling(false)
      setAgentExecuting(false)
    }
  }, 2000)

  return () => clearInterval(pollInterval)
}, [currentTaskId, polling])
```

---

## 📦 核心组件详解

### 1. AgentExecution 组件 ⭐⭐⭐

**最核心的组件**，负责展示 Agent 执行过程。

```javascript
<AgentExecution>
  {/* 步骤流程图 */}
  <Steps current={currentStep}>
    {agentSteps.map(step => (
      <Step
        title={step.title}
        status={step.status}  // process/finish/error
        icon={step.icon}
      />
    ))}
  </Steps>

  {/* 每个步骤的详细信息 */}
  <Collapse activeKey={currentStep}>
    {agentSteps.map((step, index) => (
      <Panel key={index}>
        {/* 代码 */}
        {step.code && (
          <Editor
            language="python"
            value={step.code}
            readOnly
          />
        )}

        {/* 输出 */}
        {step.output && (
          <pre>{step.output}</pre>
        )}

        {/* 错误 */}
        {step.error && (
          <Alert type="error" message={step.error} />
        )}

        {/* 结果 */}
        {step.result && (
          <ResultDisplay result={step.result} />
        )}
      </Panel>
    ))}
  </Collapse>
</AgentExecution>
```

**数据结构：**

```javascript
// agentStep 对象结构
{
  title: "步骤1：生成代码",
  description: "根据用户需求生成 Python 分析代码",
  status: "running",  // running | success | failed
  code: "import pandas as pd\n...",
  output: "✅ 数据加载成功\n...",
  error: null,
  result: {
    table_data: [...],
    chart_base64: "...",
    summary: "..."
  }
}
```

### 2. ChatArea 组件

对话交互的核心组件。

```javascript
<ChatArea>
  {/* 对话历史 */}
  <ConversationList>
    {conversations.map(conv => (
      <div className={conv.type}>
        {conv.type === 'user' ? (
          <p>{conv.content}</p>
        ) : (
          <ReactMarkdown>{conv.content}</ReactMarkdown>
        )}
      </div>
    ))}
  </ConversationList>

  {/* Agent 执行区（动态显示） */}
  {agentExecuting && <AgentExecution />}

  {/* 输入区 */}
  <div className="input-area">
    <TextArea
      value={userInput}
      placeholder="描述你的数据分析需求..."
      onPressEnter={handleSubmit}
    />
    <Button onClick={handleSubmit}>发送</Button>
  </div>
</ChatArea>
```

### 3. FieldSelector 组件

字段选择侧边栏。

```javascript
<FieldSelector>
  {/* 搜索 */}
  <Input placeholder="搜索字段..." />

  {/* 字段列表 */}
  {columns.map(col => (
    <div
      className={selectedColumns.includes(col.name) ? 'selected' : ''}
      onClick={() => toggleColumn(col.name)}
    >
      <Checkbox checked={selectedColumns.includes(col.name)}>
        {col.name}
        <Tag color={getTypeColor(col.type)}>{col.type}</Tag>
      </Checkbox>
    </div>
  ))}

  {/* 已选字段预览 */}
  <Table
    columns={selectedColumns}
    dataSource={dataPreview.slice(0, 5)}
  />
</FieldSelector>
```

---

## 🎨 UI/UX 设计原则

### 1. 渐进式信息展示

```
初始状态：
  └─ 显示文件上传界面（全屏）

上传文件后：
  ├─ 左侧：字段选择侧边栏（可折叠）
  └─ 右侧：
      ├─ 数据预览（可收起）
      └─ 对话区

开始分析后：
  └─ 对话区扩展，显示：
      ├─ 对话历史
      ├─ Agent 执行过程（实时更新）
      └─ 输入框

完成分析后：
  └─ 显示结果：
      ├─ AI 总结
      ├─ 表格数据
      └─ 图表
```

### 2. 视觉反馈

- **加载状态**：所有异步操作都有加载动画
- **进度指示**：文件上传显示进度条
- **状态颜色**：
  - 蓝色：进行中（processing）
  - 绿色：成功（success）
  - 红色：失败（error）
- **动画效果**：对话消息淡入、Agent 步骤展开

### 3. 错误处理

所有 API 调用都有错误处理：

```javascript
try {
  const response = await api.call()
  // 成功处理
} catch (error) {
  console.error('操作失败:', error)
  message.error('操作失败，请重试')
}
```

---

## 🔧 状态管理设计

使用 **Zustand** 进行状态管理，优势：
- 简单直观，无需 Provider
- 性能优秀，按需更新
- TypeScript 支持友好

### Store 结构

```javascript
const useAppStore = create((set, get) => ({
  // 文件相关
  fileData: null,
  setFileData: (data) => set({ fileData: data }),

  // 字段选择
  selectedColumns: [],
  toggleColumn: (colName) => {
    const { selectedColumns } = get()
    set({
      selectedColumns: selectedColumns.includes(colName)
        ? selectedColumns.filter(c => c !== colName)
        : [...selectedColumns, colName]
    })
  },

  // Agent 执行
  agentSteps: [],
  addAgentStep: (step) => {
    const { agentSteps } = get()
    set({ agentSteps: [...agentSteps, step] })
  },
  updateAgentStep: (index, updates) => {
    const { agentSteps } = get()
    const newSteps = [...agentSteps]
    newSteps[index] = { ...newSteps[index], ...updates }
    set({ agentSteps: newSteps })
  },

  // 对话历史
  conversations: [],
  addConversation: (conv) => {
    const { conversations } = get()
    set({ conversations: [...conversations, conv] })
  },
}))
```

### 组件使用

```javascript
// 读取状态
const agentSteps = useAppStore(state => state.agentSteps)

// 调用方法
const addAgentStep = useAppStore(state => state.addAgentStep)

// 性能优化：只订阅需要的状态
const selectedColumns = useAppStore(state => state.selectedColumns)
```

---

## 🚀 性能优化

### 1. 代码分割

使用 Vite 的动态导入：

```javascript
const MonacoEditor = lazy(() => import('@monaco-editor/react'))
```

### 2. 虚拟滚动

对于大量数据的表格，使用虚拟滚动：

```javascript
<Table
  scroll={{ y: 400 }}
  virtual
/>
```

### 3. 防抖优化

搜索输入使用防抖：

```javascript
import { useDebounce } from 'ahooks'

const debouncedSearch = useDebounce(searchText, { wait: 300 })
```

### 4. 按需加载

Ant Design 组件自动按需引入（Vite 插件）。

---

## 📱 响应式设计

### 断点设计

```css
/* 移动端 */
@media (max-width: 768px) {
  .field-sidebar {
    width: 100%;
  }
}

/* 平板 */
@media (min-width: 768px) and (max-width: 1024px) {
  .field-sidebar {
    width: 250px;
  }
}

/* 桌面 */
@media (min-width: 1024px) {
  .field-sidebar {
    width: 300px;
  }
}
```

---

## 🐛 调试指南

### 开发者工具

1. **React DevTools**：查看组件树和状态
2. **Redux DevTools**：（如果使用 Redux）
3. **Network 面板**：查看 API 请求

### 日志输出

代码中使用 `console.log` 记录关键操作：

```javascript
console.log('✅ Session 创建成功:', sessionId)
console.log('🤖 Agent 任务启动:', response)
console.log('📊 Agent 状态:', status, data)
```

搜索日志前缀快速定位：
- ✅：成功操作
- 🤖：Agent 相关
- 📊：数据相关
- ❌：错误

---

## 🔮 未来优化方向

### 1. WebSocket 替代轮询

```javascript
// 当前：每2秒轮询一次
setInterval(() => getAgentStatus(), 2000)

// 优化：WebSocket 实时推送
const ws = new WebSocket('ws://localhost:8000/ws')
ws.onmessage = (event) => {
  const step = JSON.parse(event.data)
  addAgentStep(step)
}
```

### 2. 代码编辑功能

允许用户修改 AI 生成的代码：

```javascript
<Editor
  language="python"
  value={code}
  onChange={setCode}  // 可编辑
  readOnly={false}
/>
<Button onClick={runEditedCode}>运行修改后的代码</Button>
```

### 3. 离线缓存

使用 Service Worker 缓存历史记录：

```javascript
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
}
```

### 4. 更丰富的图表类型

集成 ECharts 或 Plotly.js 支持更多图表：
- 热力图
- 3D 图表
- 地图
- 动态图表

---

## 📚 参考资源

- [React 官方文档](https://react.dev/)
- [Ant Design 组件库](https://ant.design/)
- [Zustand 状态管理](https://github.com/pmndrs/zustand)
- [Monaco Editor](https://microsoft.github.io/monaco-editor/)
- [Vite 构建工具](https://vitejs.dev/)

---

**作者**: AI Assistant  
**创建日期**: 2025-10-30  
**版本**: v1.0.0


