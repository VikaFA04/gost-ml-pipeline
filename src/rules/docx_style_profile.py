from __future__ import annotations

from pathlib import Path
from typing import Any

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

DEFAULT_WRITER_STYLE_MAP = {
    "title_section": "Heading 1",
    "bibliography_title": "Heading 1",
    "appendix_title": "Heading 1",
    "title_subsection": "Heading 2",
    "figure_caption": "Normal",
    "table_caption": "Normal",
    "bibliography_item": "List Paragraph",
    "list_item": "List Paragraph",
    "body_text": "Normal",
}


def get_writer_config(profile: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(profile, dict):
        return {}
    writer_cfg = profile.get("document_rules", {}).get("writer", {})
    return writer_cfg if isinstance(writer_cfg, dict) else {}


def get_label_config(profile: dict[str, Any] | None, label: str) -> dict[str, Any]:
    if not isinstance(profile, dict):
        return {}
    labels = profile.get("labels", {})
    if not isinstance(labels, dict):
        return {}
    cfg = labels.get(label, {})
    return cfg if isinstance(cfg, dict) else {}


def get_label_style_profile(profile: dict[str, Any] | None, label: str) -> dict[str, Any] | None:
    cfg = get_label_config(profile, label)
    style_profile = cfg.get("style_profile")
    return style_profile if isinstance(style_profile, dict) else None


def get_default_font_name(profile: dict[str, Any] | None, default: str = "Times New Roman") -> str:
    if not isinstance(profile, dict):
        return default
    font_cfg = profile.get("document_rules", {}).get("default_font", {})
    if not isinstance(font_cfg, dict):
        return default
    font_name = font_cfg.get("font_name")
    return str(font_name) if font_name else default


def resolve_writer_style_name(profile: dict[str, Any] | None, label: str) -> str:
    writer_cfg = get_writer_config(profile)
    styles_cfg = writer_cfg.get("styles", {})
    if isinstance(styles_cfg, dict):
        style_cfg = styles_cfg.get(label)
        if isinstance(style_cfg, dict):
            style_name = style_cfg.get("style_name")
            if style_name:
                return str(style_name)

    label_cfg = get_label_config(profile, label)
    style_name = label_cfg.get("writer_style_name")
    if style_name:
        return str(style_name)

    return DEFAULT_WRITER_STYLE_MAP.get(label, "Normal")


def resolve_writer_template_path(profile: dict[str, Any] | None) -> Path | None:
    writer_cfg = get_writer_config(profile)
    template_path = writer_cfg.get("template_path") or writer_cfg.get("template_docx_path")
    if not template_path:
        return None
    path = Path(str(template_path)).expanduser()
    return path


def apply_style_profile_to_paragraph(
    paragraph,
    style_profile: dict[str, Any],
    default_font_name: str = "Times New Roman",
) -> None:
    fmt = paragraph.paragraph_format

    fmt.first_line_indent = Cm(float(style_profile.get("first_line_indent_cm", 0.0)))
    fmt.left_indent = Cm(float(style_profile.get("left_indent_cm", 0.0)))
    fmt.right_indent = Cm(0)
    fmt.line_spacing = float(style_profile.get("line_spacing", 1.5))
    fmt.space_before = Pt(float(style_profile.get("space_before_pt", 0.0)))
    fmt.space_after = Pt(float(style_profile.get("space_after_pt", 0.0)))

    alignment_map = {
        "LEFT": WD_ALIGN_PARAGRAPH.LEFT,
        "CENTER": WD_ALIGN_PARAGRAPH.CENTER,
        "RIGHT": WD_ALIGN_PARAGRAPH.RIGHT,
        "JUSTIFY": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "DISTRIBUTE": WD_ALIGN_PARAGRAPH.DISTRIBUTE,
    }
    paragraph.alignment = alignment_map.get(
        style_profile.get("alignment", "LEFT"),
        WD_ALIGN_PARAGRAPH.LEFT,
    )

    for run in paragraph.runs:
        if not run.text:
            continue
        run.font.name = default_font_name
        run.font.size = Pt(int(style_profile.get("font_size_pt", 14)))
        run.bold = bool(style_profile.get("bold", False))
