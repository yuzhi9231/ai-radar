import { getAllArticles } from "@/lib/api-client";
import { ArticleCard } from "@/components/article-card";

export default async function ArticlesPage() {
	const articles = await getAllArticles();

	return (
		<div className="space-y-4">
			<div className="flex items-center justify-between">
				<h1 className="text-2xl font-bold tracking-tight">全部文章</h1>
				<span className="text-sm text-muted-foreground">
					共 {articles.length} 篇
				</span>
			</div>

			{articles.length === 0 ? (
				<div className="flex flex-col items-center justify-center py-20 text-center">
					<h1 className="text-2xl font-semibold text-foreground">暂无文章</h1>
					<p className="mt-2 text-sm text-muted-foreground">
						运行数据采集后将显示文章列表
					</p>
				</div>
			) : (
				<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{articles.map((article: any) => (
						<ArticleCard key={article.id} article={article} />
					))}
				</div>
			)}
		</div>
	);
}
