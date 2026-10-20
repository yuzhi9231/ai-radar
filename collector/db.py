"""SQLite database operations for AI Radar collector."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Article, ArticleSource, DailyBrief, PipelineRun, ProcessedArticle

# Global database connection cache
_db_conn: Optional[sqlite3.Connection] = None


def get_db_path(db_url: str = "file:/data/ai-radar.db") -> Path:
    """Extract file path from DATABASE_URL."""
    if db_url.startswith("file:"):
        return Path(db_url[5:])
    return Path(db_url)


def init_db(db_url: str = "file:/data/ai-radar.db") -> sqlite3.Connection:
    """Initialize the database and return a connection."""
    global _db_conn

    if _db_conn is not None:
        return _db_conn

    db_path = get_db_path(db_url)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    _db_conn = sqlite3.connect(str(db_path))
    _db_conn.row_factory = sqlite3.Row
    _db_conn.execute("PRAGMA journal_mode=WAL")
    _db_conn.execute("PRAGMA foreign_keys=ON")

    _create_tables(_db_conn)
    _init_sources(_db_conn)

    return _db_conn


def get_connection() -> sqlite3.Connection:
    """Get or create the global database connection."""
    import os

    db_url = os.environ.get("DATABASE_URL", "file:/data/ai-radar.db")
    return init_db(db_url)


def _create_tables(conn: sqlite3.Connection) -> None:
    """Create all tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            feed_url TEXT NOT NULL,
            feed_type TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            last_success TEXT,
            last_error TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            source_url TEXT NOT NULL UNIQUE,
            source_name TEXT NOT NULL,
            source TEXT NOT NULL,
            raw_title TEXT NOT NULL,
            raw_description TEXT NOT NULL DEFAULT '',
            published_at TEXT,
            fetched_at TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'en',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_articles_source_url ON articles(source_url);
        CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
        CREATE INDEX IF NOT EXISTS idx_articles_fetched_at ON articles(fetched_at);

        CREATE TABLE IF NOT EXISTS processed_articles (
            id TEXT PRIMARY KEY,
            article_id TEXT NOT NULL UNIQUE,
            headline_zh TEXT NOT NULL DEFAULT '',
            summary_zh TEXT NOT NULL DEFAULT '',
            why_it_matters_zh TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT 'general',
            tags TEXT NOT NULL DEFAULT '[]',
            importance_score INTEGER NOT NULL DEFAULT 0,
            source_confidence REAL NOT NULL DEFAULT 0.0,
            related_entities TEXT NOT NULL DEFAULT '[]',
            generated_at TEXT NOT NULL DEFAULT (datetime('now')),
            generation_status TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_processed_article_id ON processed_articles(article_id);
        CREATE INDEX IF NOT EXISTS idx_processed_status ON processed_articles(generation_status);

        CREATE TABLE IF NOT EXISTS clusters (
            id TEXT PRIMARY KEY,
            representative_article_id TEXT NOT NULL UNIQUE,
            cluster_type TEXT NOT NULL DEFAULT 'title_similarity',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (representative_article_id) REFERENCES articles(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS cluster_members (
            cluster_id TEXT NOT NULL,
            article_id TEXT NOT NULL,
            PRIMARY KEY (cluster_id, article_id),
            FOREIGN KEY (cluster_id) REFERENCES clusters(id) ON DELETE CASCADE,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS daily_briefs (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL UNIQUE,
            trend_summary TEXT NOT NULL DEFAULT '',
            highlights TEXT NOT NULL DEFAULT '[]',
            dev_focus TEXT NOT NULL DEFAULT '[]',
            generated_at TEXT NOT NULL DEFAULT (datetime('now')),
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
            source_results TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_pipeline_status ON pipeline_runs(status);
        CREATE INDEX IF NOT EXISTS idx_pipeline_started ON pipeline_runs(started_at);
    """)


def _init_sources(conn: sqlite3.Connection) -> None:
    """Initialize default data sources if not present."""
    sources = [
        (
            "techcrunch",
            "TechCrunch AI",
            "https://techcrunch.com/category/artificial-intelligence/feed/",
            "rss",
        ),
        (
            "theverge",
            "The Verge AI",
            "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
            "rss",
        ),
        (
            "hn",
            "Hacker News",
            "https://hn.algolia.com/api/v1/search?tags=story&dateRange=past24hours",
            "api",
        ),
    ]
    for sid, name, feed_url, feed_type in sources:
        conn.execute(
            """
            INSERT OR IGNORE INTO sources (id, name, feed_url, feed_type)
            VALUES (?, ?, ?, ?)
        """,
            (sid, name, feed_url, feed_type),
        )
    conn.commit()


# --- Article operations ---


def upsert_article(article: Article) -> bool:
    """Insert or ignore an article. Returns True if newly inserted."""
    conn = get_connection()
    try:
        result = conn.execute(
            """
            INSERT OR IGNORE INTO articles
                (id, source_url, source_name, source, raw_title, raw_description,
                 published_at, fetched_at, language)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                article.id,
                article.source_url,
                article.source_name,
                article.source.value,
                article.raw_title,
                article.raw_description,
                article.published_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                if article.published_at
                else None,
                article.fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                article.language,
            ),
        )
        conn.commit()
        return result.rowcount > 0
    except sqlite3.IntegrityError:
        return False


def get_all_articles() -> list[Article]:
    """Get all articles, newest first."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT a.id, a.source_url, a.source_name, a.source, a.raw_title,
               a.raw_description, a.published_at, a.fetched_at, a.language,
               pa.headline_zh, pa.summary_zh, pa.category,
               pa.importance_score, pa.generation_status
        FROM articles a
        LEFT JOIN processed_articles pa ON a.id = pa.article_id
        ORDER BY a.fetched_at DESC
    """).fetchall()
    return [_row_to_article(row) for row in rows]


def get_articles_by_date(date_str: str) -> list[Article]:
    """Get articles for a specific date."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT a.id, a.source_url, a.source_name, a.source, a.raw_title,
               a.raw_description, a.published_at, a.fetched_at, a.language,
               pa.headline_zh, pa.summary_zh, pa.category,
               pa.importance_score, pa.generation_status
        FROM articles a
        LEFT JOIN processed_articles pa ON a.id = pa.article_id
        WHERE date(a.fetched_at) = ?
        ORDER BY a.fetched_at DESC
    """,
        (date_str,),
    ).fetchall()
    return [_row_to_article(row) for row in rows]


def get_article_by_id(article_id: str) -> Optional[Article]:
    """Get a single article by ID."""
    conn = get_connection()
    row = conn.execute(
        """
        SELECT a.id, a.source_url, a.source_name, a.source, a.raw_title,
               a.raw_description, a.published_at, a.fetched_at, a.language,
               pa.headline_zh, pa.summary_zh, pa.category,
               pa.importance_score, pa.generation_status
        FROM articles a
        LEFT JOIN processed_articles pa ON a.id = pa.article_id
        WHERE a.id = ?
    """,
        (article_id,),
    ).fetchone()
    return _row_to_article(row) if row else None


def _row_to_article(row: sqlite3.Row) -> Article:
    """Convert a DB row to an Article model."""
    published_at = (
        datetime.fromisoformat(row["published_at"]) if row["published_at"] else None
    )
    fetched_at = datetime.fromisoformat(row["fetched_at"])
    source = ArticleSource(row["source"])

    processed = ProcessedArticle(
        id="",
        article_id=row["id"],
        headline_zh=row["headline_zh"] or "",
        summary_zh=row["summary_zh"] or "",
        category=row["category"] or "general",
        importance_score=row["importance_score"] or 0,
        generation_status=row["generation_status"] or "pending",
    )

    article = Article(
        id=row["id"],
        source_url=row["source_url"],
        source_name=row["source_name"],
        source=source,
        raw_title=row["raw_title"],
        raw_description=row["raw_description"] or "",
        published_at=published_at,
        fetched_at=fetched_at,
        language=row["language"] or "en",
    )
    article.__processed__ = processed
    return article


# --- Processed article operations ---


def upsert_processed_article(processed: ProcessedArticle) -> None:
    """Insert or update a processed article."""
    conn = get_connection()
    tags_json = json.dumps(processed.tags, ensure_ascii=False)
    entities_json = json.dumps(processed.related_entities, ensure_ascii=False)

    conn.execute(
        """
        INSERT OR REPLACE INTO processed_articles
            (id, article_id, headline_zh, summary_zh, why_it_matters_zh,
             category, tags, importance_score, source_confidence,
             related_entities, generated_at, generation_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            processed.id,
            processed.article_id,
            processed.headline_zh,
            processed.summary_zh,
            processed.why_it_matters_zh,
            processed.category,
            tags_json,
            processed.importance_score,
            processed.source_confidence,
            entities_json,
            processed.generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            processed.generation_status,
        ),
    )
    conn.commit()


# --- Daily brief operations ---


def upsert_daily_brief(brief: DailyBrief) -> None:
    """Insert or update a daily brief."""
    conn = get_connection()
    highlights_json = json.dumps(brief.highlights, ensure_ascii=False)
    dev_focus_json = json.dumps(brief.dev_focus, ensure_ascii=False)

    conn.execute(
        """
        INSERT OR REPLACE INTO daily_briefs
            (id, date, trend_summary, highlights, dev_focus, generated_at, generation_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            brief.id,
            brief.date,
            brief.trend_summary,
            highlights_json,
            dev_focus_json,
            brief.generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            brief.generation_status,
        ),
    )
    conn.commit()


def get_daily_brief(date_str: str) -> Optional[DailyBrief]:
    """Get a daily brief for a specific date."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM daily_briefs WHERE date = ?", (date_str,)
    ).fetchone()
    if not row:
        return None
    return DailyBrief(
        id=row["id"],
        date=row["date"],
        trend_summary=row["trend_summary"],
        highlights=json.loads(row["highlights"]),
        dev_focus=json.loads(row["dev_focus"]),
        generation_status=row["generation_status"],
    )


# --- Pipeline run operations ---


def create_pipeline_run(run: PipelineRun) -> str:
    """Create a new pipeline run record."""
    conn = get_connection()
    source_results_json = json.dumps(run.source_results, ensure_ascii=False)

    conn.execute(
        """
        INSERT OR REPLACE INTO pipeline_runs
            (id, started_at, completed_at, status, articles_fetched,
             articles_new, articles_updated, source_results)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            run.id,
            run.started_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            run.completed_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            if run.completed_at
            else None,
            run.status,
            run.articles_fetched,
            run.articles_new,
            run.articles_updated,
            source_results_json,
        ),
    )
    conn.commit()
    return run.id


def get_latest_pipeline_run() -> Optional[PipelineRun]:
    """Get the most recent pipeline run."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    if not row:
        return None
    return PipelineRun(
        id=row["id"],
        started_at=datetime.fromisoformat(row["started_at"]),
        completed_at=datetime.fromisoformat(row["completed_at"])
        if row["completed_at"]
        else None,
        status=row["status"],
        articles_fetched=row["articles_fetched"],
        articles_new=row["articles_new"],
        articles_updated=row["articles_updated"],
        source_results=json.loads(row["source_results"]),
    )


# --- Stats ---


def get_stats() -> dict:
    """Get overall statistics."""
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    sources = conn.execute("SELECT COUNT(*) FROM sources WHERE enabled = 1").fetchone()[
        0
    ]
    processed = conn.execute(
        "SELECT COUNT(*) FROM processed_articles WHERE generation_status = 'success'"
    ).fetchone()[0]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    today_count = conn.execute(
        "SELECT COUNT(*) FROM articles WHERE date(fetched_at) = ?", (today,)
    ).fetchone()[0]

    return {
        "total_articles": total,
        "enabled_sources": sources,
        "processed_count": processed,
        "today_count": today_count,
    }


# --- Sources ---


def get_sources() -> list[dict]:
    """Get all sources."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM sources ORDER BY name").fetchall()
    return [dict(row) for row in rows]
