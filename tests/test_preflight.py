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


def test_preflight_translate_not_implemented_pdf() -> None:
    from app import preflight_translate_error

    result = preflight_translate_error(
        NotImplementedError("PDF input is not supported in the current pipeline.")
    )
    # Russian message must mention PDF and must NOT include the raw exception
    # text (which is English and would leak through to the UI).
    assert "PDF" in result
    assert "Traceback" not in result
    assert "not supported in the current pipeline" not in result


def test_preflight_translate_unknown_error_does_not_leak_message() -> None:
    from app import preflight_translate_error

    result = preflight_translate_error(KeyError("paragraph 5: secret PII content"))
    # Generic Russian fallback for unrecognized exceptions — must NOT pass the
    # offending exception text through to the UI surface (PII boundary).
    assert "secret PII" not in result
    assert "paragraph 5" not in result
