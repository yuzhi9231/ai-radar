import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getAllArticles } from "@/lib/api-client";
import { formatDate, formatRelativeTime, getInitials } from "@/lib/utils";

export default async function ArticlesPage() {
	const articles = await getAllArticles();

	if (articles.length === 0) {
		return (
			<div className="flex flex-col items-center justify-center py-20 text-center">
				<h1 className="text-2xl font-semibold text-foreground">暂无文章</h1>
				<p className="mt-2 text-sm text-muted-foreground">
					运行数据采集后将显示文章列表
				</p>
			</div>
		);
	}

	return (
		<div className="space-y-4">
			<div className="flex items-center justify-between">
				<h1 className="text-2xl font-bold tracking-tight">全部文章</h1>
				<span className="text-sm text-muted-foreground">
					共 {articles.length} 篇
				</span>
			</div>

			<div className="space-y-3">
				{articles.map((article: any) => (
					<Card key={article.id} className="transition-shadow hover:shadow-md">
						<CardHeader className="pb-3">
							<div className="flex items-start justify-between gap-3">
								<div className="space-y-1">
									<CardTitle className="text-base leading-tight">
										<a
											href={article.source_url}
											target="_blank"
											rel="noopener noreferrer"
											className="transition-colors hover:text-primary"
										>
											{article.headline_zh || article.raw_title}
										</a>
									</CardTitle>
									<div className="flex items-center gap-2 text-xs text-muted-foreground">
										<span className="font-medium">{article.source_name}</span>
										<span>&middot;</span>
										<span>{formatRelativeTime(article.fetched_at)}</span>
									</div>
								</div>
								<span className="shrink-0 rounded-md bg-muted px-2 py-1 text-xs font-medium text-muted-foreground">
									{article.source}
								</span>
							</div>
						</CardHeader>
						<CardContent className="pt-0">
							{article.summary_zh && (
								<p className="mb-2 text-sm text-foreground/80 line-clamp-2">
									{article.summary_zh}
								</p>
							)}
							<div className="flex items-center justify-between">
								<div className="flex flex-wrap gap-1">
									{article.tags && article.tags.length > 0 ? (
										article.tags.map((tag: string) => (
											<Badge key={tag} variant="secondary" className="text-xs">
												{tag}
											</Badge>
										))
									) : (
										<Badge variant="secondary" className="text-xs">
											{article.category || "general"}
										</Badge>
									)}
								</div>
								{article.importance_score > 0 && (
									<span className="text-xs text-muted-foreground">
										重要性: {article.importance_score}/10
									</span>
								)}
							</div>
						</CardContent>
					</Card>
				))}
			</div>
		</div>
	);
}
