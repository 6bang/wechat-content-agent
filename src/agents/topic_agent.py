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
            topic_id="C",
            title="为什么老板越忙，公司越乱？",
            layer="C",
            layer_name=config.get("name", "泛流量"),
            target_user="电商老板、创业者、管理者",
            user_pain="公司变大后，老板每天救火，但团队依然靠人盯人推动。",
            content_angle=f"从老板忙乱切入，讲企业从人治走向系统化的管理认知。背景: {context}",
            opening_hook="很多老板都有一个感受：公司小的时候，自己盯一盯还能跑；公司一大，事情就开始失控。",
            core_point="老板越忙，不一定代表公司越好，可能说明系统越弱。",
            article_structure=["现象", "冲突", "真相", "解决方案"],
            case_direction="一个老板从亲自盯客服、运营、美工，到用目标和流程推动团队的转变。",
            conversion_value="可自然引出流程化组织、目标管理和管理升级咨询。",
            suitable_product="打造流程化组织",
            recommended_score=88,
            reason="标题有老板痛点和冲突感，适合 C 层破圈，也能承接组织管理咨询。",
        )

    def _build_e_layer_topic(self, config: dict[str, Any], context: str) -> ContentTopic:
        return ContentTopic(
            topic_id="E",
            title="为什么电商老板越来越不敢招运营？",
            layer="E",
            layer_name=config.get("name", "行业流量"),
            target_user="电商老板、运营负责人、电商管理者",
            user_pain="招运营成本越来越高，但结果不稳定，老板不知道怎么判断能力和产出。",
            content_angle=f"从运营岗位能力标准和绩效机制切入，讲电商公司为什么不能只靠招人解决增长。背景: {context}",
            opening_hook="很多电商老板不是不想招人，而是越来越怕招错人。",
            core_point="运营不稳定，表面是人的问题，底层是岗位标准、流程和绩效机制没搭好。",
            article_structure=["问题", "原因", "方法", "案例", "总结"],
            case_direction="一个店铺连续换运营都没起色，最后通过岗位SOP和绩效看板稳定产出的案例。",
            conversion_value="可引出运营岗位管理体系和薪酬绩效激励课程。",
            suitable_product="运营岗位管理体系",
            recommended_score=91,
            reason="高度精准命中电商老板招人、用人、分钱痛点，适合 E 层筛选精准用户。",
        )

    def _build_s_layer_topic(self, config: dict[str, Any], priority: str) -> ContentTopic:
        return ContentTopic(
            topic_id="S",
            title="新品SOP流程，为什么第一步不是写详情页？",
            layer="S",
            layer_name=config.get("name", "专业内容"),
            target_user="电商老板、运营负责人、产品负责人",
            user_pain="很多公司上新动作很快，但前置选品和打法没验证，后面详情页、投流、直播全浪费。",
            content_angle=f"从新品SOP前置条件讲流程化，强调先验证产品机会、目标人群和打法，再进入执行。重点: {priority}",
            opening_hook="很多团队一上新品，第一反应就是催详情页，结果钱花了、图做了、货备了，最后发现方向错了。",
            core_point="新品SOP第一步不是写详情页，而是验证选品逻辑和打品路径。",
            article_structure=["错误认知", "正确认知", "流程步骤", "工具模板", "行动建议"],
            case_direction="一个新品因为没做前置验证导致库存积压，后来用开品看板降低试错成本。",
            conversion_value="可引出电商SOP流程化、新品SOP流程和爆款复制体系课程。",
            suitable_product="新品SOP流程",
            recommended_score=94,
            reason="专业度强、工具感强，适合 S 层建立信任并承接课程咨询。",
        )
