---
phase: 01-engine-guardrails-cohesion-audit
plan: 01
subsystem: rule-engine-test-scaffolding
tags: [tdd-red, style-guards, rule-engine, regression-test, docx-fixture]
requires:
  - tests/test_rule_engine.py existing 38-test baseline (preserved)
  - src/rules/rule_engine.apply_rules_to_paragraph dispatcher signature (preserved)
  - python-docx Document() with built-in styles (Heading 1, List Paragraph, TOC Heading, Caption, Normal)
  - src/evaluation/format_regression_audit.build_regression_predictions
provides:
  - src/rules/style_signatures.classify_style (stub — Plan 02 implements)
  - src/rules/style_signatures.StyleClass Literal type
  - 4 module-level regex constants (LIST_STYLE_RE, HEADING_STYLE_RE, TOC_STYLE_RE, CAPTION_STYLE_RE — placeholders)
  - 6 RED unit tests pinning classify_style behavior
  - 7 RED guard tests pinning rule_engine guard contract
  - 1 RED integration test on hand-crafted DOCX fixture
  - tests/fixtures/style_guard_minimal.docx (36927 bytes)
  - tests/fixtures/_build_style_guard_minimal.py (one-shot rebuild script)
  - extended positive-corpus regression (4 files: 1, 4, 58, 59)
affects:
  - tests/test_rule_engine.py (+183 lines, 38 pre-existing tests untouched)
  - tests/test_positive_docx_regression.py (1-line edit on checked_files)
tech-stack:
  added: []
  patterns:
    - SimpleNamespace style shim (avoids python-docx KeyError on non-built-in style names)
    - one-shot fixture builder script + committed binary DOCX
    - per-task atomic commits with `test(01-01-test-scaffolding-red):` Conventional prefix
key-files:
  created:
    - src/rules/style_signatures.py
    - tests/test_style_signatures.py
    - tests/fixtures/_build_style_guard_minimal.py
    - tests/fixtures/style_guard_minimal.docx
    - .planning/phases/01-engine-guardrails-cohesion-audit/01-01-test-scaffolding-red-SUMMARY.md
  modified:
    - tests/test_rule_engine.py
    - tests/test_positive_docx_regression.py
decisions:
  - "TOC Heading replaces TOC 1 in fixture (python-docx default template ships no TOC 1)"
  - "Integration test forces body_text label on every paragraph to exercise the guard (otherwise build_regression_predictions routes styled paragraphs to non-body labels and bypasses the guard contract entirely)"
  - "RED reason for integration test pinned via explanation.startswith('style_guard_block:') rather than the plan's original summary['changed'] != 0 (the latter is naturally 0 even without a guard because the body_text path returns review on inherited-format paragraphs)"
metrics:
  duration_seconds: 434
  duration_human: "7m 14s"
  tasks_completed: 5
  files_created: 4
  files_modified: 2
  commits: 5
  completed_date: "2026-05-12T12:38:31Z"
---

# Phase 01 Plan 01: Test Scaffolding (RED) Summary

One-liner: Wave-0 TDD RED scaffold for style-class guard — stub `classify_style` returning `"body"` unconditionally plus 13+1 failing tests pinning the behavior Plans 02 and 03 must implement.

## Goal

Pin behavior BEFORE writing implementation (CLAUDE.md TDD "Железный закон"). Every new test must fail observably for the right reason, with no production logic in this plan.

## What was built

### Production stub
- **`src/rules/style_signatures.py`** (25 lines) — module exporting `classify_style`, `StyleClass`, and 4 placeholder regex constants. `classify_style(paragraph)` returns `"body"` unconditionally. Plan 02 replaces this stub with real regex-based classification.

### Unit tests for classify_style (6 functions)
File: **`tests/test_style_signatures.py`** (94 lines)

| Test | Pinned outcome | RED state |
|------|----------------|-----------|
| `test_classify_style_heading_en_ru` | 8 names → `"heading"` | FAIL: `assert 'body' == 'heading'` |
| `test_classify_style_toc_en_ru` | 7 names → `"toc"` (incl. `"TOC Heading"` to pin check-order) | FAIL: `assert 'body' == 'toc'` |
| `test_classify_style_caption_en_ru` | 5 names → `"caption"` | FAIL: `assert 'body' == 'caption'` |
| `test_classify_style_list_en_ru` | 4 names → `"list"` | FAIL: `assert 'body' == 'list'` |
| `test_classify_style_body_negatives` | 7 names → `"body"` (incl. `"mw-headline"`, `""`) | PASS (stub matches negatives) |
| `test_classify_style_handles_none_style` | `style=None` → `"body"`, no raise | PASS (stub matches) |

Uses `types.SimpleNamespace` shim — python-docx raises `KeyError` when assigning an unregistered style name like `"Заголовок 1 Знак"`.

### Guard tests for rule_engine (7 functions)
File: **`tests/test_rule_engine.py`** (appended at end)

| Test | Pinned outcome | RED state |
|------|----------------|-----------|
| `test_style_guard_blocks_body_text_on_heading` | result.status=review, explanation starts `"style_guard_block:"` | FAIL: explanation is generic body_text inherited-format text |
| `test_style_guard_blocks_body_text_on_toc` | same contract on `TOC 1` style | FAIL: same reason |
| `test_style_guard_blocks_body_text_on_caption` | same contract on `Caption` style | FAIL: same reason |
| `test_style_guard_blocks_body_text_on_list` | same contract on `List Paragraph` style | FAIL: same reason |
| `test_style_guard_passes_heading_rule_on_heading` | non-body_text label survives guard | PASS (no guard yet) |
| `test_style_guard_passes_body_text_on_normal` | body_text on Normal survives guard | PASS (no guard yet) |
| `test_style_guard_does_not_write_direct_props` | paragraph_format props remain None after blocked attempt | PASS (current body_text path already returns review without writing props) |

All 7 are vacuous-None-pass-resistant per plan acceptance: `passes_*` tests explicitly assert `result is not None` AND no `"style_guard_block:"` prefix.

### Integration test + DOCX fixture
- **`tests/fixtures/_build_style_guard_minimal.py`** — one-shot builder for the fixture.
- **`tests/fixtures/style_guard_minimal.docx`** — 36,927-byte binary fixture committed to git. Contains exactly 5 paragraphs with styles:
  1. `Heading 1` — "Глава 1. Введение"
  2. `List Paragraph` — "Первый пункт перечисления"
  3. `TOC Heading` — "Глава 1 ............... 5" *(deviation: was `TOC 1` in plan)*
  4. `Caption` — "Рисунок 1 — Схема"
  5. `Normal` — control paragraph
- **`test_style_guard_minimal_docx_changed_zero`** in `tests/test_rule_engine.py` — forces `predicted_label="body_text"` on every paragraph (simulating worst-case model misprediction) and asserts each non-Normal paragraph's report `explanation` starts with `"style_guard_block:"`. RED now, GREEN after Plan 03.

### Positive-corpus regression
- **`tests/test_positive_docx_regression.py`** — single-line edit: `checked_files = ["1.docx", "4.docx", "58.docx", "59.docx"]`. Files 58 and 59 exhibit the body_text-on-heading bug and will fail until Plan 03's guard fires. Test currently skips in the worktree because `positive_examples/` is not present (test has `pytest.skip` for missing fixtures).

## RED state contract — failing tests

Running `python3 -m pytest tests/test_rule_engine.py tests/test_style_signatures.py tests/test_positive_docx_regression.py -q`:

```
9 failed, 43 passed, 1 skipped
```

Failing tests (the RED contract handed off to Plans 02 and 03):

| Test (path::name) | Expected fixer |
|-------------------|----------------|
| `tests/test_style_signatures.py::test_classify_style_heading_en_ru` | Plan 02 |
| `tests/test_style_signatures.py::test_classify_style_toc_en_ru` | Plan 02 |
| `tests/test_style_signatures.py::test_classify_style_caption_en_ru` | Plan 02 |
| `tests/test_style_signatures.py::test_classify_style_list_en_ru` | Plan 02 |
| `tests/test_rule_engine.py::test_style_guard_blocks_body_text_on_heading` | Plan 03 |
| `tests/test_rule_engine.py::test_style_guard_blocks_body_text_on_toc` | Plan 03 |
| `tests/test_rule_engine.py::test_style_guard_blocks_body_text_on_caption` | Plan 03 |
| `tests/test_rule_engine.py::test_style_guard_blocks_body_text_on_list` | Plan 03 |
| `tests/test_rule_engine.py::test_style_guard_minimal_docx_changed_zero` | Plan 03 |

Skipped (worktree-isolation; will run in merged repo and fail on 58/59 until Plan 03):
- `tests/test_positive_docx_regression.py::test_positive_docx_examples_are_not_autofixed`

## Test counts: before → after

The plan's pre-state estimate was ~82 tests. Local environment is missing some optional ML deps (sklearn, joblib, streamlit) which prevented full-suite collection, so the canonical "before" count cannot be observed here. Plan-relevant before/after counts:

| Scope | Before | After | Delta |
|-------|--------|-------|-------|
| `tests/test_rule_engine.py` | 38 tests | 38 + 7 guard + 1 integration = **46** | +8 |
| `tests/test_style_signatures.py` | does not exist | **6** | +6 |
| `tests/test_positive_docx_regression.py` | 1 test × 2 files | 1 test × 4 files | +2 file-iterations |
| **Total new test functions** | — | — | **+14** |

Plan target was 13+; delivered 14 (6 classify_style + 7 guard + 1 integration).

## Existing tests — no regression

All 38 pre-existing tests in `tests/test_rule_engine.py` still pass. No file outside the plan's `files_modified` list was touched.

## Deviations from Plan

### Rule 3 (Auto-fix blocking issue) — TOC 1 style name

**Found during:** Task 4
**Issue:** `paragraph.style = "TOC 1"` raised `KeyError: "no style with name 'TOC 1'"` because python-docx's default template ships `"TOC Heading"` but not `"TOC 1"` / `"TOC 2"` / `"TOC 3"` paragraph styles.
**Fix:** Use `"TOC Heading"` for the TOC paragraph in `_build_style_guard_minimal.py`. This name is already pinned to map to `"toc"` by `test_classify_style_toc_en_ru` (line 41 of `tests/test_style_signatures.py` — `"TOC Heading"` is in the list of expected-toc names).
**Files modified:** `tests/fixtures/_build_style_guard_minimal.py`
**Commit:** `92c4730`

### Rule 1 (Auto-fix bug) — Integration test RED reason

**Found during:** Task 4
**Issue:** The plan asserted the integration test would fail with `summary["changed"] != 0` because "body_text autofix mutates Heading/TOC/Caption/List paragraphs". Two compounding issues invalidated this:
1. `build_regression_predictions` routes styled paragraphs to non-body labels via `infer_regression_label` (style-based heuristic), so the body_text path is never exercised under the natural pipeline.
2. Even when body_text label is forced on every paragraph, the current body_text rule path returns `status=review` (not `changed`) because all paragraphs have inherited (not direct) formatting, which the existing autofix already declines to overwrite. So `summary["changed"] == 0` holds even WITHOUT any guard.

**Fix:**
- Override `predicted_label` and `postprocessed_label` to `"body_text"` for all 5 rows after `build_regression_predictions`, simulating worst-case ML model misprediction (the exact failure mode the Plan 03 guard exists to catch).
- Switch the RED-trigger assertion from `summary["changed"] == 0` to "every non-Normal paragraph's report `explanation` starts with `style_guard_block:`". The original `summary["changed"] == 0` assertion is kept as a forward regression guard (Plan 03's guard must not introduce changes either).

**Files modified:** `tests/test_rule_engine.py`
**Commit:** `92c4730`

### Rationale captured (none of these are bugs in code we wrote)

- `tests/test_positive_docx_regression.py` skips in the worktree because `positive_examples/` is not part of the worktree HEAD checkout. This is intentional behavior of the existing test (`pytest.skip(...)` when fixture missing) and not introduced by this plan.

## Authentication gates

None — pure local file authoring + test execution.

## Known Stubs

| Stub | File | Lines | Reason | Resolution plan |
|------|------|-------|--------|-----------------|
| `classify_style` returns `"body"` unconditionally | `src/rules/style_signatures.py` | 23-25 | RED-state pin for Plan 02 (Wave 1) | Plan 02 implements real regex-based classification per pinned tests |
| 4 regex constants are `r"$^"` no-match | `src/rules/style_signatures.py` | 16-19 | Placeholder per plan §"Interfaces" | Plan 02 fills in real patterns |

These stubs are intentional Wave-0 placeholders. They are pinned by the RED tests in `tests/test_style_signatures.py` so Plan 02 cannot ship without replacing them.

## Commits

| # | Task | Hash | Files |
|---|------|------|-------|
| 1 | style_signatures.py stub | `2b2b6eb` | `src/rules/style_signatures.py` |
| 2 | classify_style unit tests | `71b0c6f` | `tests/test_style_signatures.py` |
| 3 | rule_engine guard tests | `b2b76a7` | `tests/test_rule_engine.py` |
| 4 | DOCX fixture + integration test | `92c4730` | `tests/fixtures/_build_style_guard_minimal.py`, `tests/fixtures/style_guard_minimal.docx`, `tests/test_rule_engine.py` |
| 5 | extend positive-corpus regression | `82a4be1` | `tests/test_positive_docx_regression.py` |

## Hand-off to Plans 02 and 03

- **Plan 02** must implement real `classify_style` so all 6 unit tests pass. Check-order pin (per `TOC Heading` test): toc → heading → caption → list → body.
- **Plan 03** must insert the body_text guard between `applicable_rules` check and `current_profile` extraction in `rule_engine.apply_rules_to_paragraph`. Must produce the 9-key result dict with `explanation = "style_guard_block: rule_class=body_text paragraph_style_class={style_class}"`.
- **Plan 02 + 03 together** must turn the 9 failing tests in this RED state to GREEN without regressing the 43 passing tests.

## Self-Check: PASSED

Verifying SUMMARY claims:
- `src/rules/style_signatures.py` — FOUND (25 lines, classify_style returns "body")
- `tests/test_style_signatures.py` — FOUND (94 lines, 6 test functions)
- `tests/fixtures/_build_style_guard_minimal.py` — FOUND
- `tests/fixtures/style_guard_minimal.docx` — FOUND (36927 bytes, 5 paragraphs)
- `tests/test_rule_engine.py` — MODIFIED (7 new style_guard_* + 1 integration test, 38 existing tests preserved)
- `tests/test_positive_docx_regression.py` — MODIFIED (checked_files now has 4 entries)
- Commits `2b2b6eb`, `71b0c6f`, `b2b76a7`, `92c4730`, `82a4be1` — all present in `git log`
