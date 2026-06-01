# Phase 2: Bibliography & list semantics - Pattern Map

**Mapped:** 2026-05-12
**Files analyzed:** 12 (3 new + 9 modified)
**Analogs found:** 12 / 12

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/postprocess/postprocess_rules.py` (MOD) | postprocess/dataframe transform | batch | itself (lines 110-206) + `_is_bibliography_title` already in file | exact (in-place extension) |
| `src/rules/rule_engine.py` — D-05 `_create_bibliography_multilevel_abstract` (NEW fn) | rule-engine/OOXML emitter | transform (Python→XML) | `_create_section_abstract_num_id` (lines 303-335) | exact (sibling, same idiom) |
| `src/rules/rule_engine.py` — D-05 `_create_bibliography_num_with_section_override` (NEW fn) | rule-engine/OOXML emitter | transform | `_create_section_abstract_num_id` + `_next_num_id` (lines 294-300) | role-match |
| `src/rules/rule_engine.py` — D-07 `_seed_bibliography_num_ids_from_doc` + key change (MOD) | rule-engine/cache seeding | document scan | `_get_bibliography_num_id` (lines 367-388) | exact (replaces same fn) |
| `src/rules/rule_engine.py` — D-06 first-valid-numId coercion (MOD inside `_apply_bibliography_rules` / `apply_bibliography_numbering`) | rule-engine/business logic | request-response | `apply_bibliography_numbering` (lines 409-429) + `bibliography_numbering_matches` (338-364) | exact |
| `src/rules/rule_engine.py` — D-09 ambiguous-list review branch (NEW in `apply_rules_to_paragraph`) | rule-engine/routing | request-response | Phase 1 style guard (lines 786-798) | exact (sibling branch) |
| `src/rules/rule_engine.py` — D-11 profile threading + delete `MAX_FALLBACK_LIST_*` (MOD) | rule-engine/config injection | request-response | `default_font_name` kwarg threading at line 777 + `_is_long_plain_paragraph` (line 546) | exact |
| `src/rules/rule_engine.py` — D-13 `apply_bibliography_format` profile-driven scalars (MOD) | rule-engine/business logic | transform | itself lines 230-265 (existing `for field in scalar_fields: if field not in config: continue`) | exact (already structurally correct; only `expected_value` source changes) |
| `src/rules/profile_loader.py` — D-11 helper getter (NEW fn) | profile/config loader | request-response | `get_target_style_profile` (lines 165-170) + `get_audit_policy` (173-175) | exact |
| `src/rules/profile_validator.py` — D-03 + D-11 schema extension (MOD) | profile/schema validator | validation | `validate_profile` (lines 40-86) — existing `style_profile` field-type check loop | exact |
| `src/rules/profiles/gost_7_32_2017.json` (MOD) | config/data | static | existing top-level sections `numbering_rules` (line 276) and `bibliography_rules` (line 294) | exact (extends existing top-level keys) |
| `tests/fixtures/_build_bibliography_minimal.py` (NEW) | fixture builder | file-I/O | `tests/fixtures/_build_style_guard_minimal.py` | exact (explicit mirror) |
| `tests/fixtures/bibliography_minimal.docx` (NEW) | binary fixture | static | `tests/fixtures/style_guard_minimal.docx` | exact |
| `tests/test_bibliography_phase2.py` (NEW) | test | unit + integration | `tests/test_rule_engine.py` (style-guard family lines 1124-1362) + bibliography family (355-1122) | exact |
| `tests/test_postprocess_rules.py` (MOD/extend) | test | unit | itself, `test_bibliography_context_overrides_body_text_and_list_predictions` (line 76) | exact |
| `tests/test_profile_loader.py` (NEW) | test | unit | inline tests in `test_rule_engine.py::test_caption_profiles_require_review_not_autofix` (line 60) | role-match |
| `src/evaluation/format_regression_audit.py` (READ only — keep regex import) | evaluation/harness | batch | itself (lines 40-58) | n/a — preserved unchanged |

## Pattern Assignments

### `src/postprocess/postprocess_rules.py` — D-01 unconditional override + D-04 position+heading detection

**Analog:** same file, `apply_postprocess_rules` (lines 110-206). Two distinct insertion points — D-01 is a new pre-pass; D-04 rewrites the existing `in_bibliography` loop body.

**D-01 insertion point** (pre-pass at line 128, BEFORE the body_text/list_item rewrite at line 130):
```python
# NEW first pass — D-01 unconditional override
for position in range(len(labels)):
    if _is_bibliography_title(texts[position]):
        labels[position] = "bibliography_title"
# Then run the existing body_text/list_item, list-intro, bibliography-context passes as today.
```

**D-04 detection pattern** (REPLACE existing loop body at lines 160-181). Copy outer-loop shape from existing code; replace the `_is_bibliography_subheading(text)` gate with style classification:

Existing shape to preserve (lines 160-181):
```python
in_bibliography = False
bibliography_section_index = 0
for position, (_, row) in enumerate(group.iterrows()):
    text = texts[position]
    label = labels[position]
    if _is_bibliography_title(text):
        labels[position] = "bibliography_title"
        in_bibliography = True
        continue
    if in_bibliography and _stops_bibliography_context(text, label):
        in_bibliography = False
    if not in_bibliography:
        continue
    if _is_bibliography_subheading(text):
        if _is_numbered_bibliography_subheading(text):
            bibliography_section_index += 1
        if label not in {"title_section", "title_subsection"}:
            labels[position] = "bibliography_title"
        section_indices[position] = bibliography_section_index or None
    elif label in {"body_text", "list_item"} and _looks_like_bibliography_entry(row, text):
        labels[position] = "bibliography_item"
        section_indices[position] = bibliography_section_index or None
```

New gate (researcher Example B, kept fallback regex per Open Question 2):
- Introduce row-string-based `_row_style_class(row)` helper that applies `HEADING_STYLE_RE / TOC_STYLE_RE / CAPTION_STYLE_RE / LIST_STYLE_RE` from `src/rules/style_signatures.py` to `row.get("style")`. Order MUST match `classify_style`: TOC → heading → caption → list → body. Try/except → "body" idiom (mirror of `classify_style` lines 30-45).
- Subsection trigger = `style_class == "heading"` OR `_is_bibliography_subheading(text)` (fallback).
- Always increment `bibliography_section_index` on each subsection heading (drop the `_is_numbered_bibliography_subheading` precondition — Heading 1 style is the canonical signal now).

**Imports to add:**
```python
from src.rules.style_signatures import HEADING_STYLE_RE, TOC_STYLE_RE, CAPTION_STYLE_RE, LIST_STYLE_RE
```
(Do NOT import `classify_style` itself — `classify_style` takes a `Paragraph`, not a row string. Compose a row-shaped helper.)

**Critical preservation:** `BIBLIOGRAPHY_SUBHEADING_RE`, `BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE`, and `_is_bibliography_subheading` MUST stay in the module — `src/evaluation/format_regression_audit.py:19-22, 50-51` imports `BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE` and the fallback path of D-04 keeps using `_is_bibliography_subheading`.

---

### `src/rules/rule_engine.py` — D-05 2-level abstract emission (NEW)

**Analog:** `_create_section_abstract_num_id` (lines 303-335) — exact same idiom (allocate id, append children via `OxmlElement` + `qn`, attach to numbering_root).

**Imports already in place** (rule_engine.py:6-10):
```python
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph
```

**OxmlElement-build pattern to copy** (legacy at lines 303-335):
```python
def _create_section_abstract_num_id(numbering_root, section_index: int) -> str:
    abstract_num_id = _next_abstract_num_id(numbering_root)

    abstract_num = OxmlElement("w:abstractNum")
    abstract_num.set(qn("w:abstractNumId"), str(abstract_num_id))

    multi_level_type = OxmlElement("w:multiLevelType")
    multi_level_type.set(qn("w:val"), "singleLevel")
    abstract_num.append(multi_level_type)

    level = OxmlElement("w:lvl")
    level.set(qn("w:ilvl"), "0")

    start = OxmlElement("w:start"); start.set(qn("w:val"), "1"); level.append(start)
    num_fmt = OxmlElement("w:numFmt"); num_fmt.set(qn("w:val"), "decimal"); level.append(num_fmt)
    level_text = OxmlElement("w:lvlText"); level_text.set(qn("w:val"), f"{section_index}.%1"); level.append(level_text)
    level_jc = OxmlElement("w:lvlJc"); level_jc.set(qn("w:val"), "left"); level.append(level_jc)

    abstract_num.append(level)
    numbering_root.append(abstract_num)
    return str(abstract_num_id)
```

**Two new sibling functions to write** (per researcher Example C):
1. `_create_bibliography_multilevel_abstract(numbering_root) -> str` — emits ONE abstract per document with `multiLevelType="multilevel"` and TWO `w:lvl` children (`ilvl=0` lvlText=`"%1."`, `ilvl=1` lvlText=`"%1.%2."`). No `section_index` baked into lvlText (decoupled).
2. `_create_bibliography_num_with_section_override(numbering_root, abstract_num_id, section_index) -> int` — ONE `w:num` per subsection. Each `w:num` carries:
   - `<w:abstractNumId w:val="N"/>` referencing the shared abstract
   - `<w:lvlOverride w:ilvl="0"><w:startOverride w:val="<section_index>"/></w:lvlOverride>`
   - `<w:lvlOverride w:ilvl="1"><w:startOverride w:val="1"/></w:lvlOverride>` (entry counter reset)

**Anti-pattern (researcher):** do NOT edit `_create_section_abstract_num_id` in place. Leave it; bibliography path stops calling it.

**Pitfall 2 binding:** Per-subsection `w:num` with TWO `lvlOverride` children is mandatory — without them Word does not reset the level-1 counter across subsections (no level-0 paragraph between them).

---

### `src/rules/rule_engine.py` — D-06 first-valid-numId coercion + `applied_fixes` tag

**Analog:** existing `apply_bibliography_numbering` (lines 409-429) and `bibliography_numbering_matches` (338-364).

**Existing numPr write pattern to extend** (lines 409-429):
```python
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
```

**Phase 2 changes:**
1. `ilvl.set(qn("w:val"), "0")` → `"1"` (D-05: bibliography entries live at level 1).
2. Return value gains `"numbering:coerced_to_numId=<N>"` when this paragraph is being coerced away from a different existing numId — gate on "paragraph already had a numPr with a different numId before this call". Append both `"numbering"` and the coercion tag.
3. `_get_bibliography_num_id` now returns the seeded/coerced numId via D-07's scan.

**`applied_fixes` tag convention** (D-09 mirrors same `<category>:<detail>` shape — see code_context line 132): emit `"numbering:coerced_to_numId=<N>"` so audit explains the change. Mirrors `style_guard_block:` shape from Phase 1.

---

### `src/rules/rule_engine.py` — D-07 idempotent seed + stable cache key

**Analog:** existing `_get_bibliography_num_id` (lines 367-388) — replace in place.

**Existing cache key** (line 369): `root_key = (id(numbering_root), section_index)` — leaky across documents.

**Replacement contract:**
```python
_BIBLIOGRAPHY_NUM_IDS: dict[tuple[int, int | None], int] = {}  # key changes to (doc_key, section_index)
_SEEDED_DOCS: set[int] = set()  # NEW

def _document_cache_key(paragraph: Paragraph) -> int:
    return id(paragraph.part.document.part)

def _seed_bibliography_num_ids_from_doc(paragraph: Paragraph) -> None:
    """Walk body in document order, group existing numIds on bibliography_item
    paragraphs by section_index (inferred from paragraph order — first heading
    inside biblio context = section 1, second = 2, ...). First valid numId per
    section seeds _BIBLIOGRAPHY_NUM_IDS[(doc_key, section_index)]."""
    # implementation: iterate paragraph.part.document.element.body.iter(qn("w:p"))
    ...

def _get_bibliography_num_id(paragraph: Paragraph, section_index: int | None = None) -> int:
    doc_key = _document_cache_key(paragraph)
    if doc_key not in _SEEDED_DOCS:
        _seed_bibliography_num_ids_from_doc(paragraph)
        _SEEDED_DOCS.add(doc_key)
    root_key = (doc_key, section_index)
    if root_key in _BIBLIOGRAPHY_NUM_IDS:
        return _BIBLIOGRAPHY_NUM_IDS[root_key]
    # otherwise allocate: shared multilevel abstract (once per doc) + per-subsection w:num
    ...
```

**Existing `_num_id_exists` (line 148) and `paragraph_numbering_reference_is_valid` (line 156)** are the "valid numId" oracle for D-06 coercion. Per Open Question 3 (researcher recommendation), strengthen "valid" to ALSO require the abstractNum has `multiLevelType=multilevel` + lvl-1 lvlText==`"%1.%2."` so legacy singleLevel numIds don't poison idempotency.

**Pitfall 1 binding:** key change `id(numbering_root) → id(paragraph.part.document.part)`. The document.part reference lives in `paragraph._parent._part` and survives as long as the Document object — no `id()` reuse during the same Python process.

---

### `src/rules/rule_engine.py` — D-09 ambiguous-list review branch (NEW)

**Analog:** Phase 1 style guard inside `apply_rules_to_paragraph` (lines 786-798).

**Style guard pattern to mirror** (lines 786-798):
```python
paragraph_style_class = classify_style(paragraph)
if label == "body_text" and paragraph_style_class != "body":
    return {
        "status": "review",
        "violated_rules": [],
        "applied_fixes": [],
        "suggested_fixes": [],
        "suggested_rule_ids": [],
        "manual_review_required": True,
        "blocked_unsafe_autofix": False,
        "unsafe_auto_fix_reason": "",
        "explanation": f"style_guard_block: rule_class=body_text paragraph_style_class={paragraph_style_class}",
    }
```

**New D-09 branch to add IMMEDIATELY AFTER the style guard, BEFORE `current_profile = get_current_paragraph_profile(...)` at line 800.** Reuse existing helpers `_paragraph_has_list_marker` (line 542) and `_paragraph_has_numbering` (line 534) — both already defined:
```python
def _paragraph_has_numbering(paragraph: Paragraph) -> bool:
    try:
        p_pr = paragraph._p.pPr
        return bool(p_pr is not None and p_pr.numPr is not None)
    except Exception:
        return False

def _paragraph_has_list_marker(text: str) -> bool:
    return bool(BULLET_MARKER_RE.match(text) or NUMBERED_MARKER_RE.match(text))
```

**D-09 branch shape (researcher Example E):**
```python
text = str(row_data.get("text", "") or paragraph.text or "").strip()
if (
    label == "body_text"
    and paragraph_style_class == "body"
    and _paragraph_has_list_marker(text)
    and not _paragraph_has_numbering(paragraph)
):
    return {
        "status": "review",
        "violated_rules": [],
        "applied_fixes": [],
        "suggested_fixes": [],
        "suggested_rule_ids": [],
        "manual_review_required": True,
        "blocked_unsafe_autofix": False,
        "unsafe_auto_fix_reason": "",
        "explanation": "ambiguous_list_marker_no_numId",
    }
```

**Explanation string convention:** `ambiguous_list_marker_no_numId` — matches Phase 1 `style_guard_block:` convention (D-09 explicitly mirrors it per code_context line 132). Bare token without a colon-suffix because there is no sub-detail; if a sub-detail emerges in Phase 5, switch to `ambiguous_list_marker_no_numId:<detail>`.

---

### `src/rules/rule_engine.py` — D-11 profile threading + remove `MAX_FALLBACK_LIST_*`

**Analog:** existing `default_font_name` kwarg threading at line 777 (`apply_rules_to_paragraph` signature).

**Existing signature (line 771-778):**
```python
def apply_rules_to_paragraph(
    paragraph: Paragraph,
    label: str,
    row_data: dict[str, Any],
    rules: list[dict[str, Any]],
    apply_safe: bool,
    default_font_name: str,
) -> dict[str, Any] | None:
```

**Phase 2 extension (Pitfall 5 binding):** add `profile: dict[str, Any] | None = None` as a NEW keyword argument with default `None`. When `None`, fall back to the hard-coded 40/300 defaults so existing tests keep their current behavior; new tests pass a profile to verify override.

**Existing constants to DELETE (lines 30-31):**
```python
MAX_FALLBACK_LIST_WORDS = 40
MAX_FALLBACK_LIST_CHARS = 300
```

**Existing consumer (line 546):**
```python
def _is_long_plain_paragraph(text: str) -> bool:
    return len(text) >= MAX_FALLBACK_LIST_CHARS or len(text.split()) >= MAX_FALLBACK_LIST_WORDS
```
Change signature → `_is_long_plain_paragraph(text: str, *, max_words: int, max_chars: int) -> bool`. Threaded callers: `assess_list_auto_fix_safety` (line 559, 582) and `is_list_like_paragraph` (line 599). Each acquires the thresholds via the new profile-loader helper (see below).

**Caller wiring at `inplace_formatter.py:422-430`:**
```python
rule_result = apply_rules_to_paragraph(
    paragraph=block, label=label, row_data=row_data, rules=rules,
    apply_safe=apply_safe, default_font_name=default_font_name,
)
```
Add `profile=profile` to this call site — the loaded profile dict is already in scope (line 331).

---

### `src/rules/rule_engine.py` — D-13 conditional bibliography format scalars

**Analog:** existing `apply_bibliography_format` (lines 230-265) — already iterates `scalar_fields` with `if field not in config: continue` (lines 254-256). Structurally correct; only the SOURCE of `config` changes.

**Existing scalar loop pattern to preserve** (lines 254-265):
```python
scalar_fields = [
    "alignment", "first_line_indent_cm", "left_indent_cm",
    "line_spacing", "space_before_pt", "space_after_pt",
]
for field in scalar_fields:
    if field not in config:
        continue
    applied.extend(
        apply_scalar_fix(
            paragraph=paragraph, parameter=field, expected_value=config[field],
            default_font_name="Times New Roman",
        )
    )
```

**Phase 2 change:** `config` argument flows from `formatting_rules_v1.json:118-130` `bibliography_item_format.expected_value`. Per researcher Open Question 4 recommendation: STRIP `first_line_indent_cm` and `left_indent_cm` from the rule's `expected_value`, leaving only `{"style_name": "List Number"}`. Profile JSON `labels.bibliography_item.style_profile.*` becomes the authoritative source. The `if field not in config: continue` guard then naturally implements D-13.

**Always-safe block to PRESERVE** (lines 236-244): `style_name` + `apply_bibliography_numbering(paragraph, section_index)` call.

---

### `src/rules/profile_loader.py` — D-11 helper getter

**Analog:** `get_target_style_profile` (lines 165-170) and `get_audit_policy` (173-175). Same one-liner shape.

**Existing pattern:**
```python
def get_target_style_profile(profile: dict[str, Any], label: str) -> dict[str, Any] | None:
    cfg = get_label_config(profile, label)
    return None if not cfg else cfg.get("style_profile")

def get_audit_policy(profile: dict[str, Any], label: str) -> dict[str, Any]:
    cfg = get_label_config(profile, label) or {}
    return cfg.get("audit_policy", {})
```

**New helpers to add (researcher Don't Hand-Roll table):**
```python
def get_list_detection_thresholds(profile: dict[str, Any]) -> tuple[int, int]:
    """Return (max_fallback_words, max_fallback_chars) — defaults 40/300."""
    cfg = profile.get("list_detection", {}) or {}
    return int(cfg.get("max_fallback_words", 40)), int(cfg.get("max_fallback_chars", 300))

def get_bibliography_numbering_scope(profile: dict[str, Any]) -> str:
    """Return 'per_document' | 'per_section' | 'per_subsection_pattern'. Default 'per_section'."""
    return str(profile.get("numbering", {}).get("bibliography", {}).get("scope", "per_section"))
```

Keep return types primitives (tuple/str), not dicts — matches Phase 1 helper compactness.

---

### `src/rules/profile_validator.py` — D-03 + D-11 schema extension

**Analog:** existing `validate_profile` (lines 40-86) — appends errors to a flat list; uses `set` subtraction for required-key checks; type-checks numerics via `isinstance(..., (int, float))` and enums via membership.

**Existing required-key check pattern (lines 42-44):**
```python
missing_top = REQUIRED_TOP_LEVEL_KEYS - set(profile.keys())
if missing_top:
    errors.append(f"Отсутствуют обязательные верхнеуровневые ключи: {sorted(missing_top)}")
```

**Existing type-check pattern (lines 72-81):**
```python
for key in ["first_line_indent_cm", "left_indent_cm", "line_spacing", ...]:
    if not isinstance(style_profile.get(key), (int, float)):
        errors.append(f"В label '{label_name}' поле '{key}' должно быть числом")
```

**Phase 2 additions (optional sections — NOT added to `REQUIRED_TOP_LEVEL_KEYS`):**
```python
# After the existing labels loop ends (around line 86), add:

# D-11: list_detection thresholds — optional, but if present must be a dict with int fields
list_detection = profile.get("list_detection")
if list_detection is not None:
    if not isinstance(list_detection, dict):
        errors.append("Поле list_detection должно быть словарем")
    else:
        for key in ("max_fallback_words", "max_fallback_chars"):
            if key in list_detection and not isinstance(list_detection[key], int):
                errors.append(f"В list_detection поле '{key}' должно быть целым числом")

# D-03: numbering.bibliography.scope — optional, but if present must be in allowed set
ALLOWED_BIBLIOGRAPHY_SCOPES = {"per_document", "per_section", "per_subsection_pattern"}
numbering = profile.get("numbering")
if numbering is not None:
    if not isinstance(numbering, dict):
        errors.append("Поле numbering должно быть словарем")
    else:
        bibliography_cfg = numbering.get("bibliography")
        if bibliography_cfg is not None:
            if not isinstance(bibliography_cfg, dict):
                errors.append("Поле numbering.bibliography должно быть словарем")
            else:
                scope = bibliography_cfg.get("scope")
                if scope is not None and scope not in ALLOWED_BIBLIOGRAPHY_SCOPES:
                    errors.append(f"Недопустимое numbering.bibliography.scope='{scope}'")
```

**Critical:** Both sections optional — do NOT add to `REQUIRED_TOP_LEVEL_KEYS`. Existing profiles (gost_r_7_0_100_2018_bibliography.json, mirea_normcontrol_local.json) MUST continue to validate without modification.

---

### `src/rules/profiles/gost_7_32_2017.json` — D-03 + D-11 default values

**Analog:** existing top-level sections `numbering_rules` (line 276) and `bibliography_rules` (line 294).

**Existing top-level shape (lines 276-297):**
```json
"numbering_rules": {
  "title_section": { "enabled": true, "pattern": "^\\d+\\s+.+$" },
  "title_subsection": { "enabled": true, "pattern": "^\\d+\\.\\d+\\s+.+$" },
  "unnumbered_sections": [ ... ]
},
"bibliography_rules": {
  "enabled": true,
  "separate_profile_required": true
},
```

**Phase 2 additions — place after `extraction_meta` block (line 343, before trailing `}`):**
```json
"list_detection": {
  "max_fallback_words": 40,
  "max_fallback_chars": 300
},
"numbering": {
  "bibliography": {
    "scope": "per_section"
  }
}
```

**Default value rationale:** 40/300 are the current code-level constants (`rule_engine.py:30-31`); `per_section` is the current keying behavior of `_BIBLIOGRAPHY_NUM_IDS` (D-03 explicit default).

---

### `tests/fixtures/_build_bibliography_minimal.py` (NEW)

**Analog:** `tests/fixtures/_build_style_guard_minimal.py` (exact mirror).

**Analog imports + entrypoint pattern (lines 1-49):**
```python
"""One-shot fixture builder for tests/fixtures/bibliography_minimal.docx.

Run once: `python tests/fixtures/_build_bibliography_minimal.py`
Commits the resulting .docx as a binary fixture.
"""
from __future__ import annotations
from pathlib import Path
from docx import Document

def build(output_path: Path) -> None:
    document = Document()
    p1 = document.add_paragraph("Глава 1. Введение")
    p1.style = "Heading 1"
    ...
    document.save(str(output_path))

if __name__ == "__main__":
    build(Path("tests/fixtures/bibliography_minimal.docx"))
    print("wrote tests/fixtures/bibliography_minimal.docx")
```

**Phase 2 fixture composition (D-14 spec):**
- 1 bibliography_title paragraph (`"СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"`, default Normal style — D-01 must override SVM body_text).
- 2 subsections, both Heading-styled (e.g. `"ТЕОРЕТИЧЕСКАЯ ЧАСТЬ"` and `"ИССЛЕДОВАТЕЛЬСКИЙ РАЗДЕЛ"` — mixed naming so the test proves position+style detection, not text matching).
- 3 entries per subsection (6 total). Subsection 1 must have MIXED existing numIds (entry 1: no numPr, entry 2: stale numId pointing at a singleLevel abstract, entry 3: no numPr) so D-06 coercion path fires. Subsection 2: all entries with no numPr (D-06 fresh-allocate path).

**Critical OOXML detail:** to inject a mixed numId on a single paragraph in the fixture, use the same `OxmlElement` + `qn` idiom as `rule_engine.py:apply_bibliography_numbering` (lines 410-427). Do NOT use python-docx high-level API — there isn't one for direct numPr.

---

### `tests/test_bibliography_phase2.py` (NEW)

**Analog:** `tests/test_rule_engine.py` style-guard family (lines 1124-1362) for guard-style routing tests; bibliography family (lines 355-1122) for numbering integration tests.

**Imports pattern from analog (lines 1-19):**
```python
from __future__ import annotations
from pathlib import Path
import shutil
import uuid

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm

from src.evaluation.format_regression_audit import build_regression_predictions
from src.generate.inplace_formatter import audit_or_format_docx
from src.rules.profile_loader import load_profile
from src.rules.rule_engine import apply_list_numbering, apply_rules_to_paragraph
from src.rules.rule_loader import load_rules
```

**Row-data builder helper pattern (analog lines 1126-1131):**
```python
def _row_data_body_text(text: str) -> dict:
    return {"text": text, "confidence_score": 0.99, "low_confidence": False}
```

**Style-guard-style unit test shape (analog lines 1134-1152) — pattern for D-09 review routing:**
```python
def test_ambiguous_list_marker_no_numId_routes_to_review() -> None:
    document = Document()
    paragraph = document.add_paragraph("1) Первый пункт без Word numbering")
    # leave default Normal style — body_text + marker + no numPr

    result = apply_rules_to_paragraph(
        paragraph=paragraph,
        label="body_text",
        row_data=_row_data_body_text(paragraph.text),
        rules=load_rules(),
        apply_safe=True,
        default_font_name="Times New Roman",
    )

    assert result is not None
    assert result["status"] == "review"
    assert result["manual_review_required"] is True
    assert result["applied_fixes"] == []
    assert result["explanation"] == "ambiguous_list_marker_no_numId"
```

**Bibliography integration test shape (analog lines 1045-1122) — pattern for D-14 hand-crafted + idempotency tests:**
```python
def test_bibliography_minimal_docx_single_numId_per_subsection(tmp_path) -> None:
    input_docx = Path("tests/fixtures/bibliography_minimal.docx")
    assert input_docx.exists(), "fixture missing — run _build_bibliography_minimal.py"

    predictions_csv = tmp_path / "predictions.csv"
    report_csv = tmp_path / "report.csv"
    output_docx = tmp_path / "output.docx"
    build_regression_predictions(input_docx, predictions_csv)

    summary = audit_or_format_docx(
        input_docx=input_docx,
        predictions_csv=predictions_csv,
        report_csv=report_csv,
        output_docx=output_docx,
        apply_safe=True,
        profile_id="gost_7_32_2017",
    )
    assert summary["error"] == 0

    report_df = pd.read_csv(report_csv, encoding="utf-8-sig")
    # Assertions: bibliography_item rows in subsection 1 share one numId;
    # subsection 2 rows share a different numId; applied_fixes contains "numbering".
    ...
```

**Idempotency test pattern (D-07) — run audit twice, second run = no change:**
```python
def test_bibliography_idempotent_on_rerun(tmp_path) -> None:
    # First run: produce output_docx_1
    # Second run: feed output_docx_1 back through audit_or_format_docx
    # Assert: second run summary["changed"] == 0
    ...
```

**Suggested test names (CONTEXT.md Claude's Discretion):**
- `test_bibliography_title_override_unconditional` (D-01)
- `test_bibliography_subsection_detected_by_heading_style` (D-04)
- `test_bibliography_multilevel_renders_section_dot_entry` (D-05) — assert level-1 lvlText is `"%1.%2."`
- `test_bibliography_subsection_coerces_to_first_valid_numId` (D-06) — assert `applied_fixes` includes `numbering:coerced_to_numId=<N>`
- `test_bibliography_idempotent_on_rerun` (D-07)
- `test_ambiguous_list_marker_no_numId_routes_to_review` (D-09)
- `test_long_body_text_without_marker_stays_body_text` (D-10) — control assertion
- `test_list_detection_thresholds_from_profile` (D-11)
- `test_bibliography_format_skips_alignment_when_profile_omits` (D-13)
- `test_bibliography_minimal_docx_single_numId_per_subsection` (D-14 hand-crafted)
- `test_negative_4_bibliography_single_numId` (D-14 negative integration — use `negative_examples/4_formatted_20260413_185420.docx`)
- `test_negative_corpus_diff_rate_phase2_baseline` (D-15) — calls `audit_negative_directory` with `limit=4`

---

### `tests/test_postprocess_rules.py` — extend with D-01 + D-04 unit tests

**Analog:** existing `test_bibliography_context_overrides_body_text_and_list_predictions` (line 76).

**Existing row builder + assertion shape:**
```python
def _row(block_id: int, text: str, predicted_label: str) -> dict[str, object]:
    return {
        "doc_id": "doc_1", "block_id": block_id, "text": text,
        "style": "Normal", "predicted_label": predicted_label,
    }

def test_bibliography_context_overrides_body_text_and_list_predictions() -> None:
    df = pd.DataFrame([_row(1, "СПИСОК ИСПОЛЬЗУЕМЫХ ИСТОЧНИКОВ", "body_text"), ...])
    result = apply_postprocess_rules(df)
    assert result["postprocessed_label"].tolist() == [...]
    assert result["bibliography_section_index"].tolist() == [None, 1, 1, 2, 2, None]
```

**Phase 2 new tests:**
- D-01: `_row(..., text="СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", predicted_label="body_text")` → assert `postprocessed_label == "bibliography_title"`. Pitfall 3 binding — pin the asymmetry: predicted=body_text, post=bibliography_title.
- D-04: build rows where `style="Heading 1"` (not regex-matching text) — assert `bibliography_section_index` advances; assert that the row's text is non-text-pattern (e.g. `"1 ИССЛЕДОВАТЕЛЬСКИЙ РАЗДЕЛ"`).
- D-04 fallback regex: build rows with `style="Normal"` and text matching `BIBLIOGRAPHY_SUBHEADING_RE` — assert fallback path still classifies as subsection. Strengthened assertion: not vacuous.

---

### `tests/test_profile_loader.py` (NEW) — D-11 schema-read test

**Analog:** inline-test pattern at `test_rule_engine.py:60-64`:
```python
def test_caption_profiles_require_review_not_autofix() -> None:
    profile = load_profile(profile_id="gost_7_32_2017")
    assert profile["labels"]["figure_caption"]["audit_policy"]["allow_auto_fix"] is False
```

**Phase 2 test shape:**
```python
from src.rules.profile_loader import load_profile, get_list_detection_thresholds, get_bibliography_numbering_scope

def test_list_detection_thresholds_from_profile() -> None:
    profile = load_profile(profile_id="gost_7_32_2017")
    max_words, max_chars = get_list_detection_thresholds(profile)
    assert max_words == 40
    assert max_chars == 300

def test_bibliography_numbering_scope_default_is_per_section() -> None:
    profile = load_profile(profile_id="gost_7_32_2017")
    assert get_bibliography_numbering_scope(profile) == "per_section"

def test_validator_accepts_profile_without_optional_sections() -> None:
    # gost_r_7_0_100_2018_bibliography.json / mirea_normcontrol_local.json do not
    # carry list_detection / numbering.bibliography — must still validate.
    profile = load_profile(profile_id="mirea_normcontrol_local")
    # implicit: load_profile calls assert_valid_profile; reaching here means OK.
    assert profile["profile_id"]

def test_validator_rejects_invalid_scope() -> None:
    # construct minimal-but-valid profile + inject scope="invalid"
    # assert validate_profile returns a "Недопустимое numbering.bibliography.scope" error
    ...
```

## Shared Patterns

### OxmlElement + qn construction idiom
**Source:** `src/rules/rule_engine.py:303-335` (legacy `_create_section_abstract_num_id`) and `409-429` (`apply_bibliography_numbering`).
**Apply to:** all D-05 / D-06 / D-07 OOXML emission code.
```python
elem = OxmlElement("w:tagname")
elem.set(qn("w:attribute"), "value")
parent.append(elem)
```
Use `OxmlElement` + `qn` exclusively for new XML — do NOT use python-docx high-level numbering API (none exists for multi-level — per researcher Don't Hand-Roll table).

### Try/except fall-through-to-False idiom
**Source:** `src/rules/style_signatures.py:30-45`, `src/rules/rule_engine.py:148-155, 156-163, 534-539`.
**Apply to:** all new helpers that touch `paragraph._p`, `paragraph.style`, or `paragraph.part.*`. Pattern:
```python
def _helper(paragraph: Paragraph) -> bool:
    try:
        if paragraph.style is not None and paragraph.style.name is not None:
            return bool(...)
    except Exception:
        return False
    return False
```

### Review-result dict shape
**Source:** `src/rules/rule_engine.py:786-798` (style guard).
**Apply to:** D-09 ambiguous-list branch. Eight keys, all mandatory:
```python
return {
    "status": "review",
    "violated_rules": [],
    "applied_fixes": [],
    "suggested_fixes": [],
    "suggested_rule_ids": [],
    "manual_review_required": True,
    "blocked_unsafe_autofix": False,
    "unsafe_auto_fix_reason": "",
    "explanation": "<category>:<detail>" or "<bare_token>",
}
```

### `<category>:<detail>` explanation token convention
**Source:** code_context line 132 ("Audit explanation strings carry `<category>:<detail>` shape").
**Apply to:** D-09 `ambiguous_list_marker_no_numId`, D-06 `numbering:coerced_to_numId=<N>`. Use bare token if no sub-detail.

### Optional schema validation (extension, not breaking)
**Source:** `src/rules/profile_validator.py:46-47` (the `base_profiles` optional-but-typed check):
```python
if not isinstance(profile.get("base_profiles", []), list):
    errors.append("Поле base_profiles должно быть списком")
```
**Apply to:** D-03 + D-11 new sections. Optional → no addition to `REQUIRED_TOP_LEVEL_KEYS`; type-checked → guarded `if section is not None` then validated.

### Kwarg-with-default for backwards-compatible threading
**Source:** `default_font_name: str` at `rule_engine.py:777`.
**Apply to:** D-11 `profile: dict | None = None` on `apply_rules_to_paragraph`, `_is_long_plain_paragraph`, `assess_list_auto_fix_safety`, `is_list_like_paragraph`. Default `None` → use hard-coded 40/300 fallback so existing tests pass unchanged.

### Hand-crafted DOCX fixture build pattern
**Source:** `tests/fixtures/_build_style_guard_minimal.py:1-49`.
**Apply to:** `tests/fixtures/_build_bibliography_minimal.py`. One-shot builder script that emits a binary `.docx` committed alongside; idempotent in content but NOT byte-identical (DOCX timestamps).

### Bibliography section-index plumbing
**Source:** `src/postprocess/postprocess_rules.py:178, 181, 203` (stamps `bibliography_section_index` onto df) → `src/rules/rule_engine.py:432-437` `_bibliography_section_index` reads from `row_data` via `_safe_int`.
**Apply to:** all bibliography path code. NEVER re-derive section_index inside rule_engine (researcher anti-pattern #2). Phase 2 keeps this contract.

## No Analog Found

All 12 files have an analog in the existing codebase. The deferred negative-corpus integration test (`tests/test_bibliography_negative_integration.py`, mentioned in research §"Wave 0 Gaps") is structurally identical to the D-15 negative-corpus diff-rate test in `test_bibliography_phase2.py` (both call `audit_negative_directory`). Recommend the planner consolidate these into a single Phase 2 test rather than splitting across files.

## Metadata

**Analog search scope:**
- `src/postprocess/postprocess_rules.py`
- `src/rules/rule_engine.py` (lines 1-100, 220-450, 530-820)
- `src/rules/profile_loader.py`
- `src/rules/profile_validator.py`
- `src/rules/profiles/gost_7_32_2017.json`
- `src/rules/style_signatures.py`
- `src/evaluation/format_regression_audit.py`
- `src/generate/inplace_formatter.py` (caller wiring lines 300-470)
- `tests/test_rule_engine.py` (analog test families lines 1-90, 355-555, 1040-1362)
- `tests/test_postprocess_rules.py` (full file)
- `tests/test_format_regression_audit.py` (lines 1-100)
- `tests/fixtures/_build_style_guard_minimal.py` (full file)

**Files scanned:** 12 source files, ~3,000 lines total.

**Pattern extraction date:** 2026-05-12

## PATTERN MAPPING COMPLETE
