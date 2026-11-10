import type { Article } from "@/components/article-grid";
import { ArticleGrid } from "@/components/article-grid";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
	getArticles,
	getBriefByDate,
	getLatestBrief,
	getLatestRun,
	getStats,
} from "@/lib/db";
import { dataAgeHours, parseJsonArray, parseObjectArray } from "@/lib/parse";
import { formatDate, runStatusLabel } from "@/lib/utils";

interface BriefItem {
	headline: string;
	summary: string;
	tags: string[];
}

interface Brief {
	date: string;
	trend_summary: string;
	highlights: BriefItem[];
	dev_focus: BriefItem[];
	generation_status: string;
}

function briefItems(value: unknown): BriefItem[] {
	return parseObjectArray(value).map((item) => ({
		headline: String(item.headline ?? ""),
		summary: String(item.summary ?? ""),
		tags: Array.isArray(item.tags) ? (item.tags as string[]) : [],
	}));
}

export default async function HomePage() {
	const today = new Date().toISOString().split("T")[0];

	// Read the database directly: a server component fetching its own API route
	// needs a base URL it does not have
	const rawBrief = getBriefByDate(today) ?? getLatestBrief();
	const brief: Brief | null = rawBrief
		? {
				date: String(rawBrief.date ?? today),
				trend_summary: String(rawBrief.trend_summary ?? ""),
				highlights: briefItems(rawBrief.highlights),
				dev_focus: briefItems(rawBrief.dev_focus),
				generation_status: String(rawBrief.generation_status ?? ""),
			}
		: null;

	const rows = getArticles();
	const articles: Article[] = rows.map((row) => ({
		id: String(row.id),
		source_url: String(row.source_url),
		source_name: String(row.source_name),
		source: String(row.source),
		raw_title: String(row.raw_title),
		raw_description: String(row.raw_description ?? ""),
		published_at: String(row.published_at),
		fetched_at: String(row.fetched_at),
		language: String(row.language),
		headline_zh: String(row.headline_zh ?? ""),
		summary_zh: String(row.summary_zh ?? ""),
		category: String(row.category ?? "general"),
		tags: parseJsonArray(row.tags),
		importance_score: Number(row.importance_score ?? 0),
		generation_status: String(row.generation_status ?? "pending"),
		error: (row.error as string | null) ?? null,
	}));

	const stats = getStats();
	const run = getLatestRun();
	const ageHours = dataAgeHours(stats.last_fetched_at);

	return (
		<div className="space-y-8">
			{/* Hero / Brief Section */}
			<div className="space-y-1">
				<h1 className="text-3xl font-bold tracking-tight">今日简报</h1>
				<p className="text-sm text-muted-foreground">{formatDate(today)}</p>
			</div>

			{ageHours !== null && ageHours > 24 && (
				<Card className="border-destructive/40">
					<CardContent className="pt-6 text-sm text-muted-foreground">
						数据最后采集于{" "}
						{formatDate(String(stats.last_fetched_at).split("T")[0])}（
						{ageHours} 小时前），尚未运行新的采集。
					</CardContent>
				</Card>
			)}

			{brief ? (
				<>
					{/* Trend Summary */}
					{brief.trend_summary && (
						<Card>
							<CardHeader>
								<CardTitle>趋势摘要</CardTitle>
							</CardHeader>
							<CardContent>
								<p className="whitespace-pre-wrap leading-relaxed text-foreground/90">
									{brief.trend_summary}
								</p>
							</CardContent>
						</Card>
					)}

					{/* Highlights */}
					{brief.highlights.length > 0 && (
						<div className="space-y-3">
							<h2 className="text-xl font-semibold">精选文章</h2>
							{brief.highlights.map((h, i) => (
								<Card key={i}>
									<CardHeader>
										<CardTitle className="text-base">{h.headline}</CardTitle>
									</CardHeader>
									<CardContent>
										<p className="text-sm text-muted-foreground">{h.summary}</p>
										<div className="mt-2 flex flex-wrap gap-1">
											{h.tags.map((tag) => (
												<Badge
													key={tag}
													variant="secondary"
													className="text-xs"
												>
													{tag}
												</Badge>
											))}
										</div>
									</CardContent>
								</Card>
							))}
						</div>
					)}

					{/* Developer Focus */}
					{brief.dev_focus.length > 0 && (
						<div className="space-y-3">
							<h2 className="text-xl font-semibold">开发者关注</h2>
							{brief.dev_focus.map((d, i) => (
								<Card key={i}>
									<CardHeader>
										<CardTitle className="text-base">{d.headline}</CardTitle>
									</CardHeader>
									<CardContent>
										<p className="text-sm text-muted-foreground">{d.summary}</p>
									</CardContent>
								</Card>
							))}
						</div>
					)}
				</>
			) : (
				<Card>
					<CardContent className="pt-6 text-center text-sm text-muted-foreground">
						数据采集完成后将自动生成本日 AI 行业简报
					</CardContent>
				</Card>
			)}

			{/* Recent Articles Waterfall Grid */}
			<div className="space-y-3">
				<div className="flex items-center justify-between">
					<h2 className="text-xl font-semibold">最新发布</h2>
					<a
						href="/articles"
						className="text-sm text-muted-foreground transition-colors hover:text-foreground"
					>
						查看全部 →
					</a>
				</div>

				<ArticleGrid initialArticles={articles} />
			</div>

			{/* Stats Bar */}
			{(Number(stats.total_articles) > 0 || run) && (
				<div className="flex flex-wrap items-center gap-4 rounded-lg bg-muted p-4 text-sm">
					<span>
						共{" "}
						<strong className="text-foreground">{stats.total_articles}</strong>{" "}
						篇 文章
					</span>
					<span className="text-muted-foreground">|</span>
					<span>
						已分析{" "}
						<strong className="text-foreground">{stats.processed_count}</strong>
					</span>
					<span className="text-muted-foreground">|</span>
					<span
						className={Number(stats.failed_count) > 0 ? "text-destructive" : ""}
					>
						未分析{" "}
						<strong className="text-foreground">{stats.failed_count}</strong>
					</span>
					<span className="text-muted-foreground">|</span>
					<span className="flex flex-wrap items-center gap-1">
						来源:{" "}
						{Array.from(new Set(articles.map((a) => a.source_name)))
							.slice(0, 10)
							.map((s) => (
								<Badge key={s} variant="secondary" className="text-[10px]">
									{s}
								</Badge>
							))}
					</span>
					{run && (
						<span className="flex flex-wrap items-center gap-1">
							最近运行:{" "}
							<strong className="text-foreground">
								{runStatusLabel(run.status)}
							</strong>{" "}
							<span className="text-muted-foreground">
								{run.articles_fetched} 抓取 / {run.articles_new} 新增 /{" "}
								{run.articles_processed} 分析 / {run.articles_failed} 失败
							</span>
							{run.completed_at === null && (
								<Badge variant="secondary" className="text-[10px]">
									未完成
								</Badge>
							)}
						</span>
					)}
				</div>
			)}
		</div>
	);
}
