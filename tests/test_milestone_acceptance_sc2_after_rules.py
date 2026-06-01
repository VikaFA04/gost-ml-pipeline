"""
Phase 8 SC-2 after-rules production floor gate.

Reads the most recent results/metrics/evaluation_*.json produced by
'python -m src.main train' and asserts the after_rules block clears:
  weighted avg f1-score >= 0.94
  macro avg    f1-score >= 0.9414

Conservative approach per D-E-04: skip if no evaluation_*.json exists.
Do NOT invoke training from inside this test.

Paired with test_phase_8_sc2_acceptance.py (raw-ML zoo CSV half).
Both halves must pass for SC-2 acceptance.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

_METRICS_DIR = Path(__file__).parent.parent / "results" / "metrics"
_WEIGHTED_F1_FLOOR = 0.94
_MACRO_F1_FLOOR = 0.9414


def _load_latest_evaluation() -> dict:
    candidates = sorted(_METRICS_DIR.glob("evaluation_*.json"), reverse=True)
    if not candidates:
        pytest.skip(
            "No evaluation_*.json found in results/metrics/. "
            "Run 'python -m src.main train' first. "
            "See D-E-04 in 08-CONTEXT.md."
        )
    with candidates[0].open(encoding="utf-8") as fh:
        return json.load(fh), candidates[0]


def test_sc2_after_rules_floor() -> None:
    """SC-2(b): production after-rules floor — weighted_f1 >= 0.94, macro_f1 >= 0.9414."""
    data, source = _load_latest_evaluation()
    after = data.get("after_rules", {})
    weighted_f1 = after.get("weighted avg", {}).get("f1-score")
    macro_f1 = after.get("macro avg", {}).get("f1-score")
    assert weighted_f1 is not None, (
        f"'after_rules.weighted avg.f1-score' key absent in {source}"
    )
    assert macro_f1 is not None, (
        f"'after_rules.macro avg.f1-score' key absent in {source}"
    )
    assert weighted_f1 >= _WEIGHTED_F1_FLOOR, (
        f"SC-2(b) FAIL: after_rules weighted_f1={weighted_f1:.4f} < {_WEIGHTED_F1_FLOOR}. "
        f"Source: {source}"
    )
    assert macro_f1 >= _MACRO_F1_FLOOR, (
        f"SC-2(b) FAIL: after_rules macro_f1={macro_f1:.4f} < {_MACRO_F1_FLOOR}. "
        f"Source: {source}"
    )
