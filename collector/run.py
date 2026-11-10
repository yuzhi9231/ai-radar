"""Scheduler module - triggers collection runs."""

from __future__ import annotations

import os
import signal
from datetime import datetime, timezone

from .ai import AI_PROVIDER, USE_MOCK_AI, process_article
from .collectors import collect_all
from .db import (
    create_pipeline_run,
    get_all_articles,
    get_article_by_id,
    get_connection,
    upsert_article,
    upsert_processed_article,
)
from .dedup import deduplicate
from .models import PipelineRun


def _stamp() -> str:
    """Current UTC time in the format the run record stores."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_interrupted = False


def _handle_signal(signum: int, frame: object) -> None:
    """Record the signal so the run is written with the counts collected so far."""
    global _interrupted
    _interrupted = True


def install_signal_handlers() -> None:
    """Handle SIGINT/SIGTERM so an interrupted run is stored as 'interrupted'
    with the counts collected so far, instead of being left as 'running'."""
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handle_signal)
        except (ValueError, OSError):
            # Signal handlers can only be installed on the main thread
            pass


def run_pipeline() -> PipelineRun:
    """Execute a full collection pipeline: fetch → dedup → store → AI process."""
    global _interrupted
    _interrupted = False

    run = PipelineRun(status="running")
    run.started_at = datetime.now(timezone.utc)

    # Create pipeline run record
    create_pipeline_run(run)
    get_connection()

    try:
        # Step 1: Collect from all sources, keeping per-source failures visible
        errors: dict[str, str] = {}
        results = collect_all(errors)
        all_articles = []
        total_fetched = 0
        source_stats = {}

        for source_name, articles in results.items():
            total_fetched += len(articles)
            if source_name in errors:
                status = "error"
            elif len(articles) > 0:
                status = "success"
            else:
                status = "no_articles"
            source_stats[source_name] = {
                "fetched": len(articles),
                "status": status,
                "error": errors.get(source_name),
                "timestamp": _stamp(),
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
        for article in new_articles:
            if _interrupted:
                break
            try:
                processed = process_article(article)
                upsert_processed_article(processed)
                if processed.generation_status == "success":
                    run.articles_processed += 1
                else:
                    run.articles_failed += 1
            except Exception as e:
                # AI processing failure must not lose the article
                run.articles_failed += 1
                print(f"  AI processing error for {article.source_url}: {e}")

        if _interrupted:
            run.status = "interrupted"
        elif errors and len(errors) == len(results):
            # Every source failed: nothing at all was collected
            run.status = "failed"
        elif run.articles_failed > 0 or errors:
            run.status = "partial_failure"
        else:
            # Everything already stored is a normal outcome, not a failure
            run.status = "success"

        run.completed_at = datetime.now(timezone.utc)

    except Exception as e:
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        run.source_results["error"] = {"status": "error", "message": str(e)}

    # Update the run record with what actually happened
    create_pipeline_run(run)
    return run


def reprocess_failed(limit: int = 50) -> dict[str, int]:
    """Re-run the AI layer for articles that were stored but never analysed.

    Only articles with a failed or missing processed row are touched, so a
    reprocess pass never overwrites a good result.
    """
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT a.id FROM articles a
        LEFT JOIN processed_articles pa ON pa.article_id = a.id
        WHERE pa.article_id IS NULL OR pa.generation_status = 'failed'
        ORDER BY a.fetched_at DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()

    report = {"candidates": len(rows), "processed": 0, "still_failed": 0}
    for row in rows:
        if _interrupted:
            break
        article = get_article_by_id(row["id"])
        if article is None:
            continue
        try:
            processed = process_article(article)
        except Exception as e:
            report["still_failed"] += 1
            print(f"  reprocess error for {article.source_url}: {e}")
            continue
        upsert_processed_article(processed)
        if processed.generation_status == "success":
            report["processed"] += 1
        else:
            report["still_failed"] += 1

    return report


def run_manual() -> None:
    """Run the pipeline and print results."""
    install_signal_handlers()
    mode = (
        "mock (explicitly enabled)"
        if USE_MOCK_AI
        else f"{AI_PROVIDER} @ {os.environ.get('OLLAMA_BASE_URL', 'not set')}"
    )
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting manual collection...")
    print(f"  AI mode: {mode}")

    run = run_pipeline()
    print(f"  Fetched: {run.articles_fetched}")
    print(f"  New: {run.articles_new}")
    print(f"  Processed: {run.articles_processed} ok / {run.articles_failed} failed")
    print(f"  Status: {run.status}")
    print(f"  Completed at: {run.completed_at}")


if __name__ == "__main__":
    run_manual()
