import { NextResponse } from "next/server";
import Database from "better-sqlite3";

const dbPath = process.env.DATABASE_PATH || "/data/ai-radar.db";
const db = new Database(dbPath, { readonly: true });
db.pragma("journal_mode = WAL");

export async function GET() {
  try {
    const total = db.prepare("SELECT COUNT(*) as count FROM articles").get() as { count: number };
    const sources = db.prepare(
      "SELECT COUNT(*) as count FROM sources WHERE enabled = 1"
    ).get() as { count: number };
    const processed = db.prepare(
      "SELECT COUNT(*) as count FROM processed_articles WHERE generation_status = 'success'"
    ).get() as { count: number };
    const today = new Date().toISOString().split("T")[0];
    const todayCount = db.prepare(
      "SELECT COUNT(*) as count FROM articles WHERE date(fetched_at) = ?"
    ).get(today) as { count: number };

    return NextResponse.json({
      total_articles: total.count,
      enabled_sources: sources.count,
      processed_count: processed.count,
      today_count: todayCount.count,
    });
  } catch (err) {
    console.error("GET /api/stats error:", err);
    return NextResponse.json(
      { error: "Failed to fetch stats" },
      { status: 500 }
    );
  }
}
