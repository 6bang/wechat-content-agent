from __future__ import annotations

import html
import json
import mimetypes
import os
import re
import subprocess
import uuid
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from utils.llm import load_env


WECHAT_API_BASE = "https://api.weixin.qq.com/cgi-bin"


class WeChatDraftError(RuntimeError):
    pass


def is_wechat_draft_enabled() -> bool:
    load_env()
    return os.getenv("ENABLE_WECHAT_DRAFT", "").strip().lower() == "true"


def sync_output_to_wechat_draft(output_dir: Path, dry_run: bool = False) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    article_markdown_path = output_dir / "wechat_ready_article.md"
    package_path = output_dir / "publish_package.md"

    if not article_markdown_path.exists():
        raise WeChatDraftError(f"Missing article file: {article_markdown_path}")

    article_markdown = article_markdown_path.read_text(encoding="utf-8").strip()
    publish_package = package_path.read_text(encoding="utf-8") if package_path.exists() else ""
    title = extract_title(article_markdown, publish_package)
    digest = extract_digest(publish_package, article_markdown)
    author = get_optional_env("WECHAT_AUTHOR", "老六")
    source_url = get_optional_env("WECHAT_CONTENT_SOURCE_URL", "")
    content_html = markdown_to_wechat_html(article_markdown)

    if dry_run:
        return {
            "enabled": is_wechat_draft_enabled(),
            "dry_run": True,
            "created": False,
            "title": title,
            "author": author,
            "digest": digest,
            "content_chars": len(article_markdown),
            "html_chars": len(content_html),
            "media_id": "",
            "error": "",
        }

    if not is_wechat_draft_enabled():
        raise WeChatDraftError("ENABLE_WECHAT_DRAFT must be true before syncing to WeChat draft.")

    access_token = get_access_token(
        app_id=get_required_env("WECHAT_APP_ID"),
        app_secret=get_required_env("WECHAT_APP_SECRET"),
    )
    thumb_media_id = get_thumb_media_id(access_token, output_dir=output_dir)
    media_id = add_draft(
        access_token=access_token,
        title=title,
        author=author,
        digest=digest,
        content=content_html,
        thumb_media_id=thumb_media_id,
        source_url=source_url,
    )
    return {
        "enabled": True,
        "dry_run": False,
        "created": True,
        "title": title,
        "author": author,
        "digest": digest,
        "content_chars": len(article_markdown),
        "html_chars": len(content_html),
        "thumb_media_id": thumb_media_id,
        "media_id": media_id,
        "error": "",
    }


def get_access_token(app_id: str, app_secret: str) -> str:
    query = urllib.parse.urlencode(
        {
            "grant_type": "client_credential",
            "appid": app_id,
            "secret": app_secret,
        }
    )
    payload = get_json(f"{WECHAT_API_BASE}/token?{query}")
    token = payload.get("access_token")
    if not token:
        raise WeChatDraftError(f"WeChat access_token was not returned: {payload}")
    return str(token)


def get_thumb_media_id(access_token: str, output_dir: Path | None = None) -> str:
    existing_media_id = get_optional_env("WECHAT_THUMB_MEDIA_ID", "") or get_optional_env(
        "WECHAT_COVER_MEDIA_ID",
        "",
    )
    if existing_media_id:
        return existing_media_id

    output_cover_path = resolve_output_cover_path(output_dir) if output_dir else None
    cover_path = str(output_cover_path) if output_cover_path else get_optional_env("WECHAT_COVER_IMAGE_PATH", "")
    if not cover_path:
        raise WeChatDraftError(
            "Please set WECHAT_THUMB_MEDIA_ID or WECHAT_COVER_IMAGE_PATH before creating a draft."
        )

    path = Path(cover_path).expanduser()
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    if not path.exists():
        raise WeChatDraftError(f"Cover image does not exist: {path}")

    return upload_permanent_material(access_token, path=path, material_type="thumb")


def resolve_output_cover_path(output_dir: Path | None) -> Path | None:
    if output_dir is None:
        return None

    direct_candidates = [
        output_dir / "cover_export" / "cover.jpg",
        output_dir / "cover_export" / "cover.png",
        output_dir / "visual_assets" / "cover.jpg",
        output_dir / "visual_assets" / "cover.png",
    ]
    for path in direct_candidates:
        if path.exists():
            return path

    cover_svg = output_dir / "visual_assets" / "cover.svg"
    if not cover_svg.exists():
        return None

    exported = output_dir / "cover_export" / "cover.jpg"
    if export_svg_cover_to_jpg(cover_svg, exported):
        return exported
    return None


def export_svg_cover_to_jpg(svg_path: Path, jpg_path: Path) -> bool:
    sips = shutil_which("sips")
    if not sips:
        return False

    jpg_path.parent.mkdir(parents=True, exist_ok=True)
    png_path = jpg_path.parent / "cover.png"
    try:
        subprocess.run(
            [sips, "-s", "format", "png", str(svg_path), "--out", str(png_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            [sips, "-s", "format", "jpeg", "-Z", "900", str(png_path), "--out", str(jpg_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return jpg_path.exists()
    except Exception:
        return False


def shutil_which(command: str) -> str | None:
    from shutil import which

    return which(command)


def upload_permanent_material(access_token: str, path: Path, material_type: str = "thumb") -> str:
    query = urllib.parse.urlencode({"access_token": access_token, "type": material_type})
    url = f"{WECHAT_API_BASE}/material/add_material?{query}"
    content_type, body = build_multipart_body(field_name="media", path=path)
    payload = post_bytes(url, body=body, content_type=content_type)
    media_id = payload.get("media_id")
    if not media_id:
        raise WeChatDraftError(f"WeChat did not return media_id after upload: {payload}")
    return str(media_id)


def add_draft(
    access_token: str,
    title: str,
    author: str,
    digest: str,
    content: str,
    thumb_media_id: str,
    source_url: str = "",
) -> str:
    query = urllib.parse.urlencode({"access_token": access_token})
    payload = post_json(
        f"{WECHAT_API_BASE}/draft/add?{query}",
        {
            "articles": [
                {
                    "title": title[:64],
                    "author": author[:8],
                    "digest": digest[:120],
                    "content": content,
                    "content_source_url": source_url,
                    "thumb_media_id": thumb_media_id,
                    "need_open_comment": 0,
                    "only_fans_can_comment": 0,
                }
            ]
        },
    )
    media_id = payload.get("media_id")
    if not media_id:
        raise WeChatDraftError(f"WeChat did not return draft media_id: {payload}")
    return str(media_id)


def markdown_to_wechat_html(markdown_text: str) -> str:
    lines = markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    html_lines: list[str] = []
    list_mode: str | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if list_mode:
                html_lines.append(f"</{list_mode}>")
                list_mode = None
            continue

        if line == "---":
            if list_mode:
                html_lines.append(f"</{list_mode}>")
                list_mode = None
            html_lines.append("<section style=\"height:1px;background:#E8E2D8;margin:28px 0;\"></section>")
        elif line.startswith("# "):
            if list_mode:
                html_lines.append(f"</{list_mode}>")
                list_mode = None
            html_lines.append(f"<h1 style=\"font-size:24px;line-height:1.5;margin:0 0 22px;font-weight:700;color:#1F1F1F;letter-spacing:0;\">{format_inline(line[2:])}</h1>")
        elif line.startswith("## "):
            if list_mode:
                html_lines.append(f"</{list_mode}>")
                list_mode = None
            html_lines.append(f"<h2 style=\"font-size:18px;line-height:1.7;margin:34px 0 16px;padding-left:10px;border-left:4px solid #B88746;font-weight:700;color:#1F1F1F;\">{format_inline(line[3:])}</h2>")
        elif line.startswith(">"):
            if list_mode:
                html_lines.append(f"</{list_mode}>")
                list_mode = None
            quote = line.lstrip("> ").strip()
            html_lines.append(f"<blockquote style=\"margin:22px 0;padding:14px 16px;background:#F8F5EF;border-left:4px solid #B88746;color:#4A4035;font-size:16px;line-height:1.9;\">{format_inline(quote)}</blockquote>")
        elif line.startswith("- "):
            if list_mode != "ul":
                if list_mode:
                    html_lines.append(f"</{list_mode}>")
                html_lines.append("<ul style=\"padding-left:1.2em;margin:16px 0;\">")
                list_mode = "ul"
            html_lines.append(f"<li style=\"line-height:2;margin:8px 0;color:#2A2A2A;\">{format_inline(line[2:])}</li>")
        elif re.match(r"^\d+[.、]\s+", line):
            if list_mode != "ol":
                if list_mode:
                    html_lines.append(f"</{list_mode}>")
                html_lines.append("<ol style=\"padding-left:1.2em;margin:16px 0;\">")
                list_mode = "ol"
            item = re.sub(r"^\d+[.、]\s+", "", line)
            html_lines.append(f"<li style=\"line-height:2;margin:8px 0;color:#2A2A2A;\">{format_inline(item)}</li>")
        else:
            if list_mode:
                html_lines.append(f"</{list_mode}>")
                list_mode = None
            html_lines.append(f"<p style=\"font-size:16px;line-height:2.05;margin:18px 0;color:#2A2A2A;letter-spacing:0;\">{format_inline(line)}</p>")

    if list_mode:
        html_lines.append(f"</{list_mode}>")

    return "\n".join(
        [
            "<section style=\"font-size:16px;line-height:2.05;color:#2A2A2A;padding:0 2px;\">",
            *html_lines,
            "</section>",
        ]
    )


def format_inline(text: str) -> str:
    escaped = html.escape(text.strip())
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


def extract_title(article_markdown: str, publish_package: str) -> str:
    for line in article_markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip(" 《》")

    option = extract_first_numbered_after_heading(publish_package, "## 公众号标题3个版本")
    if option:
        return option.strip(" 《》")
    return "公众号今日稿件"


def extract_digest(publish_package: str, article_markdown: str) -> str:
    digest = extract_first_numbered_after_heading(publish_package, "## 公众号摘要")
    if digest:
        return digest
    plain_text = re.sub(r"#+\s*", "", article_markdown)
    plain_text = re.sub(r"\s+", " ", plain_text).strip()
    return plain_text[:110]


def extract_first_numbered_after_heading(markdown_text: str, heading: str) -> str:
    lines = markdown_text.splitlines()
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped == heading:
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            return ""
        if in_section:
            match = re.match(r"^\d+[.、]\s*(.+)$", stripped)
            if match:
                return match.group(1).strip()
    return ""


def build_multipart_body(field_name: str, path: Path) -> tuple[str, bytes]:
    boundary = f"----wechat-content-agent-{uuid.uuid4().hex}"
    filename = path.name
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    file_bytes = path.read_bytes()
    body = b"".join(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8"),
            f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"),
            file_bytes,
            f"\r\n--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    return f"multipart/form-data; boundary={boundary}", body


def get_json(url: str, timeout: int = 20) -> dict[str, Any]:
    request = urllib.request.Request(url, method="GET")
    return open_json_request(request, timeout=timeout)


def post_json(url: str, payload: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    return open_json_request(request, timeout=timeout)


def post_bytes(url: str, body: bytes, content_type: str, timeout: int = 30) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": content_type},
        method="POST",
    )
    return open_json_request(request, timeout=timeout)


def open_json_request(request: urllib.request.Request, timeout: int) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        raise WeChatDraftError(f"WeChat HTTP {exc.code}: {raw_body}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise WeChatDraftError(f"WeChat request failed: {exc}") from exc

    try:
        payload = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError as exc:
        raise WeChatDraftError(f"WeChat returned invalid JSON: {raw_body}") from exc

    errcode = payload.get("errcode", 0)
    if errcode not in (0, None):
        raise WeChatDraftError(f"WeChat API error errcode={errcode}, errmsg={payload.get('errmsg')}, body={payload}")
    return payload


def get_required_env(name: str) -> str:
    load_env()
    value = os.getenv(name, "").strip()
    if not value:
        raise WeChatDraftError(f"{name} is required.")
    return value


def get_optional_env(name: str, default: str = "") -> str:
    load_env()
    return os.getenv(name, default).strip()
