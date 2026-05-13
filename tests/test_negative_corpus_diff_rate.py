"""D-15: automated negative-corpus diff-rate regression gate.

Phase 1 left this manual (VERIFICATION.md MH4: 0.4737 ≤ 0.4781 observed via
direct audit_negative_directory call). Phase 2 promotes a 4-doc subset to
an automated pytest gate so subsequent waves can't silently regress it.

The full-17-doc gate stays manual until Phase 4 introduces the
audit-regression CLI.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.evaluation.format_regression_audit import (
    audit_negative_directory,
    audits_to_frame,
)

PHASE_1_BASELINE_MEAN_DIFF_RATE = 0.4781


def test_negative_corpus_diff_rate_phase2_baseline() -> None:
    """Mean after_diff_rate across a 4-doc subset of negative_examples/ MUST
    stay ≤ 0.4781 (FORMAT_FIX_PLAN Этап 8 baseline carried by Phase 1).

    4-doc subset is selected via the audit_negative_directory `limit` kwarg.
    """
    positive_dir = Path("positive_examples")
    negative_dir = Path("negative_examples")
    if not negative_dir.exists() or not positive_dir.exists():
        pytest.skip("positive_examples/ or negative_examples/ not present in this environment")

    with tempfile.TemporaryDirectory() as workspace:
        audits = audit_negative_directory(
            positive_dir,
            negative_dir,
            Path(workspace),
            profile_id="gost_7_32_2017",
            limit=4,
        )

    frame = audits_to_frame(audits)
    if "after_diff_rate" not in frame.columns:
        pytest.fail(f"after_diff_rate column missing; columns={list(frame.columns)!r}")

    mean_diff_rate = float(frame["after_diff_rate"].mean())
    assert mean_diff_rate <= PHASE_1_BASELINE_MEAN_DIFF_RATE, (
        f"Negative-corpus mean after_diff_rate regressed: {mean_diff_rate:.4f} > {PHASE_1_BASELINE_MEAN_DIFF_RATE} "
        f"(subset of {len(frame)} docs). See subset:\n{frame[['after_diff_rate']]}"
    )
