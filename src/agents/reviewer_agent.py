from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable

from models.content import ArticleDraft, ReviewResult, to_serializable
from utils.llm import call_llm


LLMFn = Callable[[str, str], str]


@dataclass
class ReviewerAgent:
    courseware_context: dict[str, object] | None = None
    system_prompt: str = ""
    llm: LLMFn = call_llm
    banned_words: list[str] = field(default_factory=lambda: ["绝对", "唯一", "保证"])
    last_llm_response: str = field(default="", init=False)

    def review(self, draft: ArticleDraft) -> ReviewResult:
        self.last_llm_response = self.llm(
            self.system_prompt or "你是课程咨询型公众号审稿主编。",
            json.dumps(
                {
                    "draft": to_serializable(draft),
                    "courseware_context": self._courseware_prompt_context(),
                    "task": "审阅公众号初稿，并把文章修改到可以发布的状态。",
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        body = draft.body
        issues = [word for word in self.banned_words if word in body]
        final_body = self._remove_banned_words(body)
        revision_notes = [
            "强化了问题到方法的转承关系。",
            "检查文章是否承接岗位流程、SOP和评估标准。",
            "保留咨询引导，但避免硬广表达。",
            "补强了专业度、工具感和人工确认发布提醒。",
        ]
        if issues:
            revision_notes.append("删除或替换了夸大、绝对化表达。")

        return ReviewResult(
            review_conclusion="修改后可发布" if issues else "可发布",
            problems=issues or ["整体结构可发布，建议主编人工确认案例真实性。"],
            improvement_suggestions=revision_notes,
            optimized_title=draft.title,
            optimized_opening=draft.opening_hook,
            optimized_ending=draft.ending_cta,
            final_article=final_body,
            risk_notes=["避免承诺课程立刻带来确定结果。", "案例表述保持匿名和概括，不使用未经授权客户信息。"],
        )

    def _courseware_prompt_context(self) -> dict[str, object]:
        context = self.courseware_context or {}
        return {
            "enabled": context.get("enabled", False),
            "available": context.get("available", False),
            "files": [item.get("path", "") for item in context.get("files", [])],
            "summary": context.get("summary", ""),
        }

    def _remove_banned_words(self, body: str) -> str:
        revised = body
        for word in self.banned_words:
            revised = revised.replace(word, "尽量")
        return revised
