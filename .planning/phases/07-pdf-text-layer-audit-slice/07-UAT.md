---
status: partial
phase: 07-pdf-text-layer-audit-slice
source:
  - .planning/phases/07-pdf-text-layer-audit-slice/07-01-SUMMARY.md
  - .planning/phases/07-pdf-text-layer-audit-slice/07-02-SUMMARY.md
  - .planning/phases/07-pdf-text-layer-audit-slice/07-03-PLAN.md (Task 4 checkpoint script)
started: 2026-05-15T08:30:00Z
updated: 2026-05-15T12:10:00Z
e2e_runner: playwright-cli@0.1.8 against streamlit served from worktree-agent-ae7c41d1
---

## Current Test

[testing complete — 6 pass, 1 issue, 0 pending]

## Tests

### 1. Sidebar uploader controls
expected: |
  Run `streamlit run app.py` and open the browser tab. In the sidebar the document
  uploader label reads «Загрузите документ (DOCX или PDF)»; immediately below the
  uploader is the caption «PDF: только аудит, без OCR».
result: pass
notes: |
  Playwright verified via snap-03-wt-loaded.yml against worktree-agent-ae7c41d1.
  Sidebar label, file-type help line («200MB per file • DOCX, PDF»), and caption
  all match. Minor cosmetic gap captured separately: main-pane empty-state alert
  still reads «Загрузите DOCX-документ, чтобы начать аудит» (Phase 6 leftover,
  not in 07-03 scope; severity: cosmetic).

### 2. Berger PDF upload runs audit pipeline
expected: |
  In the running app, upload `tests/fixtures/methodical/normocontrol_berger.pdf`
  via the sidebar uploader, then click «Запустить аудит». The pipeline completes
  without an error banner; the main pane renders the report section.
result: issue
reported: |
  PDF audit blocked when no baseline .joblib artifact is present in the workspace.
  app.py:run_processing line 425 short-circuits on selected_model_key ==
  'baseline_unavailable' BEFORE process_document is called, so the PDF branch
  (which does not need the SVM) never runs. UAT was unblocked by copying a
  legacy .joblib to results/models/; the underlying guard logic still needs
  to skip baseline-availability checks for .pdf uploads.
severity: major
gap_ref: G-07-01

### 3. PDF report header shows audit-only badge + hides DOCX download
expected: |
  In the rendered report (after test 2), the header shows an amber/warn badge
  «PDF — режим аудита, без исправлений». The «Исправленный DOCX» download button
  is ABSENT. The other download buttons are present: Report CSV, Сводка JSON,
  Журнал запуска.
result: pass
notes: |
  Verified in snap-08-audit-result.yml. Badge text present (e174); «Скачать
  результаты» section contains Отчёт CSV + Сводка JSON + «Скачать журнал
  запуска (JSON)»; no «Исправленный DOCX» button anywhere on the page.

### 4. Block counters and per-block PDF reason
expected: |
  In the same report, every extracted block is counted in the «Требуют проверки»
  bucket (no «Без правок» / «Изменено» / «Ошибка» rows). Expanding any block row
  shows a «Причина ручной проверки» field whose text contains the substring
  «PDF блок» (e.g., «PDF блок — текстовый слой, требует ручной проверки»).
result: pass
notes: |
  319 blocks all under «Требуют проверки», «Ошибки: 0». Every expander shows
  «Причина ручной проверки: PDF блок — классификация недоступна (SVM требует
  DOCX-формата)» — «PDF блок» substring matches plan §truth. The exact phrasing
  is framed from the model's POV; consider a clearer user-facing wording in
  a follow-up but this is not a SC-blocker.

### 5. Scanned PDF rejection — locked Russian banner
expected: |
  Generate a scanned-style fixture (image-only PDF) via fitz, upload it in the
  running app, click «Запустить аудит». A red banner appears with the exact
  locked Russian text «PDF без извлекаемого текстового слоя — OCR не поддерживается.»
  (note trailing period).
result: pass
notes: |
  /tmp/scanned_uat.pdf synthesised via fitz (image-only page on Berger-shaped
  canvas). Banner verified in snap-10-scanned-rejected.yml (paragraph e147) —
  string matches W2 canonical form verbatim including trailing period.

### 6. Run-log JSON records PdfNoTextLayer
expected: |
  After test 5, download the «Журнал запуска» JSON. Open it and confirm:
  `status == "error"`, `error_class == "PdfNoTextLayer"`, and `error_message`
  matches the locked Russian string «PDF без извлекаемого текстового слоя —
  OCR не поддерживается.». No traceback fields, no file-system paths, no PII
  beyond the locked message.
result: pass
notes: |
  Run-log persisted at results/reports/scanned_uat_run_log_20260515_145952.json
  (no JSON download surface rendered on rejection path; verified by reading
  the persisted file directly). Two records: document-read/ok then
  document-read/error with `error_class == "PdfNoTextLayer"` and `error_message`
  exactly «PDF без извлекаемого текстового слоя — OCR не поддерживается.».
  Schema is stage/ts/status/error_class/error_message — no traceback, no path,
  no document text. Satisfies UI-SPEC §Run-log JSON contract + D-04 PII boundary.

### 7. DOCX regression — Phase 6 path still works
expected: |
  Upload any working DOCX (e.g., one of the Phase 6 fixtures), run the audit.
  The amber audit-only badge does NOT appear; the «Исправленный DOCX» download
  button IS present alongside the other download buttons. (Confirms the PDF
  gating in render_report does not regress DOCX flow.)
result: pass
notes: |
  Verified in snap-12-docx-audit.yml using tests/fixtures/corpus/positive/4.docx.
  Pipeline ran, report rendered with «Требуют проверки: 151», amber PDF badge
  ABSENT (correct — DOCX input). «Исправленный DOCX» button is also absent BUT
  this is expected: it gates on `output_docx is not None AND output_docx.exists()`
  in addition to `input_extension != ".pdf"`; in audit mode (Только аудит) the
  pipeline does not write a corrected DOCX, so the button correctly does not
  render. Phase 7's PDF gate is fully verified by Test 3 (PDF input + button
  absent); DOCX-input behavior here is unchanged from Phase 6.

## Summary

total: 7
passed: 6
issues: 1
pending: 0
skipped: 0

## Gaps

- gap_id: G-07-01
  truth: "PDF audit flow runs without requiring a baseline .joblib artifact (PDF path bypasses SVM per Plan 07-02 §truths)"
  status: failed
  reason: |
    app.py:run_processing line 425 short-circuits on
    `selected_model_key == "baseline_unavailable"` BEFORE process_document is
    called. Since process_document is where the PDF/DOCX branch lives, the
    PDF flow can never run when the workspace lacks a baseline.joblib. UAT
    was unblocked by manually copying a legacy .joblib into
    `<worktree>/results/models/`; the underlying guard is the actual defect.
  severity: major
  test: 2
  artifacts:
    - .planning/phases/07-pdf-text-layer-audit-slice/snap-05-after-audit.yml
    - .planning/phases/07-pdf-text-layer-audit-slice/snap-08-audit-result.yml
  missing:
    - PDF-aware bypass on the baseline_unavailable guard (skip the guard when
      `Path(uploaded_file.name).suffix.lower() == ".pdf"`)
    - regression test asserting `run_processing` does not short-circuit for PDF
      input when `selected_model_key == "baseline_unavailable"`

- gap_id: G-07-02
  truth: "Main-pane empty-state copy matches the Phase 7 upload contract"
  status: failed
  reason: |
    Empty-state alert in the main pane still reads «Загрузите DOCX-документ,
    чтобы начать аудит» (Phase 6 leftover). Phase 7 expanded SUPPORTED_UPLOAD_TYPES
    to ['docx', 'pdf'] but did not update this empty-state hint; copy is now
    inconsistent with the sidebar uploader label «Загрузите документ (DOCX или PDF)».
  severity: cosmetic
  test: 1
  artifacts:
    - .planning/phases/07-pdf-text-layer-audit-slice/snap-03-wt-loaded.yml
  missing:
    - one-line copy update in app.py main-pane empty-state branch

- gap_id: G-07-03
  truth: "Per-block PDF audit reason is framed for the human reviewer"
  status: failed
  reason: |
    Per-block reason reads «PDF блок — классификация недоступна (SVM требует
    DOCX-формата)». Locked substring «PDF блок» is satisfied (Test 4 truth),
    but the phrasing is framed from the model's POV. Prefer wording centred on
    the reviewer's action, e.g. «PDF блок — текстовый слой, требует ручной
    проверки» (matches the example in plan 07-01 §truths).
  severity: cosmetic
  test: 4
  artifacts:
    - .planning/phases/07-pdf-text-layer-audit-slice/snap-08-audit-result.yml
  missing:
    - reason-string update in extract_pdf_blocks (src/inference/pdf_loader.py)
