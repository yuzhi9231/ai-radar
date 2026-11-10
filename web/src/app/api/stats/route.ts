import { getStats } from "@/lib/db";
import { NextResponse } from "next/server";

export async function GET() {
	try {
		return NextResponse.json(getStats());
	} catch (err) {
		console.error("GET /api/stats error:", err);
		return NextResponse.json(
			{ error: "Failed to fetch stats" },
			{ status: 500 },
		);
	}
}
