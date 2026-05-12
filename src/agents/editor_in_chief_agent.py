from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from models.content import ContentTopic, EditorialDecision, to_serializable
from utils.llm import call_llm


LLMFn = Callable[[str, str], str]


@dataclass
class EditorInChiefAgent:
    courseware_context: dict[str, Any] | None = None
    system_prompt: str = ""
    llm: LLMFn = call_llm
    last_llm_response: str = field(default="", init=False)

    def choose_topic(
        self,
        topics: list[ContentTopic],
        calendar_item: dict[str, Any] | None = None,
    ) -> EditorialDecision:
        if not topics:
            raise ValueError("No topics available for selection.")

        self.last_llm_response = self.llm(
            self.system_prompt or "你是课程咨询型公众号内容主编。",
            json.dumps(
                {
                    "topics": to_serializable(topics),
                    "calendar_item": calendar_item or {},
                    "courseware_context": self._courseware_prompt_context(),
                    "task": "从 3 个选题中评估出今天最推荐优先发布的 1 个主推选题；C/E/S三篇都会继续成稿。",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        scores = {topic.layer: self._score_topic(topic, calendar_item) for topic in topics}
        selected_topic = max(
            topics,
            key=lambda topic: (
                self._matches_calendar_layer(topic, calendar_item or {}),
                scores[topic.layer]["total_score"],
            ),
        )
        column = ""
        if calendar_item:
            column = f"今天栏目是 {calendar_item.get('code')}「{calendar_item.get('column')}」，"

        return EditorialDecision(
            scoring_table=scores,
            selected_topic=selected_topic,
            selection_reason=(
                f"{column}今日优先推荐 {selected_topic.layer} 层，因为它符合当天栏目节奏，并且在读者痛点、业务相关性和咨询承接上综合得分最高；C/E/S三篇仍会全部成稿，最终由人工选择发布。"
            ),
            article_positioning=self._positioning_for(selected_topic),
            target_user=selected_topic.target_user,
            writing_direction="先讲清老板的真实困境，再拆解背后的流程、岗位或目标管理问题，最后给出可执行动作。",
            avoid_direction="不要写成泛泛观点文，不要只讲情绪，不要硬广课程，也不要承诺立刻见效。",
            must_include_points=[
                "一个真实的老板或团队管理场景",
                "问题背后的流程、标准或绩效原因",
                "3个可以立刻执行的动作",
                "一句能被转发的管理金句",
                "自然引出课程、咨询或工具",
            ],
            conversion_suggestion=selected_topic.suitable_product,
            final_title_suggestion=selected_topic.title,
        )

    def _courseware_prompt_context(self) -> dict[str, Any]:
        context = self.courseware_context or {}
        return {
            "enabled": context.get("enabled", False),
            "available": context.get("available", False),
            "files": [item.get("path", "") for item in context.get("files", [])],
            "summary": context.get("summary", ""),
        }

    def _score_topic(
        self,
        topic: ContentTopic,
        calendar_item: dict[str, Any] | None = None,
    ) -> dict[str, int]:
        base_scores = {
            "C": {"pain_score": 4, "spread_score": 5, "precision_score": 3, "trust_score": 3, "conversion_score": 3, "calendar_score": 3},
            "E": {"pain_score": 5, "spread_score": 4, "precision_score": 5, "trust_score": 4, "conversion_score": 4, "calendar_score": 3},
            "S": {"pain_score": 5, "spread_score": 3, "precision_score": 5, "trust_score": 5, "conversion_score": 5, "calendar_score": 3},
        }
        scores = dict(base_scores.get(
            topic.layer,
            {"pain_score": 3, "spread_score": 3, "precision_score": 3, "trust_score": 3, "conversion_score": 3, "calendar_score": 3},
        ))
        if calendar_item:
            scores["calendar_score"] = 5 if self._matches_calendar_layer(topic, calendar_item) else 1
        scores["total_score"] = sum(value for key, value in scores.items() if key != "total_score")
        return scores

    def _positioning_for(self, topic: ContentTopic) -> str:
        if topic.layer == "C":
            return "认知升级型"
        if topic.layer == "E":
            return "痛点共鸣型"
        return "方法论干货型"

    def _matches_calendar_layer(self, topic: ContentTopic, calendar_item: dict[str, Any]) -> bool:
        code = str(calendar_item.get("code", ""))
        calendar_layer = str(calendar_item.get("layer", ""))
        return code.startswith(topic.layer) or calendar_layer in topic.layer_name
