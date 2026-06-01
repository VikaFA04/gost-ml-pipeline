# Phase 3: Heading signature & DOCX generator — Pattern Map

**Mapped:** 2026-05-13
**Files analyzed:** 8 new/modified files
**Analogs found:** 8 / 8

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/rules/style_signatures.py` | utility/extractor-helper | transform | itself (Phase 1 — `classify_style`) | exact-extend |
| `src/io/block_extractor.py` | extractor | transform | itself (Phase 1 — `extract_paragraph_block`) | exact-extend |
| `src/rules/rule_engine.py` | rule dispatcher | request-response | itself (Phase 1/2 — `_apply_scalar_rule`, `apply_scalar_fix`) | exact-modify |
| `src/rules/formatting_rules_v1.json` | config/rule JSON | — | itself (existing `heading_alignment`, `heading_indent`, `heading_bold` rules) | exact-extend |
| `tests/fixtures/_build_heading_minimal.py` | fixture builder | file-I/O | `tests/fixtures/_build_bibliography_minimal.py` | exact |
| `tests/fixtures/heading_minimal.docx` | fixture binary | — | `tests/fixtures/bibliography_minimal.docx` | exact pattern |
| `tests/test_style_signatures.py` | test | CRUD | itself (Phase 1 heading/list classify tests) | exact-extend |
| `tests/test_rule_engine.py` | test | request-response | itself (Phase 1/2 heading tests lines 110–150) | exact-extend |
| `tests/test_positive_docx_regression.py` | regression gate | integration | itself (Phase 2-extended gate) | exact-extend |

---

## Pattern Assignments

### `src/rules/style_signatures.py` — add `_extract_heading_format_signature` + `_resolve_inherited_value`

**Analog:** `src/rules/style_signatures.py` (Phase 1 `classify_style`)

**Imports pattern** (lines 1–10 — copy verbatim, add `json` if serialization stays here):
```python
from __future__ import annotations

import re
from typing import Literal

from docx.text.paragraph import Paragraph
```

**Heading detection gate** (lines 58–65 — the guard that Phase 3 helpers use to short-circuit):
```python
def paragraph_has_heading_style(paragraph: Paragraph) -> bool:
    """True if paragraph.style.name matches HEADING_STYLE_RE; False on any error."""
    try:
        if paragraph.style is not None and paragraph.style.name is not None:
            return bool(HEADING_STYLE_RE.search(str(paragraph.style.name)))
    except Exception:
        return False
    return False
```

**Core pattern for new helpers** — two-pass resolver (from RESEARCH.md §Pattern 1):

```python
def _resolve_inherited_value(style, attr_getter):
    """Walk base_style chain; return first non-None value or None."""
    current = style
    while current is not None:
        val = attr_getter(current)
        if val is not None:
            return val
        current = getattr(current, 'base_style', None)
    return None


def _extract_heading_format_signature(paragraph) -> dict:
    """Two-pass resolver (D-03/D-04): returns {field: {value, source}} for 17 fields.
    Called only when classify_style(paragraph) == "heading" (D-01 lazy guard).
    """
    fmt = paragraph.paragraph_format
    style = paragraph.style

    def _walk_pf(attr: str):
        return _resolve_inherited_value(style, lambda s: getattr(s.paragraph_format, attr, None))

    def _walk_font(attr: str):
        return _resolve_inherited_value(style, lambda s: getattr(s.font, attr, None))

    def _tagged(direct_val, inherited_getter):
        if direct_val is not None:
            return {"value": direct_val, "source": "direct"}
        inherited = inherited_getter()
        if inherited is not None:
            return {"value": inherited, "source": "inherited"}
        return {"value": None, "source": "unset"}

    # Pass 1 — font fields: first run with non-None direct value
    direct_font_name = direct_font_size = direct_bold = None
    direct_italic = direct_underline = direct_color = direct_caps = None
    for run in paragraph.runs:
        if run.text and run.text.strip():
            if direct_font_name is None and run.font.name is not None:
                direct_font_name = run.font.name
            if direct_font_size is None and run.font.size is not None:
                direct_font_size = round(run.font.size.pt, 3)
            if direct_bold is None and run.bold is not None:
                direct_bold = bool(run.bold)
            if direct_italic is None and run.italic is not None:
                direct_italic = bool(run.italic)
            if direct_underline is None and run.font.underline is not None:
                direct_underline = run.font.underline
            if direct_color is None and run.font.color.type is not None:
                direct_color = str(run.font.color.rgb) if run.font.color.rgb else "auto"
            if direct_caps is None and run.font.all_caps is not None:
                direct_caps = bool(run.font.all_caps)

    # Pass 1 — paragraph scalar fields
    direct_align = paragraph.alignment  # WD_ALIGN_PARAGRAPH or None
    direct_first_line = round(fmt.first_line_indent.cm, 3) if fmt.first_line_indent is not None else None
    direct_left = round(fmt.left_indent.cm, 3) if fmt.left_indent is not None else None
    direct_right = round(fmt.right_indent.cm, 3) if fmt.right_indent is not None else None
    ls = fmt.line_spacing
    direct_ls = round(float(ls), 3) if isinstance(ls, (int, float)) else None
    direct_sb = round(fmt.space_before.pt, 3) if fmt.space_before is not None else None
    direct_sa = round(fmt.space_after.pt, 3) if fmt.space_after is not None else None

    # Pass 1 — flow flags
    direct_kwn = fmt.keep_with_next
    direct_klt = fmt.keep_together
    direct_pbb = fmt.page_break_before
    direct_wc = fmt.widow_control

    from src.io.block_extractor import ALIGNMENT_MAP  # avoid circular if needed — or inline map
    _align_str = lambda v: ALIGNMENT_MAP.get(v) if v is not None else None

    return {
        "font_name":            _tagged(direct_font_name, lambda: _walk_font("name")),
        "font_size":            _tagged(direct_font_size,
                                        lambda: round(_walk_font("size").pt, 3) if _walk_font("size") else None),
        "bold":                 _tagged(direct_bold,    lambda: _walk_font("bold")),
        "italic":               _tagged(direct_italic,  lambda: _walk_font("italic")),
        "underline":            _tagged(direct_underline, lambda: _walk_font("underline")),
        "color":                _tagged(direct_color,   lambda: None),
        "caps":                 _tagged(direct_caps,    lambda: _walk_font("all_caps")),
        "alignment":            _tagged(_align_str(direct_align), lambda: _align_str(_walk_pf("alignment"))),
        "first_line_indent_cm": _tagged(direct_first_line, lambda: round(_walk_pf("first_line_indent").cm, 3) if _walk_pf("first_line_indent") else None),
        "left_indent_cm":       _tagged(direct_left,   lambda: round(_walk_pf("left_indent").cm, 3) if _walk_pf("left_indent") else None),
        "right_indent_cm":      _tagged(direct_right,  lambda: round(_walk_pf("right_indent").cm, 3) if _walk_pf("right_indent") else None),
        "line_spacing":         _tagged(direct_ls,     lambda: round(float(_walk_pf("line_spacing")), 3) if isinstance(_walk_pf("line_spacing"), (int, float)) else None),
        "space_before_pt":      _tagged(direct_sb,     lambda: round(_walk_pf("space_before").pt, 3) if _walk_pf("space_before") else None),
        "space_after_pt":       _tagged(direct_sa,     lambda: round(_walk_pf("space_after").pt, 3) if _walk_pf("space_after") else None),
        "keep_with_next":       _tagged(direct_kwn,    lambda: _walk_pf("keep_with_next")),
        "keep_lines_together":  _tagged(direct_klt,    lambda: _walk_pf("keep_together")),
        "page_break_before":    _tagged(direct_pbb,    lambda: _walk_pf("page_break_before")),
        "widow_control":        _tagged(direct_wc,     lambda: _walk_pf("widow_control")),
    }
```

**Error handling:** wrap each `run.font.*` access in try/except as in `get_first_text_run_style` (rule_engine.py lines 73–86). Never raise from extractor — return `{"value": None, "source": "unset"}` on exception.

---

### `src/io/block_extractor.py` — extend `extract_paragraph_block`

**Analog:** `src/io/block_extractor.py` itself (lines 126–146)

**Imports to add:**
```python
import json
from src.rules.style_signatures import classify_style, _extract_heading_format_signature
```

**Core modification — add nested key after existing 5 flat keys** (line 135–146):
```python
def extract_paragraph_block(paragraph, doc_id, block_id, file_name):
    text = "" if paragraph.text is None else str(paragraph.text)
    list_type, list_level = extract_list_metadata(paragraph)

    row = {
        "doc_id": doc_id,
        "block_id": block_id,
        "text": text,
        "kind": "paragraph",
        "alignment": normalize_alignment(paragraph),
        "style": get_style_name(paragraph),
        "bold_ratio": round(compute_bold_ratio_from_runs(paragraph), 4),
        "list_type": list_type,
        "list_level": list_level,
        "file_name": file_name,
        # D-01: heading-only; non-heading rows get None (serialized as NaN in CSV)
        "heading_format_signature": None,
    }

    if classify_style(paragraph) == "heading":
        sig = _extract_heading_format_signature(paragraph)
        row["heading_format_signature"] = json.dumps(sig)

    return row
```

**Serialization contract:** `json.dumps(sig)` → compact JSON string. Non-heading rows → `None` → pandas writes as NaN column. Downstream deserialization uses NaN guard from RESEARCH.md §Pattern 3:
```python
import math
raw = row_data.get("heading_format_signature")
if raw is None or (isinstance(raw, float) and math.isnan(raw)):
    sig = None
elif isinstance(raw, str) and raw:
    sig = json.loads(raw)
else:
    sig = None
```

---

### `src/rules/rule_engine.py` — modify `_apply_scalar_rule` + extend `apply_scalar_fix`

**Analog:** `src/rules/rule_engine.py` (existing `_apply_scalar_rule` lines 928–1030 and `apply_scalar_fix` lines 752–780)

**Imports to add:**
```python
import json, math
```

**Blanket guard to REMOVE** (lines 998–1004 — the entire block):
```python
# DELETE THESE LINES:
if label in {"title_section", "title_subsection"} and _paragraph_has_heading_style(paragraph):
    return {
        "current_profile": current_profile,
        "manual_review_required": True,
        "blocked_unsafe_autofix": blocked_unsafe_autofix,
        "unsafe_auto_fix_reason": unsafe_auto_fix_reason,
    }
```

**New per-field heading rule dispatcher** — insert in `apply_rules_to_paragraph` (after the `bibliography_format` parameter check block, before `_apply_scalar_rule` call at line 1211). The parameter values `heading_*` rules use map 1:1 to signature field keys:

```python
# D-05/D-06 heading per-field source routing
if label in {"title_section", "title_subsection"} and parameter in {
    "font_name", "font_size", "bold", "italic", "underline", "color", "caps",
    "alignment", "first_line_indent_cm", "left_indent_cm", "right_indent_cm",
    "line_spacing", "space_before_pt", "space_after_pt",
    "keep_with_next", "keep_lines_together", "page_break_before", "widow_control",
}:
    raw = row_data.get("heading_format_signature")
    sig = None
    if isinstance(raw, str) and raw:
        try:
            sig = json.loads(raw)
        except Exception:
            sig = None
    elif isinstance(raw, float) and math.isnan(raw):
        sig = None

    if sig is None:
        # No signature extracted (non-heading row mis-labeled): skip silently
        continue

    entry = sig.get(parameter, {"value": None, "source": "unset"})
    source = entry.get("source", "unset")
    actual = entry.get("value")
    expected = rule["expected_value"]

    if source == "unset" or actual is None:
        continue  # nothing to check

    if not compare_scalar(actual, expected):
        violated_rules.append(rule["id"])
        suggested_fixes.append(parameter)
        if source == "inherited":
            # D-05: inherited mismatch → review only, NEVER autofix
            explanations.append(
                f"heading_inherited_mismatch:field={parameter},actual={actual},expected={expected}"
            )
            manual_review_required = True
        elif source == "direct":
            # D-06: direct mismatch → autofix (clear or set)
            explanations.append(f"{rule['id']}: expected {parameter}={expected}")
            if apply_safe and rule.get("autocorrect") and rule.get("action") == "fix":
                applied_fixes.extend(
                    apply_heading_scalar_fix(paragraph, parameter, expected)
                )
    continue  # do NOT fall through to _apply_scalar_rule
```

**New `apply_heading_scalar_fix` function** — add after `apply_scalar_fix` (line ~780). Mirrors `apply_scalar_fix` style; handles the 10 new parameter branches plus delegates existing 8 to `apply_scalar_fix`:

```python
def apply_heading_scalar_fix(paragraph: Paragraph, parameter: str, expected_value: Any) -> list[str]:
    """D-06: fix or clear direct override on a heading paragraph.
    Setting to None removes the direct override and restores style inheritance.
    """
    fmt = paragraph.paragraph_format

    if parameter == "right_indent_cm":
        fmt.right_indent = Cm(float(expected_value)) if expected_value is not None else None
    elif parameter == "keep_with_next":
        fmt.keep_with_next = bool(expected_value) if expected_value is not None else None
    elif parameter == "keep_lines_together":
        fmt.keep_together = bool(expected_value) if expected_value is not None else None
    elif parameter == "page_break_before":
        fmt.page_break_before = bool(expected_value) if expected_value is not None else None
    elif parameter == "widow_control":
        fmt.widow_control = bool(expected_value) if expected_value is not None else None
    elif parameter == "font_name":
        for run in paragraph.runs:
            if run.text:
                run.font.name = str(expected_value) if expected_value else None
    elif parameter == "italic":
        for run in paragraph.runs:
            if run.text:
                run.font.italic = bool(expected_value) if expected_value is not None else None
    elif parameter == "underline":
        for run in paragraph.runs:
            if run.text:
                run.font.underline = bool(expected_value) if expected_value is not None else None
    elif parameter == "caps":
        for run in paragraph.runs:
            if run.text:
                run.font.all_caps = bool(expected_value) if expected_value is not None else None
    elif parameter == "color":
        # D-09/Pitfall 6: color rule has autocorrect:false — this branch should never fire
        pass
    else:
        # Delegate existing 8 parameters to apply_scalar_fix (alignment, indents, spacing, bold, font_size)
        return apply_scalar_fix(paragraph, parameter, expected_value, default_font_name="")
    return [parameter]
```

**`get_current_paragraph_profile` pattern** (lines 89–105) — the same `.pt`/`.cm` conversion approach applies in `_extract_heading_format_signature`. Key snippet:
```python
line_spacing = fmt.line_spacing
line_spacing_value = None
if isinstance(line_spacing, (int, float)):
    line_spacing_value = round(float(line_spacing), 3)
# space_before stored as EMU — always convert:
"space_before_pt": round(fmt.space_before.pt, 3) if fmt.space_before is not None else None,
```

---

### `src/rules/formatting_rules_v1.json` — add ~15 new heading rules

**Analog:** existing `heading_alignment` / `heading_indent` / `heading_bold` rules (lines 33–62)

**Exact shape of the 3 existing rules to copy** (lines 33–62):
```json
{
  "id": "heading_alignment",
  "applicable_labels": ["title_section", "title_subsection"],
  "parameter": "alignment",
  "expected_value": "LEFT",
  "action": "fix",
  "severity": "high",
  "autocorrect": true,
  "priority": 40
},
{
  "id": "heading_indent",
  "applicable_labels": ["title_section", "title_subsection"],
  "parameter": "first_line_indent_cm",
  "expected_value": 0.0,
  "action": "fix",
  "severity": "medium",
  "autocorrect": true,
  "priority": 30
},
{
  "id": "heading_bold",
  "applicable_labels": ["title_section", "title_subsection"],
  "parameter": "bold",
  "expected_value": true,
  "action": "fix",
  "severity": "medium",
  "autocorrect": true,
  "priority": 20
}
```

**New rules follow identical shape.** Level-sensitive fields (`font_size`) require two rules per field — one for `title_section`, one for `title_subsection` (RESEARCH.md Open Question 2 recommendation):
```json
{
  "id": "heading_section_font_size",
  "applicable_labels": ["title_section"],
  "parameter": "font_size",
  "expected_value": 18.0,
  "action": "fix",
  "severity": "high",
  "autocorrect": true,
  "priority": 50
},
{
  "id": "heading_subsection_font_size",
  "applicable_labels": ["title_subsection"],
  "parameter": "font_size",
  "expected_value": 16.0,
  "action": "fix",
  "severity": "high",
  "autocorrect": true,
  "priority": 50
}
```

**Color rule** — `autocorrect: false` per RESEARCH.md Pitfall 6 / A3:
```json
{
  "id": "heading_color",
  "applicable_labels": ["title_section", "title_subsection"],
  "parameter": "color",
  "expected_value": null,
  "action": "fix",
  "severity": "low",
  "autocorrect": false,
  "priority": 10
}
```

**`parameter` name must match the `heading_format_signature` key exactly.** The dispatcher at rule_engine reads `sig[rule["parameter"]]`. Existing rules: `alignment`, `first_line_indent_cm`, `bold`. New rules use: `font_size`, `font_name`, `italic`, `underline`, `caps`, `color`, `left_indent_cm`, `right_indent_cm`, `space_before_pt`, `space_after_pt`, `line_spacing`, `keep_with_next`, `keep_lines_together`, `page_break_before`, `widow_control`.

---

### `tests/fixtures/_build_heading_minimal.py` — new fixture builder

**Analog:** `tests/fixtures/_build_bibliography_minimal.py` (entire file — exact pattern)

**File header docstring pattern** (lines 1–20 of `_build_bibliography_minimal.py`):
```python
"""One-shot fixture builder for tests/fixtures/heading_minimal.docx.

Run once:
    python tests/fixtures/_build_heading_minimal.py

Layout (D-10):
  1. Positive Heading 1 — target signature; all direct values None → zero fixes.
  2. Wrong-intervals heading — direct space_before_pt/space_after_pt override mismatch → autofix (D-06).
  3. Wrong-font-params heading — direct font_size/bold override mismatch → autofix (D-06).
  4. Inherited-mismatch heading — Heading 1 style-cascade value differs from profile → review (D-05).
"""
from __future__ import annotations
from pathlib import Path
from docx import Document
```

**Core build pattern** (lines 103–141 of `_build_bibliography_minimal.py` — adapt):
```python
def build(output_path: Path) -> None:
    document = Document()

    # 1. Positive — Heading 1, ALL direct overrides None
    p1 = document.add_paragraph("1 Основная часть")
    p1.style = "Heading 1"
    # No direct overrides set; all values inherited from Heading 1 style.

    # 2. Wrong-intervals — direct space_before/space_after override
    p2 = document.add_paragraph("2 Нарушение интервалов")
    p2.style = "Heading 1"
    p2.paragraph_format.space_before = Pt(99.0)  # direct override, wrong value
    p2.paragraph_format.space_after = Pt(99.0)

    # 3. Wrong-font-params — direct font_size/bold override on runs
    p3 = document.add_paragraph("3 Нарушение шрифта")
    p3.style = "Heading 1"
    for run in p3.runs:
        if run.text:
            run.font.size = Pt(9.0)   # direct override, wrong value
            run.bold = False           # direct override, wrong value

    # 4. Inherited-mismatch — style-cascade value differs from GOST profile
    # (Heading 1 style has space_after=28.35pt; profile expects 0pt)
    # No direct override → source="inherited" → D-05 review only
    p4 = document.add_paragraph("4 Унаследованное нарушение")
    p4.style = "Heading 1"
    # No direct override; inherited mismatch surfaces automatically.

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(output_path))

if __name__ == "__main__":
    build(Path("tests/fixtures/heading_minimal.docx"))
    print("wrote tests/fixtures/heading_minimal.docx")
```

**Critical:** builder MUST NOT import `rule_engine` or `style_signatures` — it is the contract anchor for RED tests (same constraint as `_build_bibliography_minimal.py` line 34).

---

### `tests/test_style_signatures.py` — extend with heading signature extraction tests

**Analog:** `tests/test_style_signatures.py` (Phase 1 `classify_style` tests — entire file)

**Shim pattern** (lines 16–22 — reuse for testing `_extract_heading_format_signature`):
```python
# For tests that need a real Heading 1 paragraph with direct overrides:
from docx import Document
from docx.shared import Pt, Cm

def _make_heading_paragraph(style="Heading 1"):
    document = Document()
    p = document.add_paragraph("Тест заголовка")
    p.style = style
    return p
```

**Test shape pattern** (lines 25–36 in existing file — each test is 6–8 lines, asserts one behavior):
```python
def test_heading_signature_key_present() -> None:
    from src.rules.style_signatures import _extract_heading_format_signature
    p = _make_heading_paragraph()
    sig = _extract_heading_format_signature(p)
    assert isinstance(sig, dict)
    assert "font_size" in sig
    assert "keep_with_next" in sig

def test_heading_signature_direct_none_is_inherited() -> None:
    # All direct values None → every field is source="inherited" or "unset"
    from src.rules.style_signatures import _extract_heading_format_signature
    p = _make_heading_paragraph()
    sig = _extract_heading_format_signature(p)
    for field, entry in sig.items():
        assert entry["source"] in ("inherited", "unset"), f"{field}: {entry}"

def test_heading_signature_direct_override_detected() -> None:
    from src.rules.style_signatures import _extract_heading_format_signature
    from docx.shared import Pt
    p = _make_heading_paragraph()
    p.paragraph_format.space_before = Pt(99.0)
    sig = _extract_heading_format_signature(p)
    assert sig["space_before_pt"]["source"] == "direct"
    assert abs(sig["space_before_pt"]["value"] - 99.0) < 0.1
```

**Import pattern** (lines 1–13 of existing `test_style_signatures.py`):
```python
from __future__ import annotations
from types import SimpleNamespace
from docx import Document
from src.rules.style_signatures import classify_style
```

---

### `tests/test_rule_engine.py` — add D-05/D-06 routing tests; update existing heading test

**Analog:** `tests/test_rule_engine.py` lines 110–150 (the two existing heading tests)

**Test setup pattern** (lines 110–128 — `apply_rules_to_paragraph` call shape):
```python
def test_heading_inherited_mismatch_routes_to_review() -> None:
    document = Document()
    paragraph = document.add_paragraph("1 Заголовок")
    paragraph.style = "Heading 1"
    # No direct override → all source="inherited"
    # Must supply heading_format_signature in row_data (pre-serialized JSON)
    import json
    from src.rules.style_signatures import _extract_heading_format_signature
    sig = _extract_heading_format_signature(paragraph)
    row_data = {
        "confidence_score": 0.99,
        "low_confidence": False,
        "heading_format_signature": json.dumps(sig),
    }
    result = apply_rules_to_paragraph(
        paragraph=paragraph,
        label="title_section",
        row_data=row_data,
        rules=load_rules(),
        apply_safe=True,
        default_font_name="Times New Roman",
    )
    assert result["status"] == "review"
    assert result["applied_fixes"] == []
    # explanation contains heading_inherited_mismatch prefix
    assert "heading_inherited_mismatch" in result["explanation"]
```

**Test that MUST BE UPDATED** (lines 131–150 — `test_heading_style_direct_alignment_requires_review_not_autofix`):
```python
# BEFORE Phase 3: asserts status="review" (blanket guard fires)
# AFTER Phase 3: paragraph.alignment = 1 is a DIRECT override → D-06 → status="changed"
# Update the assertion:
def test_heading_style_direct_alignment_autofixed_after_guard_removal() -> None:
    document = Document()
    paragraph = document.add_paragraph("Список источников")
    paragraph.style = "Heading 2"
    paragraph.alignment = 1  # direct override — CENTER (WD_ALIGN_PARAGRAPH.CENTER)
    import json
    from src.rules.style_signatures import _extract_heading_format_signature
    sig = _extract_heading_format_signature(paragraph)
    result = apply_rules_to_paragraph(
        paragraph=paragraph,
        label="title_subsection",
        row_data={
            "text": paragraph.text,
            "confidence_score": 0.99,
            "low_confidence": False,
            "heading_format_signature": json.dumps(sig),
        },
        rules=load_rules(),
        apply_safe=True,
        default_font_name="Times New Roman",
    )
    assert result["status"] == "changed"
    assert "alignment" in result["applied_fixes"]
```

**`build_prediction_csv` helper** (lines 21–50 — reuse for integration tests that go through the CSV pipeline):
```python
# heading_format_signature column must be added to the CSV row dict:
{
    ...existing fields...,
    "heading_format_signature": json.dumps(sig),  # or None for non-heading rows
}
```

---

### `tests/test_positive_docx_regression.py` — extend with heading-direct-fix invariant

**Analog:** `tests/test_positive_docx_regression.py` (entire file — lines 61–74 filtering pattern)

**Extension pattern** (add after `non_bib_changed.empty` assertion, lines 71–74):
```python
# D-07: heading-direct-fix invariant — zero heading_* autofixes on GOST-decorated subset
def _has_heading_fix(fixes: object) -> bool:
    if not isinstance(fixes, str) or not fixes:
        return False
    return any(t.strip().startswith("heading_") or t.strip() in {
        "font_name", "font_size", "bold", "italic", "underline", "caps",
        "color", "right_indent_cm", "space_before_pt", "space_after_pt",
        "line_spacing", "keep_with_next", "keep_lines_together",
        "page_break_before", "widow_control",
    } for t in fixes.split(","))

heading_changed = changed[
    changed["label"].isin({"title_section", "title_subsection"})
    & changed["applied_fixes"].apply(_has_heading_fix)
]
assert heading_changed.empty, (
    f"{file_name}: heading paragraphs were autofixed (D-07 gate):\n"
    f"{heading_changed[['block_id', 'label', 'applied_fixes', 'text']].to_string()}"
)
```

**`checked_files` stays** `["1.docx", "4.docx"]` (already correct per D-08 — 58/59 dropped in the existing file).

---

## Shared Patterns

### `classify_style` heading gate (applies to extractor + rule engine)
**Source:** `src/rules/style_signatures.py` lines 23–45 and 58–65
**Apply to:** `extract_paragraph_block` (lazy call guard), `apply_rules_to_paragraph` (heading rule branch entry)
```python
from src.rules.style_signatures import classify_style, paragraph_has_heading_style
# In extractor:
if classify_style(paragraph) == "heading":
    ...extract signature...
# In rule engine dispatcher (already present via _paragraph_has_heading_style import, line 15):
if label in {"title_section", "title_subsection"} and parameter in HEADING_SIG_FIELDS:
    ...
```

### `None` = inherited, never autofix directly
**Source:** `src/rules/rule_engine.py` lines 953–972 (`_apply_scalar_rule` None branch → review) + Phase 1 root cause A
**Apply to:** `_extract_heading_format_signature` (Pass 1 checks), `apply_heading_scalar_fix` (clear-to-None semantics)
```python
# Direct value is None → inherited. Source: rule_engine.py line 956:
if current_value is None:
    ...manual_review_required = True  # never autofix
# Inverse: clearing a direct override restores inheritance:
fmt.space_before = None  # verified: python-docx 1.2.0
```

### Length → pt/cm conversion (applies to all extractor numeric reads)
**Source:** `src/rules/rule_engine.py` lines 98–102 (`get_current_paragraph_profile`)
**Apply to:** `_extract_heading_format_signature` for all Length fields
```python
"first_line_indent_cm": round(fmt.first_line_indent.cm, 3) if fmt.first_line_indent is not None else None,
"space_before_pt":      round(fmt.space_before.pt, 3)      if fmt.space_before      is not None else None,
# font.size → EMU → .pt:
round(run.font.size.pt, 3) if run.font.size is not None else None
```

### `compare_scalar` (applies to heading field comparison)
**Source:** `src/rules/rule_engine.py` lines 740–745
**Apply to:** heading rule dispatcher `if not compare_scalar(actual, expected):`
```python
def compare_scalar(current_value, expected_value) -> bool:
    if isinstance(expected_value, float):
        if current_value is None:
            return False
        return abs(float(current_value) - expected_value) <= 0.05
    return current_value == expected_value
```

### `explanation` string format (applies to all routing outcomes)
**Source:** `src/rules/rule_engine.py` lines 748–749, 976, 1059, 1079
**Apply to:** D-05 review explanation
```python
# Existing patterns:
f"style_guard_block: rule_class=body_text paragraph_style_class={paragraph_style_class}"
"ambiguous_list_marker_no_numId"
f"{rule['id']}: expected {parameter}={rule['expected_value']}"
# New D-05 pattern:
f"heading_inherited_mismatch:field={parameter},actual={actual},expected={expected}"
```

### Fixture builder: no rule_engine imports
**Source:** `tests/fixtures/_build_bibliography_minimal.py` line 34 (comment)
**Apply to:** `tests/fixtures/_build_heading_minimal.py`
```python
# Builder MUST NOT import rule_engine internals — it is the contract anchor for RED tests.
# Allowed imports: docx, docx.shared, docx.oxml, pathlib, __future__.annotations
```

---

## No Analog Found

All 8 files have analogs in the existing codebase. No items in this category.

---

## Metadata

**Analog search scope:** `src/rules/`, `src/io/`, `tests/`, `tests/fixtures/`
**Files scanned:** 9 source files read directly
**Pattern extraction date:** 2026-05-13
