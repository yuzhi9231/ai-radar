import { NextResponse } from "next/server";
import Database from "better-sqlite3";

const dbPath = process.env.DATABASE_PATH || "/data/ai-radar.db";
const db = new Database(dbPath, { readonly: true });
db.pragma("journal_mode = WAL");

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const row = db.prepare(`
      SELECT
        a.id, a.source_url, a.source_name, a.source,
        a.raw_title, a.raw_description, a.published_at, a.fetched_at, a.language,
        pa.headline_zh, pa.summary_zh, pa.why_it_matters_zh, pa.category,
        pa.tags, pa.importance_score, pa.generation_status
      FROM articles a
      LEFT JOIN processed_articles pa ON a.id = pa.article_id
      WHERE a.id = ?
    `).get(id) as any;

    if (!row) {
      return NextResponse.json({ error: "Article not found" }, { status: 404 });
    }

    const article = {
      ...row,
      tags: row.tags ? JSON.parse(row.tags) : [],
      source: row.source as string,
    };

    return NextResponse.json(article);
  } catch (err) {
    console.error("GET /api/articles/[id] error:", err);
    return NextResponse.json(
      { error: "Failed to fetch article" },
      { status: 500 }
    );
  }
}
