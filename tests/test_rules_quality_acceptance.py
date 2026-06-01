from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import pytest

from src.evaluation.format_regression_audit import build_regression_predictions
from src.generate.inplace_formatter import audit_or_format_docx

RULES_PATH = Path("src/rules/formatting_rules_v1.json")

REQUIRED_FIELDS = {
    "id",
    "applicable_labels",
    "parameter",
    "expected_value",
    "action",
    "severity",
    "autocorrect",
    "priority",
}
ALLOWED_ACTION_VALUES = {"fix", "review", "check_or_fix"}
ALLOWED_SEVERITY_VALUES = {"low", "medium", "high"}


def _load_rules() -> list[dict]:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))["rules"]


def test_every_rule_carries_full_rulerecord_shape() -> None:
    rules = _load_rules()
    assert rules, "formatting_rules_v1.json is empty"
    failures = []
    for rule in rules:
        missing = REQUIRED_FIELDS - set(rule.keys())
        if missing:
            failures.append(f"{rule.get('id', '<no-id>')}: missing fields {sorted(missing)}")
    assert not failures, "\n".join(failures)


def test_every_rule_has_unique_id() -> None:
    rules = _load_rules()
    ids = [r["id"] for r in rules]
    assert len(ids) == len(set(ids)), f"duplicate rule ids: {[i for i in ids if ids.count(i) > 1]}"


def test_every_rule_action_and_severity_in_allowed_set() -> None:
    rules = _load_rules()
    failures = []
    for r in rules:
        if r["action"] not in ALLOWED_ACTION_VALUES:
            failures.append(f"{r['id']}: action='{r['action']}' not in {sorted(ALLOWED_ACTION_VALUES)}")
        if r["severity"] not in ALLOWED_SEVERITY_VALUES:
            failures.append(f"{r['id']}: severity='{r['severity']}' not in {sorted(ALLOWED_SEVERITY_VALUES)}")
    assert not failures, "\n".join(failures)


def test_every_rule_priority_is_int() -> None:
    rules = _load_rules()
    failures = [r["id"] for r in rules if not isinstance(r["priority"], int)]
    assert not failures, f"non-int priority on rules: {failures}"


def test_every_rule_autocorrect_is_bool() -> None:
    rules = _load_rules()
    failures = [r["id"] for r in rules if not isinstance(r["autocorrect"], bool)]
    assert not failures, f"non-bool autocorrect on rules: {failures}"


def test_audit_csv_invariants_on_negative_fixture(tmp_path) -> None:
    """Runtime smoke: pick positive_examples/3.docx, audit it, enforce
    REQ-rules-quality-acceptance acceptance bullets:
      - every status=changed row has non-empty applied_fixes
      - every manual_review_required=True row has non-empty explanation
      - every low_confidence=True row routes to manual_review_required=True
    """
    input_docx = Path("positive_examples") / "3.docx"
    if not input_docx.exists():
        if os.environ.get("CI") == "true":
            pytest.fail("positive_examples/3.docx missing in CI — rules-quality smoke cannot run.")
        pytest.skip("positive_examples/3.docx not present in this environment")

    predictions_csv = tmp_path / "3_predictions.csv"
    report_csv = tmp_path / "3_report.csv"
    formatted = tmp_path / "3_formatted.docx"
    build_regression_predictions(input_docx, predictions_csv)
    audit_or_format_docx(
        input_docx=input_docx,
        predictions_csv=predictions_csv,
        report_csv=report_csv,
        output_docx=formatted,
        apply_safe=True,
        profile_id="gost_7_32_2017",
    )
    df = pd.read_csv(report_csv, encoding="utf-8-sig")

    changed = df[df["status"] == "changed"]
    bad_changed = changed[changed["applied_fixes"].fillna("").astype(str).str.strip() == ""]
    assert bad_changed.empty, (
        f"changed rows with empty applied_fixes:\n{bad_changed[['block_id','label']].to_string()}"
    )

    review = df[df["manual_review_required"].astype(str).str.lower() == "true"]
    bad_review = review[review["explanation"].fillna("").astype(str).str.strip() == ""]
    assert bad_review.empty, (
        f"manual_review rows with empty explanation:\n{bad_review[['block_id','label']].to_string()}"
    )

    low_conf = df[df["low_confidence"].astype(str).str.lower() == "true"]
    not_routed = low_conf[low_conf["manual_review_required"].astype(str).str.lower() != "true"]
    assert not_routed.empty, (
        f"low_confidence rows not routed to manual review:\n{not_routed[['block_id','label']].to_string()}"
    )
