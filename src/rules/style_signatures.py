"""Style-class detection for rule_engine guards.

Plan 02 (Wave 1) of phase 01-engine-guardrails-cohesion-audit.
"""

from __future__ import annotations

import re
from typing import Literal

from docx.text.paragraph import Paragraph

StyleClass = Literal["heading", "toc", "caption", "list", "body"]

# Regex constants — mirror rule_engine.LIST_STYLE_RE / HEADING_STYLE_RE so the guard
# uses the same vocabulary as the existing autofix paths.
LIST_STYLE_RE = re.compile(r"list|список|маркирован|нумерован", re.IGNORECASE)
HEADING_STYLE_RE = re.compile(r"heading|заголов", re.IGNORECASE)
TOC_STYLE_RE = re.compile(r"toc|содержание", re.IGNORECASE)
CAPTION_STYLE_RE = re.compile(r"caption|подпись", re.IGNORECASE)


def classify_style(paragraph: Paragraph) -> StyleClass:
    """Return the StyleClass for a paragraph by matching its style name.

    Check order is toc → heading → caption → list → body so that names like
    "TOC Heading" classify as "toc" (the more specific match), not "heading".
    Follows the rule_engine._paragraph_has_*_style try/except → "body" idiom.
    """
    try:
        if paragraph.style is None or paragraph.style.name is None:
            return "body"
        name = str(paragraph.style.name)
    except Exception:
        return "body"

    if TOC_STYLE_RE.search(name):
        return "toc"
    if HEADING_STYLE_RE.search(name):
        return "heading"
    if CAPTION_STYLE_RE.search(name):
        return "caption"
    if LIST_STYLE_RE.search(name):
        return "list"
    return "body"


def paragraph_has_list_style(paragraph: Paragraph) -> bool:
    """True if paragraph.style.name matches LIST_STYLE_RE; False on any error."""
    try:
        if paragraph.style is not None and paragraph.style.name is not None:
            return bool(LIST_STYLE_RE.search(str(paragraph.style.name)))
    except Exception:
        return False
    return False


def paragraph_has_heading_style(paragraph: Paragraph) -> bool:
    """True if paragraph.style.name matches HEADING_STYLE_RE; False on any error."""
    try:
        if paragraph.style is not None and paragraph.style.name is not None:
            return bool(HEADING_STYLE_RE.search(str(paragraph.style.name)))
    except Exception:
        return False
    return False


def _resolve_inherited_value(style, attr_getter):
    """Walk paragraph.style.base_style chain (D-03 Pass 2). Return the first
    non-None value yielded by attr_getter(current_style), or None if the chain
    ends without one. Pure python-docx; no lxml.
    """
    current = style
    while current is not None:
        try:
            val = attr_getter(current)
        except Exception:
            val = None
        if val is not None:
            return val
        try:
            current = getattr(current, "base_style", None)
        except Exception:
            current = None
    return None


def _extract_heading_format_signature(paragraph) -> dict:
    """Two-pass resolver (D-03/D-04): returns {field: {value, source}} for 18 fields.
    Called only when classify_style(paragraph) == "heading" (D-01 lazy guard).
    """
    # Lazy import of ALIGNMENT_MAP to avoid src/io <-> src/rules import cycle
    from src.io.block_extractor import ALIGNMENT_MAP

    fmt = paragraph.paragraph_format
    style = paragraph.style

    def _walk_pf(attr: str):
        return _resolve_inherited_value(style, lambda s: getattr(s.paragraph_format, attr, None))

    def _walk_font(attr: str):
        return _resolve_inherited_value(style, lambda s: getattr(s.font, attr, None))

    def _tagged(direct_val, inherited_getter):
        if direct_val is not None:
            return {"value": direct_val, "source": "direct"}
        try:
            inherited = inherited_getter()
        except Exception:
            inherited = None
        if inherited is not None:
            return {"value": inherited, "source": "inherited"}
        return {"value": None, "source": "unset"}

    # --- Pass 1: font fields (first run with non-None direct value) ---
    direct_font_name = direct_font_size = direct_bold = None
    direct_italic = direct_underline = direct_color = direct_caps = None

    for run in paragraph.runs:
        try:
            if run.text and run.text.strip():
                if direct_font_name is None and run.font.name is not None:
                    direct_font_name = run.font.name
                if direct_font_size is None and run.font.size is not None:
                    direct_font_size = round(run.font.size.pt, 3)  # Pitfall 5: EMU -> pt
                if direct_bold is None and run.bold is not None:
                    direct_bold = bool(run.bold)
                if direct_italic is None and run.italic is not None:
                    direct_italic = bool(run.italic)
                if direct_underline is None and run.font.underline is not None:
                    direct_underline = run.font.underline  # bool or WD_UNDERLINE -- keep as is
                # Pitfall 6: color.type=None means no direct color set
                if direct_color is None and run.font.color is not None and run.font.color.type is not None:
                    direct_color = str(run.font.color.rgb) if run.font.color.rgb else "auto"
                if direct_caps is None and run.font.all_caps is not None:
                    direct_caps = bool(run.font.all_caps)
        except Exception:
            # Per RESEARCH.md "Error handling": never raise from extractor
            continue

    # --- Pass 1: paragraph scalar fields ---
    try:
        direct_align_raw = paragraph.alignment
    except Exception:
        direct_align_raw = None
    direct_first_line = round(fmt.first_line_indent.cm, 3) if fmt.first_line_indent is not None else None  # Pitfall 4
    direct_left = round(fmt.left_indent.cm, 3) if fmt.left_indent is not None else None
    direct_right = round(fmt.right_indent.cm, 3) if fmt.right_indent is not None else None
    ls = fmt.line_spacing
    direct_ls = round(float(ls), 3) if isinstance(ls, (int, float)) else None  # Pitfall 8
    direct_sb = round(fmt.space_before.pt, 3) if fmt.space_before is not None else None
    direct_sa = round(fmt.space_after.pt, 3) if fmt.space_after is not None else None

    # --- Pass 1: flow flags ---
    direct_kwn = fmt.keep_with_next
    direct_klt = fmt.keep_together  # python-docx name; D-02 surfaces as keep_lines_together
    direct_pbb = fmt.page_break_before
    direct_wc = fmt.widow_control

    def _align_str(val):
        return ALIGNMENT_MAP.get(val) if val is not None else None

    def _font_size_inherited():
        v = _walk_font("size")
        return round(v.pt, 3) if v is not None else None

    def _first_line_inherited():
        v = _walk_pf("first_line_indent")
        return round(v.cm, 3) if v is not None else None

    def _left_inherited():
        v = _walk_pf("left_indent")
        return round(v.cm, 3) if v is not None else None

    def _right_inherited():
        v = _walk_pf("right_indent")
        return round(v.cm, 3) if v is not None else None

    def _ls_inherited():
        v = _walk_pf("line_spacing")
        return round(float(v), 3) if isinstance(v, (int, float)) else None

    def _sb_inherited():
        v = _walk_pf("space_before")
        return round(v.pt, 3) if v is not None else None

    def _sa_inherited():
        v = _walk_pf("space_after")
        return round(v.pt, 3) if v is not None else None

    return {
        "font_name":            _tagged(direct_font_name,  lambda: _walk_font("name")),
        "font_size":            _tagged(direct_font_size,  _font_size_inherited),
        "bold":                 _tagged(direct_bold,       lambda: _walk_font("bold")),
        "italic":               _tagged(direct_italic,     lambda: _walk_font("italic")),
        "underline":            _tagged(direct_underline,  lambda: _walk_font("underline")),
        "color":                _tagged(direct_color,      lambda: None),  # Pitfall 6: no style-level color path in typical docs
        "caps":                 _tagged(direct_caps,       lambda: _walk_font("all_caps")),
        "alignment":            _tagged(_align_str(direct_align_raw), lambda: _align_str(_walk_pf("alignment"))),
        "first_line_indent_cm": _tagged(direct_first_line, _first_line_inherited),
        "left_indent_cm":       _tagged(direct_left,       _left_inherited),
        "right_indent_cm":      _tagged(direct_right,      _right_inherited),
        "line_spacing":         _tagged(direct_ls,         _ls_inherited),
        "space_before_pt":      _tagged(direct_sb,         _sb_inherited),
        "space_after_pt":       _tagged(direct_sa,         _sa_inherited),
        "keep_with_next":       _tagged(direct_kwn,        lambda: _walk_pf("keep_with_next")),
        "keep_lines_together":  _tagged(direct_klt,        lambda: _walk_pf("keep_together")),
        "page_break_before":    _tagged(direct_pbb,        lambda: _walk_pf("page_break_before")),
        "widow_control":        _tagged(direct_wc,         lambda: _walk_pf("widow_control")),
    }
