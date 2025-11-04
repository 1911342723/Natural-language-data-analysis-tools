@echo off
chcp 65001 >nul
echo ========================================
echo 飞书网页应用启动脚本
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未检测到 Python，请先安装 Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✓ Python 已安装
echo.

REM 检查是否存在虚拟环境
if not exist "venv" (
    echo 📦 正在创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo ✓ 虚拟环境创建成功
    echo.
)

REM 激活虚拟环境
echo 🔄 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 激活虚拟环境失败
    pause
    exit /b 1
)
echo ✓ 虚拟环境已激活
echo.

REM 安装依赖
echo 📦 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 安装依赖失败
    pause
    exit /b 1
)
echo ✓ 依赖安装完成
echo.

REM 检查 .env 配置文件
if not exist ".env" (
    echo ⚠️  警告: 未找到 .env 配置文件
    echo 正在从 .env.example 复制...
    copy .env.example .env >nul
    echo ✓ 已创建 .env 文件，请编辑此文件填入真实的 APP_ID 和 APP_SECRET
    echo.
    echo 按任意键打开配置文件...
    pause >nul
    notepad .env
    echo.
)

echo ========================================
echo 🚀 启动飞书网页应用服务...
echo ========================================
echo.
echo 访问地址: http://127.0.0.1:3000
echo 按 Ctrl+C 停止服务
echo.

REM 启动服务
python server.py

pause


