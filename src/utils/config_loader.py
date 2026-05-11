from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def load_yaml_config(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required. Please run: pip install -r requirements.txt")
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}
