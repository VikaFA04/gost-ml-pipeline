from __future__ import annotations

import re
from typing import Any

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph

ALIGNMENT_MAP = {
    "LEFT": WD_ALIGN_PARAGRAPH.LEFT,
    "CENTER": WD_ALIGN_PARAGRAPH.CENTER,
    "RIGHT": WD_ALIGN_PARAGRAPH.RIGHT,
    "JUSTIFY": WD_ALIGN_PARAGRAPH.JUSTIFY,
    "DISTRIBUTE": WD_ALIGN_PARAGRAPH.DISTRIBUTE,
}

LIST_STYLE_RE = re.compile(r"list|список|маркирован|нумерован", re.IGNORECASE)
HEADING_STYLE_RE = re.compile(r"heading|заголов", re.IGNORECASE)
NUMBERED_MARKER_RE = re.compile(r"^\s*(?:\d+[\.\)]|[A-Za-zА-Яа-я][\.\)])\s+")
BULLET_MARKER_RE = re.compile(r"^\s*[-—–•●■◦]\s+")
HIGH_CONFIDENCE_THRESHOLD = 0.9
MAX_FALLBACK_LIST_WORDS = 40
MAX_FALLBACK_LIST_CHARS = 300
BODY_TEXT_REVIEW_ONLY_PARAMETERS = {"alignment", "first_line_indent_cm", "left_indent_cm"}
LIST_ITEM_REVIEW_ONLY_PARAMETERS = {"alignment", "line_spacing"}
ACCEPTED_LIST_LAYOUTS = {
    (2.25, -1.0),
    (2.5, -1.0),
}


def normalize_alignment(value) -> str | None:
    if value is None:
        return None
    mapping = {
        WD_ALIGN_PARAGRAPH.LEFT: "LEFT",
        WD_ALIGN_PARAGRAPH.CENTER: "CENTER",
        WD_ALIGN_PARAGRAPH.RIGHT: "RIGHT",
        WD_ALIGN_PARAGRAPH.JUSTIFY: "JUSTIFY",
        WD_ALIGN_PARAGRAPH.DISTRIBUTE: "DISTRIBUTE",
        WD_ALIGN_PARAGRAPH.JUSTIFY_MED: "JUSTIFY",
        WD_ALIGN_PARAGRAPH.JUSTIFY_HI: "JUSTIFY",
        WD_ALIGN_PARAGRAPH.JUSTIFY_LOW: "JUSTIFY",
        WD_ALIGN_PARAGRAPH.THAI_JUSTIFY: "JUSTIFY",
    }
    return mapping.get(value, str(value))


def get_first_text_run_style(paragraph: Paragraph) -> dict[str, Any]:
    for run in paragraph.runs:
        if run.text and run.text.strip():
            font_size_pt = None
            try:
                if run.font.size is not None:
                    font_size_pt = round(run.font.size.pt, 3)
            except Exception:
                font_size_pt = None
            return {
                "font_size_pt": font_size_pt,
                "bold": bool(run.bold) if run.bold is not None else None,
            }
    return {"font_size_pt": None, "bold": None}


def get_current_paragraph_profile(paragraph: Paragraph) -> dict[str, Any]:
    fmt = paragraph.paragraph_format
    line_spacing = fmt.line_spacing
    line_spacing_value = None
    if isinstance(line_spacing, (int, float)):
        line_spacing_value = round(float(line_spacing), 3)
    run_style = get_first_text_run_style(paragraph)
    return {
        "alignment": normalize_alignment(paragraph.alignment),
        "first_line_indent_cm": round(fmt.first_line_indent.cm, 3) if fmt.first_line_indent is not None else None,
        "left_indent_cm": round(fmt.left_indent.cm, 3) if fmt.left_indent is not None else None,
        "line_spacing": line_spacing_value,
        "space_before_pt": round(fmt.space_before.pt, 3) if fmt.space_before is not None else None,
        "space_after_pt": round(fmt.space_after.pt, 3) if fmt.space_after is not None else None,
        "font_size_pt": run_style["font_size_pt"],
        "bold": run_style["bold"],
    }


def resolve_list_level(row_data: dict[str, Any]) -> int | None:
    raw_level = row_data.get("list_level")
    if raw_level in (None, ""):
        return None
    try:
        return max(0, min(int(raw_level), 1))
    except Exception:
        return None


def get_current_list_profile(paragraph: Paragraph) -> dict[str, float | None]:
    fmt = paragraph.paragraph_format
    tab_stop_cm = None
    try:
        tab_stops = list(fmt.tab_stops)
        if tab_stops:
            tab_stop_cm = round(tab_stops[0].position.cm, 3)
    except Exception:
        tab_stop_cm = None

    return {
        "left_indent_cm": round(fmt.left_indent.cm, 3) if fmt.left_indent is not None else None,
        "first_line_indent_cm": round(fmt.first_line_indent.cm, 3) if fmt.first_line_indent is not None else None,
        "tab_stop_cm": tab_stop_cm,
    }


def list_layout_is_inherited(paragraph: Paragraph, current_list: dict[str, float | None]) -> bool:
    return (
        _paragraph_has_list_style(paragraph)
        and current_list.get("left_indent_cm") is None
        and current_list.get("first_line_indent_cm") is None
    )


def list_layout_is_accepted(current_list: dict[str, float | None]) -> bool:
    left_indent = current_list.get("left_indent_cm")
    first_line_indent = current_list.get("first_line_indent_cm")
    if left_indent is None or first_line_indent is None:
        return False
    return (round(left_indent, 2), round(first_line_indent, 2)) in ACCEPTED_LIST_LAYOUTS


def clear_tab_stops(paragraph: Paragraph) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    tabs = p_pr.find(qn("w:tabs"))
    if tabs is not None:
        p_pr.remove(tabs)


def apply_list_format(paragraph: Paragraph, level_config: dict[str, Any]) -> list[str]:
    fmt = paragraph.paragraph_format
    clear_tab_stops(paragraph)
    fmt.left_indent = Cm(float(level_config["left_indent_cm"]))
    fmt.first_line_indent = Cm(float(level_config["first_line_indent_cm"]))
    fmt.tab_stops.add_tab_stop(Cm(float(level_config["tab_stop_cm"])))
    return ["left_indent_cm", "first_line_indent_cm", "tab_stop_cm"]


def compare_scalar(current_value: Any, expected_value: Any) -> bool:
    if isinstance(expected_value, float):
        if current_value is None:
            return False
        return abs(float(current_value) - expected_value) <= 0.05
    return current_value == expected_value


def _format_inherited_review(rule: dict[str, Any], parameter: str) -> str:
    return f"{rule['id']}: current {parameter} is inherited or unavailable"


def apply_scalar_fix(paragraph: Paragraph, parameter: str, expected_value: Any, default_font_name: str) -> list[str]:
    fmt = paragraph.paragraph_format

    if parameter == "alignment":
        paragraph.alignment = ALIGNMENT_MAP[str(expected_value)]
    elif parameter == "first_line_indent_cm":
        fmt.first_line_indent = Cm(float(expected_value))
    elif parameter == "left_indent_cm":
        fmt.left_indent = Cm(float(expected_value))
    elif parameter == "line_spacing":
        fmt.line_spacing = float(expected_value)
    elif parameter == "space_before_pt":
        fmt.space_before = Pt(float(expected_value))
    elif parameter == "space_after_pt":
        fmt.space_after = Pt(float(expected_value))
    elif parameter == "font_size_pt":
        for run in paragraph.runs:
            if run.text:
                run.font.name = default_font_name
                run.font.size = Pt(float(expected_value))
    elif parameter == "bold":
        for run in paragraph.runs:
            if run.text:
                run.font.name = default_font_name
                run.bold = bool(expected_value)
    else:
        raise ValueError(f"Unsupported rule parameter: {parameter}")

    return [parameter]


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _paragraph_has_numbering(paragraph: Paragraph) -> bool:
    try:
        p_pr = paragraph._p.pPr
        return bool(p_pr is not None and p_pr.numPr is not None)
    except Exception:
        return False


def _paragraph_has_list_marker(text: str) -> bool:
    return bool(BULLET_MARKER_RE.match(text) or NUMBERED_MARKER_RE.match(text))


def _paragraph_has_list_style(paragraph: Paragraph) -> bool:
    try:
        if paragraph.style is not None and paragraph.style.name is not None:
            return bool(LIST_STYLE_RE.search(str(paragraph.style.name)))
    except Exception:
        return False
    return False


def _paragraph_has_heading_style(paragraph: Paragraph) -> bool:
    try:
        if paragraph.style is not None and paragraph.style.name is not None:
            return bool(HEADING_STYLE_RE.search(str(paragraph.style.name)))
    except Exception:
        return False
    return False


def _is_long_plain_paragraph(text: str) -> bool:
    return len(text) >= MAX_FALLBACK_LIST_CHARS or len(text.split()) >= MAX_FALLBACK_LIST_WORDS


def assess_list_auto_fix_safety(paragraph: Paragraph, row_data: dict[str, Any]) -> dict[str, Any]:
    text = str(row_data.get("text", "") or paragraph.text or "").strip()
    confidence_score = _safe_float(row_data.get("confidence_score"))
    low_confidence = bool(row_data.get("low_confidence", False))
    list_type = row_data.get("list_type")
    list_level = resolve_list_level(row_data)
    has_numbering = _paragraph_has_numbering(paragraph)
    has_marker = _paragraph_has_list_marker(text)
    has_list_style = _paragraph_has_list_style(paragraph)
    long_plain_paragraph = _is_long_plain_paragraph(text)

    unsafe_reasons: list[str] = []
    if low_confidence or confidence_score is None or confidence_score < HIGH_CONFIDENCE_THRESHOLD:
        unsafe_reasons.append("list classification confidence is too low for auto-fix")
    if not list_type:
        unsafe_reasons.append("list_type is missing")
    if list_level is None:
        unsafe_reasons.append("list_level is missing")

    structurally_consistent = False
    if has_numbering:
        structurally_consistent = True
    elif has_list_style and list_level is not None and not long_plain_paragraph:
        structurally_consistent = True
    elif has_marker and not long_plain_paragraph:
        structurally_consistent = True
        unsafe_reasons.append("paragraph uses only a visible list marker without Word numbering or list style")
    else:
        unsafe_reasons.append("paragraph is not structurally consistent with a real list")

    if long_plain_paragraph and not has_numbering:
        unsafe_reasons.append("block looks like a long ordinary paragraph")

    return {
        "safe_to_autofix": not unsafe_reasons,
        "manual_review_required": bool(unsafe_reasons),
        "unsafe_reasons": unsafe_reasons,
        "list_type": list_type,
        "list_level": list_level,
        "structurally_consistent": structurally_consistent,
    }


def is_list_like_paragraph(paragraph: Paragraph, row_data: dict[str, Any]) -> bool:
    text = str(row_data.get("text", "") or paragraph.text or "").strip()
    if _paragraph_has_numbering(paragraph) or _paragraph_has_list_style(paragraph):
        return True
    return _paragraph_has_list_marker(text) and not _is_long_plain_paragraph(text)


def is_review_only_scalar_fix(label: str, parameter: str) -> bool:
    return (
        (label == "body_text" and parameter in BODY_TEXT_REVIEW_ONLY_PARAMETERS)
        or (label == "list_item" and parameter in LIST_ITEM_REVIEW_ONLY_PARAMETERS)
    )


def apply_rules_to_paragraph(
    paragraph: Paragraph,
    label: str,
    row_data: dict[str, Any],
    rules: list[dict[str, Any]],
    apply_safe: bool,
    default_font_name: str,
) -> dict[str, Any] | None:
    applicable_rules = [rule for rule in rules if label in rule["applicable_labels"]]
    if not applicable_rules:
        return None

    current_profile = get_current_paragraph_profile(paragraph)
    violated_rules: list[str] = []
    applied_fixes: list[str] = []
    suggested_fixes: list[str] = []
    explanations: list[str] = []
    blocked_unsafe_autofix = False
    manual_review_required = False
    unsafe_auto_fix_reason = ""
    list_assessment = assess_list_auto_fix_safety(paragraph, row_data) if label == "list_item" else None
    body_label_on_list_like_paragraph = label == "body_text" and is_list_like_paragraph(paragraph, row_data)

    for rule in applicable_rules:
        parameter = str(rule["parameter"])
        if label == "list_item" and parameter == "bold":
            continue

        if parameter == "list_format":
            if list_assessment is None:
                continue
            level = list_assessment["list_level"]
            if level is None:
                violated_rules.append(rule["id"])
                manual_review_required = True
                explanations.append(f"{rule['id']}: missing list level for safe formatting")
                continue
            expected_value = rule["expected_value"]["levels"].get(str(level), rule["expected_value"]["levels"]["0"])
            current_list = get_current_list_profile(paragraph)
            if list_layout_is_inherited(paragraph, current_list) or list_layout_is_accepted(current_list):
                continue
            if current_list.get("left_indent_cm") is None or current_list.get("first_line_indent_cm") is None:
                violated_rules.append(rule["id"])
                suggested_fixes.extend(["left_indent_cm", "first_line_indent_cm"])
                explanations.append(f"{rule['id']}: list layout is inherited or incomplete")
                manual_review_required = True
                if apply_safe and not list_assessment["safe_to_autofix"]:
                    blocked_unsafe_autofix = True
                    unsafe_auto_fix_reason = "; ".join(list_assessment["unsafe_reasons"])
                continue
            violated = [
                key
                for key, value in expected_value.items()
                if not (key == "tab_stop_cm" and current_list.get(key) is None)
                and not compare_scalar(current_list.get(key), float(value))
            ]
            if not violated:
                continue
            violated_rules.append(rule["id"])
            suggested_fixes.extend(violated)
            explanations.append(f"{rule['id']}: incorrect list layout for level {level}")
            if apply_safe and rule["autocorrect"] and rule["action"] == "fix" and list_assessment["safe_to_autofix"]:
                applied_fixes.extend(apply_list_format(paragraph, expected_value))
            elif apply_safe and violated:
                blocked_unsafe_autofix = True
                manual_review_required = True
                unsafe_auto_fix_reason = "; ".join(list_assessment["unsafe_reasons"])
            elif violated:
                manual_review_required = True
            continue

        current_value = current_profile.get(parameter)
        if parameter == "alignment":
            current_value = normalize_alignment(paragraph.alignment)
        if current_value is None:
            if label == "list_item":
                continue
            violated_rules.append(rule["id"])
            suggested_fixes.append(parameter)
            explanations.append(_format_inherited_review(rule, parameter))
            manual_review_required = True
            continue
        if not compare_scalar(current_value, rule["expected_value"]):
            violated_rules.append(rule["id"])
            suggested_fixes.append(parameter)
            explanations.append(f"{rule['id']}: expected {parameter}={rule['expected_value']}")
            if body_label_on_list_like_paragraph:
                blocked_unsafe_autofix = True
                manual_review_required = True
                unsafe_auto_fix_reason = "paragraph looks like a list but was classified as body_text"
                continue
            if is_review_only_scalar_fix(label, parameter):
                manual_review_required = True
                continue
            if label in {"title_section", "title_subsection"} and _paragraph_has_heading_style(paragraph):
                manual_review_required = True
                continue
            if (
                apply_safe
                and rule["autocorrect"]
                and rule["action"] == "fix"
                and (label != "list_item" or (list_assessment and list_assessment["safe_to_autofix"]))
            ):
                applied_fixes.extend(
                    apply_scalar_fix(
                        paragraph=paragraph,
                        parameter=parameter,
                        expected_value=rule["expected_value"],
                        default_font_name=default_font_name,
                    )
                )
                current_profile = get_current_paragraph_profile(paragraph)
            elif label == "list_item" and apply_safe:
                blocked_unsafe_autofix = True
                manual_review_required = True
                if list_assessment is not None:
                    unsafe_auto_fix_reason = "; ".join(list_assessment["unsafe_reasons"])

    status = "no_change"
    if violated_rules and not applied_fixes:
        status = "review"
    if applied_fixes:
        status = "changed"

    if label == "list_item" and list_assessment is not None and list_assessment["manual_review_required"] and status != "changed":
        manual_review_required = True
        if not unsafe_auto_fix_reason:
            unsafe_auto_fix_reason = "; ".join(list_assessment["unsafe_reasons"])

    return {
        "status": status,
        "violated_rules": violated_rules,
        "applied_fixes": sorted(set(applied_fixes)),
        "suggested_fixes": sorted(set(suggested_fixes)),
        "suggested_rule_ids": sorted(set(violated_rules)),
        "manual_review_required": manual_review_required,
        "blocked_unsafe_autofix": blocked_unsafe_autofix,
        "unsafe_auto_fix_reason": unsafe_auto_fix_reason,
        "explanation": "; ".join(explanations) if explanations else f"{label}: no rule violations",
    }
