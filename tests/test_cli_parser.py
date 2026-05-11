from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.main import build_parser, cmd_audit_regression


def write_docx(path: Path, paragraphs: list[str]) -> None:
    from docx import Document

    document = Document()
    for text in paragraphs:
        document.add_paragraph(text)
    document.save(path)


def test_cli_parser_exposes_mvp_commands() -> None:
    parser = build_parser()
    subparsers_action = next(action for action in parser._actions if action.dest == "command")

    assert set(subparsers_action.choices) >= {
        "train",
        "extract-docx",
        "predict",
        "evaluate",
        "audit-docx",
        "format-docx",
        "audit-regression",
        "extract-methodical-profile",
    }


def test_cli_parser_accepts_predict_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "predict",
            "--model-path",
            "model.joblib",
            "--input-csv",
            "blocks.csv",
            "--output-csv",
            "predictions.csv",
        ]
    )

    assert args.command == "predict"
    assert args.model_path == "model.joblib"
    assert args.input_csv == "blocks.csv"
    assert args.output_csv == "predictions.csv"


def test_cli_parser_accepts_methodical_profile_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "extract-methodical-profile",
            "--input-path",
            "guideline.txt",
            "--output-dir",
            "profiles",
            "--profile-name",
            "Локальная методичка",
            "--base-profile-ids",
            "gost_7_32_2017",
            "gost_r_7_0_100_2018_bibliography",
        ]
    )

    assert args.command == "extract-methodical-profile"
    assert args.input_path == "guideline.txt"
    assert args.output_dir == "profiles"
    assert args.profile_name == "Локальная методичка"
    assert args.base_profile_ids == ["gost_7_32_2017", "gost_r_7_0_100_2018_bibliography"]


def test_cli_parser_accepts_audit_regression_arguments(tmp_path) -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "audit-regression",
            "--positive-dir",
            "positive_examples",
            "--negative-dir",
            "negative_examples",
            "--workspace-dir",
            str(tmp_path / "workspace"),
            "--report-csv",
            str(tmp_path / "report.csv"),
            "--profile-id",
            "gost_7_32_2017",
            "--limit",
            "3",
            "--progress",
        ]
    )

    assert args.command == "audit-regression"
    assert args.positive_dir == "positive_examples"
    assert args.negative_dir == "negative_examples"
    assert args.workspace_dir == str(tmp_path / "workspace")
    assert args.report_csv == str(tmp_path / "report.csv")
    assert args.profile_id == "gost_7_32_2017"
    assert args.limit == 3
    assert args.progress is True


def test_cmd_audit_regression_writes_report_csv(tmp_path) -> None:
    positive_dir = tmp_path / "positive"
    negative_dir = tmp_path / "negative"
    workspace_dir = tmp_path / "workspace"
    report_csv = tmp_path / "report.csv"
    positive_dir.mkdir()
    negative_dir.mkdir()

    write_docx(positive_dir / "positive.docx", ["Paragraph"])
    write_docx(negative_dir / "negative.docx", ["Paragraph"])

    cmd_audit_regression(
        positive_dir=str(positive_dir),
        negative_dir=str(negative_dir),
        workspace_dir=str(workspace_dir),
        report_csv=str(report_csv),
        profile_id="gost_7_32_2017",
    )

    df = pd.read_csv(report_csv)
    assert df.loc[0, "negative"] == "negative.docx"
    assert df.loc[0, "before_field_mismatches"] == 0
    assert df.loc[0, "after_field_mismatches"] == 0


def test_cmd_audit_regression_honors_limit(tmp_path) -> None:
    positive_dir = tmp_path / "positive"
    negative_dir = tmp_path / "negative"
    workspace_dir = tmp_path / "workspace"
    report_csv = tmp_path / "report.csv"
    positive_dir.mkdir()
    negative_dir.mkdir()

    write_docx(positive_dir / "positive.docx", ["Paragraph"])
    write_docx(negative_dir / "negative_one.docx", ["Paragraph"])
    write_docx(negative_dir / "negative_two.docx", ["Paragraph"])

    cmd_audit_regression(
        positive_dir=str(positive_dir),
        negative_dir=str(negative_dir),
        workspace_dir=str(workspace_dir),
        report_csv=str(report_csv),
        profile_id="gost_7_32_2017",
        limit=1,
    )

    df = pd.read_csv(report_csv)
    assert df["negative"].tolist() == ["negative_one.docx"]


def test_cmd_audit_regression_reports_progress(tmp_path, capsys) -> None:
    positive_dir = tmp_path / "positive"
    negative_dir = tmp_path / "negative"
    workspace_dir = tmp_path / "workspace"
    report_csv = tmp_path / "report.csv"
    positive_dir.mkdir()
    negative_dir.mkdir()

    write_docx(positive_dir / "positive.docx", ["Paragraph"])
    write_docx(negative_dir / "negative.docx", ["Paragraph"])

    cmd_audit_regression(
        positive_dir=str(positive_dir),
        negative_dir=str(negative_dir),
        workspace_dir=str(workspace_dir),
        report_csv=str(report_csv),
        profile_id="gost_7_32_2017",
        progress=True,
    )

    captured = capsys.readouterr().out
    assert "[1/1] negative.docx" in captured
