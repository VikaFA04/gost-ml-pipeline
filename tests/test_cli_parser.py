from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

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
            "--summary-json",
            str(tmp_path / "summary.json"),
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
    assert args.summary_json == str(tmp_path / "summary.json")
    assert args.profile_id == "gost_7_32_2017"
    assert args.limit == 3
    assert args.progress is True


def test_cmd_audit_regression_writes_report_csv(tmp_path) -> None:
    positive_dir = tmp_path / "positive"
    negative_dir = tmp_path / "negative"
    workspace_dir = tmp_path / "workspace"
    report_csv = tmp_path / "report.csv"
    summary_json = tmp_path / "summary.json"
    positive_dir.mkdir()
    negative_dir.mkdir()

    write_docx(positive_dir / "positive.docx", ["Paragraph"])
    write_docx(negative_dir / "negative.docx", ["Paragraph"])

    cmd_audit_regression(
        positive_dir=str(positive_dir),
        negative_dir=str(negative_dir),
        workspace_dir=str(workspace_dir),
        report_csv=str(report_csv),
        summary_json=str(summary_json),
        profile_id="gost_7_32_2017",
    )

    df = pd.read_csv(report_csv)
    assert df.loc[0, "negative"] == "negative.docx"
    assert df.loc[0, "before_field_mismatches"] == 0
    assert df.loc[0, "after_field_mismatches"] == 0
    summary = json.loads(summary_json.read_text(encoding="utf-8"))
    assert summary["audits"] == 1
    assert summary["report_csv"] == str(report_csv)


def test_cmd_audit_regression_honors_limit(tmp_path) -> None:
    positive_dir = tmp_path / "positive"
    negative_dir = tmp_path / "negative"
    workspace_dir = tmp_path / "workspace"
    report_csv = tmp_path / "report.csv"
    summary_json = tmp_path / "summary.json"
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
        summary_json=str(summary_json),
        profile_id="gost_7_32_2017",
        limit=1,
    )

    df = pd.read_csv(report_csv)
    assert df["negative"].tolist() == ["negative_one.docx"]
    summary = json.loads(summary_json.read_text(encoding="utf-8"))
    assert summary["audits"] == 1


def test_cmd_audit_regression_reports_progress(tmp_path, capsys) -> None:
    positive_dir = tmp_path / "positive"
    negative_dir = tmp_path / "negative"
    workspace_dir = tmp_path / "workspace"
    report_csv = tmp_path / "report.csv"
    summary_json = tmp_path / "summary.json"
    positive_dir.mkdir()
    negative_dir.mkdir()

    write_docx(positive_dir / "positive.docx", ["Paragraph"])
    write_docx(negative_dir / "negative.docx", ["Paragraph"])

    cmd_audit_regression(
        positive_dir=str(positive_dir),
        negative_dir=str(negative_dir),
        workspace_dir=str(workspace_dir),
        report_csv=str(report_csv),
        summary_json=str(summary_json),
        profile_id="gost_7_32_2017",
        progress=True,
    )

    captured = capsys.readouterr().out
    assert "[1/1] negative.docx" in captured
    summary = json.loads(summary_json.read_text(encoding="utf-8"))
    assert summary["audits"] == 1


def test_cmd_audit_regression_defaults_summary_json_to_report_stem(tmp_path, monkeypatch) -> None:
    from src import main as main_module

    positive_dir = tmp_path / "positive"
    negative_dir = tmp_path / "negative"
    workspace_dir = tmp_path / "workspace"
    reports_dir = tmp_path / "reports"
    positive_dir.mkdir()
    negative_dir.mkdir()
    reports_dir.mkdir()

    write_docx(positive_dir / "positive.docx", ["Paragraph"])
    write_docx(negative_dir / "negative.docx", ["Paragraph"])

    monkeypatch.setattr(main_module, "REPORTS_DIR", reports_dir)
    timestamps = iter(["20260101_010101", "20260101_010102"])
    monkeypatch.setattr(main_module, "now_ts", lambda: next(timestamps))

    main_module.cmd_audit_regression(
        positive_dir=str(positive_dir),
        negative_dir=str(negative_dir),
        workspace_dir=str(workspace_dir),
        report_csv=None,
        summary_json=None,
        profile_id="gost_7_32_2017",
    )

    report_path = reports_dir / "regression_audit_positive_negative_20260101_010101.csv"
    summary_path = reports_dir / "regression_audit_positive_negative_20260101_010101.json"
    assert report_path.exists()
    assert summary_path.exists()
    assert summary_path.stem == report_path.stem


def test_cli_parser_accepts_update_baseline_and_reason(tmp_path) -> None:
    parser = build_parser()
    baseline_path = tmp_path / "baseline.json"
    args = parser.parse_args(
        [
            "audit-regression",
            "--positive-dir", "positive_examples",
            "--negative-dir", "negative_examples",
            "--update-baseline", str(baseline_path),
            "--reason", "FIX-XX: root cause locked",
        ]
    )
    assert args.command == "audit-regression"
    assert args.update_baseline == str(baseline_path)
    assert args.reason == "FIX-XX: root cause locked"


def test_cmd_audit_regression_refuses_update_baseline_without_reason(tmp_path) -> None:
    positive_dir = tmp_path / "positive"
    negative_dir = tmp_path / "negative"
    positive_dir.mkdir()
    negative_dir.mkdir()
    # Empty positive/negative dirs are acceptable for this guard test —
    # we expect SystemExit BEFORE any audit runs because reason is too short.
    baseline_path = tmp_path / "baseline.json"
    # Sub-test cases: empty, whitespace-only, and 7-char (below 8-char Probe 6 minimum).
    for bad_reason in ("", "   ", "abcdefg"):  # 7 chars triggers Probe 6 min-length guard
        with pytest.raises(SystemExit) as excinfo:
            cmd_audit_regression(
                positive_dir=str(positive_dir),
                negative_dir=str(negative_dir),
                workspace_dir=str(tmp_path / "ws"),
                report_csv=None,
                summary_json=None,
                profile_id="gost_7_32_2017",
                limit=None,
                progress=False,
                update_baseline=str(baseline_path),
                reason=bad_reason,
            )
        assert "--update-baseline" in str(excinfo.value)
        assert "--reason" in str(excinfo.value)
