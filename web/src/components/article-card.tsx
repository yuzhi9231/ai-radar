import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatRelativeTime } from "@/lib/utils";

export interface DisplayArticle {
	id: string;
	source_url: string;
	source_name: string;
	raw_title: string;
	raw_description: string;
	fetched_at: string;
	source?: string;
	headline_zh?: string | null;
	summary_zh?: string | null;
	category?: string | null;
	tags?: string[] | null;
	importance_score?: number | null;
	generation_status?: string | null;
	error?: string | null;
}

export function ArticleCard({ article }: { article: DisplayArticle }) {
	// Only show AI output as AI output when the AI layer actually produced it
	const analysed = article.generation_status === "success";
	const title =
		analysed && article.headline_zh ? article.headline_zh : article.raw_title;
	const summary =
		analysed && article.summary_zh
			? article.summary_zh
			: article.raw_description;

	return (
		<Card className="flex h-full flex-col transition-shadow hover:shadow-md">
			<CardHeader className="pb-2">
				<CardTitle className="text-sm leading-tight">
					<a
						href={article.source_url}
						target="_blank"
						rel="noopener noreferrer"
						className="transition-colors hover:text-primary"
					>
						{title}
					</a>
				</CardTitle>
				<div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
					<span className="font-medium">{article.source_name}</span>
					<span>&middot;</span>
					<span>{formatRelativeTime(article.fetched_at)}</span>
				</div>
			</CardHeader>
			<CardContent className="flex-1 pt-0">
				{summary && (
					<p className="mb-2 text-xs leading-relaxed text-foreground/80 line-clamp-3">
						{summary}
					</p>
				)}
				{!analysed && article.error && (
					<p className="mb-2 text-[10px] leading-relaxed text-destructive line-clamp-2">
						{article.error}
					</p>
				)}
				<div className="flex items-center justify-between gap-2">
					<div className="flex flex-wrap gap-1">
						{analysed && article.tags && article.tags.length > 0 ? (
							article.tags.slice(0, 3).map((tag) => (
								<Badge key={tag} variant="secondary" className="text-[10px]">
									{tag}
								</Badge>
							))
						) : (
							<Badge
								variant={analysed ? "secondary" : "destructive"}
								className="text-[10px]"
								title={analysed ? undefined : article.error || "AI 处理失败"}
							>
								{analysed ? article.category || "general" : "未分析"}
							</Badge>
						)}
					</div>
					{analysed &&
						article.importance_score != null &&
						article.importance_score > 0 && (
							<span className="shrink-0 rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
								{article.importance_score}
							</span>
						)}
				</div>
			</CardContent>
		</Card>
	);
}
