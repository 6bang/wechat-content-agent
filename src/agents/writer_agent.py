from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from models.content import ArticleDraft, ContentTopic, EditorialDecision, to_serializable
from utils.llm import call_llm


LLMFn = Callable[[str, str], str]


@dataclass
class WriterAgent:
    system_prompt: str = ""
    llm: LLMFn = call_llm
    last_llm_response: str = field(default="", init=False)

    def write_article(self, decision: EditorialDecision) -> ArticleDraft:
        self.last_llm_response = self.llm(
            self.system_prompt or "你是课程咨询型公众号内容编辑。",
            json.dumps(
                {
                    "decision": to_serializable(decision),
                    "task": "根据主编确定的选题生成文章大纲和公众号正文。",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        topic = decision.selected_topic
        outline = self._build_outline(topic)
        body = self._build_body(topic, outline, decision.editor_note)
        return ArticleDraft(
            title=decision.final_title_suggestion,
            article_type=decision.article_positioning,
            target_user=decision.target_user,
            core_pain=topic.user_pain,
            core_point=topic.core_point,
            opening_hook=topic.opening_hook,
            outline=outline,
            case_design={
                "案例背景": topic.case_direction,
                "案例冲突": topic.user_pain,
                "案例结果": "团队通过流程、目标和检查点降低试错成本，产出更稳定。",
                "案例启发": "管理不是靠老板更忙，而是靠系统让团队重复做对动作。",
            },
            golden_sentences=[
                "不是员工不努力，而是公司没有标准动作。",
                "老板越忙，不一定代表公司越好，可能说明系统越弱。",
                "流程不是把人管死，而是让普通人也能做出稳定结果。",
                "管理的终点，不是老板更勤奋，而是团队能自动运转。",
                "SOP不是写给老板看的，而是写给团队重复执行的。",
            ],
            full_draft=body,
            ending_cta="如果你也想梳理店铺运营流程，可以私信关键词「诊断」，先从一个核心流程开始拆。",
            topic=topic,
        )

    def write_draft(self, topic: ContentTopic) -> dict[str, str]:
        decision = EditorialDecision(
            scoring_table={},
            selected_topic=topic,
            selection_reason="兼容旧调用。",
            article_positioning="方法论干货型",
            target_user=topic.target_user,
            writing_direction="保持结构清晰，给出可执行建议。",
            avoid_direction="不要写成泛泛观点文。",
            must_include_points=["痛点", "方法", "案例"],
            conversion_suggestion=topic.suitable_product,
            final_title_suggestion=topic.title,
        )
        draft = self.write_article(decision)
        return {"title": draft.title, "body": draft.body}

    def _build_outline(self, topic: ContentTopic) -> list[str]:
        return [
            "开头: 用一个电商老板熟悉的管理困境切入",
            f"观点: {topic.core_insight}",
            f"痛点: {topic.pain_point}",
            "拆解: 问题为什么不是单点动作能解决",
            "方法: 给出 3 个可执行管理动作",
            "案例: 用一个电商团队的真实管理场景讲透",
            "金句: 用一句老板能记住的话收住观点",
            "结尾: 用低压力方式引导留言或私信咨询",
        ]

    def _build_body(self, topic: ContentTopic, outline: list[str], editor_note: str) -> str:
        return "\n\n".join(
            [
                f"# {topic.title}",
                "## 先说一个常见场景",
                f"很多{topic.target_reader}都会遇到类似问题: {topic.pain_point}",
                "表面看，这是一个运营动作没跟上的问题。再往下看，它往往是目标、流程、责任和检查机制没有对齐。",
                "## 真正的问题在哪里",
                topic.core_insight,
                "一个团队忙不忙，并不等于它有没有效率。真正影响结果的，是关键动作有没有被拆清楚、负责人有没有被写清楚、检查点有没有被提前设计。",
                "## 可以先做的 3 个动作",
                "第一，把目标拆成动作，而不是只拆成数字。",
                "第二，把动作写进流程，而不是只放在会议纪要里。",
                "第三，把流程接到复盘和激励，不要让 SOP 变成没人看的文档。",
                "## 给老板和运营负责人的提醒",
                "当你发现团队反复救火，不一定是大家不努力，而是系统没有替大家兜住关键节点。",
                f"主编提示: {editor_note}",
                "如果你也在梳理店铺运营流程，欢迎留言说说你现在最卡的一步。",
            ]
        )
