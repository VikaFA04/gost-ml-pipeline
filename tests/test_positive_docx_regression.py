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
    # Phase 3 D-08 (2026-05-13): 58.docx and 59.docx are practice reports
    # (отчёт по практике), not GOST coursework — applying the GOST profile to
    # them produces spurious edits because the profile doesn't cover that
    # doc type. Dropped from the gate; practice-doc support belongs in Phase 5.
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
        assert summary["no_change"] > 0, file_name

        report_df = pd.read_csv(report_csv, encoding="utf-8-sig")
        changed = report_df[report_df["status"] == "changed"].copy()

        # Appendix headings (ПРИЛОЖЕНИЕ/ПРИЛОЖЕНИЯ + level-2 'Приложение А/Б/...')
        # legitimately receive D-06 autofix toward GOST 7.32-2017 alignment
        # defaults; excluded from D-07 invariant per Phase 3 user decision
        # 2026-05-13.
        def _is_appendix_heading(text: object) -> bool:
            if not isinstance(text, str):
                return False
            return text.lstrip().upper().startswith("ПРИЛОЖЕНИ")

        # Phase 2 D-04 broadens bibliography subsection detection to all
        # Heading-styled rows inside a bibliography context, which surfaces
        # `bibliography_section_prefix` writes on subsection titles. That fix
        # is a Phase 1 feature gated on `bibliography_section_index`; it is
        # acceptable on positive corpora because the title text already
        # carries the right prefix in practice. The contract this test pins
        # is: NO direct scalar/format autofix on body or non-bibliography
        # rows. Drop bibliography labels and any row whose ONLY applied fix
        # is `bibliography_section_prefix`. Also drop appendix headings:
        # D-06 legitimately autofixes their direct overrides (see D-07 note).
        def _is_bib_only_prefix(fixes: object) -> bool:
            if not isinstance(fixes, str) or not fixes:
                return False
            tokens = {t.strip() for t in fixes.split(",") if t.strip()}
            return tokens == {"bibliography_section_prefix"}

        non_bib_changed = changed[
            (~changed["label"].isin(_BIBLIOGRAPHY_LABELS))
            & (~changed["applied_fixes"].apply(_is_bib_only_prefix))
            & (~changed["text"].apply(_is_appendix_heading))
        ]
        assert non_bib_changed.empty, (
            f"{file_name}: non-bibliography paragraphs were autofixed:\n"
            f"{non_bib_changed[['block_id', 'label', 'applied_fixes', 'text']].to_string()}"
        )

        # D-07: heading-direct-fix invariant — zero heading_* autofixes on the
        # GOST-decorated subset. The corpus sampling in 03-RESEARCH.md confirms
        # all positive heading paragraphs have ALL direct values None →
        # source='inherited' → D-05 review only → applied_fixes excludes heading
        # signature fields. If Phase 3 routing accidentally classifies a field
        # as source='direct' on a positive heading, D-06 fires and this gate
        # FAILS.
        _heading_sig_fields = {
            "font_name", "font_size", "bold", "italic", "underline", "color", "caps",
            "alignment", "first_line_indent_cm", "left_indent_cm", "right_indent_cm",
            "line_spacing", "space_before_pt", "space_after_pt",
            "keep_with_next", "keep_lines_together", "page_break_before", "widow_control",
        }

        def _has_heading_fix(fixes: object) -> bool:
            if not isinstance(fixes, str) or not fixes:
                return False
            tokens = {t.strip() for t in fixes.split(",") if t.strip()}
            return any(t.startswith("heading_") or t in _heading_sig_fields for t in tokens)

        heading_changed = changed[
            changed["label"].isin({"title_section", "title_subsection"})
            & changed["applied_fixes"].apply(_has_heading_fix)
            & (~changed["text"].apply(_is_appendix_heading))
        ]
        assert heading_changed.empty, (
            f"{file_name}: heading paragraphs were autofixed (D-07 invariant):\n"
            f"{heading_changed[['block_id', 'label', 'applied_fixes', 'text']].to_string()}"
        )

        # Plan 03-04: end-to-end signature wiring proof.
        # The predictions CSV used by audit_or_format_docx must carry the
        # heading_format_signature column produced by Plan 03-02; if a future
        # refactor drops it, the D-07 invariant above would silently become
        # vacuous (changed[label.isin(headings)] would be empty for the wrong reason).
        predictions_df = pd.read_csv(predictions_csv, encoding="utf-8-sig")
        assert "heading_format_signature" in predictions_df.columns, (
            f"{file_name}: predictions CSV missing heading_format_signature column "
            f"(Plan 03-02 wiring regressed)"
        )
        # At least one heading row in this positive doc must have a non-empty signature.
        # 1.docx and 4.docx both contain Heading 1-styled paragraphs (verified in
        # 03-RESEARCH.md "Existing Behavior of Positive Corpus"). If this assertion
        # fails, classify_style is no longer detecting headings on these docs.
        heading_rows = predictions_df[
            predictions_df["heading_format_signature"].notna()
            & predictions_df["heading_format_signature"].astype(str).str.startswith("{")
        ]
        assert not heading_rows.empty, (
            f"{file_name}: no rows have heading_format_signature populated — "
            f"Plan 03-02 lazy-extraction guard may be too restrictive"
        )
