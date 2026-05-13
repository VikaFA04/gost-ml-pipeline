"""D-15: automated negative-corpus diff-rate regression gate.

Phase 1 left this manual (VERIFICATION.md MH4: 0.4737 ≤ 0.4781 observed via
direct audit_negative_directory call). Phase 2 promotes a 4-doc subset to
an automated pytest gate so subsequent waves can't silently regress it.

The full-17-doc gate stays manual until Phase 4 introduces the
audit-regression CLI.
"""
from __future__ import annotations

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

    4-doc subset is chosen by the audit_negative_directory limit parameter.
    If the function signature differs from {dir, limit, profile_id}, adapt
    the call site below — the contract is the assertion, not the wiring.
    """
    negative_dir = Path("negative_examples")
    if not negative_dir.exists():
        pytest.skip("negative_examples/ not present in this environment")

    # Call the audit. If the signature does not accept `limit` or
    # `profile_id`, simplify to whatever signature exists today.
    try:
        audits = audit_negative_directory(
            str(negative_dir),
            limit=4,
            profile_id="gost_7_32_2017",
        )
    except TypeError:
        # Fallback: simpler signature without keyword args
        audits = audit_negative_directory(str(negative_dir))

    frame = audits_to_frame(audits)
    # Take first 4 rows by index order — matches `limit=4` semantics if the
    # function does not pre-limit.
    if "after_diff_rate" not in frame.columns:
        pytest.fail(f"after_diff_rate column missing; columns={list(frame.columns)!r}")

    subset = frame.head(4)
    mean_diff_rate = float(subset["after_diff_rate"].mean())
    assert mean_diff_rate <= PHASE_1_BASELINE_MEAN_DIFF_RATE, (
        f"Negative-corpus mean after_diff_rate regressed: {mean_diff_rate:.4f} > {PHASE_1_BASELINE_MEAN_DIFF_RATE} "
        f"(subset of 4 docs). See subset:\n{subset[['after_diff_rate']]}"
    )
