from __future__ import annotations

from src.main import build_parser


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
