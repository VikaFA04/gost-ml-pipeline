"""
Phase 8 SC-4 gate.

Direct file-read assertions per D-E-01 (amends D-C-02):
  1. 07-UAT.md frontmatter contains 'status: complete'.
  2. Zero lines matching r'severity:\\s*(blocker|high)' in 07-UAT.md.
  3. 09-03-SUMMARY.md exists (UAT 8/8 inline record).
  4. Zero lines matching r'severity:\\s*(blocker|high)' in 09-03-SUMMARY.md.
  5. 08-DESIGN-REVIEW-ROLLUP.md exists (written in 08-03).

Phase 6 design-review sign-off is synthesised from 06-05-SUMMARY.md per D-E-02;
the ROLLUP document records this. SC-4 asserts the ROLLUP exists, not a formal
sign-off field in 06-DESIGN-REVIEW.md (which was left blank by Phase 6).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).parent.parent
_PLANNING = _REPO / ".planning" / "phases"

_UAT_07 = _PLANNING / "07-pdf-text-layer-audit-slice" / "07-UAT.md"
_SUMMARY_09 = (
    _PLANNING
    / "09-classical-model-zoo-lr-svm-complementnb-randomforest-histgbm"
    / "09-03-SUMMARY.md"
)
_ROLLUP_08 = _PLANNING / "08-milestone-acceptance" / "08-DESIGN-REVIEW-ROLLUP.md"

_SEVERITY_RE = re.compile(r"severity:\s*(blocker|high)", re.IGNORECASE)


def _read(path: Path) -> str:
    assert path.exists(), f"Required file absent: {path}"
    return path.read_text(encoding="utf-8")


def test_sc4_phase7_uat_status_complete() -> None:
    """07-UAT.md frontmatter must contain 'status: complete'."""
    text = _read(_UAT_07)
    assert "status: complete" in text, (
        f"'status: complete' not found in {_UAT_07}.\n"
        f"First 400 chars:\n{text[:400]}"
    )


def test_sc4_phase7_no_open_severity() -> None:
    """07-UAT.md must have zero 'severity: blocker|high' lines."""
    text = _read(_UAT_07)
    matches = _SEVERITY_RE.findall(text)
    assert not matches, (
        f"Found {len(matches)} open severity lines in {_UAT_07}: {matches}"
    )


def test_sc4_phase9_summary_exists() -> None:
    """09-03-SUMMARY.md must exist (UAT 8/8 inline record)."""
    assert _SUMMARY_09.exists(), f"09-03-SUMMARY.md absent: {_SUMMARY_09}"


def test_sc4_phase9_no_open_severity() -> None:
    """09-03-SUMMARY.md must have zero 'severity: blocker|high' lines."""
    text = _read(_SUMMARY_09)
    matches = _SEVERITY_RE.findall(text)
    assert not matches, (
        f"Found {len(matches)} open severity lines in {_SUMMARY_09}: {matches}"
    )


def test_sc4_rollup_exists() -> None:
    """08-DESIGN-REVIEW-ROLLUP.md must exist (written in 08-03)."""
    assert _ROLLUP_08.exists(), (
        f"08-DESIGN-REVIEW-ROLLUP.md absent: {_ROLLUP_08}. "
        "Run plan 08-03 Task 1 to create it."
    )
