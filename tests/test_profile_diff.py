from __future__ import annotations

from pathlib import Path

import pytest

from src.rules.profile_diff import compute_profile_diff, write_diff_sidecar


def test_compute_profile_diff_emits_arrow_line_per_changed_leaf() -> None:
    """5-02-RED carrier: scalar leaves on both sides → one diff line per change."""
    base = {"document_rules": {"page": {"margin_left_cm": 3.0, "margin_right_cm": 1.0}}}
    cand = {"document_rules": {"page": {"margin_left_cm": 2.5, "margin_right_cm": 1.0}}}
    lines = compute_profile_diff(base, cand)
    joined = "\n".join(lines)
    assert "## document_rules" in joined
    # Unicode arrow U+2192 explicitly
    assert "document_rules.page.margin_left_cm: 3.0 → 2.5" in joined
    # Unchanged leaf does NOT appear
    assert "margin_right_cm" not in joined


def test_compute_profile_diff_groups_by_top_level_key() -> None:
    base = {
        "document_rules": {"page": {"margin_left_cm": 3.0}},
        "labels": {"body_text": {"style_profile": {"font_size_pt": 14.0}}},
    }
    cand = {
        "document_rules": {"page": {"margin_left_cm": 2.5}},
        "labels": {"body_text": {"style_profile": {"font_size_pt": 12.0}}},
    }
    lines = compute_profile_diff(base, cand)
    # Both section headers present
    assert "## document_rules" in lines
    assert "## labels" in lines
    # Sections appear in sorted order: document_rules before labels
    dr_idx = lines.index("## document_rules")
    lb_idx = lines.index("## labels")
    assert dr_idx < lb_idx


def test_compute_profile_diff_filters_source_metadata_paths() -> None:
    """5-02-RED carrier per Pitfall 4: _source paths are NEVER emitted."""
    base = {
        "document_rules": {
            "page": {
                "margin_left_cm": {
                    "value": 3.0,
                    "_source": {"file": "a.pdf", "loc": "page_1", "confidence": 0.85, "needs_review": False},
                },
            },
        },
    }
    cand = {
        "document_rules": {
            "page": {
                "margin_left_cm": {
                    "value": 3.0,  # value UNCHANGED
                    "_source": {"file": "b.pdf", "loc": "page_7", "confidence": 0.92, "needs_review": False},
                },
            },
        },
    }
    lines = compute_profile_diff(base, cand)
    # Only _source fields differ → diff must be empty (after filter)
    for line in lines:
        assert "_source" not in line, f"Pitfall 4 violated: {line!r}"
        assert "._source." not in line


def test_compute_profile_diff_handles_methodical_leaf_vs_scalar_base() -> None:
    """Base is bare scalar (GOST profile); candidate is {value, _source} dict
       (methodical-extracted). Diff compares VALUES, not the wrapper dict."""
    base = {"document_rules": {"page": {"margin_left_cm": 3.0}}}
    cand = {
        "document_rules": {
            "page": {
                "margin_left_cm": {
                    "value": 2.5,
                    "_source": {"file": "x.pdf", "loc": "page_3", "confidence": 0.85, "needs_review": False},
                },
            },
        },
    }
    lines = compute_profile_diff(base, cand)
    joined = "\n".join(lines)
    assert "document_rules.page.margin_left_cm: 3.0 → 2.5" in joined


def test_compute_profile_diff_no_changes_returns_empty() -> None:
    base = {"document_rules": {"page": {"margin_left_cm": 3.0}}}
    cand = {"document_rules": {"page": {"margin_left_cm": 3.0}}}
    assert compute_profile_diff(base, cand) == []


def test_compute_profile_diff_marks_missing_paths() -> None:
    """Path present in base but not candidate → `<missing>` placeholder on candidate side."""
    base = {"document_rules": {"page": {"margin_left_cm": 3.0, "margin_right_cm": 1.0}}}
    cand = {"document_rules": {"page": {"margin_left_cm": 3.0}}}
    lines = compute_profile_diff(base, cand)
    joined = "\n".join(lines)
    assert "margin_right_cm" in joined
    assert "<missing>" in joined


def test_write_diff_sidecar_writes_utf8(tmp_path) -> None:
    target = tmp_path / "preview.diff.txt"
    lines = ["## document_rules", "document_rules.page.margin_left_cm: 3.0 → 2.5"]
    write_diff_sidecar(lines, target)
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "→" in content  # U+2192 preserved
    assert content.endswith("\n")  # trailing newline


def test_write_diff_sidecar_creates_parent_dir(tmp_path) -> None:
    nested = tmp_path / "deep" / "nested" / "preview.diff.txt"
    write_diff_sidecar(["x: 1 → 2"], nested)
    assert nested.exists()
