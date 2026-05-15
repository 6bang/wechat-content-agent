from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from notify.feishu_notify import send_feishu_text
from utils.config_loader import load_yaml_config
from utils.llm import load_env


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "competitor_monitor"
DEFAULT_API_BASE = "https://api.justoneapi.com"
DEFAULT_TIMEZONE = "Asia/Shanghai"


class CompetitorMonitorError(RuntimeError):
    pass


@dataclass
class CompetitorAccount:
    name: str
    wxid: str
    focus: str = ""


@dataclass
class CompetitorArticle:
    account_name: str
    wxid: str
    title: str = ""
    url: str = ""
    publish_time: str = ""
    summary: str = ""
    read_count: str = "待获取"
    like_count: str = "待获取"
    share_count: str = "待获取"
    comment_count: str = "待获取"
    topic_angle: str = ""
    takeaway: str = ""
    status: str = "待配置"
    error: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor competitor WeChat official account articles.")
    parser.add_argument("--date", dest="run_date", help="Run date in YYYY-MM-DD. Defaults to Beijing today.")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config" / "competitor_accounts.yaml"))
    parser.add_argument("--no-feishu", action="store_true", help="Do not send the report to Feishu.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_date = date.fromisoformat(args.run_date) if args.run_date else beijing_today()
    result = run_competitor_monitor(run_date=run_date, config_path=Path(args.config), send_to_feishu=not args.no_feishu)
    print(f"Competitor monitor report: {result['report_path']}")
    return 0


def run_competitor_monitor(
    run_date: date | None = None,
    config_path: Path | None = None,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    send_to_feishu: bool = True,
) -> dict[str, Any]:
    load_env()
    current_date = run_date or beijing_today()
    config = load_yaml_config(config_path or PROJECT_ROOT / "config" / "competitor_accounts.yaml")
    accounts = load_competitor_accounts(config)
    provider = os.getenv("COMPETITOR_MONITOR_PROVIDER", "").strip().lower() or "justoneapi"

    if provider != "justoneapi":
        articles = [
            CompetitorArticle(
                account_name=account.name,
                wxid=account.wxid,
                status="待配置",
                error=f"Unsupported provider: {provider}",
            )
            for account in accounts
        ]
    else:
        client = JustOneWeChatClient.from_env()
        articles = [monitor_account(account, client) for account in accounts]

    output_dir = output_root / current_date.isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    report_md = render_report(current_date, articles)
    report_json = {
        "date": current_date.isoformat(),
        "provider": provider,
        "articles": [asdict(article) for article in articles],
    }
    report_path = output_dir / "competitor_monitor.md"
    json_path = output_dir / "competitor_monitor.json"
    report_path.write_text(report_md, encoding="utf-8")
    json_path.write_text(json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8")

    feishu_sent = False
    if send_to_feishu and is_competitor_feishu_enabled():
        feishu_sent = send_feishu_text(report_md, webhook_env="FEISHU_CONTROLLER_WEBHOOK_URL")

    return {
        "date": current_date.isoformat(),
        "report_path": str(report_path),
        "json_path": str(json_path),
        "feishu_sent": feishu_sent,
        "articles": articles,
    }


def beijing_today() -> date:
    return datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date()


def load_competitor_accounts(config: dict[str, Any]) -> list[CompetitorAccount]:
    raw_accounts = config.get("competitor_accounts", [])
    accounts: list[CompetitorAccount] = []
    for raw in raw_accounts:
        accounts.append(
            CompetitorAccount(
                name=str(raw.get("name", "")).strip(),
                wxid=str(raw.get("wxid", "")).strip(),
                focus=str(raw.get("focus", "")).strip(),
            )
        )
    return [account for account in accounts if account.name]


def monitor_account(account: CompetitorAccount, client: "JustOneWeChatClient") -> CompetitorArticle:
    if not account.wxid:
        return CompetitorArticle(
            account_name=account.name,
            wxid=account.wxid,
            topic_angle=guess_topic_angle("", account.focus),
            takeaway="请先补充公众号微信号 wxid，才能稳定监控最新文章。",
            status="待配置wxid",
            error="Missing wxid in config/competitor_accounts.yaml",
        )

    if not client.enabled:
        return CompetitorArticle(
            account_name=account.name,
            wxid=account.wxid,
            topic_angle=guess_topic_angle("", account.focus),
            takeaway="请先配置 JUSTONE_API_KEY，系统才能抓取最新文章和阅读数。",
            status="待配置API",
            error="Missing JUSTONE_API_KEY",
        )

    try:
        posts_payload = client.get_user_posts(account.wxid)
        post = first_article_item(posts_payload)
        title = pick_text(post, ["title", "name", "articleTitle", "article_title"])
        url = pick_text(post, ["url", "link", "articleUrl", "article_url", "content_url"])
        publish_time = pick_text(post, ["publish_time", "publishTime", "time", "date", "created_at"])
        summary = pick_text(post, ["summary", "digest", "description", "desc"])

        article = CompetitorArticle(
            account_name=account.name,
            wxid=account.wxid,
            title=title or "未识别标题",
            url=url,
            publish_time=publish_time,
            summary=summary,
            topic_angle=guess_topic_angle(title, account.focus),
            takeaway=build_takeaway(title, account.focus),
            status="已获取文章",
        )

        if url:
            feedback_payload = client.get_article_feedback(url)
            apply_feedback(article, feedback_payload)
            article.status = "已获取文章和数据"
        else:
            article.status = "已获取文章，缺少链接"
            article.error = "Article url not found in API response."
        return article
    except Exception as exc:
        return CompetitorArticle(
            account_name=account.name,
            wxid=account.wxid,
            topic_angle=guess_topic_angle("", account.focus),
            takeaway="本次抓取失败，需要查看 API 配额、wxid 是否正确，或稍后重试。",
            status="失败",
            error=str(exc),
        )


class JustOneWeChatClient:
    def __init__(self, token: str, base_url: str = DEFAULT_API_BASE):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.enabled = bool(token)

    @classmethod
    def from_env(cls) -> "JustOneWeChatClient":
        load_env()
        return cls(
            token=os.getenv("JUSTONE_API_KEY", "").strip(),
            base_url=os.getenv("JUSTONE_API_BASE", DEFAULT_API_BASE).strip() or DEFAULT_API_BASE,
        )

    def get_user_posts(self, wxid: str) -> dict[str, Any]:
        return self.get_json("/api/weixin/get-user-post/v1", {"wxid": wxid})

    def get_article_feedback(self, article_url: str) -> dict[str, Any]:
        return self.get_json("/api/weixin/get-article-feedback/v1", {"articleUrl": article_url})

    def get_json(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        if not self.token:
            raise CompetitorMonitorError("JUSTONE_API_KEY is not configured.")
        query = urllib.parse.urlencode({"token": self.token, **params})
        request = urllib.request.Request(
            f"{self.base_url}{path}?{query}",
            method="GET",
            headers={"User-Agent": "wechat-content-agent-competitor-monitor"},
        )
        try:
            with urllib.request.urlopen(request, timeout=70) as response:
                body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise CompetitorMonitorError(f"JustOne API HTTP {exc.code}: {body}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise CompetitorMonitorError(f"JustOne API request failed: {exc}") from exc

        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError as exc:
            raise CompetitorMonitorError(f"JustOne API returned invalid JSON: {body[:300]}") from exc

        code = payload.get("code")
        if code not in (None, 0, "0"):
            raise CompetitorMonitorError(f"JustOne API error code={code}: {payload}")
        return payload


def first_article_item(payload: Any) -> dict[str, Any]:
    items = find_first_list(payload)
    if not items:
        raise CompetitorMonitorError("No article list found in API response.")
    first = items[0]
    if not isinstance(first, dict):
        raise CompetitorMonitorError(f"Unexpected article item: {first}")
    return first


def find_first_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        preferred_keys = ["items", "list", "posts", "articles", "data", "result"]
        for key in preferred_keys:
            if key in value:
                found = find_first_list(value[key])
                if found:
                    return found
        for child in value.values():
            found = find_first_list(child)
            if found:
                return found
    return []


def pick_text(payload: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return str(payload[key]).strip()
    for value in payload.values():
        if isinstance(value, dict):
            nested = pick_text(value, keys)
            if nested:
                return nested
    return ""


def apply_feedback(article: CompetitorArticle, payload: dict[str, Any]) -> None:
    flat = flatten_dict(payload)
    article.read_count = pick_metric(flat, ["read_count", "readCount", "reads", "read", "read_num", "readNum"])
    article.like_count = pick_metric(flat, ["like_count", "likeCount", "likes", "like", "like_num", "old_like_num"])
    article.share_count = pick_metric(flat, ["share_count", "shareCount", "shares", "share", "share_num"])
    article.comment_count = pick_metric(flat, ["comment_count", "commentCount", "comments", "comment", "comment_num"])


def flatten_dict(value: Any, prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            text_key = f"{prefix}.{key}" if prefix else str(key)
            flat[text_key] = child
            flat.update(flatten_dict(child, text_key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            flat.update(flatten_dict(child, f"{prefix}.{index}"))
    return flat


def pick_metric(flat: dict[str, Any], keys: list[str]) -> str:
    lower_lookup = {key.lower().split(".")[-1]: value for key, value in flat.items()}
    for key in keys:
        value = lower_lookup.get(key.lower())
        if value not in (None, ""):
            return str(value)
    return "待获取"


def guess_topic_angle(title: str, focus: str = "") -> str:
    text = f"{title} {focus}"
    rules = [
        ("AI/科技趋势", ["AI", "人工智能", "大模型", "芯片", "科技", "手机", "互联网"]),
        ("商业案例拆解", ["案例", "公司", "品牌", "增长", "生意", "商业"]),
        ("组织管理认知", ["管理", "组织", "团队", "老板", "领导", "员工"]),
        ("知识学习/课程转化", ["学习", "课程", "知识", "得到", "认知"]),
        ("消费产品/年轻化表达", ["产品", "差评", "年轻", "体验", "测评"]),
    ]
    for label, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return label
    return "待人工判断"


def build_takeaway(title: str, focus: str) -> str:
    if not title:
        return "本次未抓到标题，先检查账号 wxid 或 API 配置。"
    angle = guess_topic_angle(title, focus)
    return f"可参考其「{angle}」切入方式：标题先制造具体问题，再用案例或观点承接。"


def render_report(run_date: date, articles: list[CompetitorArticle]) -> str:
    lines = [
        f"【公众号对标账号每日监控】",
        "",
        f"日期：{run_date.isoformat()}",
        "监控账号：笔记侠、得到、刘润、差评君",
        "",
        "说明：阅读数来自已配置的数据源；若显示“待获取”，说明 API Key、wxid 或第三方数据源还没配置完整。",
        "",
        "## 今日最新文章",
    ]
    for article in articles:
        lines.extend(
            [
                "",
                f"### {article.account_name}",
                "",
                f"- 状态：{article.status}",
                f"- 标题：{article.title or '待获取'}",
                f"- 发布时间：{article.publish_time or '待获取'}",
                f"- 阅读数：{article.read_count}",
                f"- 点赞/喜欢：{article.like_count}",
                f"- 分享数：{article.share_count}",
                f"- 评论数：{article.comment_count}",
                f"- 选题角度：{article.topic_angle or '待判断'}",
                f"- 选题启发：{article.takeaway or '待判断'}",
                f"- 链接：{article.url or '待获取'}",
            ]
        )
        if article.error:
            lines.append(f"- 异常：{article.error}")

    lines.extend(
        [
            "",
            "## 给六邦公众号的选题启发",
            "",
            *render_topic_suggestions(articles),
        ]
    )
    return "\n".join(lines)


def render_topic_suggestions(articles: list[CompetitorArticle]) -> list[str]:
    successful = [article for article in articles if article.title and article.status.startswith("已获取")]
    if not successful:
        return [
            "- 先完成数据源配置，再沉淀每日对标选题规律。",
            "- 当前可先人工把对标文章链接或截图发到飞书，由复盘 Agent 补录阅读数。",
        ]
    suggestions = []
    for article in successful:
        suggestions.append(
            f"- 参考「{article.account_name}」：{article.topic_angle}｜可转成电商老板视角：为什么这个问题会影响团队流程和经营结果？"
        )
    return suggestions


def is_competitor_feishu_enabled() -> bool:
    load_env()
    if os.getenv("ENABLE_FEISHU", "").strip().lower() != "true":
        return False
    return os.getenv("ENABLE_COMPETITOR_MONITOR_FEISHU", "").strip().lower() != "false"


if __name__ == "__main__":
    sys.exit(main())
