@echo off
chcp 65001 >nul
echo ========================================
echo 数据分析工具启动脚本（已集成飞书登录）
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Python
    pause
    exit /b 1
)

echo ✓ Python 已安装
echo.

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 🔄 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装/更新依赖
echo 📦 检查依赖...
pip install -r requirements.txt --quiet

REM 检查环境配置
if not exist ".env" (
    echo ⚠️  未找到 .env 文件
    if exist ".env.example" (
        echo 正在复制 .env.example 到 .env...
        copy .env.example .env >nul
        echo.
        echo ❗ 请编辑 .env 文件，配置以下信息：
        echo    1. OPENAI_API_KEY 或 ANTHROPIC_API_KEY
        echo    2. FEISHU_APP_ID 和 FEISHU_APP_SECRET（已填好）
        echo    3. SESSION_SECRET_KEY（运行生成命令）
        echo.
        echo 生成 SESSION_SECRET_KEY:
        python -c "import secrets; print('SESSION_SECRET_KEY=' + secrets.token_hex(32))"
        echo.
        pause
    )
)

echo.
echo ========================================
echo 🚀 启动数据分析工具（已集成飞书登录）
echo ========================================
echo.
echo 📝 后端地址: http://localhost:8000
echo 📚 API 文档: http://localhost:8000/docs
echo 👥 支持多用户飞书登录
echo 💾 数据持久化保存
echo.
echo 按 Ctrl+C 停止服务
echo.

REM 启动服务
python main.py

pause


