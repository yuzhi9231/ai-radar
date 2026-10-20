import { ArticleGrid } from "@/components/article-grid";

export default function ArticlesPage() {
	return (
		<div className="space-y-4">
			<div className="flex items-center justify-between">
				<h1 className="text-2xl font-bold tracking-tight">全部文章</h1>
			</div>

			<ArticleGrid />
		</div>
	);
}
