from __future__ import annotations

import app


def test_streamlit_upload_contract_is_docx_only() -> None:
    assert app.SUPPORTED_UPLOAD_TYPES == ["docx"]


def test_streamlit_methodical_upload_contract_is_expanded() -> None:
    assert app.SUPPORTED_METHODICAL_UPLOAD_TYPES == ["pdf", "docx", "txt", "md"]
