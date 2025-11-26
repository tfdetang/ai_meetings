#!/bin/bash

# AI Agent Meeting System - Web 依赖安装脚本

echo "🔧 安装 AI 代理会议系统 Web 依赖"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请先安装: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js 版本: $(node --version)"
echo "✅ npm 版本: $(npm --version)"
echo ""

# 安装后端依赖
echo "📦 安装后端依赖..."
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -e . > /dev/null 2>&1
pip install -r requirements-web.txt > /dev/null 2>&1
echo "✅ 后端依赖安装完成"
echo ""

# 安装前端依赖
echo "📦 安装前端依赖..."
cd web-frontend

if [ -f "package-lock.json" ]; then
    echo "检测到 package-lock.json，使用 npm ci..."
    npm ci
else
    echo "使用 npm install..."
    npm install
fi

if [ $? -eq 0 ]; then
    echo "✅ 前端依赖安装完成"
else
    echo "❌ 前端依赖安装失败"
    exit 1
fi

cd ..
echo ""

echo "🎉 所有依赖安装完成！"
echo ""
echo "📍 下一步："
echo "   运行 ./start_web.sh 启动服务"
echo "   或查看 QUICK_START.md 了解更多"
