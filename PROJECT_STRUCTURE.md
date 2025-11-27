# 项目结构说明

## 核心文件

- **README.md** - 项目主文档（包含安装、部署、使用说明）
- **FEATURES.md** - 功能详细说明
- **CHANGELOG.md** - 版本更新记录

## 安装部署

- **docker-compose.yml** - Docker 一键部署配置
- **install_web.sh** - 依赖安装脚本
- **start_web.sh** - 服务启动脚本
- **requirements-web.txt** - Python Web 依赖
- **pyproject.toml** - Python 项目配置

## 源代码

```
src/
├── adapters/       # AI 模型适配器
├── cli/            # 命令行工具
├── models/         # 数据模型
├── services/       # 业务逻辑
├── storage/        # 数据存储
└── web/            # Web API
```

## 前端应用

```
web-frontend/
├── src/            # React 源代码
├── package.json    # 前端依赖
└── vite.config.js  # 构建配置
```

## 数据目录

```
data/
├── agents/         # 代理数据
└── meetings/       # 会议数据
```

## 文档

```
docs/
└── role_templates.md  # 角色模板说明
```

## 测试

```
tests/              # 单元测试和集成测试
```

## 快速开始

1. **Docker 部署**（推荐）：`docker-compose up -d`
2. **本地开发**：`./install_web.sh && ./start_web.sh`
3. **访问应用**：http://localhost:5173

详细说明请查看 [README.md](README.md)
