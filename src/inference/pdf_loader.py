"""PDF text-layer detection + block extraction for the audit-only PDF slice.

Phase 7 (REQ-pdf-text-only). Read-only: never writes a PDF, never invokes
the SVM (D-02), never invokes the rule engine. Every emitted row carries
status="review" so render_report routes the document to the «Требуют
внимания» section.

Pitfall 2 (07-RESEARCH.md): strip Arabic-block noise from fitz text via
the same regex used in src/rules/methodical_extractor.iterate_text_chunks.

PII boundary (D-04 from 06-UI-SPEC.md): callers must NEVER pass str(exc)
from this module to RunLog.record(error_message=...) — the messages here
may include path components. The Russian user-facing string is mapped in
app.preflight_translate_error; this module's exception text is for
technical logs only and is NOT user-facing.
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz


_ARABIC_RE = re.compile(r"[؀-ۿ]")  # Pitfall 2: methodical_extractor.py:67
_TEXT_CAP = 500  # Matches inplace_formatter.py:527 text[:500] cap.


class PdfNoTextLayer(Exception):
    """Raised when a PDF has fewer than 50% pages with extractable text."""


def check_text_layer(path: str | Path) -> float:
    """Return ratio of pages with non-empty text in [0.0, 1.0].

    0.0 for 0-page PDFs (no division by zero). Caller compares
    `ratio >= 0.50` for the inclusive-accept threshold (07-CONTEXT.md
    D-03).
    """
    doc = fitz.open(str(path))
    try:
        total = len(doc)
        if total == 0:
            return 0.0
        non_empty = sum(1 for page in doc if page.get_text().strip())
        return non_empty / total
    finally:
        doc.close()


def extract_pdf_blocks(path: str | Path) -> list[dict]:
    """Return audit-CSV-shaped row dicts for every text block in the PDF.

    Contract (07-PATTERNS.md):
      - One row per fitz text block (block_type == 0).
      - One sentinel row per image-only page (no text blocks present).
      - block_id format: f"p{page_no}b{block_no}", page_no 1-based,
        block_no from fitz tuple [5] (0-based).
      - Every row: kind="paragraph", status="review", applied_fixes="".
    """
    doc = fitz.open(str(path))
    rows: list[dict] = []
    try:
        for page_no, page in enumerate(doc, start=1):
            blocks = page.get_text("blocks")
            text_blocks = [b for b in blocks if b[6] == 0]
            if not text_blocks:
                rows.append(
                    {
                        "block_id": f"p{page_no}b0",
                        "kind": "paragraph",
                        "text": "",
                        "status": "review",
                        "applied_fixes": "",
                        "explanation": "PDF page — без извлекаемого текста",
                    }
                )
                continue
            for b in text_blocks:
                _x0, _y0, _x1, _y1, raw_text, block_no, _btype = b
                text = _ARABIC_RE.sub("", raw_text).strip()
                rows.append(
                    {
                        "block_id": f"p{page_no}b{block_no}",
                        "kind": "paragraph",
                        "text": text[:_TEXT_CAP],
                        "status": "review",
                        "applied_fixes": "",
                        "explanation": "PDF блок — классификация недоступна (SVM требует DOCX-формата)",
                    }
                )
    finally:
        doc.close()
    return rows
