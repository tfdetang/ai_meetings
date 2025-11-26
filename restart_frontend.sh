#!/bin/bash

echo "=================================="
echo "重启前端服务"
echo "=================================="
echo ""

cd web-frontend

echo "1. 清理缓存..."
rm -rf node_modules/.vite
rm -rf dist
echo "✅ 缓存已清理"

echo ""
echo "2. 重新启动开发服务器..."
echo ""
echo "请在新终端运行: cd web-frontend && npm run dev"
echo ""
echo "然后："
echo "1. 完全关闭浏览器标签页"
echo "2. 重新打开 http://localhost:5173"
echo "3. 进入会议室"
echo "4. 关闭 '自动持续对话' 开关"
echo "5. 开启 '流式输出' 开关"
echo "6. 测试"
echo ""
echo "查看控制台应该显示:"
echo "  [Meeting Room] Using streaming endpoint"
