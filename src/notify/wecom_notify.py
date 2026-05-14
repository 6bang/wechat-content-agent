from __future__ import annotations

import os
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from utils.llm import load_env


def is_wecom_notify_enabled() -> bool:
    load_env()
    return os.getenv("ENABLE_WECOM_NOTIFY", "").strip().lower() == "true"


def get_wecom_webhook_url() -> str:
    load_env()
    return os.getenv("WECOM_WEBHOOK_URL", "").strip()


def send_wecom_text(content: str) -> bool:
    if not is_wecom_notify_enabled():
        print("WeCom notification skipped: ENABLE_WECOM_NOTIFY is not true.")
        return False

    webhook_url = get_wecom_webhook_url()
    if not webhook_url:
        print("WeCom notification skipped: WECOM_WEBHOOK_URL is empty.")
        return False

    payload = {
        "msgtype": "text",
        "text": {
            "content": content,
        },
    }
    try:
        post_json(webhook_url, payload)
    except Exception as exc:
        print(f"WeCom notification failed: {exc}")
        return False
    return True


def notify_wecom_from_output(output_dir: Path) -> bool:
    message_path = output_dir / "feishu_message.md"
    if not message_path.exists():
        print(f"WeCom final notification skipped: {message_path} does not exist.")
        return False
    content = message_path.read_text(encoding="utf-8")
    return send_wecom_text(content)


def send_wecom_stage_report(
    stage_name: str,
    role_name: str,
    task_name: str,
    status: str,
    summary: str,
    output_files: list[str],
    next_step: str,
) -> bool:
    output_text = "\n".join(f"- {path}" for path in output_files) if output_files else "- 无"
    content = "\n".join(
        [
            f"【公众号内容流水线｜{stage_name}】",
            "",
            f"日期：{datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()}",
            f"当前角色：{role_name}",
            f"当前任务：{task_name}",
            f"当前状态：{status}",
            "",
            "本阶段摘要：",
            summary,
            "",
            "交付文件：",
            output_text,
            "",
            "下一步：",
            next_step,
        ]
    )
    return send_wecom_text(content)


def send_wecom_failure_report(
    stage_name: str,
    role_name: str,
    task_name: str,
    error: Exception,
    output_files: list[str] | None = None,
) -> bool:
    output_text = "\n".join(f"- {path}" for path in output_files or []) or "- 无"
    content = "\n".join(
        [
            f"【公众号内容流水线｜{stage_name}失败】",
            "",
            f"日期：{datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()}",
            f"当前角色：{role_name}",
            f"当前任务：{task_name}",
            "当前状态：失败",
            "",
            "失败原因：",
            str(error),
            "",
            "已生成文件：",
            output_text,
            "",
            "建议动作：",
            "请查看 GitHub Actions 日志，修复后手动重新运行 workflow。",
        ]
    )
    try:
        return send_wecom_text(content)
    except Exception as exc:
        print(f"WeCom failure report skipped after secondary error: {exc}")
        return False


def post_json(url: str, payload: dict) -> None:
    import json

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "wechat-content-agent-wecom-notify",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response_body = response.read().decode("utf-8", errors="ignore")
            if response.status >= 400:
                raise RuntimeError(f"WeCom HTTP {response.status}: {response_body}")
    except urllib.error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"WeCom HTTP {exc.code}: {response_body}") from exc
