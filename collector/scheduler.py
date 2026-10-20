"""APScheduler-based scheduler for periodic collection runs."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

# Ensure collector package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.blocking import BlockingScheduler

from collector.run import run_pipeline


def scheduled_job() -> None:
    """Execute the collection pipeline as a scheduled job."""
    use_mock = os.environ.get("USE_MOCK_AI", "true")
    if use_mock.lower() == "true":
        os.environ["USE_MOCK_AI"] = "true"

    print(
        f"[{datetime.now(timezone.utc).isoformat()}] Scheduled collection starting..."
    )
    try:
        run = run_pipeline()
        print(f"  Fetched: {run.articles_fetched}")
        print(f"  New: {run.articles_new}")
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
    print(f"  OLLAMA_BASE_URL: {os.environ.get('OLLAMA_BASE_URL', 'not set')}")
    print()

    scheduler = create_scheduler()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nScheduler stopped.")


if __name__ == "__main__":
    main()
