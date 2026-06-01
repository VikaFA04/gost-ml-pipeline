---
phase: 01-engine-guardrails-cohesion-audit
plan: 02
subsystem: rule-engine-style-signatures
tags: [tdd-green, style-guards, rule-engine, classify-style]
requires:
  - 01-01 RED scaffold (stub + 6 unit tests pinning classify_style)
  - rule_engine.LIST_STYLE_RE / HEADING_STYLE_RE vocabulary (mirrored, not imported)
provides:
  - src/rules/style_signatures.classify_style — real regex-based dispatch
  - LIST_STYLE_RE / HEADING_STYLE_RE / TOC_STYLE_RE / CAPTION_STYLE_RE — populated
  - Check order pin: toc → heading → caption → list → body
affects:
  - src/rules/style_signatures.py (+28 lines net, stub replaced)
tech-stack:
  added: []
  patterns:
    - try/except → "body" fallback idiom (mirrors rule_engine._paragraph_has_*_style)
    - regex vocabulary mirrored (not imported) to keep style_signatures.py independent
      and to leave rule_engine.py untouched per Plan 03 boundary
key-files:
  created:
    - .planning/phases/01-engine-guardrails-cohesion-audit/01-02-style-signatures-green-SUMMARY.md
  modified:
    - src/rules/style_signatures.py
decisions:
  - "Check order toc → heading → caption → list → body (pinned by test_classify_style_toc_en_ru where 'TOC Heading' expects 'toc' not 'heading')"
  - "Mirror rule_engine regex constants by value rather than importing them — keeps style_signatures.py importable without creating a circular dependency once Plan 03 imports classify_style into rule_engine.py"
  - "TOC pattern is `toc|содержание`; Caption pattern is `caption|подпись` — narrowest possible to keep 'mw-headline', 'header', 'Footer', 'Body Text' all classified as 'body'"
metrics:
  duration_seconds: 177
  duration_human: "2m 57s"
  tasks_completed: 2
  files_created: 1
  files_modified: 1
  commits: 2
  completed_date: "2026-05-12T12:46:21Z"
---

# Phase 01 Plan 02: Style Signatures (GREEN) Summary

One-liner: Wave-1 TDD GREEN — replace Plan 01's `classify_style` stub with regex dispatch over `paragraph.style.name`, turning 4 RED unit tests green while keeping 2 edge tests passing.

## Goal

Implement minimum code in `src/rules/style_signatures.py` so that all 6 unit tests in `tests/test_style_signatures.py` (4 RED + 2 already-passing edges) pass. No production logic outside this file. `src/rules/rule_engine.py` is Plan 03's domain and remains untouched.

## What was built

### Real `classify_style(paragraph: Paragraph) -> StyleClass`

Replaces the Plan 01 stub. Reads `paragraph.style.name`, falls back to `"body"` on `None`/exception (mirrors the `_paragraph_has_list_style` / `_paragraph_has_heading_style` try/except idiom in `rule_engine.py`).

Dispatch order (locked by `test_classify_style_toc_en_ru` where `"TOC Heading"` must classify as `"toc"`):

| Order | Class | Regex (case-insensitive) |
|-------|-------|--------------------------|
| 1 | `toc` | `toc\|содержание` |
| 2 | `heading` | `heading\|заголов` |
| 3 | `caption` | `caption\|подпись` |
| 4 | `list` | `list\|список\|маркирован\|нумерован` |
| 5 | `body` | (fallthrough) |

### Regex constants

Plan 01's four placeholders (`r"$^"` — match nothing) replaced with real patterns. `LIST_STYLE_RE` and `HEADING_STYLE_RE` are byte-identical to `rule_engine.LIST_STYLE_RE` / `rule_engine.HEADING_STYLE_RE`. `TOC_STYLE_RE` and `CAPTION_STYLE_RE` are new in this plan.

## Test transition: RED → GREEN

Running `python3 -m pytest tests/test_style_signatures.py -v`:

| Test | Before (Plan 01 RED) | After (Plan 02 GREEN) |
|------|----------------------|------------------------|
| `test_classify_style_heading_en_ru` | FAIL | PASS |
| `test_classify_style_toc_en_ru` | FAIL | PASS |
| `test_classify_style_caption_en_ru` | FAIL | PASS |
| `test_classify_style_list_en_ru` | FAIL | PASS |
| `test_classify_style_body_negatives` | PASS (stub matched negatives) | PASS |
| `test_classify_style_handles_none_style` | PASS (stub matched) | PASS |

Result: `6 passed in 0.12s`.

## TDD Gate Compliance

- RED gate (Plan 01-01): `test(01-01-test-scaffolding-red): add 6 failing unit tests for classify_style` — `71b0c6f`
- GREEN gate (this plan):
  - `feat(01-02-style-signatures-green): fill TOC and Caption regex constants` — `af496a7`
  - `feat(01-02-style-signatures-green): implement classify_style with toc-first check order` — `ad25dfc`

Per CLAUDE.md "Железный закон": every production line added here is pinned by a previously committed failing test. Observed RED before each change (4 fail / 2 pass). Observed full GREEN (6/6 pass) after Task 2.

## No-regression check

- `tests/test_style_signatures.py`: 6/6 pass.
- `tests/test_rule_engine.py`: 41 pass, 5 fail. The 5 failures are the Plan 01 RED hand-off to Plan 03 (`test_style_guard_blocks_body_text_on_{heading,toc,caption,list}` + `test_style_guard_minimal_docx_changed_zero`). Plan 02 does not touch `rule_engine.py`, so this is the expected unchanged RED state for Plan 03.

## Files outside scope (verified untouched)

- `src/rules/rule_engine.py`
- `tests/test_rule_engine.py`
- `tests/fixtures/style_guard_minimal.docx` and `_build_style_guard_minimal.py`
- `tests/test_positive_docx_regression.py`

`git diff --stat b5063e6..HEAD` shows only `src/rules/style_signatures.py` (1 file changed, 28 insertions, 8 deletions).

## Deviations from Plan

None. Plan executed exactly as specified:
- Two new regex constants (TOC, Caption) added.
- `classify_style` stub replaced with regex-based dispatch.
- Check order pinned to toc → heading → caption → list → body.
- Reused existing `_paragraph_has_*_style` try/except idiom from `rule_engine.py`.
- `rule_engine.py` untouched.

## Authentication gates

None — pure local file authoring and pytest run.

## Known Stubs

None remaining in `src/rules/style_signatures.py`. All 4 regex constants have real patterns; `classify_style` has real implementation. The Plan 01 stub markers are gone.

## Threat Flags

None. The change is internal style classification logic with no network, auth, file, or schema surface.

## Commits

| # | Task | Hash | Files |
|---|------|------|-------|
| 1 | Real regex constants (TOC, Caption new; LIST, HEADING mirror rule_engine) | `af496a7` | `src/rules/style_signatures.py` |
| 2 | Real `classify_style` with toc-first check order | `ad25dfc` | `src/rules/style_signatures.py` |

## Hand-off to Plan 03

`classify_style(paragraph)` is now a stable contract returning one of `{"heading", "toc", "caption", "list", "body"}`. Plan 03 imports it into `rule_engine.py` and inserts the body_text guard between the `applicable_rules` check and the `current_profile` extraction in `apply_rules_to_paragraph`. When `paragraph_style_class != "body"` and the predicted rule class is `body_text`, the guard must return `status=review` with `explanation = "style_guard_block: rule_class=body_text paragraph_style_class={style_class}"`. The 5 RED tests still failing in `tests/test_rule_engine.py` (4 `test_style_guard_blocks_*` + 1 integration) will flip to GREEN once Plan 03 ships the guard.

## Self-Check: PASSED

Verifying SUMMARY claims:
- `src/rules/style_signatures.py` — modified (46 lines; real classify_style; real regex constants)
- Commit `af496a7` — present in `git log` (Task 1, regex constants)
- Commit `ad25dfc` — present in `git log` (Task 2, classify_style implementation)
- 6/6 unit tests pass (verified via `python3 -m pytest tests/test_style_signatures.py -v`)
- `src/rules/rule_engine.py` unchanged from `b5063e6` (verified via `git diff --stat b5063e6..HEAD`)
