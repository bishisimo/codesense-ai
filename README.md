# CodeSense AI - GitLab代码审查系统

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.4+-4FC08D.svg)](https://vuejs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于AI的GitLab代码审查系统，提供智能化的代码审查、项目管理、数据统计和通知功能。

## ✨ 主要特性

### 🤖 AI智能审查
- **多模型支持**: 支持DeepSeek、OpenAI、Claude等多种AI模型
- **智能分析**: 自动分析代码质量、安全性、性能等问题
- **评分系统**: 0-100分评分机制，直观展示代码质量
- **详细报告**: 生成Markdown格式的详细审查报告

### 📊 项目管理
- **项目同步**: 自动同步GitLab项目信息
- **合并请求管理**: 实时跟踪MR状态和变更
- **分支管理**: 支持多分支代码审查
- **提交分析**: 详细的提交历史和变更统计


### 🎨 现代化界面
- **响应式设计**: 支持桌面和移动端访问
- **主题支持**: 现代化的UI设计
- **实时更新**: 基于WebSocket的实时数据更新
- **多语言支持**: 支持中英文界面

## 🏗️ 技术架构

### 后端技术栈
- **框架**: FastAPI (异步高性能Web框架)
- **数据库**: SQLAlchemy + Alembic (支持MySQL/PostgreSQL)
- **AI集成**: 多模型AI服务抽象层
- **认证**: JWT + 密码加密
- **任务调度**: 异步任务管理器
- **包管理**: uv (现代化Python包管理)

### 前端技术栈
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **图表**: ECharts
- **包管理**: bun (现代化JavaScript包管理)

### 基础设施
- **容器化**: Docker + Docker Compose
- **数据库**: MySQL 8.0

## 🚀 快速开始

### 环境要求
- Python 3.13+
- Node.js 18+ (或使用bun)
- Docker & Docker Compose (推荐)
- GitLab实例访问权限
- AI模型API密钥
- MySQL数据库

### 一键启动 (推荐)

1. **克隆项目**
```bash
git clone <repository-url>
cd codesense-ai
```

2. **配置系统**
```bash
# 复制配置文件
cp backend/config/config.example.yaml config.yaml

# 编辑配置文件，设置GitLab和AI配置
vim config.yaml
```

3. **启动服务**
```bash
# 使用启动脚本
chmod +x start.sh
./start.sh
```

4. **访问系统**
- 管理界面: http://localhost:8080
- API文档: http://localhost:8080/docs
- 默认密码: `admin123`

### 手动启动

#### 后端启动
```bash
cd backend

# 使用uv (推荐)
uv pip install -e .
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8080

# 或使用传统方式
pip install -e .
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

#### 前端启动
```bash
cd frontend

# 使用bun (推荐)
bun install
bun run dev

# 或使用npm
npm install
npm run dev
```

## ⚙️ 配置说明

### 主要配置项

```yaml
# GitLab配置
gitlab:
  url: "https://gitlab.example.com"
  token: "your-gitlab-token"
  webhook_secret: "your-webhook-secret"

# AI配置
ai:
  provider: "deepseek"  # deepseek, openai, anthropic
  api_key: "your-ai-api-key"
  model: "deepseek-chat"
  max_tokens: 4000

# 数据库配置
database:
  type: "mysql"
  url: "mysql+asyncmy://codesense_ai:password123@localhost/codesense_ai"

# 认证配置
auth:
  secret_key: "your-secret-key"
  access_token_expire_minutes: 30

```

### 环境变量覆盖

支持通过环境变量覆盖配置：

```bash
export GITLAB_URL="https://gitlab.example.com"
export GITLAB_TOKEN="your-token"
export AI_API_KEY="your-key"
export ADMIN_PASSWORD="your-password"
```

## 📁 项目结构

```
codesense-ai/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API路由
│   │   │   ├── auth.py        # 认证API
│   │   │   ├── dashboard.py   # 仪表板API
│   │   │   ├── merge_requests.py # 合并请求API
│   │   │   ├── reviews.py     # 审查API
│   │   │   ├── stats/         # 统计API
│   │   │   └── webhook.py     # Webhook API
│   │   ├── core/              # 核心模块
│   │   │   ├── config.py      # 配置管理
│   │   │   ├── database.py    # 数据库连接
│   │   │   └── security.py    # 安全认证
│   │   ├── libs/              # 第三方库封装
│   │   │   ├── ai_models/     # AI模型管理
│   │   │   ├── gitlabx/       # GitLab客户端
│   │   │   └── file_filter/   # 文件过滤器
│   │   ├── models/            # 数据模型
│   │   ├── schemas/           # Pydantic模式
│   │   └── services/          # 业务逻辑
│   │       ├── ai/            # AI服务
│   │       ├── review/        # 审查服务
│   │       └── notification/  # 通知服务
│   ├── config/                # 配置文件
│   ├── scripts/               # 初始化脚本
│   └── pyproject.toml         # 项目配置
├── frontend/                  # 前端应用
│   ├── src/
│   │   ├── components/        # Vue组件
│   │   ├── views/            # 页面视图
│   │   ├── api/              # API客户端
│   │   ├── stores/           # 状态管理
│   │   └── router/           # 路由配置
│   └── package.json          # 项目配置
├── docs/                     # 文档
├── docker-compose.yml        # Docker配置
└── start.sh                  # 启动脚本
```

## 🔌 API接口

### 认证接口
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/menu-config` - 获取菜单配置

### 核心功能接口
- `GET /api/dashboard/overview` - 仪表板概览
- `GET /api/merge-requests` - 获取合并请求列表
- `POST /api/reviews/{mr_id}` - 执行代码审查
- `GET /api/reviews/{review_id}` - 获取审查详情


### Webhook接口 ⚠️ **TODO - 未验证**
- `POST /api/webhook/gitlab` - GitLab Webhook接收
- `GET /api/webhook/test` - 测试Webhook连接

## 🎯 使用指南

### 1. 初始配置
1. 配置GitLab连接信息
2. 设置AI模型API密钥
3. 配置数据库连接
4. 设置管理员密码

### 2. 项目同步
1. 系统会自动同步GitLab项目
2. 可通过"强制同步"按钮手动刷新
3. ⚠️ **TODO**: GitLab Webhook自动同步

### 3. 代码审查
1. 在"AI审查"页面查看合并请求
2. 点击"审查"按钮执行AI分析
3. 查看详细的审查报告和评分


## 🔧 开发指南

### 数据库迁移
```bash
cd backend

# 生成迁移文件
uv run alembic revision --autogenerate -m "描述"

# 执行迁移
uv run alembic upgrade head
```

## 🐳 Docker部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```


## ⚠️ 待验证功能 (TODO)

以下功能已经实现但尚未经过实际验证，使用时请注意：

### GitLab Webhook自动同步
- **状态**: 已实现，待验证
- **功能**: 自动接收GitLab webhook事件并同步数据
- **支持事件**: 合并请求、推送、问题、评论、流水线
- **测试方法**: 使用 `backend/test/test_webhook.py` 脚本进行测试
- **配置要求**: 需要在GitLab中配置webhook URL和secret token

## 📝 更新日志

### v0.1.0 (当前版本)
- ✨ 基础AI代码审查功能
- 🎨 现代化Web界面
- 🔧 灵活的配置系统
- 🐳 Docker容器化支持
- ⚠️ **TODO**: GitLab Webhook自动同步（已实现，待验证）

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---
