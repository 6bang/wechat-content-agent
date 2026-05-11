from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from notify.feishu_notify import is_feishu_enabled, send_feishu_text
from publish.wechat_draft import WeChatDraftError, sync_output_to_wechat_draft
from utils.time_utils import today_iso


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync a generated article to WeChat draft box.")
    parser.add_argument("--date", dest="run_date", help="Output date in YYYY-MM-DD. Defaults to today.")
    parser.add_argument(
        "--layer",
        choices=["C", "E", "S"],
        help="Sync one of the daily C/E/S candidate articles. Defaults to the top-level recommended article.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Render and validate locally without calling WeChat.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_date = args.run_date or today_iso()
    date.fromisoformat(run_date)
    output_dir = resolve_output_dir(run_date, args.layer)
    result_path = output_dir / "wechat_draft_result.json"

    try:
        result = sync_output_to_wechat_draft(output_dir, dry_run=args.dry_run)
        result["date"] = run_date
        result["layer"] = args.layer or "recommended"
        save_result(result_path, result)
    except Exception as exc:
        result = {
            "created": False,
            "dry_run": args.dry_run,
            "date": run_date,
            "layer": args.layer or "recommended",
            "error": str(exc),
        }
        save_result(result_path, result)
        print(f"WeChat draft sync failed: {exc}")
        return 1

    if args.dry_run:
        print(f"WeChat draft dry-run passed: {result_path}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    title = result.get("title", "")
    media_id = result.get("media_id", "")
    print(f"WeChat draft created: {title}")
    print(f"Draft media_id: {media_id}")
    notify_wechat_draft_created(run_date, args.layer or "recommended", title, media_id)
    return 0


def resolve_output_dir(run_date: str, layer: str | None) -> Path:
    base_dir = PROJECT_ROOT / "outputs" / run_date
    if not layer:
        return base_dir
    return base_dir / "articles" / layer


def save_result(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def notify_wechat_draft_created(run_date: str, layer: str, title: str, media_id: str) -> None:
    if not is_feishu_enabled():
        print("Feishu notification skipped: ENABLE_FEISHU is not true.")
        return

    content = "\n".join(
        [
            "【公众号草稿箱同步完成】",
            "",
            f"日期：{run_date}",
            f"稿件层级：{layer}",
            f"标题：《{title}》",
            f"草稿 media_id：{media_id}",
            "",
            "当前状态：待运营进入公众号后台检查排版，确认后人工发布。",
        ]
    )
    send_feishu_text(content)


if __name__ == "__main__":
    sys.exit(main())
