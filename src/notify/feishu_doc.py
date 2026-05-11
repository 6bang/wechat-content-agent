from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from utils.llm import load_env


FEISHU_API_BASE = "https://open.feishu.cn/open-apis"
TEXT_BLOCK_TYPE = 2
MAX_TEXT_BLOCK_CHARS = 1000
MAX_BLOCKS_PER_REQUEST = 40


class FeishuDocError(RuntimeError):
    pass


def is_feishu_doc_enabled() -> bool:
    load_env()
    return os.getenv("ENABLE_FEISHU_DOC", "").strip().lower() == "true"


def create_feishu_doc_from_markdown(title: str, markdown_content: str) -> dict[str, Any]:
    if not is_feishu_doc_enabled():
        print("Feishu doc skipped: ENABLE_FEISHU_DOC is not true.")
        return {
            "enabled": False,
            "created": False,
            "written": False,
            "document_id": "",
            "document_url": "",
            "error": "",
        }

    document_id = ""
    document_url = ""
    try:
        app_id = get_required_env("FEISHU_APP_ID")
        app_secret = get_required_env("FEISHU_APP_SECRET")
        folder_token = extract_folder_token(get_required_env("FEISHU_DOC_FOLDER_TOKEN"))

        tenant_access_token = get_tenant_access_token(app_id, app_secret)
        document = create_document(tenant_access_token, title=title, folder_token=folder_token)
        document_id = document["document_id"]
        document_url = build_document_url(document_id, document)

        write_markdown_to_document(
            tenant_access_token=tenant_access_token,
            document_id=document_id,
            markdown_content=markdown_content,
        )

        print(f"Feishu doc created: {document_url}")
        return {
            "enabled": True,
            "created": True,
            "written": True,
            "document_id": document_id,
            "document_url": document_url,
            "error": "",
        }
    except Exception as exc:
        print(f"Feishu doc failed: {exc}")
        return {
            "enabled": True,
            "created": bool(document_id),
            "written": False,
            "document_id": document_id,
            "document_url": document_url,
            "error": str(exc),
        }


def get_required_env(name: str) -> str:
    load_env()
    value = os.getenv(name, "").strip()
    if not value:
        raise FeishuDocError(f"{name} is required when ENABLE_FEISHU_DOC=true.")
    return value


def extract_folder_token(value: str) -> str:
    match = re.search(r"/folder/([^/?#]+)", value)
    if match:
        return match.group(1)
    return value.strip().split("?", 1)[0].strip()


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    payload = post_json(
        f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal",
        {
            "app_id": app_id,
            "app_secret": app_secret,
        },
    )
    token = payload.get("tenant_access_token") or payload.get("data", {}).get("tenant_access_token")
    if not token:
        raise FeishuDocError("tenant_access_token was not returned by Feishu.")
    return str(token)


def create_document(tenant_access_token: str, title: str, folder_token: str) -> dict[str, Any]:
    payload = post_json(
        f"{FEISHU_API_BASE}/docx/v1/documents",
        {
            "title": truncate_title(title),
            "folder_token": folder_token,
        },
        tenant_access_token=tenant_access_token,
    )
    data = payload.get("data", {})
    document = data.get("document") or data
    document_id = document.get("document_id") or data.get("document_id")
    if not document_id:
        raise FeishuDocError(f"document_id was not returned by Feishu: {payload}")
    document["document_id"] = str(document_id)
    return document


def write_markdown_to_document(
    tenant_access_token: str,
    document_id: str,
    markdown_content: str,
) -> None:
    blocks = markdown_to_text_blocks(markdown_content)
    if not blocks:
        return

    quoted_document_id = urllib.parse.quote(document_id, safe="")
    url = (
        f"{FEISHU_API_BASE}/docx/v1/documents/{quoted_document_id}"
        f"/blocks/{quoted_document_id}/children?document_revision_id=-1"
    )
    for chunk in chunked(blocks, MAX_BLOCKS_PER_REQUEST):
        post_json(
            url,
            {
                "index": -1,
                "children": chunk,
            },
            tenant_access_token=tenant_access_token,
        )
        time.sleep(0.35)


def markdown_to_text_blocks(markdown_content: str) -> list[dict[str, Any]]:
    blocks = []
    for paragraph in split_markdown_paragraphs(markdown_content):
        for part in split_text(paragraph, MAX_TEXT_BLOCK_CHARS):
            blocks.append(
                {
                    "block_type": TEXT_BLOCK_TYPE,
                    "text": {
                        "elements": [
                            {
                                "text_run": {
                                    "content": part,
                                    "text_element_style": {},
                                }
                            }
                        ],
                        "style": {},
                    },
                }
            )
    return blocks


def split_markdown_paragraphs(markdown_content: str) -> list[str]:
    normalized = markdown_content.replace("\r\n", "\n").replace("\r", "\n")
    raw_blocks = re.split(r"\n{2,}", normalized)
    return [block.strip() for block in raw_blocks if block.strip()]


def split_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    return [text[index : index + max_chars] for index in range(0, len(text), max_chars)]


def chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def truncate_title(title: str, max_chars: int = 120) -> str:
    compact = " ".join(title.strip().split())
    return compact[:max_chars] if compact else "公众号内容包"


def build_document_url(document_id: str, document: dict[str, Any]) -> str:
    for key in ("url", "document_url", "doc_url"):
        value = document.get(key)
        if value:
            return str(value)

    load_env()
    base_url = os.getenv("FEISHU_DOC_BASE_URL") or os.getenv("FEISHU_TENANT_DOMAIN") or ""
    base_url = base_url.strip().rstrip("/")
    if base_url:
        if not base_url.startswith(("http://", "https://")):
            base_url = f"https://{base_url}"
        return f"{base_url}/docx/{document_id}"

    return f"https://www.feishu.cn/docx/{document_id}"


def post_json(
    url: str,
    payload: dict[str, Any],
    tenant_access_token: str | None = None,
    timeout: int = 20,
) -> dict[str, Any]:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if tenant_access_token:
        headers["Authorization"] = f"Bearer {tenant_access_token}"

    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise FeishuDocError(f"Feishu HTTP {exc.code}: {body}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise FeishuDocError(f"Feishu request failed: {exc}") from exc

    try:
        parsed = json.loads(response_body) if response_body else {}
    except json.JSONDecodeError as exc:
        raise FeishuDocError(f"Feishu returned invalid JSON: {response_body}") from exc

    code = parsed.get("code", 0)
    if code != 0:
        raise FeishuDocError(f"Feishu API error code={code}, msg={parsed.get('msg')}, body={parsed}")
    return parsed
