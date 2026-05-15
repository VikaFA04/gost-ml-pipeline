"""Regression test for G-07-01: PDF input must not be short-circuited by the
baseline_unavailable guard in app.run_processing.

The PDF branch of process_document bypasses the SVM (Plan 07-02 §truths), so
the absence of a baseline .joblib is irrelevant for PDF input. Phase 6
introduced the guard for DOCX; Phase 7 must teach it to skip PDFs.

Test uses pytest.importorskip("streamlit") + monkeypatch on app.process_document
so no real pipeline runs — we only assert the GUARD behaviour.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("streamlit")

import app  # noqa: E402  — gated by importorskip above


def _make_uploaded(name: str) -> SimpleNamespace:
    """Build a minimal uploaded-file stub matching the duck-type that
    app.run_processing reads (Path(uploaded_file.name).suffix + .getvalue())."""
    return SimpleNamespace(name=name, getvalue=lambda: b"")


def _patch_pipeline(monkeypatch, tmp_path: Path) -> list:
    """Replace process_document + save_uploaded_bytes + RunLog with recorders
    so run_processing executes without touching disk or invoking the real
    SVM/PDF pipeline. Returns the recorder list — non-empty iff
    process_document was called."""
    process_calls: list = []

    def _record(*args, **kwargs):
        process_calls.append((args, kwargs))
        return SimpleNamespace(
            model_type="stub",
            mode="audit",
            profile_path=tmp_path / "p.json",
            input_path=tmp_path / "x",
            input_extension=".pdf",
            extracted_csv=tmp_path / "e.csv",
            predictions_csv=tmp_path / "e.csv",
            report_csv=tmp_path / "r.csv",
            report_json=tmp_path / "r.json",
            summary_json=tmp_path / "s.json",
            summary_txt=tmp_path / "s.txt",
            output_docx=None,
            predictions_df=None,
            report_df=None,
            summary={},
        )

    monkeypatch.setattr(app, "process_document", _record, raising=True)
    monkeypatch.setattr(
        app,
        "save_uploaded_bytes",
        lambda data, suffix: tmp_path / f"upload{suffix}",
        raising=True,
    )

    class _StubRunLog:
        def __init__(self, *args, **kwargs) -> None: ...
        def record(self, *args, **kwargs) -> None: ...
        def dump_json(self, *args, **kwargs) -> None: ...

    monkeypatch.setattr(app, "RunLog", _StubRunLog, raising=True)
    return process_calls


def test_run_processing_pdf_input_bypasses_baseline_unavailable_guard(
    monkeypatch, tmp_path: Path
) -> None:
    """G-07-01: PDF inputs must reach process_document even when
    selected_model_key == 'baseline_unavailable' (PDF path bypasses SVM)."""
    process_calls = _patch_pipeline(monkeypatch, tmp_path)

    app.run_processing(
        uploaded_file=_make_uploaded("sample.pdf"),
        selected_model_key="baseline_unavailable",
        selected_mode="audit",
        selected_profile_path=str(tmp_path / "p.json"),
    )

    assert len(process_calls) == 1, (
        "PDF input must NOT be short-circuited by the baseline_unavailable "
        "guard; expected process_document to be called once, got "
        f"{len(process_calls)} call(s)."
    )


def test_run_processing_docx_input_still_short_circuits_on_baseline_unavailable(
    monkeypatch, tmp_path: Path
) -> None:
    """DOCX regression guard: the fix must NOT widen the bypass to DOCX.
    Phase 6 contract — DOCX without a baseline produces st.error and returns."""
    process_calls = _patch_pipeline(monkeypatch, tmp_path)

    app.run_processing(
        uploaded_file=_make_uploaded("sample.docx"),
        selected_model_key="baseline_unavailable",
        selected_mode="audit",
        selected_profile_path=str(tmp_path / "p.json"),
    )

    assert process_calls == [], (
        "DOCX input MUST still short-circuit on baseline_unavailable; "
        f"got {len(process_calls)} unexpected call(s) to process_document."
    )
