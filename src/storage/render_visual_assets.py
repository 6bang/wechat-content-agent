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
        path.write_text(render_svg(asset, visual_layout, index), encoding="utf-8")
        saved_paths.append(path)

    return saved_paths


def render_svg(asset: VisualAsset, visual_layout: VisualLayoutPackage, index: int) -> str:
    layer = visual_layout.selected_layer
    if "封面" in asset.asset_type or asset.filename == "cover.svg":
        return render_cover_svg(asset, visual_layout, layer)

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


def render_cover_svg(asset: VisualAsset, visual_layout: VisualLayoutPackage, layer: str) -> str:
    primary, accent, background = LAYER_COLORS.get(layer, ("#222222", "#2D7DD2", "#F7F7F7"))
    title = visual_layout.title.strip(" 《》")
    title_rows = svg_cover_title_lines(title, x=68, y=300)
    subtitle = cover_subtitle(title, layer)
    subtitle_rows, _ = svg_text_lines(subtitle, x=72, y=540, css_class="cover_subtitle", max_chars=18, line_height=38, max_lines=2)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="900" viewBox="0 0 900 900" role="img" aria-label="{escape(title)}封面图">
  <defs>
    <linearGradient id="paper" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{background}"/>
      <stop offset="1" stop-color="#FFFFFF"/>
    </linearGradient>
    <style>
      .bg {{ fill: url(#paper); }}
      .cover_title {{ fill: {primary}; font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 74px; font-weight: 800; letter-spacing: 0; }}
      .cover_subtitle {{ fill: #5C6470; font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 31px; font-weight: 500; letter-spacing: 0; }}
      .eyebrow {{ fill: {accent}; font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 25px; font-weight: 800; letter-spacing: 0; }}
      .brand {{ fill: {primary}; font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 28px; font-weight: 800; letter-spacing: 0; }}
      .label {{ fill: #FFFFFF; font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 22px; font-weight: 800; letter-spacing: 0; }}
      .small {{ fill: #5C6470; font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; font-size: 22px; letter-spacing: 0; }}
    </style>
  </defs>
  <rect class="bg" width="900" height="900"/>
  <rect x="42" y="42" width="816" height="816" rx="42" fill="#FFFFFF" opacity="0.88"/>
  <rect x="68" y="82" width="180" height="48" rx="24" fill="{accent}"/>
  <text x="94" y="114" class="label">六邦电商</text>
  <text x="68" y="174" class="eyebrow">给电商老板的流程化组织课</text>
  {title_rows}
  {subtitle_rows}
  <text x="72" y="820" class="brand">不是老板更忙，而是系统更强</text>
  <g transform="translate(70 650)">
    <rect x="0" y="0" width="760" height="145" rx="28" fill="{primary}" opacity="0.06"/>
    <rect x="36" y="42" width="140" height="58" rx="18" fill="#FFFFFF" stroke="#D9DEE5" stroke-width="2"/>
    <rect x="226" y="42" width="140" height="58" rx="18" fill="#FFFFFF" stroke="#D9DEE5" stroke-width="2"/>
    <rect x="416" y="42" width="140" height="58" rx="18" fill="#FFFFFF" stroke="#D9DEE5" stroke-width="2"/>
    <rect x="606" y="42" width="118" height="58" rx="18" fill="#FFFFFF" stroke="#D9DEE5" stroke-width="2"/>
    <text x="69" y="78" class="small">流程</text>
    <text x="259" y="78" class="small">标准</text>
    <text x="449" y="78" class="small">复盘</text>
    <text x="631" y="78" class="small">复制</text>
    <path d="M176 71 H226 M366 71 H416 M556 71 H606" stroke="{accent}" stroke-width="7" stroke-linecap="round"/>
  </g>
</svg>
"""


def svg_cover_title_lines(title: str, x: int, y: int) -> str:
    normalized = title.replace("，", ",")
    if "老板越忙" in normalized and "公司越乱" in normalized:
        lines = ["为什么老板越忙", "公司越乱？"]
    elif "," in normalized:
        lines = [part.strip(" ?？") for part in normalized.split(",", 1)]
    else:
        lines = wrap_text(title, max_chars=8, max_lines=3)
    rows = [f'<text x="{x}" y="{y + index * 86}" class="cover_title">{escape(line)}</text>' for index, line in enumerate(lines[:3])]
    return "\n  ".join(rows)


def cover_subtitle(title: str, layer: str) -> str:
    if "老板越忙" in title:
        return "公司越大越不能靠老板救火"
    if "招运营" in title:
        return "别再用招聘填系统的坑"
    if "岗位流程" in title:
        return "先把岗位动作拆清楚，再谈执行力"
    if layer == "S":
        return "SOP不是文件，而是团队稳定产出的系统"
    if layer == "E":
        return "电商团队管理，先抓真正的卡点"
    return "老板要从盯人，走向看系统"


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
