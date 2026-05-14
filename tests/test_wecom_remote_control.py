from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from remote.wecom_remote_control import extract_layer, parse_remote_command


def test_parse_remote_command_reruns_all_articles() -> None:
    command = parse_remote_command("重写今日三篇")

    assert command.action == "daily_pipeline"
    assert command.stage == "all"
    assert command.should_dispatch is True


def test_parse_remote_command_syncs_layer_c() -> None:
    command = parse_remote_command("2026-05-14 发C")

    assert command.action == "sync_wechat_draft"
    assert command.layer == "C"
    assert command.run_date == "2026-05-14"


def test_parse_remote_command_stage_topics() -> None:
    command = parse_remote_command("只跑选题")

    assert command.action == "daily_pipeline"
    assert command.stage == "topics"


def test_parse_remote_command_unknown_returns_help() -> None:
    command = parse_remote_command("今天怎么样")

    assert command.should_dispatch is False
    assert command.action == "help"


def test_extract_layer_supports_chinese_layer_text() -> None:
    assert extract_layer("同步S层") == "S"
    assert extract_layer("选E篇") == "E"
