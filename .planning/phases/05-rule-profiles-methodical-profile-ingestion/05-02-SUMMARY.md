---
phase: 05-rule-profiles-methodical-profile-ingestion
plan: 02
subsystem: rule-profiles
tags: [profile-diff, pitfall-4, pure-function, tdd]

# Dependency graph
requires:
  - phase: 05-rule-profiles-methodical-profile-ingestion
    plan: 01
    provides: per-leaf {value, _source} annotated profile shape consumed by the diff walker
provides:
  - compute_profile_diff(base, candidate) -> list[str] — pure-function dotted-path diff walker that unwraps {value, _source} leaves, drops _source keys at walk time, and emits human-readable '<path>: <old> → <new>' lines grouped under '## <top_level_key>' section headers
  - write_diff_sidecar(lines, path) -> None — UTF-8 newline-joined sidecar writer with mkdir(parents=True, exist_ok=True)
  - _flatten / _unwrap helpers (internal) — recursive dict walker analogous to profile_loader.deep_merge
affects: [05-03-cli-dispatcher]

# Tech tracking
tech-stack:
  added: []  # zero new dependencies; pure stdlib (pathlib, typing, __future__)
  patterns:
    - "Pure function + thin I/O wrapper split: `compute_profile_diff` returns list[str]; `write_diff_sidecar` is the only side-effecting symbol"
    - "Defense-in-depth Pitfall 4 filter: walk-time `continue` on `_source` key + path-suffix backstop (`endswith('._source')` / `'._source.' in path`)"
    - "Annotated-leaf vs scalar-leaf symmetric comparison: `_flatten` unwraps `{value, _source}` to its `value` before recording so a GOST scalar base diffs cleanly against a methodical-annotated candidate"

key-files:
  created:
    - src/rules/profile_diff.py — 97 LoC pure module exporting compute_profile_diff + write_diff_sidecar
    - tests/test_profile_diff.py — 119 LoC, 8 tests covering arrow-emit, top-level grouping, Pitfall 4 filter, methodical-vs-scalar comparison, no-changes empty list, <missing> marker, UTF-8 sidecar writes, parent-dir creation
  modified: []

key-decisions:
  - "Per Pitfall 4, _source paths are filtered at BOTH layers (walk-time skip and path-string backstop) — defense in depth keeps a misshapen caller from leaking provenance metadata into the diff"
  - "List values are diffed as whole values (no per-index churn) — keeps the diff readable and matches the user-eyeball use case from D-02"
  - "Missing paths render as '<missing>' rather than being silently dropped — surfaces removed-key changes to the reviewer"
  - "_unwrap defined but not currently invoked outside _flatten — kept as a labelled helper for plan 5-03 (the CLI dispatcher may need it on the side for non-walker comparisons)"

patterns-established:
  - "Pure profile-comparison module: takes two dicts, returns list[str]; no I/O in compute_profile_diff"
  - "Sidecar writer convention: parent dir auto-created, trailing newline enforced, UTF-8 explicit"

requirements-completed: [REQ-methodical-profile-extract]  # partial — diff generator is the next step toward the full PROF-02 user-visible diff

# Metrics
duration: 21min
completed: 2026-05-14
---

# Phase 05 Plan 02: profile-diff generator (compute_profile_diff + write_diff_sidecar) Summary

**Pure-function `compute_profile_diff(base, candidate) -> list[str]` and its `write_diff_sidecar` writer landed at `src/rules/profile_diff.py` (97 LoC, stdlib only); flattens both dicts to dotted paths, unwraps `{value, _source}` leaves, drops `_source` at walk-time with a path-string backstop (Pitfall 4), and emits `<path>: <old> → <new>` (U+2192) lines grouped under `## <top_level_key>` section headers. 8 unit tests RED→GREEN; zero new dependencies; zero regressions on the broader collectable suite (138 passed / 1 skipped).**

## Performance

- **Duration:** ~21 min
- **Started:** 2026-05-14T12:07:24Z (plan start)
- **Completed:** 2026-05-14T12:28:00Z (GREEN commit + verification)
- **Tasks:** 2 (RED test file → GREEN implementation)
- **Files created:** 2 (`src/rules/profile_diff.py`, `tests/test_profile_diff.py`)
- **Files modified:** 0

## Accomplishments

- 8 contract tests in `tests/test_profile_diff.py` carry the D-02 / Pitfall 4 invariants:
  - `test_compute_profile_diff_emits_arrow_line_per_changed_leaf` — Unicode `→` U+2192 in line format, unchanged leaves absent
  - `test_compute_profile_diff_groups_by_top_level_key` — `## document_rules` precedes `## labels` (sorted order)
  - `test_compute_profile_diff_filters_source_metadata_paths` — Pitfall 4: provenance-only changes produce empty diff
  - `test_compute_profile_diff_handles_methodical_leaf_vs_scalar_base` — GOST scalar vs methodical `{value, _source}` diffs cleanly
  - `test_compute_profile_diff_no_changes_returns_empty` — identity case
  - `test_compute_profile_diff_marks_missing_paths` — `<missing>` placeholder on absent keys
  - `test_write_diff_sidecar_writes_utf8` — `→` preserved, trailing newline guaranteed
  - `test_write_diff_sidecar_creates_parent_dir` — `mkdir(parents=True, exist_ok=True)` honoured
- `src/rules/profile_diff.py` is 97 LoC, stdlib only (`from __future__ import annotations`, `from pathlib import Path`, `from typing import Any`).
- `compute_profile_diff` is provably pure: `grep -nE "open|read|write|print" src/rules/profile_diff.py` returns only `write_diff_sidecar`-body lines (88, 91, 97) and docstring/comment matches (lines 2, 74).
- Defense-in-depth Pitfall 4 filter: `_flatten` skips `_source` keys at walk time; `compute_profile_diff` has a secondary `path.endswith("._source") or "._source." in path` backstop.
- Annotated leaf unwrap: `{value, _source}` dicts are unwrapped to their `value` so a hand-authored GOST scalar profile diffs symmetrically against a methodical-extracted candidate.

## Task Commits

Each task was committed atomically with `--no-verify` (worktree executor):

1. **Task 1 (RED tests):** `48b497f` — `test(05-02): RED — compute_profile_diff + write_diff_sidecar`
   - Observable failure mode (verified in session): `python3 -m pytest tests/test_profile_diff.py -x -q` fails at collection with `ModuleNotFoundError: No module named 'src.rules.profile_diff'` (1 error during collection). All 8 tests blocked from running by the absent import — the strongest form of RED per the «Железный закон»: production code is physically absent.
2. **Task 2 (GREEN code):** `475ed9e` — `feat(05-02): GREEN — compute_profile_diff + write_diff_sidecar`
   - `python3 -m pytest tests/test_profile_diff.py -x -q` → `8 passed in 0.05s`.
   - `python3 -m pytest tests/ -q --ignore=tests/test_methodical_extractor.py --ignore=tests/test_app_upload_contract.py --ignore=tests/test_methodical_profile_editor.py --ignore=tests/test_application_service.py` → `138 passed, 1 skipped in 955.61s`. The three ignored modules carry the pre-existing `streamlit` / Python-3.9-`dataclass` collection errors documented in plan 5-01 and are out of scope per CLAUDE.md «чужой мёртвый код не трогай».
   - Combined methodical-extractor + profile-diff smoke: `pytest tests/test_methodical_extractor.py tests/test_profile_diff.py -q` → `13 passed`.

_TDD gate sequence verified in git log: `test(05-02)` (48b497f) → `feat(05-02)` (475ed9e)._

## Files Created/Modified

- `src/rules/profile_diff.py` — NEW, 97 LoC (≤100 per CLAUDE.md «50 строк вместо 200»). Public exports: `compute_profile_diff`, `write_diff_sidecar`. Internal helpers: `_unwrap`, `_flatten`.
- `tests/test_profile_diff.py` — NEW, 119 LoC, 8 tests, 8 `→` U+2192 occurrences.

## Decisions Made

- **Defense-in-depth Pitfall 4 filter:** the walk-time skip (`if k == "_source": continue` inside `_flatten`) is the primary defence; the path-string backstop (`path.endswith("._source") or "._source." in path`) inside `compute_profile_diff` is the redundant guard. A future caller misusing `_flatten` directly (e.g. passing a profile slice that starts inside a `_source` sub-tree) is still protected.
- **List values diffed whole:** `_flatten` records lists at their parent prefix (no `[i]` indexing). Avoids index-churn noise when the user-eyeball use case wants "this list changed".
- **`<missing>` marker for absent paths:** rather than silently dropping the path, the diff shows e.g. `document_rules.page.margin_right_cm: 1.0 → <missing>` so a removed key is visible to the reviewer.
- **`_unwrap` kept as a labelled helper:** the function is defined but only the inline `set(d.keys()) >= {"value", "_source"}` check inside `_flatten` is used in 5-02. `_unwrap` is retained for plan 5-03 (the dispatcher may need to unwrap a single leaf on the side without flattening the whole profile).

## Deviations from Plan

None — plan executed exactly as written. The plan's Task 1 and Task 2 acceptance criteria all passed on first run; no deviation, no Rule 1/2/3 invocation.

## Acceptance Criteria Verification

### Task 1 (RED)

| Criterion | Result |
|-----------|--------|
| `python3 -m pytest tests/test_profile_diff.py -x -q` exits non-zero with `ModuleNotFoundError` OR `ImportError` | OK — `ModuleNotFoundError: No module named 'src.rules.profile_diff'` |
| `wc -l tests/test_profile_diff.py >= 80` | OK — 119 |
| `grep -c "def test_" tests/test_profile_diff.py == 8` | OK — 8 |
| `grep -c "→" tests/test_profile_diff.py >= 4` | OK — 8 |
| `ls src/rules/profile_diff.py` returns nothing | OK — file absent at RED commit |
| Git commit subject matches `^test\(05-02\): RED` | OK — `test(05-02): RED — compute_profile_diff + write_diff_sidecar` |

### Task 2 (GREEN)

| Criterion | Result |
|-----------|--------|
| `python3 -m pytest tests/test_profile_diff.py -x -q` exits 0 with all 8 tests passing | OK — `8 passed in 0.05s` |
| `wc -l src/rules/profile_diff.py <= 100` | OK — 97 |
| `grep -c "_source" src/rules/profile_diff.py >= 3` | OK — 10 |
| `grep -c "→" src/rules/profile_diff.py >= 1` | OK — 2 |
| Import smoke `from src.rules.profile_diff import compute_profile_diff, write_diff_sidecar` prints OK | OK |
| Broader suite shows no regressions | OK — 138 passed / 1 skipped (excluding 3 pre-existing collection errors documented in 5-01 SUMMARY) |
| Git commit subject matches `^feat\(05-02\): GREEN` | OK — `feat(05-02): GREEN — compute_profile_diff + write_diff_sidecar` |

## Verification Block (plan-level)

| Check | Result |
|-------|--------|
| All 8 unit tests pass | OK — `8 passed in 0.05s` |
| `compute_profile_diff` is pure (no I/O calls) | OK — `grep -nE "open|read|write|print" src/rules/profile_diff.py` matches only lines inside `write_diff_sidecar` body (88, 91, 97) and docstring/comments (2, 74) |
| `src/rules/profile_diff.py` line count ≤ 100 | OK — 97 |
| No existing test regresses | OK — 138 passed / 1 skipped on the broader collectable suite; 5/5 methodical-extractor tests still GREEN |

## Required Output Confirmations

Per Plan 5-02 `<output>` section:

- **Files created with LoC counts:**
  - `src/rules/profile_diff.py`: 97 LoC.
  - `tests/test_profile_diff.py`: 119 LoC, 8 tests.
- **RED + GREEN commit SHAs:** `48b497f` (RED) / `475ed9e` (GREEN).
- **Zero-new-dependency confirmation:** `grep -nE "^import |^from " src/rules/profile_diff.py` returns:
  ```
  8:from __future__ import annotations
  10:from pathlib import Path
  11:from typing import Any
  ```
  All three are stdlib / language built-ins. No `requirements.txt` modification.
- **`compute_profile_diff` is consumed by no other module yet:** `grep -rn "profile_diff" --include="*.py" src/ tests/` outside `src/rules/profile_diff.py` and `tests/test_profile_diff.py` returns nothing. Plan 5-03 (`extract-methodical-profile` CLI dispatcher) will introduce the first caller.

## Threat Model Disposition

Per `<threat_model>` table:

- **T-04-02 (Tampering, accept):** `write_diff_sidecar(lines, path)` accepts arbitrary `path`. In 5-02 the only caller is the test suite (`tmp_path`); plan 5-03 dispatcher will own real-call sites. Severity remains low. No action taken in 5-02.
- **T-05-02 (Tampering, mitigate):** Pitfall 4 filter is path-based (`endswith("._source")` and `"._source." in path`) AND key-based (`if k == "_source": continue` in `_flatten`). Cannot be bypassed by `confidence` value tampering. Mitigation in place; carrier test `test_compute_profile_diff_filters_source_metadata_paths` proves the filter even when only `_source` fields differ.
- **T-05-04 (Info disclosure, mitigate):** Defense in depth — primary `_flatten` skip + secondary path backstop. Tested. Severity remains low.

## Known Stubs

None. `compute_profile_diff` and `write_diff_sidecar` are fully implemented; no placeholder returns, no TODO comments in production code.

## Issues Encountered

- Pre-existing collection errors in three test modules (`test_app_upload_contract.py`, `test_methodical_profile_editor.py`, `test_application_service.py`) due to `streamlit` not installed and Python-3.9 dataclass-import mismatch. **Out of scope** per CLAUDE.md scope rules — same exclusion was documented in plan 5-01 SUMMARY. Verified by running pytest with `--ignore=` for those three files and observing `138 passed, 1 skipped`.

## User Setup Required

None — pure-Python module, stdlib only, zero external services / env vars / credentials.

## Next Plan Readiness

- Plan 5-03 (`extract-methodical-profile` CLI dispatcher) can `from src.rules.profile_diff import compute_profile_diff, write_diff_sidecar` and wire stdout-print + sidecar-write for dry-run mode. The output format (`## <section>` headers + `<path>: <old> → <new>` lines) is final and tested.
- Plan 5-04 (schema lint) does not depend on 5-02 directly; the diff format is consumed only by the CLI surface.

## Self-Check: PASSED

- File `src/rules/profile_diff.py` exists: OK
  ```
  $ ls src/rules/profile_diff.py
  src/rules/profile_diff.py
  ```
- File `tests/test_profile_diff.py` exists and 8 tests GREEN: OK
  ```
  $ python3 -m pytest tests/test_profile_diff.py -q | tail -1
  8 passed in 0.05s
  ```
- Commit `48b497f` (RED) present in `git log`: OK
  ```
  $ git log --oneline | grep 48b497f
  48b497f test(05-02): RED — compute_profile_diff + write_diff_sidecar
  ```
- Commit `475ed9e` (GREEN) present in `git log`: OK
  ```
  $ git log --oneline | grep 475ed9e
  475ed9e feat(05-02): GREEN — compute_profile_diff + write_diff_sidecar
  ```
- `wc -l src/rules/profile_diff.py` ≤ 100: OK — 97
- `grep -c "_source" src/rules/profile_diff.py` ≥ 3: OK — 10
- `grep -c "→" src/rules/profile_diff.py` ≥ 1: OK — 2
- `grep -c "def test_" tests/test_profile_diff.py` = 8: OK
- TDD gate sequence (`test(05-02)` precedes `feat(05-02)`): OK

---
*Phase: 05-rule-profiles-methodical-profile-ingestion*
*Plan: 02*
*Completed: 2026-05-14*
