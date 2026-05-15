---
phase: 06-streamlit-ui-redesign
plan: 01
status: complete
commits:
  - 89fcc38 test(06-01): add failing tests for RunLog (Wave 0 dependency)
  - 8577ef6 feat(06-01): implement RunLog single-writer PII-clean stage logger
key-files:
  created:
    - src/inference/run_log.py
tests:
  green: 7
  red: 0
---

# 06-01 SUMMARY — RunLog single-writer module

## What was built

`src/inference/run_log.py` (65 LoC) — a pure-stdlib `RunLog` class implementing
the Phase 6 D-04 PII-clean stage logger.

**Public surface (per 06-PATTERNS.md scaffold):**
- `RunLog(input_filename: str)` — stores `Path(input_filename).name` (basename only).
- `record(stage, status, error_class=None, error_message=None, **extras)` — appends a
  dict with the fixed 5 mandatory keys plus passthrough extras (e.g. `block_id`,
  `profile_id`).
- `dump_json(path: Path)` — writes a JSON array, `ensure_ascii=False`, `indent=2`,
  UTF-8.
- `filename` property — exposes the basename.

**Imports:** `json`, `datetime`, `pathlib.Path`, `typing.Any`. No Streamlit / pandas
/ docx — testable in isolation.

## Verification

- `python3 -m pytest tests/test_run_log.py -q` → `7 passed in 0.07s` (all Wave 0
  RED tests are now GREEN).
- All acceptance grep checks from 06-01-PLAN.md pass:
  - `from datetime import datetime, timezone` ✓
  - `datetime.now(timezone.utc).isoformat()` ✓
  - `ensure_ascii=False, indent=2` ✓
  - `Path(input_filename).name` ✓
  - `wc -l = 65` (50–100 range) ✓
  - No `import streamlit` / `import pandas` ✓
- Broader test suite spot-check (excluding env-pinned modules):
  `156 passed, 9 skipped` — no regressions.

## Deviations from 06-PATTERNS.md scaffold

None. Implemented verbatim.

## Threat model

T-6-01 (PII leak via run-log) mitigations in place:
1. Constructor strips path → basename only.
2. `record()` writes the fixed 5-key schema; `**extras` is a documented passthrough.
3. Wave 0 test `test_run_log_records_do_not_contain_text_content` asserts the
   boundary at the JSON-output layer for the real Phase 6 callers.

T-6-01-A (callers passing forbidden extras) accepted as documented; module does
not actively reject — callers in 06-02/06-04 are constrained by 06-UI-SPEC.

## Note for 06-02 executor

Import:
```python
from src.inference.run_log import RunLog
```

Per audit run:
```python
log = RunLog(uploaded_file.name)
try:
    ...
    log.record("document-read", "ok")
except Exception as exc:
    log.record(
        "document-read",
        "error",
        error_class=type(exc).__name__,
        error_message="…fixed Russian/literal string…",
    )
```

CRITICAL: never pass `error_message=str(exc)` (PII leak risk per
06-RESEARCH.md §5).
