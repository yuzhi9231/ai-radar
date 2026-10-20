# AI Radar — Agent 工作指南

> 最后更新：2026-10-20

## 项目现状

- 阶段：Phase 1 集成测试阶段
- 代码：已完成 collector（Python）、web（Next.js）、Docker Compose、集成测试
- Git：已初始化，无远程，无提交
- 分支：`feature/integration-testing`（当前）

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

## 评审规则（本地模型约束）

**本项目运行在本地模型上，所有评审改为串行单代理执行：**

- 每次只做一项评审（代码标准 / 功能正确 / 安全性），**不要并行**
- **不使用子代理（sub-agent）**，当前代理独立完成
- 评审发现多个问题时，逐个列出并逐个修复
- 如需多个 skill 协作，按顺序依次调用，不并发

## CI/CD 故障排查指南

### 快速排查流程

```powershell
# 1. 查看最新 CI 运行
gh run list --repo yuzhi9231/ai-radar --limit 2

# 2. 查看失败 job 的详细日志（错误通常在末尾）
gh run view <run_id> --repo yuzhi9231/ai-radar --job <job_id> --log-failed 2>&1 | Select-Object -Last 80

# 3. 等待 CI 完成
Start-Sleep -Seconds 300; gh run view <run_id> --repo yuzhi9231/ai-radar --json conclusion,jobs
```

### 已知 CI 陷阱（已修复，但修复时反复踩坑）

| 陷阱 | 症状 | 正确做法 |
|------|------|----------|
| `npm ci --ignore-scripts` | `better-sqlite3` 原生绑定未编译 | 用 `npm install`（不传 `--ignore-scripts`），Ubuntu runner 有 C++ 工具链 |
| `mkdir -p /data` 在 CI runner | `permission denied` 或 `not found` | API 路由懒加载 DB，不存在时优雅返回空数据 |
| Next.js 静态生成 `onClick` 错误 | `Event handlers cannot be passed to Client Component pages` | 含事件处理器的组件必须提取到独立文件并加 `"use client"` |
| Docker `COPY --from=builder /app/public` | `"/app/public": not found` | `public` 目录必须存在，即使为空（`.gitkeep`） |
| Docker Compose 拉取 Ollama 超时 | `docker compose up` 超时 | `docker compose up --no-deps web collector` 跳过 Ollama |
| `git checkout HEAD~1 -- file` 推不到 GitHub | GitHub 上的 CI 仍是旧版本 | 改完文件后正常 commit + push，`checkout` 只是本地操作 |

### CI 修复循环（每次修复都走这个流程）

1. `gh run list` 找到最新运行 → 确认状态
2. `gh run view <id> --log-failed | Select-Object -Last 80` 定位错误
3. 分析错误 → 修改文件
4. `git add && git commit -m "fix(ci/...): <描述>"`
5. `git push origin main`
6. 等 30 秒 `gh run list` → 等 300 秒 `gh run view` 看结果
7. 如果还失败，回到步骤 2

### 分支工作流（所有修改必须走分支）

**所有修改——无论大小、代码还是文档——必须走短命分支，禁止直接改 main。**

```powershell
# 1. 先建分支（从 main 最新）
git -C "G:\AI早报\AI Radar" checkout main
git -C "G:\AI早报\AI Radar" pull origin main
git -C "G:\AI早报\AI Radar" checkout -b feature/<描述>

# 2. 在分支上做修改和提交
# （可以多次 commit，不需要完美）

# 3. 推分支 + 开 PR
git -C "G:\AI早报\AI Radar" push origin feature/<描述>
gh pr create --base main --head feature/<描述> --title "fix: <标题>" --body ""

# 4. 盯 CI（PR 上的 Checks）
gh pr checks <number> --repo yuzhi9231/ai-radar --watch
# 或
Start-Sleep -Seconds 300; gh run list --repo yuzhi9231/ai-radar --pr <number>

# 5. CI 通过后合并（squash）
gh pr merge <number> --squash --delete-branch

# 6. 收尾
git -C "G:\AI早报\AI Radar" checkout main
git -C "G:\AI早报\AI Radar" pull origin main
```

**例外**：纯 `.gitignore`、`.env.example` 等配置文件的微小调整可以直推 main，但首次此类修改也先走分支确认。
