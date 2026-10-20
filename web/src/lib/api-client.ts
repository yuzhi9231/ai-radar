/** Server-side API client that talks to the Next.js API routes. */

const BASE = "/api";

interface ArticleFilters {
	source?: string;
	category?: string;
	sort?: "newest" | "oldest" | "importance";
	limit?: number;
	offset?: number;
}

async function json<T>(url: string): Promise<T> {
	const res = await fetch(`${BASE}${url}`, { cache: "no-store" });
	if (!res.ok) {
		throw new Error(`API ${res.status}: ${res.statusText}`);
	}
	return res.json();
}

export async function getAllArticles(
	filters?: ArticleFilters,
): Promise<{ articles: any[]; total: number; limit: number; offset: number }> {
	if (!filters) {
		return json<{
			articles: any[];
			total: number;
			limit: number;
			offset: number;
		}>("/articles");
	}
	const params = new URLSearchParams();
	if (filters.source) params.set("source", filters.source);
	if (filters.category) params.set("category", filters.category);
	if (filters.sort) params.set("sort", filters.sort);
	if (filters.limit) params.set("limit", String(filters.limit));
	if (filters.offset) params.set("offset", String(filters.offset));
	return json<{
		articles: any[];
		total: number;
		limit: number;
		offset: number;
	}>(`/articles?${params.toString()}`);
}

export async function getArticleById(id: string): Promise<any> {
	return json<any>(`/articles/${id}`);
}

export async function getSources(): Promise<any[]> {
	return json<any[]>("/sources");
}

export async function getStats(): Promise<any> {
	return json<any>("/stats");
}

export async function getTodayBrief(): Promise<any | null> {
	const today = new Date().toISOString().split("T")[0];
	const data = await json<any>(`/briefs?date=${today}`);
	return data.brief || null;
}
