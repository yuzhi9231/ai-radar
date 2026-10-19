# AI Radar — Agent 工作指南

> 最后更新：2026-10-20

## 项目现状

- 阶段：Phase 1 前（仅设计文档）
- 代码：未开始
- Git：已初始化，无远程，无提交

## 关键约束

- **C 盘仅剩 ~43GB，所有数据必须放 G 盘**：Docker volume、SQLite 数据库、Ollama 模型数据全部挂载到 G 盘路径。
- **项目根目录**：`G:\AI早报\AI Radar`
- **磁盘路径注意**：PowerShell 中中文路径需用双引号包裹，如 `cd "G:\AI早报\AI Radar"`。

## 核心决策（不可在 Phase 1 推翻）

1. **架构**：Docker Compose Monorepo（web + collector + ollama），新机器 `docker compose up -d` 启动。
2. **前端**：Next.js 15 App Router + TypeScript + Tailwind + shadcn/ui。
3. **采集服务**：Python 3.12+，feedparser + httpx + APScheduler。
4. **数据库**：SQLite（单文件，Docker volume 持久化到 G 盘）。
5. **AI 模型**：Ollama 本地运行 Qwen3.6-35B-A3B，通过 OpenAI 兼容 API。
6. **数据源**（Phase 1 仅 3 个）：TechCrunch AI RSS、The Verge AI RSS、Hacker News Algolia API。
7. **去重**：URL 精确匹配 + 标题编辑距离，不做语义聚类。
8. **收藏**：localStorage，无后端用户系统。
9. **采集时间**：每天 10:00 + 15:00（Asia/Singapore）。

## 工作顺序

按 `GLOSSARY.md` → `docs/ADRs.md` → `docs/SPEC.md` 的顺序阅读。  
Phase 1 开发顺序：collector 数据流 → SQLite schema → web 展示层 → Docker 编排。

## 禁止事项

- 不引入微服务、消息队列、向量数据库、用户认证系统。
- 不虚构任何数据源 RSS 地址。
- 不使用静态 Mock 数据作为默认展示。
- AI 加工失败不得导致原始新闻丢失。

## 已有文件

| 文件 | 用途 |
|------|------|
| `GLOSSARY.md` | 领域词汇表（Article、Source、Daily Brief 等） |
| `docs/ADRs.md` | 10 条设计决策记录 |
| `docs/SPEC.md` | 完整规格文档 + 15 条用户故事 + 测试方案 |
