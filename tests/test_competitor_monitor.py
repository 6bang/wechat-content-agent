from __future__ import annotations

import sys
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from monitor.competitor_monitor import run_competitor_monitor


def test_competitor_monitor_creates_report_without_api_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("JUSTONE_API_KEY", raising=False)
    monkeypatch.setenv("ENABLE_FEISHU", "false")

    config = tmp_path / "competitor_accounts.yaml"
    config.write_text(
        """
competitor_accounts:
  - name: 笔记侠
    wxid: ""
    focus: 商业案例
  - name: 刘润
    wxid: runliu-pub
    focus: 商业认知
""".strip(),
        encoding="utf-8",
    )

    result = run_competitor_monitor(
        run_date=date(2026, 5, 15),
        config_path=config,
        output_root=tmp_path / "outputs",
        send_to_feishu=False,
    )

    report_path = Path(result["report_path"])
    report = report_path.read_text(encoding="utf-8")

    assert report_path.exists()
    assert "公众号对标账号每日监控" in report
    assert "笔记侠" in report
    assert "待配置wxid" in report
    assert "待配置API" in report
