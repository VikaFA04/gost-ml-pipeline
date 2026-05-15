---
phase: 07-pdf-text-layer-audit-slice
plan: 05
subsystem: ui
tags: [streamlit, pdf, audit-only, empty-state, pdf-loader, copy, wording, gap-closure, tdd]
gap_closure: true
closes_gaps: [G-07-02, G-07-03]

requires:
  - phase: 07-pdf-text-layer-audit-slice
    provides: extract_pdf_blocks + ProcessingArtifacts.input_extension + sidebar uploader label (plans 07-02 / 07-03)
  - phase: 07-pdf-text-layer-audit-slice
    provides: PDF bypass of baseline_unavailable guard (plan 07-04)
provides:
  - Main-pane empty-state alert mirrors sidebar uploader copy: «Загрузите документ (DOCX или PDF), чтобы начать аудит»
  - Text-block PDF audit reason is reviewer-facing: «PDF блок — текстовый слой, требует ручной проверки»
affects: [phase-8-milestone-acceptance]

tech-stack:
  added: []
  patterns:
    - "1-for-1 line replacement on string literals: zero line-count drift; preserves Phase 6 file structure and avoids touching any non-target site"

key-files:
  created: []
  modified:
    - tests/test_app_ui.py
    - tests/inference/test_pdf_loader.py
    - app.py
    - src/inference/pdf_loader.py

key-decisions:
  - "Compound-assertion split for the empty-state test (two separate `in haystack` substrings: «Загрузите документ» AND «(DOCX или PDF)») — catches partial-fix regressions and gives diagnostic-message specificity per CLAUDE.md «and в имени теста = разделить»."
  - "Function name `test_app_empty_state_visible_without_docx` preserved despite the assertion content changing — matches the Plan 07-01 `test_app_upload_contract_unchanged` precedent (keep regression-guard name, evolve contract content)."
  - "Locked-substring duality: «PDF блок» is the invariant Plan 07-01 §truth, «требует ручной проверки» is the new reviewer-facing addition — both asserted separately so future copy churn can drift one substring without losing the regression-guard on the other."

patterns-established:
  - "Cosmetic-fix TDD pattern: (a) RED test that captures both the OLD assertion-removal AND the NEW substring; (b) GREEN edit is pure string-literal replacement with zero line-count drift; (c) verification gate confirms both the new assertions pass AND adjacent invariants (image-only-page sentinel, etc.) remain untouched."

requirements-completed: [REQ-pdf-text-only]

duration: ~5min inline (2 atomic commits) + 9.7s test runtime
completed: 2026-05-15T13:30:00Z
---

# Phase 07-05: G-07-02 + G-07-03 Gap Closure — Copy + Wording

**Empty-state alert mirrors sidebar uploader («Загрузите документ (DOCX или PDF), чтобы начать аудит»); text-block PDF audit reason reframed to «PDF блок — текстовый слой, требует ручной проверки».**

## Performance

- **Duration:** ~5 min (Task 1 RED → Task 2 GREEN)
- **Started:** 2026-05-15T13:25:00Z
- **Completed:** 2026-05-15T13:30:00Z
- **Tasks:** 2 (1 TDD-RED, 1 TDD-GREEN)
- **Files modified:** 4 (2 tests, 2 prod)
- **Execution path:** Inline by orchestrator (same agent-layer regression observed on 07-04 carried forward; bypassed via direct orchestrator execution).

## Accomplishments

### Task 1 (RED — commit `57dac86`)
- `tests/test_app_ui.py::test_app_empty_state_visible_without_docx` updated:
  - Docstring rewrites to reference Phase 7 D-04 §3 + G-07-02
  - Single assertion `"Загрузите DOCX-документ" in haystack` split into two compound assertions: `"Загрузите документ"` AND `"(DOCX или PDF)"`
  - Function name preserved (regression-guard role continues)
  - Boilerplate harvesting loop untouched (lines 38-44 in original byte-identical)
- `tests/inference/test_pdf_loader.py::test_extract_pdf_blocks_text_block_reviewer_wording` added:
  - Inserted immediately after `test_extract_pdf_blocks_image_only_page_sentinel` (sentinel test untouched, out of scope)
  - Asserts `rows[0]["status"] == "review"`, «PDF блок» substring (Plan 07-01 §truth invariant), and «требует ручной проверки» substring (G-07-03 fix)
  - Deferred import style matches Plan 07-01 convention
- Both tests observed FAILING on streamlit-enabled venv (pre-fix state confirmed RED)

### Task 2 (GREEN — commit `9500121`)
- `app.py` `st.info` empty-state alert: «Загрузите DOCX-документ, чтобы начать аудит» → «Загрузите документ (DOCX или PDF), чтобы начать аудит» (G-07-02)
- `src/inference/pdf_loader.py` `extract_pdf_blocks` text-block explanation: «PDF блок — классификация недоступна (SVM требует DOCX-формата)» → «PDF блок — текстовый слой, требует ручной проверки» (G-07-03)
- Both edits are pure 1-for-1 line replacements (zero line-count drift in either file)
- `st.warning("Сначала загрузите DOCX-документ.")` transient action prompt in `run_processing` UNTOUCHED (different surface, out of scope)
- Image-only-page sentinel «PDF page — без извлекаемого текста» UNTOUCHED (its test still passes verbatim)
- Both RED tests now GREEN

## Test State (post-fix)

- `tests/test_app_ui.py::test_app_empty_state_visible_without_docx`: PASS
- `tests/inference/test_pdf_loader.py::test_extract_pdf_blocks_text_block_reviewer_wording`: PASS
- `tests/inference/test_pdf_loader.py::test_extract_pdf_blocks_image_only_page_sentinel`: PASS (untouched — sentinel string verbatim)
- `tests/inference/test_pdf_loader.py::test_extract_pdf_blocks_schema`: PASS (untouched)
- Combined `tests/inference/ tests/test_run_processing_pdf_bypass.py`: 16/16 PASS in 9.70s

## Commits

- `57dac86` test(07-05): RED — G-07-02 empty-state copy + G-07-03 PDF reason wording
- `9500121` fix(07-05): empty-state copy + PDF reason wording (G-07-02 + G-07-03)

## Self-Check

- [x] All 2 tasks executed atomically
- [x] Each task committed individually
- [x] SUMMARY.md created and to be committed in this commit
- [x] No modifications to STATE.md or ROADMAP.md
- [x] G-07-02 closed: `grep -c "Загрузите документ (DOCX или PDF), чтобы начать аудит" app.py` = 1; `grep -c "Загрузите DOCX-документ, чтобы начать аудит" app.py` = 0
- [x] G-07-03 closed: `grep -c "PDF блок — текстовый слой, требует ручной проверки" src/inference/pdf_loader.py` = 1; locked substring «PDF блок» count = 1 (preserved); image-only-page sentinel «PDF page — без извлекаемого текста» count = 1 (preserved)
- [x] `st.warning("Сначала загрузите DOCX-документ.")` transient prompt UNTOUCHED (count = 1, unchanged from pre-plan)
- [x] Zero line-count drift in app.py and src/inference/pdf_loader.py (pure 1-for-1 replacements)
- [x] Phase 7 test surface 16/16 GREEN (no regression)

## Self-Check: PASSED
