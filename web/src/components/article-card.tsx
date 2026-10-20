import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatRelativeTime } from "@/lib/utils";

export function ArticleCard({ article }: { article: any }) {
	const title = article.headline_zh || article.raw_title;
	const summary = article.summary_zh || article.raw_description || "";

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
				<div className="flex items-center justify-between gap-2">
					<div className="flex flex-wrap gap-1">
						{article.tags && article.tags.length > 0 ? (
							article.tags.slice(0, 3).map((tag: string) => (
								<Badge key={tag} variant="secondary" className="text-[10px]">
									{tag}
								</Badge>
							))
						) : (
							<Badge variant="secondary" className="text-[10px]">
								{article.category || "general"}
							</Badge>
						)}
					</div>
					{article.importance_score != null && article.importance_score > 0 && (
						<span className="shrink-0 rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
							{article.importance_score}
						</span>
					)}
				</div>
			</CardContent>
		</Card>
	);
}
