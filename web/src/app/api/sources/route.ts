import { NextResponse } from "next/server";
import Database from "better-sqlite3";

const dbPath = process.env.DATABASE_PATH || "/data/ai-radar.db";
const db = new Database(dbPath, { readonly: true });
db.pragma("journal_mode = WAL");

export async function GET() {
  try {
    const sources = db.prepare("SELECT * FROM sources ORDER BY name").all() as any[];
    return NextResponse.json(sources);
  } catch (err) {
    console.error("GET /api/sources error:", err);
    return NextResponse.json(
      { error: "Failed to fetch sources" },
      { status: 500 }
    );
  }
}
