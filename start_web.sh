#!/bin/bash

# AI Agent Meeting System - Web Interface Startup Script

echo "🚀 启动 AI 代理会议系统 Web 界面"
echo ""

# Check if Python virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ 未找到虚拟环境，请先运行: python -m venv .venv && source .venv/bin/activate && pip install -e ."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if FastAPI dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 安装 Web 依赖..."
    pip install fastapi uvicorn websockets
fi

# Start backend API
echo "🔧 启动后端 API (端口 8888)..."
cd "$(dirname "$0")"
python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8888 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请先安装: https://nodejs.org/"
    kill $BACKEND_PID
    exit 1
fi

# Install frontend dependencies if needed
if [ ! -d "web-frontend/node_modules" ]; then
    echo "📦 安装前端依赖..."
    cd web-frontend
    npm install
    cd ..
fi

# Start frontend
echo "🎨 启动前端界面 (端口 5173)..."
cd web-frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 启动完成！"
echo ""
echo "📍 访问地址："
echo "   前端界面: http://localhost:5173"
echo "   API 文档: http://localhost:8888/docs"
echo ""
echo "按 Ctrl+C 停止服务"

# Wait for user interrupt
trap "echo ''; echo '🛑 停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
