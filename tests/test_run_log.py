# Phase 6 Wave 0 RED stubs for src/inference/run_log.py (which does not yet exist).
#
# Module-level `from src.inference.run_log import RunLog` is the deliberate RED
# signal: collection fails with ModuleNotFoundError until Wave 1 lands the module.
# Once Wave 1 ships, every test below must turn GREEN with no further changes
# unless the run-log JSON contract changes (UI-SPEC §Run-log JSON contract).
#
# Coverage matches plan §Task 2 behavior list:
#   1. record() emits {stage, ts, status, error_class, error_message}
#   2. record(**extras) preserves block_id + profile_id
#   3. PII boundary — no `text`, `paragraph`, `block_content`, `traceback`,
#      `Traceback` substrings in any record after dump_json
#   4. RunLog(input_filename) keeps basename only (no full path / no username)
#   5. dump_json output is a valid JSON array, indent=2
#   6. ts is ISO-8601 UTC with explicit `+00:00`
#   7. record() is a pass-through for stage values (enum enforcement at caller)

from __future__ import annotations

import json
import re
from pathlib import Path

from src.inference.run_log import RunLog


def test_run_log_record_has_required_keys(tmp_path) -> None:
    log = RunLog("doc.docx")
    log.record("document-read", "ok")
    out = tmp_path / "run.json"
    log.dump_json(out)

    records = json.loads(out.read_text(encoding="utf-8"))
    assert len(records) == 1
    rec = records[0]
    assert set(rec.keys()) == {"stage", "ts", "status", "error_class", "error_message"}
    assert rec["stage"] == "document-read"
    assert rec["status"] == "ok"
    assert rec["error_class"] is None
    assert rec["error_message"] is None


def test_run_log_record_appends_optional_extras(tmp_path) -> None:
    log = RunLog("doc.docx")
    log.record(
        "rule-apply",
        "error",
        error_class="KeyError",
        error_message="Блок не удалось проверить из-за внутренней ошибки правила.",
        block_id=42,
        profile_id="gost_7_32_2017",
    )
    out = tmp_path / "run.json"
    log.dump_json(out)

    records = json.loads(out.read_text(encoding="utf-8"))
    assert len(records) == 1
    rec = records[0]
    assert rec["block_id"] == 42
    assert rec["profile_id"] == "gost_7_32_2017"
    assert rec["error_class"] == "KeyError"
    assert rec["error_message"] == "Блок не удалось проверить из-за внутренней ошибки правила."


def test_run_log_records_do_not_contain_text_content(tmp_path) -> None:
    log = RunLog("doc.docx")
    log.record("document-read", "ok")
    log.record(
        "classification",
        "ok",
        block_id=10,
    )
    log.record(
        "rule-apply",
        "error",
        error_class="ValueError",
        error_message="Блок не удалось проверить из-за внутренней ошибки правила.",
        block_id=42,
    )
    log.record("save", "ok")

    out = tmp_path / "run.json"
    log.dump_json(out)
    content = out.read_text(encoding="utf-8")

    # Substring-level PII boundary
    assert "Traceback" not in content
    assert "traceback" not in content

    # Field-level PII boundary
    records = json.loads(content)
    forbidden_keys = {"text", "paragraph", "block_content", "traceback"}
    for rec in records:
        for key in forbidden_keys:
            assert key not in rec, f"forbidden PII key {key!r} present in record {rec}"


def test_run_log_filename_is_basename_only(tmp_path) -> None:
    log = RunLog("/Users/secret/Documents/doc.docx")
    log.record("document-read", "ok")
    out = tmp_path / "run.json"
    log.dump_json(out)

    content = out.read_text(encoding="utf-8")
    assert "/Users/" not in content
    assert "secret" not in content


def test_run_log_dump_json_is_valid_json_array_with_indent_2(tmp_path) -> None:
    log = RunLog("doc.docx")
    log.record("document-read", "ok")
    log.record("classification", "ok")

    out = tmp_path / "run.json"
    log.dump_json(out)

    content = out.read_text(encoding="utf-8")
    assert content.startswith("[")
    assert content.rstrip().endswith("]")

    parsed = json.loads(content)
    assert isinstance(parsed, list)
    # indent=2 — first record opens with newline + two spaces
    assert "[\n  {" in content


def test_run_log_ts_is_iso_8601_utc(tmp_path) -> None:
    log = RunLog("doc.docx")
    log.record("document-read", "ok")
    out = tmp_path / "run.json"
    log.dump_json(out)

    rec = json.loads(out.read_text(encoding="utf-8"))[0]
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?\+00:00$"
    assert re.match(pattern, rec["ts"]), f"ts {rec['ts']!r} is not ISO-8601 UTC with +00:00"


def test_run_log_stage_is_enum_member(tmp_path) -> None:
    """RunLog.record is a pass-through for stage; enum enforcement lives at the
    caller per UI-SPEC §"PII boundary" field row.
    """
    log = RunLog("doc.docx")
    # A non-enum stage value should be recorded verbatim — RunLog itself does
    # not validate the enum (the caller is responsible).
    log.record("not-a-real-stage", "ok")
    out = tmp_path / "run.json"
    log.dump_json(out)
    rec = json.loads(out.read_text(encoding="utf-8"))[0]
    assert rec["stage"] == "not-a-real-stage"
