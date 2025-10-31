#!/bin/bash
# 启动脚本（Linux/Mac）

echo "🚀 启动数据分析工具后端..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "⚠️  未找到虚拟环境，正在创建..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
if [ ! -f ".deps_installed" ]; then
    echo "📦 安装依赖..."
    pip install -r requirements.txt
    touch .deps_installed
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，正在复制示例..."
    cp .env.example .env
    echo "❗ 请编辑 .env 文件配置 API 密钥！"
    exit 1
fi

# 启动服务
echo "✅ 启动服务..."
python main.py


