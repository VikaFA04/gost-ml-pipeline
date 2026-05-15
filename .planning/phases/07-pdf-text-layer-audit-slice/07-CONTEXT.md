# Phase 7: PDF text-layer audit slice — Context

**Gathered:** 2026-05-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend the existing audit pipeline (block extraction → classification → rule
engine → audit CSV) to accept PDF documents that contain an extractable text
layer. Read-only mode: no PDF writing, no autofix, `applied_fixes` always empty.
Same audit CSV schema as DOCX. Scanned/page-image PDFs are rejected at preflight
with a Russian user-facing message.

Out of scope (locked in other phases / explicitly excluded by REQ-pdf-text-only
+ D-PDF-SCOPE):
- OCR (pytesseract / cloud OCR / any image-to-text fallback)
- PDF writing (no annotated PDF, no embedded fix marks)
- PDF autofix code path (autofix branch never runs for PDF input)
- Mixed-modal output (no DOCX-from-PDF conversion)

</domain>

<decisions>
## Implementation Decisions

### Block extraction strategy
- **D-01:** Per-text-block via PyMuPDF `page.get_text("blocks")` — bbox-grouped
  text blocks become rows in the audit CSV. `block_id` derives from
  `(page_no, block_index_on_page)`. Reuses the existing `fitz` dependency
  already wired in `src/rules/methodical_extractor.iterate_text_chunks`.
  Acknowledged risk: SVM was DOCX-paragraph-trained → distribution shift.
  Mitigated by D-02.

### Classification strategy
- **D-02:** Skip the SVM entirely for PDF input. Every PDF block routes to
  `status="review"` with the original block text inspectable in the per-block
  expander. Rationale: SVM format-features (`numPr`, paragraph styles, indent)
  do not exist in PDF; faking them would produce silent low-confidence
  predictions that misrepresent the audit. «Honest» path per CLAUDE.md
  «explainable status» principle. Lightest code path; no PDF-specific
  classifier to maintain.

### Text-layer detection threshold
- **D-03:** Accept the PDF when ≥ 50% of pages return non-empty text from
  `fitz.Page.get_text()`. Otherwise reject at preflight with the Russian
  message «PDF без извлекаемого текстового слоя — OCR не поддерживается»
  (registered in `preflight_translate_error`).
  Image-only pages within an accepted PDF surface as audit rows with
  `status="review"` and reason «PDF page — без извлекаемого текста».

### UI signaling that PDF is audit-only
- **D-04:** Three-pronged signal:
  1. **Hide corrected-DOCX download** — when the input is a PDF, suppress
     the `output_docx` download button on the report page.
  2. **Prepend audit-only badge in report header** — `render_report` shows
     «PDF — режим аудита, без исправлений» next to the filename in the
     header line.
  3. **Sidebar note + README update** — short Russian sidebar note
     («PDF: только аудит, без OCR») under the uploader; README §"Limits"
     updated with the text-layer + read-only + no-OCR boundaries per
     ROADMAP SC-4.

### Claude's Discretion
- PDF fixture corpus naming + storage layout (project follows existing
  `tests/fixtures/` precedent — Claude picks).
- Preflight Russian copy phrasing details (must include «PDF без извлекаемого
  текстового слоя» and «OCR не поддерживается» substrings; rest is Claude's
  choice within the existing `preflight_translate_error` style).
- RunLog stage label for the PDF path (likely `"document-read"` for the
  text-layer detection step + `"classification"` for the no-op classifier
  call to preserve the 4-stage shape; Claude picks final mapping).
- README §Limits exact wording (must state text-layer + read-only + no-OCR
  per SC-4; English vs Russian or both — Claude picks).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 7 scope locks
- `.planning/REQUIREMENTS.md` §"PDF audit slice (D-PDF-SCOPE locked)" lines
  125-130 — REQ-pdf-text-only definition; OCR/scanned/page-images explicitly
  out of scope; PDF never edited.
- `.planning/ROADMAP.md` §"Phase 7: PDF text-layer audit slice" lines 27 +
  detail block — goal, 4 success criteria, depends-on Phase 6.

### Existing PDF infrastructure to reuse
- `src/rules/methodical_extractor.py` lines 58-82 — `iterate_text_chunks`
  PDF branch using `fitz.open(...).get_text("text")` per page; Pitfall 2
  Arabic-block noise strip; per-page text yield contract. **Reusable
  primitive — do not reinvent text-layer extraction.**
- `src/inference/document_loader.py` lines 9-37 — `SUPPORTED_EXTENSIONS`
  already includes `.pdf`; current `validate_document_input` raises
  `NotImplementedError` for PDF (the planned hook to extend).
- `tests/fixtures/methodical/normocontrol_berger.pdf` — 1.4MB existing
  fixture (Phase 5 corpus). **First PDF text-layer regression candidate.**

### Phase 6 surface to extend (do not replace)
- `app.py:24` `SUPPORTED_UPLOAD_TYPES = ["docx"]` — extend to
  `["docx", "pdf"]`.
- `app.py` — `run_processing` (calls `process_document` → `validate_document_input`),
  `preflight_translate_error` (add PDF rejection branch),
  `render_report` (gate `output_docx` download on `result.input_extension`,
  prepend audit-only badge for PDF), sidebar (add PDF note under uploader).
- `src/inference/run_log.py` — RunLog stage logging unchanged; PDF path
  uses the same 4-stage contract (see Claude's Discretion).

### Phase 5 / Phase 6 lessons that apply
- `.planning/phases/05-rule-profiles-methodical-profile-ingestion/05-CONTEXT.md`
  — D-04 PII boundary holds for PDF too (no `str(exc)` from `fitz`; basename-only
  filename in RunLog).
- `.planning/phases/06-streamlit-ui-redesign/06-CONTEXT.md` D-04 — Russian
  preflight strings are a fixed enum; new PDF branch joins the existing 5.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`src/rules/methodical_extractor.iterate_text_chunks` (PDF branch)** —
  exact text-layer extraction primitive. Wraps `fitz.open` + `page.get_text("text")`
  per page with Pitfall 2 noise stripping. Can be lifted into a shared
  `src/inference/pdf_loader.py` or called directly.
- **`src/inference/document_loader.SUPPORTED_EXTENSIONS`** — already
  includes `.pdf`; only the `NotImplementedError` raise needs replacement.
- **`app.py:preflight_translate_error`** — existing 5-string Russian
  enum extends naturally with a 6th branch for the PDF rejection path.
- **`app.py:render_report`** — already filename-aware (uses `result.filename`
  in the header); add an extension-aware badge prepend.
- **STATUS_CHIP** — all 5 statuses already cover the PDF case; no palette
  extension needed (every PDF block is `review` per D-02).

### Established Patterns
- **`fitz` (PyMuPDF) is already a project dependency** — used by
  `methodical_extractor`. No new package to add.
- **Preflight rejection routes through `preflight_translate_error`** — the
  PDF text-layer check fits this pattern exactly (raises a typed exception
  the translator maps to a fixed Russian string).
- **No format features for non-DOCX inputs** — the existing baseline
  inferencer schema can accept PDF blocks with all format features `None`,
  but D-02 routes around the SVM entirely so the schema is bypassed.

### Integration Points
- `src/inference/document_loader.validate_document_input` (PDF branch:
  text-layer detection + threshold check; raises typed exception on reject).
- New `src/inference/pdf_loader.py` (or extension of document_loader) with
  PyMuPDF block extraction returning the same `BlockRecord`-shaped data
  that the rule engine expects.
- `src/inference/application_service.process_document` — branch on
  `extension`; PDF path skips classifier entirely, maps each block to
  `status="review"` with original text + page/block-index metadata.
- `app.py:run_processing` — RunLog wiring unchanged; new preflight path
  records `stage="document-read", status="error"` with
  `error_class="PdfNoTextLayer"` (or similar) on rejection.

</code_context>

<specifics>
## Specific Ideas

- The Berger PDF (`tests/fixtures/methodical/normocontrol_berger.pdf`) is
  the natural first text-layer regression fixture — Phase 5 already proved
  it has an extractable text layer.
- A scanned-PDF fixture is needed for the rejection-path regression test.
  Can be synthesised by rasterising any text PDF + re-saving (no OCR layer);
  must NOT be committed as a large file — keep ≤ 200KB or generate at
  test setup time.

</specifics>

<deferred>
## Deferred Ideas

- OCR / scanned-PDF support — explicitly out of scope per REQ-pdf-text-only;
  belongs in a future milestone, not this phase.
- PDF writing / annotated-PDF output — explicitly out of scope per
  D-PDF-SCOPE; belongs in a future milestone.
- PDF-specific classifier (text-only SVM trained on PDF corpus) — D-02
  routes around the SVM entirely; if PDF audit needs become more granular
  later, this is its own phase.
- Per-page screenshot rendering in the UI for context — out of scope; the
  per-block `st.code` view of original text is sufficient per Phase 6 D-02.
- Mixed-input batch audit (DOCX + PDF in one run) — out of scope; current
  pipeline is single-document. Future phase.

</deferred>

---

*Phase: 07-pdf-text-layer-audit-slice*
*Context gathered: 2026-05-15*
