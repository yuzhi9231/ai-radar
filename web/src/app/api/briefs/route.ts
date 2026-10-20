import { NextResponse } from "next/server";
import Database from "better-sqlite3";

const dbPath = process.env.DATABASE_PATH || "/data/ai-radar.db";
const db = new Database(dbPath, { readonly: true });
db.pragma("journal_mode = WAL");

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const date = searchParams.get("date");

    const row = db.prepare(
      "SELECT * FROM daily_briefs WHERE date = ? ORDER BY generated_at DESC LIMIT 1"
    ).get(date || new Date().toISOString().split("T")[0]) as any;

    if (!row) {
      return NextResponse.json({ brief: null });
    }

    const brief = {
      ...row,
      highlights: row.highlights ? JSON.parse(row.highlights) : [],
      dev_focus: row.dev_focus ? JSON.parse(row.dev_focus) : [],
    };

    return NextResponse.json({ brief });
  } catch (err) {
    console.error("GET /api/briefs error:", err);
    return NextResponse.json(
      { error: "Failed to fetch brief" },
      { status: 500 }
    );
  }
}
