import { NextResponse } from "next/server";
import { getDb } from "@/lib/db";

export async function GET() {
  const db = getDb();
  if (!db) {
    return NextResponse.json([]);
  }

  try {
    const articles = db.prepare(`
      SELECT
        a.id, a.source_url, a.source_name, a.source,
        a.raw_title, a.raw_description, a.published_at, a.fetched_at, a.language,
        pa.headline_zh, pa.summary_zh, pa.category,
        pa.tags, pa.importance_score, pa.generation_status
      FROM articles a
      LEFT JOIN processed_articles pa ON a.id = pa.article_id
      ORDER BY a.fetched_at DESC
    `).all() as any[];

    // Parse JSON columns
    const result = articles.map((a) => ({
      ...a,
      tags: a.tags ? JSON.parse(a.tags) : [],
      source: a.source as string,
    }));

    return NextResponse.json(result);
  } catch (err) {
    console.error("GET /api/articles error:", err);
    return NextResponse.json(
      { error: "Failed to fetch articles" },
      { status: 500 }
    );
  }
}
