# Token Transfer Station

LLM API Token 中转站 — 统一接入国内外大模型，以兼容 OpenAI 格式对外提供服务。

## 功能特性

- **统一 API** — 兼容 OpenAI 格式，一行代码切换模型
- **多模型接入** — OpenAI、Claude、DeepSeek、通义千问、Gemini 等
- **灵活计费** — 按量付费，支持用户分层定价
- **流式响应** — 完整支持 SSE 流式输出
- **频率限制** — 基于 Redis 的滑动窗口限流
- **用量统计** — 实时记录每次调用的 Token 消耗和费用

## 快速开始

### 环境要求

- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- uv (包管理器)

### 安装

```bash
# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone https://github.com/WillAlex2017/token_transferstation.git
cd token_transferstation

# 创建虚拟环境并安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入各模型的 API Key
```

### 启动服务

```bash
# 启动 PostgreSQL 和 Redis
brew services start postgresql@16
brew services start redis

# 创建数据库
createdb token_transfer

# 启动开发服务器
make dev
# 或: uv run uvicorn app.main:app --reload
```

### 验证

```bash
# 健康检查
curl http://localhost:8000/health

# 列出可用模型
curl http://localhost:8000/v1/models

# 调用聊天 API
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-api-key" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## API 文档

服务启动后访问 http://localhost:8000/docs 查看交互式 API 文档。

### 端点概览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/v1/models` | 列出可用模型 | 否 |
| POST | `/v1/chat/completions` | 聊天补全 | 是 |
| POST | `/v1/embeddings` | 文本嵌入 | 是 |
| POST | `/v1/user/register` | 用户注册 | 否 |
| POST | `/v1/user/login` | 用户登录 | 否 |
| GET | `/v1/user/profile` | 用户信息 | 是 |
| GET | `/v1/user/balance` | 查询余额 | 是 |
| GET | `/v1/user/api-keys` | 列出 API Key | 是 |
| POST | `/v1/user/api-keys` | 创建 API Key | 是 |

## 项目结构

```
token_transferstation/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── redis.py             # Redis 连接
│   ├── models/              # SQLAlchemy 模型
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── api/v1/              # API 路由
│   ├── adapters/            # 模型适配器
│   ├── middleware/          # 中间件
│   └── services/            # 业务逻辑
├── tests/                   # 测试
├── Makefile                 # 常用命令
├── pyproject.toml           # 项目配置与依赖
└── docker-compose.yml       # 本地基础设施
```

## 开发

```bash
make dev      # 启动开发服务器（热重载）
make test     # 运行测试
make lock     # 更新依赖锁
make sync     # 同步依赖
```

## 部署

```bash
docker build -t token-transferstation .
docker run -p 8000:8000 --env-file .env token-transferstation
```

## 支持模型

| 模型 | 提供商 | 状态 |
|------|--------|------|
| GPT-4o | OpenAI | ✅ |
| GPT-4o-mini | OpenAI | ✅ |
| Claude 3.5 Sonnet | Anthropic | 🚧 |
| DeepSeek-V3 | DeepSeek | 🚧 |
| DeepSeek-R1 | DeepSeek | 🚧 |
| 通义千问 Max | Alibaba | 🚧 |
| Gemini 2.0 Flash | Google | 🚧 |
