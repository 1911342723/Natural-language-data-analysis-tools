# DeepSeek 流式配置指南

## ✅ 我们的代码已支持 DeepSeek 流式调用

DeepSeek 使用 OpenAI 兼容的 API，所以我们的代码**无需修改**即可使用 DeepSeek！

## 📝 配置步骤

### 1. 创建 `.env` 文件

在 `backend` 目录下创建 `.env` 文件（如果没有的话）：

```bash
# backend/.env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxx  # 你的 DeepSeek API Key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

### 2. 获取 DeepSeek API Key

1. 访问 [DeepSeek 官网](https://platform.deepseek.com/)
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的 API Key
5. 复制 API Key（格式：`sk-xxxxxxxxxxxxxxxx`）

### 3. 完整的 .env 配置示例

```bash
# API 服务配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# AI 模型配置（DeepSeek）
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-deepseek-api-key-here
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

# 数据库
DATABASE_URL=sqlite+aiosqlite:///./data/analysis.db

# 文件上传
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=104857600

# Jupyter 配置
JUPYTER_TIMEOUT=300
KERNEL_STARTUP_TIMEOUT=30

# 代码执行安全
ENABLE_CODE_SANDBOX=False
```

## 🚀 启动服务

配置完成后，重启后端：

```bash
cd backend
python main.py
```

你应该会看到：

```
🚀 启动数据分析工具后端...
✅ 使用 AI 提供商: openai
✅ 使用 AI 模型: deepseek-chat
✅ API Base URL: https://api.deepseek.com/v1
✅ 数据库初始化完成
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## ⚡ 流式调用已优化

我们已经对流式调用进行了以下优化：

### 后端优化

1. **`backend/core/ai_client.py`**
   - ✅ 使用 OpenAI SDK 的 `stream=True` 参数
   - ✅ 逐个 token 返回内容：`yield chunk.choices[0].delta.content`
   - ✅ 支持 DeepSeek 的 OpenAI 兼容 API

2. **`backend/core/agent.py`**
   - ✅ 每 2 个 token 更新一次 UI（频率提高）
   - ✅ 内容增加超过 20 字符就更新
   - ✅ 每次更新后 `await asyncio.sleep(0.05)` 让出控制权
   - ✅ 降低 temperature 到 0.1（更精确，减少随机性）

3. **`backend/api/agent.py`**
   - ✅ SSE 轮询间隔从 0.1 秒优化到 0.03 秒（30ms）
   - ✅ 检测步骤输出的细微变化并实时推送

### Prompt 优化

1. **严格遵循用户需求**
   - ✅ 添加"不要画多余的图，不要做多余的分析"
   - ✅ 用户要求画什么就画什么
   - ✅ 保持简洁，避免过度分析

2. **降低 AI 创造性**
   - ✅ temperature 从 0.3 降低到 0.1
   - ✅ 更准确地理解用户意图

## 🔍 验证流式效果

### 在后端终端看到的输出

当 AI 生成代码时，你应该看到：

```
🤖 [AI 流式生成开始]
📤 收到 chunk: import
📤 收到 chunk:  pandas
📤 收到 chunk:  as
📤 收到 chunk:  pd
...
🤖 [AI 响应完成] 总长度: 456 字符
```

### 在前端看到的效果

- ✅ "AI 正在思考..." → "AI 正在生成代码..."
- ✅ 代码一点一点地出现（打字机效果）
- ✅ 实时显示已生成的字符数

## 📊 DeepSeek 流式调用的特点

1. **速度非常快** - DeepSeek 生成速度很快，流式效果可能不如 GPT-4 明显
2. **稳定性高** - 流式连接很稳定，几乎不会中断
3. **成本低** - DeepSeek 的 API 价格非常实惠

## ⚠️ 常见问题

### 1. 流式效果不明显？

**原因**：DeepSeek 生成速度太快（每秒可能生成 100+ tokens）

**解决方案**：
- 我们已经优化了更新频率（每 2 个 token）
- 添加了 50ms 的延迟让前端有时间渲染
- 如果还是太快，可以尝试使用更长的提示词

### 2. API Key 无效？

**检查**：
- ✅ API Key 格式正确（`sk-` 开头）
- ✅ API Key 未过期
- ✅ 账户有足够的余额
- ✅ `OPENAI_BASE_URL` 设置为 DeepSeek 的地址

### 3. 连接超时？

**检查**：
- ✅ 网络连接正常
- ✅ 可以访问 `https://api.deepseek.com`
- ✅ 防火墙没有阻止请求

## 🎯 推荐配置

对于最佳的流式体验：

```bash
# .env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat  # 推荐使用 deepseek-chat
```

## 📚 更多资源

- [DeepSeek 官方文档](https://platform.deepseek.com/docs)
- [DeepSeek API 参考](https://platform.deepseek.com/api-docs/)
- [OpenAI SDK 文档](https://github.com/openai/openai-python)

## 🎉 现在就试试吧！

配置完成后：
1. 重启后端
2. 刷新前端
3. 上传数据并提问
4. 观察流式生成效果！

你会看到 AI 像"打字"一样逐字生成代码，就像真人在写代码一样！✨

