from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("streamlit")


@contextmanager
def _capture_streamlit_calls(monkeypatch):
    """Replace every render-side primitive used by app.render_report with a
    recorder. Yields the calls list — each entry is a (name, args, kwargs) tuple."""
    import streamlit as st
    import app

    calls: list[tuple] = []

    def make_recorder(name):
        def _recorder(*args, **kwargs):
            calls.append((name, args, kwargs))
            return None
        return _recorder

    # Streamlit primitives used inside render_report
    for st_name in ("subheader", "caption", "markdown", "write", "code",
                    "metric", "divider", "success", "info", "warning",
                    "error", "container", "columns"):
        if hasattr(st, st_name):
            monkeypatch.setattr(f"streamlit.{st_name}", make_recorder(st_name),
                                raising=False)

    # expander is a context manager — record its arg and return a dummy CM
    @contextmanager
    def _expander(*args, **kwargs):
        calls.append(("expander", args, kwargs))
        yield None
    monkeypatch.setattr("streamlit.expander", _expander, raising=False)

    # app-internal renderers we do not want to descend into
    monkeypatch.setattr("app.render_summary_counters",
                        make_recorder("render_summary_counters"), raising=False)
    monkeypatch.setattr("app.render_block_section",
                        make_recorder("render_block_section"), raising=False)
    monkeypatch.setattr("app.render_artifact_download_card",
                        make_recorder("render_artifact_download_card"),
                        raising=False)

    yield calls


def _build_pdf_artifacts(tmp_path: Path):
    """Build a minimal ProcessingArtifacts with input_extension='.pdf'."""
    from src.inference.application_service import ProcessingArtifacts

    report_csv = tmp_path / "report.csv"
    report_csv.write_text("block_id,status\np1b0,review\n", encoding="utf-8")
    report_df = pd.DataFrame([{"block_id": "p1b0", "status": "review"}])
    return ProcessingArtifacts(
        model_type="pdf_audit",
        mode="audit",
        profile_path=tmp_path / "profile.json",
        input_path=tmp_path / "doc.pdf",
        input_extension=".pdf",
        extracted_csv=report_csv,
        predictions_csv=report_csv,
        report_csv=report_csv,
        report_json=report_csv,
        summary_json=report_csv,
        summary_txt=report_csv,
        output_docx=None,
        predictions_df=pd.DataFrame(),
        report_df=report_df,
        summary={"profile_name": "gost", "profile_id": "gost"},
    )


def test_render_report_pdf_badge_renders(monkeypatch, tmp_path: Path) -> None:
    # Locked badge text per 07-CONTEXT.md D-04 §2 + 07-UI-SPEC §"Copywriting Contract".
    import app

    artifacts = _build_pdf_artifacts(tmp_path)
    with _capture_streamlit_calls(monkeypatch) as calls:
        app.render_report(artifacts, filename="doc.pdf")

    markdown_calls = [c for c in calls if c[0] == "markdown"]
    badge_renders = [
        c for c in markdown_calls
        if any("PDF — режим аудита, без исправлений" in str(a) for a in c[1])
        or any("PDF — режим аудита, без исправлений" in str(v) for v in c[2].values())
    ]
    assert badge_renders, (
        "Expected st.markdown call rendering badge «PDF — режим аудита, без исправлений» "
        f"for PDF input; got markdown calls: {markdown_calls!r}"
    )


def test_render_report_pdf_hides_docx_download(monkeypatch, tmp_path: Path) -> None:
    # 07-UI-SPEC §"Download visibility" + D-04 §1: no corrected DOCX for PDF.
    import app

    artifacts = _build_pdf_artifacts(tmp_path)
    with _capture_streamlit_calls(monkeypatch) as calls:
        app.render_report(artifacts, filename="doc.pdf")

    docx_card_calls = [
        c for c in calls
        if c[0] == "render_artifact_download_card"
        and c[2].get("key") == "download_output_docx"
    ]
    assert not docx_card_calls, (
        "render_artifact_download_card(key='download_output_docx') must NOT be called "
        f"for PDF input; got: {docx_card_calls!r}"
    )
