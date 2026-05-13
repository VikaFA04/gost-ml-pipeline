---
phase: 03-heading-signature-and-docx-generator
plan: "04"
subsystem: test-regression-gate
tags: [regression-gate, d07-invariant, signature-wiring, phase3-close]
dependency_graph:
  requires:
    - phase: 03-01
      provides: D-07 invariant + 12 RED tests (now GREEN)
    - phase: 03-02
      provides: heading_format_signature column in predictions CSV
    - phase: 03-03
      provides: per-field D-05/D-06 routing; D-07 deviation surfaced for 4.docx appendix headings
  provides:
    - tests/test_positive_docx_regression.py (narrowed D-07 + signature-presence assertion)
    - Phase 3 ROADMAP success criteria 1/2/3 empirically verified
  affects:
    - Phase 4 (regression gate inherits this baseline)
tech_stack:
  added: []
  patterns:
    - "Appendix-heading exclusion: text.lstrip().upper().startswith('ПРИЛОЖЕНИ') in both non_bib_changed and heading_changed filters"
    - "Signature-presence assertion: predictions CSV must carry heading_format_signature AND have at least one populated heading row"
key_files:
  created: []
  modified:
    - tests/test_positive_docx_regression.py
decisions:
  - "Appendix headings (ПРИЛОЖЕНИЯ, Приложение А/Б/...) excluded from D-07 invariant and non_bib_changed filter per Phase 3 user decision 2026-05-13; D-06 autofix of their direct overrides is correct GOST behavior"
  - "_is_appendix_heading defined once before both filters; reused in non_bib_changed and heading_changed"
  - "Signature-presence assertion added after D-07 block; gives positive property (signatures ARE computed) to complement D-07's negative property (no spurious fixes)"
metrics:
  duration: "812s (~14 min)"
  completed: "2026-05-13"
  tasks_completed: 2
  files_changed: 1
requirements_completed:
  - REQ-heading-style-signature
---

# Phase 03 Plan 04: Wave 3 Close-out — Regression Gate & D-07 Narrowing

**One-liner:** D-07 invariant narrowed to exclude appendix headings; signature-presence assertion added; Phase 3 ROADMAP success criteria 1/2/3 verified empirically with all 98 tests passing.

## Performance

- **Duration:** ~14 min
- **Completed:** 2026-05-13
- **Tasks:** 2/2
- **Files modified:** 1

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Narrow D-07 + add signature-presence assertion | a87852a | tests/test_positive_docx_regression.py |
| 2 | Phase 3 success-criteria verification (no file changes) | — | — |

## Changes Made

### tests/test_positive_docx_regression.py

**Two-part change:**

1. **D-07 narrowing (D-07 deviation from Plan 03-03 resolved):**
   - Added `_is_appendix_heading(text)` helper: `text.lstrip().upper().startswith("ПРИЛОЖЕНИ")`
   - Applied to BOTH `non_bib_changed` filter AND `heading_changed` filter
   - Added one-line comment pinning rationale and user-decision date (2026-05-13)
   - Root cause: 4.docx appendix headings ("ПРИЛОЖЕНИЯ", "Приложение А") have direct
     formatting overrides (line_spacing, space_after_pt, alignment) that differ from GOST
     targets. D-06 correctly autofixes them. The D-07 gate (and non_bib gate) was designed
     assuming all positive headings have inherited values only — wrong for appendix headings.

2. **Signature-presence assertion (Plan 03-04 additive scope):**
   - After `assert heading_changed.empty` block, reads predictions CSV via `pd.read_csv`
   - Asserts `heading_format_signature` column present (Plan 03-02 wiring not silently dropped)
   - Asserts at least one row where column is non-NaN and value starts with `{` (JSON object)
   - Together with D-07 (negative property: no spurious fixes) this forms a tight gate:
     if Plan 03-02 wiring regresses, the positive assertion fails; if routing regresses, D-07 fails

## Phase 3 ROADMAP Success Criteria — Empirical Verification

### SC-1: Signature includes 17 fields

**Criterion:** Extractor's heading signature includes font name/size/bold/italic/underline/color/CAPS
plus alignment / first-line indent / left+right indent / space_before+after / line_spacing /
keep_with_next / keep_lines_together / page_break_before / widow control.

**Verified by:** `test_style_signatures.py::test_heading_signature_key_present` — GREEN (Plan 03-01)

**Evidence (quick suite):**
```
tests/test_style_signatures.py tests/test_rule_engine.py
63 passed in 3.84s
```

### SC-2: Inherited→review; direct→autofix

**Criterion:** For paragraphs whose Heading style is inherited from Heading 1/2/3, autofix is
blocked — mismatch routes to `review`. Direct overrides on Heading-styled paragraphs are autofixed.

**Verified by:**
- `test_rule_engine.py::test_heading_inherited_mismatch_routes_to_review` — GREEN
- `test_rule_engine.py::test_heading_direct_mismatch_routes_to_autofix` — GREEN

**Also verified by heading_minimal.docx end-to-end (Step 3 below).**

### SC-3: Positive subset stays changed=0 for heading rules; negative moves toward target; TOC/list stable

**Criterion:** GOST-decorated positive subset stays `changed=0` for any heading rule (regression
gate extended with heading-direct-fix invariant); negative heading fixtures move toward target
signatures with no text changes; TOC and list structure remain stable.

**Verified by:**
- `tests/test_positive_docx_regression.py` — GREEN (D-07 invariant, appendix-excluded)
- `tests/test_negative_corpus_diff_rate.py` — GREEN (mean ≤ 0.4781 preserved)
- `tests/test_rule_engine.py::test_style_guard_blocks_body_text_on_heading` — GREEN (TOC/list stability)

## Full Phase 3 Acceptance Suite Results

### Quick suite
```
tests/test_style_signatures.py tests/test_rule_engine.py
63 passed in 3.84s
```

### Full Phase 3 acceptance suite
```
tests/test_style_signatures.py
tests/test_rule_engine.py
tests/test_postprocess_rules.py
tests/test_profile_loader.py
tests/test_bibliography_phase2.py
tests/test_positive_docx_regression.py
tests/test_negative_corpus_diff_rate.py
tests/test_format_regression_audit.py

98 passed, 1 skipped in 128.73s (0:02:08)
```

### heading_minimal.docx end-to-end (D-10 behavior)
```
p1: status=review, applied_fixes=[], expl_head=heading_inherited_mismatch:field=font_size,actual=14.0,expected=18.0; heading_in
p2: status=changed, applied_fixes=['space_after_pt', 'space_before_pt'], expl_head=heading_inherited_mismatch:...
p3: status=changed, applied_fixes=['bold', 'font_size_pt'], expl_head=heading_section_font_size: expected font_size=18.0; ...
p4: status=review, applied_fixes=[], expl_head=heading_inherited_mismatch:field=font_size,actual=14.0,expected=18.0; ...
```

Expected per D-10:
- p1: no_change or review — actual: **review** (D-05 inherited mismatch on font_size) — PASS
- p2: changed with space_before_pt/space_after_pt — actual: **changed, space_after_pt + space_before_pt** — PASS
- p3: changed with font_size/bold — actual: **changed, bold + font_size_pt** — PASS
- p4: review with heading_inherited_mismatch in explanation — actual: **review + heading_inherited_mismatch** — PASS

## Deviations from Plan

### [Rule 1 - Bug] non_bib_changed also needed appendix-heading exclusion

**Found during:** Task 1 (first test run)

**Issue:** The `non_bib_changed` assertion failed before the `heading_changed` (D-07) assertion
because appendix headings are not bibliography labels. Both filters needed the exclusion.

**Fix:** Moved `_is_appendix_heading` definition to above both filters; added `(~changed["text"].apply(_is_appendix_heading))` to `non_bib_changed` filter as well.

**Files modified:** `tests/test_positive_docx_regression.py`

**Commit:** a87852a (included in same Task 1 commit)

## Gate Status Summary

| Gate | Result |
|------|--------|
| D-07 positive corpus (appendix-excluded) | PASS |
| D-15 negative corpus diff-rate ≤ 0.4781 | PASS |
| Phase 1 regression suite (style guards) | PASS |
| Phase 2 regression suite (bibliography) | PASS |
| Phase 3 quick suite (12 RED tests GREEN) | PASS |
| Phase 3 full acceptance suite (98 tests) | PASS |
| heading_minimal.docx D-10 behavior | PASS |
| Signature-presence assertion (Plan 03-02) | PASS |

## Open Question 2 Carry-forward (Phase 5)

10 heading_* rules carry `expected_value=null` + `autocorrect=false` (load+skip pattern):
`heading_color`, `heading_caps`, `heading_font_name`, `heading_italic`, `heading_underline`,
`heading_right_indent_cm`, `heading_keep_with_next`, `heading_keep_lines_together`,
`heading_page_break_before`, `heading_widow_control`.

Phase 5 multi-profile work should fill these from a per-profile `heading_signature` target dict
ingested via the `extract-methodical-profile` CLI.

## D-08 Status

REQ-fix-docx-generator-custom-styles already deferred in REQUIREMENTS.md and ROADMAP.md
before Phase 3 began (2026-05-13, D-08 user decision). No further action needed in this plan.

## Self-Check: PASSED

- [x] `tests/test_positive_docx_regression.py` exists and passes
- [x] `heading_format_signature` appears 6 times in the test file
- [x] `in predictions_df.columns` appears 1 time
- [x] `heading_rows.empty` appears 1 time
- [x] `heading_changed.empty` appears 1 time (D-07 preserved)
- [x] `non_bib_changed.empty` appears 1 time (non-bib invariant preserved)
- [x] Commit a87852a verified in git log
- [x] 98 passed, 1 skipped — full suite green
- [x] No src/ modifications in this plan
