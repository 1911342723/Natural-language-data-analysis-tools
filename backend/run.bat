@echo off
REM 启动脚本（Windows）

echo 🚀 启动数据分析工具后端...

REM 检查虚拟环境
if not exist "venv" (
    echo ⚠️  未找到虚拟环境，正在创建...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
if not exist ".deps_installed" (
    echo 📦 安装依赖...
    pip install -r requirements.txt
    echo. > .deps_installed
)

REM 检查 .env 文件
if not exist ".env" (
    echo ⚠️  未找到 .env 文件，正在复制示例...
    copy .env.example .env
    echo ❗ 请编辑 .env 文件配置 API 密钥！
    pause
    exit /b 1
)

REM 启动服务
echo ✅ 启动服务...
python main.py
pause


