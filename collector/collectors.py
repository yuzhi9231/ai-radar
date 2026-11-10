"""Data source collectors for AI Radar.

Collectors for:
- TechCrunch AI (RSS)
- The Verge AI (RSS)
- Hacker News (Algolia API)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import httpx
from feedparser import parse as parse_rss

from .models import Article, ArticleSource
from .urls import normalize_article_url

# Timeout for external requests (seconds)
REQUEST_TIMEOUT = 30

# Algolia has no "ai" tag; the working filter is a text query on story posts.
HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
HN_QUERY = "AI"
HN_TAGS = "story"
HN_MAX_HITS = 30


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    """Parse an Algolia timestamp, which is an ISO-8601 string rather than an epoch."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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
                    source_url=normalize_article_url(entry.get("link", "")),
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
        raise RuntimeError(f"Failed to fetch RSS feed {url}: {e}") from e

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
    """Collect recent AI stories from Hacker News via the Algolia API."""
    params = {"query": HN_QUERY, "tags": HN_TAGS, "hitsPerPage": HN_MAX_HITS}

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            resp = client.get(HN_SEARCH_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch HN API: {e}") from e

    articles = []
    for hit in data.get("hits", [])[:HN_MAX_HITS]:
        url = hit.get("url", "")
        if not url:
            # Text and Ask posts have no external link; they cannot be deduped by URL.
            continue

        article = Article(
            source_url=normalize_article_url(url),
            source_name="Hacker News",
            source=ArticleSource.HN,
            raw_title=hit.get("title", "Untitled"),
            raw_description=hit.get("story_text", ""),
            published_at=_parse_iso_datetime(hit.get("created_at", "")),
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


def collect_all(errors: Optional[dict[str, str]] = None) -> dict[str, list[Article]]:
    """Run all collectors and return results keyed by source name.

    A source that fails yields an empty list; when `errors` is provided the failure
    reason is recorded there, so a network error is not mistaken for "no articles".
    """
    results = {}
    for source, collect_fn in COLLECTORS.items():
        try:
            results[source.value] = collect_fn()
        except Exception as e:
            if errors is not None:
                errors[source.value] = str(e)
            results[source.value] = []
    return results
