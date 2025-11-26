# AI 代理会议系统 - Web 界面使用指南

## 概述

Web 界面为 AI 代理会议系统提供了友好的图形化操作界面，让你可以通过浏览器轻松管理代理和会议。

## 技术栈

- **后端**: FastAPI + WebSocket (实时通信)
- **前端**: React + Vite + Ant Design
- **端口**: 
  - 后端 API: http://localhost:8888
  - 前端界面: http://localhost:5173

## 快速开始

### 1. 安装依赖

#### 后端依赖
```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装 Web 依赖
pip install fastapi uvicorn websockets
```

#### 前端依赖
```bash
cd web-frontend
npm install
```

### 2. 启动服务

#### 方式一：使用启动脚本（推荐）
```bash
./start_web.sh
```

#### 方式二：手动启动

**启动后端：**
```bash
source .venv/bin/activate
python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8888 --reload
```

**启动前端（新终端）：**
```bash
cd web-frontend
npm run dev
```

### 3. 访问界面

- **前端界面**: http://localhost:5173
- **API 文档**: http://localhost:8888/docs (自动生成的 Swagger 文档)

## 功能介绍

### 首页
- 查看系统统计信息（代理数量、会议数量、活跃会议）
- 快速导航到各个功能模块
- 功能特性介绍

### 代理管理
- **创建代理**: 支持选择供应商（OpenAI、Anthropic、Google、GLM）和角色模板
- **查看代理列表**: 显示所有代理的基本信息
- **编辑代理**: 修改代理的名称、角色信息
- **测试连接**: 验证 API Key 是否有效
- **删除代理**: 移除不需要的代理

### 会议管理
- **创建会议**: 
  - 设置会议主题
  - 选择参与的代理（支持多选）
  - 配置发言顺序（顺序/随机）
  - 设置最大轮次和消息长度限制
- **查看会议列表**: 显示所有会议及其状态
- **进入会议室**: 点击"查看"进入会议详情页

### 会议室（实时交互）
- **实时消息显示**: 
  - 自动滚动到最新消息
  - 区分用户消息和代理消息
  - 显示发言轮次和时间戳
- **会议控制**:
  - 开始/暂停/结束会议
  - 实时状态更新（通过 WebSocket）
- **智能互动功能**:
  - **@ 提及代理**（推荐）⭐: 在消息中使用 `@代理名` 指定发言者
  - 发送并请求所有代理响应
  - 仅发送消息（不触发 AI）
  - 运行一轮（所有代理依次发言）
  - 手动请求特定代理发言
- **便捷功能**:
  - 快速 @ 标签：点击代理标签快速插入 @
  - 支持同时 @ 多个代理
  - 自动识别消息中的 @ 提及
- **导出功能**:
  - 导出为 Markdown 格式
  - 导出为 JSON 格式

**@ 提及示例**:
- `@Alice 这个方案可行吗？` - 只有 Alice 响应
- `@Alice @Bob 你们怎么看？` - Alice 和 Bob 都响应
- `@产品经理 请评估一下` - 按角色名提及

## API 端点

### 代理相关
- `GET /api/agents` - 获取代理列表
- `POST /api/agents` - 创建代理
- `GET /api/agents/{id}` - 获取代理详情
- `PUT /api/agents/{id}` - 更新代理
- `DELETE /api/agents/{id}` - 删除代理
- `POST /api/agents/{id}/test` - 测试代理连接
- `GET /api/templates` - 获取角色模板列表

### 会议相关
- `GET /api/meetings` - 获取会议列表
- `POST /api/meetings` - 创建会议
- `GET /api/meetings/{id}` - 获取会议详情
- `POST /api/meetings/{id}/start` - 开始会议
- `POST /api/meetings/{id}/pause` - 暂停会议
- `POST /api/meetings/{id}/end` - 结束会议
- `DELETE /api/meetings/{id}` - 删除会议
- `POST /api/meetings/{id}/messages` - 发送消息
- `POST /api/meetings/{id}/request/{agent_id}` - 请求代理响应
- `GET /api/meetings/{id}/export/markdown` - 导出为 Markdown
- `GET /api/meetings/{id}/export/json` - 导出为 JSON

### WebSocket
- `WS /ws/meetings/{id}` - 会议实时更新

## 使用示例

### 1. 创建第一个代理

1. 访问 http://localhost:5173
2. 点击导航栏的"代理管理"
3. 点击"创建代理"按钮
4. 填写表单：
   - 名称: Alice
   - 供应商: OpenAI
   - 模型: gpt-4
   - API Key: 你的 OpenAI API Key
   - 角色模板: 产品经理
5. 点击"确定"

### 2. 创建会议

1. 点击导航栏的"会议管理"
2. 点击"创建会议"按钮
3. 填写表单：
   - 会议主题: 产品功能讨论
   - 参与代理: 选择刚创建的代理
   - 发言顺序: 顺序发言
   - 最大轮次: 3
4. 点击"确定"

### 3. 进行会议

1. 在会议列表中点击"查看"
2. 点击"开始"按钮启动会议
3. 在输入框中输入消息，点击"发送消息"
4. 或选择代理，点击"请求发言"
5. 实时查看代理的回复
6. 会议结束后可以导出记录

## 开发说明

### 项目结构

```
ai-agent-meeting/
├── src/web/                    # 后端 API
│   ├── api.py                  # FastAPI 应用
│   ├── schemas.py              # Pydantic 数据模型
│   └── __init__.py
├── web-frontend/               # 前端应用
│   ├── src/
│   │   ├── api/                # API 客户端
│   │   │   └── client.js
│   │   ├── pages/              # 页面组件
│   │   │   ├── Home.jsx
│   │   │   ├── AgentList.jsx
│   │   │   ├── MeetingList.jsx
│   │   │   └── MeetingRoom.jsx
│   │   ├── App.jsx             # 主应用组件
│   │   ├── main.jsx            # 入口文件
│   │   └── index.css           # 全局样式
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── start_web.sh                # 启动脚本
```

### 添加新功能

#### 后端添加新端点
在 `src/web/api.py` 中添加新的路由：

```python
@app.get("/api/your-endpoint")
async def your_function():
    # 实现逻辑
    return {"data": "result"}
```

#### 前端添加新页面
1. 在 `web-frontend/src/pages/` 创建新组件
2. 在 `App.jsx` 中添加路由
3. 在 `client.js` 中添加 API 调用

### 调试

- **后端日志**: 查看终端输出
- **前端调试**: 使用浏览器开发者工具
- **API 测试**: 访问 http://localhost:8000/docs 使用 Swagger UI

## 常见问题

### Q: 前端无法连接后端？
A: 确保后端已启动在 8888 端口，检查 `vite.config.js` 中的代理配置。

### Q: WebSocket 连接失败？
A: 检查防火墙设置，确保 WebSocket 端口未被阻止。

### Q: 代理测试失败？
A: 验证 API Key 是否正确，检查网络连接。

### Q: 页面样式异常？
A: 清除浏览器缓存，重新加载页面。

## 生产部署

### 后端部署
```bash
# 使用 gunicorn + uvicorn workers
gunicorn src.web.api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8888
```

### 前端部署
```bash
cd web-frontend
npm run build
# 将 dist/ 目录部署到静态文件服务器（如 Nginx）
```

### 环境变量
建议使用环境变量管理敏感信息：
- API Keys
- 数据库连接
- CORS 配置

## 下一步

- 添加用户认证和授权
- 实现会议录制和回放
- 添加更多图表和数据可视化
- 支持多语言界面
- 添加移动端适配

## 反馈与支持

如有问题或建议，请提交 Issue 或 Pull Request。
