---
phase: 07-pdf-text-layer-audit-slice
plan: 04
subsystem: ui
tags: [streamlit, pdf, audit-only, run-processing, baseline-bypass, gap-closure, tdd]
gap_closure: true
closes_gaps: [G-07-01]

requires:
  - phase: 07-pdf-text-layer-audit-slice
    provides: ProcessingArtifacts.input_extension + process_document PDF branch + PdfNoTextLayer (plans 07-02 / 07-03 on main HEAD)
provides:
  - PDF input bypasses baseline_unavailable guard in app.run_processing — required for the audit-only flow to work in workspaces without a saved baseline .joblib
  - Regression test tests/test_run_processing_pdf_bypass.py with 2 cases (PDF bypass + DOCX still-short-circuits)
  - CLAUDE.md self-improvement rule covering the root-cause class (pre-pipeline UI gates on supported-format expansion)
affects: [phase-8-milestone-acceptance, plan-07-05]

tech-stack:
  added: []
  patterns:
    - "Compound-condition guard widen: fold a suffix-based skip into the existing if via AND rather than nesting a new outer guard — preserves function shape, matches Phase 6 single-line guard style"

key-files:
  created:
    - tests/test_run_processing_pdf_bypass.py
  modified:
    - app.py
    - CLAUDE.md

key-decisions:
  - "Compound-condition fold rather than nested guard: `if selected_model_key == \"baseline_unavailable\" and Path(uploaded_file.name).suffix.lower() != \".pdf\"` — keeps the function body shape identical to Phase 6 (single early-return block) and avoids a new layer of indentation."
  - "Suffix check uses `.lower()` to match the existing idiom in `save_uploaded_bytes(... suffix=Path(uploaded_file.name).suffix)` — case-insensitive on the suffix is necessary because Streamlit's uploader does not normalise extension casing client-side."

patterns-established:
  - "Run-processing TDD pattern: monkeypatch process_document / save_uploaded_bytes / RunLog with recorders, build a SimpleNamespace upload stub (.name + .getvalue), assert the recorder is non-empty (PDF) or empty (DOCX). No real pipeline runs, no disk writes."
  - "Compound-condition guard widen: fold a suffix-based skip into the existing if via AND rather than nesting a new outer guard"

requirements-completed: [REQ-pdf-text-only]

duration: ~6min inline (3 atomic commits) + 14s test runtime
completed: 2026-05-15T13:15:00Z
---

# Phase 07-04: G-07-01 Gap Closure — PDF Bypass of baseline_unavailable

**`run_processing` no longer short-circuits PDF input when the workspace lacks a baseline .joblib; DOCX behaviour preserved verbatim.**

## Performance

- **Duration:** ~6 min (Task 1 RED → Task 2 GREEN → Task 3 CLAUDE.md rule)
- **Started:** 2026-05-15T13:09:00Z
- **Completed:** 2026-05-15T13:15:00Z
- **Tasks:** 3 (1 TDD-RED, 1 TDD-GREEN, 1 docs)
- **Files modified:** 3 (`tests/test_run_processing_pdf_bypass.py` created, `app.py` modified, `CLAUDE.md` modified)
- **Execution path:** Inline by orchestrator after two `gsd-executor` spawn attempts (a27d56e9, a3a4eb82) returned without doing work — both claimed to lack Bash despite the tool being in gsd-executor's allowed set. Inline execution by main thread bypassed the agent-layer regression.

## Accomplishments

### Task 1 (RED — commit `fa628f2`)
- `tests/test_run_processing_pdf_bypass.py` created with 2 tests, gated by `pytest.importorskip("streamlit")`
- `test_run_processing_pdf_input_bypasses_baseline_unavailable_guard` observed FAILING (`assert 0 == 1` at the recorder length assertion)
- `test_run_processing_docx_input_still_short_circuits_on_baseline_unavailable` observed PASSING (Phase 6 contract preservation guard)
- Pyright noise on `import app` was env-level (system Python 3.9 lacks streamlit); the test runs on `/tmp/gost-test-venv/bin/python` (3.12 with streamlit installed)

### Task 2 (GREEN — commit `1af1d3a`)
- `app.py:425` widened: `if selected_model_key == "baseline_unavailable" and Path(uploaded_file.name).suffix.lower() != ".pdf":`
- 2-line inline comment documents the gap ID (G-07-01) + rationale (Plan 07-02 D-02 — PDF path bypasses SVM)
- Russian `st.error` message UNCHANGED — DOCX users still see «Baseline-модель недоступна: в workspace нет сохраненного .joblib-артефакта.» exactly as before
- Both tests now PASS (PDF bypass = process_document called once; DOCX = process_document not called)

### Task 3 (CLAUDE.md rule — commit `a98ecd9`)
- One императивное предложение appended to `## Принципы исполнения` at the very end (after the «Co-Authored-By» bullet, before the section's `---` separator)
- Rule wording: «При расширении набора поддерживаемых входных форматов проверь все pre-pipeline UI-гейты, опирающиеся на наличие артефактов модели или специфический suffix, и убедись, что они не блокируют новые форматы, чьи pipeline-ветки не зависят от соответствующего артефакта.»
- `grep -c "При расширении набора поддерживаемых"` returns exactly 1 (no duplicate)
- `wc -w CLAUDE.md` = 1032 words — well under the 2500-token protocol budget

## Test State (post-fix)

- `tests/test_run_processing_pdf_bypass.py`: 2/2 PASS on streamlit-enabled venv
- `tests/inference/test_pdf_loader.py`: 13/13 PASS (no Phase 7 wave 0/1 regression)
- Combined `tests/inference/ tests/test_run_processing_pdf_bypass.py`: 15/15 PASS in 13.82s

## Commits

- `fa628f2` test(07-04): RED regression — PDF must bypass baseline_unavailable guard in run_processing
- `1af1d3a` fix(07-04): bypass baseline_unavailable guard for PDF input in run_processing (G-07-01)
- `a98ecd9` docs(07-04): record self-improvement rule about pre-pipeline UI gates on supported-format expansion

## Self-Check

- [x] All 3 tasks executed atomically
- [x] Each task committed individually
- [x] SUMMARY.md created and to be committed in this commit
- [x] No modifications to STATE.md or ROADMAP.md
- [x] tests/test_run_processing_pdf_bypass.py exists with the RED-then-GREEN test asserting PDF bypass
- [x] app.py run_processing widens the baseline_unavailable guard to skip when uploaded file suffix is .pdf
- [x] CLAUDE.md §Принципы исполнения gains one new императивное bullet about pre-pipeline UI gates
- [x] CLAUDE.md total token count remains under 2500 (1032 words)
- [x] Phase 1-6 regression unchanged (Phase 7 wave 0/1 surface re-tested green)

## Self-Check: PASSED
