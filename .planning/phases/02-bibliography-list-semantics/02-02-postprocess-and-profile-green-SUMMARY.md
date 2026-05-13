---
phase: 02-bibliography-list-semantics
plan: "02"
subsystem: postprocess+profile
tags:
  - bibliography
  - postprocess
  - profile
  - phase-2
  - D-01
  - D-03
  - D-04
  - D-11
dependency_graph:
  requires:
    - "02-01 (Wave 0 RED tests — test_profile_loader.py, test_postprocess_rules.py)"
    - "Phase 1 style_signatures module (HEADING_STYLE_RE, classify_style idiom)"
  provides:
    - "get_list_detection_thresholds() and get_bibliography_numbering_scope() helpers for Plans 03/04"
    - "ALLOWED_BIBLIOGRAPHY_SCOPES for profile validator"
    - "D-01 unconditional bibliography_title override in postprocess"
    - "D-04 heading-style subsection detection with regex fallback in postprocess"
  affects:
    - "src/postprocess/postprocess_rules.py"
    - "src/rules/profile_loader.py"
    - "src/rules/profile_validator.py"
    - "src/rules/profiles/gost_7_32_2017.json"
tech_stack:
  added: []
  patterns:
    - "try/except→'body' idiom for style classification (mirrors classify_style)"
    - "Optional section validation in profile_validator (if present, type-check)"
    - "Pre-pass before label-rewrite loop for unconditional overrides"
key_files:
  created: []
  modified:
    - "src/postprocess/postprocess_rules.py"
    - "src/rules/profile_loader.py"
    - "src/rules/profile_validator.py"
    - "src/rules/profiles/gost_7_32_2017.json"
decisions:
  - "D-01: Unconditional bibliography_title override runs as first pre-pass before all other label-rewriting — prevents SVM body_text from surviving the postprocess pipeline"
  - "D-04: Heading-style detection (HEADING_STYLE_RE on row style string) as primary signal; BIBLIOGRAPHY_SUBHEADING_RE as fallback — every matching row increments bibliography_section_index unconditionally"
  - "D-11: profile helpers (get_list_detection_thresholds, get_bibliography_numbering_scope) use .get() with explicit defaults so missing sections return 40/300 and 'per_section'"
  - "D-03: ALLOWED_BIBLIOGRAPHY_SCOPES defined at module level in profile_validator for importability by tests"
metrics:
  duration: "237s (3m 57s)"
  completed: "2026-05-12"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 4
---

# Phase 02 Plan 02: postprocess-and-profile-green Summary

**One-liner:** D-01 unconditional bibliography_title override + D-04 heading-style subsection detection + D-03/D-11 profile schema extension with two new helpers and JSON fields.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | D-03+D-11 profile schema — helpers + validator + JSON | 72bed8c | profile_loader.py (+21 lines), profile_validator.py (+29 lines), gost_7_32_2017.json (+12 lines) |
| 2 | D-01+D-04 postprocess — title override + heading-style detection | 013ef1a | postprocess_rules.py (+46 lines, -3 lines) |

## Files Modified

| File | Lines added | Lines removed | Description |
|------|-------------|---------------|-------------|
| `src/rules/profile_loader.py` | +21 | 0 | Two new helpers: `get_list_detection_thresholds`, `get_bibliography_numbering_scope` |
| `src/rules/profile_validator.py` | +29 | 0 | `ALLOWED_BIBLIOGRAPHY_SCOPES` constant + optional-section validation blocks |
| `src/rules/profiles/gost_7_32_2017.json` | +12 | 0 | `list_detection.{max_fallback_words:40, max_fallback_chars:300}` + `numbering.bibliography.scope='per_section'` |
| `src/postprocess/postprocess_rules.py` | +46 | -3 | `_row_style_class()` helper + D-01 pre-pass + D-04 in_bibliography loop rewrite |

## Wave 0 Tests Turned GREEN

When Wave 0 (plan 02-01) tests land and the branches are merged, the following tests will turn GREEN from this plan's implementation:

**tests/test_profile_loader.py (4 tests):**
- `test_list_detection_thresholds_from_profile` — `get_list_detection_thresholds(gost_7_32_2017)` returns `(40, 300)`
- `test_bibliography_numbering_scope_default_is_per_section` — `get_bibliography_numbering_scope(gost_7_32_2017)` returns `'per_section'`
- `test_validator_accepts_profile_without_optional_sections` — `mirea_normcontrol_local` profile validates cleanly
- `test_validator_rejects_invalid_scope` — `validate_profile` returns error for unknown scope

**tests/test_postprocess_rules.py (new tests from Wave 0):**
- `test_bibliography_title_overrides_svm_body_text` — D-01 pre-pass sets `bibliography_title` when SVM predicted `body_text`
- `test_bibliography_subsection_detected_by_heading_style` — D-04 increments `bibliography_section_index` on Heading-styled row inside bibliography context
- `test_bibliography_subsection_fallback_regex_still_works` — D-04 fallback: `BIBLIOGRAPHY_SUBHEADING_RE` match still classifies as subsection when style is Normal

## Wave 0 Tests Still RED (Handoff to Plans 03/04)

- `tests/test_bibliography_phase2.py` — D-05/D-06/D-07 (2-level numbering, coercion, idempotency) → Plan 03
- `tests/test_bibliography_phase2.py` — D-09 (ambiguous list marker review routing) → Plan 04
- `tests/test_bibliography_phase2.py` — D-13 (profile-driven scalar formatting) → Plan 03/04
- `tests/test_bibliography_phase2.py` — D-14 integration tests (bibliography_minimal.docx) → Plans 03+04

## Confirmation: Other Profile JSONs Unchanged

- `src/rules/profiles/mirea_normcontrol_local.json`: does NOT carry `list_detection` or `numbering` — validated via `assert 'list_detection' not in data` — CONFIRMED unchanged
- `src/rules/profiles/gost_r_7_0_100_2018_bibliography.json`: same confirmation — both profiles load and validate without errors via `assert_valid_profile`

## Confirmation: BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE Importable (Pitfall 4 Guard)

The constant `BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE` remains defined in `src/postprocess/postprocess_rules.py` (line 20). The function `_is_numbered_bibliography_subheading()` also remains. Import confirmed:

```
python3 -c "from src.evaluation.format_regression_audit import build_regression_predictions; print('format_regression_audit import OK')"
```
Output: `format_regression_audit import OK`

## Phase 1 Baseline: 68 passed, 1 skipped

Tests run: `tests/test_style_signatures.py tests/test_rule_engine.py tests/test_postprocess_rules.py tests/test_format_regression_audit.py tests/test_positive_docx_regression.py`

Result: **68 passed, 1 skipped** — no Phase 1 regression.

## Deviations from Plan

None — plan executed exactly as written. Both tasks completed per specification with all acceptance criteria verified.

## Known Stubs

None — all implementations are complete and functional.

## Threat Flags

None — changes are internal postprocess/profile logic with no new network endpoints, auth paths, file access patterns, or schema changes at external trust boundaries.

## Self-Check: PASSED

Files created/modified:
- [x] `src/rules/profile_loader.py` — FOUND (modified)
- [x] `src/rules/profile_validator.py` — FOUND (modified)
- [x] `src/rules/profiles/gost_7_32_2017.json` — FOUND (modified)
- [x] `src/postprocess/postprocess_rules.py` — FOUND (modified)

Commits:
- [x] `72bed8c` — FOUND (feat(02-02): D-03+D-11 profile schema)
- [x] `013ef1a` — FOUND (feat(02-02): D-01+D-04 postprocess)

Acceptance criteria verified:
- [x] `get_list_detection_thresholds(gost_7_32_2017)` == `(40, 300)`
- [x] `get_bibliography_numbering_scope(gost_7_32_2017)` == `'per_section'`
- [x] `ALLOWED_BIBLIOGRAPHY_SCOPES` appears 3 times in profile_validator.py (definition + two references)
- [x] `gost_7_32_2017.json` carries correct fields
- [x] `mirea_normcontrol_local.json` unchanged (no list_detection, no numbering)
- [x] `grep -c "from src.rules.style_signatures import HEADING_STYLE_RE"` == 1
- [x] `grep -c "def _row_style_class"` == 1
- [x] D-01 comment anchor present (grep -c "D-01" == 1)
- [x] D-04 comment anchor present (grep -c "D-04" == 1)
- [x] `BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE` constant preserved (grep -c == 1)
- [x] format_regression_audit imports cleanly
- [x] Phase 1 baseline: 68 passed, 1 skipped
