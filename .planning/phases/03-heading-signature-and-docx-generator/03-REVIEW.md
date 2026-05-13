---
phase: 03-heading-signature-and-docx-generator
reviewed: 2026-05-13T00:00:00Z
depth: standard
iteration: 2
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
  warning: 0
  info: 4
  total: 4
status: clean
---

# Phase 3: Code Review Report (iteration 2)

**Reviewed:** 2026-05-13
**Depth:** standard
**Iteration:** 2 (of `/gsd-code-review-fix --auto` loop)
**Files Reviewed:** 6
**Status:** clean

## Summary

Iteration 1 closed both Warning findings:

- **WR-01** (D-06 `bold` / `font_size` side-writing `run.font.name`) — fixed by commits
  `c0de4be` (RED test) + `d7b15d7` (fix). `apply_heading_scalar_fix` now uses inline
  writes for the `bold` and `font_size` branches and no longer delegates to
  `apply_scalar_fix`, so the `run.font.name = default_font_name` side-effect can no
  longer reach heading paragraphs (`rule_engine.py:831-840`). Two regression tests
  pin the invariant: `test_heading_direct_bold_fix_preserves_inherited_font_name`
  and `test_heading_direct_font_size_fix_preserves_inherited_font_name`
  (`tests/test_rule_engine.py:1547`, `:1579`) — both assert
  `paragraph.runs[0].font.name is None` after the fix.
- **WR-02** (empty-DataFrame schema omitted `heading_format_signature`) — fixed by
  commit `469be87`. The empty-fallback column list now includes
  `heading_format_signature` (`block_extractor.py:261`), matching the populated-path
  schema (`block_extractor.py:151`).

Re-scan of the 6 files at standard depth surfaces **no new Critical or Warning
findings**. The architecturally load-bearing invariants from iteration 1 remain
intact:

- D-05 inherited-mismatch path NEVER autofixes — only appends to
  `violated_rules` / `suggested_fixes` / `explanations` and sets
  `manual_review_required = True` (`rule_engine.py:1339-1344`). No writer reachable.
- Bibliography section-heading guard for D-06 direct-mismatch is preserved
  (`rule_engine.py:1349-1350`), honoring CLAUDE.md "Не применяй обычные heading
  scalar autofix к библиографическим section headings".
- `heading_color` rule carries `autocorrect: false` (`formatting_rules_v1.json:140`)
  AND `apply_heading_scalar_fix` defensively returns `[]` on `color`
  (`rule_engine.py:870-872`) — defence in depth per Pitfall 6.
- NaN-safe JSON parse handles empty/None, NaN-float, JSON string, and the test-only
  dict shape (`rule_engine.py:1310-1318`).
- `test_positive_docx_regression.py` correctly scoped to `["1.docx", "4.docx"]`
  per Phase 3 D-08 (line 26).
- Length values are converted to `.pt` / `.cm` at extraction time; line_spacing is
  normalized to float; lazy extraction is guarded by `classify_style == "heading"`
  (Pitfalls 3/4/5/8 honored).

Four Info-level items carry forward from iteration 1 — out of fix scope but listed
below for completeness.

## Info

### IN-01: Lazy import inside `_extract_heading_format_signature` creates a hidden module-level coupling

**File:** `src/rules/style_signatures.py:92-93`

**Issue:** `_extract_heading_format_signature` lazy-imports `ALIGNMENT_MAP` from
`src.io.block_extractor` inside the function body to avoid the
`src/io <-> src/rules` cycle. This works but hides the dependency from import-graph
linters and IDE tooling; future contributors may not realize the rules module
depends on the IO module.

**Fix:** Either (a) define a duplicate `_HEADING_ALIGNMENT_MAP` constant locally in
`style_signatures.py` (the map is 9 entries; duplication cost is low) or (b) move
`ALIGNMENT_MAP` to a third module (e.g. `src/common/alignment.py`) that both
modules import. Option (a) is the lighter Phase 3 follow-up.

### IN-02: Accepting a raw dict for `heading_format_signature` blurs the test/prod boundary

**File:** `src/rules/rule_engine.py:1317-1318`

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
comment that calls out the test-only nature with an explicit
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
_Iteration: 2_
