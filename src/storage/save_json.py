from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.content import to_serializable


def save_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_serializable(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    return path
