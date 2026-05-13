---
phase: 03-heading-signature-and-docx-generator
reviewed: 2026-05-13T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - src/rules/style_signatures.py
  - src/io/block_extractor.py
  - src/rules/rule_engine.py
  - src/rules/formatting_rules_v1.json
  - tests/fixtures/_build_heading_minimal.py
  - tests/test_positive_docx_regression.py
findings:
  critical: 0
  warning: 2
  info: 4
  total: 6
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-05-13
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Phase 3 implements the heading-signature extractor (D-01..D-04), replaces the blanket
heading guard in the rule engine with a per-field D-05/D-06 source dispatcher, adds 17
new `heading_*` rules (10 with load+skip `expected_value=null` + `autocorrect=false`),
and narrows the positive-corpus regression gate to exclude appendix headings while
adding a Plan 03-02 signature-presence assertion.

The architecturally load-bearing invariants are preserved:

- D-05 inherited-mismatch path NEVER autofixes — `_apply_scalar_rule` is not entered,
  and the dispatcher's `source == "inherited"` branch only appends to
  `violated_rules` / `suggested_fixes` / `explanations` and sets
  `manual_review_required = True` (`rule_engine.py:1326-1331`). No write helper is
  reachable from that branch.
- The bibliography section-heading guard from Phase 2 is carried forward into the
  new D-06 direct-mismatch branch via the
  `if bibliography_section_index is not None: manual_review_required = True` check
  (`rule_engine.py:1336-1337`) — CLAUDE.md rule "Не применяй обычные heading scalar
  autofix к библиографическим section headings" is preserved.
- `heading_color` rule carries `autocorrect: false` per Pitfall 6
  (`formatting_rules_v1.json:140`), and `apply_heading_scalar_fix` defensively
  returns `[]` on the `color` parameter even if the dispatcher were bypassed
  (`rule_engine.py:856-859`).
- The NaN-safe JSON parse handles all three production shapes: empty/None, NaN-float,
  JSON string, and the test-only dict shape (`rule_engine.py:1295-1305`).
- `test_positive_docx_regression.py` is correctly scoped to `["1.docx", "4.docx"]`
  per Phase 3 D-08 (line 26).
- Length values are converted to `.pt` / `.cm` at extraction time, line_spacing is
  normalized to float (Pitfalls 4/5/8 honored), and lazy extraction is enforced via
  `classify_style(paragraph) == "heading"` guard before computing the signature
  (Pitfall 3 honored).

Two Warning-level findings affect future correctness; four Info-level items document
maintainability / discoverability improvements.

## Warnings

### WR-01: `apply_scalar_fix` writes `run.font.name = default_font_name` as a side effect of `bold` / `font_size_pt` fixes — risks overwriting inherited heading font

**File:** `src/rules/rule_engine.py:777-786`

**Issue:** When the per-field D-06 dispatcher routes a heading rule
(`heading_section_font_size`, `heading_subsection_font_size`, `heading_bold`) to
`apply_heading_scalar_fix`, the helper delegates to the pre-existing
`apply_scalar_fix` for `font_size` / `bold` parameters
(`rule_engine.py:818-827`). `apply_scalar_fix` unconditionally writes
`run.font.name = default_font_name` (i.e. "Times New Roman") on every run alongside
the bold / font-size mutation:

```python
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
```

When a heading has `font_name` `source="inherited"` (the typical positive-corpus
case) but `bold` `source="direct"` with the wrong value, D-06 fires and silently
overwrites the inherited font with a direct "Times New Roman" override. This
directly violates CLAUDE.md: *"Не перезаписывай наследуемое DOCX-форматирование
прямыми значениями без regression-теста на сохранение Word-стилей."*

Before Phase 3 the blanket guard prevented this path on heading-labeled rows; Phase
3 now reaches the writer via `apply_heading_scalar_fix → apply_scalar_fix`.
`test_heading_minimal_direct_fix` (paragraph 3 of `heading_minimal.docx`) exercises
exactly this path — per `03-04-SUMMARY.md` line 144, `applied_fixes=['bold',
'font_size_pt']` fires, which means `run.font.name` is now being written even
though no `font_name` rule is involved. No test asserts that `run.font.name`
remained inherited after the fix.

**Fix:** In `apply_heading_scalar_fix`, do not delegate `bold` / `font_size`
through `apply_scalar_fix` unless the heading's `font_name` is `source="direct"`.
Safest option — duplicate the body of the `font_size_pt` / `bold` branches inline
(or factor into a private helper `_apply_font_attr_only`) that mutates only the
targeted attribute:

```python
if parameter == "font_size":
    for run in paragraph.runs:
        if run.text:
            run.font.size = Pt(float(expected_value))
    return ["font_size_pt"]

if parameter == "bold":
    for run in paragraph.runs:
        if run.text:
            run.bold = bool(expected_value) if expected_value is not None else None
    return ["bold"]
```

Add a regression test asserting `run.font.name is None` after applying
`heading_bold` autofix on a fixture whose Heading style has no direct font_name
override.

---

### WR-02: Empty-document fallback DataFrame schema omits `heading_format_signature` column

**File:** `src/io/block_extractor.py:247-262`

**Issue:** When `extract_blocks_from_docx` is called on a document yielding zero
records, the fallback builds an empty DataFrame with a fixed column list that
omits `heading_format_signature`:

```python
if df.empty:
    df = pd.DataFrame(
        columns=[
            "doc_id", "block_id", "text", "kind", "alignment",
            "style", "bold_ratio", "list_type", "list_level", "file_name",
        ]
    )
```

Downstream code (`apply_rules_to_paragraph`, the dispatcher at
`rule_engine.py:1294`) reads `row_data.get("heading_format_signature")` which
returns `None` for the missing column — the fall-through to `_apply_scalar_rule`
keeps the behavior safe. The signature-presence assertion in
`test_positive_docx_regression.py:124` (`assert "heading_format_signature" in
predictions_df.columns`) would FAIL silently if the empty-fallback path were ever
hit during the positive gate (e.g., empty DOCX, or every paragraph filtered out).
The mismatch between the populated-path schema (which includes
`heading_format_signature`) and the empty-fallback schema (which does not) is a
latent inconsistency.

**Fix:** Add `heading_format_signature` to the empty-fallback column list:

```python
if df.empty:
    df = pd.DataFrame(
        columns=[
            "doc_id", "block_id", "text", "kind", "alignment",
            "style", "bold_ratio", "list_type", "list_level",
            "file_name", "heading_format_signature",
        ]
    )
```

## Info

### IN-01: Lazy import inside `_extract_heading_format_signature` creates a hidden module-level coupling

**File:** `src/rules/style_signatures.py:92-93`

**Issue:** `_extract_heading_format_signature` lazy-imports `ALIGNMENT_MAP` from
`src.io.block_extractor` inside the function body to avoid the
`src/io ↔ src/rules` cycle. This works but hides the dependency from
import-graph linters and IDE tooling; future contributors may not realize the
rules module depends on the IO module.

**Fix:** Either (a) define a duplicate `_HEADING_ALIGNMENT_MAP` constant locally in
`style_signatures.py` (the map is 9 entries; duplication cost is low) or (b)
move `ALIGNMENT_MAP` to a third module (e.g. `src/common/alignment.py`) that both
modules import. Option (a) is the lighter Phase 3 follow-up.

### IN-02: Accepting a raw dict for `heading_format_signature` blurs the test/prod boundary

**File:** `src/rules/rule_engine.py:1304-1305`

**Issue:** The dispatcher accepts a dict literal in addition to a JSON string:

```python
elif isinstance(raw, dict):
    sig = raw  # tests may pass a dict directly without serializing
```

Production extractors always emit a JSON string (`block_extractor.py:159`); the
dict-pass-through exists only for test convenience. This means a test that passes
a dict exercises a different code path than production. If a future refactor
inadvertently allows a dict to leak through the predictions CSV (e.g., a different
serializer), the dict branch would mask a regression.

**Fix:** Either (a) require tests to call `json.dumps(sig)` before constructing
`row_data` (mirrors prod path exactly), or (b) keep the dict branch but add a
comment that calls out the test-only nature and an explicit
`# pragma: production-never-reaches-here` marker for future readers.

### IN-03: `direct_underline` comment "keep as is" obscures the JSON-serialization assumption

**File:** `src/rules/style_signatures.py:131`

**Issue:** The line `direct_underline = run.font.underline  # bool or
WD_UNDERLINE -- keep as is` stores either a `bool` or a `WD_UNDERLINE` enum
member. Empirically `WD_UNDERLINE` is an `IntEnum` and JSON-serializes to its
integer value, so `json.dumps(sig)` does not raise. But the comment "keep as is"
does not communicate that downstream consumers must treat the deserialized
underline value as an `int` (e.g., `1` for SINGLE) — not a `WD_UNDERLINE` enum
instance.

This is benign in Phase 3 because `heading_underline` has `expected_value=null`
and the dispatcher skips the rule before any comparison. But Phase 5 (which fills
the null targets per `03-04-SUMMARY.md` Open Question 2 carry-forward) will need
to know that the on-disk underline value is `int`, not enum.

**Fix:** Expand the comment to document the serialization contract:

```python
# WD_UNDERLINE (IntEnum) JSON-serializes to int; downstream compares against int.
direct_underline = run.font.underline
```

### IN-04: `BIBLIOGRAPHY_SUBHEADING_RE` is defined twice in the same module

**File:** `src/rules/rule_engine.py:36, 553`

**Issue:** The regex `BIBLIOGRAPHY_SUBHEADING_RE` is defined at module level
(line 36) AND imported from `src.postprocess.postprocess_rules` inside
`_seed_bibliography_num_ids_from_doc` as `_bib_subhead_re` (line 553). Two
sources of truth for the same regex pattern; if the bibliography subheading
vocabulary changes, both have to be updated in lockstep or the seeding logic
diverges from the section-title-matching logic.

This predates Phase 3 — flagging only because the file is in scope and the
duplication is a maintainability hazard the per-field dispatcher inherits.

**Fix:** Pick one canonical definition (preferably the one in
`postprocess_rules.py` since that is where the bibliography-context detection
lives) and import it everywhere else. Out of Phase 3 scope; track as
maintainability follow-up.

---

_Reviewed: 2026-05-13_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
