# Phase 6 Wave 0 RED stubs for app.preflight_translate_error
# (which does not yet exist in app.py).
#
# Module-level `pytest.importorskip("streamlit")` lets collection succeed on
# system Python — every test then skips cleanly. On a Streamlit-enabled venv
# the import of `app.preflight_translate_error` raises AttributeError, which
# is the deliberate RED signal until Wave 2.
#
# Coverage matches plan §Task 2 behavior list:
#   1. FileNotFoundError -> «Файл не читается...»
#   2. ValueError("...does not contain any extractable non-empty blocks.") ->
#      «В документе нет извлекаемых непустых блоков...»
#   3. zipfile.BadZipFile -> «Файл не читается...» (same as FileNotFoundError)
#   4. NotImplementedError("PDF input is not supported...") -> Russian message
#      mentioning PDF (no traceback leak)
#   5. Unknown exception -> generic Russian message that does NOT contain
#      offending PII content from the original message (PII boundary at
#      translation layer per UI-SPEC §Error state copy)

from __future__ import annotations

import zipfile

import pytest

pytest.importorskip("streamlit")


def test_preflight_translate_file_not_found() -> None:
    from app import preflight_translate_error

    result = preflight_translate_error(FileNotFoundError("doesn't matter"))
    assert "Файл не читается" in result


def test_preflight_translate_value_error_empty_blocks() -> None:
    from app import preflight_translate_error

    result = preflight_translate_error(
        ValueError("The input DOCX does not contain any extractable non-empty blocks.")
    )
    assert "В документе нет извлекаемых непустых блоков" in result


def test_preflight_translate_bad_zip() -> None:
    from app import preflight_translate_error

    result = preflight_translate_error(zipfile.BadZipFile("not a zip"))
    # BadZipFile shares the unreadable-DOCX surface with FileNotFoundError.
    assert "Файл не читается" in result


def test_preflight_translate_unknown_error_does_not_leak_message() -> None:
    from app import preflight_translate_error

    result = preflight_translate_error(KeyError("paragraph 5: secret PII content"))
    # Generic Russian fallback for unrecognized exceptions — must NOT pass the
    # offending exception text through to the UI surface (PII boundary).
    assert "secret PII" not in result
    assert "paragraph 5" not in result


def test_preflight_translate_pdf_no_text_layer() -> None:
    from app import preflight_translate_error
    from src.inference.pdf_loader import PdfNoTextLayer

    result = preflight_translate_error(PdfNoTextLayer("ratio=0.0"))
    # Locked substrings per 07-CONTEXT.md D-03 — both MUST appear verbatim.
    assert "PDF без извлекаемого текстового слоя" in result
    assert "OCR не поддерживается" in result
    # PII boundary — no fitz internals, no Traceback, no raw ratio leakage.
    assert "Traceback" not in result
    assert "ratio=0.0" not in result
