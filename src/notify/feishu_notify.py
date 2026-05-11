from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from utils.llm import load_env


KEYWORD = "公众号"
DEFAULT_TIMEZONE = "Asia/Shanghai"


def is_feishu_enabled() -> bool:
    load_env()
    return os.getenv("ENABLE_FEISHU", "").strip().lower() == "true"


def is_stage_report_enabled() -> bool:
    load_env()
    return os.getenv("ENABLE_FEISHU_STAGE_REPORT", "true").strip().lower() == "true"


def notify_feishu_from_output(output_dir: Path) -> bool:
    if not is_feishu_enabled():
        print("Feishu notification skipped: ENABLE_FEISHU is not true.")
        return False

    message_path = output_dir / "feishu_message.md"
    if not message_path.exists():
        print(f"Feishu notification skipped: {message_path} does not exist.")
        return False

    content = message_path.read_text(encoding="utf-8").strip()
    if KEYWORD not in content:
        content = f"{KEYWORD}通知\n\n{content}"

    return send_feishu_text(content)


def send_feishu_stage_report(
    stage_name: str,
    role_name: str,
    task_name: str,
    status: str,
    summary: str,
    output_files: list[str],
    next_step: str,
) -> bool:
    if not is_feishu_enabled():
        print("Feishu stage report skipped: ENABLE_FEISHU is not true.")
        return False
    if not is_stage_report_enabled():
        print("Feishu stage report skipped: ENABLE_FEISHU_STAGE_REPORT is not true.")
        return False

    content = build_stage_report_message(
        stage_name=stage_name,
        role_name=role_name,
        task_name=task_name,
        status=status,
        summary=summary,
        output_files=output_files,
        next_step=next_step,
    )
    return send_feishu_text(content)


def send_feishu_failure_report(
    stage_name: str,
    role_name: str,
    task_name: str,
    error: Exception,
    output_files: list[str] | None = None,
) -> bool:
    if not is_feishu_enabled():
        return False
    if not is_stage_report_enabled():
        return False

    files = output_files or []
    date_text = extract_date_from_output_files(files)
    content = "\n".join(
        [
            f"【公众号内容流水线｜{stage_name}失败】",
            "",
            f"日期：{date_text}",
            f"当前角色：{role_name}",
            f"当前任务：{task_name}",
            "当前状态：失败",
            "",
            "失败原因：",
            error.__class__.__name__,
            "",
            "错误信息：",
            str(error),
            "",
            "建议动作：",
            "请查看 GitHub Actions 日志，修复后手动重新运行 workflow。",
        ]
    )
    return send_feishu_text(content)


def build_stage_report_message(
    stage_name: str,
    role_name: str,
    task_name: str,
    status: str,
    summary: str,
    output_files: list[str],
    next_step: str,
) -> str:
    files = "\n".join(f"- {path}" for path in output_files) if output_files else "- 无"
    return "\n".join(
        [
            f"【公众号内容流水线｜{stage_name}】",
            "",
            f"日期：{extract_date_from_output_files(output_files)}",
            f"当前角色：{role_name}",
            f"当前任务：{task_name}",
            f"当前状态：{status}",
            "",
            "本阶段摘要：",
            summary,
            "",
            "交付文件：",
            files,
            "",
            "下一步：",
            next_step,
        ]
    )


def extract_date_from_output_files(output_files: list[str]) -> str:
    for output_file in output_files:
        parts = Path(output_file).parts
        for index, part in enumerate(parts):
            if part == "outputs" and index + 1 < len(parts):
                return parts[index + 1]
    return datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date().isoformat()


def send_feishu_text(content: str) -> bool:
    load_env()
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
    if not webhook_url:
        print("Feishu notification skipped: FEISHU_WEBHOOK_URL is not configured.")
        return False

    payload = {
        "msg_type": "text",
        "content": {
            "text": content,
        },
    }
    request = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            if response.status >= 400:
                print(f"Feishu notification failed with HTTP {response.status}.")
                return False
            if not is_success_response(body):
                print(f"Feishu notification failed: {body}")
                return False
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"Feishu notification failed: {exc}")
        return False

    print("Feishu notification sent.")
    return True


def is_success_response(body: str) -> bool:
    if not body:
        return True
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return True

    if "code" in payload:
        return payload.get("code") == 0
    if "StatusCode" in payload:
        return payload.get("StatusCode") == 0
    return True
