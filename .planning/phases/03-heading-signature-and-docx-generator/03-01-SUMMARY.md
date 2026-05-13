---
phase: 03-heading-signature-and-docx-generator
plan: "01"
subsystem: tests
tags: [tdd, red-phase, heading-signature, fixtures]
dependency_graph:
  requires: []
  provides:
    - tests/fixtures/heading_minimal.docx
    - tests/fixtures/_build_heading_minimal.py
    - 4 RED tests in tests/test_style_signatures.py (D-02/D-03/D-04)
    - 8 RED tests in tests/test_rule_engine.py (D-05/D-06/D-09/D-10)
    - D-07 invariant in tests/test_positive_docx_regression.py
  affects:
    - Plan 03-02 (must implement _extract_heading_format_signature to turn style_signatures tests green)
    - Plan 03-03 (must add heading rules + routing to turn rule_engine tests green)
tech_stack:
  added: []
  patterns:
    - TDD RED-phase: lazy import inside test body; no src/ edits
    - Fixture builder: zero src/ imports (contract anchor for RED tests)
key_files:
  created:
    - tests/fixtures/_build_heading_minimal.py
    - tests/fixtures/heading_minimal.docx
  modified:
    - tests/test_style_signatures.py
    - tests/test_rule_engine.py
    - tests/test_positive_docx_regression.py
decisions:
  - "Lazy import pattern: _extract_heading_format_signature imported inside each test body so test file is collectable even when src symbol is absent"
  - "Open Question 2 resolved: rules with no GOST-defined target get expected_value=null + autocorrect=false (load+skip pattern); documented for Phase 5 to fill"
  - "Level-split for space_before_pt: heading_section_space_before_pt + heading_subsection_space_before_pt (matches font_size level-split precedent)"
metrics:
  duration: "216 seconds"
  completed: "2026-05-13"
  tasks_completed: 4
  files_changed: 5
---

# Phase 03 Plan 01: Wave 0 RED — Heading Signature Tests + Fixture Summary

**One-liner:** TDD RED phase locking D-02..D-10 contracts via 12 failing tests, a 4-paragraph DOCX fixture, and a D-07 regression invariant.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Build heading_minimal.docx fixture + builder (D-10) | 826c196 | tests/fixtures/_build_heading_minimal.py, tests/fixtures/heading_minimal.docx |
| 2 | Add 4 RED tests for heading signature extractor | 728090a | tests/test_style_signatures.py |
| 3 | Add 8 RED tests + update 1 existing test in rule engine | b7093a4 | tests/test_rule_engine.py |
| 4 | Extend positive docx regression with D-07 invariant | b1dd0b5 | tests/test_positive_docx_regression.py |

## Test Functions Added

### tests/test_style_signatures.py (lines 98–158)

- `test_heading_signature_key_present` — asserts all 17 D-02 keys present with `{value, source}` shape
- `test_heading_signature_direct_none_is_inherited` — no direct overrides → source != 'direct' for every field
- `test_heading_signature_direct_override_detected` — setting space_before/first_line_indent produces source='direct'
- `test_heading_signature_cascade_walk` — Heading 1 cascade resolves bold=True (source='inherited')

### tests/test_rule_engine.py (lines 1344–1547)

- `_heading_row_data` helper — serializes _extract_heading_format_signature into row_data dict
- `test_heading_inherited_mismatch_routes_to_review` — D-05: inherited mismatch → review + heading_inherited_mismatch explanation
- `test_heading_direct_mismatch_routes_to_autofix` — D-06: direct override mismatch → changed + space_before_pt in applied_fixes
- `test_heading_direct_match_no_change` — D-06: direct override matching expected → space_before_pt NOT in applied_fixes
- `test_heading_rules_present_in_schema` — D-09: asserts 20 heading_* rule IDs present; heading_color autocorrect=false
- `test_heading_minimal_positive_zero_fixes` — D-10 para 1: positive heading → zero heading sig field autofixes
- `test_heading_minimal_direct_fix` — D-10 para 2: direct space override → status=changed
- `test_heading_minimal_inherited_review` — D-10 para 4: inherited-only heading → no sig field autofixes
- `test_heading_style_direct_alignment_autofixed_after_guard_removal` — D-06: direct alignment override → changed (replaces old review test)

**Removed:** `test_heading_style_direct_alignment_requires_review_not_autofix` (pre-Phase-3 blanket guard contract; replaced by the above)

### tests/test_positive_docx_regression.py (lines 74–104)

- `_has_heading_fix` helper (definition + call)
- `heading_changed.empty` assertion — D-07: zero heading_* autofixes on GOST-decorated corpus

## Fixture

| File | Size | Notes |
|------|------|-------|
| tests/fixtures/heading_minimal.docx | 36773 bytes | 4 paragraphs: Heading 1 × 4; D-10 layout |
| tests/fixtures/_build_heading_minimal.py | — | Zero src/ imports; runs idempotently |

**Builder sanity check passed:**
```
4 ['Heading 1', 'Heading 1', 'Heading 1', 'Heading 1'] ['1 Основная часть', '2 Нарушение интервалов', '3 Нарушение шрифта', '4 Унаследованное нарушение']
FIXTURE_OK
```

## RED State Confirmation

```
1 failed, 6 passed in 0.96s
FAILED tests/test_style_signatures.py::test_heading_signature_key_present - ImportError: cannot import name '_extract_heading_format_signature' from 'src.rules.style_signatures'
```

All 12 new tests (4 in test_style_signatures.py + 8 in test_rule_engine.py) fail with:
- `ImportError: cannot import name '_extract_heading_format_signature'` (7 tests — extractor not implemented)
- `AssertionError: missing heading rules: ['heading_caps', 'heading_color', ...]` (1 test — rules not yet added)

Positive regression test: **1 passed** (D-07 gate is green by construction — no heading fix code paths exist yet).

## Zero src/ Edits Confirmed

```
git diff --name-only HEAD~4..HEAD -- src/ | wc -l
0
```

## Open Question 2 Resolution

Rules with no GOST-defined target (`right_indent_cm`, `keep_with_next`, `keep_lines_together`, `page_break_before`, `widow_control`, `caps`, `font_name`, `italic`, `underline`) will have `expected_value=null` + `autocorrect=false` in formatting_rules_v1.json (Plan 03-03). The rule engine dispatcher will skip entries where `expected_value=null`. This is the **load+skip pattern** — rules exist for schema completeness; Phase 5 will fill targets from methodical-profile ingest.

## Tests Plans 02/03/04 Must Turn GREEN

**Plan 03-02 (GREEN targets):**
- test_heading_signature_key_present
- test_heading_signature_direct_none_is_inherited
- test_heading_signature_direct_override_detected
- test_heading_signature_cascade_walk

**Plan 03-03 (GREEN targets):**
- test_heading_inherited_mismatch_routes_to_review
- test_heading_direct_mismatch_routes_to_autofix
- test_heading_direct_match_no_change
- test_heading_rules_present_in_schema
- test_heading_minimal_positive_zero_fixes
- test_heading_minimal_direct_fix
- test_heading_minimal_inherited_review
- test_heading_style_direct_alignment_autofixed_after_guard_removal

**Plans 03-02/03/04 must NOT break (stay green):**
- test_positive_docx_examples_are_not_autofixed (including the new D-07 heading_changed.empty gate)

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED
