"""Deduplication module for AI Radar.

Uses URL exact match and title similarity (Levenshtein distance) to detect duplicates.
"""

from __future__ import annotations

import difflib
from typing import Sequence


# Title similarity threshold: articles above this threshold are considered duplicates
TITLE_SIMILARITY_THRESHOLD = 0.85


def url_duplicate(existing_urls: set[str], new_articles: Sequence) -> list:
    """Filter out articles whose URL already exists.

    Returns only the new (non-duplicate) articles.
    """
    return [a for a in new_articles if a.source_url not in existing_urls]


def title_similarity(article1: str, article2: str) -> float:
    """Calculate similarity ratio between two titles.

    Uses difflib.SequenceMatcher for fast approximate matching.
    Returns a value between 0 (completely different) and 1 (identical).
    """
    return difflib.SequenceMatcher(None, article1.lower(), article2.lower()).ratio()


def title_duplicate(existing_articles: Sequence, new_articles: Sequence) -> list:
    """Filter out articles with similar titles to existing articles.

    Returns only articles whose title is not too similar to any existing article.
    """
    remaining = []
    for new_art in new_articles:
        is_dup = False
        for existing_art in existing_articles:
            sim = title_similarity(new_art.raw_title, existing_art.raw_title)
            if sim >= TITLE_SIMILARITY_THRESHOLD:
                is_dup = True
                break
        if not is_dup:
            remaining.append(new_art)
    return remaining


def deduplicate(new_articles: Sequence, existing_articles: Sequence) -> tuple[list, list]:
    """Full deduplication: URL + title.

    Returns (new_articles, duplicate_count).
    """
    existing_urls = {a.source_url for a in existing_articles}

    # Step 1: URL dedup
    after_url = url_duplicate(existing_urls, new_articles)

    # Step 2: Title dedup
    after_title = title_duplicate(existing_articles, after_url)

    dup_count = len(new_articles) - len(after_title)
    return after_title, dup_count
