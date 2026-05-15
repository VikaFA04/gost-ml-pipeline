# Phase 6 Wave 0 RED stubs for the Streamlit UI top-level surface.
#
# These tests constrain Waves 2/3 implementation:
#   * test_app_imports_without_exception   — currently GREEN (smoke baseline).
#   * test_app_test_renders_without_exception — currently GREEN (smoke baseline).
#   * test_app_empty_state_visible_without_docx — RED today; expects the Phase 6
#     empty-state heading "Загрузите DOCX-документ" (UI-SPEC §Empty state copy).
#   * test_app_no_traceback_in_rendered_output — RED protection against the
#     `st.exception(exc)` regression at app.py:773 (UI-SPEC §Error state copy).

from __future__ import annotations

import pytest


def test_app_imports_without_exception() -> None:
    """Smoke baseline — `import app` must succeed.

    Skips on interpreters without Streamlit installed (system Python).
    """
    pytest.importorskip("streamlit")
    import app  # noqa: F401  (import-only smoke check)


def test_app_test_renders_without_exception(app_test) -> None:
    """AppTest can run app.py end-to-end without raising."""
    at = app_test.run(timeout=30)
    # AppTest stores uncaught exceptions in `at.exception`; an empty tuple/list is success.
    assert not at.exception, f"app.py raised during AppTest run: {list(at.exception)}"


def test_app_empty_state_visible_without_docx(app_test) -> None:
    """Phase 7 D-04 §3 / G-07-02 empty-state copy must mention DOCX + PDF.

    Original Phase 6 copy was «Загрузите DOCX-документ»; Phase 7 expanded
    SUPPORTED_UPLOAD_TYPES to ['docx', 'pdf'] and Plan 07-03 updated the
    sidebar uploader label to «Загрузите документ (DOCX или PDF)». G-07-02
    closes the drift between sidebar uploader copy and main-pane empty
    state — the empty-state alert now mirrors the uploader: «Загрузите
    документ (DOCX или PDF), чтобы начать аудит».
    """
    at = app_test.run(timeout=30)
    rendered = []
    for collection in (at.markdown, at.title, at.header, at.subheader, at.warning, at.info):
        for element in collection:
            value = getattr(element, "value", None)
            if value is not None:
                rendered.append(str(value))
    haystack = "\n".join(rendered)
    assert "Загрузите документ" in haystack, (
        "Phase 7 G-07-02 empty-state copy missing «Загрузите документ» substring"
    )
    assert "(DOCX или PDF)" in haystack, (
        "Phase 7 G-07-02 empty-state copy missing «(DOCX или PDF)» substring"
    )


def test_app_no_traceback_in_rendered_output(app_test) -> None:
    """No Python `Traceback` substring may appear in any rendered element.

    RED protection against the current `st.exception(exc)` call at app.py:773
    (UI-SPEC §Error state copy: tracebacks belong in the run-log JSON only,
    never in the UI surface). Drives Wave 2.
    """
    at = app_test.run(timeout=30)
    rendered = []
    for collection in (at.markdown, at.title, at.header, at.subheader, at.warning, at.info, at.error):
        for element in collection:
            value = getattr(element, "value", None)
            if value is not None:
                rendered.append(str(value))
    haystack = "\n".join(rendered)
    assert "Traceback" not in haystack, "Python Traceback leaked into UI output"
