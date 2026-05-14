"""Wave 0 RED tests for src.inference.run_log.RunLog.

These tests were declared in 06-00-PLAN.md and are required as a dependency by
06-01-PLAN.md. Prior to implementation they fail with ModuleNotFoundError; after
06-01 lands they all pass (GREEN).

PII boundary contract (06-RESEARCH.md §5, 06-UI-SPEC.md §"Run-log JSON contract"):
    IN  : stage, ts (ISO-8601 UTC), status, error_class, error_message,
          plus whitelisted extras (block_id, profile_id), filename basename only.
    OUT : raw document text, paragraph/block_content, traceback strings,
          absolute path components.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.inference.run_log import RunLog


def test_run_log_record_has_required_keys(tmp_path: Path) -> None:
    log = RunLog("doc.docx")
    log.record("document-read", "ok")
    out = tmp_path / "run.json"
    log.dump_json(out)

    records = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(records, list)
    assert len(records) == 1
    rec = records[0]
    assert set(rec.keys()) == {"stage", "ts", "status", "error_class", "error_message"}
    assert rec["stage"] == "document-read"
    assert rec["status"] == "ok"
    assert rec["error_class"] is None
    assert rec["error_message"] is None


def test_run_log_record_appends_optional_extras(tmp_path: Path) -> None:
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
    rec = records[0]
    assert rec["error_class"] == "KeyError"
    assert rec["error_message"] == "Блок не удалось проверить из-за внутренней ошибки правила."
    assert rec["block_id"] == 42
    assert rec["profile_id"] == "gost_7_32_2017"


def test_run_log_records_do_not_contain_text_content(tmp_path: Path) -> None:
    log = RunLog("doc.docx")
    log.record("document-read", "ok")
    log.record(
        "classification",
        "ok",
        block_id=1,
        profile_id="gost_7_32_2017",
    )
    log.record(
        "rule-apply",
        "error",
        error_class="KeyError",
        error_message="Блок не удалось проверить из-за внутренней ошибки правила.",
        block_id=2,
    )
    log.record("save", "ok")
    out = tmp_path / "run.json"
    log.dump_json(out)

    content = out.read_text(encoding="utf-8")
    assert "Traceback" not in content

    records = json.loads(content)
    for rec in records:
        assert "text" not in rec
        assert "paragraph" not in rec
        assert "block_content" not in rec
        assert "traceback" not in rec


def test_run_log_filename_is_basename_only(tmp_path: Path) -> None:
    log = RunLog("/Users/secret/Documents/doc.docx")
    log.record("document-read", "ok")
    out = tmp_path / "run.json"
    log.dump_json(out)

    content = out.read_text(encoding="utf-8")
    assert "/Users/" not in content
    assert "secret" not in content


def test_run_log_dump_json_is_valid_json_array_with_indent_2(tmp_path: Path) -> None:
    log = RunLog("doc.docx")
    log.record("document-read", "ok")
    log.record("save", "ok")
    out = tmp_path / "run.json"
    log.dump_json(out)

    content = out.read_text(encoding="utf-8")
    assert content.startswith("[")
    assert content.rstrip().endswith("]")

    parsed = json.loads(content)
    assert isinstance(parsed, list)
    # indent=2 produces lines like "\n  {" right after "[".
    assert "\n  {" in content


def test_run_log_ts_is_iso_8601_utc(tmp_path: Path) -> None:
    log = RunLog("doc.docx")
    log.record("document-read", "ok")
    out = tmp_path / "run.json"
    log.dump_json(out)

    records = json.loads(out.read_text(encoding="utf-8"))
    ts = records[0]["ts"]
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?\+00:00$"
    assert re.match(pattern, ts), f"ts {ts!r} not ISO-8601 UTC"


def test_run_log_stage_is_enum_member(tmp_path: Path) -> None:
    """record() does NOT validate stage values — pass-through per 06-UI-SPEC.

    Enum enforcement lives at the call site (app.py / pipeline stages).
    """
    log = RunLog("doc.docx")
    log.record("not-a-real-stage", "ok")
    out = tmp_path / "run.json"
    log.dump_json(out)

    records = json.loads(out.read_text(encoding="utf-8"))
    assert records[0]["stage"] == "not-a-real-stage"
