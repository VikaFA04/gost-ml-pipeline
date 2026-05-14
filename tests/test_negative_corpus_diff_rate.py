"""D-03 / D-06: per-pair negative-corpus regression gate.

Wave B (Plan 04-02) replaces the Phase-2 aggregate-mean-only gate with a
triple-metric per-pair gate. Source of truth for ceilings is
`tests/baselines/negative_corpus.json` (loaded at runtime). The Phase 1
aggregate baseline 0.4781 now lives only in `_metadata.aggregate_mean_ceiling`.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.evaluation.format_regression_audit import (
    audit_negative_directory,
    audits_to_frame,
)

BASELINE_PATH = Path("tests/baselines/negative_corpus.json")


def _load_baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def _run_audit_for_subset(subset_filenames):
    positive_dir = Path("positive_examples")
    negative_dir = Path("negative_examples")
    if not negative_dir.exists() or not positive_dir.exists():
        if os.environ.get("CI") == "true":
            pytest.fail("Negative/positive corpus missing in CI — regression gate cannot run.")
        pytest.skip("positive_examples/ or negative_examples/ not present in this environment")
    with tempfile.TemporaryDirectory() as workspace:
        audits = audit_negative_directory(
            positive_dir,
            negative_dir,
            Path(workspace),
            profile_id="gost_7_32_2017",
        )
    frame = audits_to_frame(audits)
    return frame[frame["negative"].isin(subset_filenames)].reset_index(drop=True)


def test_per_pair_field_mismatch_no_regression() -> None:
    baseline = _load_baseline()
    subset = baseline["_metadata"]["subset_filenames"]
    frame = _run_audit_for_subset(subset)
    failures = []
    for _, row in frame.iterrows():
        name = row["negative"]
        ceiling = baseline[name]["field_mismatch_ceiling"]
        delta = int(row["field_mismatch_delta"])
        if delta > 0:
            failures.append(f"{name}: field_mismatch_delta={delta} > 0")
        after = int(row["after_field_mismatches"])
        if after > ceiling:
            failures.append(f"{name}: after_field_mismatches={after} > ceiling={ceiling}")
    assert not failures, "\n".join(failures)


def test_per_pair_after_diff_rate_no_regression() -> None:
    baseline = _load_baseline()
    subset = baseline["_metadata"]["subset_filenames"]
    frame = _run_audit_for_subset(subset)
    failures = []
    for _, row in frame.iterrows():
        name = row["negative"]
        ceiling = float(baseline[name]["after_diff_rate_ceiling"])
        actual = float(row["after_diff_rate"])
        if actual > ceiling:
            failures.append(f"{name}: after_diff_rate={actual:.6f} > ceiling={ceiling:.6f}")
    assert not failures, "\n".join(failures)


def test_subset_aggregate_mean_diff_rate_under_phase1_baseline() -> None:
    baseline = _load_baseline()
    subset = baseline["_metadata"]["subset_filenames"]
    ceiling = float(baseline["_metadata"]["aggregate_mean_ceiling"])
    frame = _run_audit_for_subset(subset)
    mean = float(frame["after_diff_rate"].mean())
    assert mean <= ceiling, f"mean after_diff_rate {mean:.4f} > ceiling {ceiling:.4f}"
