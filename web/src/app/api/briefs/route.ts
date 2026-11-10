import { getDb } from "@/lib/db";
import { parseObjectArray } from "@/lib/parse";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
	const db = getDb();
	if (!db) {
		return NextResponse.json({ brief: null });
	}

	try {
		const { searchParams } = new URL(request.url);
		const date = searchParams.get("date");

		const row = db
			.prepare(
				"SELECT * FROM daily_briefs WHERE date = ? ORDER BY generated_at DESC LIMIT 1",
			)
			.get(date || new Date().toISOString().split("T")[0]) as any;

		if (!row) {
			return NextResponse.json({ brief: null });
		}

		const brief = {
			...row,
			highlights: parseObjectArray(row.highlights),
			dev_focus: parseObjectArray(row.dev_focus),
		};

		return NextResponse.json({ brief });
	} catch (err) {
		console.error("GET /api/briefs error:", err);
		return NextResponse.json(
			{ error: "Failed to fetch brief" },
			{ status: 500 },
		);
	}
}
