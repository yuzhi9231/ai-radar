# AI Radar — 每日 AI 情报工作台

> 规格文档 v1.0 · 2026-10-20
> 状态：ready-for-agent

---

## Problem Statement

AI 从业者、开发者和产品设计者每天需要花大量时间从多个分散的信息源（英文媒体、官方博客、论文平台、开发者社区）中筛选有价值的 AI 动态。信息分散、英文阅读成本高、新闻重复报道严重、难以判断每条信息的实际重要性。用户希望有一个中文平台，每天花 5-10 分钟就能全面了解全球 AI 领域发生了什么、哪些最重要、为什么重要，以及有哪些值得自己尝试的新技术。

## Solution

**AI Radar** 是一个本地部署、每日自动更新的 AI 新闻智能聚合 Web 应用。它是一个信息密度高、阅读效率高、可追溯信源的 AI 情报工作台，而非静态新闻站点。

核心工作方式：
1. 每天 10:00 和 15:00（Asia/Singapore）自动采集 3 个经过验证的信息源
2. 通过本地 Ollama 模型对每条新闻进行中文标题生成、中文摘要、分类、重要性评分
3. URL 去重 + 标题相似度去重，避免重复报道
4. 前端展示今日简报（5-8 条重点）和全部资讯（按分类、时间筛选）

## User Stories

1. 作为一名 AI 从业者，我希望每天早上打开网站就能用 3 分钟阅读当天最重要的 5-8 条 AI 动态，这样我就能快速了解当天最值得关注的变化。

2. 作为一名 AI 开发者，我希望浏览按分类（大模型/API、AI Coding/Agent、AI 产品/工具、开源项目、论文/研究、行业/公司/政策）组织的新闻列表，这样我就能快速找到与我工作相关的信息。

3. 作为一名中文用户，我希望每条新闻都有中文标题和 80-150 字的中文摘要，这样我就不用花时间去读全文就能判断是否有价值。

4. 作为一名开发者，我希望每条新闻都显示原始来源名称、原文链接和发布时间，这样我能追溯到原始信息并验证真实性。

5. 作为一名产品观察者，我希望看到每条新闻的重要性评分（0-100）和分类标签，这样我能快速判断信息的权重。

6. 作为一名收藏者，我希望可以将感兴趣的新闻加入收藏（localStorage），这样我可以在以后回顾。

7. 作为一名用户，我希望筛选功能支持按时间范围（24 小时/7 天/30 天）、分类、关键词和排序方式（最新/重要性）过滤新闻，这样我能快速定位感兴趣的内容。

8. 作为一名技术趋势追踪者，我希望每日简报包含"当日总体趋势概述"和"开发者关注点"，这样我能看到宏观层面的 AI 行业动态而不仅仅是单条新闻。

9. 作为一名用户，我希望前端支持浅色/深色主题切换，这样我在不同光线环境下都能舒适阅读。

10. 作为一名桌面端用户，我希望界面采用主内容 + 侧栏的桌面布局，这样我能高效浏览大量信息。

11. 作为一名移动端用户，我希望界面在手机和平板上也能正常显示，这样我在任何设备上都能访问。

12. 作为一名用户，我希望采集失败时网站仍能显示历史内容，并提示"信息可能过期"，这样服务不会完全中断。

13. 作为一名用户，我希望看到"最后更新时间"标识，这样我知道数据的时效性。

14. 作为一名 AI Radar 使用者，我希望相同事件的多媒体报道只显示一条主条目，但在详情中能看到其他相关报道链接，这样我不会看到重复内容但能获取全面信息。

15. 作为一名注重隐私的用户，我希望整个系统可以本地运行，不依赖外部 API 服务，这样我的阅读行为不会被第三方追踪。

## Implementation Decisions

### 架构决策

- **部署方式**：Docker Compose Monorepo，包含三个服务（web、collector、ollama）。新机器通过 `docker compose up -d` 即可启动全部服务。
- **项目位置**：`G:\AI早报\AI Radar`。所有 Docker volume 和数据文件通过绝对路径挂载到 G 盘。
- **公开仓库**：项目代码将推送到公开 Git 仓库，他人可 fork 使用。

### 技术栈决策

| 层 | 技术 |
|----|------|
| 前端 | Next.js 15 (App Router) + TypeScript |
| UI | Tailwind CSS + shadcn/ui |
| 数据库 | SQLite（单文件，Docker volume 持久化） |
| 采集服务 | Python 3.12+（feedparser + httpx + APScheduler） |
| AI 加工 | Ollama 本地模型（Qwen3.6-35B-A3B-UD-Q4_K_M） |
| 调度 | Python APScheduler（容器内运行） |

### 数据源决策

Phase 1 接入 3 个数据源：

| 数据源 | 类型 | URL |
|--------|------|-----|
| TechCrunch AI | RSS | `https://techcrunch.com/category/artificial-intelligence/feed/` |
| The Verge AI | RSS | `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml` |
| Hacker News | Algolia API | `https://hn.algolia.com/api/v1/search?tags=story&dateRange=past24hours` |

所有来源均需支持独立启用/禁用和失败重试。无官方 RSS 的网站不得虚构地址。

### 数据处理流程决策

采集管道分为五个步骤：

1. **采集**：从 RSS 或 API 读取标题、描述、链接、来源、发布时间。设置请求超时、重试和频率限制。
2. **标准化**：统一 UTC 存储时间，规范化 URL，提取原始语言，区分发布时间与采集时间。
3. **去重与聚类**：URL 精确匹配去重 + 标题编辑距离/关键词重叠去重。同一事件的不同报道保留为独立 Article，在详情中关联为 Cluster。
4. **AI 加工**：调用 Ollama 生成结构化输出（headline_zh、summary_zh、why_it_matters_zh、category、tags、importance_score、source_confidence、related_entities）。使用 Schema 验证输出，验证失败时保留原始新闻。
5. **每日简报**：每天生成一次，包含 trend_summary（趋势概述）、highlight_events（5-8 条重点）、dev_focus（3-5 条开发者关注）。简报必须基于真实入库数据生成，模型不得编造新闻。

### 数据库决策

使用 SQLite，包含以下核心表：

- `sources`：数据源配置（id, name, feed_url, feed_type, enabled, last_success, last_error, created_at, updated_at）
- `articles`：原始新闻（id, source_url, source_name, raw_title, raw_description, fetched_at, language, created_at, updated_at）
- `processed_articles`：AI 加工后的新闻（id, article_id [FK], headline_zh, summary_zh, why_it_matters_zh, category, tags [JSON], importance_score, source_confidence, related_entities [JSON], generated_at, generation_status [pending/success/failed]）
- `clusters`：事件聚类（id, representative_article_id [FK], cluster_type [title_similarity/url_match], created_at）
- `cluster_members`：聚类成员（cluster_id [FK], article_id [FK]）
- `daily_briefs`：每日简报（id, date, trend_summary, highlights [JSON], dev_focus [JSON], generated_at, generation_status）
- `pipeline_runs`：采集任务日志（id, started_at, completed_at, status, articles_fetched, articles_new, articles_updated, source_results [JSON], created_at）

所有表具备唯一约束、索引和幂等写入机制。

### AI 加工决策

- **模型**：Qwen3.6-35B-A3B-UD-Q4_K_M（MoE，35B 总参数，3B 激活参数），通过 Ollama 本地运行。
- **输出格式**：结构化 JSON，包含 headline_zh、summary_zh（80-150 字）、why_it_matters_zh、category（枚举）、tags（字符串数组）、importance_score（0-100）、source_confidence（0-1）、related_entities（字符串数组）。
- **验证机制**：使用 JSON Schema 验证模型输出。验证失败时保留原始新闻，标记 generation_status 为 failed，前端显示"摘要待生成"。
- **事实约束**：AI 生成的标题、摘要和评分必须基于原始新闻内容。信息不足时不得编造。
- **区分标注**：AI 生成的内容（headline_zh、summary_zh）与原始数据（raw_title）在前端和数据库中明确区分。

### 前端决策

- **路由**：`/`（今日简报 + 最新动态）、`/articles`（全部资讯）、`/article/[id]`（新闻详情）、`/collections`（收藏页）
- **导航**：AI Radar Logo + 今日简报 + 最新资讯 + 收藏 + 搜索 + 主题切换
- **布局**：桌面端主内容 + 侧栏，移动端单栏
- **设计语言**：现代、简洁、克制，参考 Linear/Vercel Dashboard 的信息组织方式。默认浅色 + 深色主题。统一 spacing、typography、radius、color tokens。
- **状态处理**：Loading、Empty、Error、Stale Data 状态均需有明确的 UI 反馈。
- **收藏**：localStorage 存储，结构 `{ article_id, collected_at }`。
- **数据真实性**：所有数量必须来自数据库真实查询，不使用演示数字。

## Testing Decisions

### 测试原则

- 测试外部行为，不测试内部实现细节。
- 优先测试有清晰输入输出的模块边界（seam）。
- 新增测试以最高层级（集成测试）优先，单元测试覆盖核心逻辑。

### 测试分层与模块

| 层级 | 模块 | 测试内容 | 框架 |
|------|------|----------|------|
| 单元测试 | Collector：解析器 | RSS/HTML 解析正确性、字段提取、异常处理 | Python pytest |
| 单元测试 | Collector：去重器 | URL 去重、标题相似度计算、边缘情况（空标题、特殊字符） | Python pytest |
| 单元测试 | Collector：评分器 | importance_score 计算逻辑（技术影响 30% + 相关性 25% + 来源 20% + 时效 15% + 热度 10%） | Python pytest |
| 单元测试 | Web：API 路由 | API 返回数据格式正确性、分页、排序、筛选 | Next.js testing library / Vitest |
| 集成测试 | Collector → SQLite | 完整采集流程：从 RSS 获取 → 解析 → 去重 → AI 加工 → 入库 | Python pytest + 内存 SQLite |
| 集成测试 | SQLite → Web API | 数据库数据通过 API 正确返回，包含关联的 Cluster 成员 | Playwright / Next.js testing library |
| E2E 测试 | 核心用户流程 | 采集 → 首页展示 → 分类筛选 → 详情 → 收藏 | Playwright |

### 模拟策略

- **Ollama**：集成测试中使用 mock Ollama 服务器（返回预定义 JSON），确保 AI 加工逻辑可独立测试，不依赖实际模型。
- **RSS 源**：使用本地 fixture 文件模拟 RSS 响应，确保解析器测试不依赖外部网络。
- **Hacker News API**：使用固定 JSON fixture 模拟 API 响应。
- **前端交互**：Playwright E2E 测试使用真实 Next.js 实例，API 层 mock 数据库查询。

### 验收标准

- 构建、类型检查（tsc --noEmit）、核心测试通过。
- Collector 单元测试覆盖率 ≥ 80%。
- E2E 测试覆盖核心用户流程（采集、展示、筛选、收藏）。
- 所有测试在 Docker 环境中可复现（不依赖外部网络）。

## Out of Scope

以下功能不在第一版范围内：

- **用户注册与账户系统**：收藏功能使用 localStorage，不保留后端用户数据结构。
- **用户认证与权限**：无登录、无角色管理。
- **评论与社区功能**：无讨论、无评论、无社交功能。
- **个性化推荐**：无用户画像、无推荐算法、无个性化内容流。
- **推送通知**：无邮件推送、Telegram 推送等。
- **周报功能**：无每周趋势汇总。
- **向量搜索 / 语义搜索**：搜索仅基于关键词和全文匹配。
- **多语言支持**：界面和新闻内容均为简体中文。
- **后端多设备同步**：收藏仅限当前浏览器的 localStorage。
- **全文存储**：不存储新闻完整内容，仅存储标题、描述摘要和元信息。
- **图片/视频内容**：不处理多媒体新闻内容。
- **RSS 订阅输出**：不对外提供 AI Radar 自己的 RSS 订阅。
- **第三方集成**：无 Slack/Discord/Webhook 集成。
- **微服务/消息队列/向量数据库**：不使用不必要的中间件。

## Further Notes

### 约束与注意事项

1. **磁盘空间**：C 盘仅剩 43.5GB。项目代码位于 G 盘，Docker volume 必须通过绝对路径挂载到 G 盘。
2. **Ollama 容器**：需要在 Docker 中运行 Ollama 容器并拉取 Qwen3.6-35B-A3B 模型。需要 GPU 支持 Docker（NVIDIA Container Toolkit）。
3. **AI 输出容错**：AI 加工失败（模型超时、输出格式错误、网络问题）不得导致原始新闻丢失。failed 状态的新闻仍然展示，仅标注"摘要待生成"。
4. **数据真实性**：网站必须展示真实的外部新闻数据，不得使用静态 Mock 数据作为默认状态。
5. **幂等写入**：重复执行采集任务不得产生重复新闻。
6. **外部输入安全**：所有新闻内容视为不可信输入。限制外部 URL 协议和域名，防范 SSRF。AI 生成的内容需与原始数据区分展示。
7. **API Key 安全**：如后续接入外部 API，Key 只存储在服务端环境变量，不暴露到前端。
8. **采集失败隔离**：单个数据源采集失败不应阻塞其他数据源的处理。
9. **时区**：数据存储 UTC，展示使用 Asia/Singapore。

### Phase 演进规划

- **Phase 1**：真实数据闭环。RSS/API 采集、SQLite 入库、基础去重、最小可用资讯列表。验收：至少 3 个真实信息源可稳定入库、展示、跳转原文。
- **Phase 2**：AI 情报加工。分类、翻译、摘要、重要性排序、事件聚类、每日简报。验收：新闻正确关联信源，重复事件归并，AI 输出有失败降级。
- **Phase 3**：完整用户界面。响应式主页、筛选、搜索、详情、收藏、主题切换、空状态。验收：桌面与移动端均正常使用。
- **Phase 4**：自动化与交付。调度验证、健康检查、测试报告、部署文档。验收：按 README 可独立部署。

### 领域模型核心概念

本项目使用以下核心领域概念（详见 GLOSSARY.md）：

- **Article** → 原始新闻条目（从数据源采集）
- **Processed Article** → 经过 AI 加工的 enriched 版本
- **Source** → 外部信息提供者
- **Cluster** → 同一事件的多个报道聚类
- **Daily Brief** → 每日结构化简报
- **Pipeline Run** → 采集任务执行记录
- **Collection** → 用户本地收藏
