---
phase: 06-streamlit-ui-redesign
reviewed: 2026-05-14T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - src/inference/run_log.py
  - app.py
  - tests/conftest.py
  - tests/test_app_ui.py
  - tests/test_run_log.py
  - tests/test_render_block_section.py
  - tests/test_preflight.py
findings:
  critical: 2
  warning: 5
  info: 4
  total: 11
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-05-14
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Phase 6 adds the PII-clean `RunLog` (06-01), the Streamlit UI redesign (`STATUS_CHIP`, `preflight_translate_error`, `modal_reason_is_valid`, `render_summary_counters`, `render_block_section`, `render_report`, `methodical_modal`), and Wave-0 RED test scaffolding. The PII boundary in `RunLog` and `run_processing` is broadly intact — no `str(exc)`, `traceback`, or document text leaks to the UI, `st.exception(exc)` is gone, and `preflight_translate_error` returns one of 5 fixed Russian strings as the spec mandates.

Two critical issues block the D-004 mirror and create a Streamlit-runtime hazard:

1. **CR-01** — `modal_reason_is_valid` enforces only `len(strip) >= 8`. The Phase 5 CLI `cmd_extract_methodical_profile` D-004 / T-05-01 contract additionally requires at least one printable non-whitespace non-control character. The modal accepts `"​​​​​​​​" `+ space (zero-width joiners) or 8 control characters as a "reason" — silent rewrite bypass.
2. **CR-02** — `methodical_modal(available_profile_ids)` is invoked from inside `with st.sidebar:` (app.py:617-618). The Phase 6 researcher recorded that `st.sidebar` + `@st.dialog` is incompatible (RESEARCH.md line 307, `dialog_decorator.py:175`). On Streamlit ≥ 1.32 this raises `StreamlitAPIException` or renders the dialog DOM into the sidebar column, breaking the modal entirely.

Warnings cover stage-label misattribution in the catch-all branch, per-render disk write of the run-log JSON (timestamped file per rerun), missing JSON dump for the run-log on the early-return error path, an `IndentationError`-adjacent missing `st.set_page_config` ordering risk (cosmetic), and lack of `extras` key validation in `RunLog.record` despite the docstring promising "boundary is enforced at the call site." Info items track tests-only nits and minor copy drift vs. UI-SPEC.

## Critical Issues

### CR-01: `modal_reason_is_valid` does not mirror Phase 5 T-05-01 contract

**File:** `app.py:41-43`
**Issue:** Phase 5 `cmd_extract_methodical_profile` (`src/main.py:367-374`) requires BOTH `len(stripped) >= 8` AND `any(c.isprintable() and not c.isspace() for c in stripped)`. The Streamlit gate only enforces the length condition. A reason consisting of 8 zero-width spaces (`"​" * 8`), 8 control characters, or 8 non-printable Unicode points after `.strip()` (which only trims standard whitespace) silently passes the UI gate, while the CLI rejects it. This is exactly the "silent rewrite" D-004 forbids and breaks the «UI mirrors CLI» success criterion declared in 06-UI-SPEC §Destructive actions and 06-CONTEXT D-03.
**Fix:**
```python
def modal_reason_is_valid(reason: str) -> bool:
    """D-004 / T-05-01: reason must be >= 8 chars after strip AND contain at
    least one printable non-whitespace character (mirrors src/main.py:367-374).
    """
    stripped = reason.strip()
    if len(stripped) < 8:
        return False
    return any(c.isprintable() and not c.isspace() for c in stripped)
```
Add a matching RED test in `tests/test_render_block_section.py`:
```python
def test_modal_reason_is_valid_rejects_printable_whitespace_only() -> None:
    from app import modal_reason_is_valid
    assert modal_reason_is_valid("​" * 10) is False  # zero-width joiners
    assert modal_reason_is_valid("\x01\x02\x03\x04\x05\x06\x07\x08") is False
```

### CR-02: `methodical_modal` invoked from inside `with st.sidebar:` violates `st.dialog` constraint

**File:** `app.py:604-618`
**Issue:** `methodical_modal(...)` is decorated with `@st.dialog(...)` and called at line 618, which is nested inside the `with st.sidebar:` context manager opened at line 604. Per the Phase 6 researcher (`06-RESEARCH.md:307`, verified directly against `dialog_decorator.py:175`): «`st.sidebar` inside `@st.dialog`: Will raise at runtime». The same incompatibility applies in the inverse direction — calling a `@st.dialog`-decorated function while the sidebar `DeltaGenerator` is the active container puts the dialog widgets into the sidebar render tree rather than the page overlay. On Streamlit 1.56 (pinned) this either raises `StreamlitAPIException` or silently renders the modal contents inline in the sidebar, making the «+ Создать профиль из методички» button non-functional.
**Fix:** Move the modal invocation OUT of the `with st.sidebar:` block. Capture the button click inside the sidebar, dispatch the modal in the main script context:
```python
with st.sidebar:
    ...
    open_modal_clicked = st.button(
        "+ Создать профиль из методички",
        key="open_methodical_modal",
        use_container_width=True,
    )
    # ... rest of sidebar widgets ...

# Dispatch dialog OUTSIDE the sidebar context manager:
if open_modal_clicked:
    methodical_modal(available_profile_ids)
```
Add an AppTest regression: click `open_methodical_modal`, assert `not at.exception`.

## Warnings

### WR-01: Catch-all branch hard-codes `stage="rule-apply"` regardless of failure stage

**File:** `app.py:419-429`
**Issue:** When `process_document` raises a non-translated `Exception`, `run_processing` records `stage="rule-apply"` unconditionally. But `process_document` covers all 4 pipeline stages (document-read → classification → rule-apply → save). A `save`-stage failure (e.g. permission denied writing the corrected DOCX) is logged as a `rule-apply` error, misleading the audit log and contradicting the UI-SPEC §Run-log JSON contract enum invariant.
**Fix:** Either record stage as `"unknown"` or, preferably, propagate stage from `process_document` by raising a typed wrapper (`StageError(stage, original_exc)`) at each stage boundary, then unpack `exc.stage` in the catch-all:
```python
except Exception as exc:
    stage = getattr(exc, "stage", "rule-apply")
    run_log.record(
        stage,
        "error",
        error_class=type(exc).__name__,
        error_message="Не удалось обработать документ.",
    )
```
If wrapping is out of scope for Phase 6 GREEN, at minimum change the literal to a non-misleading sentinel that documents the limitation.

### WR-02: `render_report` writes a new run-log JSON to disk on every Streamlit rerun

**File:** `app.py:364-378`
**Issue:** Every time the script reruns while `last_result` is in session_state (e.g. user toggles an expander, hovers a metric, changes any unrelated widget), `render_report` recomputes `timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")` and calls `run_log.dump_json(log_path)` to a NEW file in `results/reports/`. After 30 seconds of UI interaction the directory accumulates a per-second snapshot of the same run-log content. This violates UI-06 «artifact filenames are stable per audit run», pollutes the reports directory, and risks I/O errors filling the disk during long sessions.
**Fix:** Compute the log path once when the run completes and cache it in session_state. Read from disk for the download:
```python
# In run_processing, AFTER successful processing:
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
stem = Path(input_path).stem
log_path = REPORTS_DIR / f"{stem}_run_log_{timestamp}.json"
run_log.dump_json(log_path)
st.session_state["last_run_log_path"] = log_path

# In render_report:
log_path: Path | None = st.session_state.get("last_run_log_path")
if log_path is not None and log_path.exists():
    st.download_button(
        "Скачать журнал запуска (JSON)",
        data=log_path.read_bytes(),
        ...
    )
```

### WR-03: Run-log is never dumped to disk on the early-return error path

**File:** `app.py:407-429`, `app.py:364-378`
**Issue:** When `run_processing` catches a preflight/translated error or a generic exception, it stores `run_log` in `st.session_state["last_run_log"]` and returns early. `last_result` stays `None`. `render_report` never runs, so `run_log.dump_json(...)` is never called — the user sees the Russian error but has NO way to download the run-log JSON that contains the `error_class` they need to file a bug. This breaks D-04 «journal запуска is downloadable per audit run, including failed runs».
**Fix:** Dump the run-log JSON unconditionally inside `run_processing` (success and failure paths), and render the download button from the main pane whenever `last_run_log_path` is in session_state, not only inside `render_report`:
```python
def _persist_run_log(run_log: RunLog, input_filename: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(input_filename).stem
    log_path = REPORTS_DIR / f"{stem}_run_log_{timestamp}.json"
    run_log.dump_json(log_path)
    return log_path

# In all three exit paths of run_processing:
st.session_state["last_run_log_path"] = _persist_run_log(run_log, uploaded_file.name)
```
Then move the run-log download button to a top-level `main()` block so it appears even when `last_result is None`.

### WR-04: `RunLog.record(**extras)` accepts forbidden PII keys silently

**File:** `src/inference/run_log.py:42-58`
**Issue:** The class docstring promises «Callers MUST NOT pass `text`, `paragraph`, `block_content`, or `traceback` as extras. The class does not actively reject these keys — the boundary is enforced at the call site». But `tests/test_run_log.py:91-95` enforces the boundary at field-level — meaning the contract is observable from outside the class. Relying on "every caller remembers" is exactly the kind of out-of-band invariant that breaks during refactoring (e.g. a future test helper that copies `predictions_df.iloc[i].to_dict()` into `**extras`). The single-writer module IS the natural enforcement point and the cost is one set membership check.
**Fix:** Reject forbidden keys at the source so the boundary cannot be silently violated:
```python
_FORBIDDEN_EXTRA_KEYS: frozenset[str] = frozenset({
    "text", "paragraph", "block_content", "traceback",
})

def record(
    self,
    stage: str,
    status: str,
    error_class: str | None = None,
    error_message: str | None = None,
    **extras: Any,
) -> None:
    forbidden = _FORBIDDEN_EXTRA_KEYS & extras.keys()
    if forbidden:
        raise ValueError(
            f"RunLog.record forbids PII extras: {sorted(forbidden)} "
            "(D-04 PII boundary: filename + technical metadata IN; document content OUT)."
        )
    entry: dict[str, Any] = {
        "stage": stage,
        ...
    }
```
This converts a silent failure into a loud one and removes the «call site MUST remember» footgun without weakening the existing field-level tests.

### WR-05: `methodical_modal` collision check diverges from CLI by checking both directories

**File:** `app.py:504-508`
**Issue:** The CLI (`src/main.py:334-335, 360`) checks for collisions against `target_dir = output_dir or PROFILES_DIR` — a SINGLE directory. The modal at line 504-508 checks `PROFILES_DIR / {id}.json` AND `CUSTOM_PROFILES_DIR / {id}.json`. This is stricter than the CLI in one direction (a profile_id matching a built-in shipped profile is flagged as a collision even though the modal always writes to `CUSTOM_PROFILES_DIR`), and weaker in another (if Phase 5 CLI was run with `--output-dir results/generated_profiles`, the contract matches; otherwise it does not). This is a contract drift that means a user who can use `--apply` in the CLI cannot use «Применить и сохранить» in the modal for the same `profile_id`, or vice versa.
**Fix:** Match the CLI: check collision against the actual write target only (`CUSTOM_PROFILES_DIR`). If shadowing a built-in profile_id is itself a concern, surface it as a separate warning, not as a force-reason gate:
```python
target_path = CUSTOM_PROFILES_DIR / f"{profile_id}.json"
target_exists = target_path.exists()
shadowing_builtin = (PROFILES_DIR / f"{profile_id}.json").exists()
if shadowing_builtin and not target_exists:
    st.info(f"`{profile_id}` совпадает с именем встроенного профиля — пользовательский профиль скроет встроенный в списке.")
```

## Info

### IN-01: `inject_page_styles()` is called AFTER `st.set_page_config`, but `set_page_config` is at module level

**File:** `app.py:68`, `app.py:587`
**Issue:** `st.set_page_config(...)` runs at import time (module body, line 68). On certain rerun paths (e.g. Streamlit reloads via watcher) this can trigger `StreamlitAPIException("set_page_config must be called as the first Streamlit command")` if any other Streamlit call snuck in earlier. Currently the module-level imports do not call Streamlit, so this is safe today, but it's a fragility — a future top-level `st.cache_data` annotation or similar would break it. Convention is to put `set_page_config` as the first call inside `main()`.
**Fix:** Move line 68 to the top of `main()`, before `inject_page_styles()`.

### IN-02: `conftest.py` references a non-existent file location in the docstring comment

**File:** `tests/test_app_ui.py:9-10`
**Issue:** Comment refers to «the `st.exception(exc)` regression at app.py:773». After the Phase 6 rewrite, `app.py` is 668 lines and contains no `st.exception(exc)` call. The comment is correct historically but misleads future readers into thinking there's a live regression at a line that no longer exists.
**Fix:** Update the comment to «(historical regression — removed in Phase 6 Wave 2)» or drop the line reference.

### IN-03: `render_block_section` rejects `confidence == 0.0` via `_has` check

**File:** `app.py:264-271`, `app.py:239-249`
**Issue:** `_has(0.0)` returns `False` because `str(0.0).strip() == "0.0"` passes but `pd.isna(0.0)` is `False`, so it actually returns `True` — wait, let me re-read: `_has(0.0)` evaluates `pd.isna(0.0)` → False, then `s = "0.0"`, `bool(s) == True`, `s.lower() != "nan"` → True. So it returns True. Numeric 0 confidence renders as `"0.00"`. OK, this is actually fine. However `_has(False)` returns `True` (`"False".lower() != "nan"`), which means an explicit `False` in `unsafe_auto_fix_reason` would render «Заблокированное автоисправление: False». Low risk but worth a guard.
**Fix:** Narrow `_has` to reject explicit booleans, or only apply `_has` to text fields and check `confidence_score` numerically:
```python
def _has_text(value: Any) -> bool:
    if value is None or isinstance(value, bool):
        return False
    try:
        if pd.isna(value): return False
    except (TypeError, ValueError):
        pass
    s = str(value).strip()
    return bool(s) and s.lower() != "nan"
```

### IN-04: Russian-string copy drift — modal collision message vs. UI-SPEC

**File:** `app.py:531-534`, `06-UI-SPEC.md:207`
**Issue:** UI-SPEC line 207 specifies the collision string as «Профиль `{profile_id}` уже существует. Чтобы перезаписать, отметьте чекбокс ниже и заполните поле «Причина» (минимум 8 символов).». `app.py:531-534` renders «Профиль \`{profile_id}\` уже существует. Чтобы перезаписать, отметьте чекбокс ниже и заполните поле «Причина» (минимум 8 символов).» — identical text but rendered through `st.warning` (UI-SPEC says «inline below the «Применить и сохранить» button»). The UI-SPEC implies the message appears UNDER the disabled button, but the implementation places it ABOVE the checkbox/textarea pair. Minor information-architecture drift; not a bug.
**Fix:** If owner-of-record (D-DESIGN-REVIEW) considers this a regression, restructure the layout:
```python
overwrite = st.checkbox(..., key="modal_overwrite_checkbox")
reason = st.text_area(..., key="modal_reason_textarea")
apply_clicked = st.button("Применить и сохранить", ..., disabled=apply_disabled)
if not (overwrite and reason_ok):
    st.warning("Профиль уже существует. Отметьте чекбокс и заполните причину...")
```

---

_Reviewed: 2026-05-14_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
