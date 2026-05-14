# Phase 6: Streamlit UI Redesign — Pattern Map

**Mapped:** 2026-05-14
**Files analyzed:** 5 (2 modified, 1 new module, 2 new test files)
**Analogs found:** 5 / 5

---

## CRITICAL FINDING: report_df schema (verified from real run output)

`blocked_unsafe_autofix` is a **separate boolean column**, NOT a `status` value.
Status column values found in real run: `['review', 'no_change', 'changed']` — no `'error'` or `'blocked_unsafe_autofix'` as status strings.

This means `render_block_section` group logic must be:
- «Требуют внимания»: `status.isin(["review", "error"]) | (blocked_unsafe_autofix == True)`
- «Изменены»: `status == "changed"` and `blocked_unsafe_autofix == False`
- «Без изменений»: `status == "no_change"`

Full column list (from `results/reports/*.csv`):
`block_id, kind, label, status, action, profile_id, profile_name, confidence_score, low_confidence, manual_review_required, blocked_unsafe_autofix, unsafe_auto_fix_reason, violated_rules, suggested_rule_ids, applied_fixes, suggested_fix, changed_fields, uncertain_fields, reason, explanation, recommendation, text`

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `app.py` (modified) | component (Streamlit app) | request-response + event-driven | `app.py` itself (evolve in-place) | self |
| `src/inference/run_log.py` (new) | utility / logger | transform (in-memory list → JSON file) | `src/inference/application_service.py` `_save_run_sidecars` | role-match |
| `tests/test_run_log.py` (new) | test | unit | `tests/test_application_service.py` | role-match |
| `tests/test_render_block_section.py` (new) | test | unit | `tests/test_app_upload_contract.py` | role-match |
| `tests/test_preflight.py` (new) | test | unit | `tests/test_methodical_extractor.py` | partial |

---

## Pattern Assignments

### `app.py` — `render_report` + `render_block_section` (replaces `render_results`)

**Analog:** `app.py` `render_results` (lines 526–748)

**Imports pattern** (lines 1–17, keep verbatim):
```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.inference.application_service import (
    ProcessingArtifacts,
    get_profile_options,
    list_model_options,
    process_document,
    save_uploaded_bytes,
)
from src.rules.methodical_extractor import build_methodical_profile, extract_text_from_file, save_methodical_profile
```

Add to imports for Phase 6:
```python
from src.inference.run_log import RunLog
from src.rules.profile_diff import compute_profile_diff
from src.rules.profile_loader import load_profile
```

**Page config + constants** (lines 19–23, keep verbatim):
```python
SUPPORTED_UPLOAD_TYPES = ["docx"]
SUPPORTED_METHODICAL_UPLOAD_TYPES = ["pdf", "docx", "txt", "md"]
CUSTOM_PROFILES_DIR = Path("results/generated_profiles")

st.set_page_config(page_title="ГОСТ Formatter", page_icon="📄", layout="wide")
```

**`inject_page_styles` — keep verbatim** (lines 26–155). Badge CSS classes that render_block_section uses:
```python
# lines 97–102 — status chip classes (KEEP, referenced by render_block_section)
.badge-neutral { background: #eef2ff; color: #243447; }
.badge-ok      { background: #dff7ea; color: #166534; }
.badge-warn    { background: #fff3db; color: #8a5a00; }
.badge-change  { background: #fff1dd; color: #9a4d00; }
.badge-error   { background: #fde7ef; color: #9f1239; }
.badge-muted   { background: #ede9fe; color: #5b21b6; }
```

**`normalize_table_values` — keep verbatim** (lines 208–215):
```python
def normalize_table_values(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    normalized = df.copy()
    for column in normalized.columns:
        normalized[column] = normalized[column].fillna("")
    return normalized
```

**`format_profile_option` / `build_profile_options` — keep verbatim** (lines 218–236):
```python
def format_profile_option(item: dict[str, str]) -> str:
    profile_name = item.get("profile_name", "Профиль")
    profile_id = item.get("profile_id", "unknown")
    profile_type = item.get("profile_type", "unknown")
    source_type = item.get("source_type", "unknown")
    return f"{profile_name} [{profile_id}] · {profile_type} · {source_type}"
```

**`render_artifact_download_card` — keep verbatim** (lines 458–478):
```python
def render_artifact_download_card(title: str, description: str, path: Path, mime: str, key: str) -> None:
    st.markdown(f'<div class="artifact-card"><h4>{title}</h4><p>{description}</p></div>',
                unsafe_allow_html=True)
    with open(path, "rb") as artifact_file:
        st.download_button(
            f"Скачать {path.name}",
            data=artifact_file.read(),
            file_name=path.name,
            mime=mime,
            use_container_width=True,
            key=key,
        )
    st.caption(str(path))
```

**`run_processing` — modify in-place** (lines 750–778). Core try/except pattern to copy:
```python
def run_processing(uploaded_file, selected_model_key: str, selected_mode: str, selected_profile_path: str) -> None:
    if uploaded_file is None:
        st.warning("Сначала загрузите DOCX-документ.")
        return
    if selected_model_key == "baseline_unavailable":
        st.error("Baseline-модель недоступна: в workspace нет сохраненного .joblib-артефакта.")
        return

    input_path = save_uploaded_bytes(uploaded_file.getvalue(), suffix=Path(uploaded_file.name).suffix)
    # PHASE 6 ADD: run_log = RunLog(uploaded_file.name)
    try:
        result = process_document(...)
    except NotImplementedError as exc:
        st.error(str(exc))   # keep for NotImplementedError (no PII risk)
        return
    except Exception as exc:
        st.exception(exc)    # PHASE 6: REPLACE with st.error("Не удалось обработать документ: " + type(exc).__name__)
        return

    st.session_state["last_result"] = result
    st.session_state["last_uploaded_name"] = uploaded_file.name
    # PHASE 6 ADD: st.session_state["last_run_log"] = run_log
```

**`main()` sidebar pattern** (lines 800–1194). Session state defaults pattern to copy:
```python
# lines 790–795
st.session_state.setdefault("custom_profile_items", [])
# ... etc
all_profile_items = build_profile_options(profile_items, custom_profile_items)
profile_label_to_path = {format_profile_option(item): item["path"] for item in all_profile_items}
```

Sidebar structure pattern (lines 800–1194) — the new sidebar is a slimmed version of this block. Key patterns to copy:
```python
with st.sidebar:
    st.header("Панель управления")
    # ... profile selectbox with key="profile_selectbox"
    selected_profile_label = st.selectbox(
        "Профиль ГОСТ",
        options=list(profile_label_to_path.keys()),
        key="profile_selectbox",   # modal close writes to this key
    )
    process_clicked = st.button("Запустить аудит", type="primary", use_container_width=True)
```

**STATUS_CHIP dict for render_block_section — new constant:**
```python
# NOTE: blocked_unsafe_autofix is a boolean column, not a status value.
# The "blocked_unsafe_autofix" key here is used for display only when the boolean is True.
STATUS_CHIP: dict[str, tuple[str, str, str]] = {
    "no_change":              ("●",  "Без изменений",                             "badge-ok"),
    "changed":                ("✏️", "Изменено",                                   "badge-change"),
    "review":                 ("⚠️", "Требует проверки",                           "badge-warn"),
    "error":                  ("✗",  "Ошибка",                                     "badge-error"),
    "blocked_unsafe_autofix": ("🛑", "Небезопасное автоисправление заблокировано", "badge-muted"),
}
```

**render_block_section group-split logic (critical — informed by real column schema):**
```python
# Split report_df into three groups — blocked_unsafe_autofix is boolean, not status
df_attention = report_df[
    report_df["status"].isin(["review", "error"])
    | (report_df.get("blocked_unsafe_autofix", False) == True)
]
df_changed = report_df[
    (report_df["status"] == "changed")
    & ~(report_df.get("blocked_unsafe_autofix", False) == True)
]
df_ok = report_df[report_df["status"] == "no_change"]
```

---

### `src/inference/run_log.py` (new utility module)

**Analog:** `src/inference/application_service.py` `_save_run_sidecars` (lines 109–129)

**Analog pattern** — `_save_run_sidecars` shows the exact write pattern (json.dumps, ensure_ascii=False, indent=2, write_text with utf-8 encoding):
```python
# application_service.py lines 119–124
report_json.write_text(
    report_df.to_json(orient="records", force_ascii=False, indent=2),
    encoding="utf-8",
)
summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
```

**Analog pattern** — `_timestamp()` (lines 86–87) shows the UTC-free datetime approach already in use:
```python
def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
```
Phase 6 `RunLog` uses `datetime.now(timezone.utc).isoformat()` instead (ISO-8601 UTC, stricter).

**Imports pattern** for `run_log.py`:
```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
```

**Core class pattern** (from RESEARCH.md §3 Pattern 3, fully specified):
```python
class RunLog:
    def __init__(self, input_filename: str) -> None:
        self._filename = Path(input_filename).name   # basename only — PII boundary
        self._records: list[dict[str, Any]] = []

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
        path.write_text(
            json.dumps(self._records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
```

**PII boundary rules (from RESEARCH.md §5):**
- `stage`: one of `"document-read"`, `"classification"`, `"rule-apply"`, `"save"`
- `error_class`: `type(exc).__name__` only — never `repr(exc)` or `str(exc)`
- `error_message`: fixed Russian user-message string — never `str(exc)` when exc may carry doc text
- `**extras`: only `block_id` (int) and `profile_id` (str) allowed — never raw text fields

---

### `tests/test_run_log.py` (new test file)

**Analog:** `tests/test_application_service.py` (lines 1–31)

**Imports + style pattern** (copy from `test_application_service.py` lines 1–4):
```python
from __future__ import annotations

from pathlib import Path
import json

from src.inference.run_log import RunLog
```

**Test structure pattern** — `tmp_path` fixture, no monkeypatch needed for unit tests on pure classes:
```python
def test_run_log_records_do_not_contain_text_content(tmp_path) -> None:
    log = RunLog("my_doc.docx")
    log.record("rule-apply", "error",
               error_class="KeyError",
               error_message="Блок не удалось проверить из-за внутренней ошибки правила.",
               block_id=42)
    out = tmp_path / "run.json"
    log.dump_json(out)
    content = out.read_text(encoding="utf-8")
    assert "Traceback" not in content
    records = json.loads(content)
    for rec in records:
        assert "text" not in rec
        assert "traceback" not in rec
```

**Monkeypatch pattern** (from `test_application_service.py` lines 6–11) — copy for tests that need to mock module-level functions:
```python
def test_something(monkeypatch) -> None:
    monkeypatch.setattr(module_under_test, "function_name", lambda: ...)
```

---

### `tests/test_render_block_section.py` (new test file)

**Analog:** `tests/test_app_upload_contract.py` (lines 1–11) — module-level constant contract tests

**Import pattern** (copy from `test_app_upload_contract.py`):
```python
from __future__ import annotations

import app
```

**Contract test pattern** — pure module attribute assertions, no Streamlit machinery needed:
```python
def test_streamlit_upload_contract_is_docx_only() -> None:
    assert app.SUPPORTED_UPLOAD_TYPES == ["docx"]
```

**Pure-function unit test pattern** for `render_block_section` helpers. Since `render_block_section` calls `st.*` directly, tests targeting it must extract pure predicates:
```python
# Extract pure helper from app.py (or test via module-level callable)
def test_status_chip_covers_all_five_statuses() -> None:
    from app import STATUS_CHIP
    for status in ["no_change", "changed", "review", "error", "blocked_unsafe_autofix"]:
        assert status in STATUS_CHIP

def test_modal_reason_is_valid_rejects_short_reason() -> None:
    # modal_reason_is_valid is a pure predicate extracted into app.py
    from app import modal_reason_is_valid
    assert modal_reason_is_valid("") is False
    assert modal_reason_is_valid("abcdefg") is False      # 7 chars
    assert modal_reason_is_valid("abcdefgh") is True      # 8 chars
    assert modal_reason_is_valid("   ") is False          # whitespace-only
```

**Note:** `modal_reason_is_valid(reason: str) -> bool` should be extracted as a one-liner in `app.py`:
```python
def modal_reason_is_valid(reason: str) -> bool:
    return len(reason.strip()) >= 8
```
This makes it testable without invoking Streamlit.

---

### `tests/test_preflight.py` (new test file)

**Analog:** `tests/test_methodical_extractor.py` (lines 1–59) — uses `tmp_path`, writes fixture files, calls the function under test directly

**Import + fixture pattern** (copy from `test_methodical_extractor.py` lines 1–6):
```python
from __future__ import annotations

import json
from pathlib import Path

import pytest
```

**Fixture file creation pattern** (from `test_methodical_extractor.py` lines 10–26):
```python
def test_preflight_rejects_unreadable_file(tmp_path) -> None:
    bad_file = tmp_path / "not_a_docx.docx"
    bad_file.write_bytes(b"this is not a zip")
    # call preflight_check(bad_file) and assert it returns/raises the typed error
```

**`pytest.raises` pattern** — follow existing project tests:
```python
with pytest.raises(ValueError, match="..."):
    some_function(bad_input)
```

---

## Shared Patterns

### Session State Initialization
**Source:** `app.py` `main()` lines 790–795
**Apply to:** `main()` rewrite in `app.py`
```python
st.session_state.setdefault("custom_profile_items", [])
st.session_state.setdefault("methodical_profile_draft", None)
# Phase 6 adds:
st.session_state.setdefault("last_run_log", None)
st.session_state.setdefault("modal_diff_lines", None)
st.session_state.setdefault("modal_draft_profile", None)
```

### Profile Options Build Pattern
**Source:** `app.py` lines 795–796 (keep verbatim)
**Apply to:** new `main()` sidebar block
```python
all_profile_items = build_profile_options(profile_items, custom_profile_items)
profile_label_to_path = {format_profile_option(item): item["path"] for item in all_profile_items}
```

### Error Surfacing Pattern (D-04)
**Source:** `app.py` `run_processing` lines 769–773 (current — to be modified)
**Apply to:** `run_processing` (modified), `methodical_modal` function
```python
# CURRENT (line 773) — DO NOT COPY, this is the anti-pattern:
#   st.exception(exc)
# PHASE 6 REPLACEMENT:
st.error("Не удалось обработать документ: " + type(exc).__name__)
run_log.record("rule-apply", "error",
               error_class=type(exc).__name__,
               error_message="Не удалось обработать документ.")
```

### Download Button Pattern
**Source:** `app.py` `render_artifact_download_card` lines 458–478 (keep verbatim)
**Apply to:** `render_report` downloads section + run-log download button
```python
st.download_button(
    "Скачать журнал запуска (JSON)",
    data=log_bytes,
    file_name=log_filename,
    mime="application/json",
    use_container_width=True,
    key="download_run_log",
)
```

### `st.dialog` Modal + `st.rerun()` Close Pattern
**Source:** RESEARCH.md §1 Pattern 1 (verified against dialog_decorator.py)
**Apply to:** `methodical_modal` function in `app.py`
```python
@st.dialog("Создать профиль из методички", width="large")
def methodical_modal(available_profile_ids: list[str]) -> None:
    # ... modal body ...
    if st.button("Применить и сохранить", type="primary"):
        save_methodical_profile(draft, CUSTOM_PROFILES_DIR)
        st.session_state["profile_selectbox"] = profile_id
        for k in ("modal_diff_lines", "modal_draft_profile"):
            st.session_state.pop(k, None)
        st.rerun()   # closes dialog on next script run
```

### `st.metric` Summary Counters Pattern
**Source:** RESEARCH.md §4 (Streamlit-native)
**Apply to:** `render_report` summary section
```python
c = st.columns(6)
metrics = [
    ("Всего блоков",               summary.get("blocks_total", 0)),
    ("Без изменений",              summary.get("no_change", 0)),
    ("Изменены",                   summary.get("changed", 0)),
    ("Требуют проверки",           summary.get("review", 0)),
    ("Ошибки",                     summary.get("error", 0)),
    ("Небезопасно (заблокировано)", summary.get("blocked_unsafe_autofix", 0)),
]
for col, (label, value) in zip(c, metrics):
    col.metric(label, int(value))
```

### JSON Write Pattern (UTF-8, no ASCII escape)
**Source:** `src/inference/application_service.py` `_save_run_sidecars` lines 122–127
**Apply to:** `RunLog.dump_json`
```python
path.write_text(
    json.dumps(self._records, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
```

### `cmd_extract_methodical_profile` Reference (D-004 contract)
**Source:** `src/main.py` lines 295–374
**Apply to:** `methodical_modal` apply branch
Key logic to mirror:
- `len(stripped) < 8 or not printable_non_ws` → reject (line 369)
- `draft["extraction_meta"]["override_reason"] = reason.strip()` before save
- `save_methodical_profile(profile, target_dir)` (not `save_methodical_profile(profile, output_dir=target_dir)`)

---

## No Analog Found

All files have close matches. No gaps.

---

## Deleted Code (orphans from executor's changes)

Per CLAUDE.md «Удаляй orphans, появившиеся из-за твоих изменений»:

| Function | Lines | Why orphaned |
|---|---|---|
| `render_hero` | 158–175 | Replaced by report header block in `render_report` |
| `build_methodical_profile_draft` | 239–249 | Replaced by direct call to `build_methodical_profile` in modal |
| `persist_custom_profile` | 252–261 | Replaced by direct call to `save_methodical_profile` in modal |
| `_set_session_methodical_draft` | 264–267 | Modal uses `modal_*` session keys directly |
| `_get_session_methodical_draft` | 270–272 | Modal uses `modal_*` session keys directly |
| `_apply_methodical_form_edits` | 275–386 | Old form editor removed; modal takes its place |
| `filter_audit_df` | 389–425 | No tab-level filter widgets in new flow |
| `filter_predictions_df` | 428–455 | Predictions tab dropped |
| `render_manual_decision_table` | 481–523 | No manual decision table in new flow |
| `render_results` (body) | 526–748 | Replaced by `render_report` |
| Old `main()` sidebar methodical form | ~803–1171 | Replaced by `methodical_modal` |

`render_metric_card` and `render_status_badges` (lines 178–205) are retired from the primary flow but CLAUDE.md says «не рефактори то, что работает» — leave callable for legacy compat; executor may leave or remove them at discretion.

---

## Metadata

**Analog search scope:** `app.py`, `src/inference/application_service.py`, `src/main.py`, `tests/test_app_upload_contract.py`, `tests/test_application_service.py`, `tests/test_methodical_extractor.py`, `tests/test_profile_diff.py`
**Files scanned:** 7
**report_df column schema:** verified from `results/reports/*.csv` (real run output, 2026-05-11)
**Pattern extraction date:** 2026-05-14
