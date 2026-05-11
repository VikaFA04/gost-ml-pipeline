from __future__ import annotations

import re
from typing import Any

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
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
BIBLIOGRAPHY_SUBHEADING_RE = re.compile(r"^(?:\d+\s*)?(теоретическая\s+часть|практическая\s+часть)$", re.IGNORECASE)
NUMBERED_MARKER_RE = re.compile(r"^\s*(?:\d+[\.\)]|[A-Za-zА-Яа-я][\.\)])\s+")
BULLET_MARKER_RE = re.compile(r"^\s*[-—–•●■◦]\s+")
HIGH_CONFIDENCE_THRESHOLD = 0.9
MAX_FALLBACK_LIST_WORDS = 40
MAX_FALLBACK_LIST_CHARS = 300
BODY_TEXT_REVIEW_ONLY_PARAMETERS = {
    "alignment",
    "first_line_indent_cm",
    "left_indent_cm",
    "line_spacing",
}
LIST_ITEM_REVIEW_ONLY_PARAMETERS = {"alignment", "line_spacing"}
ACCEPTED_LIST_LAYOUTS = {
    (2.25, -1.0),
    (2.5, -1.0),
}
_BIBLIOGRAPHY_NUM_IDS: dict[tuple[int, int | None], int] = {}


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


def _num_id_exists(paragraph: Paragraph, num_id: str | int | None) -> bool:
    if num_id is None:
        return False
    numbering_root = paragraph.part.numbering_part.element
    expected = str(num_id)
    return any(num.get(qn("w:numId")) == expected for num in numbering_root.findall(qn("w:num")))


def paragraph_numbering_reference_is_valid(paragraph: Paragraph) -> bool:
    try:
        num_pr = paragraph._p.pPr.numPr if paragraph._p.pPr is not None else None
        if num_pr is None or num_pr.numId is None:
            return False
        return _num_id_exists(paragraph, num_pr.numId.val)
    except Exception:
        return False


def _find_abstract_num_id_by_format(numbering_root, num_format: str) -> str:
    for abstract_num in numbering_root.findall(qn("w:abstractNum")):
        level = abstract_num.find(qn("w:lvl"))
        if level is None:
            continue
        num_fmt = level.find(qn("w:numFmt"))
        if num_fmt is not None and num_fmt.get(qn("w:val")) == num_format:
            return str(abstract_num.get(qn("w:abstractNumId")))
    return _find_decimal_abstract_num_id(numbering_root)


def _create_num_for_abstract(numbering_root, abstract_num_id: str) -> int:
    num_id = _next_num_id(numbering_root)
    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))
    abstract_ref = OxmlElement("w:abstractNumId")
    abstract_ref.set(qn("w:val"), abstract_num_id)
    num.append(abstract_ref)
    numbering_root.append(num)
    return num_id


def apply_list_numbering(paragraph: Paragraph, list_type: Any) -> list[str]:
    if paragraph_numbering_reference_is_valid(paragraph):
        return []
    numbering_root = paragraph.part.numbering_part.element
    num_format = "decimal" if str(list_type) == "numbered" else "bullet"
    abstract_num_id = _find_abstract_num_id_by_format(numbering_root, num_format)
    num_id = _create_num_for_abstract(numbering_root, abstract_num_id)

    p_pr = paragraph._p.get_or_add_pPr()
    num_pr = p_pr.find(qn("w:numPr"))
    if num_pr is None:
        num_pr = OxmlElement("w:numPr")
        p_pr.append(num_pr)
    ilvl = num_pr.find(qn("w:ilvl"))
    if ilvl is None:
        ilvl = OxmlElement("w:ilvl")
        num_pr.append(ilvl)
    ilvl.set(qn("w:val"), "0")
    num_id_element = num_pr.find(qn("w:numId"))
    if num_id_element is None:
        num_id_element = OxmlElement("w:numId")
        num_pr.append(num_id_element)
    num_id_element.set(qn("w:val"), str(num_id))
    return ["numbering"]


def apply_list_format(
    paragraph: Paragraph,
    level_config: dict[str, Any],
    list_type: Any = None,
) -> list[str]:
    fmt = paragraph.paragraph_format
    applied = []
    clear_tab_stops(paragraph)
    fmt.left_indent = Cm(float(level_config["left_indent_cm"]))
    fmt.first_line_indent = Cm(float(level_config["first_line_indent_cm"]))
    fmt.tab_stops.add_tab_stop(Cm(float(level_config["tab_stop_cm"])))
    applied.extend(["left_indent_cm", "first_line_indent_cm", "tab_stop_cm"])
    applied.extend(apply_list_numbering(paragraph, list_type))
    return sorted(set(applied))


def apply_bibliography_format(
    paragraph: Paragraph,
    config: dict[str, Any],
    section_index: int | None = None,
) -> list[str]:
    applied = []
    style_name = str(config.get("style_name", "List Number"))
    try:
        if paragraph.style is None or paragraph.style.name != style_name:
            paragraph.style = style_name
            applied.append("style_name")
    except Exception:
        pass

    applied.extend(apply_bibliography_numbering(paragraph, section_index))

    scalar_fields = [
        "alignment",
        "first_line_indent_cm",
        "left_indent_cm",
        "line_spacing",
        "space_before_pt",
        "space_after_pt",
    ]
    for field in scalar_fields:
        if field not in config:
            continue
        applied.extend(
            apply_scalar_fix(
                paragraph=paragraph,
                parameter=field,
                expected_value=config[field],
                default_font_name="Times New Roman",
            )
        )
    return sorted(set(applied))


def _find_decimal_abstract_num_id(numbering_root) -> str:
    for abstract_num in numbering_root.findall(qn("w:abstractNum")):
        level = abstract_num.find(qn("w:lvl"))
        if level is None:
            continue
        num_fmt = level.find(qn("w:numFmt"))
        level_text = level.find(qn("w:lvlText"))
        if (
            num_fmt is not None
            and num_fmt.get(qn("w:val")) == "decimal"
            and level_text is not None
            and level_text.get(qn("w:val")) in {"%1.", "%1)"}
        ):
            return str(abstract_num.get(qn("w:abstractNumId")))
    return "0"


def _next_abstract_num_id(numbering_root) -> int:
    existing = [
        int(abstract_num.get(qn("w:abstractNumId")))
        for abstract_num in numbering_root.findall(qn("w:abstractNum"))
        if abstract_num.get(qn("w:abstractNumId")) is not None
    ]
    return (max(existing) if existing else 0) + 1


def _next_num_id(numbering_root) -> int:
    existing = [
        int(num.get(qn("w:numId")))
        for num in numbering_root.findall(qn("w:num"))
        if num.get(qn("w:numId")) is not None
    ]
    return (max(existing) if existing else 0) + 1


def _create_section_abstract_num_id(numbering_root, section_index: int) -> str:
    abstract_num_id = _next_abstract_num_id(numbering_root)

    abstract_num = OxmlElement("w:abstractNum")
    abstract_num.set(qn("w:abstractNumId"), str(abstract_num_id))

    multi_level_type = OxmlElement("w:multiLevelType")
    multi_level_type.set(qn("w:val"), "singleLevel")
    abstract_num.append(multi_level_type)

    level = OxmlElement("w:lvl")
    level.set(qn("w:ilvl"), "0")

    start = OxmlElement("w:start")
    start.set(qn("w:val"), "1")
    level.append(start)

    num_fmt = OxmlElement("w:numFmt")
    num_fmt.set(qn("w:val"), "decimal")
    level.append(num_fmt)

    level_text = OxmlElement("w:lvlText")
    level_text.set(qn("w:val"), f"{section_index}.%1")
    level.append(level_text)

    level_jc = OxmlElement("w:lvlJc")
    level_jc.set(qn("w:val"), "left")
    level.append(level_jc)

    abstract_num.append(level)
    numbering_root.append(abstract_num)

    return str(abstract_num_id)


def bibliography_numbering_matches(paragraph: Paragraph, section_index: int | None) -> bool:
    try:
        num_pr = paragraph._p.pPr.numPr if paragraph._p.pPr is not None else None
        if num_pr is None or num_pr.numId is None or not _num_id_exists(paragraph, num_pr.numId.val):
            return False
        if section_index is None:
            return True
        numbering_root = paragraph.part.numbering_part.element
        num_id = str(num_pr.numId.val)
        abstract_num_id = None
        for num in numbering_root.findall(qn("w:num")):
            if num.get(qn("w:numId")) == num_id:
                abstract_ref = num.find(qn("w:abstractNumId"))
                abstract_num_id = abstract_ref.get(qn("w:val")) if abstract_ref is not None else None
                break
        if abstract_num_id is None:
            return False
        expected_level_text = f"{section_index}.%1"
        for abstract_num in numbering_root.findall(qn("w:abstractNum")):
            if abstract_num.get(qn("w:abstractNumId")) != abstract_num_id:
                continue
            level = abstract_num.find(qn("w:lvl"))
            level_text = level.find(qn("w:lvlText")) if level is not None else None
            return bool(level_text is not None and level_text.get(qn("w:val")) == expected_level_text)
    except Exception:
        return False
    return False


def _get_bibliography_num_id(paragraph: Paragraph, section_index: int | None = None) -> int:
    numbering_root = paragraph.part.numbering_part.element
    root_key = (id(numbering_root), section_index)
    if root_key in _BIBLIOGRAPHY_NUM_IDS:
        return _BIBLIOGRAPHY_NUM_IDS[root_key]

    abstract_num_id = (
        _create_section_abstract_num_id(numbering_root, section_index)
        if section_index is not None
        else _find_decimal_abstract_num_id(numbering_root)
    )
    num_id = _next_num_id(numbering_root)

    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))
    abstract_ref = OxmlElement("w:abstractNumId")
    abstract_ref.set(qn("w:val"), abstract_num_id)
    num.append(abstract_ref)
    numbering_root.append(num)

    _BIBLIOGRAPHY_NUM_IDS[root_key] = num_id
    return num_id


def _safe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        if pd_is_na(value):
            return None
    except Exception:
        pass
    try:
        return int(float(value))
    except Exception:
        return None


def pd_is_na(value: Any) -> bool:
    return value != value


def apply_bibliography_numbering(paragraph: Paragraph, section_index: int | None = None) -> list[str]:
    p_pr = paragraph._p.get_or_add_pPr()
    num_pr = p_pr.find(qn("w:numPr"))
    if num_pr is None:
        num_pr = OxmlElement("w:numPr")
        p_pr.append(num_pr)

    ilvl = num_pr.find(qn("w:ilvl"))
    if ilvl is None:
        ilvl = OxmlElement("w:ilvl")
        num_pr.append(ilvl)
    ilvl.set(qn("w:val"), "0")

    num_id_value = str(_get_bibliography_num_id(paragraph, section_index))
    num_id = num_pr.find(qn("w:numId"))
    if num_id is None:
        num_id = OxmlElement("w:numId")
        num_pr.append(num_id)
    num_id.set(qn("w:val"), num_id_value)

    return ["numbering"]


def _bibliography_section_index(row_data: dict[str, Any]) -> int | None:
    raw_value = row_data.get("bibliography_section_index")
    value = _safe_int(raw_value)
    if value is None or value < 1:
        return None
    return value


def _bibliography_section_title(text: str, section_index: int) -> str:
    title = re.sub(r"^\s*\d+\s+", "", text).strip().upper()
    return f"{section_index} {title}"


def _is_bibliography_section_heading(text: str) -> bool:
    return BIBLIOGRAPHY_SUBHEADING_RE.search(text) is not None


def bibliography_section_title_matches(paragraph: Paragraph, row_data: dict[str, Any]) -> bool:
    section_index = _bibliography_section_index(row_data)
    if section_index is None:
        return True
    return paragraph.text.strip() == _bibliography_section_title(paragraph.text, section_index)


def apply_bibliography_section_title(paragraph: Paragraph, row_data: dict[str, Any]) -> list[str]:
    section_index = _bibliography_section_index(row_data)
    if section_index is None:
        return []
    expected_text = _bibliography_section_title(paragraph.text, section_index)
    if paragraph.text.strip() == expected_text:
        return []
    paragraph.text = expected_text
    return ["bibliography_section_prefix"]


def bibliography_format_matches(
    paragraph: Paragraph,
    config: dict[str, Any],
    row_data: dict[str, Any],
) -> bool:
    section_index = _bibliography_section_index(row_data)
    current = get_current_paragraph_profile(paragraph)
    for field, expected in config.items():
        if field == "style_name":
            continue
        if not compare_scalar(current.get(field), expected):
            return False
    return bibliography_numbering_matches(paragraph, section_index)


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
    if str(list_type) == "list" and not has_numbering and not has_marker:
        unsafe_reasons.append("generic list_type without marker or Word numbering")
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
    bibliography_section_index = _bibliography_section_index(row_data)
    if label in {"title_section", "title_subsection"} and bibliography_section_index is not None:
        expected_text = _bibliography_section_title(paragraph.text, bibliography_section_index)
        if paragraph.text.strip() != expected_text:
            if apply_safe:
                paragraph.text = expected_text
                applied_fixes.append("bibliography_section_prefix")
            else:
                manual_review_required = True

    for rule in applicable_rules:
        parameter = str(rule["parameter"])
        if label == "list_item" and parameter == "bold":
            continue

        if parameter == "bibliography_section_title":
            if bibliography_section_title_matches(paragraph, row_data):
                continue
            violated_rules.append(rule["id"])
            suggested_fixes.append("bibliography_section_prefix")
            explanations.append(f"{rule['id']}: bibliography section title needs numbering")
            if apply_safe and rule["autocorrect"] and rule["action"] == "fix":
                applied_fixes.extend(apply_bibliography_section_title(paragraph, row_data))
            else:
                manual_review_required = True
            continue

        if parameter == "bibliography_format":
            expected_value = rule["expected_value"]
            if bibliography_format_matches(paragraph, expected_value, row_data):
                continue
            violated_rules.append(rule["id"])
            suggested_fixes.extend(
                [
                    "style_name",
                    "first_line_indent_cm",
                    "left_indent_cm",
                    "numbering",
                ]
            )
            explanations.append(f"{rule['id']}: bibliography item is not numbered/formatted")
            if apply_safe and rule["autocorrect"] and rule["action"] == "fix":
                applied_fixes.extend(
                    apply_bibliography_format(
                        paragraph,
                        expected_value,
                        _bibliography_section_index(row_data),
                    )
                )
            else:
                manual_review_required = True
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
            if list_layout_is_inherited(paragraph, current_list):
                continue
            if (
                current_list.get("left_indent_cm") is None
                and current_list.get("first_line_indent_cm") is None
                and paragraph_numbering_reference_is_valid(paragraph)
            ):
                continue
            if list_layout_is_accepted(current_list):
                raw_text = str(row_data.get("text", "") or paragraph.text or "")
                raw_text_has_list_hint = _paragraph_has_list_marker(raw_text) or raw_text.lstrip(" ").startswith("\t")
                current_style_name = ""
                try:
                    current_style_name = str(paragraph.style.name) if paragraph.style is not None and paragraph.style.name is not None else ""
                except Exception:
                    current_style_name = ""
                if not _paragraph_has_numbering(paragraph):
                    if apply_safe and rule["autocorrect"] and rule["action"] == "fix" and raw_text_has_list_hint:
                        applied_fixes.extend(apply_list_numbering(paragraph, list_assessment["list_type"]))
                    continue
                if not paragraph_numbering_reference_is_valid(paragraph):
                    violated_rules.append(rule["id"])
                    suggested_fixes.append("numbering")
                    explanations.append(f"{rule['id']}: broken list numbering reference")
                    if apply_safe and rule["autocorrect"] and rule["action"] == "fix":
                        applied_fixes.extend(apply_list_numbering(paragraph, list_assessment["list_type"]))
                    else:
                        manual_review_required = True
                continue
            if current_list.get("left_indent_cm") is None or current_list.get("first_line_indent_cm") is None:
                violated_rules.append(rule["id"])
                suggested_fixes.extend(["left_indent_cm", "first_line_indent_cm", "numbering"])
                explanations.append(f"{rule['id']}: list layout is inherited or incomplete")
                has_partial_existing_layout = (
                    current_list.get("left_indent_cm") is not None
                    or current_list.get("first_line_indent_cm") is not None
                )
                if has_partial_existing_layout and (
                    _paragraph_has_list_style(paragraph) or _paragraph_has_numbering(paragraph)
                ):
                    manual_review_required = True
                    continue
                raw_text = str(row_data.get("text", "") or paragraph.text or "").strip()
                trusted_missing_layout = (
                    not _paragraph_has_list_marker(raw_text)
                    and not _is_long_plain_paragraph(raw_text)
                )
                if apply_safe and rule["autocorrect"] and rule["action"] == "fix" and (
                    list_assessment["safe_to_autofix"] or trusted_missing_layout
                ):
                    applied_fixes.extend(apply_list_format(paragraph, expected_value, list_assessment["list_type"]))
                else:
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
                applied_fixes.extend(apply_list_format(paragraph, expected_value, list_assessment["list_type"]))
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
            if label in {"title_section", "title_subsection"} and bibliography_section_index is not None:
                manual_review_required = True
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
