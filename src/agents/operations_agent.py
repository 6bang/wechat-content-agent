from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from models.content import ContentTopic, PublishPackage, ReviewResult, to_serializable
from utils.llm import call_llm


LLMFn = Callable[[str, str], str]


@dataclass
class OperationsAgent:
    courseware_context: dict[str, object] | None = None
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
                    "courseware_context": self._courseware_prompt_context(),
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
            cover_copy={
                "main_title": self._build_cover_main_title(topic),
                "subtitle": self._build_cover_subtitle(topic),
                "visual_suggestion": "使用电商团队会议、流程看板或老板复盘场景，画面简洁、有管理感。",
            },
            digest=[
                summary,
                f"这篇文章从{topic.layer_name}角度，拆解{topic.user_pain}",
                f"给电商老板一个可执行提醒：{topic.core_point}",
            ],
            layout_suggestions=self._build_layout_suggestions(),
            moments_copy=self._build_moments_copy_options(topic),
            group_copy=self._build_community_copy_options(topic),
            private_message_copy=self._build_direct_message_script(topic),
            comment_questions=self._build_comment_questions(topic),
            repurpose_suggestions=[
                "适合拆成短视频：老板越忙，公司越乱的三个信号。",
                "适合做朋友圈长图：岗位流程梳理的3个检查点。",
                "适合沉淀成销售素材：客户咨询时用于解释为什么要先梳理岗位流程。",
                "适合放进课程案例库：作为运营岗位管理、SOP或流程化组织章节案例。",
            ],
            data_review_template=self._build_review_metrics(),
            body=review.final_body,
            selected_layer=topic.layer,
        )

    def _courseware_prompt_context(self) -> dict[str, object]:
        context = self.courseware_context or {}
        return {
            "enabled": context.get("enabled", False),
            "available": context.get("available", False),
            "files": [item.get("path", "") for item in context.get("files", [])],
            "summary": context.get("summary", ""),
        }

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
            "小标题使用问题式标题，方便老板快速扫读。",
            "参考爆文排版：短段落、强小标题、关键句单独成段。",
            "正文每段尽量控制在手机端 3 行以内，段落之间留一行空白。",
            "开头 300 字要让老板有情绪代入：怕招错人、怕钱白花、怕团队复制不了。",
            "金句加粗，适合截图转发。",
            "方法部分必须穿插工具截图建议，如知识库截图、多维表截图、流程看板截图。",
            "案例后放一张流程表或看板图，增强平台推荐所需的信息增量。",
            "每段控制在 3-5 行，减少手机阅读压力。",
            "二维码放在结尾转化提醒之后，文案用领取资料/流程表/诊断表，不要硬卖课。",
            "结尾引导放在互动问题后，用轻咨询口吻。",
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
            "打开率",
            "点赞率",
            "在看率",
            "分享率",
            "收藏率",
            "留言数",
            "新增关注",
            "转发到朋友圈和社群次数",
            "评论区有效问题数量",
            "私信咨询数量",
            "课程咨询数",
            "线索质量",
            "下次优化建议",
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
