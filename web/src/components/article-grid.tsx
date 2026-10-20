"use client";

import { getAllArticles } from "@/lib/api-client";
import { useCallback, useEffect, useRef, useState } from "react";

import { ArticleCard } from "@/components/article-card";
import { ArticleFilterBar } from "@/components/article-filter-bar";
import { ArticleSkeleton } from "@/components/article-skeleton";
import { LoadMore } from "@/components/load-more";

interface Article {
	id: string;
	source_url: string;
	source_name: string;
	source: string;
	raw_title: string;
	raw_description: string;
	published_at: string;
	fetched_at: string;
	language: string;
	headline_zh: string;
	summary_zh: string;
	category: string;
	tags: string[];
	importance_score: number;
	generation_status: string;
}

interface ArticleGridProps {
	/** Server-rendered initial articles (can be empty). Used as fallback while client loads. */
	initialArticles?: Article[];
}

export function ArticleGrid({ initialArticles }: ArticleGridProps) {
	const hasLoadedRef = useRef(false);

	const [articles, setArticles] = useState<Article[]>(initialArticles || []);
	const [total, setTotal] = useState(initialArticles?.length || 0);
	const [filters, setFilters] = useState<{
		source: string | undefined;
		category: string | undefined;
		sort: "newest" | "oldest" | "importance";
	}>({ source: undefined, category: undefined, sort: "newest" });
	const [limit] = useState(12);
	const [offset, setOffset] = useState(initialArticles?.length || 0);
	const [loading, setLoading] = useState(initialArticles === undefined);
	const [isLoadingMore, setIsLoadingMore] = useState(false);

	const loadArticles = useCallback(
		async (f: typeof filters, l: number, o: number) => {
			const res = await getAllArticles({
				source: f.source,
				category: f.category,
				sort: f.sort,
				limit: l,
				offset: o,
			});
			return res;
		},
		[],
	);

	// Initial load (only once)
	useEffect(() => {
		if (hasLoadedRef.current) return;
		hasLoadedRef.current = true;

		const cancelled = false;
		setLoading(true);
		loadArticles(filters, limit, 0)
			.then((res) => {
				if (cancelled) return;
				setArticles(res.articles);
				setTotal(res.total);
				setOffset(res.articles.length);
			})
			.finally(() => {
				if (cancelled) return;
				setLoading(false);
			});
	}, [filters, limit, loadArticles]);

	const handleFilterChange = (newFilters: typeof filters) => {
		setFilters(newFilters);
		setOffset(0);
	};

	const handleLoadMore = async () => {
		setIsLoadingMore(true);
		try {
			const res = await loadArticles(filters, limit, offset);
			setArticles((prev) => [...prev, ...res.articles]);
			setTotal(res.total);
			setOffset(offset + res.articles.length);
		} finally {
			setIsLoadingMore(false);
		}
	};

	if (loading) {
		return <ArticleSkeleton count={limit} />;
	}

	return (
		<div className="space-y-6">
			<ArticleFilterBar onFilterChange={handleFilterChange} />

			{articles.length === 0 ? (
				<div className="py-12 text-center text-sm text-muted-foreground">
					没有匹配的文章
				</div>
			) : (
				<>
					<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
						{articles.map((article) => (
							<ArticleCard key={article.id} article={article} />
						))}
					</div>
					<LoadMore
						total={total}
						loaded={articles.length}
						limit={limit}
						onLoadMore={handleLoadMore}
					/>
				</>
			)}
		</div>
	);
}
