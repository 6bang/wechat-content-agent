from __future__ import annotations

from pathlib import Path
from typing import Any

from storage.save_article import save_article
from storage.save_json import save_json


def ensure_output_dir(root_dir: Path, publish_date: str) -> Path:
    output_dir = root_dir / "outputs" / publish_date
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_markdown_output(output_dir: Path, filename: str, content: str) -> Path:
    return save_article(output_dir / filename, content)


def save_json_output(output_dir: Path, filename: str, payload: Any) -> Path:
    return save_json(output_dir / filename, payload)
