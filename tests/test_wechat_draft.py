from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from publish.wechat_draft import markdown_to_wechat_html, sync_output_to_wechat_draft


def test_markdown_to_wechat_html_converts_headings_and_lists() -> None:
    html = markdown_to_wechat_html(
        """
# 标题

## 小标题

- 第一条
- 第二条

正文 **重点**。
""".strip()
    )

    assert "<h1" in html
    assert "<h2" in html
    assert "<ul" in html
    assert "<strong>重点</strong>" in html


def test_markdown_to_wechat_html_converts_images(tmp_path: Path) -> None:
    image_path = tmp_path / "qr.jpg"
    image_path.write_bytes(b"fake-image")

    html = markdown_to_wechat_html(
        "![打开图片长按识别二维码添加我的微信](qr.jpg)",
        output_dir=tmp_path,
        image_url_resolver=lambda image_src: f"https://img.example.com/{image_src}",
    )

    assert "<img" in html
    assert "https://img.example.com/qr.jpg" in html
    assert "打开图片长按识别二维码添加我的微信" in html


def test_wechat_draft_dry_run_reads_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs" / "2026-05-11"
    output_dir.mkdir(parents=True)
    (output_dir / "wechat_ready_article.md").write_text(
        """
# 为什么老板越忙，公司越乱？

正文第一段。
""".strip(),
        encoding="utf-8",
    )
    (output_dir / "publish_package.md").write_text(
        """
## 公众号摘要
1. 这是一篇给电商老板看的管理文章。
""".strip(),
        encoding="utf-8",
    )

    result = sync_output_to_wechat_draft(output_dir, dry_run=True)

    assert result["dry_run"] is True
    assert result["title"] == "为什么老板越忙，公司越乱？"
    assert result["digest"] == "这是一篇给电商老板看的管理文章。"
    assert result["html_chars"] > 0
