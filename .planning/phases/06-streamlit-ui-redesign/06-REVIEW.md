---
phase: 06-streamlit-ui-redesign
reviewed: 2026-05-15T10:00:00Z
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
  critical: 0
  warning: 0
  info: 6
  total: 6
verified_fixes:
  - id: CR-01
    fix_commit: a81b892
    note: modal_reason_is_valid (app.py:41-48) now requires len(strip)>=8 AND any printable non-whitespace char. Boolean-equivalent to CLI predicate at src/main.py:367-369 (`len(stripped) < 8 or not printable_non_ws`). Defensive `(reason or "")` guard added against None. CONFIRMED.
  - id: CR-02
    fix_commit: a81b892
    note: methodical_modal call lifted out of `with st.sidebar:` (app.py:684-685). Sidebar button (line 651) sets st.session_state["methodical_modal_request"]=True; the @st.dialog-decorated function is invoked at top-level script context after the sidebar `with` block exits. CONFIRMED.
  - id: WR-01
    fix_commit: d93f7a0
    note: Catch-all (app.py:445-450) now records stage="unknown" with documented rationale comment. Pre-existing `RunLog.record` is a pass-through for stage values per tests/test_run_log.py:138-149, so the new label is accepted by the contract. CONFIRMED.
  - id: WR-02
    fix_commit: d93f7a0
    note: Single helper `_persist_run_log` (app.py:384-396) writes once per run; success path caches path at line 467. `render_report` (app.py:372-381) reads from `st.session_state["last_run_log_path"]` instead of re-computing a fresh timestamp + dump on every rerun. CONFIRMED.
  - id: WR-03
    fix_commit: d93f7a0
    note: Both error paths (app.py:435 and 453) call `_persist_run_log` and cache the path before early return. Empty-state branch in `main()` (app.py:707-715) renders `download_run_log_failed` button when cached log exists. Distinct widget key avoids collision with success-path `download_run_log` (app.py:380). CONFIRMED.
  - id: WR-04
    fix_commit: 9516166
    note: `_FORBIDDEN_EXTRA_KEYS` (run_log.py:18-20) and explicit `ValueError` raise (run_log.py:57-63) convert the previous docstring-only contract into an enforced one. No existing caller in src/ or app.py passes any of the forbidden keys (verified by grep), so the new ValueError cannot break in-tree callers. CONFIRMED.
  - id: WR-05
    fix_commit: d93f7a0
    note: Modal collision check (app.py:540-547) uses only `CUSTOM_PROFILES_DIR / {id}.json` — the actual write target — matching CLI semantics at src/main.py:334-335. Built-in shadowing surfaces as `st.info` note, not as a force-reason gate. CONFIRMED.
status: clean
---

# Phase 6: Code Review Report (re-review iteration 3)

**Reviewed:** 2026-05-15
**Depth:** standard
**Files Reviewed:** 7
**Status:** clean

## Summary

All 2 CRITICAL and 5 WARNING findings from `06-REVIEW.iter2.md` have been verified as fixed in commits `a81b892`, `d93f7a0`, `9516166`. No new CRITICAL or WARNING issues introduced by the fixes.

Verification highlights:
- **CR-01** — `modal_reason_is_valid` (`app.py:41-48`) is now boolean-equivalent to the CLI predicate at `src/main.py:367-369`. Defensive `(reason or "")` guard added against `None`.
- **CR-02** — `methodical_modal` is dispatched at top-level script context (`app.py:684-685`) via a `session_state` request flag set inside the sidebar; the `@st.dialog`-decorated function never executes inside the sidebar `DeltaGenerator`.
- **WR-01** — Catch-all branch records `stage="unknown"` with a documented rationale comment; the pre-existing pass-through stage contract (`tests/test_run_log.py::test_run_log_stage_is_enum_member`) accepts the new label.
- **WR-02 + WR-03** — Single `_persist_run_log` helper writes the run-log JSON once per run on all three exit paths (success, typed-preflight error, generic catch-all), caches the path in `session_state`, and a distinct `download_run_log_failed` button renders on the empty-state branch when only a failed-run log exists.
- **WR-04** — `RunLog.record` rejects forbidden PII extras (`text`, `paragraph`, `block_content`, `traceback`) at the boundary with a clear `ValueError` referencing D-04. No in-tree caller passes any of these keys, so the new check cannot break existing flows.
- **WR-05** — Modal collision check uses only `CUSTOM_PROFILES_DIR/{id}.json` (the actual write target), matching CLI semantics; built-in shadowing surfaces as an `st.info` note, not as a force-reason gate.

The 4 INFO items from iter2 (IN-01 set_page_config ordering, IN-02 historical comment, IN-03 `_has(False)`, IN-04 collision-message layout) remain unaddressed because the orchestrator scoped the fix run to `critical_warning`; they are propagated below alongside 2 NEW INFO items observed during this re-review (one stage-enum docstring drift in `run_log.py`, one cross-contamination of `last_result` + new `last_run_log_path` after a fail-after-success sequence). All info items are non-blocking.

Setting `status: clean` per the orchestrator's instruction (no NEW critical/warning findings).

## Info

### IN-01: `st.set_page_config` is at module level (carried over from iter2)

**File:** `app.py:73`
**Issue:** `st.set_page_config(...)` runs at import time. On certain rerun paths this can trigger `StreamlitAPIException("set_page_config must be called as the first Streamlit command")` if any other Streamlit call snuck in earlier. Convention is to put it as the first call inside `main()`.
**Fix:** Move line 73 to the top of `main()`, before `inject_page_styles()`. (Out of scope for current `critical_warning` fix run.)

### IN-02: `tests/test_app_ui.py` references a removed code location (carried over from iter2)

**File:** `tests/test_app_ui.py:9-10, 53-56`
**Issue:** Comment refers to «the `st.exception(exc)` regression at app.py:773». After the Phase 6 rewrite, `app.py` is 723 lines and contains no `st.exception(exc)` call. The comment is correct historically but misleads future readers.
**Fix:** Update the comment to «(historical regression — removed in Phase 6 Wave 2)» or drop the line reference.

### IN-03: `_has(False)` returns True (carried over from iter2)

**File:** `app.py:244-254`
**Issue:** `_has(False)` evaluates `pd.isna(False) → False`, then `s = "False"`, `bool(s) → True`, `s.lower() != "nan" → True`, returning `True`. An explicit `False` in `unsafe_auto_fix_reason` would render «Заблокированное автоисправление: False».
**Fix:** Add `if isinstance(value, bool): return False` early in `_has`. Low risk.

### IN-04: Modal collision message placement vs. UI-SPEC (carried over from iter2)

**File:** `app.py:570-573`, `06-UI-SPEC.md:207`
**Issue:** UI-SPEC implies the collision message appears UNDER the disabled «Применить и сохранить» button; current implementation places `st.warning` ABOVE the checkbox/textarea pair. Cosmetic IA drift.
**Fix:** Owner-of-record (DESIGN-REVIEW) decides whether to restructure the layout. Identical text otherwise.

### IN-05 (NEW): `RunLog` docstring stage enum is out of date with `unknown` sentinel

**File:** `src/inference/run_log.py:27`
**Issue:** Docstring still says `stage: one of "document-read", "classification", "rule-apply", "save"`. After the WR-01 fix, `app.py:446` emits `stage="unknown"` in the catch-all branch. The class IS a pass-through for stage values (verified by `tests/test_run_log.py::test_run_log_stage_is_enum_member`) so this is documentation drift only — not a functional bug — but a future reader who only consults the docstring will be surprised by `"unknown"` in real run-log JSON files.
**Fix:** Update the docstring to reflect the documented limitation:
```python
stage:         one of "document-read", "classification", "rule-apply", "save"
               or "unknown" when the catch-all in run_processing cannot
               attribute a non-translated exception to a specific stage
               (see app.py:438-455 / WR-01)
```

### IN-06 (NEW): Stale `last_result` cross-contamination after fail-after-success sequence

**File:** `app.py:425-455`, `app.py:697-718`
**Issue:** Both error paths in `run_processing` set `st.session_state["last_run_log_path"]` (lines 435, 453) but neither clears `st.session_state["last_result"]`. Sequence: user successfully audits Doc A → uploads Doc B → audit fails. After the fail, `last_result` still holds Doc A's `ProcessingArtifacts` and `last_run_log_path` now points at Doc B's failure log. The empty-state branch at line 698 is NOT reached (because `last_result` is non-None), so `render_report(result)` is called with Doc A's artifacts — and its run-log download button (app.py:372-381) reads Doc B's error log. The user sees Doc A's report layout with Doc B's error journal as the «Скачать журнал запуска» payload.

This is a logical consequence of the new caching behaviour combined with the pre-existing «sticky session_state» pattern. Not a regression of any specific WR fix in isolation, but worth surfacing because the new run-log path caching makes the cross-contamination observable in a new place (the journal download button payload). The `st.error("Не удалось обработать документ...")` from the failure path also surfaces, so the user is not silently misled — they see both signals — but the journal-download payload identity is mismatched.
**Fix:** Either clear `last_result` on both error paths, or scope the run-log download button to only render when its cached path matches `Path(result.input_path).stem`:
```python
# In both `except` branches of run_processing, before `return`:
st.session_state.pop("last_result", None)
```
Optional — does not block merge.

---

_Reviewed: 2026-05-15_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Iteration: 3 (post-fix verification of iter2 findings)_
