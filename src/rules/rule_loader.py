from __future__ import annotations

import json
from pathlib import Path
from typing import Any


RULES_PATH = Path(__file__).resolve().parent / "formatting_rules_v1.json"
REQUIRED_RULE_KEYS = {
    "id",
    "applicable_labels",
    "parameter",
    "action",
    "severity",
    "autocorrect",
    "priority",
}


def load_rules(path: str | Path | None = None) -> list[dict[str, Any]]:
    rule_path = Path(path) if path is not None else RULES_PATH
    payload = json.loads(rule_path.read_text(encoding="utf-8"))
    rules = payload.get("rules")
    if not isinstance(rules, list):
        raise ValueError(f"Rule file '{rule_path}' must contain a top-level 'rules' list.")

    validated: list[dict[str, Any]] = []
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError("Each rule must be a JSON object.")
        missing = REQUIRED_RULE_KEYS - set(rule)
        if missing:
            raise ValueError(f"Rule '{rule.get('id', '<unknown>')}' is missing keys: {sorted(missing)}")
        if "expected_value" not in rule and "constraint" not in rule:
            raise ValueError(f"Rule '{rule['id']}' must define 'expected_value' or 'constraint'.")
        validated.append(rule)

    return sorted(validated, key=lambda item: int(item["priority"]), reverse=True)
