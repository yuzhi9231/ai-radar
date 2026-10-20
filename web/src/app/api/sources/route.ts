import { NextResponse } from "next/server";
import { getDb } from "@/lib/db";

export async function GET() {
  const db = getDb();
  if (!db) {
    return NextResponse.json([]);
  }

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
