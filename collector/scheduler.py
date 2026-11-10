"""APScheduler-based scheduler for periodic collection runs."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler

from .run import install_signal_handlers, run_pipeline


def scheduled_job() -> None:
    """Execute the collection pipeline as a scheduled job."""
    print(
        f"[{datetime.now(timezone.utc).isoformat()}] Scheduled collection starting..."
    )
    try:
        run = run_pipeline()
        print(f"  Fetched: {run.articles_fetched}")
        print(f"  New: {run.articles_new}")
        print(
            f"  Processed: {run.articles_processed} ok / {run.articles_failed} failed"
        )
        print(f"  Status: {run.status}")
    except Exception as e:
        print(f"  Error: {e}")


def create_scheduler() -> BlockingScheduler:
    """Create and configure the scheduler."""
    scheduler = BlockingScheduler(timezone="Asia/Singapore")

    schedule_str = os.environ.get("SCHEDULE", "10:00,15:00")
    times = [t.strip() for t in schedule_str.split(",")]

    for t in times:
        hour, minute = t.split(":")
        scheduler.add_job(
            scheduled_job,
            "cron",
            hour=int(hour),
            minute=int(minute),
            id=f"collection_{hour}_{minute}",
            replace_existing=True,
        )
        print(f"  Scheduled at {t} (Asia/Singapore)")

    return scheduler


def main() -> None:
    """Entry point for the scheduler service."""
    print("AI Radar Collector Scheduler")
    print(f"  USE_MOCK_AI: {os.environ.get('USE_MOCK_AI', 'false')}")
    print(f"  AI_PROVIDER: {os.environ.get('AI_PROVIDER', 'ollama')}")
    print(f"  OLLAMA_BASE_URL: {os.environ.get('OLLAMA_BASE_URL', 'not set')}")
    print()

    install_signal_handlers()
    scheduler = create_scheduler()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nScheduler stopped.")


if __name__ == "__main__":
    main()
