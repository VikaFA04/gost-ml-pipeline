"""Phase 5 plan 5-04: profile schema lint (two-tier, D-08 + Pitfall 1).

Tier A applies to ALL src/rules/profiles/*.json (GOST + methodical).
Tier B applies only to profile_type == "methodical_guidelines" — at HEAD this
set is empty so Tier B passes vacuously; plan 5-05 CI runs Бергер extraction
which makes Tier B fire substantively.

The synthetic-RED carrier (`test_red_carrier_fires_on_synthetic_methodical_profile`)
is the explicit RED carrier per Phase 4 Wave C Option 1 deviation — at RED the
methodical required-key set contains a bogus extra key that no profile carries,
so the synthetic profile is missing it and the test fails. The GREEN commit
removes the bogus key from `REQUIRED_TOP_LEVEL_KEYS_FOR_METHODICAL`. The test
is retained post-GREEN as a permanent regression guard against future
re-introduction of a divergent required-key set.

The other tests over real profiles in `src/rules/profiles/*.json` stay GREEN
at HEAD because no methodical-typed profile is committed (Tier B vacuous).
"""
from __future__ import annotations

import json
from pathlib import Path

from src.rules.profile_validator import validate_profile

PROFILES_DIR = Path("src/rules/profiles")

# Tier A — all profiles must carry these top-level keys.
REQUIRED_TOP_LEVEL_KEYS_FOR_ANY = {
    "profile_id", "profile_name", "profile_type", "is_default",
}

# Tier B — methodical profiles additionally must have these.
REQUIRED_TOP_LEVEL_KEYS_FOR_METHODICAL = {
    "profile_id", "profile_name", "profile_type", "is_default",
    "extraction_meta",
}


def _load_all_profiles() -> list[tuple[Path, dict]]:
    return [
        (p, json.loads(p.read_text(encoding="utf-8")))
        for p in sorted(PROFILES_DIR.glob("*.json"))
    ]


def _walk_leaf_paths(node, prefix=""):
    """Yield (path, value) for every leaf. Annotated leaves are treated as a single leaf."""
    if isinstance(node, dict):
        if set(node.keys()) >= {"value", "_source"}:
            yield (prefix, node)
            return
        for k, v in node.items():
            if k == "_source":
                continue
            new = f"{prefix}.{k}" if prefix else k
            yield from _walk_leaf_paths(v, new)
    elif isinstance(node, list):
        # lists treated as leaves (consistent with profile_diff._flatten)
        yield (prefix, node)
    else:
        yield (prefix, node)


def _any_leaf_needs_review(node) -> bool:
    if isinstance(node, dict):
        if "_source" in node and isinstance(node["_source"], dict):
            if node["_source"].get("needs_review"):
                return True
        return any(
            _any_leaf_needs_review(v) for k, v in node.items() if k != "_source"
        )
    if isinstance(node, list):
        return any(_any_leaf_needs_review(item) for item in node)
    return False


# ---------- Tier A: all profiles ----------

def test_every_profile_passes_validator() -> None:
    """Tier A — every src/rules/profiles/*.json validates."""
    failures = []
    for path, profile in _load_all_profiles():
        errors = validate_profile(profile)
        if errors:
            failures.append(f"{path.name}: {errors}")
    assert not failures, "\n".join(failures)


def test_every_profile_has_required_top_level_keys() -> None:
    """Tier A — universal top-level shape."""
    failures = []
    for path, profile in _load_all_profiles():
        missing = REQUIRED_TOP_LEVEL_KEYS_FOR_ANY - set(profile)
        if missing:
            failures.append(f"{path.name}: missing {sorted(missing)}")
    assert not failures, "\n".join(failures)


# ---------- Tier B: methodical profiles only ----------

def test_red_carrier_bogus_required_field() -> None:
    """RED carrier per Phase 4 Wave C Option 1 — bogus-required-field shape mismatch.

    Iterates real methodical profiles and asserts none are missing any of
    REQUIRED_TOP_LEVEL_KEYS_FOR_METHODICAL. Vacuous over real profiles at HEAD
    because no methodical profile is committed; substantive once plan 5-05
    Бергер extraction lands a methodical profile. The synthetic-profile twin
    below makes the RED empirically observable at HEAD.
    """
    failures = []
    for path, profile in _load_all_profiles():
        if profile.get("profile_type") != "methodical_guidelines":
            continue
        missing = REQUIRED_TOP_LEVEL_KEYS_FOR_METHODICAL - set(profile)
        if missing:
            failures.append(f"{path.name}: missing {sorted(missing)}")
    assert not failures, "\n".join(failures)


def test_red_carrier_fires_on_synthetic_methodical_profile() -> None:
    """Force RED at HEAD by injecting a synthetic methodical profile.

    The synthetic profile carries every documented field of a methodical
    profile. At RED, REQUIRED_TOP_LEVEL_KEYS_FOR_METHODICAL had a bogus extra
    key (Phase 4 Wave C Option 1 carrier) that no profile — synthetic or real —
    could supply, so the assertion failed. GREEN removed the bogus key. The
    test is retained as a permanent regression guard: any future commit that
    re-adds a divergent required key here will trip this assertion immediately
    rather than waiting for a methodical profile to land on disk.
    """
    synthetic = {
        "profile_id": "methodical_synthetic_for_lint",
        "profile_name": "synthetic",
        "profile_type": "methodical_guidelines",
        "is_default": False,
        "extraction_meta": {"needs_manual_review": True},
    }
    missing = REQUIRED_TOP_LEVEL_KEYS_FOR_METHODICAL - set(synthetic)
    assert not missing, f"synthetic methodical profile missing {sorted(missing)}"


def test_every_methodical_profile_has_source_per_leaf() -> None:
    """Tier B — every leaf in document_rules.*, labels.*.style_profile, bibliography_rules.*
    of a methodical profile carries `_source` per D-05.

    Vacuous at HEAD; substantive after a methodical profile lands."""
    failures = []
    for path, profile in _load_all_profiles():
        if profile.get("profile_type") != "methodical_guidelines":
            continue
        # Walk only the policy subtrees that D-05 mandates _source for
        for subtree_key in ("document_rules", "labels", "bibliography_rules"):
            subtree = profile.get(subtree_key, {})
            for leaf_path, leaf in _walk_leaf_paths(subtree, prefix=subtree_key):
                # labels-level leaves we care about live under labels.<x>.style_profile.*
                if subtree_key == "labels" and ".style_profile." not in leaf_path:
                    continue
                if not isinstance(leaf, dict) or "_source" not in leaf:
                    failures.append(f"{path.name}: {leaf_path} missing _source")
    assert not failures, "\n".join(failures)


def test_methodical_needs_manual_review_consistent_with_per_leaf_sources() -> None:
    """Tier B — derived field consistency per D-05 + Pitfall 8.
    Vacuous at HEAD; substantive after a methodical profile lands."""
    failures = []
    for path, profile in _load_all_profiles():
        if profile.get("profile_type") != "methodical_guidelines":
            continue
        declared = profile.get("extraction_meta", {}).get("needs_manual_review")
        computed = _any_leaf_needs_review(profile)
        if declared is not computed:
            failures.append(
                f"{path.name}: declared={declared!r} but any-leaf-needs-review={computed!r}"
            )
    assert not failures, "\n".join(failures)
