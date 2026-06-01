# Phase 03: Heading signature & DOCX generator — Research

**Researched:** 2026-05-12
**Domain:** python-docx style cascade, per-field heading rules, direct/inherited source tagging
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01** Hybrid schema. Existing 5 flat extractor keys (`alignment`, `style`, `bold_ratio`, `list_type`, `list_level`) stay flat. New heading-only fields land in nested `heading_format_signature: {...}` key. Audit CSV serializes the nest as a JSON string column.
- **D-02** All 17 fields ship in Phase 3 — no defer. Font: `font_name, font_size, bold, italic, underline, color, caps`. Paragraph scalars: `alignment, first_line_indent_cm, left_indent_cm, right_indent_cm, space_before_pt, space_after_pt, line_spacing`. Flow flags: `keep_with_next, keep_lines_together, page_break_before, widow_control`.
- **D-03** Two-pass resolver. Pass 1: `paragraph.paragraph_format.X` / `run.font.X` directly (None = inherited). Pass 2: walk `paragraph.style.base_style` chain until non-None or chain ends. Pure python-docx; no lxml. Multi-run: first run with non-None value wins; if all None, walk cascade.
- **D-04** Per-field source tagging: every signature entry is `{value: <T>, source: "direct"|"inherited"|"unset"}`.
- **D-05** Inherited mismatch → `review` only. Explanation pattern `heading_inherited_mismatch:field=<name>,actual=<a>,expected=<e>`. NEVER autofix.
- **D-06** Direct mismatch → autofix (set to expected OR clear to `None` to fall back to style). `applied_fixes` lists field name.
- **D-07** Reuse Phase 2 positive-corpus gate; extend with heading-direct-fix invariant: zero `heading_*` autofixes on GOST-decorated positive subset.
- **D-08** `REQ-fix-docx-generator-custom-styles` dropped; 58/59 excluded from gate. Phase 3 covers `REQ-heading-style-signature` only.
- **D-09** Per-field heading rules in `formatting_rules_v1.json`. One rule per signature field. Rule `parameter` maps 1:1 to signature field key. `applied_fixes` lists each field separately.
- **D-10** Hand-crafted `tests/fixtures/heading_minimal.docx` (4 paragraphs) + builder `tests/fixtures/_build_heading_minimal.py`.

### Claude's Discretion

- Exact JSON shape of signature entries (`{value, source}` dict literal vs `{v, s}` short keys vs tuple).
- Internal helper naming.
- Whether cascade explanation includes the chain (`cascade=Heading_1<-Normal`) or just `field=,actual=,expected=`.
- Whether `heading_caps` uses `style.font.all_caps` flag OR `text == text.upper()` heuristic.
- Exact `expected_value` JSON shape per heading rule.

### Deferred Ideas (OUT OF SCOPE)

- `REQ-fix-docx-generator-custom-styles` — v2 / Phase 5.
- Heading TOC integration.
- Multi-level heading rules with level-specific targets (Phase 3 ships generic across heading levels).
- Color check if too aggressive — researcher confirms: positive headings have `color.type=None` (no color set), so color rule would always be `source=inherited` → goes to review, never autofix.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-heading-style-signature | Heading style signature extended (font name/size/bold/italic/underline/color/CAPS + alignment/indents/spacing/keep_with_next/keep_lines/page_break/widow) with direct-vs-inherited separation. Positive corpus stays `changed=0`; negative heading fixtures move toward target signature with no text changes. | Two-pass resolver pattern verified via python-docx API audit; safety guarantee confirmed by corpus sampling showing all-None direct state on positive headings. |
</phase_requirements>

---

## Summary

Phase 3 extends `extract_paragraph_block` with a nested `heading_format_signature` key carrying 17–18 fields, each tagged `{value, source: "direct"|"inherited"|"unset"}`. The resolver uses a two-pass python-docx walk: first read direct (paragraph-level) properties (None = inherited), then walk the `paragraph.style.base_style` chain to resolve effective inherited value. Rule engine then routes per source: direct mismatch → autofix (D-06); inherited mismatch → review (D-05).

The critical safety property is confirmed: all heading paragraphs in `positive_examples/1.docx` and `4.docx` have ALL-None direct formatting. Every field resolves to `source="inherited"`, which means D-05 fires (never autofix), and the positive corpus gate passes with zero `heading_*` applied_fixes. The existing blanket heading guard in `_apply_scalar_rule` (line 998–1004) must be REPLACED by the per-field source routing introduced in Phase 3 — it currently blocks all heading scalar fixes as `manual_review_required=True` without the new source discrimination.

Three existing rules (`heading_alignment`, `heading_indent`, `heading_bold`) already exist in `formatting_rules_v1.json` with correct `applicable_labels` but their behavior must be updated by the new routing logic. Approximately 15 new rules are needed. The `apply_scalar_fix` function covers 8 parameters; 10 new parameter branches are required for the full heading signature. Audit CSV serialization of the nested `heading_format_signature` must use `json.dumps` in the extractor; `json.loads` in the rule engine (with NaN guard for non-heading rows).

**Primary recommendation:** Build the two-pass resolver as a standalone helper in `src/rules/style_signatures.py`, consume it in `extract_paragraph_block`, serialize via `json.dumps`, then in the rule engine read the JSON string and route per field source.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Signature extraction (17 fields, source tagging) | `src/io/block_extractor.py` | `src/rules/style_signatures.py` (helper) | Extraction happens at DOCX-read time; helper centralizes cascade walk reused across modules |
| Two-pass cascade resolver | `src/rules/style_signatures.py` | — | Already owns `classify_style`, `HEADING_STYLE_RE`; adding `_resolve_inherited_value` / `_extract_heading_format_signature` here keeps heading concerns together |
| Per-field source routing (review vs autofix) | `src/rules/rule_engine.py` | — | `apply_rules_to_paragraph` is the central dispatcher; D-05/D-06 routing replaces existing blanket guard |
| Per-field heading rules (JSON) | `src/rules/formatting_rules_v1.json` | — | D-09 — same rule format as existing; 18 total rules |
| Profile expected values | `src/rules/formatting_rules_v1.json` | `src/rules/profiles/gost_7_32_2017.json` (future) | Currently embedded in rule JSON (consistent with existing pattern); Phase 5 moves to profile selection |
| Autofix writes | `src/rules/rule_engine.py::apply_scalar_fix` (extended) | — | Existing apply_scalar_fix handles 8 params; 10 new branches added inline |
| Positive-corpus regression gate | `tests/test_positive_docx_regression.py` | — | Phase 2 established pattern; Phase 3 adds heading-direct-fix invariant assertion |
| Fixture building | `tests/fixtures/_build_heading_minimal.py` | — | Phase 1/2 pattern; self-contained, no rule_engine imports |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-docx | 1.2.0 (verified) | Read/write Word paragraph format, run font, style cascade | Only stable python OOXML library; already in use |
| pytest | installed | Test runner | Already in use; system python `/usr/bin/python3` |

### python-docx API Reference (VERIFIED)

**`Paragraph.style`** returns `_ParagraphStyle | None`. Style objects have `paragraph_format`, `font`, and `base_style` properties. [VERIFIED: python-docx 1.2.0 runtime]

**`_ParagraphStyle.base_style`** returns the parent style or `None` if the chain ends. [VERIFIED: runtime]

**`_ParagraphStyle.font`** returns a `Font` object giving character formatting at the style level. [VERIFIED: runtime]

**`_ParagraphStyle.paragraph_format`** returns a `ParagraphFormat` object at the style level. [VERIFIED: runtime]

**`Font` properties (all tri-state: value | None = inherited):** [VERIFIED: python-docx 1.2.0 source + runtime]
- `name: str | None` — typeface name; `None` = inherited
- `size: Length | None` — font height in EMU; `None` = inherited; use `.pt` for points
- `bold: bool | None` — `None` = inherited
- `italic: bool | None` — tri-state
- `underline: bool | WD_UNDERLINE | None` — `None` = inherited; `True` = single; `False` = none; `WD_UNDERLINE` enum for other styles
- `all_caps: bool | None` — `None` = inherited; `True` = all caps active
- `color: ColorFormat` — never None; `.type` is `MSO_COLOR_TYPE.RGB | .THEME | .AUTO | None`; `.rgb` is `RGBColor | None`
- Setting any font property to `None` clears the direct override and restores inheritance [VERIFIED: runtime]

**`ParagraphFormat` properties (all tri-state: value | None = inherited):** [VERIFIED: runtime]
- `alignment: WD_ALIGN_PARAGRAPH | None` — `None` = inherited
- `first_line_indent: Length | None` — use `.cm` for cm
- `left_indent: Length | None`
- `right_indent: Length | None`
- `line_spacing: float | Length | None`
- `space_before: Length | None` — use `.pt` for points
- `space_after: Length | None`
- `keep_with_next: bool | None` — `None` = inherited
- `keep_together: bool | None` — `None` = inherited (`keep_lines_together` in D-02 maps to this)
- `page_break_before: bool | None`
- `widow_control: bool | None`
- Setting any property to `None` restores inheritance [VERIFIED: runtime]

**No Supporting Libraries Needed.** All 17 fields are accessible via python-docx 1.2.0 without lxml.

---

## Architecture Patterns

### System Architecture Diagram

```
DOCX file
    │
    ▼
extract_paragraph_block()               [src/io/block_extractor.py]
    │
    ├── existing 5 flat keys (unchanged)
    │
    └── classify_style(paragraph) == "heading"?
            │YES                       │NO
            ▼                         ▼
    _extract_heading_format_signature()   heading_format_signature = None
    [src/rules/style_signatures.py]
            │
            │  Pass 1: read paragraph_format / run.font directly
            │  Pass 2: walk base_style chain for inherited value
            │  Output: {field: {value, source}} for all 17 fields
            │
            ▼
    json.dumps(signature)   ← serialized to JSON string
            │
            ▼
    Row dict  →  DataFrame  →  CSV  →  predictions_csv
                                              │
                                              ▼
                                    audit_or_format_docx()
                                    [src/generate/inplace_formatter.py]
                                              │
                                              ▼
                                    apply_rules_to_paragraph()
                                    [src/rules/rule_engine.py]
                                              │
                                    sig = json.loads(row_data["heading_format_signature"])
                                              │
                                    for each heading_* rule:
                                        field = rule["parameter"]
                                        entry = sig[field]  # {value, source}
                                              │
                            ┌─────────────────┼─────────────────┐
                            │                 │                 │
                     source="direct"   source="inherited"  source="unset"
                            │                 │                 │
                     compare vs              compare vs       skip (no
                     expected_value         expected_value    value to check)
                            │                 │
                     mismatch?           mismatch?
                      YES→autofix         YES→review
                      NO→no_change        NO→no_change
                            │
                    apply_heading_scalar_fix()
                    (extends apply_scalar_fix with new params)
```

### Recommended Project Structure

No new directories needed. New/modified files:

```
src/
├── io/
│   └── block_extractor.py      # ADD heading_format_signature extraction (eager for heading rows)
├── rules/
│   ├── style_signatures.py     # ADD _extract_heading_format_signature, _resolve_inherited_value
│   ├── rule_engine.py          # MODIFY: apply_scalar_fix (10 new param branches),
│   │                           #   replace blanket heading guard with per-field source routing
│   ├── formatting_rules_v1.json # ADD ~15 new heading_* rules (3 existing updated in behavior)
│   └── profiles/
│       └── gost_7_32_2017.json # ADD heading_signature section (if profile carries targets)
│                               # OR embed expected_value in rule JSON (current pattern)
tests/
├── fixtures/
│   ├── heading_minimal.docx    # NEW hand-crafted fixture
│   └── _build_heading_minimal.py # NEW builder script
├── test_style_signatures.py    # ADD heading signature extraction tests
├── test_rule_engine.py         # ADD per-field source routing tests (replace blanket guard tests)
└── test_positive_docx_regression.py # EXTEND with heading-direct-fix invariant
```

### Pattern 1: Two-Pass Resolver

**What:** For each of 17 heading signature fields, check direct (paragraph) value first; if None, walk `base_style` chain.

**When to use:** Inside `_extract_heading_format_signature` for heading-classified paragraphs.

**Example:**
```python
# Source: verified via python-docx 1.2.0 runtime
def _resolve_inherited_value(style, attr_getter):
    """Walk base_style chain; return (value, source_style_name) or (None, 'unset')."""
    current = style
    while current is not None:
        val = attr_getter(current)
        if val is not None:
            return val, current.name
        current = getattr(current, 'base_style', None)
    return None, 'unset'

def _make_entry(direct_val, style, attr_getter):
    if direct_val is not None:
        return {"value": direct_val, "source": "direct"}
    inherited_val, _ = _resolve_inherited_value(style, attr_getter)
    if inherited_val is not None:
        return {"value": inherited_val, "source": "inherited"}
    return {"value": None, "source": "unset"}
```

### Pattern 2: Multi-Run Font Resolution

**What:** For font fields on a multi-run paragraph, take the first run with a non-None direct value.

**When to use:** Pass 1 of the resolver for all run.font fields.

**Example:**
```python
# Source: verified via python-docx 1.2.0 runtime
# Pass 1: find first run with non-None value
direct_val = None
for run in paragraph.runs:
    if run.text and run.text.strip():
        val = run.font.bold  # or .name, .size, etc.
        if val is not None:
            direct_val = val
            break
# Pass 2: if direct_val is None, walk style cascade
```

### Pattern 3: CSV Serialization

**What:** `heading_format_signature` is a nested dict; serialize to JSON string for CSV compatibility.

**When to use:** In `extract_paragraph_block` before returning the row dict.

**Example:**
```python
import json

# In extract_paragraph_block, for heading rows only:
sig = _extract_heading_format_signature(paragraph)
row["heading_format_signature"] = json.dumps(sig)  # compact JSON string

# In rule_engine, deserialize safely (row_data["heading_format_signature"] is str or NaN):
import math
raw = row_data.get("heading_format_signature")
if raw is None or (isinstance(raw, float) and math.isnan(raw)):
    sig = None
elif isinstance(raw, str) and raw:
    sig = json.loads(raw)
else:
    sig = None
```

### Pattern 4: Heading Scalar Fix (D-06)

**What:** Autofix direct override by either setting to expected value OR clearing to None.

**When to use:** `source="direct"` AND `value != expected_value`.

**Example:**
```python
# Clear-to-None semantics: setting to None restores style inheritance
# Verified: paragraph.paragraph_format.space_before = None removes direct override
# Verified: run.font.bold = None removes direct override
# apply_scalar_fix extension branches:
elif parameter == "right_indent_cm":
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
elif parameter == "caps":
    for run in paragraph.runs:
        if run.text:
            run.font.all_caps = bool(expected_value) if expected_value is not None else None
```

### Pattern 5: Explanation String Format (D-05)

**What:** Review explanation for inherited mismatches.

```python
explanation = f"heading_inherited_mismatch:field={field},actual={actual},expected={expected}"
```

Note: Whether cascade chain is included is Claude's Discretion. Recommendation: omit chain for now (keeps audit CSV readable).

### Fixture Builder Pattern

**What:** Phase 1/2 pattern — standalone script that builds the DOCX directly via python-docx API with no rule_engine imports. Committed as binary; builder script documents the intent.

**See:** `tests/fixtures/_build_bibliography_minimal.py` for the exact pattern to follow.

### Anti-Patterns to Avoid

- **Writing `None` directly via `apply_scalar_fix` when expected_value is 0.0:** `fmt.first_line_indent = Cm(0.0)` is valid and different from `None`. The `None` clear-path is for when we want to REMOVE a wrong direct override and let the style cascade apply. For heading_first_line_indent_cm expected_value=0.0, set `Cm(0.0)` not `None`.
- **Setting paragraph-level font without checking run existence:** If `paragraph.runs` is empty, iterating does nothing. Always guard.
- **Hard-coding expected_value in rule routing code:** Expected values belong in the rule JSON, not in the routing logic. The router reads `rule["expected_value"]`.
- **Importing rule_engine from the fixture builder:** The builder is the contract anchor for RED tests; it must be self-contained.
- **Calling `_extract_heading_format_signature` on every paragraph (including body_text):** D-01 says heading-only. The heading ratio is 3–8% in real docs. Lazy is correct; call only when `classify_style(paragraph) == "heading"`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Style cascade walk | Custom XML traversal via lxml | `paragraph.style.base_style` chain (D-03) | python-docx wraps the OOXML correctly; lxml raw traversal is fragile across Word versions |
| Color comparison | Custom hex string compare | `run.font.color.rgb` returns `RGBColor` or `None`; compare directly | RGBColor implements `__eq__`; `None` means no color (transparent/auto) |
| "Direct vs inherited" detection | Heuristics on text content | `attribute is None` on python-docx objects | `None` is the explicit API contract for "inherited, not set directly" |
| Heading detection | Extra regex or property walking | `classify_style(paragraph)` from Phase 1 | Already accounts for EN+RU locale; consistent with rule engine |
| CSV round-trip | Custom serialization format | `json.dumps` / `json.loads` | pandas-safe; NaN guard handles non-heading rows gracefully |

---

## Runtime State Inventory

> Omitted — greenfield additions only; no rename/refactor/migration.

---

## Common Pitfalls

### Pitfall 1: Blanket Heading Guard in `_apply_scalar_rule` Must Be Removed

**What goes wrong:** The existing guard at lines 998–1004 of `rule_engine.py` unconditionally sets `manual_review_required=True` for any heading-labeled paragraph with a heading style. If Phase 3 adds new `heading_*` rules without removing this guard, ALL heading rules (including D-06 direct-fix cases) will go to review — D-06 autofix will never fire.

**Why it happens:** Phase 1 installed a blanket guard because there was no source discrimination. Phase 3 replaces it with per-field source routing.

**How to avoid:** In Plan 03-02 (GREEN), the first task is to remove the lines `if label in {"title_section", "title_subsection"} and _paragraph_has_heading_style(paragraph): return {...manual_review_required=True...}` from `_apply_scalar_rule`. Replace with the new per-field source check inside the heading rule dispatcher.

**Warning signs:** Tests for D-06 (direct-mismatch → autofix) return `status="review"` instead of `status="changed"`.

### Pitfall 2: Existing Tests `test_inherited_heading_bold_requires_review_not_autofix` and `test_heading_style_direct_alignment_requires_review_not_autofix` Will Change Behavior

**What goes wrong:** These tests currently pass because the blanket guard fires. After Phase 3 replaces the guard, these tests may need updating — `test_inherited_heading_bold_requires_review_not_autofix` tests source=inherited (D-05 → still review, test stays valid), but `test_heading_style_direct_alignment_requires_review_not_autofix` sets `paragraph.alignment = 1` as a PARAGRAPH-LEVEL direct override — which will be source=direct in Phase 3 (D-06 → autofix). The test asserts `result["status"] == "review"` which will become `"changed"`. Plan must explicitly update this test.

**How to avoid:** In Wave 0 RED, rewrite the direct-alignment test to assert `status="changed"` (D-06 path). Add a new test for inherited-alignment → `status="review"` (D-05 path).

### Pitfall 3: Heading Signature Extraction Must Be Eager at Extraction Time, Not at Rule Engine Time

**What goes wrong:** If signature extraction happens inside `apply_rules_to_paragraph`, the rule engine never wrote the signature to the CSV, so the audit CSV lacks it for post-hoc analysis.

**Why it happens:** The natural implementation instinct is to compute it where it is needed (rule engine). But the pipeline architecture requires all block metadata to be in the CSV.

**How to avoid:** `heading_format_signature` is computed in `extract_paragraph_block`, serialized to JSON string, lands in the CSV column, then deserialized in `apply_rules_to_paragraph`. For non-heading rows the column contains empty/NaN. This is D-01 as stated.

### Pitfall 4: `space_before` and `space_after` Stored as `Length` (EMU), Not Points

**What goes wrong:** `paragraph.paragraph_format.space_before` returns a `Length` object (EMU), not a float. Comparing against `expected_value=0.0` (points) without conversion yields wrong results.

**Root cause:** Current `get_current_paragraph_profile` correctly converts via `.pt`. The heading signature resolver must do the same: `space_before_pt = fmt.space_before.pt if fmt.space_before is not None else None`.

**How to avoid:** Always convert Length to pt (for space_before/after) or cm (for indents) immediately on extraction. Never store raw Length objects in the signature.

### Pitfall 5: `font.size` in EMU Needs `.pt` Conversion

**What goes wrong:** `run.font.size` returns Length in EMU (203200 for 16pt). Comparing against `expected_value=16.0` directly fails.

**How to avoid:** Extract as `font_size_pt = run.font.size.pt if run.font.size is not None else None`.

### Pitfall 6: `color` Field May Be Unusable for GOST Rules

**What goes wrong:** GOST-decorated positive headings have `font.color.type=None` (no color set — Word's "Automatic" color inherits from theme). If a heading rule checks color, it will always produce `source="inherited"` → review. This is correct behavior but means the color rule will NEVER autofix anything — it is a review-only signal.

**Researcher recommendation:** Include `color` in the signature (D-02 requires it), but in `formatting_rules_v1.json` set `autocorrect: false` for `heading_color` rule since color checks are inherently review-only in the current corpus.

### Pitfall 7: Positive Corpus Gate Is Safe IF D-05 Routing Is Correct

**What goes wrong:** If the source-routing logic accidentally classifies `source="direct"` for fields that are actually inherited (None at paragraph level), D-06 would fire on positive docs → gate fails.

**Root cause:** The condition for "direct" is simply `direct_val is not None`. If `paragraph.paragraph_format.X` returns a non-None value even for inherited-from-style fields, the routing would be wrong. This is NOT an issue — confirmed empirically: all 5 sampled positive headings in 1.docx and 4.docx have ALL direct values as None for all relevant fields.

**Warning signs:** `test_positive_docx_examples_are_not_autofixed` fails with `heading_*` in `applied_fixes`.

### Pitfall 8: `line_spacing` Format — Float Ratio vs `Length`

**What goes wrong:** `paragraph.paragraph_format.line_spacing` returns a `float` (line multiple) for proportional spacing (e.g., 1.5) but a `Length` object for absolute spacing. The heading signature should normalize to a float, not return the raw value.

**How to avoid:** Use the same pattern as `get_current_paragraph_profile` in rule_engine.py: `line_spacing_value = round(float(line_spacing), 3) if isinstance(line_spacing, (int, float)) else None`.

---

## Code Examples

### Heading Signature Extractor

```python
# Computed in extract_paragraph_block; helper in style_signatures.py
# Source: verified via python-docx 1.2.0 runtime + Phase 1/2 code patterns

def _extract_heading_format_signature(paragraph) -> dict:
    """Two-pass resolver (D-03) for all 17 heading signature fields."""
    fmt = paragraph.paragraph_format
    style = paragraph.style

    def _walk_style_font(attr: str):
        s = style
        while s is not None:
            val = getattr(s.font, attr, None)
            if val is not None:
                return val
            s = getattr(s, 'base_style', None)
        return None

    def _walk_style_pf(attr: str):
        s = style
        while s is not None:
            val = getattr(s.paragraph_format, attr, None)
            if val is not None:
                return val
            s = getattr(s, 'base_style', None)
        return None

    def _tagged(direct_val, inherited_getter):
        if direct_val is not None:
            return {"value": direct_val, "source": "direct"}
        inherited = inherited_getter()
        if inherited is not None:
            return {"value": inherited, "source": "inherited"}
        return {"value": None, "source": "unset"}

    # --- Font fields (Pass 1: first run with non-None value) ---
    direct_font_name = None
    direct_font_size = None
    direct_bold = None
    direct_italic = None
    direct_underline = None
    direct_color_rgb = None
    direct_caps = None

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
                direct_underline = run.font.underline  # bool or WD_UNDERLINE
            if direct_color_rgb is None and run.font.color.type is not None:
                direct_color_rgb = str(run.font.color.rgb) if run.font.color.rgb else "auto"
            if direct_caps is None and run.font.all_caps is not None:
                direct_caps = bool(run.font.all_caps)

    # --- Paragraph scalar fields (Pass 1: direct read) ---
    direct_align = paragraph.alignment  # WD_ALIGN_PARAGRAPH or None
    direct_first_line = round(fmt.first_line_indent.cm, 3) if fmt.first_line_indent is not None else None
    direct_left = round(fmt.left_indent.cm, 3) if fmt.left_indent is not None else None
    direct_right = round(fmt.right_indent.cm, 3) if fmt.right_indent is not None else None
    ls = fmt.line_spacing
    direct_line_spacing = round(float(ls), 3) if isinstance(ls, (int, float)) else None
    direct_space_before = round(fmt.space_before.pt, 3) if fmt.space_before is not None else None
    direct_space_after = round(fmt.space_after.pt, 3) if fmt.space_after is not None else None

    # --- Flow flags (Pass 1: direct read) ---
    direct_kwn = fmt.keep_with_next
    direct_klt = fmt.keep_together
    direct_pbb = fmt.page_break_before
    direct_wc = fmt.widow_control

    # Build entries
    return {
        "font_name": _tagged(direct_font_name, lambda: _walk_style_font("name")),
        "font_size": _tagged(direct_font_size,
            lambda: round(style.font.size.pt, 3) if (_walk_style_font("size")) else None
            # simplified; real code uses _walk_style_font
        ),
        "bold": _tagged(direct_bold, lambda: _walk_style_font("bold")),
        "italic": _tagged(direct_italic, lambda: _walk_style_font("italic")),
        "underline": _tagged(direct_underline, lambda: _walk_style_font("underline")),
        "color": _tagged(direct_color_rgb, lambda: None),  # No style-level color in typical docs
        "caps": _tagged(direct_caps, lambda: _walk_style_font("all_caps")),
        "alignment": _tagged(
            ALIGNMENT_MAP.get(direct_align) if direct_align is not None else None,
            lambda: ALIGNMENT_MAP.get(_walk_style_pf("alignment"))
        ),
        "first_line_indent_cm": _tagged(direct_first_line,
            lambda: round(_walk_style_pf("first_line_indent").cm, 3) if _walk_style_pf("first_line_indent") else None),
        # ... remaining 8 fields follow same pattern ...
        "keep_with_next": _tagged(direct_kwn, lambda: _walk_style_pf("keep_with_next")),
        "keep_lines_together": _tagged(direct_klt, lambda: _walk_style_pf("keep_together")),
        "page_break_before": _tagged(direct_pbb, lambda: _walk_style_pf("page_break_before")),
        "widow_control": _tagged(direct_wc, lambda: _walk_style_pf("widow_control")),
    }
```

### Existing Behavior of Positive Corpus (VERIFIED)

From runtime sampling of `positive_examples/1.docx` and `4.docx`:
- All 22 sampled heading paragraphs: ALL direct values are `None`
- Style-level values (from Heading 1 style cascade):
  - `font.size` = 18.0 pt, `font.bold` = True (Heading 1 in 1.docx and 4.docx)
  - `alignment` = LEFT (both docs)
  - `keep_with_next` = True, `keep_together` = True (Heading 1)
  - `space_after` ≈ 28.35 pt (NOT 10.0 pt from gost profile — inherited mismatch → review only)
- All positive headings → `source="inherited"` for all fields → D-05 → review only → `applied_fixes=[]`

### Rule JSON Shape (D-09)

```json
{
  "id": "heading_font_size",
  "applicable_labels": ["title_section", "title_subsection"],
  "parameter": "font_size",
  "expected_value": 18.0,
  "action": "fix",
  "severity": "high",
  "autocorrect": true,
  "priority": 50
}
```

Note: `parameter` name maps to `heading_format_signature[parameter]`. Rule engine looks up `sig[rule["parameter"]]` to get `{value, source}`.

The `heading_font_size` rule must use `parameter="font_size"` (not `font_size_pt`) to match the signature key name. The existing `heading_bold` rule uses `parameter="bold"` — this is consistent.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Blanket `heading_has_style` → review for all heading-label scalar rules | Per-field source routing: direct→autofix, inherited→review | Phase 3 | Enables D-06 safe autofixes on direct overrides |
| `heading_alignment`, `heading_indent`, `heading_bold` rules with blanket block | Same rules, now discriminated by source | Phase 3 | Existing rules gain correct behavior |

**Deprecated/outdated:**
- The blanket guard `if label in {"title_section", "title_subsection"} and _paragraph_has_heading_style(paragraph): return {manual_review_required: True}` in `_apply_scalar_rule` (line 998–1004): remove in Phase 3 GREEN plans.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `space_after` in Heading 1 style being 28.35 pt (not 10.0 pt from gost profile) means inherited mismatch → review, so positive corpus stays `changed=0` for `heading_space_after_pt` rule | Common Pitfalls / Corpus Sampling | Low — confirmed on 2 positive docs; if other positive docs have direct overrides on space_after, D-06 would fire → gate failure. Mitigated by D-07 gate. |
| A2 | Flow flags (`keep_with_next`, `keep_together`) on positive headings are all `None` at paragraph level (inherited) | VERIFIED: runtime corpus sampling | No risk — confirmed directly |
| A3 | `heading_color` rule should have `autocorrect: false` because color in positive headings is always `source="inherited"` from no-color-set state | Pitfall 6 | Low — worst case: color rule fires review noise. No autofix would occur since source=inherited → D-05. |
| A4 | `heading_caps` should use `font.all_caps` flag, not `text == text.upper()` heuristic | Claude's Discretion item | Low — `font.all_caps` is the correct API; text heuristic is unreliable for mixed case. Planner should resolve as `font.all_caps`. |

---

## Open Questions (RESOLVED)

1. **Expected values for heading rules: embedded in rule JSON vs read from profile**
   - What we know: Current pattern (all existing rules) embeds expected_value in rule JSON. CONTEXT.md D-09 says "profile-driven expected_value." The GOST profile has `title_section.style_profile` but it lacks heading signature fields (keep_with_next, right_indent_cm, caps, etc.).
   - What's unclear: Should heading signature targets be added to `gost_7_32_2017.json` under a new key (e.g., `labels.title_section.heading_signature`), or embedded in each heading rule's `expected_value`?
   - Recommendation: **Embed in rule JSON** for Phase 3 (consistent with existing pattern; simpler; Phase 5 owns profile-selectability). Add a `heading_signature` key to the profile ONLY if the planner wants Phase 5 to override values without modifying rule JSON.
   - **RESOLVED:** Embed `expected_value` in rule JSON for Phase 3 (consistent with existing pattern). Phase 5 owns profile-selectability — that work will introduce a `labels.<label>.heading_signature` block in the profile and a runtime lookup path. Pinned in Plan 03-03 Task 1 (rule JSON) and SUMMARY hand-off.

2. **Level-specific expected_value for title_section vs title_subsection**
   - What we know: `gost_7_32_2017.json` has `font_size_pt=18` for title_section and `font_size_pt=16` for title_subsection.
   - What's unclear: A single `heading_font_size` rule with `applicable_labels: ["title_section", "title_subsection"]` cannot carry two different expected_values.
   - Recommendation: **Two separate rules** for level-sensitive fields: `heading_section_font_size` (expected=18.0, labels=[title_section]) and `heading_subsection_font_size` (expected=16.0, labels=[title_subsection]). OR a single rule that reads expected_value from `profile.labels[label].style_profile.font_size_pt` at runtime. **Simpler: two rules per level-sensitive field.** This avoids a new lookup path in the rule engine and keeps the JSON readable.
   - **RESOLVED:** Two rules per level-sensitive field. `font_size` → `heading_section_font_size` (expected=18.0, labels=[title_section]) + `heading_subsection_font_size` (expected=16.0, labels=[title_subsection]). `space_before_pt` → `heading_section_space_before_pt` (expected=0.0, labels=[title_section]) + `heading_subsection_space_before_pt` (expected=15.0, labels=[title_subsection]). Fields without GOST-defined targets (right_indent_cm, keep_with_next, keep_lines_together, page_break_before, widow_control, caps, font_name, italic, underline) load with `expected_value=null` and `autocorrect=false` (load+skip pattern — dispatcher continues when expected is None). Pinned in Plan 03-03 Task 1 and Plan 03-01 Task 3 schema-presence test.

3. **What to do with `heading_alignment` and `heading_indent` existing rules**
   - What we know: They exist in `formatting_rules_v1.json` and already work with the new label. Their routing behavior (currently blanket → review) changes after the guard is removed.
   - What's unclear: Do they need renaming? No. Their `parameter` field matches the signature key names (`alignment`, `first_line_indent_cm`) so they naturally integrate with the new routing.
   - Recommendation: Keep `id: "heading_alignment"` and `id: "heading_indent"` — just update routing behavior by removing the blanket guard. No rule JSON change needed for these 3.
   - **RESOLVED:** Keep existing rule IDs `heading_alignment`, `heading_indent`, `heading_bold` byte-identical (no rename, no reorder, no field changes). Behavior changes solely via removal of the blanket heading guard at lines 998-1004 of `src/rules/rule_engine.py` (Plan 03-03 Task 2). Pinned in Plan 03-03 Task 1 acceptance criteria ("existing 3 heading rules byte-identical").

---

## Environment Availability

> Phase 3 has no external service dependencies beyond python-docx (already installed) and pytest (already installed).

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python-docx | All DOCX operations | ✓ | 1.2.0 | — |
| /usr/bin/python3 | Test runner | ✓ | system python | — |
| pytest | Tests | ✓ | installed | — |
| positive_examples/1.docx | D-07 regression gate | ✓ | — | pytest.skip |
| positive_examples/4.docx | D-07 regression gate | ✓ | — | pytest.skip |

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (installed, system python) |
| Config file | none (run directly) |
| Quick run command | `/usr/bin/python3 -m pytest tests/test_style_signatures.py tests/test_rule_engine.py -x -q` |
| Full suite command | `/usr/bin/python3 -m pytest tests/test_style_signatures.py tests/test_rule_engine.py tests/test_positive_docx_regression.py tests/test_negative_corpus_diff_rate.py tests/test_postprocess_rules.py tests/test_profile_loader.py tests/test_bibliography_phase2.py -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-heading-style-signature / D-01 | `extract_paragraph_block` adds `heading_format_signature` JSON string key | unit | `pytest tests/test_style_signatures.py::test_heading_signature_key_present -x` | ❌ Wave 0 |
| D-03 / D-04 | Pass 1: direct=None on inherited heading → `source="inherited"` | unit | `pytest tests/test_style_signatures.py::test_heading_signature_direct_none_is_inherited -x` | ❌ Wave 0 |
| D-03 / D-04 | Pass 1: direct override on heading paragraph → `source="direct"` | unit | `pytest tests/test_style_signatures.py::test_heading_signature_direct_override_detected -x` | ❌ Wave 0 |
| D-03 | Pass 2: base_style chain walk resolves inherited value | unit | `pytest tests/test_style_signatures.py::test_heading_signature_cascade_walk -x` | ❌ Wave 0 |
| D-05 | Inherited mismatch → `status="review"`, `applied_fixes=[]` | unit | `pytest tests/test_rule_engine.py::test_heading_inherited_mismatch_routes_to_review -x` | ❌ Wave 0 |
| D-06 | Direct mismatch → `status="changed"`, field in `applied_fixes` | unit | `pytest tests/test_rule_engine.py::test_heading_direct_mismatch_routes_to_autofix -x` | ❌ Wave 0 |
| D-06 | Direct match (value correct) → `status="no_change"` | unit | `pytest tests/test_rule_engine.py::test_heading_direct_match_no_change -x` | ❌ Wave 0 |
| D-07 | GOST positive corpus stays `changed=0` for heading rules | integration | `pytest tests/test_positive_docx_regression.py -x` | ✅ (needs extension) |
| D-10 | Fixture: positive heading → zero changes | unit/integration | `pytest tests/test_rule_engine.py::test_heading_minimal_positive_zero_fixes -x` | ❌ Wave 0 |
| D-10 | Fixture: direct-override heading → autofixed (D-06) | unit/integration | `pytest tests/test_rule_engine.py::test_heading_minimal_direct_fix -x` | ❌ Wave 0 |
| D-10 | Fixture: inherited-mismatch heading → review only (D-05) | unit/integration | `pytest tests/test_rule_engine.py::test_heading_minimal_inherited_review -x` | ❌ Wave 0 |
| D-09 | 18 heading rules present in formatting_rules_v1.json | schema | `pytest tests/test_rule_engine.py::test_heading_rules_present_in_schema -x` | ❌ Wave 0 |
| Regression | Negative corpus diff-rate gate | integration | `pytest tests/test_negative_corpus_diff_rate.py -x` | ✅ |

### Sampling Rate
- **Per task commit:** `/usr/bin/python3 -m pytest tests/test_style_signatures.py tests/test_rule_engine.py -x -q`
- **Per wave merge:** Full suite command above
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_style_signatures.py` — add heading signature extraction tests (4+ tests above)
- [ ] `tests/test_rule_engine.py` — add D-05/D-06 routing tests (6+ tests above); update `test_heading_style_direct_alignment_requires_review_not_autofix` to assert `status="changed"` (D-06 behavior after blanket guard removed)
- [ ] `tests/fixtures/heading_minimal.docx` — hand-crafted fixture (4 paragraphs per D-10)
- [ ] `tests/fixtures/_build_heading_minimal.py` — builder script
- [ ] `tests/test_positive_docx_regression.py` — extend with heading-direct-fix invariant assertion

---

## Security Domain

> Phase 3 is a backend rule extension with no new user input surfaces, no new API endpoints, no authentication changes. `security_enforcement` not configured in `.planning/config.json`.

ASVS categories: V5 Input Validation applies to `heading_format_signature` JSON deserialization. Use `json.loads` (safe); never `eval`. All other ASVS categories do not apply.

---

## Sources

### Primary (HIGH confidence)
- python-docx 1.2.0 runtime — ALL API claims about Font, ParagraphFormat, style.base_style, ColorFormat verified via direct runtime introspection on the project's installed library
- `src/rules/rule_engine.py` — existing `apply_scalar_fix`, `_apply_scalar_rule`, `apply_rules_to_paragraph` read directly from codebase
- `src/io/block_extractor.py` — `extract_paragraph_block` structure verified directly
- `src/rules/style_signatures.py` — `classify_style`, `HEADING_STYLE_RE`, `paragraph_has_heading_style` verified directly
- `src/rules/formatting_rules_v1.json` — existing heading rules verified directly
- `src/rules/profiles/gost_7_32_2017.json` — profile structure verified directly
- `tests/fixtures/_build_bibliography_minimal.py` — fixture builder pattern verified directly
- `tests/test_rule_engine.py` — existing heading tests (5 tests) verified via pytest run
- `positive_examples/1.docx`, `4.docx` — corpus sampling verified directly via python-docx runtime

### Secondary (MEDIUM confidence)
- CONTEXT.md D-01 through D-10 — user locked decisions

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — python-docx 1.2.0 verified at runtime; all API claims tested directly
- Architecture: HIGH — derived from direct codebase reading + runtime verification
- Pitfalls: HIGH — Pitfall 1 (blanket guard) confirmed via code read; Pitfall 2 (test update needed) confirmed via test source; Pitfalls 3–8 confirmed via runtime experiments
- Expected values for new rules: MEDIUM — gost profile has font_size/bold/alignment; others (right_indent, keep_with_next, etc.) not yet confirmed against GOST standard values

**Research date:** 2026-05-12
**Valid until:** 2026-06-12 (python-docx API is stable; 30 days appropriate)
