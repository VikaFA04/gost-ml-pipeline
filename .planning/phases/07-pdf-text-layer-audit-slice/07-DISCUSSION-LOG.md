# Phase 7: PDF text-layer audit slice — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution
> agents. Decisions are captured in `07-CONTEXT.md` — this log preserves the
> alternatives considered.

**Date:** 2026-05-15
**Phase:** 07-pdf-text-layer-audit-slice
**Areas discussed:** Block extraction strategy, SVM feature adapter for PDF,
Text-layer detection threshold, UI signaling that PDF is audit-only

---

## Block extraction strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Per-page = one block | Each PDF page → one row in audit CSV. Simplest, predictable. Coarse. | |
| Per-paragraph via blank-line heuristic | Split each page on `\n\n`. Heuristic-fragile on column layouts and single-line breaks. | |
| Per-text-block via PyMuPDF block API | `page.get_text("blocks")` — bbox-grouped. Structurally accurate. SVM-distribution-shift risk. | ✓ |

**User's choice:** Per-text-block via PyMuPDF block API
**Notes:** Calibration risk acknowledged and mitigated downstream by D-02
(skip-SVM-route-to-review).

---

## SVM feature adapter for PDF

| Option | Description | Selected |
|--------|-------------|----------|
| Synthesize features from PyMuPDF metadata | bbox + font + flags → existing format-feature schema. Lower confidence than DOCX. One classifier path. | |
| Text-only classification (drop format features) | SVM with format features zeroed. Big confidence drop. Most blocks → `review`. | |
| Lock everything to `review` for PDF (no SVM) | Skip SVM entirely. Every block `review`. Honest, no false `no_change` claims. Lightest code path. | ✓ |

**User's choice:** Lock everything to `review` for PDF (no SVM)
**Notes:** Aligns with CLAUDE.md «explainable status» principle and the
read-only audit-only contract. Removes the maintenance burden of a PDF feature
adapter and the ambiguity of low-confidence DOCX-trained predictions on PDF
inputs.

---

## Text-layer detection threshold

| Option | Description | Selected |
|--------|-------------|----------|
| Strict — all pages must yield non-empty text | Any single image page kills the audit. Catches hybrid PDFs early. | |
| Threshold ≥ 50% of pages with extractable text | Allows hybrid PDFs (scanned cover + text body). Image pages surface as `review` rows in the CSV. | ✓ |
| Permissive — any page with text passes | Watermark-only PDFs would slip through. | |

**User's choice:** Threshold ≥ 50% of pages with extractable text (recommended)
**Notes:** Image-only pages within an accepted PDF still surface as audit rows
with `review` status and a clear page-level reason.

---

## UI signaling that PDF is audit-only

(multi-select question — user picked 3 of 4 options)

| Option | Description | Selected |
|--------|-------------|----------|
| Hide corrected-DOCX download for PDF input | Suppress `output_docx` button when input is PDF. Cheapest, clearest signal. | ✓ |
| Prepend audit-only badge in report header | Add «PDF — режим аудита, без исправлений» next to filename in `render_report` header. | ✓ |
| Different STATUS_CHIP palette for PDF rows | Adds a `pdf` row indicator. Risks diluting the 5-status palette. | |
| README + sidebar note | Sidebar note «PDF: только аудит, без OCR»; README §Limits update per SC-4. | ✓ |

**User's choice:** Combined — hide DOCX download + prepend report header badge
+ README + sidebar note. STATUS_CHIP palette deliberately left alone (every
PDF block is `review` per D-02 anyway).

---

## Claude's Discretion

- PDF fixture corpus naming + storage layout under `tests/fixtures/`.
- Preflight Russian copy phrasing details (must include «PDF без извлекаемого
  текстового слоя» and «OCR не поддерживается» substrings).
- RunLog stage label mapping for the PDF path (within the existing 4-stage
  contract).
- README §Limits exact wording (must state text-layer + read-only + no-OCR
  per SC-4).

## Deferred Ideas

- OCR / scanned-PDF support (out of scope per REQ-pdf-text-only).
- PDF writing / annotated-PDF output (out of scope per D-PDF-SCOPE).
- PDF-specific classifier (its own phase if needed).
- Per-page screenshot rendering in the UI.
- Mixed-input batch audit (DOCX + PDF in one run).
