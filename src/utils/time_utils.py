from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "Asia/Shanghai"


def today_iso() -> str:
    return datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date().isoformat()
