from __future__ import annotations

import base64
import hashlib
import json
import os
import random
import re
import string
import struct
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from flask import Flask, Response, request


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.llm import load_env


GITHUB_API_VERSION = "2022-11-28"
WECOM_TEXT_MAX_LEN = 1900


class WeComRemoteError(RuntimeError):
    pass


@dataclass(frozen=True)
class RemoteCommand:
    action: str
    description: str
    run_date: str
    stage: str = "all"
    layer: str = "C"
    should_dispatch: bool = True

    def workflow_inputs(self) -> dict[str, str]:
        return {
            "run_date": self.run_date,
            "action": self.action,
            "stage": self.stage,
            "layer": self.layer,
        }


def create_app() -> Flask:
    load_env()
    app = Flask(__name__)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "service": "wecom-remote-control"}

    @app.get("/wecom/callback")
    def verify_callback() -> Response:
        crypto = WeComCrypto.from_env()
        echo = crypto.decrypt_echostr(
            msg_signature=required_query("msg_signature"),
            timestamp=required_query("timestamp"),
            nonce=required_query("nonce"),
            echostr=required_query("echostr"),
        )
        return Response(echo, mimetype="text/plain")

    @app.post("/wecom/callback")
    def receive_message() -> Response:
        crypto = WeComCrypto.from_env()
        timestamp = required_query("timestamp")
        nonce = required_query("nonce")
        msg_signature = required_query("msg_signature")
        decrypted_xml = crypto.decrypt_message(
            msg_signature=msg_signature,
            timestamp=timestamp,
            nonce=nonce,
            body=request.data.decode("utf-8"),
        )
        reply_text, to_user, from_user = handle_incoming_message(decrypted_xml)
        encrypted_reply = crypto.encrypt_reply(
            reply_text=reply_text,
            to_user=to_user,
            from_user=from_user,
            nonce=nonce,
        )
        return Response(encrypted_reply, mimetype="application/xml")

    return app


def required_query(name: str) -> str:
    value = request.args.get(name, "").strip()
    if not value:
        raise WeComRemoteError(f"Missing query parameter: {name}")
    return value


class WeComCrypto:
    def __init__(self, token: str, encoding_aes_key: str, corp_id: str):
        if len(encoding_aes_key) != 43:
            raise WeComRemoteError("WECOM_ENCODING_AES_KEY must be 43 characters.")
        self.token = token
        self.corp_id = corp_id
        self.aes_key = base64.b64decode(f"{encoding_aes_key}=")
        if len(self.aes_key) != 32:
            raise WeComRemoteError("Decoded WECOM_ENCODING_AES_KEY must be 32 bytes.")

    @classmethod
    def from_env(cls) -> "WeComCrypto":
        return cls(
            token=get_required_env("WECOM_CALLBACK_TOKEN"),
            encoding_aes_key=get_required_env("WECOM_ENCODING_AES_KEY"),
            corp_id=get_required_env("WECOM_CORP_ID"),
        )

    def decrypt_echostr(self, msg_signature: str, timestamp: str, nonce: str, echostr: str) -> str:
        self.verify_signature(msg_signature, timestamp, nonce, echostr)
        return self.decrypt(echostr)

    def decrypt_message(self, msg_signature: str, timestamp: str, nonce: str, body: str) -> str:
        encrypted = parse_xml_text(body, "Encrypt")
        self.verify_signature(msg_signature, timestamp, nonce, encrypted)
        return self.decrypt(encrypted)

    def encrypt_reply(self, reply_text: str, to_user: str, from_user: str, nonce: str) -> str:
        timestamp = str(int(time.time()))
        reply_xml = build_text_reply_xml(to_user=to_user, from_user=from_user, content=reply_text)
        encrypted = self.encrypt(reply_xml)
        msg_signature = make_signature(self.token, timestamp, nonce, encrypted)
        return "\n".join(
            [
                "<xml>",
                f"<Encrypt><![CDATA[{encrypted}]]></Encrypt>",
                f"<MsgSignature><![CDATA[{msg_signature}]]></MsgSignature>",
                f"<TimeStamp>{timestamp}</TimeStamp>",
                f"<Nonce><![CDATA[{nonce}]]></Nonce>",
                "</xml>",
            ]
        )

    def verify_signature(self, msg_signature: str, timestamp: str, nonce: str, encrypted: str) -> None:
        expected = make_signature(self.token, timestamp, nonce, encrypted)
        if expected != msg_signature:
            raise WeComRemoteError("Invalid WeCom message signature.")

    def decrypt(self, encrypted: str) -> str:
        raw = base64.b64decode(encrypted)
        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(self.aes_key[:16]))
        decryptor = cipher.decryptor()
        padded = decryptor.update(raw) + decryptor.finalize()
        plain = pkcs7_unpad(padded)
        if len(plain) < 20:
            raise WeComRemoteError("Invalid encrypted WeCom payload.")
        msg_len = struct.unpack(">I", plain[16:20])[0]
        msg = plain[20 : 20 + msg_len]
        corp_id = plain[20 + msg_len :].decode("utf-8")
        if corp_id != self.corp_id:
            raise WeComRemoteError("WeCom corp_id mismatch.")
        return msg.decode("utf-8")

    def encrypt(self, message_xml: str) -> str:
        message_bytes = message_xml.encode("utf-8")
        plain = (
            random_bytes(16)
            + struct.pack(">I", len(message_bytes))
            + message_bytes
            + self.corp_id.encode("utf-8")
        )
        padded = pkcs7_pad(plain)
        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(self.aes_key[:16]))
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded) + encryptor.finalize()
        return base64.b64encode(encrypted).decode("utf-8")


def make_signature(token: str, timestamp: str, nonce: str, encrypted: str) -> str:
    payload = "".join(sorted([token, timestamp, nonce, encrypted]))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def pkcs7_pad(data: bytes, block_size: int = 32) -> bytes:
    pad_len = block_size - len(data) % block_size
    return data + bytes([pad_len]) * pad_len


def pkcs7_unpad(data: bytes, block_size: int = 32) -> bytes:
    if not data:
        raise WeComRemoteError("Empty decrypted payload.")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > block_size:
        raise WeComRemoteError("Invalid PKCS7 padding.")
    return data[:-pad_len]


def random_bytes(length: int) -> bytes:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length)).encode("utf-8")


def parse_xml_text(xml_text: str, field_name: str, default: str = "") -> str:
    root = ET.fromstring(xml_text)
    value = root.findtext(field_name)
    return value if value is not None else default


def build_text_reply_xml(to_user: str, from_user: str, content: str) -> str:
    safe_content = content[:WECOM_TEXT_MAX_LEN]
    return "\n".join(
        [
            "<xml>",
            f"<ToUserName><![CDATA[{to_user}]]></ToUserName>",
            f"<FromUserName><![CDATA[{from_user}]]></FromUserName>",
            f"<CreateTime>{int(time.time())}</CreateTime>",
            "<MsgType><![CDATA[text]]></MsgType>",
            f"<Content><![CDATA[{safe_content}]]></Content>",
            "</xml>",
        ]
    )


def handle_incoming_message(message_xml: str) -> tuple[str, str, str]:
    root = ET.fromstring(message_xml)
    to_user = root.findtext("FromUserName") or ""
    from_user = root.findtext("ToUserName") or get_optional_env("WECOM_CORP_ID", "")
    sender = root.findtext("FromUserName") or ""
    msg_type = root.findtext("MsgType") or ""
    content = (root.findtext("Content") or "").strip()

    if not sender_allowed(sender):
        return "公众号远程控制已拒绝：你不在允许名单里。", to_user, from_user

    if msg_type != "text":
        return help_text(prefix="公众号远程控制目前先支持文字指令。"), to_user, from_user

    command = parse_remote_command(content)
    if not command.should_dispatch:
        return help_text(prefix=command.description), to_user, from_user

    try:
        trigger_github_workflow(command)
    except Exception as exc:
        return (
            "公众号远程控制收到指令，但触发 GitHub Actions 失败。\n"
            f"指令：{command.description}\n"
            f"错误：{exc}\n"
            "请检查远程服务环境变量 GITHUB_ACTIONS_TOKEN。"
        ), to_user, from_user

    return (
        "公众号远程控制已收到。\n"
        f"任务：{command.description}\n"
        f"日期：{command.run_date}\n"
        "状态：已触发 GitHub Actions，请稍后看企业微信群/飞书群汇报。"
    ), to_user, from_user


def sender_allowed(sender: str) -> bool:
    allowlist = get_optional_env("WECOM_ALLOWED_USER_IDS", "").strip()
    if not allowlist:
        return True
    allowed = {item.strip() for item in allowlist.split(",") if item.strip()}
    return sender in allowed


def parse_remote_command(text: str) -> RemoteCommand:
    normalized = normalize_command(text)
    run_date = extract_run_date(normalized)

    if not normalized or "帮助" in normalized or "菜单" in normalized or normalized.lower() in {"help", "/help"}:
        return RemoteCommand(
            action="help",
            description="企业微信公众号远程控制菜单",
            run_date=run_date,
            should_dispatch=False,
        )

    layer = extract_layer(normalized)
    if layer and re.search(r"(发|同步|推送|草稿箱|选)", normalized):
        return RemoteCommand(
            action="sync_wechat_draft",
            description=f"同步 {layer} 层文章到公众号草稿箱",
            run_date=run_date,
            layer=layer,
        )

    stage_keywords = [
        ("topics", ["只跑选题", "跑选题", "生成选题", "选题"]),
        ("editor", ["主编评估", "评估选题"]),
        ("outline", ["写大纲", "生成大纲", "大纲"]),
        ("draft", ["写初稿", "生成初稿", "初稿"]),
        ("review", ["审稿", "定稿"]),
        ("publish", ["发布包", "运营包"]),
        ("visual", ["视觉", "封面", "排版"]),
    ]
    for stage, keywords in stage_keywords:
        if any(keyword in normalized for keyword in keywords):
            return RemoteCommand(
                action="daily_pipeline",
                description=f"运行公众号内容流水线阶段：{stage}",
                run_date=run_date,
                stage=stage,
            )

    if any(keyword in normalized for keyword in ["重写", "重新写", "重新生成", "今日三篇", "三篇文章", "跑全流程"]):
        return RemoteCommand(
            action="daily_pipeline",
            description="重新生成今日 C/E/S 三篇公众号文章",
            run_date=run_date,
            stage="all",
        )

    return RemoteCommand(
        action="help",
        description=f"没有识别到指令：{text}",
        run_date=run_date,
        should_dispatch=False,
    )


def normalize_command(text: str) -> str:
    return re.sub(r"\s+", "", text.strip())


def extract_run_date(text: str) -> str:
    match = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    if match:
        return match.group(1)
    return datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()


def extract_layer(text: str) -> str | None:
    upper_text = text.upper()
    match = re.search(r"(?:发|同步|推送|草稿箱|选)([CES])", upper_text)
    if match:
        return match.group(1)
    match = re.search(r"([CES])(?:层|篇)", upper_text)
    if match:
        return match.group(1)
    return None


def trigger_github_workflow(command: RemoteCommand) -> None:
    owner = get_required_env("GITHUB_OWNER")
    repo = get_required_env("GITHUB_REPO")
    workflow_file = get_optional_env("GITHUB_WORKFLOW_FILE", "daily_content.yml")
    branch = get_optional_env("GITHUB_DEFAULT_BRANCH", "main")
    token = get_required_env("GITHUB_ACTIONS_TOKEN")
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches"
    payload = {
        "ref": branch,
        "inputs": command.workflow_inputs(),
    }
    body = json.dumps(payload).encode("utf-8")
    request_obj = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Content-Type": "application/json",
            "User-Agent": "wechat-content-agent-wecom-remote",
        },
    )
    try:
        with urllib.request.urlopen(request_obj, timeout=15) as response:
            if response.status != 204:
                raise WeComRemoteError(f"GitHub Actions returned HTTP {response.status}.")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise WeComRemoteError(f"GitHub Actions HTTP {exc.code}: {error_body}") from exc


def help_text(prefix: str = "") -> str:
    lines = [
        "【公众号企业微信远程控制】",
        "",
        "可用指令：",
        "1. 重写今日三篇",
        "2. 只跑选题",
        "3. 主编评估",
        "4. 写大纲",
        "5. 写初稿",
        "6. 审稿",
        "7. 发布包",
        "8. 视觉排版",
        "9. 发C / 发E / 发S",
        "",
        "也可以带日期，例如：2026-05-14 发C",
    ]
    if prefix:
        lines.insert(0, prefix)
        lines.insert(1, "")
    return "\n".join(lines)


def get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise WeComRemoteError(f"Missing environment variable: {name}")
    return value


def get_optional_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
