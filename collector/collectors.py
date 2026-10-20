"""Data source collectors for AI Radar.

Collectors for:
- TechCrunch AI (RSS)
- The Verge AI (RSS)
- Hacker News (Algolia API)
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
from feedparser import parse as parse_rss

from .models import Article, ArticleSource

# Timeout for external requests (seconds)
REQUEST_TIMEOUT = 30


def _parse_rss_feed(url: str, source_name: str, source: ArticleSource) -> list[Article]:
    """Fetch and parse an RSS feed, returning a list of Articles."""
    articles = []
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            resp = client.get(url)
            resp.raise_for_status()
            feed = parse_rss(resp.text)

            for entry in feed.entries:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(
                        *entry.published_parsed[:6], tzinfo=timezone.utc
                    )

                article = Article(
                    source_url=entry.get("link", ""),
                    source_name=source_name,
                    source=source,
                    raw_title=entry.get("title", "Untitled"),
                    raw_description=entry.get("summary", "")
                    or entry.get("description", ""),
                    published_at=published,
                    language=entry.get("language", "en"),
                )
                articles.append(article)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch RSS feed {url}: {e}")

    return articles


def collect_techcrunch() -> list[Article]:
    """Collect articles from TechCrunch AI RSS feed."""
    url = "https://techcrunch.com/category/artificial-intelligence/feed/"
    return _parse_rss_feed(url, "TechCrunch AI", ArticleSource.TECHCRUNCH)


def collect_theverge() -> list[Article]:
    """Collect articles from The Verge AI RSS feed."""
    url = "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"
    return _parse_rss_feed(url, "The Verge AI", ArticleSource.THE_VERGE)


def collect_hackernews() -> list[Article]:
    """Collect articles from Hacker News via Algolia API."""
    url = "https://hn.algolia.com/api/v1/search?tags=ai"

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch HN API: {e}")

    articles = []
    hits = data.get("hits", [])

    for hit in hits[:30]:  # Limit to top 30
        published_str = hit.get("created_at", "")
        try:
            published = datetime.fromtimestamp(int(published_str), tz=timezone.utc)
        except (ValueError, TypeError):
            published = None

        article = Article(
            source_url=hit.get("url", ""),
            source_name="Hacker News",
            source=ArticleSource.HN,
            raw_title=hit.get("title", "Untitled"),
            raw_description=hit.get("story_text", ""),
            published_at=published,
        )
        articles.append(article)

    return articles


COLLECTORS = {
    ArticleSource.TECHCRUNCH: collect_techcrunch,
    ArticleSource.THE_VERGE: collect_theverge,
    ArticleSource.HN: collect_hackernews,
}

# Aliases for common naming conventions
collect_hn = collect_hackernews


def collect_all() -> dict[str, list[Article]]:
    """Run all collectors and return results keyed by source name."""
    results = {}
    for source, collect_fn in COLLECTORS.items():
        try:
            articles = collect_fn()
            results[source.value] = articles
        except Exception:
            results[source.value] = []
    return results
