"""Scheduler module - triggers collection runs."""

from __future__ import annotations

from datetime import datetime, timezone

from .ai import process_article
from .collectors import collect_all
from .db import (
    create_pipeline_run,
    get_all_articles,
    get_connection,
    upsert_article,
    upsert_processed_article,
)
from .dedup import deduplicate
from .models import PipelineRun


def run_pipeline() -> PipelineRun:
    """Execute a full collection pipeline: fetch → dedup → store → AI process."""
    run = PipelineRun(status="running")
    run.started_at = datetime.now(timezone.utc)

    # Create pipeline run record
    create_pipeline_run(run)
    get_connection()

    try:
        # Step 1: Collect from all sources
        results = collect_all()
        all_articles = []
        total_fetched = 0
        source_stats = {}

        for source_name, articles in results.items():
            total_fetched += len(articles)
            source_stats[source_name] = {
                "fetched": len(articles),
                "status": "success" if len(articles) > 0 else "no_articles",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            all_articles.extend(articles)

        run.articles_fetched = total_fetched
        run.source_results = source_stats

        # Step 2: Existing articles for dedup comparison
        existing = get_all_articles()

        # Step 3: Deduplication
        new_articles, dup_count = deduplicate(all_articles, existing)
        run.articles_new = len(new_articles)

        # Step 4: Store new articles
        inserted = 0
        for article in new_articles:
            if upsert_article(article):
                inserted += 1
        run.articles_new = inserted

        # Step 5: AI processing for new articles
        processed_count = 0
        for article in new_articles:
            try:
                processed = process_article(article)
                upsert_processed_article(processed)
                processed_count += 1
            except Exception:
                # AI processing failure should not lose the article
                pass

        run.status = "success" if inserted > 0 else "partial_failure"
        run.completed_at = datetime.now(timezone.utc)

    except Exception as e:
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        run.source_results["error"] = {"status": "error", "message": str(e)}

    # Update pipeline run record
    create_pipeline_run(run)
    return run


def run_manual() -> None:
    """Run the pipeline and print results."""
    import os

    os.environ.setdefault("USE_MOCK_AI", "true")  # Default to mock for manual runs

    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting manual collection...")
    run = run_pipeline()
    print(f"  Fetched: {run.articles_fetched}")
    print(f"  New: {run.articles_new}")
    print(f"  Status: {run.status}")
    print(f"  Completed at: {run.completed_at}")


if __name__ == "__main__":
    run_manual()
