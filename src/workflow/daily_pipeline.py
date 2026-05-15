from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from agents.editor_in_chief_agent import EditorInChiefAgent
from agents.publisher_agent import PublisherAgent
from agents.reviewer_agent import ReviewerAgent
from agents.topic_agent import TopicAgent
from agents.visual_designer_agent import VisualDesignerAgent
from agents.writer_agent import WriterAgent
from models.content import (
    ArticleDraft,
    EditorialDecision,
    PublishPackage,
    ReviewResult,
    VisualLayoutPackage,
    to_serializable,
)
from notify.email_notify import send_email_backup
from notify.feishu_doc import create_feishu_doc_from_markdown
from notify.feishu_notify import (
    notify_feishu_from_output,
    send_feishu_failure_report,
    send_feishu_stage_report,
)
from notify.wecom_notify import (
    notify_wecom_from_output,
    send_wecom_failure_report,
    send_wecom_stage_report,
)
from storage.save_article import save_article
from storage.save_json import save_json
from storage.render_visual_assets import save_visual_assets
from utils.llm import call_llm, load_env
from utils.courseware_loader import load_courseware_context, render_courseware_reference

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


ROOT_DIR = Path(__file__).resolve().parents[2]
WEEKDAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
STAGE_ORDER = ["topics", "editor", "outline", "draft", "review", "publish", "visual", "all"]

DEFAULT_LAYERS = {
    "layers": {
        "C": {"name": "泛流量内容", "conversion_role": "建立老板认知和品牌信任"},
        "E": {"name": "行业流量内容", "conversion_role": "把行业痛点引向运营管理体系问题"},
        "S": {"name": "专业内容", "conversion_role": "承接课程、咨询和企业服务转化"},
    }
}
DEFAULT_SCHEDULE = {
    "daily_run_time": "01:00",
    "timezone": "Asia/Shanghai",
    "suggested_publish_time": "18:00",
}
FEISHU_SPACER_MARKER = "<FEISHU_SPACER>"
FEISHU_ARTICLE_LINE_CHARS = 34
FEISHU_ARTICLE_PARAGRAPH_LINES = 3
WECHAT_ARTICLE_LINE_CHARS = 28
WECHAT_ARTICLE_PARAGRAPH_LINES = 3
DEFAULT_WECHAT_CONTACT_QR_PATH = "assets/wechat_contact_qr.jpg"
DEFAULT_WECHAT_RESOURCE_FOOTER_TEXT = "我这里整理一份合适品牌的打品的SOP流程\n\n如果你有需要可以找我"
DEFAULT_WECHAT_RESOURCE_IMAGE_PATHS = [
    "assets/brand_sop_flow_01.jpg",
    "assets/brand_sop_flow_02.jpg",
    "assets/brand_sop_flow_03.jpg",
    "assets/brand_sop_flow_04.jpg",
]

STAGE_REPORTS = {
    "topics": {
        "stage_name": "选题策划完成",
        "role_name": "选题策划 Agent",
        "task_name": "生成 C/E/S 三层选题",
        "status": "已完成",
        "summary": "已生成今日3个候选选题，分别对应C层泛流量、E层行业流量、S层专业内容。",
        "output_files": ["topics.json", "topics.md"],
        "next_step": "内容主编 Agent 将评估3个选题，并确定今日主选题。",
    },
    "editor": {
        "stage_name": "主编评估完成",
        "role_name": "内容主编 Agent",
        "task_name": "评估选题并给出今日推荐主推",
        "status": "已完成",
        "summary": "已根据痛点强度、传播价值、精准流量价值、专业信任价值、转化价值、节奏匹配度完成评分，并给出今日推荐主推；C/E/S三篇都会继续成稿，最终由人工选择发布。",
        "output_files": ["selected_topic.md"],
        "next_step": "内容编辑 Agent 将分别为C/E/S三个选题生成文章大纲和初稿。",
    },
    "outline": {
        "stage_name": "文章大纲完成",
        "role_name": "内容编辑 Agent",
        "task_name": "生成C/E/S三篇公众号文章大纲",
        "status": "已完成",
        "summary": "已完成C/E/S三篇文章的标题、开头钩子、核心观点、正文结构、案例设计、金句和结尾转化设计。",
        "output_files": ["articles/C/draft.md", "articles/E/draft.md", "articles/S/draft.md"],
        "next_step": "内容编辑 Agent 将继续生成C/E/S三篇公众号初稿。",
    },
    "draft": {
        "stage_name": "公众号初稿完成",
        "role_name": "内容编辑 Agent",
        "task_name": "生成C/E/S三篇公众号初稿",
        "status": "已完成",
        "summary": "已完成C/E/S三篇公众号初稿，文章包含痛点开头、案例、方法、金句和转化引导。",
        "output_files": ["articles/C/draft.md", "articles/E/draft.md", "articles/S/draft.md"],
        "next_step": "审稿 Agent 将分别进行审稿、修改和定稿。",
    },
    "review": {
        "stage_name": "审稿定稿完成",
        "role_name": "审稿 Agent",
        "task_name": "审阅C/E/S三篇初稿并生成最终定稿",
        "status": "待人工确认",
        "summary": "已完成C/E/S三篇稿件的标题、开头、逻辑、案例、方法、专业度、转化和风险检查，并输出最终定稿。",
        "output_files": ["articles/C/final_article.md", "articles/E/final_article.md", "articles/S/final_article.md"],
        "next_step": "新媒体运营 Agent 将分别生成发布包；主编可人工选择今天发布哪一篇。",
    },
    "publish": {
        "stage_name": "发布包完成",
        "role_name": "新媒体运营 Agent",
        "task_name": "生成C/E/S三篇公众号发布包",
        "status": "已完成",
        "summary": "已为C/E/S三篇文章生成公众号标题、摘要、封面文案、朋友圈文案、社群文案、私聊话术、评论区问题和数据复盘表。",
        "output_files": ["article_selection.md", "articles/C/publish_package.md", "articles/E/publish_package.md", "articles/S/publish_package.md"],
        "next_step": "视觉排版 Agent 将为C/E/S三篇文章生成配图清单、封面方向、排版方案和原创SVG示意图。",
    },
    "visual": {
        "stage_name": "视觉排版完成",
        "role_name": "视觉排版 Agent",
        "task_name": "生成C/E/S三篇文章视觉排版方案",
        "status": "已完成",
        "summary": "已为C/E/S三篇文章生成封面方向、正文配图清单、流程图、看板图、检查清单、结尾引导卡和公众号排版建议。",
        "output_files": [
            "visual_layout.md",
            "articles/C/visual_layout.md",
            "articles/E/visual_layout.md",
            "articles/S/visual_layout.md",
            "articles/C/visual_assets/cover.svg",
            "articles/E/visual_assets/cover.svg",
            "articles/S/visual_assets/cover.svg",
        ],
        "next_step": "请老板/主编从C/E/S三篇中选择一篇，运营根据视觉排版方案进入公众号草稿箱和人工发布流程。",
    },
    "complete": {
        "stage_name": "今日内容包完成",
        "role_name": "总控 Agent",
        "task_name": "完成今日公众号内容生产流水线",
        "status": "待人工发布",
        "summary": "今日公众号内容包已全部生成，包含C/E/S三篇文章、主编推荐、初稿、审稿、终稿、可复制公众号正文、发布包、视觉排版方案、飞书消息和邮件摘要。",
        "output_files": [
            "topics.md",
            "selected_topic.md",
            "article_selection.md",
            "feishu_doc_preview.md",
            "visual_layout.md",
            "articles/C/wechat_ready_article.md",
            "articles/E/wechat_ready_article.md",
            "articles/S/wechat_ready_article.md",
            "feishu_message.md",
        ],
        "next_step": "请主编从C/E/S三篇中选择一篇，运营同步到公众号草稿箱，建议今天18:00人工发布。",
    },
}


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required. Please run: pip install -r requirements.txt")
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_optional_yaml(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    data = load_yaml(path)
    merged = dict(default)
    merged.update(data)
    return merged


def beijing_today() -> date:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date()


def load_prompt(root_dir: Path, prompt_file: str) -> str:
    path = root_dir / "prompts" / prompt_file
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def get_today_calendar_item(calendar: dict[str, Any], current_date: date) -> dict[str, Any]:
    weekly_calendar = calendar.get("weekly_calendar", {})
    weekday_key = WEEKDAY_KEYS[current_date.weekday()]
    day_config = weekly_calendar.get(weekday_key)
    if not day_config:
        raise KeyError(f"Missing weekly calendar config for {weekday_key}.")

    item = dict(day_config)
    item["date"] = current_date.isoformat()
    item["weekday"] = weekday_key
    item["business_context"] = (
        f"今天是{weekday_key}，栏目编号 {item.get('code')}，栏目「{item.get('column')}」。"
        f"内容方向: {item.get('description')}。"
    )
    item["priority"] = (
        f"围绕「{item.get('column')}」服务课程、咨询、企业服务转化，"
        "让电商老板和管理者看到痛点、案例和方法。"
    )
    return item


def load_recent_topic_titles(root_dir: Path, current_date: date, max_days: int = 45) -> list[str]:
    outputs_dir = root_dir / "outputs"
    if not outputs_dir.exists():
        return []

    titles: list[str] = []
    min_date = date.fromordinal(current_date.toordinal() - max_days)
    for path in sorted(outputs_dir.glob("*/topics.json"), reverse=True):
        try:
            output_date = date.fromisoformat(path.parent.name)
        except ValueError:
            continue
        if output_date >= current_date or output_date < min_date:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for topic in payload.get("topics", []):
            title = str(topic.get("title", "")).strip()
            if title and title not in titles:
                titles.append(title)
    return titles


def output_file_path(publish_date: str, filename: str) -> str:
    return str(Path("outputs") / publish_date / filename)


def output_file_paths(publish_date: str, filenames: list[str]) -> list[str]:
    return [output_file_path(publish_date, filename) for filename in filenames]


def should_report_stage(target_stage: str, report_stage: str) -> bool:
    if report_stage == "complete":
        return target_stage in {"visual", "all"}
    return target_stage == "all" or target_stage == report_stage


def report_stage(target_stage: str, report_stage: str, publish_date: str) -> None:
    if not should_report_stage(target_stage, report_stage):
        return

    report = STAGE_REPORTS[report_stage]
    send_feishu_stage_report(
        stage_name=report["stage_name"],
        role_name=report["role_name"],
        task_name=report["task_name"],
        status=report["status"],
        summary=report["summary"],
        output_files=output_file_paths(publish_date, report["output_files"]),
        next_step=report["next_step"],
    )
    send_wecom_stage_report(
        stage_name=report["stage_name"],
        role_name=report["role_name"],
        task_name=report["task_name"],
        status=report["status"],
        summary=report["summary"],
        output_files=output_file_paths(publish_date, report["output_files"]),
        next_step=report["next_step"],
    )


def report_failure(target_stage: str, publish_date: str, error: Exception) -> None:
    report = STAGE_REPORTS.get(target_stage) or STAGE_REPORTS["complete"]
    send_feishu_failure_report(
        stage_name=report["stage_name"],
        role_name=report["role_name"],
        task_name=report["task_name"],
        error=error,
        output_files=output_file_paths(publish_date, report["output_files"]),
    )
    send_wecom_failure_report(
        stage_name=report["stage_name"],
        role_name=report["role_name"],
        task_name=report["task_name"],
        error=error,
        output_files=output_file_paths(publish_date, report["output_files"]),
    )


def render_topics(topics: list, calendar_item: dict[str, Any]) -> str:
    lines = [
        "# 今日公众号候选选题",
        "",
        f"- 日期: {calendar_item['date']}",
        f"- 今日栏目: {calendar_item.get('code')}｜{calendar_item.get('column')}",
    ]
    for topic in topics:
        material_suggestions = "、".join(topic.material_suggestions)
        lines.extend(
            [
                "",
                f"## {topic.layer}层｜{topic.title}",
                "",
                f"- 内容层级: {topic.layer_name}",
                f"- 目标用户: {topic.target_reader}",
                f"- 用户痛点: {topic.pain_point}",
                f"- 内容角度: {topic.core_insight}",
                f"- 转化价值: {topic.conversion_intent}",
                f"- 素材建议: {material_suggestions}",
            ]
        )
    return "\n".join(lines)


def render_selected_topic(decision: EditorialDecision, calendar_item: dict[str, Any]) -> str:
    topic = decision.selected_topic
    score_lines = []
    for layer, scores in decision.scores.items():
        total = scores.get("total_score", sum(value for key, value in scores.items() if key != "total_score"))
        score_detail = "，".join(f"{key}: {value}" for key, value in scores.items() if key != "total_score")
        score_lines.append(f"- {layer}层: {total} 分（{score_detail}）")

    return "\n".join(
        [
            f"# 今日主选题: {topic.title}",
            "",
            f"- 日期: {calendar_item['date']}",
            f"- 今日栏目: {calendar_item.get('code')}「{calendar_item.get('column')}」",
            f"- 内容层级: {topic.layer}层 / {topic.layer_name}",
            f"- 目标用户: {topic.target_reader}",
            f"- 用户痛点: {topic.pain_point}",
            f"- 核心观点: {topic.core_insight}",
            f"- 转化价值: {topic.conversion_intent}",
            "",
            "## 主编评分",
            *score_lines,
            "",
            "## 选择理由",
            decision.rationale,
            "",
            "## 写作方向",
            decision.writing_direction,
            "",
            "## 不要写偏的地方",
            decision.avoid_direction,
            "",
            "## 必须写到的重点",
            *[f"- {point}" for point in decision.must_include_points],
            "",
            "## 可植入课程或咨询服务",
            decision.conversion_suggestion,
        ]
    )


def build_article_decision(
    editor_decision: EditorialDecision,
    topic,
    calendar_item: dict[str, Any],
) -> EditorialDecision:
    recommended_marker = "主编推荐发布" if topic.layer == editor_decision.selected_topic.layer else "候选备选稿"
    return EditorialDecision(
        scoring_table=editor_decision.scoring_table,
        selected_topic=topic,
        selection_reason=(
            f"{topic.layer}层文章作为今日{recommended_marker}进入成稿池。"
            f"今日栏目是 {calendar_item.get('code')}「{calendar_item.get('column')}」，最终由老板/主编人工选择发布。"
        ),
        article_positioning=article_positioning_for_layer(topic.layer),
        target_user=topic.target_user,
        writing_direction=(
            "参考平台推荐型长文排版：强观察标题、强冲突开头、真实案例中段、"
            "知识库+多维表+流程可视化方法、结果清单和轻转化。"
        ),
        avoid_direction="不要写成泛泛观点文，不要只讲情绪，不要硬广课程，也不要承诺立刻见效。",
        must_include_points=[
            "一个让老板有代入感的强冲突开头",
            "问题背后的流程、标准或绩效原因",
            "知识库、多维表、流程可视化等工具感方法",
            "一个电商团队案例或场景",
            "自然引出流程表、诊断表或咨询服务",
        ],
        conversion_suggestion=topic.suitable_product,
        final_title_suggestion=topic.title,
    )


def article_positioning_for_layer(layer: str) -> str:
    if layer == "C":
        return "认知升级型"
    if layer == "E":
        return "痛点共鸣型"
    return "方法论干货型"


def article_dir(output_dir: Path, layer: str) -> Path:
    return output_dir / "articles" / layer


def render_draft(draft: ArticleDraft) -> str:
    outline = "\n".join(f"- {item}" for item in draft.outline)
    golden_sentences = "\n".join(f"- {item}" for item in draft.golden_sentences)
    case_design = "\n".join(f"- {key}: {value}" for key, value in draft.case_design.items())
    return "\n".join(
        [
            f"# {draft.title}",
            "",
            f"- 文章类型: {draft.article_type}",
            f"- 目标用户: {draft.target_user}",
            f"- 核心痛点: {draft.core_pain}",
            f"- 核心观点: {draft.core_point}",
            "",
            "## 开头钩子",
            draft.opening_hook,
            "",
            "## 文章大纲",
            outline,
            "",
            "## 案例设计",
            case_design,
            "",
            "## 金句设计",
            golden_sentences,
            "",
            "## 公众号正文",
            draft.body,
            "",
            "## 结尾互动和转化引导",
            draft.ending_cta,
        ]
    )


def render_outline(draft: ArticleDraft) -> str:
    outline = "\n".join(f"- {item}" for item in draft.outline)
    return "\n".join(
        [
            f"# {draft.title}",
            "",
            "## 文章大纲",
            outline,
        ]
    )


def render_final_article(review: ReviewResult) -> str:
    notes = "\n".join(f"- {item}" for item in review.revision_notes)
    issues = "\n".join(f"- {item}" for item in review.issues) if review.issues else "- 无"
    return "\n".join(
        [
            f"# {review.final_title}",
            "",
            "## 审稿结论",
            "可以发布" if review.approved else "需要继续修改",
            "",
            "## 主要问题",
            issues,
            "",
            "## 修改建议",
            notes,
            "",
            "## 最终定稿版本",
            review.final_body,
        ]
    )


def render_review(review: ReviewResult) -> str:
    notes = "\n".join(f"- {item}" for item in review.improvement_suggestions)
    issues = "\n".join(f"- {item}" for item in review.problems) if review.problems else "- 无"
    risk_notes = "\n".join(f"- {item}" for item in review.risk_notes) if review.risk_notes else "- 无"
    return "\n".join(
        [
            "# 审稿记录",
            "",
            "## 审稿结论",
            review.review_conclusion,
            "",
            "## 主要问题",
            issues,
            "",
            "## 修改建议",
            notes,
            "",
            f"## 优化后的标题\n{review.final_title}",
            "",
            f"## 优化后的开头\n{review.optimized_opening}",
            "",
            f"## 优化后的结尾\n{review.optimized_ending}",
            "",
            "## 风险提示",
            risk_notes,
        ]
    )


def render_publish_package(package: PublishPackage) -> str:
    cover_copy = "\n".join(f"- {key}: {value}" for key, value in package.cover_copy.items())
    return "\n".join(
        [
            "# 发布包",
            "",
            "## 公众号标题3个版本",
            *[f"{index}. {title}" for index, title in enumerate(package.title_options, start=1)],
            "",
            "## 封面主标题",
            package.cover_main_title,
            "",
            "## 封面副标题",
            package.cover_subtitle,
            "",
            "## 封面文案与视觉建议",
            cover_copy,
            "",
            "## 公众号摘要",
            *[f"{index}. {item}" for index, item in enumerate(package.digest, start=1)],
            "",
            "## 排版建议",
            *[f"- {item}" for item in package.layout_suggestions],
            "",
            "## 朋友圈分发文案3个版本",
            *[f"{index}. {copy}" for index, copy in enumerate(package.moments_copy_options, start=1)],
            "",
            "## 社群分发文案2个版本",
            *[f"{index}. {copy}" for index, copy in enumerate(package.community_copy_options, start=1)],
            "",
            "## 私聊推荐话术",
            package.direct_message_script,
            "",
            "## 评论区互动问题3个",
            *[f"{index}. {question}" for index, question in enumerate(package.comment_questions, start=1)],
            "",
            "## 发布后数据复盘指标",
            *[f"- {metric}" for metric in package.review_metrics],
            "",
            "## 二次分发建议",
            *[f"- {item}" for item in package.repurpose_suggestions],
        ]
    )


def render_visual_layout(visual_layout: VisualLayoutPackage) -> str:
    asset_lines: list[str] = []
    for asset in visual_layout.visual_assets:
        asset_lines.extend(
            [
                f"### {asset.asset_type}｜{asset.title}",
                "",
                f"- 文件名: visual_assets/{asset.filename}",
                f"- 用途: {asset.purpose}",
                f"- 插入位置: {asset.placement}",
                f"- 图注: {asset.caption}",
                f"- 替代文本: {asset.alt_text}",
                f"- 注意事项: {asset.notes}",
                "",
                "生成提示词：",
                asset.prompt,
                "",
            ]
        )

    return "\n".join(
        [
            "# 视觉排版方案",
            "",
            f"- 文章标题: {visual_layout.title}",
            f"- 内容层级: {visual_layout.selected_layer}层",
            f"- 封面方向: {visual_layout.cover_direction}",
            f"- 整体风格: {visual_layout.article_tone}",
            "",
            "## 字体层级建议",
            *[f"- {item}" for item in visual_layout.typography_rules],
            "",
            "## 色彩建议",
            *[f"- {item}" for item in visual_layout.color_rules],
            "",
            "## 正文排版结构",
            *[f"- {item}" for item in visual_layout.section_layout],
            "",
            "## 配图清单",
            *asset_lines,
            "## 飞书文档排版建议",
            *[f"- {item}" for item in visual_layout.feishu_doc_notes],
            "",
            "## 微信公众号后台排版建议",
            *[f"- {item}" for item in visual_layout.wechat_layout_notes],
            "",
            "## 图片生成与发布注意事项",
            *[f"- {item}" for item in visual_layout.image_generation_notes],
        ]
    )


def render_feishu_message(
    package: PublishPackage,
    calendar_item: dict[str, Any],
    output_dir: Path,
    suggested_publish_time: str,
    feishu_doc_result: dict[str, Any] | None = None,
    article_results: list[dict[str, Any]] | None = None,
) -> str:
    output_path = Path("outputs") / calendar_item["date"]
    wechat_ready_path = output_path / "wechat_ready_article.md"
    final_article_path = output_path / "final_article.md"
    publish_package_path = output_path / "publish_package.md"
    selection_path = output_path / "article_selection.md"
    article_results = article_results or []
    feishu_doc_result = feishu_doc_result or {}
    feishu_doc_url = str(feishu_doc_result.get("document_url") or "").strip()
    feishu_doc_error = str(feishu_doc_result.get("error") or "").strip()
    if feishu_doc_url:
        feishu_doc_status = feishu_doc_url
        if feishu_doc_result.get("written") is False:
            feishu_doc_status = f"{feishu_doc_url}\n注意：文档已创建，但写入未确认，请同时查看 GitHub Actions artifact 或本地 outputs。"
    elif feishu_doc_result.get("enabled") is False:
        feishu_doc_status = "未启用飞书协作文档，请查看 GitHub Actions artifact 或本地 outputs 文件。"
    else:
        feishu_doc_status = "未创建成功，请先查看 GitHub Actions artifact 或本地 outputs 文件。"
    return "\n".join(
        [
            "【今日公众号稿件已生成】",
            "",
            f"日期：{calendar_item['date']}",
            f"栏目编号：{calendar_item.get('code')}",
            f"栏目名称：{calendar_item.get('column')}",
            f"内容层级：{calendar_item.get('layer')}",
            f"主编推荐：{package.selected_layer}层｜《{package.title}》",
            "当前状态：C/E/S三篇候选稿已生成，待人工选择发布哪一篇",
            "",
            "请主编检查：",
            "1. 三篇标题哪一篇更适合今天发布",
            "2. 开头是否击中老板痛点",
            "3. 案例是否真实可信",
            "4. 方法是否有工具感和落地感",
            "5. 结尾是否适合引导咨询或领取资料",
            "",
            "请运营执行：",
            "1. 查看 article_selection.md 选择C/E/S其中一篇",
            "2. 根据对应 publish_package.md 准备标题、摘要、封面文案",
            "3. 根据对应 visual_layout.md 插入封面、流程图、看板图、检查清单和结尾引导卡",
            "4. 用 `python src/sync_wechat_draft.py --date 日期 --layer C/E/S` 同步到公众号草稿箱",
            "5. 参考爆文排版：短段落、强小标题、工具截图、领取资料二维码",
            "6. 发布前请老板/主编确认",
            "",
            "选稿清单：",
            str(selection_path),
            "",
            *render_feishu_article_paths(article_results, calendar_item["date"]),
            "飞书协作文档：",
            feishu_doc_status,
            "",
            *(
                ["飞书文档异常：", feishu_doc_error, ""]
                if feishu_doc_error
                else []
            ),
            "建议发布时间：",
            f"今天{suggested_publish_time}",
            "",
            "飞书群人工确认规则：",
            "主编回复：发C / 发E / 发S / 修改",
            "运营回复：已排版 / 待排版",
            "老板回复：可发 / 暂缓",
            "",
            "可复制到微信的提醒文案：",
            "老板，今日C/E/S三篇公众号候选稿已生成，主编推荐：",
            f"{package.selected_layer}层｜《{package.title}》",
            "已发到飞书群，并生成视觉排版方案，请选择今天发布哪一篇。",
        ]
    )


def render_feishu_article_paths(article_results: list[dict[str, Any]], publish_date: str) -> list[str]:
    if not article_results:
        return []
    lines = ["三篇候选稿件："]
    for result in article_results:
        topic = result["topic"]
        layer_dir = Path("outputs") / publish_date / "articles" / topic.layer
        lines.extend(
            [
                f"- {topic.layer}层｜《{result['package'].title}》",
                f"  正文：{layer_dir / 'wechat_ready_article.md'}",
                f"  发布包：{layer_dir / 'publish_package.md'}",
                f"  视觉排版：{layer_dir / 'visual_layout.md'}",
            ]
        )
    lines.append("")
    return lines


def render_wechat_ready_article(review: ReviewResult) -> str:
    return format_wechat_ready_article(review.final_title, sanitize_public_article_text(review.final_body))


def format_wechat_ready_article(title: str, markdown_text: str) -> str:
    lines: list[str] = []
    title_written = False
    highlighted_count = 0
    pull_quote = build_pull_quote(title, markdown_text)

    for block in article_blocks(markdown_text):
        if not block:
            continue
        if block.startswith("主编提示"):
            continue
        if is_internal_courseware_note(block):
            continue

        if block.startswith("# "):
            clean_title = block[2:].strip() or title
            lines.extend([f"# {clean_title}", ""])
            if pull_quote:
                lines.extend([f"> {pull_quote}", "", "---", ""])
            title_written = True
            continue

        if block.startswith("## "):
            lines.extend([format_wechat_heading(block[3:].strip()), ""])
            continue

        if block.startswith("### "):
            lines.extend([f"### {block[4:].strip()}", ""])
            continue

        if block.startswith(">"):
            quote = clean_markdown_block(block).lstrip("> ").strip()
            if quote:
                lines.extend([f"> {quote}", ""])
            continue

        if is_markdown_list_block(block):
            for item in clean_markdown_block(block).splitlines():
                if item.strip():
                    lines.extend([item.strip(), ""])
            continue

        for paragraph in split_article_paragraph(
            clean_markdown_block(block),
            max_chars=WECHAT_ARTICLE_LINE_CHARS * WECHAT_ARTICLE_PARAGRAPH_LINES,
        ):
            paragraph = tighten_article_sentence(paragraph)
            if highlighted_count < 8 and should_highlight_paragraph(paragraph):
                paragraph = f"**{paragraph}**"
                highlighted_count += 1
            lines.extend([paragraph, ""])

    if not title_written:
        lines = [f"# {title}", "", *( [f"> {pull_quote}", "", "---", ""] if pull_quote else []), *lines]

    lines = append_wechat_article_footer(lines)
    return trim_blank_lines(lines)


def append_wechat_article_footer(lines: list[str]) -> list[str]:
    load_env()
    enabled = os.getenv("ENABLE_WECHAT_RESOURCE_FOOTER", "true").strip().lower() == "true"
    if not enabled:
        return lines

    footer: list[str] = ["", "---", ""]
    footer_text = os.getenv("WECHAT_RESOURCE_FOOTER_TEXT", DEFAULT_WECHAT_RESOURCE_FOOTER_TEXT)
    footer_text = footer_text.replace("\\n", "\n").strip()
    if footer_text:
        for paragraph in footer_text.split("\n"):
            footer.append(paragraph.strip())
            footer.append("")

    for index, image_path in enumerate(get_wechat_resource_image_paths(), start=1):
        footer.append(f"![打品SOP流程图{index}]({image_path})")
        footer.append("")

    qr_enabled = os.getenv("ENABLE_WECHAT_CONTACT_QR", "true").strip().lower() == "true"
    image_path = os.getenv("WECHAT_CONTACT_QR_IMAGE_PATH", DEFAULT_WECHAT_CONTACT_QR_PATH).strip()
    alt_text = os.getenv("WECHAT_CONTACT_QR_ALT", "打开图片长按识别二维码添加我的微信").strip()
    if qr_enabled and image_path:
        footer.append(f"![{alt_text}]({image_path})")
        footer.append("")
    caption = os.getenv("WECHAT_CONTACT_QR_CAPTION", "").strip()
    if qr_enabled and image_path and caption:
        footer.append(caption)
        footer.append("")
    return [*lines, *footer]


def get_wechat_resource_image_paths() -> list[str]:
    if "WECHAT_RESOURCE_IMAGE_PATHS" not in os.environ:
        return DEFAULT_WECHAT_RESOURCE_IMAGE_PATHS
    raw_paths = os.getenv("WECHAT_RESOURCE_IMAGE_PATHS", "").strip()
    if not raw_paths:
        return []
    return [path.strip() for path in raw_paths.split(",") if path.strip()]


def format_wechat_heading(heading: str) -> str:
    compact = re.sub(r"\s+", "", heading.strip())
    return f"## {compact}"


def build_pull_quote(title: str, markdown_text: str) -> str:
    if "不敢招运营" in title or "招运营" in title:
        return "你以为是在招运营，其实是在给系统漏洞买单。"
    if "老板越忙" in title:
        return "老板越忙，不一定是公司更强，可能是系统更弱。"
    if "新品SOP" in title or "详情页" in title:
        return "新品第一步做错了，后面每一步都在烧钱。"

    candidates = [
        "老板越忙，不一定是公司更强，可能是系统更弱。",
        "不是员工不努力，而是公司没有标准动作。",
        "爆款可复制，靠的不是人，而是流程。",
        "管理的终点，不是老板更勤奋，而是团队能自动运转。",
        "你缺的不是努力，缺的是一套能跑起来的系统。",
    ]
    source = f"{title}\n{markdown_text}"
    for candidate in candidates:
        if candidate in source:
            return candidate
    return "真正能长大的电商公司，最后拼的不是个人英雄，而是系统能力。"


def is_internal_courseware_note(block: str) -> bool:
    internal_markers = [
        "这一篇的底层框架",
        "本次读取到的重点资料包括",
        "GitHub课件库",
        "GitHub 课件库",
        "课件库路径",
        "写成文章时不照搬课件原文",
        "outputs/",
        ".pptx",
        "今天的选题",
        "对应到今天的选题",
        "本次读取",
        "Agent",
    ]
    return any(marker in block for marker in internal_markers)


def sanitize_public_article_text(markdown_text: str) -> str:
    replacements = {
        "这背后对应到今天的选题，就是：": "",
        "这背后对应到今天的选题，就是": "",
        "今天的选题": "这个问题",
        "选题": "主题",
        "Agent": "",
    }
    sanitized = markdown_text
    for source, target in replacements.items():
        sanitized = sanitized.replace(source, target)
    sanitized = re.sub(r"本次读取到的重点资料包括：.*?。", "", sanitized)
    sanitized = re.sub(r"这一篇的底层框架.*?。", "", sanitized)
    return sanitized


def should_highlight_paragraph(paragraph: str) -> bool:
    if len(paragraph) > 90:
        return False
    keywords = [
        "老板越忙",
        "不是员工不努力",
        "真正的问题",
        "爆款可复制",
        "管理就从",
        "你缺的不是",
        "流程不是",
        "公司没有标准动作",
        "系统越弱",
    ]
    return any(keyword in paragraph for keyword in keywords)


def tighten_article_sentence(text: str) -> str:
    replacements = {
        "这几年我看过很多电商团队，有一个现象特别明显：": "我看过很多电商团队，发现一个扎心现象：",
        "这篇文章不讲虚的，我们就拆一个问题：": "这篇不讲虚的，只拆一个问题：",
        "你以为的问题，可能是运营能力不行。": "你以为是运营不行。",
        "但真正的问题往往是：": "但真正的问题是：",
        "第一件事，做知识库。": "第一，做知识库。",
        "第二件事，做多维表。": "第二，做多维表。",
        "第三件事，做流程可视化。": "第三，做流程可视化。",
        "第一个动作，": "第一个动作：",
        "第二个动作，": "第二个动作：",
        "第三个动作，": "第三个动作：",
    }
    tightened = text.strip()
    for source, target in replacements.items():
        tightened = tightened.replace(source, target)
    return tightened


def trim_blank_lines(lines: list[str]) -> str:
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    normalized: list[str] = []
    blank_count = 0
    for line in lines:
        if not line.strip():
            blank_count += 1
            if blank_count <= 1:
                normalized.append("")
            continue
        blank_count = 0
        normalized.append(line.rstrip())
    return "\n".join(normalized)


def render_article_selection(
    article_results: list[dict[str, Any]],
    editor_decision: EditorialDecision,
    calendar_item: dict[str, Any],
) -> str:
    lines = [
        "# 今日三篇候选文章",
        "",
        f"- 日期: {calendar_item['date']}",
        f"- 今日栏目: {calendar_item.get('code')}｜{calendar_item.get('column')}",
        f"- 主编推荐优先发布: {editor_decision.selected_topic.layer}层｜{editor_decision.selected_topic.title}",
        "- 人工发布规则: 老板/主编从C/E/S三篇中选择1篇，运营再同步到公众号草稿箱。",
        "",
        "## 三篇文章清单",
    ]
    for result in article_results:
        topic = result["topic"]
        layer_dir = Path("outputs") / calendar_item["date"] / "articles" / topic.layer
        marker = "（主编推荐）" if topic.layer == editor_decision.selected_topic.layer else ""
        lines.extend(
            [
                "",
                f"### {topic.layer}层｜{topic.layer_name}{marker}",
                "",
                f"- 标题: {result['package'].title}",
                f"- 目标用户: {topic.target_user}",
                f"- 核心痛点: {topic.user_pain}",
                f"- 可复制正文: {layer_dir / 'wechat_ready_article.md'}",
                f"- 完整终稿: {layer_dir / 'final_article.md'}",
                f"- 发布包: {layer_dir / 'publish_package.md'}",
                f"- 视觉排版方案: {layer_dir / 'visual_layout.md'}",
                f"- 配图素材目录: {layer_dir / 'visual_assets'}",
                f"- 同步草稿箱命令: `python src/sync_wechat_draft.py --date {calendar_item['date']} --layer {topic.layer}`",
            ]
        )
    return "\n".join(lines)


def render_email_summary(
    publish_date: str,
    calendar_item: dict[str, Any],
    decision: EditorialDecision,
    package: PublishPackage,
    suggested_publish_time: str,
    feishu_doc_result: dict[str, Any] | None = None,
    article_results: list[dict[str, Any]] | None = None,
) -> str:
    output_path = Path("outputs") / publish_date
    feishu_doc_url = ""
    if feishu_doc_result:
        feishu_doc_url = str(feishu_doc_result.get("document_url") or "")
    lines = [
        f"# 【公众号今日稿件】{publish_date}｜三篇候选稿已生成",
        "",
        f"- 今日日期: {publish_date}",
        f"- 今日栏目: {calendar_item.get('code')}｜{calendar_item.get('column')}",
        f"- 主编推荐: {decision.selected_topic.layer}层｜{decision.selected_topic.title}",
        "- 当前状态: 待人工选择发布稿件",
        f"- 建议发布时间: 今天{suggested_publish_time}",
        f"- 选稿清单路径: {output_path / 'article_selection.md'}",
        f"- 飞书协作文档: {feishu_doc_url or '未创建或未启用'}",
    ]
    if article_results:
        lines.extend(["", "## 三篇文章"])
        for result in article_results:
            topic = result["topic"]
            layer_dir = output_path / "articles" / topic.layer
            lines.extend(
                [
                    f"- {topic.layer}层｜{result['package'].title}",
                    f"  正文: {layer_dir / 'wechat_ready_article.md'}",
                    f"  发布包: {layer_dir / 'publish_package.md'}",
                    f"  视觉排版: {layer_dir / 'visual_layout.md'}",
                ]
            )
    return "\n".join(lines)


def render_feishu_doc_preview(markdown_content: str) -> str:
    return "\n".join(line for line in markdown_content.splitlines() if line.strip() != FEISHU_SPACER_MARKER)


def render_feishu_doc_content(
    output_dir: Path,
    calendar_item: dict[str, Any],
    package: PublishPackage,
    suggested_publish_time: str,
    article_results: list[dict[str, Any]] | None = None,
) -> str:
    article_results = article_results or []
    paragraphs = [
        f"【{calendar_item['date']}｜C/E/S三篇公众号内容包】",
        "【公众号内容协作文档】",
        f"- 日期：{calendar_item['date']}",
        f"- 栏目：{calendar_item.get('code')}｜{calendar_item.get('column')}",
        f"- 主编推荐：《{package.title}》",
        f"- 建议发布时间：今天{suggested_publish_time}",
        "- 当前状态：待老板/主编从C/E/S三篇中选择发布稿",
        "【人工确认发布规则】",
        "- 老板/主编回复：发C / 发E / 发S / 修改",
        "- 运营回复：已排版 / 待排版",
        "- 老板回复：可发 / 暂缓",
        "【阅读排版说明】",
        "以下三篇候选稿已按公众号阅读节奏重新排版：每段尽量控制在手机端3行以内，换段留一行空白，三篇文章之间留5行，方便主编和老板在飞书里直接阅读。",
    ]
    if article_results:
        paragraphs.extend(["【三篇候选稿件｜连续阅读版】"])
        for index, result in enumerate(article_results):
            topic = result["topic"]
            article_output_dir = output_dir / "articles" / topic.layer
            article_body = read_output_text(article_output_dir / "wechat_ready_article.md")
            title = result["package"].title
            paragraphs.extend(
                [
                    f"【{topic.layer}层｜{topic.layer_name}】",
                    f"《{title}》",
                    f"目标用户：{topic.target_user}",
                    f"主编建议：{'优先发布' if topic.layer == package.selected_layer else '候选备选'}",
                    *format_article_for_feishu(article_body),
                ]
            )
            if index < len(article_results) - 1:
                paragraphs.extend(feishu_spacer_blocks(5))

        paragraphs.extend(
            [
                "【发布与协作文件索引】",
                "以下文件用于运营排版、同步公众号草稿箱和人工确认，不再穿插到正文中，避免飞书阅读版显得杂乱。",
                f"- 选题清单：{Path('outputs') / calendar_item['date'] / 'topics.md'}",
                f"- 主编评估：{Path('outputs') / calendar_item['date'] / 'selected_topic.md'}",
                f"- 三篇选择清单：{Path('outputs') / calendar_item['date'] / 'article_selection.md'}",
            ]
        )
        for result in article_results:
            topic = result["topic"]
            layer_dir = Path("outputs") / calendar_item["date"] / "articles" / topic.layer
            paragraphs.extend(
                [
                    f"【{topic.layer}层文件】",
                    f"- 可复制公众号正文：{layer_dir / 'wechat_ready_article.md'}",
                    f"- 完整终稿：{layer_dir / 'final_article.md'}",
                    f"- 发布包：{layer_dir / 'publish_package.md'}",
                    f"- 视觉排版方案：{layer_dir / 'visual_layout.md'}",
                    f"- 配图素材目录：{layer_dir / 'visual_assets'}",
                    f"- 同步草稿箱命令：python src/sync_wechat_draft.py --date {calendar_item['date']} --layer {topic.layer}",
                ]
            )
    else:
        paragraphs.extend(
            [
                "【今日主推稿件】",
                *format_article_for_feishu(read_output_text(output_dir / "wechat_ready_article.md")),
                "【发布与协作文件索引】",
                f"- 可复制公众号正文：{Path('outputs') / calendar_item['date'] / 'wechat_ready_article.md'}",
                f"- 完整终稿：{Path('outputs') / calendar_item['date'] / 'final_article.md'}",
                f"- 发布包：{Path('outputs') / calendar_item['date'] / 'publish_package.md'}",
                f"- 视觉排版方案：{Path('outputs') / calendar_item['date'] / 'visual_layout.md'}",
            ]
        )

    return "\n\n".join(paragraphs)


def read_output_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.exists() else "本文件尚未生成。"


def feishu_spacer_blocks(count: int) -> list[str]:
    return [FEISHU_SPACER_MARKER for _ in range(count)]


def format_article_for_feishu(markdown_text: str) -> list[str]:
    paragraphs: list[str] = []
    for block in article_blocks(markdown_text):
        if not block:
            continue
        if block.startswith("主编提示"):
            continue
        if is_internal_courseware_note(block):
            continue
        if block.strip() == "---":
            continue
        if block.startswith("# "):
            paragraphs.append(block[2:].strip())
            continue
        if block.startswith("## "):
            paragraphs.append(block[3:].strip())
            continue
        if block.startswith("### "):
            paragraphs.append(block[4:].strip())
            continue
        if block.startswith(">"):
            quote = clean_markdown_block(block)
            if quote:
                paragraphs.append(f"金句：{quote}")
            continue
        if is_markdown_list_block(block):
            paragraphs.append(clean_markdown_block(block))
            continue
        paragraphs.extend(split_article_paragraph(clean_markdown_block(block)))
    return paragraphs


def article_blocks(markdown_text: str) -> list[str]:
    normalized = markdown_text.replace("\r\n", "\n").replace("\r", "\n")
    raw_blocks = re.split(r"\n{2,}", normalized)
    return [block.strip() for block in raw_blocks if block.strip()]


def is_markdown_list_block(block: str) -> bool:
    return all(line.strip().startswith("- ") or re.match(r"^\d+[.、]\s+", line.strip()) for line in block.splitlines())


def clean_markdown_block(block: str) -> str:
    text = re.sub(r"^\s{0,3}[-*]\s+", "• ", block, flags=re.MULTILINE)
    text = re.sub(r"^\s{0,3}>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    return text.strip()


def split_article_paragraph(text: str, max_chars: int | None = None) -> list[str]:
    max_chars = max_chars or FEISHU_ARTICLE_LINE_CHARS * FEISHU_ARTICLE_PARAGRAPH_LINES
    sentences = split_sentences(text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) > max_chars:
            chunks.append(current.strip())
            current = sentence
        else:
            current = f"{current}{sentence}"
    if current.strip():
        chunks.append(current.strip())

    refined: list[str] = []
    for chunk in chunks:
        if len(chunk) <= max_chars + 12:
            refined.append(chunk)
            continue
        refined.extend(chunk[index : index + max_chars].strip() for index in range(0, len(chunk), max_chars))
    return [chunk for chunk in refined if chunk]


def split_sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", "", text.strip())
    if not compact:
        return []
    return [match.group(0) for match in re.finditer(r".+?[。！？；]|.+$", compact)]


def build_run_summary(
    publish_date: str,
    calendar_item: dict[str, Any],
    decision: EditorialDecision,
    package: PublishPackage,
    feishu_sent: bool,
    wecom_sent: bool,
    email_sent: bool,
    status: str,
    suggested_publish_time: str,
    feishu_doc_result: dict[str, Any] | None = None,
    article_results: list[dict[str, Any]] | None = None,
    courseware_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    feishu_doc_result = feishu_doc_result or {}
    article_results = article_results or []
    courseware_context = courseware_context or {}
    return {
        "date": publish_date,
        "calendar": {
            "code": calendar_item.get("code"),
            "column": calendar_item.get("column"),
            "layer": calendar_item.get("layer"),
        },
        "selected_topic": decision.selected_topic.title,
        "article_title": package.title,
        "article_count": len(article_results) or 1,
        "feishu_doc_preview": str(Path("outputs") / publish_date / "feishu_doc_preview.md"),
        "articles": [
            {
                "layer": result["topic"].layer,
                "layer_name": result["topic"].layer_name,
                "title": result["package"].title,
                "wechat_ready_article": str(Path("outputs") / publish_date / "articles" / result["topic"].layer / "wechat_ready_article.md"),
                "publish_package": str(Path("outputs") / publish_date / "articles" / result["topic"].layer / "publish_package.md"),
                "visual_layout": str(Path("outputs") / publish_date / "articles" / result["topic"].layer / "visual_layout.md"),
                "visual_assets": str(Path("outputs") / publish_date / "articles" / result["topic"].layer / "visual_assets"),
            }
            for result in article_results
        ],
        "status": status,
        "feishu_sent": feishu_sent,
        "wecom_sent": wecom_sent,
        "email_sent": email_sent,
        "feishu_doc_created": bool(feishu_doc_result.get("created")),
        "feishu_doc_written": bool(feishu_doc_result.get("written")),
        "feishu_doc_url": feishu_doc_result.get("document_url", ""),
        "feishu_doc_error": feishu_doc_result.get("error", ""),
        "courseware_context_enabled": bool(courseware_context.get("enabled")),
        "courseware_context_available": bool(courseware_context.get("available")),
        "courseware_root": courseware_context.get("root", ""),
        "courseware_files": [item.get("path", "") for item in courseware_context.get("files", [])],
        "manual_publish_required": True,
        "suggested_publish_time": suggested_publish_time,
    }


def get_recommended_article_result(
    article_results: list[dict[str, Any]],
    editor_decision: EditorialDecision,
) -> dict[str, Any]:
    for result in article_results:
        if result["topic"].layer == editor_decision.selected_topic.layer:
            return result
    if not article_results:
        raise ValueError("No article results available.")
    return article_results[0]


def run_daily_pipeline(
    root_dir: Path = ROOT_DIR,
    run_date: date | None = None,
    llm=call_llm,
    stage: str = "all",
) -> dict[str, object]:
    if stage not in STAGE_ORDER:
        raise ValueError(f"Unknown stage: {stage}. Expected one of: {', '.join(STAGE_ORDER)}")

    current_date = run_date or beijing_today()
    publish_date = current_date.isoformat()
    try:
        return _run_daily_pipeline_impl(root_dir=root_dir, run_date=current_date, llm=llm, stage=stage)
    except Exception as exc:
        report_failure(stage, publish_date, exc)
        raise


def _run_daily_pipeline_impl(
    root_dir: Path,
    run_date: date,
    llm=call_llm,
    stage: str = "all",
) -> dict[str, object]:
    current_date = run_date
    brand = load_yaml(root_dir / "config" / "brand.yaml")
    calendar = load_yaml(root_dir / "config" / "content_calendar.yaml")
    schedule = load_optional_yaml(root_dir / "config" / "schedule.yaml", DEFAULT_SCHEDULE)
    suggested_publish_time = str(schedule.get("suggested_publish_time") or "18:00")
    calendar_item = get_today_calendar_item(calendar, current_date)
    calendar_item["recent_topic_titles"] = load_recent_topic_titles(root_dir, current_date)
    publish_date = calendar_item["date"]
    output_dir = root_dir / "outputs" / publish_date
    output_dir.mkdir(parents=True, exist_ok=True)
    courseware_context = load_courseware_context(root_dir, calendar_item)
    save_article(output_dir / "courseware_reference.md", render_courseware_reference(courseware_context))

    topic_agent = TopicAgent(
        brand=brand,
        layers=DEFAULT_LAYERS,
        courseware_context=courseware_context,
        system_prompt=load_prompt(root_dir, "topic_agent.md"),
        llm=llm,
    )
    topics = topic_agent.generate_topics(calendar_item)
    save_json(
        output_dir / "topics.json",
        {
            "date": publish_date,
            "weekday": calendar_item["weekday"],
            "calendar": calendar_item,
            "brand": brand.get("brand", {}),
            "topics": topics,
        },
    )
    save_article(output_dir / "topics.md", render_topics(topics, calendar_item))
    report_stage(stage, "topics", publish_date)
    if stage == "topics":
        return build_pipeline_result(
            publish_date,
            output_dir,
            calendar_item,
            topics,
            courseware_context=courseware_context,
            llm_outputs={"topic_agent": topic_agent.last_llm_response},
            completed_stage=stage,
        )

    editor_agent = EditorInChiefAgent(
        courseware_context=courseware_context,
        system_prompt=load_prompt(root_dir, "editor_in_chief_agent.md"),
        llm=llm,
    )
    decision = editor_agent.choose_topic(topics, calendar_item=calendar_item)
    save_article(output_dir / "selected_topic.md", render_selected_topic(decision, calendar_item))
    report_stage(stage, "editor", publish_date)
    if stage == "editor":
        return build_pipeline_result(
            publish_date,
            output_dir,
            calendar_item,
            topics,
            decision=decision,
            courseware_context=courseware_context,
            llm_outputs={
                "topic_agent": topic_agent.last_llm_response,
                "editor_in_chief_agent": editor_agent.last_llm_response,
            },
            completed_stage=stage,
        )

    writer_agent = WriterAgent(
        courseware_context=courseware_context,
        system_prompt=load_prompt(root_dir, "writer_agent.md"),
        llm=llm,
    )
    article_results: list[dict[str, Any]] = []
    for topic in topics:
        topic_decision = build_article_decision(decision, topic, calendar_item)
        draft = writer_agent.write_article(topic_decision)
        topic_output_dir = article_dir(output_dir, topic.layer)
        topic_output_dir.mkdir(parents=True, exist_ok=True)
        save_article(topic_output_dir / "draft.md", render_outline(draft))
        article_results.append(
            {
                "topic": topic,
                "decision": topic_decision,
                "draft": draft,
                "output_dir": topic_output_dir,
            }
        )

    recommended = get_recommended_article_result(article_results, decision)
    draft = recommended["draft"]
    save_article(output_dir / "draft.md", render_outline(draft))
    report_stage(stage, "outline", publish_date)
    if stage == "outline":
        return build_pipeline_result(
            publish_date,
            output_dir,
            calendar_item,
            topics,
            decision=decision,
            draft=draft,
            article_results=article_results,
            courseware_context=courseware_context,
            llm_outputs={
                "topic_agent": topic_agent.last_llm_response,
                "editor_in_chief_agent": editor_agent.last_llm_response,
                "writer_agent": writer_agent.last_llm_response,
            },
            completed_stage=stage,
        )

    for result in article_results:
        save_article(result["output_dir"] / "draft.md", render_draft(result["draft"]))
    save_article(output_dir / "draft.md", render_draft(draft))
    report_stage(stage, "draft", publish_date)
    if stage == "draft":
        return build_pipeline_result(
            publish_date,
            output_dir,
            calendar_item,
            topics,
            decision=decision,
            draft=draft,
            article_results=article_results,
            courseware_context=courseware_context,
            llm_outputs={
                "topic_agent": topic_agent.last_llm_response,
                "editor_in_chief_agent": editor_agent.last_llm_response,
                "writer_agent": writer_agent.last_llm_response,
            },
            completed_stage=stage,
        )

    reviewer_agent = ReviewerAgent(
        courseware_context=courseware_context,
        system_prompt=load_prompt(root_dir, "reviewer_agent.md"),
        llm=llm,
    )
    for result in article_results:
        review = reviewer_agent.review(result["draft"])
        result["review"] = review
        save_article(result["output_dir"] / "review.md", render_review(review))
        save_article(result["output_dir"] / "final_article.md", render_final_article(review))
        save_article(result["output_dir"] / "wechat_ready_article.md", render_wechat_ready_article(review))

    recommended = get_recommended_article_result(article_results, decision)
    review = recommended["review"]
    save_article(output_dir / "review.md", render_review(review))
    save_article(output_dir / "final_article.md", render_final_article(review))
    save_article(output_dir / "wechat_ready_article.md", render_wechat_ready_article(review))
    report_stage(stage, "review", publish_date)
    if stage == "review":
        return build_pipeline_result(
            publish_date,
            output_dir,
            calendar_item,
            topics,
            decision=decision,
            draft=draft,
            review=review,
            article_results=article_results,
            courseware_context=courseware_context,
            llm_outputs={
                "topic_agent": topic_agent.last_llm_response,
                "editor_in_chief_agent": editor_agent.last_llm_response,
                "writer_agent": writer_agent.last_llm_response,
                "reviewer_agent": reviewer_agent.last_llm_response,
            },
            completed_stage=stage,
        )

    publisher_agent = PublisherAgent(
        courseware_context=courseware_context,
        system_prompt=load_prompt(root_dir, "publisher_agent.md"),
        llm=llm,
    )
    for result in article_results:
        package = publisher_agent.build_package(result["topic"], result["review"])
        result["package"] = package
        save_article(result["output_dir"] / "publish_package.md", render_publish_package(package))

    recommended = get_recommended_article_result(article_results, decision)
    package = recommended["package"]
    save_article(output_dir / "publish_package.md", render_publish_package(package))
    save_article(output_dir / "article_selection.md", render_article_selection(article_results, decision, calendar_item))
    report_stage(stage, "publish", publish_date)
    if stage == "publish":
        return build_pipeline_result(
            publish_date,
            output_dir,
            calendar_item,
            topics,
            decision=decision,
            draft=draft,
            review=review,
            package=package,
            article_results=article_results,
            courseware_context=courseware_context,
            llm_outputs={
                "topic_agent": topic_agent.last_llm_response,
                "editor_in_chief_agent": editor_agent.last_llm_response,
                "writer_agent": writer_agent.last_llm_response,
                "reviewer_agent": reviewer_agent.last_llm_response,
                "publisher_agent": publisher_agent.last_llm_response,
            },
            completed_stage=stage,
        )

    visual_agent = VisualDesignerAgent(
        courseware_context=courseware_context,
        system_prompt=load_prompt(root_dir, "visual_designer_agent.md"),
        llm=llm,
    )
    for result in article_results:
        visual_layout = visual_agent.design_layout(result["topic"], result["review"], result["package"])
        result["visual_layout"] = visual_layout
        result["visual_assets"] = save_visual_assets(result["output_dir"], visual_layout)
        save_article(result["output_dir"] / "visual_layout.md", render_visual_layout(visual_layout))

    recommended = get_recommended_article_result(article_results, decision)
    visual_layout = recommended["visual_layout"]
    save_visual_assets(output_dir, visual_layout)
    save_article(output_dir / "visual_layout.md", render_visual_layout(visual_layout))
    save_article(output_dir / "article_selection.md", render_article_selection(article_results, decision, calendar_item))
    report_stage(stage, "visual", publish_date)
    if stage == "visual":
        return build_pipeline_result(
            publish_date,
            output_dir,
            calendar_item,
            topics,
            decision=decision,
            draft=draft,
            review=review,
            package=package,
            visual_layout=visual_layout,
            article_results=article_results,
            courseware_context=courseware_context,
            llm_outputs={
                "topic_agent": topic_agent.last_llm_response,
                "editor_in_chief_agent": editor_agent.last_llm_response,
                "writer_agent": writer_agent.last_llm_response,
                "reviewer_agent": reviewer_agent.last_llm_response,
                "publisher_agent": publisher_agent.last_llm_response,
                "visual_designer_agent": visual_agent.last_llm_response,
            },
            completed_stage=stage,
        )

    feishu_doc_content = render_feishu_doc_content(
        output_dir=output_dir,
        calendar_item=calendar_item,
        package=package,
        suggested_publish_time=suggested_publish_time,
        article_results=article_results,
    )
    save_article(output_dir / "feishu_doc_preview.md", render_feishu_doc_preview(feishu_doc_content))
    feishu_doc_result = create_feishu_doc_from_markdown(
        title=f"{publish_date}｜C/E/S三篇公众号内容包｜主推{package.title}",
        markdown_content=feishu_doc_content,
    )
    save_article(
        output_dir / "feishu_message.md",
        render_feishu_message(
            package,
            calendar_item,
            output_dir,
            suggested_publish_time,
            feishu_doc_result,
            article_results,
        ),
    )
    email_summary = render_email_summary(
        publish_date,
        calendar_item,
        decision,
        package,
        suggested_publish_time,
        feishu_doc_result,
        article_results,
    )
    save_article(output_dir / "email_summary.md", email_summary)
    report_stage(stage, "complete", publish_date)
    feishu_sent = notify_feishu_from_output(output_dir)
    wecom_sent = notify_wecom_from_output(output_dir)
    email_sent = send_email_backup(
        subject=f"【公众号今日稿件】{publish_date}｜{package.title}",
        body=email_summary,
        attachments=[
            output_dir / "article_selection.md",
            output_dir / "wechat_ready_article.md",
            output_dir / "final_article.md",
            output_dir / "publish_package.md",
            output_dir / "visual_layout.md",
            output_dir / "feishu_message.md",
            *(result["output_dir"] / "wechat_ready_article.md" for result in article_results),
            *(result["output_dir"] / "publish_package.md" for result in article_results),
            *(result["output_dir"] / "visual_layout.md" for result in article_results),
        ],
    )
    save_json(
        output_dir / "run_summary.json",
        build_run_summary(
            publish_date=publish_date,
            calendar_item=calendar_item,
            decision=decision,
            package=package,
            feishu_sent=feishu_sent,
            wecom_sent=wecom_sent,
            email_sent=email_sent,
            status="待人工发布",
            suggested_publish_time=suggested_publish_time,
            feishu_doc_result=feishu_doc_result,
            article_results=article_results,
            courseware_context=courseware_context,
        ),
    )

    return build_pipeline_result(
        publish_date,
        output_dir,
        calendar_item,
        topics,
        decision=decision,
        draft=draft,
        review=review,
        package=package,
        visual_layout=visual_layout,
        article_results=article_results,
        courseware_context=courseware_context,
        llm_outputs={
            "topic_agent": topic_agent.last_llm_response,
            "editor_in_chief_agent": editor_agent.last_llm_response,
            "writer_agent": writer_agent.last_llm_response,
            "reviewer_agent": reviewer_agent.last_llm_response,
            "publisher_agent": publisher_agent.last_llm_response,
            "visual_designer_agent": visual_agent.last_llm_response,
        },
        completed_stage="all",
    )


def build_pipeline_result(
    publish_date: str,
    output_dir: Path,
    calendar_item: dict[str, Any],
    topics: list,
    decision: EditorialDecision | None = None,
    draft: ArticleDraft | None = None,
    review: ReviewResult | None = None,
    package: PublishPackage | None = None,
    visual_layout: VisualLayoutPackage | None = None,
    article_results: list[dict[str, Any]] | None = None,
    courseware_context: dict[str, Any] | None = None,
    llm_outputs: dict[str, str] | None = None,
    completed_stage: str = "all",
) -> dict[str, object]:
    return {
        "date": publish_date,
        "output_dir": output_dir,
        "calendar_item": calendar_item,
        "topics": topics,
        "decision": decision,
        "draft": draft,
        "review": review,
        "publish_package": package,
        "visual_layout": visual_layout,
        "article_results": article_results or [],
        "courseware_context": courseware_context or {},
        "llm_outputs": llm_outputs or {},
        "completed_stage": completed_stage,
    }
