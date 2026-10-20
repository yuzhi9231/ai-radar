/**
 * Integration tests for AI Radar web API client.
 * Run with: npx jest tests/  (install jest + @testing-library/react-hooks first)
 *
 * For Phase 1, these are smoke tests that verify the API client
 * constructs correct URLs and handles responses.
 */

import {
	getAllArticles,
	getArticleById,
	getSources,
	getStats,
	getTodayBrief,
} from "@/lib/api-client";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe("API Client", () => {
	beforeEach(() => {
		mockFetch.mockReset();
	});

	describe("getAllArticles", () => {
		it("should fetch from /api/articles", async () => {
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: async () => ({
					articles: [
						{ id: "abc123", raw_title: "Test Article", source: "techcrunch" },
					],
					total: 1,
					limit: 1,
					offset: 0,
				}),
			});

			const result = await getAllArticles();
			expect(mockFetch).toHaveBeenCalledWith(
				"/api/articles",
				expect.objectContaining({ cache: "no-store" }),
			);
			expect(result.articles).toHaveLength(1);
			expect(result.articles[0].raw_title).toBe("Test Article");
		});

		it("should throw on error response", async () => {
			mockFetch.mockResolvedValueOnce({
				ok: false,
				status: 500,
				statusText: "Internal Server Error",
			});

			await expect(getAllArticles()).rejects.toThrow("API 500");
		});

		it("should pass filter params to API", async () => {
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: async () => ({
					articles: [],
					total: 0,
					limit: 10,
					offset: 0,
				}),
			});

			await getAllArticles({ source: "techcrunch", sort: "newest", limit: 5 });
			expect(mockFetch).toHaveBeenCalledWith(
				"/api/articles?source=techcrunch&sort=newest&limit=5",
				expect.any(Object),
			);
		});
	});

	describe("getArticleById", () => {
		it("should fetch specific article", async () => {
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: async () => ({ id: "abc123", raw_title: "Specific Article" }),
			});

			const article = await getArticleById("abc123");
			expect(mockFetch).toHaveBeenCalledWith(
				"/api/articles/abc123",
				expect.any(Object),
			);
			expect(article.id).toBe("abc123");
		});
	});

	describe("getSources", () => {
		it("should fetch sources", async () => {
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: async () => [
					{ id: "techcrunch", name: "TechCrunch AI" },
					{ id: "theverge", name: "The Verge AI" },
					{ id: "hn", name: "Hacker News" },
				],
			});

			const sources = await getSources();
			expect(sources).toHaveLength(3);
		});
	});

	describe("getStats", () => {
		it("should fetch statistics", async () => {
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: async () => ({
					total_articles: 42,
					enabled_sources: 3,
					processed_count: 38,
					today_count: 5,
				}),
			});

			const stats = await getStats();
			expect(stats.total_articles).toBe(42);
			expect(stats.enabled_sources).toBe(3);
		});
	});

	describe("getTodayBrief", () => {
		it("should fetch today's brief", async () => {
			const today = new Date().toISOString().split("T")[0];
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: async () => ({
					brief: {
						date: today,
						trend_summary: "AI continues to advance rapidly",
						highlights: [],
						dev_focus: [],
					},
				}),
			});

			const brief = await getTodayBrief();
			expect(mockFetch).toHaveBeenCalledWith(
				`/api/briefs?date=${today}`,
				expect.any(Object),
			);
			expect(brief.trend_summary).toBe("AI continues to advance rapidly");
		});

		it("should return null when no brief exists", async () => {
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: async () => ({ brief: null }),
			});

			const brief = await getTodayBrief();
			expect(brief).toBeNull();
		});
	});
});
