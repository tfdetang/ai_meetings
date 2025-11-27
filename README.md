# AI Agent Meeting System

AI 代理会议系统是一个允许用户配置多个 AI 代理（来自不同模型供应商）并让它们在虚拟会议中进行角色扮演讨论的应用程序。

## 功能特性

### 核心功能
- **多供应商支持**: 集成来自 OpenAI、Anthropic、Google 和 GLM（智谱AI）的 AI 代理
- **基于角色的代理**: 使用模板或自定义提示词配置具有特定角色和行为的代理
- **结构化会议**: 创建具有可配置发言顺序、轮次限制和消息长度约束的会议
- **会议管理**: 暂停、恢复和结束会议，具有完整的状态管理
- **导出功能**: 将会议记录导出为 Markdown 或 JSON 格式

### 🆕 最新功能 (v1.2.0)
- **📝 自动会议纪要**: AI 主持人在会议结束时自动生成纪要，包含摘要、决策和待办事项
- **🔄 自动持续对话**: AI @ AI 时自动触发响应，形成自然的连续对话链
- **⚡ 流式输出**: AI 回复实时显示，无需等待完整响应，更流畅的体验
- **前端开关控制**: 可随时启用/禁用自动响应和流式输出

### 交互功能
- **@ 提及功能**: 像社交媒体一样使用 `@代理名` 指定发言者，自然直观 🎯
- **Markdown 渲染**: 支持完整的 Markdown 格式，包括代码块、表格、图片等 📝
- **彩色识别**: 每个代理自动分配独特颜色，消息气泡和标签一目了然 🎨
- **智能交互**: 支持 @ 提及、请求所有代理、运行一轮等多种互动方式

### 界面
- **命令行界面**: 功能完整的 CLI，用于管理代理和会议
- **Web 界面**: 友好的图形化界面，支持实时会议交互（WebSocket）

## 前置要求

- Python 3.9+
- Node.js 16+
- npm 或 yarn

## 安装与部署

### 方式一：Docker Compose（最简单）🐳

使用 Docker Compose 可以一键启动整个系统，无需手动安装依赖：

```bash
# 克隆仓库
git clone https://github.com/tfdetang/ai_meetings
cd ai_meetings

# 启动服务（首次启动会自动构建镜像）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

服务启动后：
- **前端界面**: http://localhost:3005
- **后端 API**: http://localhost:8888

数据持久化：会议和代理数据保存在 `./data` 目录，容器重启后数据不会丢失

### 方式二：一键安装脚本（推荐）

```bash
# 克隆仓库
git clone <repository-url>
cd ai-agent-meeting

# 一键安装所有依赖
./install_web.sh

# 启动服务
./start_web.sh
```

### 方式三：手动安装

```bash
# 1. 安装 Python 依赖
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows

pip install -e .
pip install -r requirements-web.txt

# 2. 安装前端依赖
cd web-frontend
npm install
cd ..

# 3. 启动后端（终端 1）
python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8888 --reload

# 4. 启动前端（终端 2）
cd web-frontend
npm run dev
```

### 访问应用

- **前端界面**: http://localhost:5173
- **API 文档**: http://localhost:8888/docs （Swagger UI）
- **API 备用文档**: http://localhost:8888/redoc （ReDoc）

## 快速开始

### Web 界面使用

1. 打开浏览器访问 http://localhost:5173
2. 点击"代理管理" → "创建代理"
3. 填写代理信息（名称、供应商、模型、API Key、角色模板）
4. 点击"会议管理" → "创建会议"
5. 选择参与代理，设置会议主题和参数
6. 进入会议室，开始讨论

**使用技巧**：
- **@ 提及代理**：在消息中输入 `@代理名`，如 `@Alice 你怎么看？`
- **@ 多个代理**：`@Alice @Bob 你们觉得呢？`
- **请求所有代理**：点击"发送并请求所有代理"
- **运行一轮**：让所有代理依次发言
- **导出会议**：支持 Markdown 和 JSON 格式

### 命令行使用

```bash
# 创建代理
python -m src.cli.main agent create \
  --name "Alice" \
  --provider openai \
  --model gpt-4 \
  --api-key YOUR_API_KEY \
  --template product_manager

# 创建会议
python -m src.cli.main meeting create \
  --topic "产品规划讨论" \
  --agents "AGENT_ID_1,AGENT_ID_2,AGENT_ID_3" \
  --max-rounds 3 \
  --order sequential

# 运行会议
python -m src.cli.main meeting run MEETING_ID --rounds 1

# 导出会议
python -m src.cli.main meeting export MEETING_ID --format markdown -o meeting.md
```

## 可用角色模板

- **product_manager**: 专注于用户需求和业务价值的战略产品经理
- **software_engineer**: 专注于技术实现的务实工程师
- **ux_designer**: 专注于体验和可用性的以用户为中心的设计师
- **qa_engineer**: 专注于测试和质量的细致 QA 工程师
- **data_analyst**: 专注于指标和洞察的分析专业人员
- **business_analyst**: 连接技术和业务利益相关者的业务分析师
- **devops_engineer**: 专注于部署和可靠性的基础设施工程师
- **security_engineer**: 识别漏洞的安全工程师
- **technical_writer**: 专注于清晰沟通的文档专家
- **project_manager**: 专注于时间表和资源的组织领导者

## CLI 命令参考

**代理管理**：`agent create/list/show/update/delete/test/templates`

**会议管理**：`meeting create/list/show/start/pause/end/delete/send/request/run/history/export`

## 项目结构

```
ai-agent-meeting/
├── src/
│   ├── adapters/          # AI 模型适配器（OpenAI、Anthropic、Google、GLM）
│   ├── cli/               # 命令行界面
│   ├── models/            # 领域模型（Agent、Meeting、Message、Role）
│   ├── services/          # 业务逻辑服务
│   ├── storage/           # 数据持久化
│   └── web/               # Web API（FastAPI + WebSocket）
├── web-frontend/          # React 前端应用
├── data/                  # 数据存储目录
│   ├── agents/            # 代理数据
│   └── meetings/          # 会议数据
├── docs/                  # 文档
├── tests/                 # 测试套件
├── docker-compose.yml     # Docker 部署配置
└── README.md              # 本文档
```

## 常见问题

### 端口被占用
修改 `start_web.sh`、`src/web/api.py` 和 `web-frontend/vite.config.js` 中的端口配置

### 前端无法连接后端
1. 确保后端已启动：访问 http://localhost:8888 应该看到 `{"status":"ok"}`
2. 检查 `web-frontend/vite.config.js` 中的代理配置

### 代理测试连接失败
1. 检查 API Key 是否正确
2. 确认模型名称正确（如 OpenAI 的 "gpt-4"）
3. 检查网络连接

### 会议中代理不响应
1. 确保会议状态是"进行中"
2. 检查后端日志是否有错误
3. 验证代理的 API Key 是否有效

## 文档

- [功能指南](FEATURES.md) - 所有功能的详细说明
- [更新日志](CHANGELOG.md) - 版本更新记录
- [角色模板](docs/role_templates.md) - 角色模板信息

## 支持的 AI 模型供应商

- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude)
- Google (Gemini)
- GLM (智谱 AI)
