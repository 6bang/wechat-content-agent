from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from workflow.daily_pipeline import get_today_calendar_item


CALENDAR = {
    "weekly_calendar": {
        "monday": {
            "code": "C1",
            "layer": "泛流量",
            "column": "老板认知课",
            "description": "企业家故事、商业案例、经营认知、管理启发",
        },
        "tuesday": {
            "code": "E1",
            "layer": "行业流量",
            "column": "电商老板观察",
            "description": "电商老板痛点、行业变化、经营难题",
        },
        "wednesday": {
            "code": "S1",
            "layer": "专业内容",
            "column": "SOP流程课",
            "description": "流程化组织、SOP方法、目标管理、工具模板",
        },
        "thursday": {
            "code": "E2",
            "layer": "行业流量",
            "column": "电商团队管理",
            "description": "运营团队、客服、美工、主管管理",
        },
        "friday": {
            "code": "S2",
            "layer": "专业内容",
            "column": "流程工具箱",
            "description": "表格、SOP、绩效、目标管理工具",
        },
        "saturday": {
            "code": "C2",
            "layer": "泛流量",
            "column": "商业案例拆解",
            "description": "企业案例、创业故事、战略方法论",
        },
        "sunday": {
            "code": "E3",
            "layer": "行业流量",
            "column": "一周电商复盘",
            "description": "行业观察、案例点评、老板复盘",
        },
    }
}


def test_weekly_calendar_returns_expected_codes() -> None:
    monday = date(2026, 5, 11)
    expected_codes = ["C1", "E1", "S1", "E2", "S2", "C2", "E3"]

    for offset, expected_code in enumerate(expected_codes):
        item = get_today_calendar_item(CALENDAR, monday + timedelta(days=offset))
        assert item["code"] == expected_code
