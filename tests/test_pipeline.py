from __future__ import annotations

import sys
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from workflow.daily_pipeline import run_daily_pipeline


def test_daily_pipeline_creates_publish_package(tmp_path: Path) -> None:
    root = tmp_path / "project"
    (root / "config").mkdir(parents=True)
    (root / "outputs").mkdir()
    (root / "config" / "brand.yaml").write_text(
        """
brand:
  name: 测试品牌
  target_users:
    - 电商老板
  core_products:
    - 电商SOP流程化
""".strip(),
        encoding="utf-8",
    )
    (root / "config" / "content_calendar.yaml").write_text(
        """
weekly_calendar:
  monday:
    code: C1
    layer: 泛流量
    column: 老板认知课
    description: 企业经营认知
""".strip(),
        encoding="utf-8",
    )
    (root / "prompts").mkdir()
    for name in [
        "topic_agent.md",
        "editor_in_chief_agent.md",
        "writer_agent.md",
        "reviewer_agent.md",
        "publisher_agent.md",
    ]:
        (root / "prompts" / name).write_text("mock prompt", encoding="utf-8")

    result = run_daily_pipeline(root, run_date=date(2026, 5, 11))
    package = result["publish_package"]
    output_dir = root / "outputs" / "2026-05-11"

    assert len(result["topics"]) == 3
    assert result["calendar_item"]["code"] == "C1"
    assert result["decision"].selected_topic.layer == "C"
    assert package.title
    assert package.direct_message_script
    assert result["review"].approved is True
    assert (output_dir / "topics.json").exists()
    assert (output_dir / "topics.md").exists()
    assert (output_dir / "selected_topic.md").exists()
    assert (output_dir / "draft.md").exists()
    assert (output_dir / "review.md").exists()
    assert (output_dir / "final_article.md").exists()
    assert (output_dir / "publish_package.md").exists()
    assert (output_dir / "feishu_message.md").exists()
