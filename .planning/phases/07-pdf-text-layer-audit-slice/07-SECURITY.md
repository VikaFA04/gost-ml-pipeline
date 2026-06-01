---
phase: 07
slug: pdf-text-layer-audit-slice
status: verified
threats_open: 0
asvs_level: 2
created: 2026-05-15
---

# Phase 07 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail for the PDF text-layer audit slice.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Test fixture → fitz | tmp_path-only; scanned_pdf + text_pdf synthesised at test setup via fitz, never committed as binaries | Synthetic PDF bytes, no user data |
| User upload (untrusted bytes) → fitz.open() | Untrusted PDF parsed via PyMuPDF — fitz is the trust boundary | PDF bytes, filename.suffix |
| pdf_loader exception text → RunLog | PdfNoTextLayer + fitz parse errors must never reach RunLog.error_message verbatim; only type(exc).__name__ is recorded | Exception class name only |
| pdf_loader return value → report_df → audit CSV | fitz block text capped at 500 chars, Arabic noise stripped; written to local disk only | Block text (≤500 chars), no PII above D-04 boundary |
| preflight_translate_error(exc) → st.error | Exception object enters translator; only fixed Russian string exits | Fixed string, no exc internals |
| render_report(result) → DOM | Audit-only badge uses unsafe_allow_html=True with a hardcoded span; no user-input interpolation | Hardcoded HTML constant |
| Streamlit upload widget → save_uploaded_bytes | Untrusted bytes from browser; suffix taken from uploaded_file.name via Path.suffix.lower() | Extension string (.pdf / .docx) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-07-W0-01 | Information Disclosure | tests/test_preflight.py assertion strings | mitigate | test_preflight_translate_pdf_no_text_layer asserts `"Traceback" not in result` AND `"ratio=0.0" not in result` — PII boundary encoded at the test layer; tests/test_preflight.py:72-73 | closed |
| T-07-W0-02 | Denial of Service | scanned_pdf fitz fixture | accept | Synthesised on tmp_path at 24.5 KB; bounded by fitz.new_page(width=595, height=842) A4 default and fitz.Matrix(1.0, 1.0) no-upscaling; no committed binary | closed |
| T-07-W0-03 | Tampering | Locked Russian substring drift | mitigate | Verbatim substring assertions for «PDF без извлекаемого текстового слоя», «OCR не поддерживается» in tests/test_preflight.py:69-70 and «PDF page — без извлекаемого текста» in tests/inference/test_pdf_loader.py:83; CI fails on any character change | closed |
| T-07-W1-01 | Denial of Service | fitz.open on malformed PDF | mitigate | fitz raises a typed exception; check_text_layer + extract_pdf_blocks use try/finally for doc.close() only — no bare except, no infinite loop; exception propagates to app.run_processing generic except branch; src/inference/pdf_loader.py:43-49, 67-94 | closed |
| T-07-W1-02 | Denial of Service | Oversized PDF | accept | Streamlit 200 MB upload cap; _TEXT_CAP=500 caps per-block bytes; same risk profile as existing DOCX path | closed |
| T-07-W1-03 | Denial of Service | Encrypted/password-protected PDF | mitigate | fitz raises on page.get_text() for encrypted docs; exception propagates per T-07-W1-01 path to app.run_processing generic except branch surfacing «Не удалось обработать документ.» | closed |
| T-07-W1-04 | Information Disclosure | str(exc) from fitz leaks path or internal byte offsets | mitigate | pdf_loader never catches fitz exceptions to re-wrap with str(exc); orchestrator records only type(exc).__name__ and a fixed message; RunLog._FORBIDDEN_EXTRA_KEYS enforces no raw text/traceback keys; src/inference/run_log.py:18, app.py:52-74 | closed |
| T-07-W1-05 | Information Disclosure | PDF block text in report CSV | mitigate | Text capped at 500 chars (_TEXT_CAP), Arabic noise stripped (_ARABIC_RE); report CSV is local-only output per C-NFR-PRIVACY (REQUIREMENTS.md §Out of Scope); no upload, no telemetry; src/inference/pdf_loader.py:27, 87 | closed |
| T-07-W1-06 | Tampering | PDF block_id collision | accept | block_id is f"p{page_no}b{block_no}" from fitz native indices; fitz guarantees per-page block_no uniqueness; cross-page collision impossible because page_no is the prefix | closed |
| T-07-W1-07 | Tampering | Russian sentinel string drift «PDF page — без извлекаемого текста» | mitigate | String asserted verbatim by test_extract_pdf_blocks_image_only_page_sentinel; CI fails on any character change; tests/inference/test_pdf_loader.py:83, src/inference/pdf_loader.py:76 | closed |
| T-07-W2-01 | Cross-Site Scripting | st.markdown unsafe_allow_html badge | mitigate | HTML string is a hardcoded constant with no user-input interpolation: `'<span class="badge badge-warn">PDF — режим аудита, без исправлений</span>'`; grep audit asserts exact literal; app.py:329 | closed |
| T-07-W2-02 | Information Disclosure | preflight_translate_error returns user-facing string | mitigate | PdfNoTextLayer branch at app.py:63-66 returns a literal Russian constant; no str(exc) interpolation; test_preflight_translate_pdf_no_text_layer asserts no «Traceback» and no «ratio=0.0» | closed |
| T-07-W2-03 | Spoofing | Uploader accepting .pdf extension | accept | Streamlit type=["docx","pdf"] client-side; server-side validate_document_input re-checks via SUPPORTED_EXTENSIONS; fitz.open validates PDF magic bytes; non-PDF with .pdf extension raises fitz parse error caught by generic except branch | closed |
| T-07-W2-04 | Tampering | Locked Russian strings drift across deploys | mitigate | Four locked substrings asserted by tests landed in Plan 07-01: tests/test_preflight.py, tests/inference/test_pdf_loader.py, tests/test_app_upload_contract.py, README substrings by test_readme_limits_keywords; CI fails on any drift | closed |
| T-07-W2-05 | Information Disclosure | README §Limits leaks implementation details | accept | English paragraph contains only product-level limits (text-layer requirement, OCR scope, audit-only output); no file paths, no exception names, no internal API references | closed |
| T-07-04-01 | Spoofing | .pdf-named non-PDF file bypasses baseline guard | accept | Bypass only skips the baseline_unavailable short-circuit; file still flows into process_document → validate_document_input → fitz.open magic-bytes validation; non-PDF raises fitz parse error caught by generic except branch | closed |
| T-07-04-02 | Tampering | Test monkeypatch leaks into other tests | mitigate | pytest monkeypatch fixture is function-scoped — all setattr calls auto-reverted after each test; recorder list is local to each test invocation; tests/test_run_processing_pdf_bypass.py:30-70 | closed |
| T-07-04-03 | Information Disclosure | .suffix.lower() call leaks filename casing | accept | Path(uploaded_file.name).suffix.lower() returns only the lowercased extension (.pdf or .docx); no full filename, no path; RunLog already records full filename per Phase 6 contract; this gap fix does not widen that surface | closed |
| T-07-04-04 | Denial of Service | Repeated .pdf uploads through bypass code path | accept | Same DoS profile as existing PDF path (T-07-W1-02); bounded by Streamlit 200 MB cap; baseline-bypass adds no new processing step, only removes an early return | closed |
| T-07-04-05 | Elevation of Privilege | Bypass of baseline_unavailable could invoke elevated PDF path | accept | _process_pdf runs in the same process / same user context as the existing DOCX path; no privilege boundary crossed; function is local-only per REQ-pdf-text-only + C-NFR-PRIVACY | closed |
| T-07-05-01 | Tampering | Locked-substring duality drift (PDF блок + требует ручной проверки) | mitigate | test_extract_pdf_blocks_text_block_reviewer_wording asserts both «PDF блок» (Plan 07-01 invariant) AND «требует ручной проверки» (new reviewer-facing substring); image-only-page sentinel test continues to assert «PDF page — без извлекаемого текста» verbatim; tests/inference/test_pdf_loader.py:99-103 | closed |
| T-07-05-02 | Tampering | Empty-state copy drift between sidebar uploader and main pane | mitigate | test_app_empty_state_visible_without_docx asserts compound: «Загрузите документ» AND «(DOCX или PDF)» — any future revert to «Загрузите DOCX-документ» fails CI; tests/test_app_ui.py:50-54 | closed |
| T-07-05-03 | Information Disclosure | New text-block explanation surfaces in audit CSV | accept | «PDF блок — текстовый слой, требует ручной проверки» contains no path, no exception name, no document text; same PII profile as old wording; D-04 boundary unchanged | closed |
| T-07-05-04 | Spoofing | Attacker hopes empty-state copy change reveals new attack surface | accept | Empty-state copy renders only when st.session_state["last_result"] is None; no user input flows through the rendering; pure presentation change; no new code path; app.py:715-717 | closed |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-07-01 | T-07-W0-02 | scanned_pdf fitz fixture is synthesised on tmp_path at 24.5 KB; bounded by A4 dimensions and 1.0x matrix; no binary committed to repo; pytest cleans tmp_path automatically | project owner (07-01-PLAN.md §STRIDE register) | 2026-05-15 |
| AR-07-02 | T-07-W1-02 | Oversized PDF DoS bounded by Streamlit 200 MB cap; same risk profile as DOCX path accepted in Phase 6; _TEXT_CAP=500 limits per-block memory footprint | project owner (07-02-PLAN.md §STRIDE register) | 2026-05-15 |
| AR-07-03 | T-07-W1-06 | block_id collision impossible by construction: fitz guarantees per-page block_no uniqueness; page_no prefix eliminates cross-page collisions | project owner (07-02-PLAN.md §STRIDE register) | 2026-05-15 |
| AR-07-04 | T-07-W2-03 | Extension-based spoofing bounded by fitz magic-bytes validation downstream; non-PDF with .pdf extension raises fitz parse error in the existing generic except branch; no new attack surface | project owner (07-03-PLAN.md §STRIDE register) | 2026-05-15 |
| AR-07-05 | T-07-W2-05 | README §Limits is product-level documentation only; no implementation details, exception names, file paths, or internal API references | project owner (07-03-PLAN.md §STRIDE register) | 2026-05-15 |
| AR-07-06 | T-07-04-01 | Bypass only skips baseline_unavailable short-circuit; fitz magic-bytes validation still runs downstream; existing generic except branch catches non-PDF spoofed files | project owner (07-04-PLAN.md §STRIDE register) | 2026-05-15 |
| AR-07-07 | T-07-04-03 | Path.suffix.lower() returns only the lowercased extension; no full path or filename exposed; RunLog full-filename recording is a pre-existing Phase 6 acceptance | project owner (07-04-PLAN.md §STRIDE register) | 2026-05-15 |
| AR-07-08 | T-07-04-04 | Repeated PDF uploads through bypass code path: same DoS ceiling as T-07-W1-02 (Streamlit 200 MB cap); baseline-bypass removes an early return but adds no new processing step | project owner (07-04-PLAN.md §STRIDE register) | 2026-05-15 |
| AR-07-09 | T-07-04-05 | _process_pdf runs in same process/user context as DOCX path; local-only per C-NFR-PRIVACY; no privilege boundary | project owner (07-04-PLAN.md §STRIDE register) | 2026-05-15 |
| AR-07-10 | T-07-05-03 | Reviewer-facing explanation text contains no PII (no path, no exception name, no document content); D-04 boundary unchanged | project owner (07-05-PLAN.md §STRIDE register) | 2026-05-15 |
| AR-07-11 | T-07-05-04 | Empty-state copy is pure presentation; renders only when last_result is None; no user input flows through the rendering path | project owner (07-05-PLAN.md §STRIDE register) | 2026-05-15 |

---

## Unregistered Threat Flags

No unregistered threat flags. All five SUMMARY files for Phase 07 report no new threat surface beyond the STRIDE register. The 07-02-SUMMARY.md §Threat Surface Scan explicitly states: "No new network endpoints, auth paths, or schema changes at trust boundaries introduced. All fitz calls match the threat register (T-07-W1-01 through T-07-W1-07) already documented in 07-02-PLAN.md. No additional threat flags."

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-05-15 | 24 | 24 | 0 | gsd-security-auditor (claude-sonnet-4-6) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-05-15
