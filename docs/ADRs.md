# AI Radar · 设计决策记录 (ADRs)

> 最后更新：2026-10-20

---

## ADR-001：产品形态 — 半公开工具

**状态**：已决定
**决策**：第一版为半公开工具，任何人都能访问阅读，不做用户注册、评论、社区功能。收藏用 localStorage。

**理由**：
- MVP 阶段工程复杂度最低
- 能立刻让朋友/同事使用
- 用户系统可在有真实需求时再添加
- 避免过早优化

**替代方案**：
- 纯个人工具：分享不便
- 公开平台：用户系统、评论、社交功能增加大量工程复杂度

---

## ADR-002：AI 加工 — 本地 Ollama 模型

**状态**：已决定
**决策**：AI 加工（摘要生成、分类、评分）使用本地 Ollama 服务，模型为 Qwen3.6-35B-A3B-UD-Q4_K_M（MoE：35B 总参数，3B 激活参数）。

**理由**：
- 零 API 成本
- 数据不出本机
- Qwen 系列对中文理解能力强
- MoE 架构激活参数少，推理效率高

**替代方案**：
- 云端 API：有持续成本，需要管理 Key
- 本地 CPU 运行：速度慢

**注意事项**：
- Docker 中运行 Ollama 需要 GPU 支持
- 35B 模型需要足够显存（建议 ≥16GB VRAM）

---

## ADR-003：部署架构 — Docker Compose Monorepo

**状态**：已决定
**决策**：使用 Docker Compose 管理所有服务，Monorepo 项目结构。所有服务自包含，新机器一键启动。

**服务组成**：
- `web`：Next.js 前端 + API（端口 3000）
- `collector`：Python 采集服务（不暴露端口）
- `ollama`：本地 AI 模型服务（端口 11434）

**理由**：
- 环境一致性，开发/部署无差异
- 新机器 `docker compose up -d` 即可运行
- 公开仓库，他人可 fork 使用

**注意事项**：
- Docker volume 和数据文件必须指向 G 盘（C 盘空间不足）
- docker-compose.yml 中使用绝对路径挂载 volume

---

## ADR-004：数据采集频率 — 每天 2 次

**状态**：已决定
**决策**：每天早晨 10:00 和下午 15:00（Asia/Singapore）各执行一次采集。

**理由**：
- 覆盖上午和下午的新闻
- 比每天 1 次更全面，比 3 次更轻量
- 采集任务在容器内通过 cron 或 node-cron 调度

**替代方案**：
- 每天 1 次：信息不够及时
- 每天 3 次：GitHub Actions 免费额度不够，VPS 成本高

---

## ADR-005：去重策略 — 浅去重

**状态**：已决定
**决策**：第一版使用 URL 去重 + 标题编辑距离/关键词重叠去重。同一事件的不同报道保留为独立 Article，但在详情中作为"相关报道"关联。

**理由**：
- 语义聚类的误合并率高（同名模型会错合）
- 浅去重准确率高，实现简单
- 保留信息完整性，不丢失任何报道

**替代方案**：
- 深度聚类：误合并风险高，实现复杂
- 不做去重：用户体验差

---

## ADR-006：数据库 — SQLite

**状态**：已决定
**决策**：使用 SQLite 作为第一版数据库，通过 Python 的 `sqlite3` 模块或 `aiosqlite` 访问。

**理由**：
- 零运维、零成本、文件数据库
- MVP 阶段数据量不大，SQLite 完全够用
- 单文件数据库，备份方便
- 后续迁移 PostgreSQL 成本低

**替代方案**：
- Supabase：免费额度有限，500MB 存储新闻场景可能耗尽
- 本地 PostgreSQL：需要额外运维

---

## ADR-007：数据来源 — Phase 1 接 3 个源

**状态**：已决定
**决策**：Phase 1 接入以下 3 个数据源：

| 数据源 | 类型 | URL |
|--------|------|-----|
| TechCrunch AI | RSS | `https://techcrunch.com/category/artificial-intelligence/feed/` |
| The Verge AI | RSS | `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml` |
| Hacker News | Algolia API | `https://hn.algolia.com/api/v1/search?tags=story&dateRange=past24hours` |

**理由**：
- TechCrunch + The Verge 覆盖媒体和产品视角
- Hacker News 提供开发者社区热度信号
- 3 个源足够 MVP 阶段验证数据流

**Phase 2 计划接入**：OpenAI、Google DeepMind、Hugging Face、Mistral、arXiv

---

## ADR-008：技术栈 — Next.js + Python Collector

**状态**：已决定
**决策**：

| 层 | 技术 |
|----|------|
| 前端 | Next.js 15 (App Router) + TypeScript |
| UI | Tailwind CSS + shadcn/ui |
| 数据库 | SQLite |
| 采集服务 | Python 3.12+ (feedparser + httpx) |
| AI 加工 | Ollama (本地模型) |
| 部署 | Docker Compose |
| 调度 | Python APScheduler 或 Docker cron |

**理由**：
- Next.js：SSR/SSG、API Routes、SEO 均方便
- shadcn/ui：现成组件，快速建立设计系统
- Python 采集：feedparser 生态成熟，数据处理能力强
- SQLite：零运维

---

## ADR-009：每日简报 — 结构化 JSON

**状态**：已决定
**决策**：每日简报存储为结构化 JSON，包含：
- `trend_summary`：当日 AI 领域趋势概述（100-200 字）
- `highlight_events`：5-8 个重点事件（每条关联到 Article）
- `dev_focus`：3-5 条开发者关注点

**理由**：
- 结构化数据前端可灵活渲染
- 便于后续扩展（如导出为邮件、推送）
- 每条可追溯到原始 Article

**替代方案**：
- 纯文本长文：前端展示不够灵活
- Markdown 文件：与数据库分离

---

## ADR-010：磁盘约束 — C 盘不足，Docker 数据放 G 盘

**状态**：已决定
**决策**：
- 项目代码位于 `G:\AI早报\AI Radar`
- Docker volume 和数据文件通过绝对路径挂载到 G 盘
- `.env` 中配置 SQLite 数据库路径为 G 盘路径

**理由**：
- C 盘仅剩 43.5GB，不够 Docker 和数据库使用
- G 盘有 922.7GB 可用

**注意事项**：
- Docker Desktop for Windows 中需要确保 G 盘被共享
- docker-compose.yml 中使用绝对路径（如 `G:/AI早报/ai-radar/data/`）
