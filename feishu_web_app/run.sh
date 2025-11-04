#!/bin/bash

# 飞书网页应用启动脚本（Linux/Mac）

echo "========================================"
echo "飞书网页应用启动脚本"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未检测到 Python3，请先安装 Python 3.7+"
    exit 1
fi

echo "✓ Python 已安装: $(python3 --version)"
echo ""

# 检查是否存在虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 正在创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 创建虚拟环境失败"
        exit 1
    fi
    echo "✓ 虚拟环境创建成功"
    echo ""
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ 激活虚拟环境失败"
    exit 1
fi
echo "✓ 虚拟环境已激活"
echo ""

# 安装依赖
echo "📦 安装依赖包..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 安装依赖失败"
    exit 1
fi
echo "✓ 依赖安装完成"
echo ""

# 检查 .env 配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: 未找到 .env 配置文件"
    echo "正在从 .env.example 复制..."
    cp .env.example .env
    echo "✓ 已创建 .env 文件"
    echo "📝 请编辑 .env 文件填入真实的 APP_ID 和 APP_SECRET"
    echo ""
    read -p "按回车键继续..."
fi

echo "========================================"
echo "🚀 启动飞书网页应用服务..."
echo "========================================"
echo ""
echo "访问地址: http://127.0.0.1:3000"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动服务
python server.py


