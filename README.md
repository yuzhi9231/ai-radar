# AI Radar

> 每日 AI 行业精选资讯，智能摘要，一键订阅

AI Radar 是一个自动化 AI 行业新闻采集与智能摘要工具。它每日从 TechCrunch、The Verge、Hacker News 等来源收集 AI 相关报道，通过本地 AI 模型（Ollama）进行中文摘要、分类和重要性评分，最终生成结构化的每日简报。

## 架构

```
┌─────────────┐     ┌──────────────┐     ┌───────────┐
│  Collector   │────▶│   SQLite     │────▶│   Web     │
│  (Python)    │     │   Database   │     │ (Next.js) │
│              │     │   (G: drive) │     │           │
│ • RSS/API    │     │              │     │ • 文章浏览 │
│ • 去重       │     │              │     │ • 每日简报 │
│ • AI 加工    │     │              │     │ • 深色模式 │
└─────────────┘     └──────────────┘     └───────────┘
        ▲                        │
        │                        │
   ┌────┴────┐              ┌────┴────┐
   │ Ollama  │              │ Browser │
   │ (Qwen3.6)│             │         │
   └─────────┘              └─────────┘
```

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | Next.js 15 (App Router) + TypeScript + Tailwind CSS |
| 后端 | Python 3.12+ + httpx + feedparser + APScheduler |
| 数据库 | SQLite (单文件，Docker volume 持久化) |
| AI | Ollama 本地运行 Qwen3.6-35B-A3B |
| 部署 | Docker Compose Monorepo |

## 快速开始

### 前置要求

- Docker Desktop (包含 Docker Compose)
- 至少 40GB 可用磁盘空间（数据库和模型数据存储在 G 盘）

### 一键启动

```powershell
cd "G:\AI早报\AI Radar"
docker compose up -d
```

启动后访问 http://localhost:3000 即可使用。

### 首次运行

1. Ollama 容器启动后，拉取模型：
   ```powershell
   docker exec ai-radar-ollama ollama pull qwen3.6:35b-a3b
   ```
2. 手动运行一次数据采集：
   ```powershell
   docker exec ai-radar-collector python -m collector.run
   ```
3. 刷新浏览器，查看生成的每日简报。

### 环境变量

复制 `.env.example` 为 `.env` 并根据需要修改：

```powershell
Copy-Item .env.example .env
```

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `file:/data/ai-radar.db` | SQLite 数据库路径 |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API 地址 |
| `USE_MOCK_AI` | `false` | 使用 Mock AI 模式（开发/测试用） |
| `SCHEDULE` | `10:00,15:00` | 采集时间（Asia/Singapore） |

## 开发

### 本地开发（不使用 Docker）

#### Collector

```powershell
cd collector
pip install -r requirements.txt
USE_MOCK_AI=true python -m collector.run
```

#### Web

```powershell
cd web
npm install
npm run dev
```

### Mock AI 模式

设置 `USE_MOCK_AI=true` 可在没有 Ollama 的情况下运行完整 pipeline，所有 AI 处理都会返回模拟数据。适用于：
- 本地开发（无需下载大模型）
- 集成测试
- 快速验证功能

### 运行测试

```powershell
# Collector 集成测试
cd collector
pip install -r requirements.txt
pytest tests/ -v

# Web API 客户端测试（需要安装 Jest）
cd web
npx jest tests/
```

## 数据源（Phase 1）

| 来源 | 类型 | 地址 |
|------|------|------|
| TechCrunch AI | RSS | `techcrunch.com/category/artificial-intelligence/feed/` |
| The Verge AI | RSS | `theverge.com/rss/ai-artificial-intelligence/index.xml` |
| Hacker News | Algolia API | `hn.algolia.com/api/v1/search` |

## 采集时间

每天 **10:00** 和 **15:00**（Asia/Singapore 时区），可通过 `SCHEDULE` 环境变量自定义。

## 目录结构

```
AI Radar/
├── collector/              # Python 采集服务
│   ├── __init__.py
│   ├── models.py           # Pydantic 数据模型
│   ├── db.py               # SQLite 操作
│   ├── collectors.py       # 数据源采集器
│   ├── dedup.py            # 去重逻辑
│   ├── ai.py               # AI 加工（支持 Mock）
│   ├── scheduler.py        # APScheduler 定时任务
│   ├── run.py              # Pipeline 编排
│   ├── cli.py              # CLI 入口
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/              # 集成测试
│       └── test_integration.py
├── web/                    # Next.js 前端
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── Dockerfile
│   ├── src/
│   │   ├── app/            # App Router 页面
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx    # 首页（每日简报）
│   │   │   ├── globals.css # 主题变量
│   │   │   ├── articles/   # 文章列表
│   │   │   ├── about/      # 关于
│   │   │   └── api/        # API 路由
│   │   │       ├── articles/route.ts
│   │   │       ├── sources/route.ts
│   │   │       ├── stats/route.ts
│   │   │       └── briefs/route.ts
│   │   ├── components/     # UI 组件
│   │   └── lib/            # 工具函数
│   └── tests/              # Web 测试
│       └── api-client.test.ts
├── docs/
│   ├── SPEC.md             # 完整规格文档
│   └── ADRs.md             # 架构决策记录
├── docker-compose.yml      # Docker Compose 编排
├── .env.example            # 环境变量模板
└── README.md               # 本文件
```

## 测试覆盖

集成测试覆盖以下场景：

- [x] 数据采集（RSS + API）
- [x] 去重（URL 精确匹配 + 标题相似度）
- [x] AI 加工（Mock 模式）
- [x] 数据库存储（SQLite CRUD）
- [x] API 路由（Articles / Sources / Stats / Briefs）
- [x] 前端页面（首页 / 文章列表 / 关于）
- [x] 每日简报（生成与读取）
- [x] 深色模式（localStorage 持久化）
- [x] Docker Compose 编排
- [x] README 文档

## 许可证

MIT
