@echo off
chcp 65001 >nul
echo ========================================
echo 🔧 环境配置助手
echo ========================================
echo.

REM 检查是否已有 .env 文件
if exist ".env" (
    echo ⚠️  检测到已存在 .env 文件
    echo.
    choice /C YN /M "是否覆盖现有配置？"
    if errorlevel 2 (
        echo ❌ 已取消配置
        pause
        exit /b 1
    )
)

echo 📝 正在创建 .env 配置文件...
echo.

REM 创建 .env 文件
(
echo # ========================================
echo # 智能数据分析工具 - 环境变量配置
echo # ========================================
echo.
echo # ==================== API 服务配置 ====================
echo API_HOST=0.0.0.0
echo API_PORT=8000
echo DEBUG=True
echo.
echo # ==================== AI 模型配置 ====================
echo AI_PROVIDER=openai
echo.
echo # 🔑 请替换为你的 DeepSeek API Key！
echo # 获取方式：访问 https://platform.deepseek.com/ 注册并获取
echo OPENAI_API_KEY=your-api-key-here
echo OPENAI_BASE_URL=https://api.deepseek.com/v1
echo OPENAI_MODEL=deepseek-chat
echo.
echo # ==================== 数据库配置 ====================
echo DATABASE_URL=sqlite+aiosqlite:///./data/analysis.db
echo.
echo # ==================== 文件上传配置 ====================
echo UPLOAD_DIR=./uploads
echo MAX_FILE_SIZE=104857600
echo.
echo # ==================== Jupyter 配置 ====================
echo JUPYTER_TIMEOUT=300
echo KERNEL_STARTUP_TIMEOUT=30
echo.
echo # ==================== 代码执行安全配置 ====================
echo ENABLE_CODE_SANDBOX=False
) > .env

echo ✅ 配置文件已创建: .env
echo.
echo ========================================
echo 📋 接下来的步骤：
echo ========================================
echo.
echo 1. 访问 DeepSeek 官网获取 API Key：
echo    https://platform.deepseek.com/
echo.
echo 2. 注册/登录账号
echo.
echo 3. 进入 API Keys 页面，创建新的 API Key
echo.
echo 4. 复制 API Key（格式：sk-xxxxxxxx）
echo.
echo 5. 编辑 .env 文件，替换 "your-api-key-here"
echo    使用记事本打开：notepad .env
echo.
echo ========================================
echo.
choice /C YN /M "是否现在打开 .env 文件进行编辑？"
if errorlevel 2 (
    echo.
    echo 💡 你也可以稍后手动编辑 .env 文件
    echo    命令：notepad .env
    pause
    exit /b 0
)

notepad .env
echo.
echo ✅ 配置完成！
echo 💡 保存文件后，运行 python main.py 启动服务
echo.
pause

