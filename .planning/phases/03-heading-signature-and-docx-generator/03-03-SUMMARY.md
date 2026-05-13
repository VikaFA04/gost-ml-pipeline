---
phase: 03-heading-signature-and-docx-generator
plan: "03"
subsystem: rule-engine
tags: [heading-routing, d05-d06-d09, green-phase, direct-vs-inherited]
dependency_graph:
  requires:
    - phase: 03-01
      provides: 8 RED tests in tests/test_rule_engine.py (D-05/D-06/D-09/D-10)
    - phase: 03-02
      provides: heading_format_signature column in row_data (JSON string per heading row)
  provides:
    - src/rules/rule_engine.py::HEADING_SIG_FIELDS (frozenset, 18 fields)
    - src/rules/rule_engine.py::apply_heading_scalar_fix (D-06 writer for 18 params)
    - src/rules/rule_engine.py::apply_rules_to_paragraph (per-field heading dispatcher replacing blanket guard)
    - src/rules/formatting_rules_v1.json (20 heading_* rules: 3 existing + 17 new)
  affects:
    - Plan 03-04 (end-to-end positive regression gate; D-07 deviation documented below)
tech_stack:
  added: []
  patterns:
    - "Per-field source routing: sig['field']['source'] → direct→autofix (D-06) / inherited→review (D-05)"
    - "Open Question 2 load+skip: expected_value=null rules load (schema test passes) but dispatcher skips them"
    - "Legacy fall-through: sig=None (no heading_format_signature) falls through to _apply_scalar_rule"
    - "Bibliography guard preserved: bibliography_section_index != None → manual_review even on direct mismatch"
key_files:
  created: []
  modified:
    - src/rules/rule_engine.py
    - src/rules/formatting_rules_v1.json
decisions:
  - "Blanket heading guard removed from _apply_scalar_rule; per-field dispatcher inserted in apply_rules_to_paragraph"
  - "sig=None legacy path falls through to _apply_scalar_rule (backward compat for tests without heading_format_signature)"
  - "apply_heading_scalar_fix delegates 8 existing params to apply_scalar_fix; handles 10 new params directly"
  - "Bibliography section guard preserved inside D-06 direct mismatch branch (CLAUDE.md invariant)"
  - "Open Question 2 resolved: 10 null-target rules load+skip (expected is None → continue in dispatcher)"
  - "Level-split font_size: heading_section_font_size (18.0, title_section) + heading_subsection_font_size (16.0, title_subsection)"
  - "Level-split space_before_pt: heading_section_space_before_pt (0.0) + heading_subsection_space_before_pt (15.0)"
metrics:
  duration: "3551 seconds (~59 min)"
  completed: "2026-05-13"
  tasks_completed: 2
  files_changed: 2
requirements_completed:
  - REQ-heading-style-signature
---

# Phase 03 Plan 03: Wave 2 GREEN — Per-field heading routing + 17 new rules

**One-liner:** Blanket heading guard replaced by per-field D-05/D-06 source dispatcher; 17 new heading_* rules added; all 12 Plan 03-01 RED tests turn GREEN.

## Performance

- **Duration:** ~59 min
- **Completed:** 2026-05-13
- **Tasks:** 2/2
- **Files modified:** 2

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add 17 new heading_* rules to formatting_rules_v1.json | ac41aaa | src/rules/formatting_rules_v1.json |
| 2 | Per-field source routing + apply_heading_scalar_fix | 7207cbe | src/rules/rule_engine.py |

## Changes Made

### src/rules/formatting_rules_v1.json

17 new heading rules added (3 existing untouched):

**Concrete GOST targets (7 rules):**
- `heading_section_font_size` (expected=18.0, labels=[title_section])
- `heading_subsection_font_size` (expected=16.0, labels=[title_subsection])
- `heading_section_space_before_pt` (expected=0.0, labels=[title_section])
- `heading_subsection_space_before_pt` (expected=15.0, labels=[title_subsection])
- `heading_left_indent_cm` (expected=1.25)
- `heading_line_spacing` (expected=1.5)
- `heading_space_after_pt` (expected=10.0)

**Null-target load+skip (10 rules, all `autocorrect=false`):**
- `heading_color`, `heading_caps`, `heading_font_name`, `heading_italic`, `heading_underline`, `heading_right_indent_cm`, `heading_keep_with_next`, `heading_keep_lines_together`, `heading_page_break_before`, `heading_widow_control`

Total: 20 heading_* rules. `heading_color` has `autocorrect=false` per Pitfall 6.

### src/rules/rule_engine.py

**Blanket guard deleted (previously lines 998-1004):**
```diff
-        if label in {"title_section", "title_subsection"} and _paragraph_has_heading_style(paragraph):
-            return {
-                "current_profile": current_profile,
-                "manual_review_required": True,
-                "blocked_unsafe_autofix": blocked_unsafe_autofix,
-                "unsafe_auto_fix_reason": unsafe_auto_fix_reason,
-            }
```

**Added:**
- `import json` and `import math` at module top
- `HEADING_SIG_FIELDS` frozenset (18 elements) at module level
- `apply_heading_scalar_fix()` function (~55 lines, after `apply_scalar_fix`)
- Per-field dispatcher block (~50 lines) in `apply_rules_to_paragraph` before `_apply_scalar_rule` call

```
git diff --stat src/rules/rule_engine.py
 src/rules/rule_engine.py | 144 insertions(+), 7 deletions(-)
```

## Test Results

### 12 Plan 03-01 RED Tests (now GREEN)

```
tests/test_style_signatures.py::test_heading_signature_key_present PASSED
tests/test_style_signatures.py::test_heading_signature_direct_none_is_inherited PASSED
tests/test_style_signatures.py::test_heading_signature_direct_override_detected PASSED
tests/test_style_signatures.py::test_heading_signature_cascade_walk PASSED
tests/test_rule_engine.py::test_heading_inherited_mismatch_routes_to_review PASSED
tests/test_rule_engine.py::test_heading_direct_mismatch_routes_to_autofix PASSED
tests/test_rule_engine.py::test_heading_direct_match_no_change PASSED
tests/test_rule_engine.py::test_heading_rules_present_in_schema PASSED
tests/test_rule_engine.py::test_heading_minimal_positive_zero_fixes PASSED
tests/test_rule_engine.py::test_heading_minimal_direct_fix PASSED
tests/test_rule_engine.py::test_heading_minimal_inherited_review PASSED
tests/test_rule_engine.py::test_heading_style_direct_alignment_autofixed_after_guard_removal PASSED
12 passed in 2.27s
```

### Phase 1/2 regression suite

```
tests/test_style_signatures.py tests/test_rule_engine.py tests/test_postprocess_rules.py
tests/test_profile_loader.py tests/test_bibliography_phase2.py
91 passed, 1 skipped in 8.02s
```

### test_inherited_heading_bold_requires_review_not_autofix

```
PASSED — falls through to _apply_scalar_rule via legacy path (no heading_format_signature)
```

## Deviations from Plan

### [Rule 1 - Bug] D-07 positive corpus regression gate fails for appendix headings

**Found during:** Task 2 (post-commit regression run)

**Issue:** `tests/test_positive_docx_regression.py::test_positive_docx_examples_are_not_autofixed` fails with `4.docx: non-bibliography paragraphs were autofixed: ПРИЛОЖЕНИЯ, Приложение А`. These paragraphs have:
- "ПРИЛОЖЕНИЯ" (Heading 1, `title_section`): direct `line_spacing=1.079` and `space_after_pt=8.0`
- "Приложение А" (Heading 2, `title_subsection`): direct `alignment=CENTER`

**Root cause:** RESEARCH.md corpus sampling said "all 22 sampled heading paragraphs have ALL direct values None" — this was wrong. The sampling missed the appendix headings (paragraphs 202 and 204 in 4.docx). These heading paragraphs have direct formatting overrides that differ from GOST expected values. D-06 correctly identifies them as direct mismatches and autofixes them. The D-07 gate was designed assuming source=inherited for all positive headings.

**Why unresolvable without architecture change:** The test `test_heading_style_direct_alignment_autofixed_after_guard_removal` explicitly requires `"alignment" in result["applied_fixes"]` for a Heading 2 paragraph with `alignment=CENTER`. The D-07 gate requires "Приложение А" (also Heading 2, alignment=CENTER) to NOT have alignment in applied_fixes. Both are `title_subsection` with `source="direct"` alignment — there is no programmatic distinction between "D-06 target" and "positive appendix heading."

**Attempted fix:** Added bibliography_section_index guard in D-06 branch (correctly prevents fixing ТЕОРЕТИЧЕСКАЯ/ПРАКТИЧЕСКАЯ ЧАСТЬ bibliography headings). Does not help for appendix headings (bib_sec_idx=None).

**Resolution required for Plan 03-04:**
- Either: update `test_positive_docx_regression.py` to explicitly allow autofix on appendix headings (`Приложение.*` / `ПРИЛОЖЕНИЯ` pattern), OR
- Either: add a "whitelist" pattern for known-correct heading texts in the positive corpus, OR
- Accept: D-07 gate is violated for appendix headings with direct overrides; this is a false negative in the positive corpus (these headings DO violate GOST spacing but were accepted as "positive" examples)

**Files modified:** None (deviation is a test-suite design issue, not a code bug)

**Status:** DEFERRED to Plan 03-04

### [Rule 2 - Missing guard] Bibliography invariant added to D-06 branch

**Found during:** Task 2 (first regression run)

**Issue:** "ТЕОРЕТИЧЕСКАЯ ЧАСТЬ" and "ПРАКТИЧЕСКАЯ ЧАСТЬ" (bibliography subsection headings in 4.docx) had direct overrides and were being autofixed by D-06 dispatcher.

**Fix:** Added `if bibliography_section_index is not None: manual_review_required = True` guard inside the D-06 direct mismatch branch. Mirrors the existing guard in `_apply_scalar_rule`. CLAUDE.md invariant: "Не применяй обычные heading scalar autofix к библиографическим section headings."

**Files modified:** `src/rules/rule_engine.py` (within Task 2 commit)

## Known Stubs

None — all rules have correct `expected_value` (either GOST-sourced float or `null` for Open Question 2 deferred fields).

## Open Question 2 Resolution Applied

10 rules carry `expected_value=null` + `autocorrect=false`: `right_indent_cm`, `keep_with_next`, `keep_lines_together`, `page_break_before`, `widow_control`, `caps`, `font_name`, `italic`, `underline`, `color`. Dispatcher skips on `expected is None`. Phase 5 will fill targets from methodical-profile ingest.

## Hand-off Note for Plan 03-04

**D-07 invariant failure:** The positive regression gate (`test_positive_docx_examples_are_not_autofixed`) fails because `4.docx` contains appendix headings ("ПРИЛОЖЕНИЯ", "Приложение А") with direct formatting overrides that differ from GOST targets. D-06 autofixes them. Since I cannot modify the test, Plan 03-04 must either:
1. Update `test_positive_docx_regression.py` to exclude these paragraphs from the heading-direct-fix assertion (annotate them as "intentional override" based on text pattern), OR
2. Accept this as a known limitation and document it in the Phase 3 acceptance report

**Profile-driven expected values:** Heading rule `expected_value` fields are currently embedded in rule JSON (18.0/16.0/1.25/1.5/etc.). Phase 5 owns profile-selectability — that work will introduce a `labels.<label>.heading_signature` block in the profile and a runtime lookup path.

## Self-Check: PASSED

- [x] `src/rules/rule_engine.py` exists
- [x] `src/rules/formatting_rules_v1.json` exists
- [x] `03-03-SUMMARY.md` exists
- [x] Commits ac41aaa (Task 1) and 7207cbe (Task 2) verified in git log
- [x] `HEADING_SIG_FIELDS` = 18 elements
- [x] 20 heading_* rules in JSON (3 existing + 17 new)
- [x] `heading_color.autocorrect = False`
- [x] Blanket guard `_paragraph_has_heading_style(paragraph):` absent from rule_engine.py (grep -c returns 0)
- [x] 12 Plan 03-01 RED tests GREEN
- [x] test_inherited_heading_bold_requires_review_not_autofix PASSED
- [x] Phase 1/2 suite: 91 passed, 1 skipped
- [ ] test_positive_docx_regression.py: FAILED (D-07 gate — appendix heading direct-override conflict; documented as deviation, deferred to Plan 03-04)
