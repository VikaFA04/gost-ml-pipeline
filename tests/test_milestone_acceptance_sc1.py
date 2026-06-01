"""
Phase 8 SC-1 acceptance gate.

Calls process_document() on the fast-tier corpus subset (always) and the
slow-tier full corpus (local only, marked @pytest.mark.slow).

Fast-tier fixtures: tests/fixtures/corpus/positive/{1.docx,4.docx}
Slow-tier: positive_examples/ + negative_examples/ (gitignored; skips if absent)

SC-1 contract (D-E-08 + D-A-02):
  - Every fixture produces a non-empty report CSV.
  - Every row in the report CSV has a non-empty "status" field.
  - No fixture raises an unhandled exception.
"""
from __future__ import annotations

import pandas as pd
import pytest
from pathlib import Path

from src.inference.application_service import process_document

_REPO = Path(__file__).parent.parent
_FAST_POSITIVE = [
    _REPO / "tests" / "fixtures" / "corpus" / "positive" / "1.docx",
    _REPO / "tests" / "fixtures" / "corpus" / "positive" / "4.docx",
]
_PROFILE = _REPO / "src" / "rules" / "profiles" / "gost_7_32_2017.json"
_MODEL = "baseline"


def _run_fixture(docx_path: Path) -> Path:
    """Run process_document on one fixture and return report_csv path."""
    artifacts = process_document(
        input_path=docx_path,
        model_choice=_MODEL,
        mode="fix",
        profile_path=_PROFILE,
    )
    return artifacts.report_csv


def _assert_report(report_csv: Path, fixture: Path) -> None:
    assert report_csv.exists(), f"report_csv not created for {fixture}"
    df = pd.read_csv(report_csv)
    assert not df.empty, f"report_csv is empty for {fixture}"
    assert "status" in df.columns, f"'status' column missing in report for {fixture}"
    missing = df[df["status"].isna() | (df["status"].astype(str).str.strip() == "")]
    assert missing.empty, (
        f"{len(missing)} rows have empty 'status' in report for {fixture}"
    )


@pytest.mark.parametrize("fixture", _FAST_POSITIVE)
def test_sc1_fast_tier(fixture: Path) -> None:
    """SC-1 fast tier — always runs in CI."""
    if not fixture.exists():
        pytest.skip(f"Fast-tier fixture absent: {fixture}")
    report_csv = _run_fixture(fixture)
    _assert_report(report_csv, fixture)


@pytest.mark.slow
def test_sc1_slow_tier() -> None:
    """SC-1 slow tier — full corpus; local-only."""
    positive_dir = _REPO / "positive_examples"
    negative_dir = _REPO / "negative_examples"
    if not positive_dir.exists() and not negative_dir.exists():
        pytest.skip(
            "Slow-tier corpus absent (positive_examples/ + negative_examples/ not found). "
            "Run locally with full corpus before milestone acceptance."
        )
    fixtures = []
    for d in (positive_dir, negative_dir):
        if d.exists():
            fixtures.extend(sorted(p for p in d.rglob("*.docx") if not p.name.startswith("~$")))
    assert fixtures, "Slow-tier dirs exist but contain no .docx files"
    for fixture in fixtures:
        report_csv = _run_fixture(fixture)
        _assert_report(report_csv, fixture)
