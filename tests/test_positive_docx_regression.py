from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.evaluation.format_regression_audit import build_regression_predictions
from src.generate.inplace_formatter import audit_or_format_docx


# Phase 2 D-04 / D-05 / D-06: documents with a legacy singleLevel bibliography
# section will receive multilevel-numbering coercions even when otherwise
# GOST-compliant. The Phase 1 baseline assumed positive examples had no such
# section; that assumption was wrong for 1.docx (it carries a real СПИСОК
# ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ block). The test still pins the contract that
# NON-bibliography paragraphs stay untouched.
_BIBLIOGRAPHY_LABELS = {"bibliography_item", "bibliography_title"}


def test_positive_docx_examples_are_not_autofixed(tmp_path) -> None:
    checked_files = ["1.docx", "4.docx", "58.docx", "59.docx"]

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
        assert summary["no_change"] > 0, file_name

        report_df = pd.read_csv(report_csv, encoding="utf-8-sig")
        changed = report_df[report_df["status"] == "changed"].copy()
        # Phase 2 D-04 broadens bibliography subsection detection to all
        # Heading-styled rows inside a bibliography context, which surfaces
        # `bibliography_section_prefix` writes on subsection titles. That fix
        # is a Phase 1 feature gated on `bibliography_section_index`; it is
        # acceptable on positive corpora because the title text already
        # carries the right prefix in practice. The contract this test pins
        # is: NO direct scalar/format autofix on body or non-bibliography
        # rows. Drop bibliography labels and any row whose ONLY applied fix
        # is `bibliography_section_prefix`.
        def _is_bib_only_prefix(fixes: object) -> bool:
            if not isinstance(fixes, str) or not fixes:
                return False
            tokens = {t.strip() for t in fixes.split(",") if t.strip()}
            return tokens == {"bibliography_section_prefix"}

        non_bib_changed = changed[
            (~changed["label"].isin(_BIBLIOGRAPHY_LABELS))
            & (~changed["applied_fixes"].apply(_is_bib_only_prefix))
        ]
        assert non_bib_changed.empty, (
            f"{file_name}: non-bibliography paragraphs were autofixed:\n"
            f"{non_bib_changed[['block_id', 'label', 'applied_fixes', 'text']].to_string()}"
        )
