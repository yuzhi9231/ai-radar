"""CLI entry point for the collector."""

import argparse
import sys
from datetime import datetime

from .run import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="AI Radar Collector")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("run", help="Run a single collection pipeline")
    subparsers.add_parser(
        "schedule", help="Start scheduled collection (10:00 + 15:00 SGT)"
    )

    args = parser.parse_args()

    if args.command == "run":
        print(f"[{datetime.utcnow().isoformat()}] Running manual collection...")
        run = run_pipeline()
        print(f"  Fetched: {run.articles_fetched}")
        print(f"  New: {run.articles_new}")
        print(f"  Status: {run.status}")
        sys.exit(0 if run.status == "success" else 1)

    elif args.command == "schedule":
        from datetime import timezone

        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger

        # Parse schedule from environment
        schedule_str = "10,15"
        hours = [int(h) for h in schedule_str.split(",")]

        scheduler = BlockingScheduler(
            timezone=timezone.utc + __import__("datetime").timedelta(hours=8)
        )
        for hour in hours:
            scheduler.add_job(
                run_pipeline,
                CronTrigger(
                    hour=hour,
                    minute=0,
                    timezone=timezone.utc + __import__("datetime").timedelta(hours=8),
                ),
                id=f"collection_{hour}",
                max_instances=1,
            )
        print(f"Scheduler started. Collection at {hours}:00 SGT")
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("Scheduler stopped.")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
