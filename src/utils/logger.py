from __future__ import annotations

from datetime import datetime


def log_info(message: str) -> None:
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {message}")
