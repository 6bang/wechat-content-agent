from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any


@dataclass
class ContentTopic:
    layer: str
    layer_name: str
    title: str
    core_insight: str
    target_reader: str
    pain_point: str
    conversion_intent: str
    material_suggestions: list[str]


@dataclass
class EditorialDecision:
    selected_topic: ContentTopic
    scores: dict[str, dict[str, int]]
    rationale: str
    editor_note: str


@dataclass
class ArticleDraft:
    title: str
    outline: list[str]
    body: str
    topic: ContentTopic


@dataclass
class ReviewResult:
    approved: bool
    issues: list[str]
    revision_notes: list[str]
    final_title: str
    final_body: str


@dataclass
class PublishPackage:
    title: str
    title_options: list[str]
    cover_main_title: str
    cover_subtitle: str
    summary: str
    layout_suggestions: list[str]
    moments_copy_options: list[str]
    community_copy_options: list[str]
    direct_message_script: str
    comment_questions: list[str]
    review_metrics: list[str]
    tags: list[str]
    body: str
    selected_layer: str


def to_serializable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_serializable(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [to_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_serializable(item) for key, item in value.items()}
    return value
