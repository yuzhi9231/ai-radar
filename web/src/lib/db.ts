import Database from "better-sqlite3";
import fs from "fs";
import path from "path";

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
