import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

// Resolving from the process working directory keeps this file loadable by the
// CommonJS jest runtime as well; import.meta.url would make it ESM-only.
const requireModule = createRequire(path.join(process.cwd(), "index.js"));

export interface Prepared {
	get: (...params: unknown[]) => unknown;
	all: (...params: unknown[]) => unknown[];
}

export interface Queryable {
	prepare: (sql: string) => Prepared;
	pragma?: (sql: string) => unknown;
}

let cachedDb: Queryable | null = null;

function resolveDbPath(): string {
	let dbPath = process.env.DATABASE_PATH || "/data/ai-radar.db";
	const projectRoot = path.resolve(process.cwd(), "..");
	if (dbPath.startsWith("/") && !fs.existsSync(dbPath)) {
		dbPath = path.resolve(projectRoot, "data", path.basename(dbPath));
	}
	return dbPath;
}

function openBetterSqlite3(file: string): Queryable | null {
	try {
		const Database = requireModule("better-sqlite3");
		const db = new Database(file, { readonly: true });
		db.pragma("journal_mode = WAL");
		return db as Queryable;
	} catch (err) {
		console.warn(
			`better-sqlite3 unavailable: ${(err as Error).message.split("\n")[0]}`,
		);
		return null;
	}
}

function openNodeSqlite(file: string): Queryable | null {
	type DatabaseSync = {
		prepare: (sql: string) => Prepared;
		pragma: (sql: string) => unknown;
	};
	try {
		const mod = requireModule("node:sqlite") as {
			DatabaseSync: new (
				path: string,
				options?: { open?: boolean; readOnly?: boolean },
			) => DatabaseSync;
		};
		const db = new mod.DatabaseSync(file, { open: true, readOnly: true });
		return db;
	} catch (err) {
		console.warn(
			`node:sqlite unavailable: ${(err as Error).message.split("\n")[0]}`,
		);
		return null;
	}
}

export function getDb(): Queryable | null {
	if (cachedDb) {
		return cachedDb;
	}

	const dbPath = resolveDbPath();
	if (!fs.existsSync(dbPath)) {
		return null;
	}

	// better-sqlite3 is the intended driver; node:sqlite is the fallback when the
	// native binding was never built on this machine
	cachedDb = openBetterSqlite3(dbPath) ?? openNodeSqlite(dbPath);
	return cachedDb;
}

export function getArticles(filters?: {
	source?: string;
	category?: string;
}): Record<string, unknown>[] {
	const db = getDb();
	if (!db) return [];

	let query = `
    SELECT
      a.id, a.source_url, a.source_name, a.source,
      a.raw_title, a.raw_description, a.published_at, a.fetched_at, a.language,
      pa.headline_zh, pa.summary_zh, pa.category,
      pa.tags, pa.importance_score, pa.generation_status, pa.error
    FROM articles a
    LEFT JOIN processed_articles pa ON a.id = pa.article_id
  `;
	const params: unknown[] = [];
	const whereClauses: string[] = [];

	if (filters?.source) {
		whereClauses.push("a.source = ?");
		params.push(filters.source);
	}
	if (filters?.category) {
		whereClauses.push("pa.category = ?");
		params.push(filters.category);
	}

	if (whereClauses.length > 0) {
		query += ` WHERE ${whereClauses.join(" AND ")}`;
	}

	query += " ORDER BY a.fetched_at DESC LIMIT 12";

	return db.prepare(query).all(...params) as Record<string, unknown>[];
}

export function getBriefByDate(date: string): Record<string, unknown> | null {
	const db = getDb();
	if (!db) return null;
	const row = db
		.prepare("SELECT * FROM daily_briefs WHERE date = ?")
		.get(date) as Record<string, unknown> | undefined;
	return row ?? null;
}

export function getLatestBrief(): Record<string, unknown> | null {
	const db = getDb();
	if (!db) return null;
	const row = db
		.prepare("SELECT * FROM daily_briefs ORDER BY date DESC LIMIT 1")
		.get() as Record<string, unknown> | undefined;
	return row ?? null;
}

export interface LatestRun {
	status: string;
	started_at: string;
	completed_at: string | null;
	articles_fetched: number;
	articles_new: number;
	articles_processed: number;
	articles_failed: number;
}

/** The most recent collection run, so the UI can show what actually happened. */
export function getLatestRun(): LatestRun | null {
	const db = getDb();
	if (!db) return null;
	const row = db
		.prepare("SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 1")
		.get() as Record<string, unknown> | undefined;
	if (!row) return null;

	return {
		status: String(row.status),
		started_at: String(row.started_at),
		completed_at: (row.completed_at as string | null) ?? null,
		articles_fetched: Number(row.articles_fetched ?? 0),
		articles_new: Number(row.articles_new ?? 0),
		articles_processed: Number(row.articles_processed ?? 0),
		articles_failed: Number(row.articles_failed ?? 0),
	};
}

export interface Stats {
	total_articles: number;
	enabled_sources: number;
	processed_count: number;
	failed_count: number;
	last_fetched_at: string | null;
}

export function getStats(): Stats {
	const db = getDb();
	if (!db) {
		return {
			total_articles: 0,
			enabled_sources: 0,
			processed_count: 0,
			failed_count: 0,
			last_fetched_at: null,
		};
	}

	const total = db.prepare("SELECT COUNT(*) as count FROM articles").get() as {
		count: number;
	};
	const sources = db
		.prepare("SELECT COUNT(*) as count FROM sources WHERE enabled = 1")
		.get() as { count: number };
	const processed = db
		.prepare(
			"SELECT COUNT(*) as count FROM processed_articles WHERE generation_status = 'success'",
		)
		.get() as { count: number };
	const failed = db
		.prepare(
			"SELECT COUNT(*) as count FROM processed_articles WHERE generation_status = 'failed'",
		)
		.get() as { count: number };
	const lastFetched = db
		.prepare("SELECT MAX(fetched_at) as last FROM articles")
		.get() as { last: string | null };

	return {
		total_articles: total.count,
		enabled_sources: sources.count,
		processed_count: processed.count,
		failed_count: failed.count,
		last_fetched_at: lastFetched.last,
	};
}
