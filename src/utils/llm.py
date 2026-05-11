from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
_ENV_LOADED = False


def load_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    if load_dotenv is not None:
        load_dotenv(dotenv_path=ENV_PATH, override=False)
    else:
        load_env_file(ENV_PATH)
    _ENV_LOADED = True


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def str_to_bool(value: str | None, default: bool = False) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def use_mock_mode() -> bool:
    load_env()
    return str_to_bool(os.getenv("USE_MOCK"), default=True)


def get_model_name(default: str = "gpt-4.1-mini") -> str:
    load_env()
    return os.getenv("OPENAI_MODEL") or os.getenv("MODEL") or default


def get_temperature(default: float = 0.7) -> float:
    load_env()
    raw_value = os.getenv("OPENAI_TEMPERATURE")
    if not raw_value:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


def mock_llm(system_prompt: str, user_prompt: str) -> str:
    model = get_model_name()
    prompt_preview = " ".join(user_prompt.strip().split())[:120]
    return f"[mock:{model}] {prompt_preview}"


def call_llm(system_prompt: str, user_prompt: str) -> str:
    try:
        if use_mock_mode():
            return mock_llm(system_prompt, user_prompt)

        load_env()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required when USE_MOCK=false.")

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("openai package is required. Please run: pip install -r requirements.txt") from exc

        base_url = os.getenv("OPENAI_BASE_URL") or None
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        client = OpenAI(**client_kwargs)
        if hasattr(client, "responses"):
            response = client.responses.create(
                model=get_model_name(),
                instructions=system_prompt,
                input=user_prompt,
            )
            return extract_response_text(response)

        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=get_temperature(),
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        print(f"LLM call failed: {exc}")
        raise


def extract_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    output_items = getattr(response, "output", None) or []
    text_parts: list[str] = []
    for item in output_items:
        content_items = get_value(item, "content") or []
        for content in content_items:
            text = get_value(content, "text")
            if text:
                text_parts.append(str(text))
    return "\n".join(text_parts)


def get_value(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)
