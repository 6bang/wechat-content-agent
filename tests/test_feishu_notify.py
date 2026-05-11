from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from notify.feishu_notify import get_feishu_webhook_url, webhook_env_for_role


def test_webhook_env_for_role() -> None:
    assert webhook_env_for_role("选题策划 Agent") == "FEISHU_TOPIC_WEBHOOK_URL"
    assert webhook_env_for_role("内容编辑 Agent") == "FEISHU_WRITER_WEBHOOK_URL"
    assert webhook_env_for_role("总控 Agent") == "FEISHU_CONTROLLER_WEBHOOK_URL"
    assert webhook_env_for_role("未知 Agent") == "FEISHU_WEBHOOK_URL"


def test_get_feishu_webhook_url_falls_back(monkeypatch) -> None:
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "fallback")
    monkeypatch.delenv("FEISHU_WRITER_WEBHOOK_URL", raising=False)

    selected_env, webhook_url = get_feishu_webhook_url("FEISHU_WRITER_WEBHOOK_URL")

    assert selected_env == "FEISHU_WEBHOOK_URL"
    assert webhook_url == "fallback"
