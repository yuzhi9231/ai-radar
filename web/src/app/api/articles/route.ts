import { getDb } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
	const db = getDb();
	if (!db) {
		return NextResponse.json([]);
	}

	const { searchParams } = new URL(req.url);
	const source = searchParams.get("source");
	const category = searchParams.get("category");
	const sort = searchParams.get("sort") || "newest";
	const limit = Math.min(parseInt(searchParams.get("limit") || "20"), 50);
	const offset = parseInt(searchParams.get("offset") || "0");

	try {
		let query = `
      SELECT
        a.id, a.source_url, a.source_name, a.source,
        a.raw_title, a.raw_description, a.published_at, a.fetched_at, a.language,
        pa.headline_zh, pa.summary_zh, pa.category,
        pa.tags, pa.importance_score, pa.generation_status
      FROM articles a
      LEFT JOIN processed_articles pa ON a.id = pa.article_id
    `;
		const params: any[] = [];
		const whereClauses: string[] = [];

		if (source) {
			whereClauses.push("a.source = ?");
			params.push(source);
		}
		if (category) {
			whereClauses.push("pa.category = ?");
			params.push(category);
		}
		if (whereClauses.length > 0) {
			query += " WHERE " + whereClauses.join(" AND ");
		}

		switch (sort) {
			case "oldest":
				query += " ORDER BY a.fetched_at ASC";
				break;
			case "importance":
				query += " ORDER BY pa.importance_score DESC, a.fetched_at DESC";
				break;
			default:
				query += " ORDER BY a.fetched_at DESC";
		}

		query += " LIMIT ? OFFSET ?";
		params.push(limit, offset);

		// Count total (without LIMIT/OFFSET, with filter params only)
		const filterParams = params.slice(0, -2) as any[];
		let totalQuery = `SELECT COUNT(*) as count FROM articles a`;
		if (whereClauses.length > 0) {
			totalQuery += " WHERE " + whereClauses.join(" AND ");
		}
		const total = db.prepare(totalQuery).get(...filterParams) as { count: number };

		const articles = db.prepare(query).all(...params) as any[];

		// Parse JSON columns
		const result = articles.map((a) => ({
			...a,
			tags: a.tags ? JSON.parse(a.tags) : [],
			source: a.source as string,
		}));

		return NextResponse.json({
			articles: result,
			total: total.count,
			limit,
			offset,
		});
	} catch (err) {
		console.error("GET /api/articles error:", err);
		return NextResponse.json(
			{ error: "Failed to fetch articles" },
			{ status: 500 },
		);
	}
}
