# AI Agent Meeting System

AI 代理会议系统是一个允许用户配置多个 AI 代理（来自不同模型供应商）并让它们在虚拟会议中进行角色扮演讨论的应用程序。

## 功能特性

- **多供应商支持**: 集成来自 OpenAI、Anthropic、Google 和 GLM（智谱AI）的 AI 代理
- **基于角色的代理**: 使用模板或自定义提示词配置具有特定角色和行为的代理
- **@ 提及功能**: 像社交媒体一样使用 `@代理名` 指定发言者，自然直观 🎯
- **结构化会议**: 创建具有可配置发言顺序、轮次限制和消息长度约束的会议
- **智能交互**: 支持 @ 提及、请求所有代理、运行一轮等多种互动方式
- **会议管理**: 暂停、恢复和结束会议，具有完整的状态管理
- **导出功能**: 将会议记录导出为 Markdown 或 JSON 格式
- **命令行界面**: 功能完整的 CLI，用于管理代理和会议
- **Web 界面**: 友好的图形化界面，支持实时会议交互（WebSocket）

## 安装

```bash
# 克隆仓库
git clone <repository-url>
cd ai-agent-meeting

# 安装依赖
pip install -e .

# 或安装开发依赖
pip install -e ".[dev]"
```

## 快速开始

### 使用 Web 界面（推荐）

```bash
# 安装依赖
pip install -e .
pip install -r requirements-web.txt

cd web-frontend
npm install
cd ..

# 启动服务
./start_web.sh

# 访问 http://localhost:5173
```

详细使用说明请查看：
- [快速开始指南](QUICK_START.md) - 新手入门必读
- [Web 界面使用指南](WEB_INTERFACE_GUIDE.md) - 完整功能说明

### 使用命令行

#### 1. 创建代理

```bash
# 使用角色模板创建代理
python -m src.cli.main agent create \
  --name "Alice" \
  --provider openai \
  --model gpt-4 \
  --api-key YOUR_API_KEY \
  --template product_manager

# 列出可用模板
python -m src.cli.main agent templates

# 列出所有代理
python -m src.cli.main agent list
```

### 2. 创建并运行会议

```bash
# 创建会议
python -m src.cli.main meeting create \
  --topic "产品规划讨论" \
  --agents "AGENT_ID_1,AGENT_ID_2,AGENT_ID_3" \
  --max-rounds 3 \
  --order sequential

# 运行会议一轮
python -m src.cli.main meeting run MEETING_ID --rounds 1

# 查看会议历史
python -m src.cli.main meeting history MEETING_ID

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

## CLI 命令

### 代理管理

- `agent create` - 创建新代理
- `agent list` - 列出所有代理
- `agent show AGENT_ID` - 显示代理详情
- `agent update AGENT_ID` - 更新代理配置
- `agent delete AGENT_ID` - 删除代理
- `agent test AGENT_ID` - 测试代理连接
- `agent templates` - 列出可用角色模板

### 会议管理

- `meeting create` - 创建新会议
- `meeting list` - 列出所有会议
- `meeting show MEETING_ID` - 显示会议详情
- `meeting start MEETING_ID` - 启动/恢复会议
- `meeting pause MEETING_ID` - 暂停会议
- `meeting end MEETING_ID` - 结束会议
- `meeting delete MEETING_ID` - 删除会议
- `meeting send MEETING_ID` - 发送用户消息
- `meeting request MEETING_ID AGENT_ID` - 请求代理响应
- `meeting run MEETING_ID` - 运行多轮会议
- `meeting history MEETING_ID` - 查看完整会议历史
- `meeting export MEETING_ID` - 导出会议到文件

## 架构

系统遵循清晰的模块化架构：

```
┌─────────────────────────────────────┐
│      CLI 层 (Click)                 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│    应用服务层                        │
│  - AgentService                     │
│  - MeetingService                   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│     领域模型                         │
│  - Agent, Role, ModelConfig         │
│  - Meeting, Message                 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   基础设施                           │
│  - ModelAdapters (OpenAI, etc.)     │
│  - FileStorage                      │
└─────────────────────────────────────┘
```

## 项目结构

```
ai-agent-meeting/
├── src/
│   ├── adapters/          # AI 模型适配器
│   ├── cli/               # 命令行界面
│   ├── models/            # 领域模型
│   ├── services/          # 业务逻辑服务
│   └── storage/           # 数据持久化
├── tests/                 # 测试套件
├── examples/              # 示例脚本
└── docs/                  # 文档
```

## 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并显示覆盖率
pytest --cov=src

# 运行特定测试文件
pytest tests/test_cli_integration.py -v
```

### 开发工具

本项目使用：
- **pytest**: 测试框架
- **pytest-asyncio**: 异步测试支持
- **Hypothesis**: 基于属性的测试
- **pytest-cov**: 代码覆盖率
- **Click**: CLI 框架

## 文档

- [快速开始指南](QUICK_START.md) - 新手入门必读 ⭐
- [@ 提及功能指南](MENTION_FEATURE.md) - 智能 @ 提及使用说明 🎯
- [使用示例](USAGE_EXAMPLES.md) - 实际使用场景和技巧 💡
- [Web 界面使用指南](WEB_INTERFACE_GUIDE.md) - Web 界面详细使用说明
- [故障排查指南](TROUBLESHOOTING.md) - 常见问题解决方案 🔧
- [性能调优指南](PERFORMANCE_TUNING.md) - 超时配置和性能优化 ⚡
- [CLI 使用指南](CLI_USAGE.md) - 详细的 CLI 命令参考
- [角色模板](docs/role_templates.md) - 角色模板信息
- [设计文档](.kiro/specs/ai-agent-meeting/design.md) - 系统设计和架构
- [需求文档](.kiro/specs/ai-agent-meeting/requirements.md) - 系统需求

## 支持的 AI 模型供应商

- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude)
- Google (Gemini)
- GLM (智谱 AI)
