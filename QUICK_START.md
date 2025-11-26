# 快速开始指南

## 前置要求

- Python 3.9+
- Node.js 16+
- npm 或 yarn

## 安装步骤

### 方式一：一键安装（推荐）

```bash
./install_web.sh
```

这会自动安装所有后端和前端依赖。

### 方式二：手动安装

**1. 安装 Python 依赖**

```bash
# 激活虚拟环境（如果还没有）
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows

# 安装核心依赖
pip install -e .

# 安装 Web 依赖
pip install -r requirements-web.txt
```

**2. 安装前端依赖**

```bash
cd web-frontend
npm install
cd ..
```

**3. 测试 API（可选）**

```bash
python test_web_api.py
```

如果看到 "✅ All tests passed!"，说明后端配置正确。

## 启动应用

### 方式一：一键启动（推荐）

```bash
./start_web.sh
```

这会自动启动：
- 后端 API 服务（端口 8888）
- 前端开发服务器（端口 5173）

### 方式二：分别启动

**终端 1 - 启动后端：**
```bash
source .venv/bin/activate
python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8888 --reload
```

**终端 2 - 启动前端：**
```bash
cd web-frontend
npm run dev
```

## 访问应用

- **前端界面**: http://localhost:5173
- **API 文档**: http://localhost:8888/docs （Swagger UI）
- **API 备用文档**: http://localhost:8888/redoc （ReDoc）

## 第一次使用

### 1. 创建你的第一个代理

1. 打开浏览器访问 http://localhost:5173
2. 点击导航栏的 "代理管理"
3. 点击 "创建代理" 按钮
4. 填写表单：
   - **名称**: 给代理起个名字，如 "Alice"
   - **供应商**: 选择你有 API Key 的供应商（OpenAI、Anthropic、Google 或 GLM）
   - **模型**: 输入模型名称，如 "gpt-4" 或 "claude-3-opus-20240229"
   - **API Key**: 输入你的 API Key
   - **角色模板**: 可以选择预设模板（如"产品经理"），或者自定义角色
5. 点击 "确定"

💡 **提示**: 如果你还没有 API Key，可以：
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/
- Google: https://makersuite.google.com/app/apikey

### 2. 创建你的第一个会议

1. 点击导航栏的 "会议管理"
2. 点击 "创建会议" 按钮
3. 填写表单：
   - **会议主题**: 如 "产品功能讨论"
   - **参与代理**: 选择刚创建的代理（可以多选）
   - **发言顺序**: 选择 "顺序发言" 或 "随机发言"
   - **最大轮次**: 可选，限制会议轮数
4. 点击 "确定"

### 3. 进行会议

1. 在会议列表中点击 "查看" 进入会议室
2. 会议会自动处于 "进行中" 状态
3. 你可以：
   - **使用 @ 提及代理**（推荐）⭐: 
     - 在消息中输入 `@代理名`，如 `@Alice 你怎么看？`
     - 点击 "发送并 @ 代理响应"
     - 被 @ 的代理会自动响应
   - **请求所有代理响应**: 点击 "发送并请求所有代理"
   - **仅发送消息**: 点击 "仅发送消息"，不触发 AI
   - **运行一轮**: 点击 "运行一轮" 让所有代理依次发言
   - **手动请求**: 选择特定代理，点击 "请求发言"
   - **暂停/结束会议**: 使用对应按钮控制会议状态
4. 所有消息会实时显示在页面上
5. 会议结束后可以导出为 Markdown 或 JSON 格式

💡 **使用技巧**:
- **@ 单个代理**: `@Alice 这个方案可行吗？` → 只有 Alice 响应
- **@ 多个代理**: `@Alice @Bob 你们觉得呢？` → Alice 和 Bob 都会响应
- **快速 @**: 点击输入框上方的代理标签快速插入 @
- **Markdown 格式**: AI 回复支持 Markdown 渲染，包括代码块、表格、图片等
- **切换渲染**: 点击消息卡片右上角的开关可以切换 Markdown 渲染

## 常见问题

### Q: 端口被占用怎么办？

**后端端口 8888 被占用：**
编辑以下文件，将 8888 改为其他端口：
- `start_web.sh`
- `src/web/api.py` (最后一行)
- `web-frontend/vite.config.js` (proxy 配置)

**前端端口 5173 被占用：**
编辑 `web-frontend/vite.config.js`，修改 `server.port`

### Q: 前端无法连接后端？

1. 确保后端已启动：访问 http://localhost:8888 应该看到 `{"status":"ok"}`
2. 检查浏览器控制台是否有 CORS 错误
3. 确认 `web-frontend/vite.config.js` 中的代理配置正确

### Q: 代理测试连接失败？

1. 检查 API Key 是否正确
2. 检查网络连接
3. 确认模型名称正确（如 OpenAI 的 "gpt-4"，不是 "GPT-4"）

### Q: 会议中代理不响应？

1. 确保会议状态是 "进行中"（不是 "已暂停" 或 "已结束"）
2. 检查后端日志是否有错误
3. 验证代理的 API Key 是否有效

### Q: 如何查看后端日志？

后端日志会显示在启动后端的终端窗口中。如果使用 `start_web.sh`，日志会混合显示。

建议分别启动以便查看日志：
```bash
# 终端 1
python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8888 --reload

# 终端 2
cd web-frontend && npm run dev
```

## 使用技巧

### 1. 使用角色模板

系统内置了 10 种专业角色模板：
- 产品经理 (product_manager)
- 软件工程师 (software_engineer)
- UX 设计师 (ux_designer)
- QA 工程师 (qa_engineer)
- 数据分析师 (data_analyst)
- 业务分析师 (business_analyst)
- DevOps 工程师 (devops_engineer)
- 安全工程师 (security_engineer)
- 技术文档工程师 (technical_writer)
- 项目经理 (project_manager)

创建代理时选择模板可以快速获得专业的角色设定。

### 2. 组织有效的会议

**好的会议主题示例：**
- "讨论新功能的技术实现方案"
- "评审用户注册流程的用户体验"
- "分析产品数据并制定优化策略"

**参与者建议：**
- 2-4 个代理最佳
- 选择互补的角色（如：产品经理 + 工程师 + 设计师）
- 避免太多代理导致讨论混乱

### 3. 引导讨论

- 在会议开始时发送明确的问题或背景信息
- 使用 "请求发言" 功能让特定代理回应
- 适时加入讨论，提供额外信息或引导方向

### 4. 导出和分享

- 会议结束后导出为 Markdown 格式便于阅读
- 导出为 JSON 格式便于进一步处理或分析
- 导出的文件包含完整的会议历史和元数据

## 下一步

- 查看 [Web 界面使用指南](WEB_INTERFACE_GUIDE.md) 了解详细功能
- 查看 [CLI 使用指南](CLI_USAGE.md) 了解命令行操作
- 查看 API 文档 http://localhost:8888/docs 了解 API 详情

## 获取帮助

如果遇到问题：
1. 查看本文档的"常见问题"部分
2. 检查后端日志和浏览器控制台
3. 运行 `python test_web_api.py` 测试基础功能
4. 提交 Issue 或查看项目文档

祝使用愉快！🎉
