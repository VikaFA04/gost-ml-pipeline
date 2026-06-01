---
phase: 06-streamlit-ui-redesign
fixed_at: 2026-05-14T00:00:00Z
review_path: .planning/phases/06-streamlit-ui-redesign/06-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 2
status: fixed
---

# Phase 6: Code Review Fix Report

**Fixed at:** 2026-05-14
**Source review:** `.planning/phases/06-streamlit-ui-redesign/06-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in REVIEW.md: 7 (2 critical + 5 warning, info excluded by scope)
- Findings in scope (this run): 5 warning
- Fixed: 5 warning
- Skipped: 2 critical (already resolved by commit `a81b892` per REVIEW.md frontmatter `critical_resolved` block)

## Per-Finding Action Table

| ID    | Severity | File                                | Action  | Reason / Commit message file                |
|-------|----------|-------------------------------------|---------|---------------------------------------------|
| CR-01 | critical | `app.py:41-43`                      | skipped | already resolved by commit `a81b892`        |
| CR-02 | critical | `app.py:604-618`                    | skipped | already resolved by commit `a81b892`        |
| WR-01 | warning  | `app.py:419-429`                    | fixed   | `/tmp/06-fix-WR-01-commit.txt`              |
| WR-02 | warning  | `app.py:364-378`                    | fixed   | `/tmp/06-fix-WR-02-commit.txt`              |
| WR-03 | warning  | `app.py:407-429`, `app.py:364-378`  | fixed   | `/tmp/06-fix-WR-03-commit.txt`              |
| WR-04 | warning  | `src/inference/run_log.py:42-58`    | fixed   | `/tmp/06-fix-WR-04-commit.txt`              |
| WR-05 | warning  | `app.py:504-508`                    | fixed   | `/tmp/06-fix-WR-05-commit.txt`              |

## Fixed Issues

### WR-01: Catch-all branch hard-codes `stage="rule-apply"` regardless of failure stage

**File modified:** `app.py`
**Commit message:** `/tmp/06-fix-WR-01-commit.txt`
**Applied fix:** Replaced the misleading `stage="rule-apply"` literal in the catch-all branch with `stage="unknown"`, the explicit sentinel that documents the limitation without violating the audit-log enum semantics. Per the review's own fallback advice and CLAUDE.md «минимум кода», no exception-wrapper was introduced — the structural fix (typed `StageError`) is out of scope for Phase 6 GREEN.

### WR-02: `render_report` writes a new run-log JSON to disk on every Streamlit rerun

**File modified:** `app.py`
**Commit message:** `/tmp/06-fix-WR-02-commit.txt`
**Applied fix:** Introduced `_persist_run_log(run_log, input_filename) -> Path` helper. `run_processing` calls it on the success path and caches the resulting `Path` in `st.session_state["last_run_log_path"]`. `render_report` now reads from that cached path via `log_path.read_bytes()` instead of re-dumping a new timestamped file every rerun. Net effect: one disk write per audit run, regardless of how many UI reruns happen.

### WR-03: Run-log is never dumped to disk on the early-return error path

**Files modified:** `app.py`
**Commit message:** `/tmp/06-fix-WR-03-commit.txt`
**Applied fix:** Both early-return error paths in `run_processing` (preflight-translated and generic catch-all) now persist the run-log via `_persist_run_log` and cache the path in `st.session_state["last_run_log_path"]`. `main()` renders a `download_run_log_failed` button on the empty-state branch (when `last_result is None`) whenever a cached log path exists, mirroring the success-path download. D-04 «journal запуска is downloadable per audit run, including failed runs» now holds.

### WR-04: `RunLog.record(**extras)` accepts forbidden PII keys silently

**File modified:** `src/inference/run_log.py`
**Commit message:** `/tmp/06-fix-WR-04-commit.txt`
**Applied fix:** Added module-level `_FORBIDDEN_EXTRA_KEYS = frozenset({"text", "paragraph", "block_content", "traceback"})`. `RunLog.record` checks `_FORBIDDEN_EXTRA_KEYS & extras.keys()` at the top of the method and raises `ValueError` with a D-04-citing message when any forbidden key appears. Updated the class docstring to reflect the new active enforcement. Verified by `python3 -m pytest tests/test_run_log.py -q` — 7/7 GREEN (existing field-level test still passes; no test relies on silent acceptance of forbidden keys).

### WR-05: `methodical_modal` collision check diverges from CLI by checking both directories

**File modified:** `app.py`
**Commit message:** `/tmp/06-fix-WR-05-commit.txt`
**Applied fix:** Replaced the two-directory collision probe (`PROFILES_DIR ∪ CUSTOM_PROFILES_DIR`) with a single check against the actual write target (`CUSTOM_PROFILES_DIR / {profile_id}.json`), mirroring `src/main.py:334-335` (`target_dir = output_dir or PROFILES_DIR`). When `profile_id` shadows a built-in shipped profile, the modal now surfaces an inline `st.info` note for transparency rather than gating with a force-reason requirement. «UI mirrors CLI» now holds in both directions.

## Skipped Issues

### CR-01: `modal_reason_is_valid` does not mirror Phase 5 T-05-01 contract

**File:** `app.py:41-43`
**Reason:** Already resolved — commit `a81b892` («fix(06): CR-01 + CR-02 — tighten modal reason gate, lift @st.dialog out of sidebar»). Per REVIEW.md frontmatter `critical_resolved` block: «`modal_reason_is_valid` now requires printable non-whitespace char per src/main.py:367-374 T-05-01». Verified by re-reading `app.py:41-48` — the predicate now enforces both `len(stripped) >= 8` AND `any(c.isprintable() and not c.isspace() for c in stripped)`.

### CR-02: `methodical_modal` invoked from inside `with st.sidebar:` violates `st.dialog` constraint

**File:** `app.py:604-618`
**Reason:** Already resolved — same commit `a81b892`. Per REVIEW.md frontmatter `critical_resolved` block: «`methodical_modal` call lifted out of `with st.sidebar:` via session_state flag pop at top level». Verified by re-reading `app.py`: the sidebar block now only sets `st.session_state["methodical_modal_request"] = True` on click; the modal is invoked at lines 684-685 (`if st.session_state.pop("methodical_modal_request", False): methodical_modal(...)`) outside any `with st.sidebar:` context.

## Verification

**Per-fix verification (3-tier):**
- Tier 1 (re-read): all modified file regions re-read, fixes confirmed present, surrounding code intact.
- Tier 2 (syntax): `python3 -c "import ast; ast.parse(open('<file>').read())"` PASSED for both `src/inference/run_log.py` and `app.py`.
- Test suite: `python3 -m pytest tests/test_run_log.py -q` → 7/7 PASSED before and after the WR-04 change. Streamlit-dependent tests skip on the orchestrator's system Python 3.9 + Windows-binary `.venv` per OQ-3 (expected; not a regression).

**Pre-existing collection errors NOT caused by this fix:**
- `tests/test_application_service.py` — `TypeError: dataclass() got an unexpected keyword argument 'slots'` (Python 3.9 vs Python 3.10+ feature; pre-existing).
- `tests/test_app_upload_contract.py`, `tests/test_methodical_profile_editor.py` — `ModuleNotFoundError: No module named 'streamlit'` (system Python lacks Streamlit; pre-existing, expected per OQ-3).

## Staging State

Both modified files are staged (`git add` only — no commits made by the fixer per orchestrator's instruction):
- `src/inference/run_log.py` — WR-04 fix
- `app.py` — WR-01, WR-02, WR-03, WR-05 fixes (single file, multiple findings)

Per-fix commit message bodies are written to:
- `/tmp/06-fix-WR-01-commit.txt`
- `/tmp/06-fix-WR-02-commit.txt`
- `/tmp/06-fix-WR-03-commit.txt`
- `/tmp/06-fix-WR-04-commit.txt`
- `/tmp/06-fix-WR-05-commit.txt`
- `/tmp/06-fix-review-fix-commit.txt` (for REVIEW-FIX.md commit, written below)

**Note for orchestrator:** WR-01, WR-02, WR-03, WR-05 all modify `app.py` in a single staged diff. The orchestrator can either:
(a) split the diff into 4 atomic commits using `git add -p` per finding, or
(b) collapse them into one combined commit referencing all four findings (the four message files document each scope independently).

---

_Fixed: 2026-05-14_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
