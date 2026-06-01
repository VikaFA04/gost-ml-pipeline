---
phase: 07
slug: pdf-text-layer-audit-slice
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-15
revised: 2026-05-15
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Revised per checker issue B2 — template shell replaced with actual per-task content. Updated 2026-05-15 post-execution: all 15 tasks verified green (38/38 tests pass on Streamlit-enabled venv).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (no version pin file; project uses ad-hoc `python -m pytest`) |
| **Config file** | none at repo root — `tests/conftest.py` injects REPO_ROOT into `sys.path`; no `pyproject.toml`/`pytest.ini`/`setup.cfg` |
| **Venv** | `/tmp/gost-test-venv/bin/python` (Python 3.12, streamlit + fitz + pandas + torch + transformers + sklearn + joblib + python-docx) |
| **Quick smoke command** | `/tmp/gost-test-venv/bin/python -m pytest tests/inference/test_pdf_loader.py tests/test_render_report_pdf.py tests/test_run_processing_pdf_bypass.py -x -q` |
| **Phase 7 surface command** | `/tmp/gost-test-venv/bin/python -m pytest tests/inference/ tests/test_preflight.py tests/test_app_upload_contract.py tests/test_render_block_section.py tests/test_render_report_pdf.py tests/test_run_processing_pdf_bypass.py tests/test_app_ui.py -x -q` |
| **Full suite command** | `/tmp/gost-test-venv/bin/python -m pytest tests/` |
| **Estimated quick-smoke runtime** | ~14s (verified 2026-05-15) |
| **Estimated full-suite runtime** | ~60–120s |

---

## Sampling Rate

- **After every task commit:** Run the quick smoke command: `/tmp/gost-test-venv/bin/python -m pytest tests/inference/test_pdf_loader.py tests/test_render_report_pdf.py tests/test_run_processing_pdf_bypass.py -x -q`
- **After every plan wave:** Run the Phase 7 surface command.
- **Before `/gsd-verify-work`:** Full suite must be green (`/tmp/gost-test-venv/bin/python -m pytest tests/`).
- **Max feedback latency (Nyquist target):** 20 seconds (quick smoke) — tight enough to fail fast on any RED regression during TDD cycles.
- **No watch-mode flags** in any task `<verify>` block (verified by grep — see Sign-Off checklist).

---

## Per-Task Verification Map

Status legend: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 0 | REQ-pdf-text-only | T-07-W0-02 | fitz fixtures bounded to tmp_path; no committed binaries | scaffolding | `/tmp/gost-test-venv/bin/python -m pytest tests/inference/ --collect-only` | ✅ | ✅ green |
| 07-01-02 | 01 | 0 | REQ-pdf-text-only / SC-1, SC-2, SC-4 | T-07-W0-01, T-07-W0-03 | 14 tests assert backend contract (check_text_layer, extract_pdf_blocks, ProcessingArtifacts.input_extension + sentinels, Berger end-to-end, README §Limits keywords, reviewer wording) | unit + integration | `/tmp/gost-test-venv/bin/python -m pytest tests/inference/test_pdf_loader.py --collect-only 2>&1 \| grep "collected"` | ✅ | ✅ green |
| 07-01-03 | 01 | 0 | REQ-pdf-text-only / SC-1, SC-3 | T-07-W0-01, T-07-W0-03 | DELETE dead `test_preflight_translate_not_implemented_pdf`; ADD `test_preflight_translate_pdf_no_text_layer` with PII boundary asserts; flip upload-contract assertions in BOTH carrier files | unit | `/tmp/gost-test-venv/bin/python -m pytest tests/test_preflight.py tests/test_app_upload_contract.py tests/test_render_block_section.py --collect-only 2>&1 \| tail -5` | ✅ | ✅ green |
| 07-01-04 | 01 | 0 | REQ-pdf-text-only / SC-3 (W1 resolution) | T-07-W2-01, T-07-W2-04 | 2 tests assert render_report renders the audit-only badge AND does NOT render the corrected-DOCX download card for `input_extension='.pdf'` (captured via monkeypatched Streamlit) | unit | `/tmp/gost-test-venv/bin/python -m pytest tests/test_render_report_pdf.py --collect-only 2>&1 \| grep "collected"` | ✅ | ✅ green |
| 07-02-01 | 02 | 1 | REQ-pdf-text-only / SC-1, SC-2 | T-07-W1-01..05 | Create `pdf_loader.py` (PdfNoTextLayer + check_text_layer + extract_pdf_blocks); fitz lifecycle in try/finally; Arabic strip; 500-char cap; no `str(exc)` propagation | unit (TDD) | `/tmp/gost-test-venv/bin/python -m pytest tests/inference/test_pdf_loader.py::test_check_text_layer_berger_accepted tests/inference/test_pdf_loader.py::test_check_text_layer_scanned_rejected tests/inference/test_pdf_loader.py::test_check_text_layer_zero_page_returns_zero tests/inference/test_pdf_loader.py::test_check_text_layer_50pct_threshold_inclusive tests/inference/test_pdf_loader.py::test_extract_pdf_blocks_schema tests/inference/test_pdf_loader.py::test_extract_pdf_blocks_block_id_format tests/inference/test_pdf_loader.py::test_extract_pdf_blocks_image_only_page_sentinel -x` | ✅ | ✅ green |
| 07-02-02 | 02 | 1 | REQ-pdf-text-only / SC-1, SC-2 | T-07-W1-01..07 | Add `ProcessingArtifacts.input_extension`; delete `NotImplementedError` block in `document_loader.py`; delete DOCX-only guard in `application_service.py:process_document`; add `_process_pdf` helper; predictions_csv=extracted_csv=report_csv sentinels (B3) | unit + integration (TDD) | `/tmp/gost-test-venv/bin/python -m pytest tests/inference/test_pdf_loader.py -x` | ✅ | ✅ green |
| 07-03-01 | 03 | 2 | REQ-pdf-text-only / SC-1, SC-3 | T-07-W2-02, T-07-W2-03, T-07-W2-04 | app.py — extend SUPPORTED_UPLOAD_TYPES; swap preflight branch to PdfNoTextLayer (canonical period form per W2); update run_processing except tuple; change uploader label + add sidebar caption | unit + integration | `/tmp/gost-test-venv/bin/python -m pytest tests/test_preflight.py tests/test_app_upload_contract.py tests/test_render_block_section.py -x 2>&1 \| tail -5` | ✅ | ✅ green |
| 07-03-02 | 03 | 2 | REQ-pdf-text-only / SC-2, SC-3 | T-07-W2-01, T-07-W2-04 | app.py:render_report — insert audit-only badge gated on `input_extension==".pdf"`; widen DOCX-download `if` to also check `input_extension!=".pdf"`; reuse `.badge.badge-warn` (no new CSS) | unit | `/tmp/gost-test-venv/bin/python -m pytest tests/inference/test_pdf_loader.py tests/test_render_report_pdf.py -x` | ✅ | ✅ green |
| 07-03-03 | 03 | 2 | REQ-pdf-text-only / SC-4 | T-07-W2-05 | README.md — add `## Limits` English section with 4 locked substrings (audit-only, text layer, OCR is not supported / no OCR, no corrected PDF) | static | `/tmp/gost-test-venv/bin/python -m pytest tests/inference/test_pdf_loader.py::test_readme_limits_keywords -x` | ✅ | ✅ green |
| 07-03-04 | 03 | 2 | REQ-pdf-text-only / SC-1, SC-2, SC-3, SC-4 | T-07-W2-01..05 | Manual UAT (human-verify checkpoint) — Streamlit upload flow + scanned-PDF rejection path; verifies what unit tests cannot (visual badge, hidden DOCX card, real Streamlit rendering) | manual | MANUAL — `streamlit run app.py` + upload `tests/fixtures/methodical/normocontrol_berger.pdf` + upload synthesised scanned PDF; 8 verification points per Plan 07-03 Task 4 `<verify>` block | n/a | ✅ green |
| 07-04-01 | 04 | 3 | REQ-pdf-text-only / G-07-01 | T-07-04-01..05 | RED test scaffolding in `tests/test_run_processing_pdf_bypass.py` — 2 tests asserting PDF bypasses and DOCX still short-circuits on `baseline_unavailable`; gated by `pytest.importorskip("streamlit")` | unit (TDD RED) | `/tmp/gost-test-venv/bin/python -m pytest tests/test_run_processing_pdf_bypass.py --collect-only 2>&1 \| grep "collected"` | ✅ | ✅ green |
| 07-04-02 | 04 | 3 | REQ-pdf-text-only / G-07-01 | T-07-04-01..05 | GREEN guard widen in `app.py:run_processing` — `baseline_unavailable` guard now bypassed for `.pdf` suffix; DOCX still short-circuits; both tests pass | unit (TDD GREEN) | `/tmp/gost-test-venv/bin/python -m pytest tests/test_run_processing_pdf_bypass.py -v` | ✅ | ✅ green |
| 07-04-03 | 04 | 3 | REQ-pdf-text-only / G-07-01 (CLAUDE.md rule) | n/a | CLAUDE.md §Принципы исполнения gains one new императивное rule about pre-pipeline UI gates on supported-format expansion; no duplicate; under 2500-token budget | static | `grep -c "расширении набора поддерживаемых входных форматов" CLAUDE.md` | ✅ | ✅ green |
| 07-05-01 | 05 | 4 | REQ-pdf-text-only / G-07-02, G-07-03 | T-07-05-01..04 | RED test updates — `tests/test_app_ui.py::test_app_empty_state_visible_without_docx` asserts «Загрузите документ» AND «(DOCX или PDF)»; new `tests/inference/test_pdf_loader.py::test_extract_pdf_blocks_text_block_reviewer_wording` asserts «PDF блок» AND «требует ручной проверки» | unit (TDD RED) | `/tmp/gost-test-venv/bin/python -m pytest tests/test_app_ui.py::test_app_empty_state_visible_without_docx tests/inference/test_pdf_loader.py::test_extract_pdf_blocks_text_block_reviewer_wording --collect-only 2>&1 \| grep "collected"` | ✅ | ✅ green |
| 07-05-02 | 05 | 4 | REQ-pdf-text-only / G-07-02, G-07-03 | T-07-05-01..04 | GREEN string replacements — `app.py` empty-state copy mirrors sidebar uploader; `src/inference/pdf_loader.py` text-block reason is reviewer-facing; locked «PDF блок» + image-only-page sentinel both preserved | unit (TDD GREEN) | `/tmp/gost-test-venv/bin/python -m pytest tests/test_app_ui.py::test_app_empty_state_visible_without_docx tests/inference/test_pdf_loader.py::test_extract_pdf_blocks_text_block_reviewer_wording tests/inference/test_pdf_loader.py::test_extract_pdf_blocks_image_only_page_sentinel tests/inference/test_pdf_loader.py::test_extract_pdf_blocks_schema -x` | ✅ | ✅ green |

**Coverage summary:** 15 tasks across 5 plans. 14 tasks have an `<automated>` verify command. 1 task (07-03-04) is the documented manual UAT — approved in re-UAT 2026-05-15 with all 3 gaps resolved.

---

## Wave 0 Requirements

Wave 0 created these test files before Wave 1/2 implementation landed. All items verified present and green on 2026-05-15:

- [x] `tests/inference/__init__.py` — package marker (Plan 07-01 Task 1)
- [x] `tests/inference/conftest.py` — `text_pdf` + `scanned_pdf` fitz fixtures + `BERGER_PDF` constant (Plan 07-01 Task 1)
- [x] `tests/inference/test_pdf_loader.py` — 14 tests (13 original + 1 added by Plan 07-05): 4× check_text_layer, 3× extract_pdf_blocks, 1× text_block_reviewer_wording, 1× ProcessingArtifacts.input_extension, 1× README §Limits, + 4 per B1+B3: test_pdf_output_docx_none, test_berger_end_to_end, test_pdf_artifacts_predictions_csv_sentinel, test_pdf_artifacts_extracted_csv_sentinel
- [x] `tests/test_preflight.py` — DELETE `test_preflight_translate_not_implemented_pdf`; ADD `test_preflight_translate_pdf_no_text_layer` (Plan 07-01 Task 3)
- [x] `tests/test_app_upload_contract.py` — flip `SUPPORTED_UPLOAD_TYPES == ["docx"]` → `["docx", "pdf"]` (Plan 07-01 Task 3)
- [x] `tests/test_render_block_section.py` — flip `test_app_upload_contract_unchanged` assertion to `["docx", "pdf"]` (Plan 07-01 Task 3)
- [x] `tests/test_render_report_pdf.py` — 2 tests (`test_render_report_pdf_badge_renders` + `test_render_report_pdf_hides_docx_download`) using monkeypatched Streamlit capture (Plan 07-01 Task 4)

---

## Gap-Closure Test Files (Plans 07-04 + 07-05)

Added post original-draft, now part of the permanent validation surface:

- [x] `tests/test_run_processing_pdf_bypass.py` — 2 tests (G-07-01): `test_run_processing_pdf_input_bypasses_baseline_unavailable_guard` + `test_run_processing_docx_input_still_short_circuits_on_baseline_unavailable` (Plan 07-04 Tasks 1-2)
- [x] `tests/test_app_ui.py::test_app_empty_state_visible_without_docx` — assertion updated to require «Загрузите документ» AND «(DOCX или PDF)» (Plan 07-05 Task 1, G-07-02)
- [x] `tests/inference/test_pdf_loader.py::test_extract_pdf_blocks_text_block_reviewer_wording` — new test asserting «PDF блок» AND «требует ручной проверки» (Plan 07-05 Task 1, G-07-03)

---

## Manual-Only Verifications

Manual verification is required where automated coverage is impossible (real Streamlit rendering, browser-visible color/spacing, end-to-end upload UX). Every other surface has an automated verify.

| Behavior | Requirement | Why Manual | Test Instructions | Status |
|----------|-------------|------------|-------------------|--------|
| Streamlit upload `.pdf` accepted; audit-only badge visible; corrected-DOCX download card hidden; sidebar caption «PDF: только аудит, без OCR» under uploader; report-CSV + summary-JSON + run-log-JSON still downloadable | REQ-pdf-text-only / SC-3 + D-04 §§1-3 | Streamlit DOM rendering is not unit-testable | Plan 07-03 Task 4 `<verify>` block — 8 numbered steps | ✅ Approved (07-UAT.md re-UAT 2026-05-15) |
| Scanned-PDF rejection path — locked Russian `st.error` banner displays «PDF без извлекаемого текстового слоя — OCR не поддерживается.» (canonical form WITH trailing period per W2); run-log JSON has `error_class="PdfNoTextLayer"`, NO `text`/`traceback` keys leaked | REQ-pdf-text-only / SC-1 + D-03 + D-04 PII boundary | Streamlit `st.error` banner rendering requires a live browser context | Plan 07-03 Task 4 `<verify>` step 6-8 | ✅ Approved (07-UAT.md re-UAT 2026-05-15) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or are explicitly listed under Manual-Only Verifications (1 manual task: 07-03-04)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (max 1 consecutive — only task 07-03-04 is manual; surrounded by automated)
- [x] Wave 0 covers all MISSING references — every test file/function referenced by Wave 1+2 verifies is created in Plan 07-01 (Tasks 1-4)
- [x] No watch-mode flags — grep across all 5 plan files returns no matches (verified at revision time)
- [x] Feedback latency target documented: 20s for quick smoke, ≤120s for full suite — both well under any TDD inner-loop threshold
- [x] Every Phase 7 success criterion (SC-1..SC-4) maps to at least one automated test row in the per-task map above
- [x] `nyquist_compliant: true` set in frontmatter — all 38 tests collected and passing on Streamlit-enabled venv (`/tmp/gost-test-venv`)
- [x] `wave_0_complete: true` set in frontmatter — Plans 07-01..07-05 all executed; all files exist; all tests green

---

## Validation Audit 2026-05-15

Post-execution audit run by gsd-nyquist-auditor. Venv: `/tmp/gost-test-venv/bin/python` (Python 3.12).

### Test Surface Metrics

| Metric | Value |
|--------|-------|
| Total tests collected (Phase 7 surface) | 38 |
| Tests passed | 38 |
| Tests failed | 0 |
| Tests skipped | 0 |
| Runtime | 17.17s |
| Command | `/tmp/gost-test-venv/bin/python -m pytest tests/inference/ tests/test_preflight.py tests/test_app_upload_contract.py tests/test_render_block_section.py tests/test_render_report_pdf.py tests/test_run_processing_pdf_bypass.py tests/test_app_ui.py -x -q` |

### Per-Task Verification Results

| Task ID | Command Result | Tests | Status |
|---------|---------------|-------|--------|
| 07-01-01 | `--collect-only` → 14 collected | tests/inference/ | ✅ green |
| 07-01-02 | `--collect-only` → 14 collected | tests/inference/test_pdf_loader.py | ✅ green |
| 07-01-03 | `--collect-only` → 16 collected | test_preflight + test_app_upload_contract + test_render_block_section | ✅ green |
| 07-01-04 | `--collect-only` → 2 collected | tests/test_render_report_pdf.py | ✅ green |
| 07-02-01 | 7 passed | 7 check_text_layer + extract_pdf_blocks tests | ✅ green |
| 07-02-02 | 14 passed | tests/inference/test_pdf_loader.py full suite | ✅ green |
| 07-03-01 | 16 passed | test_preflight + upload_contract + render_block | ✅ green |
| 07-03-02 | 16 passed | test_pdf_loader + test_render_report_pdf | ✅ green |
| 07-03-03 | 1 passed | test_readme_limits_keywords | ✅ green |
| 07-03-04 | MANUAL | re-UAT approved all 3 gaps resolved | ✅ green |
| 07-04-01 | `--collect-only` → 2 collected | tests/test_run_processing_pdf_bypass.py | ✅ green |
| 07-04-02 | 2 passed | test_run_processing_pdf_bypass.py both tests | ✅ green |
| 07-04-03 | `grep -c` → 1 | CLAUDE.md rule present once | ✅ green |
| 07-05-01 | `--collect-only` → 2 collected | empty-state + reviewer-wording tests | ✅ green |
| 07-05-02 | 2 passed (+ 2 invariant tests) | empty-state + reviewer-wording + schema + sentinel | ✅ green |

### File Exists Audit

| File | Exists |
|------|--------|
| `tests/inference/__init__.py` | ✅ |
| `tests/inference/conftest.py` | ✅ |
| `tests/inference/test_pdf_loader.py` | ✅ |
| `tests/test_render_report_pdf.py` | ✅ |
| `tests/test_preflight.py` | ✅ |
| `tests/test_app_upload_contract.py` | ✅ |
| `tests/test_render_block_section.py` | ✅ |
| `tests/test_run_processing_pdf_bypass.py` | ✅ |
| `tests/test_app_ui.py` | ✅ |

### Gap Closure Verification

| Gap ID | Status | Evidence |
|--------|--------|----------|
| G-07-01 | resolved | `test_run_processing_pdf_bypass.py` 2/2 pass; `app.py` guard widened with `.suffix.lower() != ".pdf"` |
| G-07-02 | resolved | `test_app_empty_state_visible_without_docx` 2-assertion form passes; `app.py` reads «Загрузите документ (DOCX или PDF)» |
| G-07-03 | resolved | `test_extract_pdf_blocks_text_block_reviewer_wording` passes; `pdf_loader.py` reads «PDF блок — текстовый слой, требует ручной проверки» |

### Open Items

None. All 15 tasks green. All 3 gaps resolved.
