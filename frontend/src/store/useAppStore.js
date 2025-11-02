import { create } from 'zustand'

/**
 * 全局状态管理 Store
 * 使用 Zustand 轻量级状态管理
 */
const useAppStore = create((set, get) => ({
  // ========== 文件相关 ==========
  uploadMode: 'single', // 'single' | 'multiple'
  uploadedFile: null, // 单文件模式
  fileData: null, // 解析后的文件数据（单文件）
  sheets: [], // 所有工作表（单文件）
  currentSheetName: null, // 当前选择的工作表名称（单文件）
  
  // 多文件模式
  fileGroup: null, // { group_id, files: [{file_id, file_name, sheets: [...]}] }
  selectedTables: [], // 用户选择的表格 [{file_id, sheet_name, alias, file_name}]
  
  setUploadMode: (mode) => set({ uploadMode: mode }),
  
  setUploadedFile: (file) => set({ uploadedFile: file }),
  
  setFileData: (data) => {
    // 支持多工作表结构（单文件模式）
    const sheets = data.sheets || []
    const firstSheet = sheets.length > 0 ? sheets[0] : null
    
    set({
      fileData: data,
      sheets: sheets,
      currentSheetName: firstSheet ? firstSheet.sheet_name : null,
    })
  },
  
  // 设置文件组（多文件模式）
  setFileGroup: (group) => set({
    fileGroup: group,
    uploadMode: 'multiple',
    selectedTables: [],
  }),
  
  // 添加/移除选择的表格
  toggleTable: (table) => {
    const { selectedTables } = get()
    const exists = selectedTables.find(
      t => t.file_id === table.file_id && t.sheet_name === table.sheet_name
    )
    
    if (exists) {
      set({
        selectedTables: selectedTables.filter(
          t => !(t.file_id === table.file_id && t.sheet_name === table.sheet_name)
        )
      })
    } else {
      // 生成alias（df1, df2, df3...）
      const alias = `df${selectedTables.length + 1}`
      set({
        selectedTables: [...selectedTables, { 
          ...table, 
          alias,
          selected_columns: [] // 初始化为空，用户可以选择字段
        }]
      })
    }
  },
  
  // 更新表格的字段选择
  updateTableColumns: (fileId, sheetName, columns) => {
    const { selectedTables } = get()
    const newTables = selectedTables.map(t => {
      if (t.file_id === fileId && t.sheet_name === sheetName) {
        return { ...t, selected_columns: columns }
      }
      return t
    })
    set({ selectedTables: newTables })
  },
  
  // 切换表格的某个字段选择状态
  toggleTableColumn: (fileId, sheetName, columnName) => {
    const { selectedTables } = get()
    const newTables = selectedTables.map(t => {
      if (t.file_id === fileId && t.sheet_name === sheetName) {
        const selectedCols = t.selected_columns || []
        const isSelected = selectedCols.includes(columnName)
        return {
          ...t,
          selected_columns: isSelected
            ? selectedCols.filter(c => c !== columnName)
            : [...selectedCols, columnName]
        }
      }
      return t
    })
    set({ selectedTables: newTables })
  },
  
  // 全选/取消全选表格的所有字段
  toggleAllTableColumns: (fileId, sheetName, allColumns, selectAll) => {
    const { selectedTables } = get()
    const newTables = selectedTables.map(t => {
      if (t.file_id === fileId && t.sheet_name === sheetName) {
        return {
          ...t,
          selected_columns: selectAll ? allColumns : []
        }
      }
      return t
    })
    set({ selectedTables: newTables })
  },
  
  clearSelectedTables: () => set({ selectedTables: [] }),
  
  setCurrentSheet: (sheetName) => set({ currentSheetName: sheetName }),
  
  // 获取当前工作表的数据
  getCurrentSheet: () => {
    const { sheets, currentSheetName } = get()
    return sheets.find(sheet => sheet.sheet_name === currentSheetName) || null
  },
  
  clearFileData: () => set({
    uploadedFile: null,
    fileData: null,
    sheets: [],
    currentSheetName: null,
    selectedColumns: [],
    fileGroup: null,
    selectedTables: [],
    uploadMode: 'single',
  }),

  // ========== 字段选择相关 ==========
  columns: [], // 所有字段列表（含类型信息）
  selectedColumns: [], // 用户选择的字段
  
  setColumns: (columns) => set({ columns }),
  
  setSelectedColumns: (selectedColumns) => set({ selectedColumns }),
  
  toggleColumn: (columnName) => {
    const { selectedColumns } = get()
    const isSelected = selectedColumns.includes(columnName)
    
    set({
      selectedColumns: isSelected
        ? selectedColumns.filter(col => col !== columnName)
        : [...selectedColumns, columnName]
    })
  },
  
  selectAllColumns: () => {
    const { columns } = get()
    set({ selectedColumns: columns.map(col => col.name) })
  },
  
  clearSelectedColumns: () => set({ selectedColumns: [] }),

  // ========== Session 相关 ==========
  sessionId: null,
  
  setSessionId: (sessionId) => set({ sessionId }),

  // ========== Agent 执行相关 ==========
  agentExecuting: false, // Agent 是否正在执行
  currentTaskId: null, // 当前任务ID
  agentSteps: [], // Agent 执行步骤记录
  agentMode: 'smart', // Agent 模式: 'classic' | 'smart'
  chartStyle: 'publication', // 图表样式: 'publication' | 'presentation' | 'web'
  enableResearchMode: false, // 是否启用科研模式
  selectedChartTypes: [], // 用户选择的图表类型数组: ['boxplot', 'scatter', ...]
  
  setAgentExecuting: (executing) => set({ agentExecuting: executing }),
  
  setCurrentTaskId: (taskId) => set({ currentTaskId: taskId }),
  
  setAgentMode: (mode) => set({ agentMode: mode }),
  setChartStyle: (style) => set({ chartStyle: style }),
  setEnableResearchMode: (enabled) => set({ enableResearchMode: enabled }),
  setSelectedChartTypes: (types) => set({ selectedChartTypes: types }),
  
  addAgentStep: (step) => {
    const { agentSteps } = get()
    set({ agentSteps: [...agentSteps, step] })
  },
  
  updateAgentStep: (stepIndex, updates) => {
    const { agentSteps } = get()
    const newSteps = [...agentSteps]
    newSteps[stepIndex] = { ...newSteps[stepIndex], ...updates }
    set({ agentSteps: newSteps })
  },
  
  clearAgentSteps: () => set({ agentSteps: [] }),

  // ========== 对话历史 ==========
  conversations: [], // 当前会话的对话历史
  
  addConversation: (conversation) => {
    const { conversations } = get()
    set({ conversations: [...conversations, conversation] })
  },
  
  clearConversations: () => set({ conversations: [] }),

  // ========== 结果展示 ==========
  currentResult: null, // 当前分析结果
  
  setCurrentResult: (result) => set({ currentResult: result }),
  
  clearCurrentResult: () => set({ currentResult: null }),

  // ========== 侧边栏状态 ==========
  sidebarCollapsed: false,
  historySidebarVisible: false,
  
  toggleSidebar: () => set({ sidebarCollapsed: !get().sidebarCollapsed }),
  
  setHistorySidebarVisible: (visible) => set({ historySidebarVisible: visible }),
  
  // ========== 重置所有状态 ==========
  resetAll: () => set({
    // 文件相关
    uploadMode: 'single',
    uploadedFile: null,
    fileData: null,
    sheets: [],
    currentSheetName: null,
    fileGroup: null,
    selectedTables: [],
    // 字段选择
    columns: [],
    selectedColumns: [],
    // Session
    sessionId: null,
    // Agent 执行
    agentExecuting: false,
    currentTaskId: null,
    agentSteps: [],
    agentMode: 'smart',
    chartStyle: 'publication',
    enableResearchMode: false,
    selectedChartTypes: [],
    // 对话历史
    conversations: [],
    // 结果
    currentResult: null,
    // UI 状态
    sidebarCollapsed: false,
    historySidebarVisible: false,
  }),
}))

export default useAppStore

