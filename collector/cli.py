"""CLI entry point for the collector."""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

from .run import install_signal_handlers, reprocess_failed, run_pipeline


def main():
    parser = argparse.ArgumentParser(description="AI Radar Collector")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("run", help="Run a single collection pipeline")
    subparsers.add_parser(
        "schedule", help="Start scheduled collection (10:00 + 15:00 SGT)"
    )
    subparsers.add_parser(
        "repair-urls", help="Repair rows written before the collector fixes"
    )
    reprocess = subparsers.add_parser(
        "reprocess", help="Re-run the AI layer for articles that were not analysed"
    )
    reprocess.add_argument(
        "--limit", type=int, default=50, help="Maximum articles to reprocess"
    )

    args = parser.parse_args()

    install_signal_handlers()

    if args.command == "run":
        print(
            f"[{datetime.now(timezone.utc).isoformat()}] Running manual collection..."
        )
        run = run_pipeline()
        print(f"  Fetched: {run.articles_fetched}")
        print(f"  New: {run.articles_new}")
        print(
            f"  Processed: {run.articles_processed} ok / {run.articles_failed} failed"
        )
        print(f"  Status: {run.status}")
        sys.exit(0 if run.status == "success" else 1)

    elif args.command == "repair-urls":
        from .repair import main as repair_main

        repair_main()

    elif args.command == "reprocess":
        report = reprocess_failed(args.limit)
        print(f"  Candidates: {report['candidates']}")
        print(f"  Analysed: {report['processed']}")
        print(f"  Still failed: {report['still_failed']}")
        sys.exit(0 if report["still_failed"] == 0 else 1)

    elif args.command == "schedule":
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger

        # Schedule comes from SCHEDULE (e.g. "10:00,15:00"), hours only
        schedule_str = os.environ.get("SCHEDULE", "10:00,15:00")
        hours = [
            int(part.split(":")[0]) for part in schedule_str.split(",") if part.strip()
        ]

        # timezone.utc + timedelta is not valid; build the SGT timezone directly
        sgt = timezone(timedelta(hours=8))
        scheduler = BlockingScheduler(timezone=sgt)
        for hour in hours:
            scheduler.add_job(
                run_pipeline,
                CronTrigger(
                    hour=hour,
                    minute=0,
                    timezone=sgt,
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
