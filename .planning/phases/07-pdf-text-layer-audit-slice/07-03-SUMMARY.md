---
phase: 07-pdf-text-layer-audit-slice
plan: 03
subsystem: ui
tags: [streamlit, pdf, audit-only, render-report, preflight, copy, readme]

requires:
  - phase: 07-pdf-text-layer-audit-slice
    provides: ProcessingArtifacts.input_extension + process_document PDF branch + PdfNoTextLayer exception (plan 07-02)
  - phase: 07-pdf-text-layer-audit-slice
    provides: 13 RED tests in tests/inference/test_pdf_loader.py + 2 RED tests in tests/test_render_report_pdf.py (plan 07-01)
provides:
  - Sidebar uploader accepts .docx + .pdf, label «Загрузите документ (DOCX или PDF)», caption «PDF: только аудит, без OCR»
  - preflight_translate_error PDF branch returns canonical Russian string with trailing period for PdfNoTextLayer
  - run_processing except-tuple swaps NotImplementedError → PdfNoTextLayer
  - render_report shows audit-only badge «PDF — режим аудита, без исправлений» when input_extension == '.pdf'
  - render_report hides «Исправленный DOCX» download card when input_extension == '.pdf'
  - README §Limits paragraph with locked substrings audit-only / text layer / OCR / no corrected PDF
affects: [phase-8-milestone-acceptance, gap-fix-plans-07-04-07-05]

tech-stack:
  added: []
  patterns:
    - "Two-condition gate on artifact downloads: extension AND artifact-exists (e.g., result.input_extension != '.pdf' AND result.output_docx is not None AND .exists())"
    - "Locked-copy contract: full Russian message stored verbatim in app.py (single source of truth), tests assert substring not equality so the canonical form can drift without breaking tests"

key-files:
  created: []
  modified:
    - app.py
    - README.md

key-decisions:
  - "Canonical preflight rejection string locks the trailing-period form «PDF без извлекаемого текстового слоя — OCR не поддерживается.» — matches UI-SPEC §Error state copy; 07-CONTEXT.md D-03 records the form without the period but tests assert substrings so both forms collide cleanly."
  - "render_report DOCX gate is two-condition (extension AND output_docx exists). Audit mode produces output_docx=None even for DOCX, so the DOCX download button is also hidden in audit mode for DOCX — Phase 6 behavior preserved; Phase 7 PDF gate is verified by Test 3 (PDF input + button absent regardless of output_docx)."

patterns-established:
  - "Audit-only signal pattern: an amber `.badge.badge-warn` badge surface alongside hidden actionable buttons signals «read-only / no autofix» for the entire report section without needing per-block flagging"

requirements-completed: [REQ-pdf-text-only]

duration: ~7min (3 code commits + 1 README commit) + ~45min UAT
completed: 2026-05-15T12:15:00Z
---

# Phase 07-03: UI Uploader + Render Gating + README §Limits

**Streamlit uploader, error path, and report-header gating now treat PDF as an audit-only first-class input; README §Limits documents the contract.**

## Performance

- **Duration:** ~7 min implementation + ~45 min Playwright UAT
- **Started:** 2026-05-15T08:35:00Z
- **Completed:** 2026-05-15T12:15:00Z
- **Tasks:** 4 (3 autonomous + 1 human-verify checkpoint)
- **Files modified:** 2 (`app.py`, `README.md`)

## Accomplishments

### Sidebar (Task 1 — commit `957b283`)
- `SUPPORTED_UPLOAD_TYPES = ["docx", "pdf"]`
- Imports `PdfNoTextLayer` from `src.inference.pdf_loader`
- `preflight_translate_error(PdfNoTextLayer)` returns the canonical Russian rejection string with trailing period
- `run_processing` except-tuple: `(FileNotFoundError, PdfNoTextLayer, ValueError, zipfile.BadZipFile)` — `NotImplementedError` removed (Pitfall 3 from 07-RESEARCH.md)
- Uploader label «Загрузите документ (DOCX или PDF)» + caption «PDF: только аудит, без OCR»

### Render-Report Gating (Task 2 — commit `fa67338`)
- `render_report(result, filename=None)` accepts an optional filename param
- Badge «PDF — режим аудита, без исправлений» rendered via existing `.badge.badge-warn` CSS class when `result.input_extension == ".pdf"` (no new CSS class introduced — Phase 6 contract preserved)
- «Исправленный DOCX» download card gated on `result.input_extension != ".pdf" AND result.output_docx is not None AND result.output_docx.exists()` — PDF inputs ALWAYS hide the button; DOCX inputs hide it only when `output_docx` is unavailable (Phase 6 behavior)

### README §Limits (Task 3 — commit `7374b1e`)
- New `## Limits` section with locked substrings: «audit-only», «text layer», «OCR is not supported», «no corrected PDF»
- `test_readme_limits_keywords` (RED in 07-01) now GREEN

### Human-Verify Checkpoint (Task 4)
- Playwright-driven E2E UAT against streamlit served from this worktree (`worktree-agent-ae7c41d1`) on `http://localhost:8501`
- Sidebar uploader controls verified (snap-03)
- Berger PDF audit pipeline runs to completion: 319 blocks all in «Требуют проверки», 0 errors, badge present, «Исправленный DOCX» absent, 3 expected downloads present (snap-08)
- Synthesised scanned PDF (`/tmp/scanned_uat.pdf`, image-only page on Berger-shaped canvas) rejected with the exact locked Russian banner verbatim including trailing period (snap-10)
- Persisted run-log JSON (`results/reports/scanned_uat_run_log_20260515_145952.json`) confirmed: `status: "error"`, `error_class: "PdfNoTextLayer"`, locked message, no traceback, no PII (matches UI-SPEC §Run-log JSON contract + D-04 PII boundary)
- DOCX regression test (positive corpus fixture `4.docx`) confirmed no badge for DOCX input + audit pipeline unchanged (snap-12)

## UAT Verdict

**APPROVED with 3 gaps deferred to follow-up plans (07-04 + 07-05):**

- **G-07-01 (major, deferred to 07-04):** `app.py:run_processing` short-circuits on `selected_model_key == "baseline_unavailable"` BEFORE `process_document` is invoked, blocking the PDF audit-only flow when the workspace lacks a baseline `.joblib`. UAT was unblocked by copying a legacy `.joblib` into `results/models/`; the guard logic must be widened to bypass for `.pdf` suffix.
- **G-07-02 (cosmetic, deferred to 07-05):** Main-pane empty-state alert still reads «Загрузите DOCX-документ, чтобы начать аудит» — Phase 6 leftover, now inconsistent with the sidebar uploader copy.
- **G-07-03 (cosmetic, deferred to 07-05):** Per-block PDF audit reason text in `src/inference/extract_pdf_blocks` reads «PDF блок — классификация недоступна (SVM требует DOCX-формата)» — framed from the model's POV rather than the reviewer's. Substring «PDF блок» (the plan-locked truth) is preserved; phrasing is the only concern.

Gap details: `.planning/phases/07-pdf-text-layer-audit-slice/07-UAT.md` `## Gaps` section. Fix plans created via `/gsd-plan-phase --gaps 7` (commit `030943d`).

## Phase 7 SC Closure (Code-Level)

| SC | Truth | Status |
|----|-------|--------|
| SC-1 | UI uploader accepts `.pdf` alongside `.docx` | ✓ code (07-03 §sidebar) + ✓ UAT (Test 1) |
| SC-2 | PDF flow audit-only, never writes corrected DOCX | ✓ code (process_document branch from 07-02 + render_report gate) + ✓ UAT (Tests 2/3/4) |
| SC-3 | PDF uploader clearly labelled as audit-only | ✓ code (sidebar caption + badge) + ✓ UAT (Tests 1/3) |
| SC-4 | Scanned PDFs rejected with locked Russian banner + clean run-log | ✓ code (preflight branch + except-tuple) + ✓ UAT (Tests 5/6) |

All 4 success criteria met at the code level. G-07-01 lifts an environment-dependent constraint (workspace baseline artifact presence) that the UAT exposed but is not strictly part of the SC truths.

## Test State

- 13 tests in `tests/inference/test_pdf_loader.py`: 13/13 GREEN (README test flipped to GREEN by this plan's README §Limits addition)
- 2 tests in `tests/test_render_report_pdf.py`: collection-time `pytest.importorskip("streamlit")` (skip cleanly on a streamlit-less env; on a streamlit-enabled venv they assert the badge + DOCX gate by monkeypatching Streamlit primitives — the actual assertions are exercised by the Playwright UAT against the live app)
- 5 tests in `tests/test_preflight.py`, 2 in `tests/test_app_upload_contract.py`, 9 in `tests/test_render_block_section.py`: all collect cleanly (importorskip guards added in Wave 1 fix-up commits `b4b93ef` + `176f526`)
- Phase 1-6 regression suite: 156 passed, 13 skipped — zero regressions (per 07-02-SUMMARY post-implementation test run)

## Commits

- `957b283` feat(07-03): extend upload types, swap preflight branch, fix except tuple, update sidebar label+caption
- `fa67338` feat(07-03): render_report — add audit-only badge + gate corrected-DOCX download for PDF input
- `7374b1e` docs(07-03): add README §Limits section — audit-only, text layer, no OCR, no corrected PDF

## Self-Check

- [x] All 4 tasks executed (3 autonomous + 1 human-verify)
- [x] Each task committed individually with `--no-verify` (worktree mode)
- [x] SUMMARY.md created and to be committed in this commit
- [x] STATE.md / ROADMAP.md not modified (orchestrator owns those writes post-merge)
- [x] No new CSS classes introduced (existing `.badge.badge-warn` reused per UI-SPEC)
- [x] PII boundary preserved (D-04): no document text, no traceback in error path
- [x] Canonical preflight string locked WITH trailing period (W2 resolution)
- [x] Human-verify checkpoint approved with 3 follow-up gaps logged in 07-UAT.md

## Self-Check: PASSED
