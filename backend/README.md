# 智能数据分析工具 - 后端

基于 FastAPI + Jupyter Kernel 的智能数据分析后端服务。

## ✨ 核心特性

### 1. Jupyter Kernel 集成 ⭐⭐⭐
- 为每个用户创建独立的 Jupyter Kernel Session
- 支持实时代码执行和输出捕获
- 自动管理 Kernel 生命周期

### 2. AI Agent 智能分析 ⭐⭐⭐
- 自然语言理解用户需求
- 自动生成 Python 分析代码
- 执行代码并捕获输出
- 错误检测和自动修复（最多3次重试）
- AI 总结分析结果

### 3. 文件处理
- 支持 Excel (.xlsx, .xls) 和 CSV 文件
- 自动解析数据类型和统计信息
- 提取字段元数据

### 4. 数据持久化
- SQLite/PostgreSQL 数据库
- 历史记录存储

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

推荐使用虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# API配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# AI模型配置（必需！）
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# 或使用 Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here
AI_PROVIDER=anthropic
```

**⚠️ 重要：** 必须配置 AI API 密钥才能使用代码生成功能！

### 3. 启动服务

```bash
python main.py
```

服务启动后访问：
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

---

## 📂 项目结构

```
backend/
├── main.py                     # FastAPI 应用入口
├── config.py                   # 配置管理
├── requirements.txt            # 依赖列表
├── .env                        # 环境变量（需自己创建）
├── .gitignore                  # Git 忽略文件
├── api/                        # API 路由层
│   ├── __init__.py
│   ├── upload.py               # 文件上传
│   ├── session.py              # Session 管理
│   ├── agent.py                # Agent 分析
│   └── history.py              # 历史记录
├── core/                       # 核心业务逻辑
│   ├── __init__.py
│   ├── database.py             # 数据库模型
│   ├── jupyter_manager.py     # Jupyter Kernel 管理 ⭐
│   ├── agent.py                # Agent 核心逻辑 ⭐⭐⭐
│   ├── ai_client.py            # AI 客户端封装
│   ├── prompts.py              # AI Prompt 模板
│   └── file_handler.py         # 文件处理
├── data/                       # 数据库文件（自动创建）
├── uploads/                    # 上传文件（自动创建）
└── logs/                       # 日志文件（自动创建）
```

---

## 🔧 核心模块详解

### 1. Jupyter Manager (`core/jupyter_manager.py`) ⭐

**功能：**
- 创建和管理 Jupyter Kernel Session
- 执行 Python 代码并捕获输出
- 支持多用户并发

**关键方法：**

```python
# 创建 Session
session_id = await jupyter_manager.create_session(data_json)

# 获取 Session
session = jupyter_manager.get_session(session_id)

# 执行代码
result = await session.execute_code(code, timeout=60)

# 结果格式
{
    'stdout': [],      # 标准输出
    'stderr': [],      # 错误输出
    'data': [],        # 数据输出（图表、DataFrame）
    'error': None,     # 异常信息
}

# 关闭 Session
await jupyter_manager.close_session(session_id)
```

### 2. Analysis Agent (`core/agent.py`) ⭐⭐⭐

**Agent 执行流程：**

```
用户需求
  ↓
步骤1：生成代码（AI）
  ↓
步骤2：执行代码（Jupyter Kernel）
  ↓
判断：成功？
  ├─ 是 → 步骤3：提取结果 → 步骤4：生成总结 → 完成 ✅
  └─ 否 → 步骤3：分析错误 + 修复代码 → 返回步骤2（最多3次）
```

**关键类：**

```python
# 创建 Agent
agent = AnalysisAgent(
    session_id=session_id,
    user_request="计算销售额平均值",
    selected_columns=["销售额", "地区"],
    data_schema=data_schema
)

# 运行 Agent
result = await agent.run()

# 结果格式
{
    "status": "completed",  # running | completed | failed
    "data": {
        "steps": [
            {
                "title": "生成代码",
                "status": "success",
                "code": "...",
                "output": "...",
                "error": None
            },
            ...
        ],
        "result": {
            "chart_base64": "...",
            "summary": "..."
        }
    }
}
```

### 3. AI Client (`core/ai_client.py`)

**支持的 AI 提供商：**
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)

**使用方法：**

```python
from core.ai_client import ai_client

# 调用 AI
messages = [
    {"role": "system", "content": "你是数据分析助手"},
    {"role": "user", "content": "生成代码..."}
]

response = ai_client.chat(messages, temperature=0.3)
```

### 4. File Handler (`core/file_handler.py`)

**功能：**
- 文件上传和保存
- 数据解析（Excel/CSV）
- 提取元数据和统计信息

**使用方法：**

```python
from core.file_handler import file_handler

# 解析文件
file_info = file_handler.parse_file(file_id, filename)

# 返回信息
{
    'file_id': 'xxx',
    'total_rows': 1000,
    'total_columns': 10,
    'columns': [
        {
            'name': '销售额',
            'type': 'float',
            'nullable': False,
            'stats': {'min': 100, 'max': 50000, 'mean': 8500}
        },
        ...
    ],
    'preview': [...],  # 前100行
    'data_json': '...'  # 完整数据JSON
}
```

---

## 📡 API 接口文档

### 1. 文件上传

```http
POST /api/upload
Content-Type: multipart/form-data

Body: file=<binary>

Response:
{
    "success": true,
    "message": "文件上传成功",
    "data": {
        "file_id": "xxx",
        "file_name": "data.csv",
        "total_rows": 1000,
        "total_columns": 10,
        "columns": [...],
        "preview": [...]
    }
}
```

### 2. 创建 Session

```http
POST /api/session/create
Content-Type: application/json

Body:
{
    "file_id": "xxx",
    "selected_columns": ["col1", "col2"]
}

Response:
{
    "success": true,
    "message": "Session 创建成功",
    "data": {
        "session_id": "xxx"
    }
}
```

### 3. 提交分析请求 ⭐

```http
POST /api/agent/analyze
Content-Type: application/json

Body:
{
    "session_id": "xxx",
    "user_request": "计算销售额的平均值和总和",
    "selected_columns": ["销售额", "地区"]
}

Response:
{
    "success": true,
    "message": "任务已提交",
    "data": {
        "task_id": "xxx"
    }
}
```

### 4. 获取 Agent 状态（轮询）⭐⭐⭐

```http
GET /api/agent/status/{task_id}

Response:
{
    "success": true,
    "status": "running",  # running | completed | failed
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
            "chart_base64": "...",
            "summary": "..."
        }
    }
}
```

**前端轮询机制：**
- 每 2 秒调用一次此接口
- 根据 `status` 判断是否继续轮询
- `completed` 或 `failed` 时停止

### 5. 历史记录

```http
# 获取列表
GET /api/history/list?page=1&page_size=20

# 获取详情
GET /api/history/{id}

# 删除记录
DELETE /api/history/{id}
```

---

## 🔑 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `API_HOST` | 服务监听地址 | 0.0.0.0 |
| `API_PORT` | 服务端口 | 8000 |
| `DEBUG` | 调试模式 | False |
| `DATABASE_URL` | 数据库 URL | sqlite+aiosqlite:///./data/analysis.db |
| `UPLOAD_DIR` | 上传目录 | ./uploads |
| `MAX_FILE_SIZE` | 最大文件大小 | 104857600 (100MB) |
| `JUPYTER_TIMEOUT` | Jupyter 执行超时 | 300 (5分钟) |
| `OPENAI_API_KEY` | OpenAI API 密钥 | (必需) |
| `OPENAI_MODEL` | OpenAI 模型 | gpt-4o-mini |
| `ANTHROPIC_API_KEY` | Claude API 密钥 | (可选) |
| `AI_PROVIDER` | AI 提供商 | openai |

---

## 🐛 调试技巧

### 1. 查看日志

后端会输出详细日志：

```
🚀 启动数据分析工具后端...
✅ 数据库初始化完成
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. 测试 API

使用 API 文档测试：

```
http://localhost:8000/docs
```

### 3. 数据库查看

SQLite 数据库位于 `./data/analysis.db`

可以使用工具查看：
- DB Browser for SQLite
- DBeaver

### 4. Jupyter Kernel 调试

如果 Kernel 启动失败，检查：
- Python 环境是否正确
- jupyter-client 是否安装
- ipykernel 是否安装

手动测试：

```bash
python -m ipykernel --version
```

---

## 🚀 部署建议

### 1. 使用 Docker

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

构建并运行：

```bash
docker build -t data-analysis-backend .
docker run -p 8000:8000 --env-file .env data-analysis-backend
```

### 2. 使用 Supervisor

```ini
[program:data-analysis-backend]
directory=/path/to/backend
command=/path/to/venv/bin/python main.py
autostart=true
autorestart=true
stderr_logfile=/var/log/data-analysis-backend.err.log
stdout_logfile=/var/log/data-analysis-backend.out.log
```

### 3. 使用 systemd

```ini
[Unit]
Description=Data Analysis Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## ⚠️ 注意事项

### 1. 安全性
- ⚠️ 当前代码执行未完全沙箱化
- 生产环境建议使用 Docker 隔离
- 限制用户上传文件大小
- 定期清理过期 Session

### 2. 性能
- Session 会占用内存，定期清理
- 大文件处理可能较慢
- AI API 调用有延迟

### 3. 依赖
- 需要 Python 3.11+
- 需要 AI API 密钥
- Jupyter Kernel 启动需要时间

---

## 📚 参考资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Jupyter Client 文档](https://jupyter-client.readthedocs.io/)
- [OpenAI API 文档](https://platform.openai.com/docs/api-reference)
- [Anthropic API 文档](https://docs.anthropic.com/)

---

**作者**: AI Assistant  
**创建日期**: 2025-10-30  
**版本**: v1.0.0  
**状态**: ✅ 核心功能已完成


