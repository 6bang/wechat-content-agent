from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from agents.editor_in_chief_agent import EditorInChiefAgent
from agents.publisher_agent import PublisherAgent
from agents.reviewer_agent import ReviewerAgent
from agents.topic_agent import TopicAgent
from agents.writer_agent import WriterAgent
from models.content import ArticleDraft, EditorialDecision, PublishPackage, ReviewResult, to_serializable
from notify.email_notify import send_email_backup
from notify.feishu_doc import create_feishu_doc_from_markdown
from notify.feishu_notify import (
    notify_feishu_from_output,
    send_feishu_failure_report,
    send_feishu_stage_report,
)
from storage.save_article import save_article
from storage.save_json import save_json
from utils.llm import call_llm

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


ROOT_DIR = Path(__file__).resolve().parents[2]
WEEKDAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
STAGE_ORDER = ["topics", "editor", "outline", "draft", "review", "publish", "all"]

DEFAULT_LAYERS = {
    "layers": {
        "C": {"name": "泛流量内容", "conversion_role": "建立老板认知和品牌信任"},
        "E": {"name": "行业流量内容", "conversion_role": "把行业痛点引向运营管理体系问题"},
        "S": {"name": "专业内容", "conversion_role": "承接课程、咨询和企业服务转化"},
    }
}
DEFAULT_SCHEDULE = {
    "daily_run_time": "06:00",
    "timezone": "Asia/Shanghai",
    "suggested_publish_time": "18:00",
}

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
        "task_name": "评估选题并确定今日主选题",
        "status": "已完成",
        "summary": "已根据痛点强度、传播价值、精准流量价值、专业信任价值、转化价值、节奏匹配度完成评分，并选出今日主选题。",
        "output_files": ["selected_topic.md"],
        "next_step": "内容编辑 Agent 将根据主选题生成文章大纲和初稿。",
    },
    "outline": {
        "stage_name": "文章大纲完成",
        "role_name": "内容编辑 Agent",
        "task_name": "生成公众号文章大纲",
        "status": "已完成",
        "summary": "已完成文章标题、开头钩子、核心观点、正文结构、案例设计、金句和结尾转化设计。",
        "output_files": ["draft.md"],
        "next_step": "内容编辑 Agent 将继续生成公众号初稿。",
    },
    "draft": {
        "stage_name": "公众号初稿完成",
        "role_name": "内容编辑 Agent",
        "task_name": "生成公众号初稿",
        "status": "已完成",
        "summary": "已根据主选题完成公众号初稿，文章包含痛点开头、案例、方法、金句和转化引导。",
        "output_files": ["draft.md"],
        "next_step": "审稿 Agent 将进行审稿、修改和定稿。",
    },
    "review": {
        "stage_name": "审稿定稿完成",
        "role_name": "审稿 Agent",
        "task_name": "审阅初稿并生成最终定稿",
        "status": "待人工确认",
        "summary": "已完成标题、开头、逻辑、案例、方法、专业度、转化和风险检查，并输出最终定稿。",
        "output_files": ["review.md", "final_article.md"],
        "next_step": "新媒体运营 Agent 将生成发布包；主编可同步人工检查终稿。",
    },
    "publish": {
        "stage_name": "发布包完成",
        "role_name": "新媒体运营 Agent",
        "task_name": "生成公众号发布包",
        "status": "已完成",
        "summary": "已生成公众号标题、摘要、封面文案、朋友圈文案、社群文案、私聊话术、评论区问题和数据复盘表。",
        "output_files": ["publish_package.md"],
        "next_step": "运营人员可复制终稿到飞书文档或公众号后台，等待老板/主编确认发布。",
    },
    "complete": {
        "stage_name": "今日内容包完成",
        "role_name": "总控 Agent",
        "task_name": "完成今日公众号内容生产流水线",
        "status": "待人工发布",
        "summary": "今日公众号内容包已全部生成，包含选题、主选题、初稿、审稿、终稿、可复制公众号正文、发布包、飞书消息和邮件摘要。",
        "output_files": [
            "topics.md",
            "selected_topic.md",
            "wechat_ready_article.md",
            "final_article.md",
            "publish_package.md",
            "feishu_message.md",
        ],
        "next_step": "请主编确认终稿，运营排版公众号，建议今天18:00人工发布。",
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


def output_file_path(publish_date: str, filename: str) -> str:
    return str(Path("outputs") / publish_date / filename)


def output_file_paths(publish_date: str, filenames: list[str]) -> list[str]:
    return [output_file_path(publish_date, filename) for filename in filenames]


def should_report_stage(target_stage: str, report_stage: str) -> bool:
    if report_stage == "complete":
        return target_stage in {"publish", "all"}
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


def report_failure(target_stage: str, publish_date: str, error: Exception) -> None:
    report = STAGE_REPORTS.get(target_stage) or STAGE_REPORTS["complete"]
    send_feishu_failure_report(
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


def render_feishu_message(
    package: PublishPackage,
    calendar_item: dict[str, Any],
    output_dir: Path,
    suggested_publish_time: str,
    feishu_doc_result: dict[str, Any] | None = None,
) -> str:
    output_path = Path("outputs") / calendar_item["date"]
    wechat_ready_path = output_path / "wechat_ready_article.md"
    final_article_path = output_path / "final_article.md"
    publish_package_path = output_path / "publish_package.md"
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
            f"今日主选题：{package.title}",
            f"文章标题：《{package.title}》",
            "当前状态：待主编确认 / 待运营排版 / 可发布",
            "",
            "请主编检查：",
            "1. 标题是否有点击欲望",
            "2. 开头是否击中老板痛点",
            "3. 案例是否真实可信",
            "4. 方法是否有落地感",
            "5. 结尾是否适合引导咨询",
            "",
            "请运营执行：",
            "1. 复制 wechat_ready_article.md 到飞书文档",
            "2. 根据 publish_package.md 准备标题、摘要、封面文案",
            "3. 排版公众号",
            "4. 准备朋友圈文案",
            "5. 准备社群分发文案",
            "6. 发布前请老板确认",
            "",
            "稿件路径：",
            str(wechat_ready_path),
            "",
            "完整终稿路径：",
            str(final_article_path),
            "",
            "发布包路径：",
            str(publish_package_path),
            "",
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
            "主编回复：通过 / 修改",
            "运营回复：已排版 / 待排版",
            "老板回复：可发 / 暂缓",
            "",
            "可复制到微信的提醒文案：",
            "老板，今日公众号稿件已生成：",
            f"《{package.title}》",
            "已发到飞书群，请查看终稿和发布包。",
        ]
    )


def render_wechat_ready_article(review: ReviewResult) -> str:
    return review.final_body


def render_email_summary(
    publish_date: str,
    calendar_item: dict[str, Any],
    decision: EditorialDecision,
    package: PublishPackage,
    suggested_publish_time: str,
    feishu_doc_result: dict[str, Any] | None = None,
) -> str:
    output_path = Path("outputs") / publish_date
    feishu_doc_url = ""
    if feishu_doc_result:
        feishu_doc_url = str(feishu_doc_result.get("document_url") or "")
    return "\n".join(
        [
            f"# 【公众号今日稿件】{publish_date}｜{package.title}",
            "",
            f"- 今日日期: {publish_date}",
            f"- 今日栏目: {calendar_item.get('code')}｜{calendar_item.get('column')}",
            f"- 今日主选题: {decision.selected_topic.title}",
            f"- 文章标题: {package.title}",
            "- 当前状态: 待人工确认发布",
            f"- 建议发布时间: 今天{suggested_publish_time}",
            f"- 可复制公众号正文路径: {output_path / 'wechat_ready_article.md'}",
            f"- 发布包路径: {output_path / 'publish_package.md'}",
            f"- 飞书协作文档: {feishu_doc_url or '未创建或未启用'}",
        ]
    )


def render_feishu_doc_content(
    output_dir: Path,
    calendar_item: dict[str, Any],
    package: PublishPackage,
    suggested_publish_time: str,
) -> str:
    sections = [
        ("一、今日3个选题", "topics.md"),
        ("二、主编评估结果", "selected_topic.md"),
        ("三、文章大纲与公众号初稿", "draft.md"),
        ("四、审稿意见", "review.md"),
        ("五、最终定稿", "final_article.md"),
        ("六、可复制公众号正文", "wechat_ready_article.md"),
        ("七、发布包", "publish_package.md"),
    ]
    lines = [
        f"# {calendar_item['date']}｜{calendar_item.get('code')}｜{package.title}",
        "",
        "【公众号内容协作文档】",
        "",
        f"- 日期：{calendar_item['date']}",
        f"- 栏目：{calendar_item.get('code')}｜{calendar_item.get('column')}",
        f"- 内容层级：{calendar_item.get('layer')}",
        f"- 文章标题：《{package.title}》",
        f"- 建议发布时间：今天{suggested_publish_time}",
        "- 当前状态：待主编确认 / 待运营排版 / 待老板确认发布",
        "",
        "## 人工确认发布规则",
        "",
        "- 主编回复：通过 / 修改",
        "- 运营回复：已排版 / 待排版",
        "- 老板回复：可发 / 暂缓",
    ]
    for title, filename in sections:
        path = output_dir / filename
        content = path.read_text(encoding="utf-8").strip() if path.exists() else "本文件尚未生成。"
        lines.extend(["", f"## {title}", "", content])
    return "\n".join(lines)


def build_run_summary(
    publish_date: str,
    calendar_item: dict[str, Any],
    decision: EditorialDecision,
    package: PublishPackage,
    feishu_sent: bool,
    email_sent: bool,
    status: str,
    suggested_publish_time: str,
    feishu_doc_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    feishu_doc_result = feishu_doc_result or {}
    return {
        "date": publish_date,
        "calendar": {
            "code": calendar_item.get("code"),
            "column": calendar_item.get("column"),
            "layer": calendar_item.get("layer"),
        },
        "selected_topic": decision.selected_topic.title,
        "article_title": package.title,
        "status": status,
        "feishu_sent": feishu_sent,
        "email_sent": email_sent,
        "feishu_doc_created": bool(feishu_doc_result.get("created")),
        "feishu_doc_written": bool(feishu_doc_result.get("written")),
        "feishu_doc_url": feishu_doc_result.get("document_url", ""),
        "feishu_doc_error": feishu_doc_result.get("error", ""),
        "manual_publish_required": True,
        "suggested_publish_time": suggested_publish_time,
    }


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
    publish_date = calendar_item["date"]
    output_dir = root_dir / "outputs" / publish_date
    output_dir.mkdir(parents=True, exist_ok=True)

    topic_agent = TopicAgent(
        brand=brand,
        layers=DEFAULT_LAYERS,
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
            llm_outputs={"topic_agent": topic_agent.last_llm_response},
            completed_stage=stage,
        )

    editor_agent = EditorInChiefAgent(
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
            llm_outputs={
                "topic_agent": topic_agent.last_llm_response,
                "editor_in_chief_agent": editor_agent.last_llm_response,
            },
            completed_stage=stage,
        )

    writer_agent = WriterAgent(
        system_prompt=load_prompt(root_dir, "writer_agent.md"),
        llm=llm,
    )
    draft = writer_agent.write_article(decision)
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
            llm_outputs={
                "topic_agent": topic_agent.last_llm_response,
                "editor_in_chief_agent": editor_agent.last_llm_response,
                "writer_agent": writer_agent.last_llm_response,
            },
            completed_stage=stage,
        )
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
            llm_outputs={
                "topic_agent": topic_agent.last_llm_response,
                "editor_in_chief_agent": editor_agent.last_llm_response,
                "writer_agent": writer_agent.last_llm_response,
            },
            completed_stage=stage,
        )

    reviewer_agent = ReviewerAgent(
        system_prompt=load_prompt(root_dir, "reviewer_agent.md"),
        llm=llm,
    )
    review = reviewer_agent.review(draft)
    save_article(output_dir / "review.md", render_review(review))
    save_article(output_dir / "final_article.md", render_final_article(review))
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
            llm_outputs={
                "topic_agent": topic_agent.last_llm_response,
                "editor_in_chief_agent": editor_agent.last_llm_response,
                "writer_agent": writer_agent.last_llm_response,
                "reviewer_agent": reviewer_agent.last_llm_response,
            },
            completed_stage=stage,
        )

    publisher_agent = PublisherAgent(
        system_prompt=load_prompt(root_dir, "publisher_agent.md"),
        llm=llm,
    )
    package = publisher_agent.build_package(decision.selected_topic, review)
    save_article(output_dir / "publish_package.md", render_publish_package(package))
    save_article(output_dir / "wechat_ready_article.md", render_wechat_ready_article(review))
    feishu_doc_result = create_feishu_doc_from_markdown(
        title=f"{publish_date}｜{calendar_item.get('code')}｜{package.title}｜公众号内容包",
        markdown_content=render_feishu_doc_content(
            output_dir=output_dir,
            calendar_item=calendar_item,
            package=package,
            suggested_publish_time=suggested_publish_time,
        ),
    )
    save_article(
        output_dir / "feishu_message.md",
        render_feishu_message(
            package,
            calendar_item,
            output_dir,
            suggested_publish_time,
            feishu_doc_result,
        ),
    )
    email_summary = render_email_summary(
        publish_date,
        calendar_item,
        decision,
        package,
        suggested_publish_time,
        feishu_doc_result,
    )
    save_article(output_dir / "email_summary.md", email_summary)
    report_stage(stage, "publish", publish_date)
    report_stage(stage, "complete", publish_date)
    feishu_sent = notify_feishu_from_output(output_dir)
    email_sent = send_email_backup(
        subject=f"【公众号今日稿件】{publish_date}｜{package.title}",
        body=email_summary,
        attachments=[
            output_dir / "wechat_ready_article.md",
            output_dir / "final_article.md",
            output_dir / "publish_package.md",
            output_dir / "feishu_message.md",
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
            email_sent=email_sent,
            status="待人工发布",
            suggested_publish_time=suggested_publish_time,
            feishu_doc_result=feishu_doc_result,
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
        llm_outputs={
            "topic_agent": topic_agent.last_llm_response,
            "editor_in_chief_agent": editor_agent.last_llm_response,
            "writer_agent": writer_agent.last_llm_response,
            "reviewer_agent": reviewer_agent.last_llm_response,
            "publisher_agent": publisher_agent.last_llm_response,
        },
        completed_stage="publish" if stage == "publish" else "all",
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
        "llm_outputs": llm_outputs or {},
        "completed_stage": completed_stage,
    }
