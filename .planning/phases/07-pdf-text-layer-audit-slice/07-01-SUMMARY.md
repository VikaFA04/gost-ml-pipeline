---
phase: 07
plan: 01
subsystem: tests
tags: [pdf, audit, tdd, red, fitz, streamlit]
dependency_graph:
  requires: []
  provides:
    - tests/inference/test_pdf_loader.py (13 RED tests for Wave 1 + Wave 2)
    - tests/test_render_report_pdf.py (2 RED tests for Wave 2)
    - tests/inference/conftest.py (text_pdf + scanned_pdf fitz fixtures + BERGER_PDF)
  affects:
    - tests/test_preflight.py (dead test deleted, PdfNoTextLayer test added)
    - tests/test_app_upload_contract.py (upload type assertion flipped)
    - tests/test_render_block_section.py (upload type assertion flipped)
tech_stack:
  added: []
  patterns:
    - Deferred import inside test body (from src.inference.pdf_loader import ...) keeps --collect-only clean before Wave 1 implementation
    - fitz tmp_path fixture synthesis (no committed binary, 24.5 KB scanned PDF per Pitfall 7)
    - pytest.importorskip("streamlit") gate on Streamlit-dependent test files
key_files:
  created:
    - tests/inference/__init__.py
    - tests/inference/conftest.py
    - tests/inference/test_pdf_loader.py
    - tests/test_render_report_pdf.py
  modified:
    - tests/test_preflight.py
    - tests/test_app_upload_contract.py
    - tests/test_render_block_section.py
decisions:
  - Deferred imports inside test bodies chosen over module-level imports to keep pytest --collect-only clean before Wave 1 lands pdf_loader.py
  - scanned_pdf synthesised via fitz rasterise+re-save in tmp_path (24.5 KB, no committed binary per Pitfall 7)
  - PdfNoTextLayer test uses str arg "ratio=0.0" to match locked Wave 1 exception signature
metrics:
  duration: 243s
  completed: 2026-05-15
  tasks: 4
  files: 7
---

# Phase 07 Plan 01: Wave 0 RED Tests — PDF Text-Layer Audit Slice Summary

**One-liner:** 13+2 RED TDD tests establishing the full Wave 1+2 contract for PDF text-layer audit: check_text_layer thresholds, extract_pdf_blocks schema, ProcessingArtifacts.input_extension, output_docx=None, CSV sentinels, Berger end-to-end, render_report badge + DOCX gate.

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create tests/inference/ scaffolding + fitz fixtures | f140769 | tests/inference/__init__.py, tests/inference/conftest.py |
| 2 | Write 13 RED tests in tests/inference/test_pdf_loader.py | b07dab7 | tests/inference/test_pdf_loader.py |
| 3 | Update test_preflight.py + test_app_upload_contract.py + test_render_block_section.py | 7968c3b | tests/test_preflight.py, tests/test_app_upload_contract.py, tests/test_render_block_section.py |
| 4 | Write 2 RED tests in tests/test_render_report_pdf.py | 280689c | tests/test_render_report_pdf.py |

## RED Count

```
python3 -m pytest tests/inference/ tests/test_preflight.py tests/test_render_block_section.py tests/test_render_report_pdf.py 2>&1 | tail -1
```
Result: `13 failed, 3 skipped, 5 warnings in 2.47s`

- 13 failures: all in `tests/inference/test_pdf_loader.py` — `ModuleNotFoundError` on `src.inference.pdf_loader` (not yet implemented) + `TypeError` on `ProcessingArtifacts` missing `input_extension` field
- 3 skipped: Streamlit-gated tests skipped cleanly on system Python (test_preflight.py, test_render_block_section.py, test_render_report_pdf.py) — correct behavior on system Python without Streamlit
- `tests/test_app_upload_contract.py` fails at collection on system Python (bare `import app` without importorskip gate — pre-existing design; RED on Streamlit-enabled venv where `SUPPORTED_UPLOAD_TYPES == ["docx"]` still)

## Deleted Test

- **test_preflight_translate_not_implemented_pdf** — DELETED from `tests/test_preflight.py` (dead code per Pitfall 3 in 07-RESEARCH.md; the NotImplementedError raise in validate_document_input is deleted in Wave 1)

## New Test Names

### tests/test_preflight.py (new)
- `test_preflight_translate_pdf_no_text_layer` — asserts locked Russian substrings «PDF без извлекаемого текстового слоя» + «OCR не поддерживается» + PII boundary (no Traceback, no raw ratio)

### tests/inference/test_pdf_loader.py (B1+B3 resolution)
- `test_pdf_output_docx_none` — process_document on text_pdf returns ProcessingArtifacts.output_docx is None
- `test_berger_end_to_end` — process_document on Berger PDF returns input_extension=".pdf", non-empty report_df, all status="review"
- `test_pdf_artifacts_predictions_csv_sentinel` — ProcessingArtifacts.predictions_csv == report_csv (B3 sentinel)
- `test_pdf_artifacts_extracted_csv_sentinel` — ProcessingArtifacts.extracted_csv == report_csv (B3 sentinel)

### tests/test_render_report_pdf.py (W1 resolution)
- `test_render_report_pdf_badge_renders` — render_report emits st.markdown with «PDF — режим аудита, без исправлений»
- `test_render_report_pdf_hides_docx_download` — render_artifact_download_card NOT called with key="download_output_docx" for PDF

## File Sizes (sanity)

| File | Size |
|------|------|
| tests/inference/conftest.py | 1,187 bytes |
| tests/inference/test_pdf_loader.py | 5,315 bytes |
| tests/test_render_report_pdf.py | 4,388 bytes |

All well under 10 KB per plan requirement.

## Deviations from Plan

None — plan executed exactly as written. All test bodies match the verbatim patterns from the plan's `<action>` sections. The acceptance criteria grep counts for "PDF — режим аудита, без исправлений" (3 occurrences vs. "exactly 1" stated) is a minor discrepancy in the plan itself — the verbatim test body from the plan contains the string 3 times (2 assertion lines + 1 error message). This does not affect correctness.

## Open Question for Wave 1

`PdfNoTextLayer.__init__` signature must accept a single `str` arg — the test uses `PdfNoTextLayer("ratio=0.0")`. Wave 1 implementation in `src/inference/pdf_loader.py` must define the class to accept a string argument (standard `Exception` subclass with no custom `__init__` satisfies this).

## TDD Gate Compliance

This plan is a pure RED-phase plan (type: tdd, Wave 0). All 4 tasks create tests only — no production code committed. The RED gate is confirmed:
- tests/inference/test_pdf_loader.py: 13 tests FAIL with ModuleNotFoundError/TypeError/AttributeError
- tests/test_render_report_pdf.py: 2 tests SKIP (Streamlit absent) — will FAIL on Streamlit-enabled venv with AttributeError: 'ProcessingArtifacts' object has no attribute 'input_extension'
- No `feat(...)` commit exists — GREEN gate is Wave 1 (Plan 07-02)

## Self-Check: PASSED

Files exist:
- tests/inference/__init__.py: FOUND
- tests/inference/conftest.py: FOUND
- tests/inference/test_pdf_loader.py: FOUND
- tests/test_render_report_pdf.py: FOUND
- tests/test_preflight.py: FOUND (modified)
- tests/test_app_upload_contract.py: FOUND (modified)
- tests/test_render_block_section.py: FOUND (modified)

Commits exist:
- f140769: FOUND (scaffold)
- b07dab7: FOUND (13 RED tests)
- 7968c3b: FOUND (preflight + upload contract updates)
- 280689c: FOUND (2 render_report RED tests)
