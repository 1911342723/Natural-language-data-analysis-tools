# 🔑 API 密钥配置指南

## 快速配置（推荐）⭐

### Windows 用户

在 `backend` 目录下运行配置助手：

```bash
cd backend
setup_env.bat
```

这个脚本会：
1. ✅ 自动创建 `.env` 配置文件
2. ✅ 打开记事本让你编辑
3. ✅ 提供详细的配置说明

---

## 手动配置步骤

### 第 1 步：创建 .env 文件

在 `backend` 目录下创建一个名为 `.env` 的文件（注意：文件名就是 `.env`，没有其他后缀）

**Windows 创建方法：**

```powershell
cd backend
notepad .env
# 在弹出的记事本中粘贴下面的配置内容，然后保存
```

**或者在文件资源管理器中：**
1. 打开 `backend` 文件夹
2. 右键 → 新建 → 文本文档
3. 重命名为 `.env`（删除 `.txt` 后缀）

---

### 第 2 步：填写配置内容

将以下内容粘贴到 `.env` 文件中：

```env
# ========================================
# 智能数据分析工具 - 环境变量配置
# ========================================

# ==================== API 服务配置 ====================
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# ==================== AI 模型配置 ====================
AI_PROVIDER=openai

# 🔑 请替换为你的 DeepSeek API Key！
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

# ==================== 数据库配置 ====================
DATABASE_URL=sqlite+aiosqlite:///./data/analysis.db

# ==================== 文件上传配置 ====================
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=104857600

# ==================== Jupyter 配置 ====================
JUPYTER_TIMEOUT=300
KERNEL_STARTUP_TIMEOUT=30

# ==================== 代码执行安全配置 ====================
ENABLE_CODE_SANDBOX=False
```

---

### 第 3 步：获取 DeepSeek API Key（推荐）⭐

DeepSeek 成本低、速度快，兼容 OpenAI 格式！

#### 3.1 注册 DeepSeek 账号

1. 访问：**https://platform.deepseek.com/**
2. 点击右上角"注册"或"登录"
3. 使用邮箱或手机号注册

#### 3.2 获取 API Key

1. 登录后，进入控制台
2. 左侧菜单找到 **"API Keys"**
3. 点击 **"创建 API Key"**
4. 给 Key 起个名字（如：`数据分析工具`）
5. 点击创建，**立即复制 API Key**（格式：`sk-xxxxxxxxxxxxxxxx`）

⚠️ **重要**：API Key 只显示一次，请妥善保存！

#### 3.3 充值（可选）

DeepSeek 可能需要充值才能使用：
- 最低充值：¥1 元
- 推荐充值：¥10-50 元（够用很久）
- 价格：约 ¥0.001 / 1K tokens（非常便宜）

#### 3.4 配置 API Key

编辑 `.env` 文件，将 `your-api-key-here` 替换为你的 API Key：

```env
OPENAI_API_KEY=sk-abcdef1234567890abcdef1234567890
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

**保存文件！**

---

## 其他 AI 提供商配置

### 选项 2：使用 OpenAI（GPT-4/GPT-3.5）

如果你有 OpenAI 账号：

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

**获取 OpenAI API Key：**
1. 访问：https://platform.openai.com/
2. 注册/登录
3. 进入 API Keys 页面
4. 创建新的 API Key

**注意**：OpenAI 需要国际信用卡充值，且价格较高。

---

### 选项 3：使用 Anthropic Claude

如果你想使用 Claude：

```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

**获取 Claude API Key：**
1. 访问：https://www.anthropic.com/
2. 注册/登录
3. 进入 API Keys 页面
4. 创建新的 API Key

---

## 第 4 步：验证配置

### 4.1 启动后端

```bash
cd backend
python main.py
```

### 4.2 检查输出

如果配置正确，你会看到：

```
============================================================
🚀 智能数据分析工具后端启动中...
============================================================
✅ AI 提供商: openai
✅ AI 模型: deepseek-chat
✅ API Base URL: https://api.deepseek.com/v1
✅ API Key: sk-abcdef12...   ← 显示了你的 API Key 前缀
✅ 上传目录: ./uploads
✅ 数据库: sqlite+aiosqlite:///./data/analysis.db
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

如果看到 **❌ 未设置 API Key**，说明配置有问题。

---

## 常见问题排查

### ❌ 问题 1：仍然显示"未设置 API Key"

**原因**：
- `.env` 文件位置错误（应该在 `backend` 目录下）
- `.env` 文件名错误（必须是 `.env`，不能有其他后缀）
- 配置内容有误（有多余空格、引号等）

**解决方案**：

1. 确认文件位置：
```bash
cd backend
dir .env  # 应该能看到 .env 文件
```

2. 检查文件内容：
```bash
type .env  # 查看文件内容
```

3. 确认配置格式：
```env
# ✅ 正确格式
OPENAI_API_KEY=sk-abc123456789

# ❌ 错误格式（不要加引号）
OPENAI_API_KEY="sk-abc123456789"

# ❌ 错误格式（等号两边不要有空格）
OPENAI_API_KEY = sk-abc123456789
```

---

### ❌ 问题 2：API Key 无效

启动后提示 `Invalid API Key` 或 `401 Unauthorized`

**解决方案**：

1. 检查 API Key 格式：
   - DeepSeek: `sk-` 开头，约 48 个字符
   - OpenAI: `sk-` 开头
   - Claude: `sk-ant-` 开头

2. 检查 API Key 是否过期

3. 检查账户余额是否充足

4. 重新生成 API Key

---

### ❌ 问题 3：连接超时

启动后提示连接 API 失败

**解决方案**：

1. 检查网络连接

2. 检查 `OPENAI_BASE_URL` 配置是否正确：
   - DeepSeek: `https://api.deepseek.com/v1`
   - OpenAI: `https://api.openai.com/v1`

3. 尝试在浏览器访问该 URL（去掉 `/v1`）

4. 检查防火墙设置

---

### ❌ 问题 4：Windows 无法创建 .env 文件

**解决方案**：

使用命令行创建：

```powershell
cd backend
echo. > .env
notepad .env
```

然后粘贴配置内容并保存。

---

## 完整配置示例

### DeepSeek 配置（推荐）⭐

```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

AI_PROVIDER=openai
OPENAI_API_KEY=sk-1234567890abcdef1234567890abcdef1234567890ab
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

DATABASE_URL=sqlite+aiosqlite:///./data/analysis.db
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=104857600
JUPYTER_TIMEOUT=300
KERNEL_STARTUP_TIMEOUT=30
ENABLE_CODE_SANDBOX=False
```

---

## 下一步

配置完成后：

1. ✅ 启动后端：`python main.py`
2. ✅ 启动前端：`cd frontend && npm run dev`
3. ✅ 打开浏览器：http://localhost:5173
4. ✅ 上传数据文件，开始分析！

---

## 需要帮助？

如果还有问题：

1. 查看完整错误日志
2. 检查 `backend/logs/` 目录下的日志文件
3. 运行测试脚本：`python test_config.py`

---

**祝使用愉快！🎉**

