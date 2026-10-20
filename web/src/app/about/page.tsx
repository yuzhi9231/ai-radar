import { AppVersion } from "@/components/app-version";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";

export default function AboutPage() {
	return (
		<div className="space-y-6">
			{/* Header */}
			<div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
				<div className="space-y-1">
					<h1 className="text-3xl font-bold tracking-tight">关于 AI Radar</h1>
					<p className="text-muted-foreground">
						自动化 AI 行业情报收集与智能摘要
					</p>
				</div>
				<AppVersion />
			</div>

			{/* Project Overview */}
			<Card>
				<CardHeader>
					<CardTitle>项目简介</CardTitle>
					<CardDescription>AI Radar 是什么、为什么构建</CardDescription>
				</CardHeader>
				<CardContent className="space-y-3 text-sm leading-relaxed text-foreground/80">
					<p>
						AI Radar 是一个本地部署、每日自动更新的 AI 行业新闻智能聚合 Web
						应用。它帮助 AI 从业者、开发者和产品设计者每天花 5–10 分钟，
						全面了解全球 AI
						领域发生了什么、哪些最重要、为什么重要，以及有哪些值得尝试的新技术。
					</p>
					<p>
						系统每日从 TechCrunch、The Verge、Hacker News 等权威来源自动采集 AI
						相关报道，通过本地 Ollama 模型（Qwen3.6-35B-A3B）进行中文标题生成、
						中文摘要、分类、重要性评分，最终生成结构化的每日简报。
					</p>
					<p className="text-muted-foreground">
						目标用户：AI
						从业者、开发者、产品观察者。核心理念：信息密度高、阅读效率高、
						可追溯信源。
					</p>
				</CardContent>
			</Card>

			{/* Data Sources */}
			<Card>
				<CardHeader>
					<CardTitle>数据来源</CardTitle>
					<CardDescription>Phase 1 接入 3 个经过验证的信息源</CardDescription>
				</CardHeader>
				<CardContent>
					<div className="space-y-3">
						{[
							{
								name: "TechCrunch AI",
								type: "RSS",
								url: "https://techcrunch.com/category/artificial-intelligence/feed/",
							},
							{
								name: "The Verge AI",
								type: "RSS",
								url: "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
							},
							{
								name: "Hacker News",
								type: "Algolia API",
								url: "https://hn.algolia.com/api/v1/search?tags=story&dateRange=past24hours",
							},
						].map((s) => (
							<div
								key={s.name}
								className="flex items-center justify-between rounded-lg border border-border p-3 transition-colors hover:bg-muted/50"
							>
								<div className="flex items-center gap-3">
									<Badge variant="outline">{s.type}</Badge>
									<span className="font-medium">{s.name}</span>
								</div>
								<a
									href={s.url}
									target="_blank"
									rel="noopener noreferrer"
									className="text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground"
								>
									查看源地址 →
								</a>
							</div>
						))}
					</div>
				</CardContent>
			</Card>

			{/* Tech Stack */}
			<Card>
				<CardHeader>
					<CardTitle>技术栈</CardTitle>
					<CardDescription>现代化全栈技术组合</CardDescription>
				</CardHeader>
				<CardContent>
					<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
						{[
							{
								name: "Next.js 15",
								desc: "App Router + TypeScript",
								detail: "SSR/SSG 混合渲染，服务端组件优先",
								icon: "▲",
							},
							{
								name: "Tailwind CSS",
								desc: "设计系统",
								detail: "原子化 CSS，响应式优先",
								icon: "◈",
							},
							{
								name: "shadcn/ui",
								desc: "组件库",
								detail: "Radix UI 基础，可定制",
								icon: "◆",
							},
							{
								name: "SQLite",
								desc: "单文件数据库",
								detail: "better-sqlite3 驱动，Docker volume 持久化",
								icon: "💾",
							},
							{
								name: "Python 3.12",
								desc: "采集服务",
								detail: "feedparser + httpx + APScheduler",
								icon: "🐍",
							},
							{
								name: "Ollama",
								desc: "本地 AI 推理",
								detail: "Qwen3.6-35B-A3B，支持 Mock 模式",
								icon: "🤖",
							},
						].map((t) => (
							<div
								key={t.name}
								className="rounded-lg border border-border bg-card p-4"
							>
								<div className="mb-2 flex items-center gap-2">
									<span className="text-lg">{t.icon}</span>
									<span className="font-semibold">{t.name}</span>
								</div>
								<p className="text-xs text-muted-foreground">{t.desc}</p>
								<p className="mt-1 text-xs text-muted-foreground/70">
									{t.detail}
								</p>
							</div>
						))}
					</div>
				</CardContent>
			</Card>

			{/* Deployment Guide */}
			<Card>
				<CardHeader>
					<CardTitle>本地部署指南</CardTitle>
					<CardDescription>
						一键启动全部服务（需 Docker Desktop）
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="space-y-3 text-sm">
						<div className="flex gap-3">
							<span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
								1
							</span>
							<div>
								<p className="font-medium">安装 Docker Desktop</p>
								<p className="text-muted-foreground">
									确保 Docker 引擎正在运行。Ollama 容器需要 GPU 支持（NVIDIA
									Container Toolkit）。
								</p>
							</div>
						</div>
						<div className="flex gap-3">
							<span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
								2
							</span>
							<div>
								<p className="font-medium">克隆并进入项目</p>
								<pre className="mt-1 rounded bg-muted p-2 text-xs">
									{`git clone https://github.com/yuzhi9231/ai-radar.git
cd "G:\\AI早报\\AI Radar"`}
								</pre>
							</div>
						</div>
						<div className="flex gap-3">
							<span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
								3
							</span>
							<div>
								<p className="font-medium">启动服务</p>
								<pre className="mt-1 rounded bg-muted p-2 text-xs">
									{"docker compose up -d"}
								</pre>
								<p className="mt-1 text-xs text-muted-foreground">
									首次启动会拉取镜像并下载 Ollama 模型（约 2GB）。Ollama
									启动较慢，请耐心等待。
								</p>
							</div>
						</div>
						<div className="flex gap-3">
							<span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
								4
							</span>
							<div>
								<p className="font-medium">访问应用</p>
								<p className="text-muted-foreground">
									打开浏览器访问{" "}
									<code className="rounded bg-muted px-1 text-xs">
										http://localhost:3000
									</code>
								</p>
							</div>
						</div>
					</div>
					<div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200">
						⚠️ 如果 Ollama 启动超时，可跳过 Ollama 使用 Mock AI 模式：
						<code className="ml-1 rounded bg-amber-100 px-1 dark:bg-amber-900">
							docker compose up --no-deps web collector
						</code>
					</div>
				</CardContent>
			</Card>

			{/* Privacy Statement */}
			<Card>
				<CardHeader>
					<CardTitle>隐私声明</CardTitle>
					<CardDescription>你的数据完全属于你</CardDescription>
				</CardHeader>
				<CardContent className="space-y-3 text-sm text-foreground/80">
					<div className="flex gap-3">
						<span className="text-xl">🔒</span>
						<div>
							<p className="font-medium">无用户数据收集</p>
							<p className="text-muted-foreground">
								AI Radar 不收集任何用户行为数据、不追踪访问记录、
								不依赖任何外部分析服务。你的阅读行为不会被第三方追踪。
							</p>
						</div>
					</div>
					<div className="flex gap-3">
						<span className="text-xl">💽</span>
						<div>
							<p className="font-medium">本地存储</p>
							<p className="text-muted-foreground">
								收藏功能使用浏览器 localStorage
								存储，仅保存在当前设备上，不会上传到任何服务器。
							</p>
						</div>
					</div>
					<div className="flex gap-3">
						<span className="text-xl">🏠</span>
						<p className="text-muted-foreground">
							整个系统可以完全本地运行，不依赖任何外部 API 服务（Ollama
							除外，模型运行在本地）。你可以将系统部署在内网中，完全隔离外部环境。
						</p>
					</div>
				</CardContent>
			</Card>

			{/* Architecture Overview */}
			<Card>
				<CardHeader>
					<CardTitle>架构概览</CardTitle>
					<CardDescription>数据处理从采集到展示的全流程</CardDescription>
				</CardHeader>
				<CardContent>
					<div className="grid gap-3 text-sm md:grid-cols-2 lg:grid-cols-4">
						{[
							{
								step: "01",
								title: "数据采集",
								desc: "RSS / Algolia API 定时抓取",
							},
							{
								step: "02",
								title: "AI 加工",
								desc: "中文标题、摘要、分类、评分",
							},
							{
								step: "03",
								title: "存储",
								desc: "SQLite 持久化，去重 + 聚类",
							},
							{
								step: "04",
								title: "展示",
								desc: "Web 端浏览、筛选、收藏",
							},
						].map((s) => (
							<div key={s.step} className="rounded-lg border border-border p-4">
								<span className="mb-2 block text-2xl font-bold text-primary">
									{s.step}
								</span>
								<p className="font-medium">{s.title}</p>
								<p className="text-muted-foreground">{s.desc}</p>
							</div>
						))}
					</div>
				</CardContent>
			</Card>

			{/* Footer */}
			<div className="text-center text-xs text-muted-foreground">
				AI Radar · MIT License · 2026
			</div>
		</div>
	);
}
