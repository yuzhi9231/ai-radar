import { ArticleCard } from "@/components/article-card";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getAllArticles, getTodayBrief } from "@/lib/api-client";
import { formatDate } from "@/lib/utils";

export default async function HomePage() {
	const brief = await getTodayBrief();
	const allArticles = await getAllArticles();
	const today = new Date().toISOString().split("T")[0];

	// Show up to 12 most recent articles in the waterfall grid
	const recentArticles = allArticles.slice(0, 12);

	return (
		<div className="space-y-8">
			{/* Hero / Brief Section */}
			<div className="space-y-1">
				<h1 className="text-3xl font-bold tracking-tight">今日简报</h1>
				<p className="text-sm text-muted-foreground">{formatDate(today)}</p>
			</div>

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
							{brief.highlights.map((h: any, i: number) => (
								<Card key={i}>
									<CardHeader>
										<CardTitle className="text-base">{h.headline}</CardTitle>
									</CardHeader>
									<CardContent>
										<p className="text-sm text-muted-foreground">{h.summary}</p>
										<div className="mt-2 flex flex-wrap gap-1">
											{(h.tags || []).map((tag: string) => (
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
							{brief.dev_focus.map((d: any, i: number) => (
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

				{recentArticles.length === 0 ? (
					<Card>
						<CardContent className="pt-6 text-center text-sm text-muted-foreground">
							暂无文章，等待数据采集...
						</CardContent>
					</Card>
				) : (
					<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
						{recentArticles.map((article: any) => (
							<ArticleCard key={article.id} article={article} />
						))}
					</div>
				)}
			</div>

			{/* Stats Bar */}
			{allArticles.length > 0 && (
				<div className="flex flex-wrap items-center gap-4 rounded-lg bg-muted p-4 text-sm">
					<span>
						共 <strong className="text-foreground">{allArticles.length}</strong>{" "}
						篇 文章
					</span>
					<span className="text-muted-foreground">|</span>
					<span className="flex flex-wrap items-center gap-1">
						来源:{" "}
						{Array.from(new Set(allArticles.map((a: any) => a.source_name)))
							.slice(0, 10)
							.map((s: string) => (
								<Badge key={s} variant="secondary" className="text-[10px]">
									{s}
								</Badge>
							))}
					</span>
				</div>
			)}
		</div>
	);
}
