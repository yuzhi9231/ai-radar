import fs from "node:fs";
import path from "node:path";
import Database from "better-sqlite3";

let cachedDb: Database.Database | null = null;

export function getDb(): Database.Database | null {
	if (cachedDb) return cachedDb;

	const dbPath = process.env.DATABASE_PATH || "/data/ai-radar.db";

	// Check if the database file exists (and its parent directory exists)
	const dir = path.dirname(dbPath);
	if (!fs.existsSync(dir)) {
		return null;
	}

	if (!fs.existsSync(dbPath)) {
		return null;
	}

	cachedDb = new Database(dbPath, { readonly: true });
	cachedDb.pragma("journal_mode = WAL");
	return cachedDb;
}
