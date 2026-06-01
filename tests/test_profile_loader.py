"""Unit tests for src/rules/profile_loader.py D-11 + D-03 helpers, and
src/rules/profile_validator.py D-03 + D-11 schema extension.

RED-state in Wave 0 (phase 02-bibliography-list-semantics). Plan 02 (Wave 1)
implements the helpers and the validator extensions so these turn GREEN.
"""
from __future__ import annotations

import pytest

from src.rules.profile_loader import load_profile
from src.rules.profile_validator import validate_profile


def test_list_detection_thresholds_from_profile() -> None:
    """D-11: get_list_detection_thresholds returns (40, 300) for gost_7_32_2017."""
    from src.rules.profile_loader import get_list_detection_thresholds  # NEW helper — RED via ImportError today

    profile = load_profile(profile_id="gost_7_32_2017")
    max_words, max_chars = get_list_detection_thresholds(profile)
    assert max_words == 40
    assert max_chars == 300


def test_bibliography_numbering_scope_default_is_per_section() -> None:
    """D-03: get_bibliography_numbering_scope returns 'per_section' default for gost_7_32_2017."""
    from src.rules.profile_loader import get_bibliography_numbering_scope  # NEW helper — RED via ImportError today

    profile = load_profile(profile_id="gost_7_32_2017")
    assert get_bibliography_numbering_scope(profile) == "per_section"


def test_validator_accepts_profile_without_optional_sections() -> None:
    """Existing profiles (mirea_normcontrol_local.json,
    gost_r_7_0_100_2018_bibliography.json) MUST continue to validate after
    D-03 + D-11 add optional sections. Sanity guard against regression."""
    for profile_id in ("mirea_normcontrol_local", "gost_r_7_0_100_2018_bibliography"):
        profile = load_profile(profile_id=profile_id)
        # load_profile calls assert_valid_profile internally — reaching here means OK.
        assert profile["profile_id"], f"profile {profile_id!r} missing profile_id"


def test_validator_rejects_invalid_scope() -> None:
    """D-03: numbering.bibliography.scope must be one of
    {per_document, per_section, per_subsection_pattern}. Anything else returns
    a validation error."""
    # Construct a minimal-but-otherwise-valid profile by loading gost_7_32_2017
    # and mutating just the field under test. This way we don't need to author
    # all REQUIRED_TOP_LEVEL_KEYS manually.
    profile = load_profile(profile_id="gost_7_32_2017")
    profile.setdefault("numbering", {}).setdefault("bibliography", {})["scope"] = "INVALID_VALUE"
    errors = validate_profile(profile)
    assert any("scope" in err.lower() for err in errors), (
        f"Expected validator to reject scope='INVALID_VALUE', got errors={errors!r}"
    )
