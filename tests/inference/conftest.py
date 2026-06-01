from __future__ import annotations

from pathlib import Path

import fitz
import pytest

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
BERGER_PDF = FIXTURES_DIR / "methodical" / "normocontrol_berger.pdf"


@pytest.fixture
def text_pdf(tmp_path: Path) -> Path:
    """Single-page PDF with extractable text layer (Wave 0 baseline)."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Тестовый текст параграфа")
    out = tmp_path / "text.pdf"
    doc.save(str(out))
    doc.close()
    return out


@pytest.fixture
def scanned_pdf(tmp_path: Path) -> Path:
    """Single-page image-only PDF — no text layer; size ≤ 200 KB (verified 24.5 KB)."""
    src = fitz.open()
    page = src.new_page(width=595, height=842)  # A4 at 72 DPI
    text_doc = fitz.open()
    text_page = text_doc.new_page()
    text_page.insert_text((50, 100), "placeholder")
    mat = fitz.Matrix(1.0, 1.0)
    pix = text_doc[0].get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
    page.insert_image(page.rect, pixmap=pix)
    text_doc.close()
    out = tmp_path / "scanned.pdf"
    src.save(str(out), deflate=True)
    src.close()
    return out
