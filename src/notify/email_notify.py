from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from utils.llm import load_env


def is_email_enabled() -> bool:
    load_env()
    return os.getenv("ENABLE_EMAIL", "").strip().lower() == "true"


def send_email_backup(subject: str, body: str, attachments: list[Path]) -> bool:
    if not is_email_enabled():
        print("Email backup skipped: ENABLE_EMAIL is not true.")
        return False

    load_env()
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587") or "587")
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    email_to = os.getenv("EMAIL_TO", "").strip()

    if not all([smtp_host, smtp_user, smtp_password, email_to]):
        print("Email backup skipped: SMTP settings are incomplete.")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_user
    message["To"] = email_to
    message.set_content(body)

    for attachment in attachments:
        if not attachment.exists():
            print(f"Email attachment skipped: {attachment} does not exist.")
            continue
        message.add_attachment(
            attachment.read_bytes(),
            maintype="text",
            subtype="markdown",
            filename=attachment.name,
        )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(message)
    except Exception as exc:  # noqa: BLE001
        print(f"Email backup failed: {exc}")
        return False

    print("Email backup sent.")
    return True
