"""Helpers to persist evaluation outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def write_json_report(report: dict[str, object], output_path: Path) -> None:
    """Write a JSON report to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv_report(df: pd.DataFrame, output_path: Path) -> None:
    """Write a dataframe to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")


def write_text_report(text: str, output_path: Path) -> None:
    """Write a plain text report to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
