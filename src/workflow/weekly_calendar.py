from __future__ import annotations

from datetime import date, timedelta


WEEKLY_CONTENT_CALENDAR = [
    {
        "code": "C1",
        "layer": "泛流量",
        "column": "老板认知课",
        "description": "企业家故事、商业案例、经营认知、管理启发",
    },
    {
        "code": "E1",
        "layer": "行业流量",
        "column": "电商老板观察",
        "description": "电商老板痛点、行业变化、经营难题",
    },
    {
        "code": "S1",
        "layer": "专业内容",
        "column": "SOP流程课",
        "description": "流程化组织、SOP方法、目标管理、工具模板",
    },
    {
        "code": "E2",
        "layer": "行业流量",
        "column": "电商团队管理",
        "description": "运营团队、客服、美工、主管管理",
    },
    {
        "code": "S2",
        "layer": "专业内容",
        "column": "流程工具箱",
        "description": "表格、SOP、绩效、目标管理工具",
    },
    {
        "code": "C2",
        "layer": "泛流量",
        "column": "商业案例拆解",
        "description": "企业案例、创业故事、战略方法论",
    },
    {
        "code": "E3",
        "layer": "行业流量",
        "column": "一周电商复盘",
        "description": "行业观察、案例点评、老板复盘",
    },
]


def build_weekly_calendar(start_date: date) -> list[dict[str, str]]:
    monday = start_date - timedelta(days=start_date.weekday())
    weekly_items = []
    for offset, item in enumerate(WEEKLY_CONTENT_CALENDAR):
        weekly_items.append(
            {
                "date": (monday + timedelta(days=offset)).isoformat(),
                **item,
                "business_context": (
                    f"栏目编号 {item['code']}，栏目「{item['column']}」，"
                    f"内容方向: {item['description']}。"
                ),
                "priority": "兼顾专业信任、精准流量和课程咨询转化。",
            }
        )
    return weekly_items


def get_calendar_code(current_date: date) -> str:
    return WEEKLY_CONTENT_CALENDAR[current_date.weekday()]["code"]
