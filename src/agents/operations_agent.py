from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from models.content import ContentTopic, PublishPackage, ReviewResult, to_serializable
from utils.llm import call_llm


LLMFn = Callable[[str, str], str]


@dataclass
class OperationsAgent:
    system_prompt: str = ""
    llm: LLMFn = call_llm
    last_llm_response: str = field(default="", init=False)

    def build_publish_package(self, topic: ContentTopic, review: ReviewResult) -> PublishPackage:
        self.last_llm_response = self.llm(
            self.system_prompt or "你是课程咨询型公众号发布运营 Agent。",
            json.dumps(
                {
                    "topic": to_serializable(topic),
                    "review": to_serializable(review),
                    "task": "根据定稿文章生成发布包。",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        summary = self._build_summary(topic)
        return PublishPackage(
            title=review.final_title,
            title_options=self._build_title_options(topic, review),
            cover_main_title=self._build_cover_main_title(topic),
            cover_subtitle=self._build_cover_subtitle(topic),
            summary=summary,
            layout_suggestions=self._build_layout_suggestions(),
            moments_copy_options=self._build_moments_copy_options(topic),
            community_copy_options=self._build_community_copy_options(topic),
            direct_message_script=self._build_direct_message_script(topic),
            comment_questions=self._build_comment_questions(topic),
            review_metrics=self._build_review_metrics(),
            tags=["电商运营", "电商管理", topic.layer_name, "流程化组织"],
            body=review.final_body,
            selected_layer=topic.layer,
        )

    def _build_title_options(self, topic: ContentTopic, review: ReviewResult) -> list[str]:
        return [
            review.final_title,
            f"{topic.title}，很多老板第一步就做错了",
            f"团队越忙越乱？先看懂这件事",
        ]

    def _build_summary(self, topic: ContentTopic) -> str:
        return f"{topic.pain_point} 这篇文章从 {topic.layer_name} 角度，拆解背后的管理问题和可执行动作。"

    def _build_cover_main_title(self, topic: ContentTopic) -> str:
        return topic.title

    def _build_cover_subtitle(self, topic: ContentTopic) -> str:
        return f"{topic.layer}层内容｜给电商老板的管理提醒"

    def _build_layout_suggestions(self) -> list[str]:
        return [
            "开头痛点段落控制在 3 段内，先让老板看到自己的问题。",
            "方法部分用编号列表，方便收藏和转发给团队。",
            "结尾转化用轻咨询口吻，不使用强销售表达。",
        ]

    def _build_moments_copy_options(self, topic: ContentTopic) -> list[str]:
        return [
            f"很多电商团队卡住，不是缺努力，而是缺一套能落地的流程。今天这篇聊: {topic.title}",
            f"如果你是电商老板，最近觉得团队越忙越乱，可以看看这篇: {topic.title}",
            f"运营问题最后往往会变成管理问题。今天这篇把背后的逻辑拆开讲清楚。",
        ]

    def _build_community_copy_options(self, topic: ContentTopic) -> list[str]:
        return [
            (
                "今天的文章适合老板和运营负责人一起看。\n"
                f"主题: {topic.title}\n"
                "如果你的团队也经常靠临时沟通推进，可以重点看文中的 3 个动作。"
            ),
            (
                f"分享一篇关于「{topic.title}」的文章。\n"
                "建议老板、运营主管、客服主管、美工主管一起看，重点讨论哪些动作要流程化。"
            ),
        ]

    def _build_review_metrics(self) -> list[str]:
        return [
            "阅读完成率",
            "收藏率",
            "转发到朋友圈和社群次数",
            "评论区有效问题数量",
            "私信咨询数量",
            "课程或诊断关键词触发数量",
        ]

    def _build_direct_message_script(self, topic: ContentTopic) -> str:
        return (
            "你好，我看到你关注的是电商团队流程和运营管理问题。\n"
            f"这篇文章讲的核心卡点是: {topic.pain_point}\n"
            "如果你愿意，我可以先帮你梳理一下店铺当前最需要标准化的 3 个流程。"
        )

    def _build_comment_questions(self, topic: ContentTopic) -> list[str]:
        return [
            "你们团队现在最容易卡住的是目标拆解、过程跟进，还是复盘激励？",
            "你觉得 SOP 在团队里没人执行，最大的原因是什么？",
            f"关于「{topic.title}」，你最想看哪类案例？",
        ]
