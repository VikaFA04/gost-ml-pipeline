"""
Phase 8 SC-2 acceptance gate.

Reads the most recent classical zoo run from results/reports/classical_zoo_<ts>/
and asserts the linear_svm_production row clears the Phase 8 SC-2 floor.

This test is NOT a unit test for src/. It is an artifact-level acceptance gate.
Run 'python -m src.main compare-classical' (or 'make compare-classical-acceptance')
before invoking this test directly.

SC-2 floor (D-D-02 + D-E-01):
  linear_svm_production  weighted_f1 >= 0.94
  linear_svm_production  macro_f1 >= 0.86
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

_REPORTS_DIR = Path(__file__).parent.parent / "results" / "reports"
_SC2_ROW = "linear_svm_production"
_SC2_WEIGHTED_F1_FLOOR = 0.94
_SC2_MACRO_F1_FLOOR = 0.86


def _find_latest_zoo_csv() -> Path | None:
    """Return results.csv from the most recent classical_zoo run, or None."""
    candidates = sorted(_REPORTS_DIR.glob("classical_zoo_*/results.csv"), reverse=True)
    return candidates[0] if candidates else None


def test_linear_svm_production_clears_phase_8_sc2_floor() -> None:
    """Phase 8 SC-2: linear_svm_production row must clear weighted_f1>=0.94 AND macro_f1 >= 0.86."""
    csv_path = _find_latest_zoo_csv()
    if csv_path is None:
        pytest.skip(
            "No zoo run found. Run 'python -m src.main compare-classical' first "
            "(or 'make compare-classical-acceptance' to run both steps at once)."
        )

    df = pd.read_csv(csv_path)

    prod_rows = df[df["model"] == _SC2_ROW]
    assert len(prod_rows) == 1, (
        f"Expected exactly 1 '{_SC2_ROW}' row in {csv_path}, got {len(prod_rows)}.\n"
        f"Available models: {df['model'].tolist()}"
    )

    row = prod_rows.iloc[0]

    assert row["weighted_f1"] >= _SC2_WEIGHTED_F1_FLOOR, (
        f"Phase 8 SC-2 FAIL: {_SC2_ROW} weighted_f1={row['weighted_f1']:.4f} "
        f"< {_SC2_WEIGHTED_F1_FLOOR} floor. "
        f"Source CSV: {csv_path}"
    )
    assert row["macro_f1"] >= _SC2_MACRO_F1_FLOOR, (
        f"Phase 8 SC-2 FAIL: {_SC2_ROW} macro_f1={row['macro_f1']:.4f} "
        f"< {_SC2_MACRO_F1_FLOOR} floor. "
        f"Source CSV: {csv_path}"
    )
