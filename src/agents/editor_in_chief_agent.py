from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from models.content import ContentTopic, EditorialDecision, to_serializable
from utils.llm import call_llm


LLMFn = Callable[[str, str], str]


@dataclass
class EditorInChiefAgent:
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
                    "task": "从 3 个选题中选出今天最值得写的 1 个主选题。",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        scores = {topic.layer: self._score_topic(topic, calendar_item) for topic in topics}
        selected_topic = max(
            topics,
            key=lambda topic: sum(scores[topic.layer].values()),
        )
        column = ""
        if calendar_item:
            column = f"今天栏目是 {calendar_item.get('code')}「{calendar_item.get('column')}」，"

        return EditorialDecision(
            selected_topic=selected_topic,
            scores=scores,
            rationale=(
                f"{column}今日主选题选择 {selected_topic.layer} 层，因为它在读者痛点、业务相关性和咨询承接上综合得分最高。"
            ),
            editor_note="写作时要先讲清老板的真实困境，再给出可执行方法，最后轻量引导咨询。",
        )

    def _score_topic(
        self,
        topic: ContentTopic,
        calendar_item: dict[str, Any] | None = None,
    ) -> dict[str, int]:
        base_scores = {
            "C": {"传播价值": 28, "精准流量价值": 20, "专业信任价值": 18, "业务转化价值": 16, "是否符合本周内容节奏": 18},
            "E": {"传播价值": 24, "精准流量价值": 26, "专业信任价值": 22, "业务转化价值": 22, "是否符合本周内容节奏": 20},
            "S": {"传播价值": 18, "精准流量价值": 24, "专业信任价值": 28, "业务转化价值": 30, "是否符合本周内容节奏": 20},
        }
        scores = dict(base_scores.get(
            topic.layer,
            {"传播价值": 20, "精准流量价值": 20, "专业信任价值": 20, "业务转化价值": 20, "是否符合本周内容节奏": 20},
        ))
        if calendar_item and self._matches_calendar_layer(topic, calendar_item):
            scores["是否符合本周内容节奏"] += 30
        return scores

    def _matches_calendar_layer(self, topic: ContentTopic, calendar_item: dict[str, Any]) -> bool:
        code = str(calendar_item.get("code", ""))
        calendar_layer = str(calendar_item.get("layer", ""))
        return code.startswith(topic.layer) or calendar_layer in topic.layer_name
