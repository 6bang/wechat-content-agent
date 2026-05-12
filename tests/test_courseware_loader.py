from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from utils.courseware_loader import load_courseware_context


def test_load_courseware_context_reads_markdown(tmp_path: Path, monkeypatch) -> None:
    courseware_root = tmp_path / "6bang-courseware"
    courseware_root.mkdir()
    (courseware_root / "01_课程总纲").mkdir()
    (courseware_root / "01_课程总纲" / "岗位流程.md").write_text(
        "先找流程，再找方法，最后找人跑。用 S/A/B/C 标准评估岗位流程。",
        encoding="utf-8",
    )

    monkeypatch.setenv("ENABLE_COURSEWARE_CONTEXT", "true")
    monkeypatch.setenv("COURSEWARE_PATH", str(courseware_root))
    monkeypatch.setenv("COURSEWARE_REFERENCE_PATHS", "01_课程总纲")

    context = load_courseware_context(tmp_path, {"code": "S1", "column": "SOP流程课"})

    assert context["enabled"] is True
    assert context["available"] is True
    assert context["files"][0]["path"] == "01_课程总纲/岗位流程.md"
    assert "先找流程" in context["summary"]
