"""One-off repair of rows written before the collector fixes.

Repairs:
1. Article URLs whose date segment was stored as YYYY-MM-DD instead of the
   slash form the site serves (those links 404). Each candidate is verified
   against the live article before the row is written.
2. The Hacker News source feed_url, which pointed at a filter Algolia returns
   no hits for.
3. Pipeline runs left as 'running' because the process never finished.
"""

from __future__ import annotations

import html
import re

import httpx

from .db import get_connection
from .urls import looks_uncanonical, normalize_article_url

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
)
REQUEST_TIMEOUT = 30
HN_FEED_URL = (
    "https://hn.algolia.com/api/v1/search_by_date?query=AI&tags=story&hitsPerPage=30"
)

OG_TITLE = re.compile(r'property="og:title" content="([^"]*)"')


def _clean_title(value: str) -> str:
    """Normalise a title for comparison: unescape entities, lowercase, collapse spaces."""
    return " ".join(html.unescape(value or "").split()).strip().lower()


def _titles_match(live: str, stored: str) -> bool:
    """True when the live og:title is the stored title.

    Pages usually add the site name to og:title ("Title | TechCrunch", sometimes
    "TechCrunch - Title"), while the stored raw_title is the RSS title without it, so a
    strict equality check would reject every candidate from such a source.
    """
    live_clean = _clean_title(live)
    stored_clean = _clean_title(stored)
    if live_clean == stored_clean:
        return True

    segments = [segment for segment in re.split(r"\s+[|-]\s+", live_clean) if segment]
    return len(segments) > 1 and stored_clean in segments


def fetch_og_title(url: str) -> str | None:
    """Read og:title from the live page, or None when it cannot be fetched."""
    try:
        with httpx.Client(
            timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT}
        ) as c:
            resp = c.get(url)
            resp.raise_for_status()
            match = OG_TITLE.search(resp.text)
            return match.group(1) if match else None
    except Exception as e:
        print(f"  verify skipped ({url}): {e}")
        return None


def repair_urls(verify: bool = True, dry_run: bool = False) -> dict[str, int]:
    """Rewrite dash-form date segments; verify against the live article when asked."""
    conn = get_connection()
    report = {"checked": 0, "fixed": 0, "already_ok": 0, "unverified": 0}

    for row in conn.execute(
        "SELECT id, source_url, raw_title FROM articles"
    ).fetchall():
        report["checked"] += 1
        current = row["source_url"]
        if not looks_uncanonical(current):
            report["already_ok"] += 1
            continue

        candidate = normalize_article_url(current)
        if verify:
            live = fetch_og_title(candidate)
            if live is None or not _titles_match(live, row["raw_title"]):
                print(f"  unverified: {candidate} (og:title: {live!r})")
                report["unverified"] += 1
                continue

        if dry_run:
            print(f"  would fix: {current} -> {candidate}")
        else:
            conn.execute(
                "UPDATE articles SET source_url = ? WHERE id = ?",
                (candidate, row["id"]),
            )
        report["fixed"] += 1

    if not dry_run:
        conn.commit()
    return report


def repair_hn_feed_url(dry_run: bool = False) -> bool:
    """Point the HN source at the query that actually returns hits."""
    conn = get_connection()
    row = conn.execute("SELECT feed_url FROM sources WHERE id = 'hn'").fetchone()
    if not row or row["feed_url"] == HN_FEED_URL:
        return False

    if dry_run:
        print(f"  would fix: {row['feed_url']} -> {HN_FEED_URL}")
    else:
        conn.execute("UPDATE sources SET feed_url = ? WHERE id = 'hn'", (HN_FEED_URL,))
        conn.commit()
    return True


def mark_interrupted_runs(dry_run: bool = False) -> int:
    """Runs that never completed are 'running' rows with no completion time."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id FROM pipeline_runs WHERE status = 'running' AND completed_at IS NULL"
    ).fetchall()
    for row in rows:
        if dry_run:
            print(f"  would mark interrupted: {row['id']}")
        else:
            conn.execute(
                "UPDATE pipeline_runs SET status = 'interrupted' WHERE id = ?",
                (row["id"],),
            )
    if rows and not dry_run:
        conn.commit()
    return len(rows)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Repair rows written before the fixes")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="rewrite URLs without checking them against the live article",
    )
    args = parser.parse_args()

    print("URLs:")
    print(f"  {repair_urls(verify=not args.no_verify, dry_run=args.dry_run)}")
    print("Sources:")
    print(f"  hn feed_url changed: {repair_hn_feed_url(dry_run=args.dry_run)}")
    print("Pipeline runs:")
    print(f"  interrupted marked: {mark_interrupted_runs(dry_run=args.dry_run)}")


if __name__ == "__main__":
    main()
