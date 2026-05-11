from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any


@dataclass
class ContentTopic:
    topic_id: str
    title: str
    layer: str
    layer_name: str
    target_user: str
    user_pain: str
    content_angle: str
    opening_hook: str
    core_point: str
    article_structure: list[str]
    case_direction: str
    conversion_value: str
    suitable_product: str
    recommended_score: int
    reason: str

    @property
    def target_reader(self) -> str:
        return self.target_user

    @property
    def pain_point(self) -> str:
        return self.user_pain

    @property
    def core_insight(self) -> str:
        return self.core_point

    @property
    def conversion_intent(self) -> str:
        return self.conversion_value

    @property
    def material_suggestions(self) -> list[str]:
        return [self.case_direction, self.suitable_product]


@dataclass
class EditorialDecision:
    scoring_table: dict[str, dict[str, int]]
    selected_topic: ContentTopic
    selection_reason: str
    article_positioning: str
    target_user: str
    writing_direction: str
    avoid_direction: str
    must_include_points: list[str]
    conversion_suggestion: str
    final_title_suggestion: str

    @property
    def scores(self) -> dict[str, dict[str, int]]:
        return self.scoring_table

    @property
    def rationale(self) -> str:
        return self.selection_reason

    @property
    def editor_note(self) -> str:
        return self.writing_direction


@dataclass
class ArticleDraft:
    title: str
    article_type: str
    target_user: str
    core_pain: str
    core_point: str
    opening_hook: str
    outline: list[str]
    case_design: dict[str, str]
    golden_sentences: list[str]
    full_draft: str
    ending_cta: str
    topic: ContentTopic

    @property
    def body(self) -> str:
        return self.full_draft


@dataclass
class ReviewResult:
    review_conclusion: str
    problems: list[str]
    improvement_suggestions: list[str]
    optimized_title: str
    optimized_opening: str
    optimized_ending: str
    final_article: str
    risk_notes: list[str]

    @property
    def approved(self) -> bool:
        return self.review_conclusion in {"可发布", "修改后可发布"}

    @property
    def issues(self) -> list[str]:
        return self.problems

    @property
    def revision_notes(self) -> list[str]:
        return self.improvement_suggestions

    @property
    def final_title(self) -> str:
        return self.optimized_title

    @property
    def final_body(self) -> str:
        return self.final_article


@dataclass
class PublishPackage:
    title: str
    title_options: list[str]
    cover_copy: dict[str, str]
    digest: list[str]
    layout_suggestions: list[str]
    moments_copy: list[str]
    group_copy: list[str]
    private_message_copy: str
    comment_questions: list[str]
    repurpose_suggestions: list[str]
    data_review_template: list[str]
    body: str
    selected_layer: str

    @property
    def cover_main_title(self) -> str:
        return self.cover_copy.get("main_title", self.title)

    @property
    def cover_subtitle(self) -> str:
        return self.cover_copy.get("subtitle", "")

    @property
    def summary(self) -> str:
        return self.digest[0] if self.digest else ""

    @property
    def moments_copy_options(self) -> list[str]:
        return self.moments_copy

    @property
    def community_copy_options(self) -> list[str]:
        return self.group_copy

    @property
    def direct_message_script(self) -> str:
        return self.private_message_copy

    @property
    def review_metrics(self) -> list[str]:
        return self.data_review_template

    @property
    def tags(self) -> list[str]:
        return ["电商运营", "电商管理", self.selected_layer, "流程化组织"]


def to_serializable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_serializable(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [to_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_serializable(item) for key, item in value.items()}
    return value
