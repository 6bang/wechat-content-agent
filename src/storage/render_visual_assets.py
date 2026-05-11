from __future__ import annotations

import html
import re
from pathlib import Path

from models.content import VisualAsset, VisualLayoutPackage


LAYER_COLORS = {
    "C": ("#2F2A24", "#B88746", "#FFF8EF"),
    "E": ("#263445", "#D86C35", "#F5F7FA"),
    "S": ("#173F35", "#2D7DD2", "#F4FBF8"),
}


def save_visual_assets(output_dir: Path, visual_layout: VisualLayoutPackage) -> list[Path]:
    assets_dir = output_dir / "visual_assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []

    for index, asset in enumerate(visual_layout.visual_assets, start=1):
        filename = safe_svg_filename(asset.filename or f"visual_{index}.svg")
        path = assets_dir / filename
        path.write_text(render_svg(asset, visual_layout.selected_layer, index), encoding="utf-8")
        saved_paths.append(path)

    return saved_paths


def render_svg(asset: VisualAsset, layer: str, index: int) -> str:
    primary, accent, background = LAYER_COLORS.get(layer, ("#222222", "#2D7DD2", "#F7F7F7"))
    bullets = build_bullets(asset.prompt)
    title_rows, next_y = svg_text_lines(asset.title, x=84, y=160, css_class="title", max_chars=20, line_height=48, max_lines=2)
    purpose_rows, next_y = svg_text_lines(asset.purpose, x=84, y=next_y + 10, css_class="body", max_chars=32, line_height=34, max_lines=2)
    bullet_rows, next_y = svg_bullet_lines(bullets[:5], x=84, y=next_y + 28)
    caption_rows, next_y = svg_text_lines(asset.caption, x=84, y=548, css_class="caption", max_chars=42, line_height=28, max_lines=2)
    notes_rows, _ = svg_text_lines(asset.notes, x=84, y=next_y + 8, css_class="caption", max_chars=42, line_height=28, max_lines=1)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675" role="img" aria-label="{escape(asset.alt_text)}">
  <defs>
    <style>
      .bg {{ fill: {background}; }}
      .title {{ fill: {primary}; font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 42px; font-weight: 700; }}
      .eyebrow {{ fill: {accent}; font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 22px; font-weight: 700; }}
      .body {{ fill: {primary}; font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 25px; }}
      .bullet {{ fill: {primary}; font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 23px; }}
      .caption {{ fill: #5C6470; font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 20px; }}
      .card {{ fill: #FFFFFF; stroke: #E2E6EA; stroke-width: 2; }}
      .line {{ stroke: {accent}; stroke-width: 6; stroke-linecap: round; fill: none; }}
      .node {{ fill: {accent}; opacity: 0.95; }}
    </style>
  </defs>
  <rect class="bg" width="1200" height="675"/>
  <rect class="card" x="48" y="46" width="1104" height="583" rx="18"/>
  <text x="84" y="105" class="eyebrow">公众号视觉排版｜{escape(asset.asset_type)}｜{layer}层｜{index:02d}</text>
  {title_rows}
  {purpose_rows}
  {render_visual_motif(asset.asset_type, primary, accent)}
  {bullet_rows}
  {caption_rows}
  {notes_rows}
</svg>
"""


def render_visual_motif(asset_type: str, primary: str, accent: str) -> str:
    if "看板" in asset_type or "多维表" in asset_type:
        return f"""
  <rect x="770" y="230" width="280" height="210" rx="12" fill="#FFFFFF" stroke="#D9DEE5" stroke-width="2"/>
  <line x1="790" y1="285" x2="1030" y2="285" stroke="{accent}" stroke-width="4"/>
  <line x1="790" y1="340" x2="1030" y2="340" stroke="#D9DEE5" stroke-width="3"/>
  <line x1="790" y1="395" x2="1030" y2="395" stroke="#D9DEE5" stroke-width="3"/>
  <circle cx="825" cy="255" r="10" fill="{accent}"/>
  <circle cx="920" cy="255" r="10" fill="{primary}"/>
  <circle cx="1015" cy="255" r="10" fill="#94A3B8"/>
"""
    if "流程" in asset_type or "问题" in asset_type:
        return f"""
  <path class="line" d="M775 338 H1030"/>
  <circle class="node" cx="775" cy="338" r="28"/>
  <circle class="node" cx="860" cy="338" r="28"/>
  <circle class="node" cx="945" cy="338" r="28"/>
  <circle class="node" cx="1030" cy="338" r="28"/>
"""
    if "清单" in asset_type or "资料" in asset_type:
        return f"""
  <rect x="790" y="238" width="240" height="245" rx="16" fill="#FFFFFF" stroke="#D9DEE5" stroke-width="2"/>
  <path d="M835 302 l18 18 l42 -50" stroke="{accent}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <path d="M835 380 l18 18 l42 -50" stroke="{accent}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <rect x="910" y="278" width="76" height="76" fill="{primary}" opacity="0.12"/>
  <rect x="910" y="374" width="76" height="76" fill="{primary}" opacity="0.12"/>
"""
    return f"""
  <rect x="790" y="250" width="250" height="170" rx="16" fill="{accent}" opacity="0.12"/>
  <path d="M820 390 C880 275 955 440 1030 300" stroke="{accent}" stroke-width="8" fill="none" stroke-linecap="round"/>
  <circle cx="820" cy="390" r="13" fill="{primary}"/>
  <circle cx="1030" cy="300" r="13" fill="{primary}"/>
"""


def build_bullets(prompt: str) -> list[str]:
    text = re.sub(r"[，。；;]", "\n", prompt)
    items = [item.strip() for item in text.splitlines() if item.strip()]
    return items or ["突出业务问题", "展示流程方法", "保留品牌专业感"]


def safe_svg_filename(filename: str) -> str:
    stem = filename.strip() or "visual.svg"
    if not stem.endswith(".svg"):
        stem = f"{stem}.svg"
    return re.sub(r"[^A-Za-z0-9_.-]", "_", stem)


def escape(value: str) -> str:
    return html.escape(value.strip(), quote=True)


def wrap_text(text: str, max_chars: int, max_lines: int) -> list[str]:
    compact = " ".join(text.strip().split())
    if not compact:
        return []

    lines = [compact[index : index + max_chars] for index in range(0, len(compact), max_chars)]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip("，。；、 ") + "..."
    return lines


def svg_text_lines(
    text: str,
    x: int,
    y: int,
    css_class: str,
    max_chars: int,
    line_height: int,
    max_lines: int,
) -> tuple[str, int]:
    rows = []
    lines = wrap_text(text, max_chars=max_chars, max_lines=max_lines)
    for index, line in enumerate(lines):
        rows.append(f'<text x="{x}" y="{y + index * line_height}" class="{css_class}">{escape(line)}</text>')
    next_y = y + max(len(lines), 1) * line_height
    return "\n  ".join(rows), next_y


def svg_bullet_lines(bullets: list[str], x: int, y: int) -> tuple[str, int]:
    rows: list[str] = []
    current_y = y
    for bullet in bullets:
        lines = wrap_text(f"- {bullet}", max_chars=30, max_lines=2)
        for line in lines:
            rows.append(f'<text x="{x}" y="{current_y}" class="bullet">{escape(line)}</text>')
            current_y += 34
        current_y += 8
    return "\n  ".join(rows), current_y
