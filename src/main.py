from __future__ import annotations

import argparse
from datetime import date

from workflow.daily_pipeline import STAGE_ORDER, run_daily_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the WeChat content agent pipeline.")
    parser.add_argument(
        "--stage",
        choices=STAGE_ORDER,
        default="all",
        help="Pipeline stage to run.",
    )
    parser.add_argument(
        "--date",
        dest="run_date",
        help="Run date in YYYY-MM-DD format. Defaults to today.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_date = date.fromisoformat(args.run_date) if args.run_date else None
    result = run_daily_pipeline(run_date=run_date, stage=args.stage)
    package = result["publish_package"]
    if package is not None:
        print(f"Publish package created: {package.title}")
    else:
        print(f"Pipeline stage completed: {result['completed_stage']}")
    print(f"Output directory: {result['output_dir']}")


if __name__ == "__main__":
    main()
