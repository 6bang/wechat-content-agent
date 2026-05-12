from __future__ import annotations

import os
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from utils.llm import load_env


TEXT_EXTENSIONS = {".md", ".txt", ".csv", ".json", ".yaml", ".yml"}
ARCHIVE_EXTENSIONS = {".pptx", ".docx", ".xlsx"}
DEFAULT_MAX_FILES = 12
DEFAULT_FILE_CHARS = 2200
DEFAULT_TOTAL_CHARS = 14000

DEFAULT_REFERENCE_PATHS = [
    "01_课程总纲",
    "02_线下课课件",
    "05_客户案例",
    "06_销售素材",
    "07_公众号素材",
]

KEYWORD_BY_LAYER = {
    "C": ["打造流程化", "流程化组织", "老板", "管理", "目标"],
    "E": ["岗位流程", "运营流程", "作战参谋", "选品", "打品", "薪酬", "绩效"],
    "S": ["SOP", "岗位流程", "新品SOP", "流程", "SABC", "工具"],
}

CORE_KEYWORDS = [
    "如何来梳理岗位流程",
    "岗位流程",
    "打造流程化组织",
    "新品SOP",
    "作战参谋",
    "运营流程化",
    "目标",
    "绩效",
    "薪酬",
    "招聘",
    "训战",
]


def load_courseware_context(root_dir: Path, calendar_item: dict[str, Any] | None = None) -> dict[str, Any]:
    load_env()
    enabled = env_bool("ENABLE_COURSEWARE_CONTEXT", default=False)
    if not enabled:
        return {
            "enabled": False,
            "available": False,
            "root": "",
            "files": [],
            "summary": "",
            "message": "ENABLE_COURSEWARE_CONTEXT is not true.",
        }

    courseware_root = resolve_courseware_root(root_dir)
    if courseware_root is None:
        return {
            "enabled": True,
            "available": False,
            "root": "",
            "files": [],
            "summary": "",
            "message": "Courseware repository was not found.",
        }

    max_files = int(os.getenv("COURSEWARE_MAX_FILES", str(DEFAULT_MAX_FILES)) or DEFAULT_MAX_FILES)
    file_chars = int(os.getenv("COURSEWARE_FILE_CHARS", str(DEFAULT_FILE_CHARS)) or DEFAULT_FILE_CHARS)
    total_chars = int(os.getenv("COURSEWARE_TOTAL_CHARS", str(DEFAULT_TOTAL_CHARS)) or DEFAULT_TOTAL_CHARS)

    files: list[dict[str, str]] = []
    for path in collect_candidate_files(courseware_root, calendar_item)[: max_files * 3]:
        text = extract_text(path)
        if not text:
            continue
        rel_path = str(path.relative_to(courseware_root))
        files.append({"path": rel_path, "excerpt": text[:file_chars].strip()})
        if len(files) >= max_files:
            break

    summary = render_context_summary(files, total_chars)
    return {
        "enabled": True,
        "available": bool(files),
        "root": str(courseware_root),
        "files": files,
        "summary": summary,
        "message": "Courseware context loaded." if files else "No readable courseware files found.",
    }


def render_courseware_reference(context: dict[str, Any]) -> str:
    lines = [
        "# 课件库参考上下文",
        "",
        f"- 是否启用: {context.get('enabled')}",
        f"- 是否可用: {context.get('available')}",
        f"- 课件库路径: {context.get('root') or '未找到'}",
        f"- 说明: {context.get('message') or ''}",
        "",
    ]
    files = context.get("files") or []
    if not files:
        lines.append("本次运行没有读取到可用课件内容。")
        return "\n".join(lines)

    lines.append("## 已读取文件")
    for item in files:
        lines.extend(["", f"### {item.get('path')}", "", item.get("excerpt", "").strip()])
    return "\n".join(lines).strip()


def resolve_courseware_root(root_dir: Path) -> Path | None:
    explicit_path = os.getenv("COURSEWARE_PATH", "").strip()
    candidates = []
    if explicit_path:
        candidates.append(Path(explicit_path).expanduser())

    candidates.extend(
        [
            root_dir / "courseware" / "6bang-courseware",
            root_dir.parent / "6bang-courseware",
            Path.home() / "Documents" / "6bang-courseware",
        ]
    )

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve()
    return None


def collect_candidate_files(root: Path, calendar_item: dict[str, Any] | None = None) -> list[Path]:
    reference_paths = parse_reference_paths(os.getenv("COURSEWARE_REFERENCE_PATHS", ""))
    if not reference_paths:
        reference_paths = DEFAULT_REFERENCE_PATHS

    candidates: list[Path] = []
    for reference_path in reference_paths:
        path = root / reference_path
        if path.is_file() and is_readable_courseware_file(path):
            candidates.append(path)
        elif path.is_dir():
            candidates.extend(path.rglob("*"))

    readable = [path for path in candidates if is_readable_courseware_file(path)]
    return sorted(set(readable), key=lambda path: (-score_file(path, root, calendar_item), str(path)))


def parse_reference_paths(raw: str) -> list[str]:
    return [item.strip() for item in re.split(r"[\n,;]+", raw) if item.strip()]


def is_readable_courseware_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.name.startswith(".") or path.name.startswith("~$"):
        return False
    if any(part in {".git", "__MACOSX"} for part in path.parts):
        return False
    return path.suffix.lower() in TEXT_EXTENSIONS | ARCHIVE_EXTENSIONS


def score_file(path: Path, root: Path, calendar_item: dict[str, Any] | None = None) -> int:
    rel = str(path.relative_to(root))
    text = rel.lower()
    score = 0

    for keyword in CORE_KEYWORDS:
        if keyword.lower() in text:
            score += 20

    if calendar_item:
        code = str(calendar_item.get("code", ""))
        layer = code[:1]
        for keyword in KEYWORD_BY_LAYER.get(layer, []):
            if keyword.lower() in text:
                score += 16
        column = str(calendar_item.get("column", ""))
        for piece in re.split(r"[\s｜/、-]+", column):
            if piece and piece.lower() in text:
                score += 8

    if "课件" in rel:
        score += 4
    if path.suffix.lower() == ".pptx":
        score += 3
    if "v-2.1" in rel.lower() or "v2.1" in rel.lower():
        score += 5
    return score


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    try:
        if suffix in TEXT_EXTENSIONS:
            return normalize_text(path.read_text(encoding="utf-8", errors="ignore"))
        if suffix == ".pptx":
            return extract_pptx_text(path)
        if suffix == ".docx":
            return extract_docx_text(path)
        if suffix == ".xlsx":
            return extract_xlsx_text(path)
    except Exception as exc:
        return f"读取失败：{path.name}，错误：{exc}"
    return ""


def extract_pptx_text(path: Path) -> str:
    texts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        slide_names = natural_sort(
            name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
        for slide_name in slide_names:
            xml_text = archive.read(slide_name)
            slide_text = " ".join(extract_xml_text_nodes(xml_text))
            if slide_text.strip():
                texts.append(slide_text)
    return normalize_text("\n".join(texts))


def extract_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        if "word/document.xml" not in archive.namelist():
            return ""
        return normalize_text("\n".join(extract_xml_text_nodes(archive.read("word/document.xml"))))


def extract_xlsx_text(path: Path) -> str:
    texts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name == "xl/sharedStrings.xml" or (name.startswith("xl/worksheets/") and name.endswith(".xml")):
                texts.extend(extract_xml_text_nodes(archive.read(name)))
    return normalize_text("\n".join(texts))


def extract_xml_text_nodes(xml_bytes: bytes) -> list[str]:
    root = ElementTree.fromstring(xml_bytes)
    values = []
    for element in root.iter():
        if element.tag.endswith("}t") or element.tag == "t":
            text = element.text or ""
            if text.strip():
                values.append(text.strip())
    return values


def normalize_text(text: str) -> str:
    cleaned_lines = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        line = re.sub(r"\b[A-Fa-f0-9]{32,}\b", "", line).strip()
        if not line:
            continue
        if re.fullmatch(r"[A-Fa-f0-9]{32,}", line):
            continue
        if len(line) <= 2 and re.fullmatch(r"[\W_]+", line):
            continue
        if line:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def natural_sort(values: Any) -> list[str]:
    return sorted(values, key=lambda value: [int(piece) if piece.isdigit() else piece for piece in re.split(r"(\d+)", value)])


def render_context_summary(files: list[dict[str, str]], max_chars: int) -> str:
    if not files:
        return ""

    parts = [
        "以下内容来自六邦 GitHub 课件库。写作时优先参考这些课程框架、案例、工具和表达方式；可以转化为原创公众号表达，不要逐字复制课件原文。",
        "",
    ]
    for item in files:
        parts.extend([f"【课件文件】{item['path']}", item["excerpt"], ""])

    summary = "\n".join(parts).strip()
    return summary[:max_chars].strip()


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}
