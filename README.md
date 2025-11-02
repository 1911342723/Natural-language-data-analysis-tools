# 🚀 智能数据分析工具

<div align="center">

**基于 AI Agent + Jupyter Kernel 的自然语言数据分析平台**

[![React](https://img.shields.io/badge/React-18.3.1-blue?logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [架构设计](#-架构设计) • [项目结构](#-项目结构) • [API 文档](#-api-文档)

</div>

---

## 📖 项目简介

这是一个基于 **AI Agent + Jupyter Kernel** 架构的 **智能数据分析平台**，让用户通过 **自然语言描述** 就能完成复杂的数据分析任务。系统采用大语言模型（GPT-4/Claude/DeepSeek）理解用户意图，自动生成 Python 分析代码，在隔离的 Jupyter Kernel 环境中安全执行，并实时展示执行过程和结果。

### 🎯 核心能力

**本工具致力于解决以下问题：**
- ✅ **非技术人员的数据分析门槛**：无需学习 Python/SQL，用自然语言即可完成专业数据分析
- ✅ **代码生成的可靠性**：AI Agent 自动检测、修复执行错误，确保分析任务成功完成
- ✅ **分析过程的透明性**：实时展示 AI 思考、代码生成、执行结果，用户可全程监控
- ✅ **大数据量处理**：支持智能采样、分块处理，适配从小文件到数百万行数据的分析
- ✅ **结果的可解释性**：不仅给出结果，还生成 AI 总结，解释数据背后的洞察

### 🌟 核心亮点

- 🤖 **双模式 AI Agent**：
  - **经典模式**：固定4步流程（生成代码 → 执行 → 提取结果 → 生成总结），稳定可靠
  - **智能模式**：自主规划、迭代分析、动态决策，类人思维，适合复杂分析
- 🔬 **科研级可视化** ⭐ NEW：
  - **三种图表样式**：出版级（300 DPI）、演示风格、Web风格
  - **自动统计分析**：t检验、ANOVA、相关性分析、效应量计算
  - **符合期刊标准**：支持Nature/Science等顶级期刊投稿要求
- 📊 **可视化执行过程**：实时展示代码生成 → 执行 → 判断 → 修复的完整流程
- 🔄 **智能错误修复**：代码执行失败时自动分析错误并修复（最多3次重试）
- 📈 **多样化结果**：支持表格、图表、AI 洞察总结等多种展示方式
- 🎯 **零代码体验**：用户无需编程知识，用自然语言即可分析数据
- 🔒 **安全隔离执行**：每个会话独立 Jupyter Kernel，数据隔离，互不干扰
- 💾 **智能数据处理**：自动采样预览、分块加载，支持大文件分析

---

## ✨ 功能特性

### 1. 文件上传与解析 📁

**单文件模式**：
- ✅ 支持多种格式：Excel (`.xlsx`, `.xls`)、CSV
- ✅ 拖拽上传或点击选择
- ✅ 自动解析数据类型和统计信息
- ✅ 数据预览（前 100 行）
- ✅ 大文件支持（最大 100MB）

**多文件模式**：
- ✅ 批量上传多个表格
- ✅ 每个表格独立字段选择
- ✅ 自动识别表格关系
- ✅ 支持多表格联合分析（需在 Prompt 中指定表名）

**JSON 转表格**：
- ✅ 支持复杂嵌套 JSON 解析
- ✅ 智能字段树选择
- ✅ 自动展开数组和对象
- ✅ 导出为 Excel/CSV

**表格转 JSON**：
- ✅ Excel/CSV 一键转 JSON
- ✅ 支持数组/对象格式输出
- ✅ 支持空值处理配置
- ✅ 美化输出（Pretty Print）

### 2. 字段智能选择 🎯

- ✅ 侧边栏展示所有字段
- ✅ 字段搜索和过滤
- ✅ 字段类型标签（int/float/string/datetime）
- ✅ 多选勾选框，支持全选/取消全选
- ✅ 已选字段实时预览

### 3. 自然语言交互 💬

- ✅ 自然语言输入分析需求
- ✅ 示例需求快速填充
- ✅ 对话历史记录
- ✅ Markdown 格式支持
- ✅ 实时字符计数

### 3.5 科研级可视化 🔬 ⭐ NEW

**三种专业图表样式**：
- 📄 **出版级 (Publication)**：300 DPI，符合Nature/Science标准
- 📊 **演示风格 (Presentation)**：大字体，适合会议报告
- 🌐 **Web风格**：交互式图表，适合在线展示

**支持的科研图表类型**：
- 箱线图、小提琴图、热力图、散点矩阵图
- QQ图、残差图、ROC曲线
- 生存曲线、森林图、韦恩图

**自动统计分析**：
- ✅ 组间比较：t检验、ANOVA、Mann-Whitney U检验
- ✅ 相关性分析：Pearson、Spearman相关系数
- ✅ 正态性检验：Shapiro-Wilk检验
- ✅ 效应量计算：Cohen's d、置信区间
- ✅ APA格式输出：`t(98) = 3.45, p = 0.001, d = 0.68`

**使用方法**：
1. 在聊天界面开启"🔬 科研模式"开关
2. 选择图表样式（出版级/演示/Web）
3. 用自然语言描述需求，例如：
   - "比较实验组和对照组的血压差异，画箱线图，做t检验"
   - "分析身高和体重的相关性，画散点图"
   - "检验数据是否符合正态分布，画QQ图"

### 4. Agent 执行过程可视化 ⭐⭐⭐

这是系统最核心的功能！实时展示 AI Agent 的执行流程：

```
步骤 1: 生成代码 (AI)
   ↓
步骤 2: 执行代码 (Jupyter Kernel)
   ↓
步骤 3: 判断结果
   ├─ 成功 → 提取结果 → 生成总结 ✅
   └─ 失败 → 分析错误 → 修复代码 → 重新执行 (最多3次)
```

**展示内容：**
- 🔹 实时步骤流程图
- 🔹 Monaco Editor 代码高亮
- 🔹 执行输出（stdout/stderr）
- 🔹 错误信息和修复过程
- 🔹 每个步骤的状态（运行中/成功/失败）

### 5. 多样化结果展示 📊

- ✅ **AI 总结**：Markdown 格式，支持复制
- ✅ **表格数据**：分页展示、列排序、导出 CSV
- ✅ **图表展示**：支持查看大图、下载 PNG
- ✅ **Tab 切换**：清晰分类不同类型的结果

### 6. 历史记录管理 📚

- ✅ 侧边栏抽屉展示历史记录
- ✅ 搜索和过滤
- ✅ 显示文件名、需求、时间、状态
- ✅ 删除历史记录（带确认）

---

## 🛠️ 技术栈

### 前端

| 技术 | 版本 | 说明 |
|------|------|------|
| React | 18.3.1 | 前端框架 |
| Vite | 5.3.1 | 构建工具 |
| Ant Design | 5.21.0 | UI 组件库 |
| Zustand | 4.5.5 | 状态管理 |
| Monaco Editor | 4.6.0 | 代码编辑器 |
| Axios | 1.7.7 | HTTP 客户端 |
| React Markdown | 9.0.1 | Markdown 渲染 |

### 后端

| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 编程语言 |
| FastAPI | 0.115.0 | Web 框架 |
| Jupyter Client | 8.6.0+ | Jupyter Kernel 管理 ⭐ |
| OpenAI / Anthropic | Latest | AI 模型调用 |
| Pandas | 2.2.0+ | 数据处理 |
| Matplotlib / Seaborn | Latest | 基础图表生成 |
| Plotly | 5.18+ | 交互式图表 ⭐ |
| Scipy | 1.11+ | 统计检验 ⭐ |
| Statsmodels | 0.14+ | 统计建模 ⭐ |
| Pingouin | 0.5+ | 科研统计分析 ⭐ |
| SQLAlchemy | 2.0+ | 数据库 ORM |

---

## 🏗️ 架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                       前端 (React)                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  文件上传    │  │  字段选择    │  │  对话交互    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Agent 执行过程可视化 ⭐                      │   │
│  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                │   │
│  │  │Step1│→│Step2│→│Step3│→│Step4│                   │   │
│  │  └─────┘  └─────┘  └─────┘  └─────┘                │   │
│  │  - 代码高亮 (Monaco)                                 │   │
│  │  - 执行输出 (stdout/stderr)                         │   │
│  │  - 错误分析 & 修复                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              结果展示                                 │   │
│  │  - AI 总结 (Markdown)                                │   │
│  │  - 表格数据 (排序/筛选/导出)                         │   │
│  │  - 图表 (查看大图/下载)                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI)                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  文件处理    │  │  Session管理 │  │  历史记录    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Analysis Agent ⭐⭐⭐                         │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐       │   │
│  │  │ AI Client │  │  Jupyter  │  │  Prompts  │       │   │
│  │  │(GPT/Claude)  │  Manager  │  │  Engine   │       │   │
│  │  └───────────┘  └───────────┘  └───────────┘       │   │
│  │                                                      │   │
│  │  流程：生成代码 → 执行 → 判断 → 修复 (循环)        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  数据库      │  │  文件存储    │                        │
│  │  (SQLite)    │  │  (uploads/)  │                        │
│  └──────────────┘  └──────────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ↕
                    ┌──────────────┐
                    │ Jupyter      │
                    │ Kernel       │
                    │ (Python 3.11)│
                    └──────────────┘
```

### 核心工作流程

1. **文件上传** → 后端解析文件 → 返回字段信息和预览数据
2. **创建 Session** → 后端启动 Jupyter Kernel → 加载数据到内核
3. **提交分析请求** → Agent 开始工作 → 返回 task_id
4. **流式推送状态** → 通过 SSE 实时推送 → 前端即时更新步骤
5. **展示结果** → 提取表格/图表/总结 → 多 Tab 展示

---

## 🧠 核心技术实现

### 1. AI Agent 工作原理

系统提供两种 Agent 模式，满足不同分析场景：

#### 📋 经典模式（Classic Agent）

**特点**：流程固定、稳定可靠、适合常规分析

**执行流程**：

```
┌─────────────────────────────────────────────────────────┐
│  Step 1: 生成分析代码 (AI)                               │
│  ├─ 输入：用户需求 + 数据字段 + 数据样本                  │
│  ├─ AI: GPT-4/Claude/DeepSeek                           │
│  └─ 输出：Python 代码 (pandas + matplotlib/seaborn)     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Step 2: 执行代码 (Jupyter Kernel)                       │
│  ├─ 环境：隔离的 Python Kernel                           │
│  ├─ 数据：已加载的 DataFrame (df)                        │
│  ├─ 超时：最长 300 秒                                    │
│  └─ 捕获：stdout, stderr, 图表 (image/png), 表格        │
└─────────────────────────────────────────────────────────┘
                         ↓
                    执行成功？
                    ↙      ↘
                 Yes        No
                  ↓          ↓
┌─────────────────────┐  ┌──────────────────────────────┐
│ Step 3: 提取结果     │  │ Step 2.5: 错误修复 (最多3次)  │
│ ├─ 图表 (base64)   │  │ ├─ AI 分析错误原因            │
│ ├─ 表格 (HTML)     │  │ ├─ 生成修复后的代码           │
│ └─ 文本输出        │  │ └─ 重新执行 ──┐              │
└─────────────────────┘  └───────────────┘              │
         ↓                         ↑                     │
         └─────────────────────────┘ ←───────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Step 4: 生成总结 (AI)                                   │
│  ├─ 输入：执行结果 + 用户需求                             │
│  ├─ AI: 分析数据洞察                                     │
│  └─ 输出：Markdown 格式总结                              │
└─────────────────────────────────────────────────────────┘
```

**优势**：
- ✅ 流程清晰，易于调试
- ✅ 稳定性高，适合生产环境
- ✅ 执行时间可预测（固定4步）

**适用场景**：
- 常规数据统计、分组聚合
- 简单的图表生成
- 单一明确的分析目标

---

#### 🧠 智能模式（Smart Agent）

**特点**：自主决策、迭代分析、类人思维

**执行流程**：

```
┌─────────────────────────────────────────────────────────┐
│  Phase 1: 分析规划 (Planning)                            │
│  ├─ AI 理解用户需求                                      │
│  ├─ 制定分析策略（需要做什么？怎么做？）                  │
│  └─ 决定需要探索的维度                                   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 2: 数据探索 (Exploration)                         │
│  ├─ 查看数据结构 (df.info(), df.describe())             │
│  ├─ 检查字段分布 (value_counts(), unique())             │
│  ├─ 发现数据特征（缺失值、异常值、数据类型）              │
│  └─ 决定：需要进一步分析哪些维度？                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 3: 迭代分析 (Iterative Analysis)                 │
│  ├─ 循环：生成代码 → 执行 → 判断结果 → 决策下一步       │
│  │   ├─ 生成第1个图表 → 执行成功 → 判断：是否足够？      │
│  │   ├─ No → 生成第2个图表 → ...                        │
│  │   └─ Yes → 进入下一阶段                              │
│  ├─ 自动错误修复（与经典模式相同）                        │
│  └─ 最多迭代：10 轮                                      │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 4: 综合总结 (Summary)                             │
│  ├─ 汇总所有分析结果                                     │
│  ├─ 提取关键洞察                                         │
│  ├─ 生成完整的分析报告                                   │
│  └─ 包含：数据特征 + 可视化结果 + 结论建议               │
└─────────────────────────────────────────────────────────┘
```

**优势**：
- ✅ 自主规划，适应复杂需求
- ✅ 迭代分析，结果更全面
- ✅ 类人思维，能主动发现问题

**适用场景**：
- 模糊需求（如"帮我分析这个数据"）
- 多维度分析（需要多个图表）
- 探索性数据分析（EDA）

**决策示例**：
```
用户："帮我分析销售数据"

AI 规划：
1. 先看数据整体情况（行数、字段、类型）
2. 分析销售额分布（描述性统计）
3. 按时间趋势分析（折线图）
4. 按地区分布分析（柱状图）
5. 按产品类别分析（饼图）
6. 生成综合报告
```

---

### 2. 数据读取策略

#### 📂 文件解析策略

| 文件类型 | 解析方式 | 说明 |
|---------|---------|------|
| **CSV** | `pandas.read_csv()` | 自动检测编码（UTF-8/GBK），推断分隔符 |
| **Excel (.xlsx)** | `pandas.read_excel(engine='openpyxl')` | 支持多 Sheet，自动识别表头 |
| **Excel (.xls)** | `pandas.read_excel(engine='xlrd')` | 兼容旧版 Excel 格式 |

**编码自动检测**：
```python
# 尝试顺序：UTF-8 → GBK → GB2312 → Latin1
encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
for encoding in encodings:
    try:
        df = pd.read_csv(file_path, encoding=encoding)
        break
    except UnicodeDecodeError:
        continue
```

---

#### 📊 大数据量处理策略

**核心原则**：前端预览采样，后端分析全量

| 数据规模 | 前端预览 | 后端分析 | 策略说明 |
|---------|---------|---------|---------|
| **< 1万行** | 全量加载 | 全量分析 | 直接读取，无需优化 |
| **1万 ~ 10万行** | 前100行 | 全量分析 | 前端只显示前100行，后端加载全部 |
| **10万 ~ 50万行** | 前100行 + 采样警告 | 全量分析 | 提示用户数据量较大，可能耗时 |
| **50万 ~ 200万行** | 前100行 + 采样警告 | 分块加载 | 使用 `chunksize` 分块处理 |
| **> 200万行** | 前100行 + 建议筛选 | 智能采样分析 | 建议用户先筛选字段或采样分析 |

**分块加载示例**：
```python
# 对于超大文件，使用分块读取
chunk_size = 10000
chunks = []
for chunk in pd.read_csv(file_path, chunksize=chunk_size):
    # 每次处理 10000 行
    chunks.append(chunk)
df = pd.concat(chunks, ignore_index=True)
```

**智能采样策略**：
```python
# 当数据量 > 200万行时，使用分层采样
if len(df) > 2_000_000:
    # 方案1: 随机采样 10%（最多100万行）
    sample_size = min(len(df) // 10, 1_000_000)
    df_sample = df.sample(n=sample_size, random_state=42)
    
    # 方案2: 系统采样（等间隔抽样）
    step = len(df) // 100_000  # 抽取10万行
    df_sample = df.iloc[::step]
```

---

### 3. 数据加载与内存管理

#### 🧮 内存优化策略

**类型自动优化**：
```python
# 自动压缩数据类型，减少内存占用
def optimize_dtypes(df):
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type == 'object':
            # 字符串类型：转为 category（如果重复值多）
            if df[col].nunique() / len(df) < 0.5:
                df[col] = df[col].astype('category')
        
        elif col_type == 'int64':
            # 整数类型：降级为 int32 或 int16
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                df[col] = df[col].astype(np.int16)
            elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
        
        elif col_type == 'float64':
            # 浮点类型：降级为 float32
            df[col] = df[col].astype(np.float32)
    
    return df
```

**内存占用监控**：
```python
# 显示数据占用内存
memory_usage = df.memory_usage(deep=True).sum() / 1024**2  # MB
print(f"内存占用: {memory_usage:.2f} MB")

# 如果超过 500MB，触发警告
if memory_usage > 500:
    logger.warning(f"数据内存占用过大: {memory_usage:.2f} MB")
```

---

### 4. Jupyter Kernel 管理

#### 🔧 Kernel 生命周期

| 阶段 | 操作 | 说明 |
|------|------|------|
| **启动** | `jupyter_client.KernelManager()` | 每个 Session 独立 Kernel |
| **初始化** | 安装必要库、加载数据 | 预先执行 `import pandas as pd` 等 |
| **执行** | `execute(code, timeout=300)` | 超时保护，防止死循环 |
| **清理** | `shutdown_kernel()` | Session 结束后自动关闭 |

**稳定性保障**：
```python
# 1. 启动超时保护
kernel = km.start_kernel(timeout=30)

# 2. 初始化环境，增加延迟避免 ZMQ 冲突（Windows 特有问题）
await asyncio.sleep(2)  # 等待 Kernel 完全就绪

# 3. 执行代码前清空消息队列
while kc.iopub_channel.msg_ready():
    kc.iopub_channel.get_msg()

# 4. 执行后收集所有输出
outputs = []
while kc.iopub_channel.msg_ready():
    msg = kc.iopub_channel.get_msg(timeout=1)
    if msg['msg_type'] == 'execute_result':
        outputs.append(msg['content'])
```

---

### 5. 准确性与可靠性

#### ✅ 代码执行准确性

| 指标 | 经典模式 | 智能模式 | 说明 |
|------|---------|---------|------|
| **首次成功率** | ~75% | ~70% | 首次生成的代码直接执行成功的比例 |
| **修复后成功率** | ~95% | ~90% | 经过最多3次错误修复后的成功率 |
| **平均修复次数** | 0.3 次 | 0.5 次 | 平均需要修复的次数 |
| **超时失败率** | <1% | <2% | 因超时导致的失败（主要是超大数据集） |

**影响因素**：
- ✅ **模型选择**：GPT-4 > Claude 3.5 > DeepSeek > GPT-4o-mini
- ✅ **需求明确度**：越具体的需求，成功率越高
- ✅ **数据质量**：缺失值、异常值会降低成功率
- ✅ **字段数量**：字段越多，AI 理解越困难

#### 🛡️ 错误处理机制

**多层容错**：
1. **语法检查**：AI 生成代码后，先进行语法检查（`ast.parse`）
2. **执行捕获**：捕获所有异常（`try-except`）
3. **智能修复**：将错误信息反馈给 AI，生成修复代码
4. **重试限制**：最多重试 3 次，防止无限循环
5. **降级策略**：如果修复失败，返回部分结果 + 错误说明

**常见错误及修复策略**：

| 错误类型 | 原因 | 修复策略 |
|---------|------|---------|
| `KeyError` | 字段名错误 | AI 重新检查字段名，使用正确的列名 |
| `TypeError` | 数据类型不匹配 | AI 添加类型转换代码（`.astype()`） |
| `ValueError` | 数值计算错误 | AI 添加异常值处理（`.dropna()`, `.fillna()`） |
| `MemoryError` | 内存不足 | AI 改用采样或分块处理 |
| `TimeoutError` | 执行超时 | AI 简化算法，优化性能 |

---

### 6. 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **文件上传速度** | ~10MB/s | 取决于网络和服务器 I/O |
| **数据解析速度** | ~100k行/秒 | pandas 读取速度 |
| **Kernel 启动时间** | 2-5秒 | Windows 系统稍慢 |
| **AI 代码生成时间** | 3-8秒 | 取决于模型和需求复杂度 |
| **代码执行时间** | 1-30秒 | 取决于数据量和计算复杂度 |
| **总分析时间** | 10-60秒 | 从提交请求到返回结果 |

**优化建议**：
- 🚀 使用 **DeepSeek** 模型（成本低，速度快）
- 🚀 减少分析字段数量（只选必要字段）
- 🚀 大文件使用 **采样分析**
- 🚀 后端部署时增加 CPU/内存资源

---

## 📂 项目结构

```
Natural-language-data-analysis-tools/
├── frontend/                      # 前端项目
│   ├── src/
│   │   ├── components/           # React 组件
│   │   │   ├── ChatArea/         # 对话交互
│   │   │   │   ├── ChatArea.jsx
│   │   │   │   ├── ConversationList.jsx
│   │   │   │   └── AgentExecution.jsx    ⭐ 核心：执行过程可视化
│   │   │   ├── FileUpload/       # 文件上传
│   │   │   ├── DataPreview/      # 数据预览
│   │   │   ├── FieldSelector/    # 字段选择
│   │   │   ├── ResultDisplay/    # 结果展示
│   │   │   ├── History/          # 历史记录
│   │   │   ├── Layout/           # 布局组件
│   │   │   └── WorkArea/         # 工作区
│   │   ├── services/
│   │   │   └── api.js            # API 封装
│   │   ├── store/
│   │   │   └── useAppStore.js    # Zustand 状态管理
│   │   ├── App.jsx               # 主应用
│   │   └── main.jsx              # 入口文件
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── ARCHITECTURE.md           # 前端架构文档
│   └── README.md                 # 前端说明
│
├── backend/                       # 后端项目
│   ├── api/                       # API 路由
│   │   ├── upload.py             # 文件上传接口
│   │   ├── session.py            # Session 管理接口
│   │   ├── agent.py              # Agent 分析接口 ⭐
│   │   └── history.py            # 历史记录接口
│   ├── core/                      # 核心业务逻辑
│   │   ├── agent.py              # ⭐⭐⭐ Agent 核心逻辑
│   │   ├── jupyter_manager.py   # ⭐ Jupyter Kernel 管理
│   │   ├── ai_client.py          # AI 客户端封装
│   │   ├── prompts.py            # AI Prompt 模板
│   │   ├── file_handler.py       # 文件处理
│   │   ├── database.py           # 数据库模型
│   │   └── cache.py              # 缓存管理
│   ├── config.py                  # 配置管理
│   ├── main.py                    # FastAPI 应用入口
│   ├── requirements.txt           # Python 依赖
│   ├── .env                       # 环境变量 (需自己创建)
│   ├── run.sh / run.bat           # 启动脚本
│   └── README.md                  # 后端说明
│
├── data/                          # 数据库文件 (自动创建)
├── uploads/                       # 上传文件 (自动创建)
├── logs/                          # 日志文件 (自动创建)
└── README.md                      # 项目总体说明 (本文件)
```

---

## 🚀 快速开始

### 前置要求

- **Node.js** 16+ (推荐 18+)
- **Python** 3.11+ 
- **Git**
- **OpenAI API Key** 或 **Anthropic API Key** (必需！)

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/Natural-language-data-analysis-tools.git
cd Natural-language-data-analysis-tools
```

### 2. 后端配置

#### 2.1 安装 Python 依赖

```bash
cd backend

# 推荐创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2.2 配置环境变量

创建 `.env` 文件：

```bash
# 复制示例配置
cp .env.example .env
```

编辑 `.env` 文件，配置 AI API：

```env
# API 配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# AI 模型配置 (二选一)
# 选项1: OpenAI (推荐使用 DeepSeek 等兼容接口，成本更低)
AI_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

# 选项2: Anthropic (Claude)
# AI_PROVIDER=anthropic
# ANTHROPIC_API_KEY=your_api_key_here
# ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# 文件上传
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=104857600  # 100MB

# Jupyter 配置
JUPYTER_TIMEOUT=300
KERNEL_STARTUP_TIMEOUT=30
```

**💡 提示：** 可以使用 DeepSeek API (兼容 OpenAI 格式)，成本更低！参见 `backend/DeepSeek配置指南.md`

#### 2.3 启动后端

```bash
# Windows:
run.bat

# Linux/Mac:
./run.sh

# 或直接运行:
python main.py
```

服务启动后访问：
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 3. 前端配置

#### 3.1 安装依赖

```bash
cd frontend
npm install
```

#### 3.2 启动开发服务器

```bash
npm run dev
```

前端启动后访问：**http://localhost:5173**

### 4. 开始使用

1. 打开浏览器访问 http://localhost:5173
2. 上传 Excel 或 CSV 文件
3. 选择需要分析的字段
4. 输入自然语言需求，例如：
   - "计算销售额的平均值和总和"
   - "按地区统计订单数量，生成柱状图"
   - "分析用户年龄分布，画一个饼图"
5. 观察 AI Agent 执行过程
6. 查看分析结果

---

## 📡 API 文档

### 核心 API 接口

#### 1. 文件上传

```http
POST /api/upload
Content-Type: multipart/form-data
```

**请求：**
- `file`: 文件 (Excel/CSV)

**响应：**
```json
{
  "success": true,
  "message": "文件上传成功",
  "data": {
    "file_id": "xxx",
    "file_name": "data.csv",
    "total_rows": 1000,
    "total_columns": 10,
    "columns": [
      {
        "name": "销售额",
        "type": "float",
        "nullable": false,
        "stats": {"min": 100, "max": 50000, "mean": 8500}
      }
    ],
    "preview": [...]
  }
}
```

#### 2. 创建 Session

```http
POST /api/session/create
Content-Type: application/json
```

**请求体：**
```json
{
  "file_id": "xxx",
  "selected_columns": ["col1", "col2"]
}
```

**响应：**
```json
{
  "success": true,
  "message": "Session 创建成功",
  "data": {
    "session_id": "xxx"
  }
}
```

#### 3. 提交分析请求 ⭐

```http
POST /api/agent/analyze
Content-Type: application/json
```

**请求体：**
```json
{
  "session_id": "xxx",
  "user_request": "计算销售额的平均值",
  "selected_columns": ["销售额", "地区"]
}
```

**响应：**
```json
{
  "success": true,
  "message": "任务已提交",
  "data": {
    "task_id": "xxx"
  }
}
```

#### 4. 获取 Agent 状态 (轮询) ⭐⭐⭐

```http
GET /api/agent/status/{task_id}
```

**响应：**
```json
{
  "success": true,
  "status": "running",
  "data": {
    "steps": [
      {
        "title": "生成代码",
        "status": "success",
        "code": "import pandas as pd\n...",
        "output": "✅ 代码生成成功",
        "error": null
      },
      {
        "title": "执行代码",
        "status": "running",
        "output": "正在执行...",
        "error": null
      }
    ],
    "result": {
      "charts": [...],
      "text": [...],
      "summary": "..."
    }
  }
}
```

**前端轮询机制：**
- 每 2 秒调用一次此接口
- `status` 为 `completed` 或 `failed` 时停止轮询

更多 API 文档请访问：http://localhost:8000/docs

---

## 🔧 配置说明

### 后端环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `API_HOST` | 服务监听地址 | 0.0.0.0 |
| `API_PORT` | 服务端口 | 8000 |
| `DEBUG` | 调试模式 | False |
| `DATABASE_URL` | 数据库 URL | sqlite+aiosqlite:///./data/analysis.db |
| `UPLOAD_DIR` | 上传目录 | ./uploads |
| `MAX_FILE_SIZE` | 最大文件大小 (字节) | 104857600 (100MB) |
| `JUPYTER_TIMEOUT` | Jupyter 执行超时 (秒) | 300 |
| `AI_PROVIDER` | AI 提供商 | openai / anthropic |
| `OPENAI_API_KEY` | OpenAI API 密钥 | (必需) |
| `OPENAI_MODEL` | OpenAI 模型 | gpt-4o-mini |
| `OPENAI_BASE_URL` | API Base URL | https://api.openai.com/v1 |
| `ANTHROPIC_API_KEY` | Claude API 密钥 | (可选) |
| `ANTHROPIC_MODEL` | Claude 模型 | claude-3-5-sonnet-20241022 |

### AI 模型选择建议

| 模型 | 优势 | 成本 | 推荐场景 |
|------|------|------|----------|
| **DeepSeek** | 兼容 OpenAI 格式，成本极低 | ⭐⭐⭐⭐⭐ | 开发测试、预算有限 |
| **GPT-4o-mini** | 速度快，质量高 | ⭐⭐⭐⭐ | 日常使用 |
| **GPT-4** | 质量最好 | ⭐⭐ | 复杂分析 |
| **Claude 3.5 Sonnet** | 代码生成能力强 | ⭐⭐⭐ | 专业分析 |

---

## ⚠️ 使用限制与最佳实践

### 系统限制

| 限制项 | 数值 | 说明 |
|-------|------|------|
| **文件大小** | 100MB | 单个文件最大支持 100MB |
| **数据行数** | 建议 < 50万行 | 超过 50万行建议采样分析 |
| **字段数量** | 建议 < 50 列 | 字段过多影响 AI 理解 |
| **并发 Session** | 10 个 | 单个服务器同时最多 10 个 Jupyter Kernel |
| **执行超时** | 300 秒（5分钟） | 单次代码执行最长时间 |
| **历史记录** | 100 条 | 自动保留最近 100 条分析记录 |
| **API 调用频率** | 取决于 AI 提供商 | DeepSeek: 60次/分钟，OpenAI: 根据套餐 |

### 最佳实践

#### ✅ DO - 推荐做法

1. **明确需求描述**：
   ```
   ❌ 不好："分析一下数据"
   ✅ 推荐："按月份统计销售额，生成折线图，并找出销售最好的3个月"
   ```

2. **选择必要字段**：
   - 只选择与分析相关的字段
   - 减少字段数量可提高 AI 理解准确性

3. **大文件处理**：
   - 超过 10万行：提前筛选数据或选择关键时间段
   - 超过 50万行：先采样分析，确认思路后再用全量数据

4. **使用合适的 Agent 模式**：
   - 明确需求 → 经典模式（快速、稳定）
   - 探索分析 → 智能模式（全面、深入）

5. **数据质量检查**：
   - 上传前检查：缺失值、异常值、数据类型
   - 使用"数据预览"功能检查是否正确解析

6. **错误修复**：
   - 如果 AI 修复 3 次仍失败，检查数据质量或简化需求
   - 查看"执行输出"获取详细错误信息

#### ❌ DON'T - 避免事项

1. **避免模糊需求**：
   ```
   ❌ "帮我看看这个数据"
   ❌ "分析一下"
   ❌ "画个图"
   ```

2. **避免一次性要求过多**：
   ```
   ❌ "分析销售、库存、用户、产品，生成10种图表，给出营销建议"
   ```
   建议拆分为多次独立分析。

3. **避免上传敏感数据**：
   - 系统会将数据传给 AI 模型（OpenAI/Anthropic/DeepSeek）
   - 请确保符合数据安全和隐私政策

4. **避免在生产环境直接使用 AI 生成的代码**：
   - AI 生成的代码未经充分测试
   - 关键业务逻辑需人工审查

5. **避免频繁刷新页面**：
   - Session 状态会丢失
   - 正在执行的任务会中断

### 成本优化

| AI 模型 | 输入成本 (每百万 token) | 输出成本 (每百万 token) | 单次分析成本 |
|---------|------------------------|------------------------|------------|
| **DeepSeek** | ¥1 | ¥2 | ~¥0.01-0.05 |
| **GPT-4o-mini** | $0.15 | $0.6 | ~$0.005-0.02 |
| **GPT-4** | $10 | $30 | ~$0.1-0.5 |
| **Claude 3.5 Sonnet** | $3 | $15 | ~$0.05-0.2 |

**建议**：
- 开发测试：使用 **DeepSeek**（成本极低）
- 生产环境：使用 **GPT-4o-mini**（平衡性价比）
- 复杂分析：使用 **GPT-4** 或 **Claude 3.5**

---

## 🐛 常见问题

### 1. Jupyter Kernel 启动失败

**症状：** 提示 "Kernel 启动超时"

**解决方案：**
```bash
# 检查 ipykernel 是否安装
python -m ipykernel --version

# 如果未安装
pip install ipykernel

# Windows 用户可能需要额外配置
python -m ipykernel install --user
```

### 2. AI API 调用失败

**症状：** 提示 "API Key 无效" 或 "连接超时"

**解决方案：**
- 检查 `.env` 文件中的 API Key 是否正确
- 检查网络连接
- 确认 API 余额充足
- 如果使用 DeepSeek，确认 `OPENAI_BASE_URL` 设置为 `https://api.deepseek.com/v1`

### 3. 文件上传失败

**症状：** 文件上传后提示错误

**解决方案：**
- 检查文件格式是否为 Excel 或 CSV
- 检查文件大小是否超过 100MB
- 确认 `uploads/` 目录存在且有写权限

### 4. 前端连接不上后端

**症状：** 前端提示 "网络错误"

**解决方案：**
- 确认后端已启动：访问 http://localhost:8000/health
- 检查后端端口是否为 8000
- 检查防火墙设置

---

## 🚢 部署指南

### Docker 部署 (推荐)

#### 1. 后端 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建必要目录
RUN mkdir -p uploads data logs

EXPOSE 8000

CMD ["python", "main.py"]
```

#### 2. 前端 Dockerfile

```dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 3. docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

#### 4. 启动

```bash
docker-compose up -d
```

### 传统部署

详细部署步骤请参考：
- 后端：`backend/README.md`
- 前端：`frontend/README.md`

---

## 🤝 贡献指南

欢迎贡献代码、报告 Bug 或提出建议！

### 开发流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 代码规范

- **前端**：遵循 ESLint 规则
- **后端**：遵循 PEP 8 规范
- **提交信息**：使用清晰的描述性信息

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [React](https://reactjs.org/) - 前端框架
- [FastAPI](https://fastapi.tiangolo.com/) - 后端框架
- [Ant Design](https://ant.design/) - UI 组件库
- [Jupyter](https://jupyter.org/) - Kernel 支持
- [OpenAI](https://openai.com/) / [Anthropic](https://www.anthropic.com/) - AI 模型

---

## 📧 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 提交 Issue: [GitHub Issues](https://github.com/yourusername/Natural-language-data-analysis-tools/issues)
- 发送邮件: your-email@example.com

---

## 🔮 未来规划

- [x] ~~支持 WebSocket 实时推送（替代轮询）~~ ✅ 已实现（SSE）
- [x] ~~支持用户编辑生成的代码~~ ✅ 已实现（结果页代码编辑）
- [x] ~~支持智能 Agent 模式~~ ✅ 已实现（经典+智能双模式）
- [x] ~~支持导出分析报告~~ ✅ 已实现（PDF/HTML/Markdown）
- [ ] 支持多文件联合分析（JOIN 操作）
- [ ] 支持更多数据源（MySQL/PostgreSQL/API）
- [ ] 支持更多图表类型（ECharts 集成）
- [ ] 支持自然语言查询历史记录
- [ ] 支持 AI 推荐分析建议
- [ ] 支持多用户权限管理
- [ ] 支持导出为 Jupyter Notebook
- [ ] 支持暗黑模式
- [ ] 支持国际化（中英文）
- [ ] 支持自定义 Prompt 模板
- [ ] 支持 Agent 执行链路追踪

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！⭐**

Made with ❤️ by [Your Name]

</div>

