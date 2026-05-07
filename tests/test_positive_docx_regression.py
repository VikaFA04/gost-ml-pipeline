from __future__ import annotations

from pathlib import Path

import pytest

from src.evaluation.format_regression_audit import build_regression_predictions
from src.generate.inplace_formatter import audit_or_format_docx


def test_positive_docx_examples_are_not_autofixed(tmp_path) -> None:
    checked_files = ["1.docx", "4.docx"]

    for file_name in checked_files:
        input_docx = Path("positive_examples") / file_name
        if not input_docx.exists():
            pytest.skip(f"Local positive DOCX fixture is not available: {input_docx}")

        predictions_csv = tmp_path / f"{input_docx.stem}_predictions.csv"
        report_csv = tmp_path / f"{input_docx.stem}_report.csv"
        output_docx = tmp_path / f"{input_docx.stem}_output.docx"
        build_regression_predictions(input_docx, predictions_csv)

        summary = audit_or_format_docx(
            input_docx=input_docx,
            predictions_csv=predictions_csv,
            report_csv=report_csv,
            output_docx=output_docx,
            apply_safe=True,
            profile_id="gost_7_32_2017",
        )

        assert summary["error"] == 0, file_name
        assert summary["changed"] == 0, file_name
        assert summary["no_change"] > 0, file_name
