# AI Radar · 领域词汇表

> 最后更新：2026-10-20

## Article（新闻条目）
从数据源采集的原始新闻记录，包含标题、链接、来源、发布时间、原始内容等字段。是系统中最基本的信息单元。

**属性**：source_url（原文链接）、source_name（来源名称）、fetched_at（采集时间）、raw_title（原始标题）、raw_description（原始描述）

## Processed Article（处理后新闻条目）
Article 经过采集、去重、AI 加工后的 enriched 版本。包含中文标题、摘要、分类、评分等字段。

**属性**：headline_zh、summary_zh、why_it_matters_zh、category、tags、importance_score、generated_at

## Source（数据源）
外部信息提供者，如 RSS 订阅、API 接口等。每个 Source 有独立的启用/禁用状态和健康指标。

**属性**：feed_url、feed_type（rss/api）、enabled（布尔值）、last_success（上次成功时间）、last_error（最近错误信息）

## Daily Brief（每日简报）
系统每天生成的高级别 AI 领域摘要，包含趋势概述和 5-8 个重点事件，每条关联到具体的 Article。

**属性**：date、trend_summary、highlight_events（关联 Article 的列表）、dev_focus（关联 Article 的列表）、generated_at

## Pipeline Run（采集任务）
一次数据采集与处理的执行记录，记录开始时间、结束时间、成功/失败状态、处理的文章数量和涉及的数据源。

**属性**：started_at、completed_at、status（success/partial_failure/failed）、articles_fetched、articles_new、articles_updated、source_results（各源的状态）

## Collection（收藏）
用户标记为值得日后回顾的 Article，存储在本地（localStorage）。

**属性**：article_id、collected_at（前端时间戳）

## Ollama（本地 AI 服务）
本地运行的 AI 模型服务，通过 localhost API 提供 OpenAI 兼容接口。

**当前模型**：Qwen3.6-35B-A3B-UD-Q4_K_M（MoE：35B 总参数，3B 激活参数）
**端点**：http://ollama:11434（容器网络）或 http://host.docker.internal:11434（宿主机模式）

## Cluster（事件聚类）
多个报道同一事件的不同 Article 被聚类为一个 Cluster。第一版使用标题相似度进行浅聚类。

**属性**：cluster_id、representative_article（主报道）、member_article_ids（关联文章列表）、similarity_threshold
