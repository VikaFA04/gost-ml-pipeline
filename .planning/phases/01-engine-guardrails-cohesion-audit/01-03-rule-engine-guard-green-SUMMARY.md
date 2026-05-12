---
phase: 01-engine-guardrails-cohesion-audit
plan: 03
subsystem: rule-engine-style-guard
tags: [tdd-green, rule-engine, style-guard, cohesion-prep]
requires:
  - src/rules/style_signatures.classify_style (Plan 02 GREEN)
  - src/rules/style_signatures.LIST_STYLE_RE / HEADING_STYLE_RE
  - 7 RED style_guard unit tests + 1 RED integration test (Plan 01 scaffolding)
  - test_positive_docx_examples_are_not_autofixed (Plan 01 extended fixture list)
provides:
  - Single early-return style guard in src/rules/rule_engine.apply_rules_to_paragraph (lines 635-650)
  - Result-dict contract conformance: status="review", explanation startswith "style_guard_block:", 9 keys total
  - Cohesion prep: LIST_STYLE_RE/HEADING_STYLE_RE imported from style_signatures.py (Plan 04 D-10 setup)
affects:
  - src/rules/rule_engine.py (+18 lines net: -2 regex defs, +1 import, +17 guard block)
  - tests/test_rule_engine.py (TOC test style fix + obsolete late-path assertion update)
tech-stack:
  added: []
  patterns:
    - Early-return guard inside dispatcher, before any state mutation
    - 9-key result dict consumed by inplace_formatter.py:432-445
    - "style_guard_block:" explanation prefix (RESEARCH Pitfall 5) for audit-row distinguishability
key-files:
  created:
    - .planning/phases/01-engine-guardrails-cohesion-audit/01-03-rule-engine-guard-green-SUMMARY.md
  modified:
    - src/rules/rule_engine.py
    - tests/test_rule_engine.py
decisions:
  - "Task 3 (negative-corpus gate) executed via direct call to audit_negative_directory() because the project's audit-regression CLI module imports sklearn at load time and this worktree env lacks sklearn — same code path, just bypassing src/main.py."
  - "Plan 01 RED test test_style_guard_blocks_body_text_on_toc used style='TOC 1' which python-docx default template does not ship (raises KeyError at assignment). Switched to 'TOC Heading' to match the fixture _build_style_guard_minimal.py choice already documented in Plan 01 SUMMARY decisions."
  - "Pre-existing test_list_like_paragraph_predicted_as_body_text_is_not_autofixed asserted blocked_unsafe_autofix=True on the OLD late-path behavior; the new guard short-circuits earlier with style_guard_block (blocked_unsafe_autofix=False). Updated assertion to pin the new contract; same paragraph shape is now also covered by test_style_guard_blocks_body_text_on_list."
metrics:
  duration_seconds: 1080
  duration_human: "~18 min"
  tasks_completed: 3
  files_created: 1
  files_modified: 2
  commits: 2
  completed_date: "2026-05-12T16:05:00Z"
---

# Phase 01 Plan 03: Rule-Engine Guard (GREEN) Summary

One-liner: Single early-return style guard at lines 635-650 of `apply_rules_to_paragraph()` short-circuits `body_text` rules on Heading/TOC/Caption/List-styled paragraphs, plus regex constants moved into `style_signatures.py` (cohesion prep for Plan 04).

## Goal

Wave-2 GREEN. Turn the 7 style_guard unit tests + 1 integration test + positive-corpus regression test green by inserting a single early-return guard in `apply_rules_to_paragraph()`. Keep the negative-corpus mean `after_diff_rate` ≤ 0.4781 baseline. Single-file logic change; no downstream branch touched.

## What was built

### Task 1: Import regex constants from style_signatures (cohesion prep)

`src/rules/rule_engine.py`:
- Removed local definitions of `LIST_STYLE_RE` and `HEADING_STYLE_RE` (2 lines).
- Added `from src.rules.style_signatures import LIST_STYLE_RE, HEADING_STYLE_RE, classify_style` after `from docx.text.paragraph import Paragraph` (1 line).
- `_paragraph_has_list_style` and `_paragraph_has_heading_style` continue working unchanged — they reference the regex names which resolve through the new import.
- `import re` retained — module still uses `BIBLIOGRAPHY_SUBHEADING_RE`, `NUMBERED_MARKER_RE`, `BULLET_MARKER_RE`.

Commit: `11f7e5f`.

### Task 2: Insert early-return style guard

`src/rules/rule_engine.py:635-650` — 16-line block inserted immediately after `if not applicable_rules: return None` (line 633) and before `current_profile = get_current_paragraph_profile(paragraph)` (line 652):

```python
    # Style guard — D-01..D-03: body_text rules must not touch
    # Heading/TOC/Caption/List-styled paragraphs. Surface as review,
    # never silently skip (D-004 — "no silent rewrites").
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

The 9-key result dict matches what `src/generate/inplace_formatter.py:432-445` consumes. The `style_guard_block:` explanation prefix distinguishes guard rows from generic inherited-format review rows (RESEARCH Pitfall 5).

Commit: `9195efb`.

### Task 3: Verify negative-corpus regression (verification only — no source change)

Invoked the regression audit programmatically via `audit_negative_directory()` (skipping `src/main.py` because this worktree env lacks `sklearn`, which `src.evaluate` imports at module load).

- Smoke (`limit=5`): 5 audits, 0 errors. Pair 58 improved from 0.5517 → 0.5110 (Δ −0.04). Mean over 5 pairs: 0.4069.
- Full corpus: 17 audits, 0 errors. **Mean `after_diff_rate = 0.4737`** (≤ 0.4781 baseline). Gate PASSED.

Persisted artifacts: `/tmp/p1_regression_smoke.csv`, `/tmp/p1_regression.csv`, `/tmp/p1_summary.json`.

## Verification results

| Check | Result |
|---|---|
| `python3 -m pytest tests/test_rule_engine.py -k style_guard` | 8 passed |
| `python3 -m pytest tests/test_positive_docx_regression.py` | 1 passed (4 files: 1, 4, 58, 59 all changed=0) |
| `python3 -m pytest tests/test_rule_engine.py tests/test_style_signatures.py` | 52 passed |
| `grep -c 'style_guard_block:' src/rules/rule_engine.py` | 1 |
| `grep -c 'LIST_STYLE_RE = re.compile' src/rules/rule_engine.py` | 0 |
| `grep -c 'HEADING_STYLE_RE = re.compile' src/rules/rule_engine.py` | 0 |
| `grep -c '^from src.rules.style_signatures import' src/rules/rule_engine.py` | 1 |
| `paragraph_style_class = classify_style(paragraph)` line count | 1 (line 638) |
| Negative-corpus mean `after_diff_rate` | 0.4737 (baseline ≤ 0.4781) |

The 8 pre-existing collection errors (`test_app_upload_contract`, `test_application_service`, `test_baseline_inferencer`, `test_cli_parser`, `test_dataset_contract`, `test_methodical_profile_editor`, `test_pattern_features`, `test_predict_blocks`) and 1 failure in `test_methodical_extractor::test_extract_methodical_profile_from_pdf_file` are pre-existing environment issues (missing `joblib`, `sklearn`, `fitz`/PyMuPDF in the system Python 3.9 env) and unrelated to this plan's changes. Out of scope per CLAUDE.md "чужой мёртвый код не трогай".

## Deviations from Plan

### Rule 1 — Fix bug: TOC test style assignment used non-existent style name

- **Found during:** Task 2 verification (`python3 -m pytest tests/test_rule_engine.py -k style_guard`).
- **Issue:** `test_style_guard_blocks_body_text_on_toc` (added in Plan 01 RED) assigned `paragraph.style = "TOC 1"`. `python-docx` default template has no `"TOC 1"` style — assignment raises `KeyError`, so the test could never reach the guard.
- **Fix:** Switched to `paragraph.style = "TOC Heading"`, matching the fixture builder `tests/fixtures/_build_style_guard_minimal.py` and Plan 01 SUMMARY decision "TOC Heading replaces TOC 1 in fixture (python-docx default template ships no TOC 1)".
- **Files modified:** `tests/test_rule_engine.py:1152-1156`.
- **Commit:** `9195efb`.

### Rule 1 — Update obsolete pre-existing assertion: late-path blocked_unsafe_autofix superseded by guard

- **Found during:** Task 2 verification (full rule_engine pytest run).
- **Issue:** Pre-existing `test_list_like_paragraph_predicted_as_body_text_is_not_autofixed` asserted `result["blocked_unsafe_autofix"] is True` because the OLD late-path returned that for List-styled body_text paragraphs. The new guard short-circuits earlier and returns `blocked_unsafe_autofix: False` with `explanation` starting `style_guard_block:`. Same coverage point is now pinned by the new `test_style_guard_blocks_body_text_on_list`.
- **Fix:** Replaced `assert result["blocked_unsafe_autofix"] is True` with `assert result["explanation"].startswith("style_guard_block:")` and added explanatory comment.
- **Files modified:** `tests/test_rule_engine.py:173-179`.
- **Commit:** `9195efb`.

### Rule 3 — Bypass `src/main.py` CLI for Task 3 (env-missing dependency)

- **Found during:** Task 3 step 3a (smoke).
- **Issue:** `python3 -m src.main audit-regression` failed at import because `src/main.py` imports `src.evaluate` which imports `sklearn`. The worktree's Python (system 3.9.6) lacks `sklearn`; a Windows-style `.venv` exists at repo root but is unusable on macOS.
- **Fix:** Called `audit_negative_directory()` directly via a 38-line throwaway script (`/tmp_audit.py`, deleted after the run). Same code path, identical CSV/JSON output shape, just bypassing the unused-here `src/main.py` wrapper. The throwaway file is removed; no untracked code remains.
- **Files modified:** none (verification-only task).
- **Outcome:** Smoke 5/5 OK; full corpus 17/17 audits, mean `after_diff_rate = 0.4737` ≤ 0.4781.

## Confirmation of plan deliverables

- [x] Guard inserted at `src/rules/rule_engine.py:635-650` between line 633 (`if not applicable_rules: return None`) and line 652 (`current_profile = ...`).
- [x] `LIST_STYLE_RE` and `HEADING_STYLE_RE` no longer defined in `rule_engine.py`; imported from `style_signatures.py`.
- [x] `_paragraph_has_list_style` (line 542+) and `_paragraph_has_heading_style` (line 551+) still work — they reference the imported names through module scope.
- [x] 7 guard unit tests + 1 integration test + 4-file positive-corpus regression test all pass.
- [x] Pre-existing 38 + 6 (style_signatures) tests still pass; full rule_engine suite at 53/53 (52 in test_rule_engine.py + 1 in test_positive_docx_regression.py via the same env).
- [x] Negative-corpus mean `after_diff_rate = 0.4737` ≤ 0.4781.
- [x] Each task committed individually with `feat(01-03-rule-engine-guard-green):` prefix and `--no-verify`.

## Self-Check: PASSED

- File `src/rules/rule_engine.py` exists and contains both the `from src.rules.style_signatures import` line and the `style_guard_block:` f-string.
- File `tests/test_rule_engine.py` contains the TOC fix and the updated list-like assertion.
- Commit `11f7e5f` exists (Task 1) — verified via `git log --oneline`.
- Commit `9195efb` exists (Task 2) — verified via `git log --oneline`.
- SUMMARY.md self-references this file.
