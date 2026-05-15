from __future__ import annotations

import app


def test_streamlit_upload_contract_is_docx_and_pdf() -> None:
    # Phase 7 D-04 §3: uploader accepts DOCX and PDF; PDF audit-only.
    assert app.SUPPORTED_UPLOAD_TYPES == ["docx", "pdf"]


def test_streamlit_methodical_upload_contract_is_expanded() -> None:
    assert app.SUPPORTED_METHODICAL_UPLOAD_TYPES == ["pdf", "docx", "txt", "md"]
