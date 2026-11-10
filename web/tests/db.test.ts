/**
 * Tests for the DB access layer.
 *
 * The routes must work when the database file is absent (the CI runner has no
 * /data volume), and the counts must reflect what is actually stored.
 */

import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";

import {
	getArticles,
	getBriefByDate,
	getDb,
	getLatestBrief,
	getLatestRun,
	getStats,
} from "@/lib/db";

// createRequire needs a module path; using cwd keeps the test free of import.meta
const requireModule = createRequire(path.join(process.cwd(), "index.js"));

const SCHEMA = `
CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    source_url TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    source TEXT NOT NULL,
    raw_title TEXT NOT NULL,
    raw_description TEXT DEFAULT '',
    published_at TEXT,
    fetched_at TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en'
);

CREATE TABLE IF NOT EXISTS processed_articles (
    id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL UNIQUE,
    headline_zh TEXT NOT NULL DEFAULT '',
    summary_zh TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'general',
    tags TEXT NOT NULL DEFAULT '[]',
    importance_score INTEGER NOT NULL DEFAULT 0,
    generated_at TEXT NOT NULL,
    generation_status TEXT NOT NULL DEFAULT 'pending',
    error TEXT
);

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    feed_url TEXT NOT NULL,
    feed_type TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS daily_briefs (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    trend_summary TEXT NOT NULL DEFAULT '',
    highlights TEXT NOT NULL DEFAULT '[]',
    dev_focus TEXT NOT NULL DEFAULT '[]',
    generated_at TEXT NOT NULL,
    generation_status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    articles_fetched INTEGER NOT NULL DEFAULT 0,
    articles_new INTEGER NOT NULL DEFAULT 0,
    articles_updated INTEGER NOT NULL DEFAULT 0,
    articles_processed INTEGER NOT NULL DEFAULT 0,
    articles_failed INTEGER NOT NULL DEFAULT 0,
    source_results TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
`;

type Driver = {
	exec: (sql: string) => void;
	prepare: (sql: string) => { run: (...params: unknown[]) => void };
	close: () => void;
};

function openWritableDriver(file: string): Driver | null {
	try {
		const Database = requireModule("better-sqlite3");
		const db = new Database(file);
		return db as unknown as Driver;
	} catch {
		try {
			const sqlite = requireModule("node:sqlite");
			const db = new sqlite.DatabaseSync(file);
			return db as unknown as Driver;
		} catch {
			return null;
		}
	}
}

describe("db with no database file", () => {
	beforeAll(() => {
		process.env.DATABASE_PATH = path.join(os.tmpdir(), "ai-radar-absent.db");
	});

	it("returns null instead of throwing", () => {
		expect(getDb()).toBeNull();
	});

	it("returns empty results", () => {
		expect(getArticles()).toEqual([]);
		expect(getBriefByDate("2026-11-10")).toBeNull();
		expect(getLatestBrief()).toBeNull();
	});

	it("reports zeroed stats", () => {
		expect(getStats()).toEqual({
			total_articles: 0,
			enabled_sources: 0,
			processed_count: 0,
			failed_count: 0,
			last_fetched_at: null,
		});
	});
});

describe("db with a fixture database", () => {
	const fixturePath = path.join(os.tmpdir(), "ai-radar-fixture.db");
	let driver: Driver | null = null;

	beforeAll(() => {
		fs.rmSync(fixturePath, { force: true });
		driver = openWritableDriver(fixturePath);
		if (!driver) return;

		driver.exec(SCHEMA);
		driver
			.prepare("INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")
			.run(
				"a1",
				"https://example.com/1",
				"TechCrunch",
				"techcrunch",
				"Analysed article",
				"",
				null,
				"2026-11-10T09:00:00Z",
				"en",
			);
		driver
			.prepare("INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")
			.run(
				"a2",
				"https://example.com/2",
				"The Verge",
				"theverge",
				"Article the model could not analyse",
				"",
				null,
				"2026-11-10T08:00:00Z",
				"en",
			);
		driver
			.prepare("INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")
			.run(
				"a3",
				"https://example.com/3",
				"Hacker News",
				"hn",
				"Article not processed yet",
				"",
				null,
				"2026-11-09T10:00:00Z",
				"en",
			);

		driver
			.prepare(
				"INSERT INTO processed_articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
			)
			.run(
				"p1",
				"a1",
				"标题",
				"摘要",
				"product",
				'["ai"]',
				80,
				"2026-11-10T09:05:00Z",
				"success",
				null,
			);
		driver
			.prepare(
				"INSERT INTO processed_articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
			)
			.run(
				"p2",
				"a2",
				"",
				"",
				"general",
				"[]",
				0,
				"2026-11-10T08:05:00Z",
				"failed",
				"Ollama request failed: timeout",
			);

		driver
			.prepare("INSERT INTO sources VALUES (?, ?, ?, ?, ?)")
			.run("techcrunch", "TechCrunch AI", "https://example.com/feed", "rss", 1);
		driver
			.prepare("INSERT INTO sources VALUES (?, ?, ?, ?, ?)")
			.run("theverge", "The Verge AI", "https://example.com/feed", "rss", 1);
		driver
			.prepare("INSERT INTO sources VALUES (?, ?, ?, ?, ?)")
			.run("hn", "Hacker News", "https://example.com/api", "api", 0);

		driver
			.prepare("INSERT INTO daily_briefs VALUES (?, ?, ?, ?, ?, ?, ?)")
			.run("b1", "2026-11-10", "", "[", "[]", "2026-11-10T10:00:00Z", "failed");

		driver
			.prepare(
				"INSERT INTO pipeline_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
			)
			.run(
				"r1",
				"2026-11-10T10:00:00Z",
				null,
				"interrupted",
				3,
				3,
				0,
				1,
				1,
				"{}",
				"2026-11-10T10:00:00Z",
			);

		driver.close();
		process.env.DATABASE_PATH = fixturePath;
	});

	afterAll(() => {
		// The read-only connection jest opened is still holding the file on Windows
		try {
			fs.rmSync(fixturePath, { force: true, maxRetries: 2 });
		} catch {
			// left in the temp directory, which is fine for a test fixture
		}
	});

	it("counts stored rows by generation status", () => {
		if (!driver) return;
		const stats = getStats();
		expect(stats.total_articles).toBe(3);
		// Only enabled sources count
		expect(stats.enabled_sources).toBe(2);
		expect(stats.processed_count).toBe(1);
		expect(stats.failed_count).toBe(1);
		expect(stats.last_fetched_at).toBe("2026-11-10T09:00:00Z");
	});

	it("reads the failure reason of an unanalysed article", () => {
		if (!driver) return;
		const rows = getArticles();
		const failed = rows.find((row) => row.generation_status === "failed");
		expect(failed?.error).toBe("Ollama request failed: timeout");
	});

	it("reads a brief whose JSON column is corrupt", () => {
		if (!driver) return;
		const brief = getBriefByDate("2026-11-10");
		expect(brief?.generation_status).toBe("failed");
	});

	it("reads the latest run with its counts", () => {
		if (!driver) return;
		const run = getLatestRun();
		expect(run?.status).toBe("interrupted");
		// A run that never finished has no completion time
		expect(run?.completed_at).toBeNull();
		expect(run?.articles_fetched).toBe(3);
		expect(run?.articles_processed).toBe(1);
		expect(run?.articles_failed).toBe(1);
	});
});
