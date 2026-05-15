"""PII-clean single-writer stage logger for Phase 6 audit runs.

D-04 contract: filename + technical metadata IN; document content OUT.
See `.planning/phases/06-streamlit-ui-redesign/06-UI-SPEC.md` §"Run-log JSON
contract" for the field allow/forbid table.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RunLog:
    """Single-writer stage log. One instance per audit run.

    Records have exactly these top-level keys:
        stage:         one of "document-read", "classification", "rule-apply", "save"
        ts:            ISO-8601 UTC timestamp (always +00:00 suffix)
        status:        one of "ok", "partial", "error"
        error_class:   bare exception class name (e.g. "KeyError") or None
        error_message: short user-facing or technical-class-name string;
                       NEVER str(exc) when exc may contain document text
    Plus optional whitelisted extras: block_id (int), profile_id (str).

    Callers MUST NOT pass `text`, `paragraph`, `block_content`, or `traceback`
    as extras. The class does not actively reject these keys — the boundary
    is enforced at the call site (see app.py run_processing / methodical_modal).
    """

    def __init__(self, input_filename: str) -> None:
        # Basename only — strips any path PII.
        self._filename = Path(input_filename).name
        self._records: list[dict[str, Any]] = []

    @property
    def filename(self) -> str:
        return self._filename

    def record(
        self,
        stage: str,
        status: str,
        error_class: str | None = None,
        error_message: str | None = None,
        **extras: Any,
    ) -> None:
        entry: dict[str, Any] = {
            "stage": stage,
            "ts": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "error_class": error_class,
            "error_message": error_message,
        }
        entry.update(extras)
        self._records.append(entry)

    def dump_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
