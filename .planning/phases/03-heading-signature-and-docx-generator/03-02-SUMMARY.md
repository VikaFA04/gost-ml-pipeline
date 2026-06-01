---
phase: 03-heading-signature-and-docx-generator
plan: "02"
subsystem: extractor
tags: [heading-signature, style-cascade, block-extractor, green-phase]
dependency_graph:
  requires:
    - phase: 03-01
      provides: 4 RED tests in tests/test_style_signatures.py + heading_minimal fixture
  provides:
    - src/rules/style_signatures.py::_resolve_inherited_value(style, attr_getter)
    - src/rules/style_signatures.py::_extract_heading_format_signature(paragraph) -> dict[18]
    - block_extractor.extract_paragraph_block now emits row["heading_format_signature"] (JSON string for heading rows, None otherwise)
  affects:
    - Plan 03-03 (rule_engine reads heading_format_signature for per-field source routing)
    - Plan 03-04 (positive regression test asserts signature column is populated end-to-end)
tech_stack:
  added: []
  patterns:
    - "Two-pass resolver: Pass 1 read paragraph_format/run.font direct values; Pass 2 walk style.base_style chain via _resolve_inherited_value"
    - "Lazy extraction: signature computed only when classify_style(paragraph)=='heading' (Pitfall 3)"
    - "Hybrid schema: JSON-serialized dict for heading rows; None for others (CSV NaN, invisible to existing readers)"
    - "Conservative try/except in extractor — any signature failure returns None, never raises (downstream treats None as 'no signature available')"
key_files:
  created: []
  modified:
    - src/rules/style_signatures.py
    - src/io/block_extractor.py
decisions:
  - "Length values converted at extraction time: .pt for font_size/space_before/space_after, .cm for indents (Pitfall 4 — avoid storing EMU)"
  - "line_spacing normalized: float for proportional spacing, None when Length-typed (Pitfall 5)"
  - "Color stored as RGB hex string when direct, None when inherited/unset (Pitfall 8)"
  - "block_extractor never raises from signature computation — protects extraction pipeline integrity for non-heading-related extracts"
metrics:
  duration: "~25 min orchestrated (executor + manual finalization)"
  completed: "2026-05-13"
  tasks_completed: 2
  files_changed: 2
requirements_completed:
  - REQ-heading-style-signature
---

# Phase 03-02: Heading Signature Extractor (GREEN)

**Implemented `_extract_heading_format_signature` and wired it into `block_extractor`; 4 RED tests in `tests/test_style_signatures.py` now GREEN.**

## Performance

- **Duration:** ~25 min (executor + finalization)
- **Completed:** 2026-05-13
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

- `_resolve_inherited_value(style, attr_getter)` walks the `style.base_style` cascade and returns `(value, source)` where `source ∈ {'direct','inherited','unset'}`.
- `_extract_heading_format_signature(paragraph)` returns an 18-key dict per D-02; each entry is `{value, source}` with Length values pre-converted to `.pt`/`.cm` per D-04.
- `block_extractor.extract_paragraph_block` now sets `row['heading_format_signature']` lazily — JSON string for heading rows (classify_style==heading), Python None otherwise.
- All 4 RED tests in `tests/test_style_signatures.py` from Plan 03-01 pass; total style_signatures suite is 10/10 GREEN.

## Task Commits

1. **Task 1: style_signatures.py extractor + resolver** — `467155a` (feat)
2. **Task 2: block_extractor wiring** — `364d90e` (feat)

## Files Created/Modified

- `src/rules/style_signatures.py` — appended `_resolve_inherited_value`, `_extract_heading_format_signature` (18 fields, Length conversion at extraction time)
- `src/io/block_extractor.py` — added `heading_format_signature` column to `extract_paragraph_block` return dict; lazy guard via `classify_style(paragraph) == 'heading'`; conservative try/except wrapping

## Verification

- `pytest tests/test_style_signatures.py -x -q` → 10/10 PASS (was 6/10 with 4 RED ImportErrors)
- `pytest tests/test_rule_engine.py -q` → 6 FAIL (Plan 03-03 targets; 2 of the 8 Plan 03-01 RED tests coincide with current default-review behavior — D-05/D-06 path mismatches remain RED until Plan 03-03)
- `pytest tests/test_positive_docx_regression.py tests/test_negative_corpus_diff_rate.py -q` → PASS (Phase 1/2 + D-07 invariant intact)
- 59 passes across the 4 relevant suites confirm zero regression on Phase 1/2.

## Self-Check: PASSED

- [x] 4 RED tests in tests/test_style_signatures.py GREEN
- [x] rule_engine RED tests still RED (Plan 03-03's job)
- [x] No new failures in Phase 1/2 tests
- [x] src/rules/rule_engine.py and src/rules/formatting_rules_v1.json UNCHANGED
- [x] Lazy guard honored (signature computed only on heading paragraphs)
- [x] Each task committed atomically
- [x] SUMMARY.md written

## Deviations

None.

## Next Up

Plan 03-03 (Wave 2): remove blanket heading guard in `apply_rules_to_paragraph`; add per-field source routing (D-05 inherited → review, D-06 direct → autofix); add 15 new heading_* rules to formatting_rules_v1.json. Turns the 8 RED tests in `tests/test_rule_engine.py` GREEN.
