from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import fitz
import pytest

# Fixtures (text_pdf, scanned_pdf) and BERGER_PDF come from tests/inference/conftest.py


def test_check_text_layer_berger_accepted() -> None:
    from src.inference.pdf_loader import check_text_layer
    from tests.inference.conftest import BERGER_PDF
    assert check_text_layer(BERGER_PDF) >= 0.50


def test_check_text_layer_scanned_rejected(scanned_pdf: Path) -> None:
    from src.inference.pdf_loader import check_text_layer
    assert check_text_layer(scanned_pdf) < 0.50


def test_check_text_layer_zero_page_returns_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # fitz refuses to save a 0-page PDF ("cannot save with zero pages"), so the
    # defensive `if total == 0: return 0.0` branch in check_text_layer cannot
    # be reached via a real file. Patch fitz.open at the pdf_loader module
    # boundary to return a stub doc with len == 0.
    from src.inference import pdf_loader

    class _ZeroPageStub:
        def __len__(self) -> int:
            return 0
        def __iter__(self):
            return iter(())
        def close(self) -> None:
            return None

    monkeypatch.setattr(pdf_loader, "fitz", type("F", (), {"open": staticmethod(lambda _p: _ZeroPageStub())}))
    assert pdf_loader.check_text_layer(tmp_path / "empty.pdf") == 0.0


def test_check_text_layer_50pct_threshold_inclusive(tmp_path: Path) -> None:
    from src.inference.pdf_loader import check_text_layer
    doc = fitz.open()
    text_page = doc.new_page()
    text_page.insert_text((72, 72), "Текст")
    image_page = doc.new_page()
    # leave second page blank/image-only
    out = tmp_path / "half.pdf"
    doc.save(str(out))
    doc.close()
    assert check_text_layer(out) == 0.5


def test_extract_pdf_blocks_schema(text_pdf: Path) -> None:
    from src.inference.pdf_loader import extract_pdf_blocks
    rows = extract_pdf_blocks(text_pdf)
    assert len(rows) > 0
    row = rows[0]
    for key in ("block_id", "kind", "text", "status", "applied_fixes", "explanation"):
        assert key in row, f"missing key {key!r}"
    assert row["status"] == "review"
    assert row["applied_fixes"] == ""
    assert row["kind"] == "paragraph"


def test_extract_pdf_blocks_block_id_format(text_pdf: Path) -> None:
    from src.inference.pdf_loader import extract_pdf_blocks
    rows = extract_pdf_blocks(text_pdf)
    pattern = re.compile(r"^p\d+b\d+$")
    for row in rows:
        assert pattern.match(row["block_id"]), f"block_id {row['block_id']!r} does not match p{{N}}b{{M}}"


def test_extract_pdf_blocks_image_only_page_sentinel(scanned_pdf: Path) -> None:
    from src.inference.pdf_loader import extract_pdf_blocks
    rows = extract_pdf_blocks(scanned_pdf)
    assert len(rows) == 1
    row = rows[0]
    assert row["status"] == "review"
    assert row["text"] == ""
    assert "PDF page — без извлекаемого текста" in row["explanation"]


def test_extract_pdf_blocks_text_block_reviewer_wording(text_pdf: Path) -> None:
    """G-07-03: text-block explanation must be framed for the human reviewer.

    Locked substring «PDF блок» (Plan 07-01 §truth) is preserved. The full
    wording shifts from model-POV «классификация недоступна (SVM требует
    DOCX-формата)» to reviewer-action «требует ручной проверки» per
    07-UAT.md G-07-03.
    """
    from src.inference.pdf_loader import extract_pdf_blocks

    rows = extract_pdf_blocks(text_pdf)
    assert len(rows) >= 1
    first = rows[0]
    assert first["status"] == "review"
    # Locked substring — preserves Plan 07-01 §truth / UAT Test 4 invariant.
    assert "PDF блок" in first["explanation"]
    # New reviewer-facing substring — the G-07-03 fix.
    assert "требует ручной проверки" in first["explanation"]


def test_processing_artifacts_has_input_extension_field() -> None:
    from src.inference.application_service import ProcessingArtifacts
    field_names = {f.name for f in dataclasses.fields(ProcessingArtifacts)}
    assert "input_extension" in field_names
    ext_field = next(f for f in dataclasses.fields(ProcessingArtifacts) if f.name == "input_extension")
    assert ext_field.type in ("str", str)


def test_readme_limits_keywords() -> None:
    readme = Path(__file__).resolve().parents[2] / "README.md"
    text = readme.read_text(encoding="utf-8")
    assert "audit-only" in text
    assert "text layer" in text
    assert ("no OCR" in text) or ("OCR is not supported" in text)
    assert ("no corrected PDF" in text) or ("no corrected" in text and "PDF" in text)


def test_pdf_output_docx_none(text_pdf: Path) -> None:
    # RESEARCH.md Phase Requirements → Test Map row "SC-2 / output_docx is None".
    from src.inference.application_service import process_document
    profile = Path(__file__).resolve().parents[2] / "src" / "rules" / "profiles" / "gost_7_32_2017.json"
    result = process_document(text_pdf, model_choice="baseline", mode="audit", profile_path=profile)
    assert result.output_docx is None


def test_berger_end_to_end() -> None:
    # RESEARCH.md Phase Requirements → Test Map row "SC-1+SC-2 / Berger end-to-end".
    from src.inference.application_service import process_document
    from tests.inference.conftest import BERGER_PDF
    profile = Path(__file__).resolve().parents[2] / "src" / "rules" / "profiles" / "gost_7_32_2017.json"
    result = process_document(BERGER_PDF, model_choice="baseline", mode="audit", profile_path=profile)
    assert result.input_extension == ".pdf"
    assert len(result.report_df) > 0
    assert (result.report_df["status"] == "review").all()


def test_pdf_artifacts_predictions_csv_sentinel(text_pdf: Path) -> None:
    # B3 resolution (OQ-1): PDF path emits no separate predictions CSV — sentinel aliasing to report_csv.
    from src.inference.application_service import process_document
    profile = Path(__file__).resolve().parents[2] / "src" / "rules" / "profiles" / "gost_7_32_2017.json"
    result = process_document(text_pdf, model_choice="baseline", mode="audit", profile_path=profile)
    assert result.predictions_csv == result.report_csv


def test_pdf_artifacts_extracted_csv_sentinel(text_pdf: Path) -> None:
    # B3 resolution (OQ-1): PDF path emits no separate extracted CSV — sentinel aliasing to report_csv.
    from src.inference.application_service import process_document
    profile = Path(__file__).resolve().parents[2] / "src" / "rules" / "profiles" / "gost_7_32_2017.json"
    result = process_document(text_pdf, model_choice="baseline", mode="audit", profile_path=profile)
    assert result.extracted_csv == result.report_csv
