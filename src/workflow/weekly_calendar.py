from __future__ import annotations

from datetime import date, timedelta


THEMES = ["方法论", "案例拆解", "行业观察", "工具模板", "复盘总结", "轻观点", "下周预告"]


def build_weekly_calendar(start_date: date) -> list[dict[str, str]]:
    return [
        {
            "date": (start_date + timedelta(days=offset)).isoformat(),
            "theme": THEMES[offset % len(THEMES)],
            "business_context": "围绕电商老板、运营负责人和管理者当天最关心的问题生成内容。",
            "priority": "把流量、经营或团队问题引导到 SOP、流程和管理动作上。",
        }
        for offset in range(7)
    ]
