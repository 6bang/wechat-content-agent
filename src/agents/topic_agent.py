from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from models.content import ContentTopic
from utils.llm import call_llm


LLMFn = Callable[[str, str], str]


@dataclass
class TopicAgent:
    brand: dict[str, Any]
    layers: dict[str, Any]
    system_prompt: str = ""
    llm: LLMFn = call_llm
    last_llm_response: str = field(default="", init=False)

    def generate_topics(self, calendar_item: dict[str, Any]) -> list[ContentTopic]:
        self.last_llm_response = self.llm(
            self.system_prompt or "你是课程咨询型公众号选题策划 Agent。",
            json.dumps(
                {
                    "brand": self.brand,
                    "layers": self.layers,
                    "calendar_item": calendar_item,
                    "task": "生成 C/E/S 三个公众号选题。",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        layer_config = self.layers.get("layers", {})
        context = calendar_item.get("business_context", "电商老板正在面对增长放缓和团队管理压力。")
        priority = calendar_item.get("priority", "把经营问题拆成可执行的管理动作。")

        return [
            self._build_c_layer_topic(layer_config.get("C", {}), context),
            self._build_e_layer_topic(layer_config.get("E", {}), context),
            self._build_s_layer_topic(layer_config.get("S", {}), priority),
        ]

    def _build_c_layer_topic(self, config: dict[str, Any], context: str) -> ContentTopic:
        return ContentTopic(
            layer="C",
            layer_name=config.get("name", "泛流量内容"),
            title="一个电商老板最容易误判的增长真相",
            core_insight=f"很多经营焦虑表面是流量问题，底层是老板对组织能力的判断问题。背景: {context}",
            target_reader="电商老板、创业者、业务负责人",
            pain_point="知道要增长，但分不清到底是市场问题、团队问题还是管理问题。",
            conversion_intent=config.get("conversion_role", "建立商业认知和信任"),
            material_suggestions=["企业经营故事", "老板决策场景", "增长误判案例"],
        )

    def _build_e_layer_topic(self, config: dict[str, Any], context: str) -> ContentTopic:
        return ContentTopic(
            layer="E",
            layer_name=config.get("name", "行业流量内容"),
            title="流量越来越贵后，电商团队真正要补的不是人",
            core_insight=f"行业变化会放大团队协同问题，缺人常常只是缺流程的外在表现。背景: {context}",
            target_reader="电商运营负责人、电商老板、电商管理者",
            pain_point="投流、内容、直播、货架协同越来越复杂，但团队靠临时沟通推进。",
            conversion_intent=config.get("conversion_role", "把行业问题引向运营体系问题"),
            material_suggestions=["行业趋势", "运营团队岗位分工", "大促协同场景"],
        )

    def _build_s_layer_topic(self, config: dict[str, Any], priority: str) -> ContentTopic:
        return ContentTopic(
            layer="S",
            layer_name=config.get("name", "专业内容"),
            title="大促前，电商团队最该补上的不是方案，而是一张 SOP 表",
            core_insight=f"把目标、动作、负责人、检查点写进 SOP，团队才不会只靠老板追进度。重点: {priority}",
            target_reader="电商老板、运营总监、店铺负责人",
            pain_point="目标拆了，动作散了，复盘时才发现关键节点没人负责。",
            conversion_intent=config.get("conversion_role", "承接课程咨询和私域转化"),
            material_suggestions=["大促筹备流程", "SOP 表格字段", "目标拆解模板", "绩效追踪方法"],
        )
