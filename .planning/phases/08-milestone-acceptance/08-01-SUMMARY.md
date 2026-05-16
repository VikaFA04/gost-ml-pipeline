---
phase: 08-milestone-acceptance
plan: 01
subsystem: testing
tags: [pytest, acceptance-gate, tdd, streamlit, sc1, sc2, sc4]

# Dependency graph
requires:
  - phase: 07-pdf-text-layer-audit-slice
    provides: 07-UAT.md status=complete (referenced by SC-4 test)
  - phase: 09-classical-model-zoo-lr-svm-complementnb-randomforest-histgbm
    provides: 09-03-SUMMARY.md UAT 8/8 record (referenced by SC-4 test)
provides:
  - pytest.ini with slow marker registration (D-E-07)
  - tests/test_milestone_acceptance_sc1.py — SC-1 end-to-end corpus gate
  - tests/test_milestone_acceptance_sc2_after_rules.py — SC-2 after-rules production floor gate
  - tests/test_milestone_acceptance_sc4.py — SC-4 design-review consolidation gate
  - tests/test_streamlit_smoke.py — Streamlit headless boot gate
affects: [08-milestone-acceptance, phase-08-02, phase-08-03]

# Tech tracking
tech-stack:
  added: [pytest.ini]
  patterns: [RED-state TDD gate definition, direct file-read SC-4 assertions (D-E-01), conservative skip guard for SC-2 (D-E-04), subprocess.Popen Streamlit headless smoke (D-C-04)]

key-files:
  created:
    - pytest.ini
    - tests/test_milestone_acceptance_sc1.py
    - tests/test_milestone_acceptance_sc2_after_rules.py
    - tests/test_milestone_acceptance_sc4.py
    - tests/test_streamlit_smoke.py
  modified: []

key-decisions:
  - "D-E-07: pytest.ini (not pyproject.toml or setup.cfg) to register slow marker — zero risk to D-D-04 no-pyproject constraint"
  - "D-E-08: SC-1 calls process_document() Python API directly, not CLI subprocess (audit-docx has no --apply-safe)"
  - "D-E-04: SC-2 after-rules test is conservative — skip if no evaluation_*.json rather than invoking train"
  - "D-E-01: SC-4 uses direct file-read assertions, not gsd-sdk audit.uat-aggregate (which lacks severity fields)"
  - "Profile path adapted from rules/gost_7_32_2017.json to src/rules/profiles/gost_7_32_2017.json for worktree branch"

patterns-established:
  - "Acceptance gate tests: importorskip gating for optional deps (streamlit, requests)"
  - "SC-4 pattern: assert file exists + grep severity lines == 0, no SDK calls"
  - "SC-2 after-rules pattern: sorted glob reverse=True, skip if empty"

requirements-completed: [REQ-mvp-acceptance]

# Metrics
duration: 15min
completed: 2026-05-15
---

# Phase 8 Plan 01: Milestone Acceptance RED Gate Summary

**pytest.ini + 4 RED acceptance-gate test files defining SC-1/SC-2/SC-4/Streamlit contracts; test_sc4_rollup_exists confirmed FAILED awaiting 08-03**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-15T13:00:00Z
- **Completed:** 2026-05-15T13:15:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Created pytest.ini at repo root — PytestUnknownMarkWarning absent from all pytest runs
- Created 4 RED acceptance-gate test files covering all Phase 8 success criteria (SC-1, SC-2b, SC-4, Streamlit)
- Confirmed RED state: test_sc4_rollup_exists FAILED with "08-DESIGN-REVIEW-ROLLUP.md absent" as required

## Task Commits

1. **Task 1: Create pytest.ini** - `b4583d8` (chore)
2. **Task 2: Create RED test files** - `09a376e` (test)
3. **Task 3: Confirm RED state** - (no commit — verification only, no files changed)

## Files Created/Modified

- `pytest.ini` — [pytest] markers = slow: ... (D-E-07)
- `tests/test_milestone_acceptance_sc1.py` — SC-1 gate: calls process_document() on fast/slow tier corpus
- `tests/test_milestone_acceptance_sc2_after_rules.py` — SC-2(b) gate: reads results/metrics/evaluation_*.json after_rules block
- `tests/test_milestone_acceptance_sc4.py` — SC-4 gate: direct file-read of 07-UAT.md, 09-03-SUMMARY.md, 08-DESIGN-REVIEW-ROLLUP.md
- `tests/test_streamlit_smoke.py` — Streamlit headless boot: subprocess.Popen port 8502, HTTP 200 within 30s

## Test Run Output (Task 3 — RED state confirmation)

```
FAILED tests/test_milestone_acceptance_sc4.py::test_sc4_phase7_uat_status_complete
FAILED tests/test_milestone_acceptance_sc4.py::test_sc4_phase7_no_open_severity
FAILED tests/test_milestone_acceptance_sc4.py::test_sc4_phase9_summary_exists
FAILED tests/test_milestone_acceptance_sc4.py::test_sc4_phase9_no_open_severity
FAILED tests/test_milestone_acceptance_sc4.py::test_sc4_rollup_exists - 08-DESIGN-REVIEW-ROLLUP.md absent
FAILED tests/test_streamlit_smoke.py::test_streamlit_app_upload_contract
======= 6 failed, 1 passed, 3 skipped, 1 deselected, 1 warning in 7.06s ========
```

Key outcomes:
- `test_sc4_rollup_exists`: FAILED — "08-DESIGN-REVIEW-ROLLUP.md absent" (08-03 writes it)
- `test_sc1_fast_tier[*.docx]`: SKIPPED — corpus fixtures absent in this worktree branch
- `test_sc2_after_rules_floor`: SKIPPED — no evaluation_*.json in worktree results/metrics/
- `test_streamlit_boots_to_200`: PASSED — Streamlit booted successfully on port 8502
- `test_streamlit_app_upload_contract`: FAILED — app.SUPPORTED_UPLOAD_TYPES=['docx'] != ['docx','pdf']

## Decisions Made

- Profile path adapted from `rules/gost_7_32_2017.json` (plan spec for newer branch) to `src/rules/profiles/gost_7_32_2017.json` (actual path in this worktree branch). The test uses `_PROFILE = _REPO / "src" / "rules" / "profiles" / "gost_7_32_2017.json"` — deviation documented below.
- SC-4 `_PLANNING` resolves to worktree's `.planning/phases/` (no phases/ subdir in worktree), causing all SC-4 file-present tests to FAIL. This is acceptable RED state per plan ("all FAIL or SKIP").

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Profile path adapted to worktree branch structure**
- **Found during:** Task 2 (test_milestone_acceptance_sc1.py authoring)
- **Issue:** Plan specified `_PROFILE = _REPO / "rules" / "gost_7_32_2017.json"` (path valid on `a5bd46b` branch). Worktree branch (`cbb1104`) has profiles at `src/rules/profiles/gost_7_32_2017.json`.
- **Fix:** Used `_PROFILE = _REPO / "src" / "rules" / "profiles" / "gost_7_32_2017.json"` in test_milestone_acceptance_sc1.py
- **Files modified:** tests/test_milestone_acceptance_sc1.py
- **Verification:** pytest --collect-only succeeds; no import error
- **Committed in:** 09a376e (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — profile path correction for worktree branch)
**Impact on plan:** Necessary for the test to reference an existing file path. No scope creep.

## Issues Encountered

- Worktree branch (`cbb1104`) predates Phase 7/9 outputs and has no `tests/fixtures/corpus/` — SC-1 fast-tier tests SKIP gracefully (expected per plan).
- Worktree `.planning/` has only one file (not the full phases/ tree) — SC-4 tests FAIL on file-absent assertions. This is acceptable: `test_sc4_rollup_exists` FAILED for the correct reason.
- `test_streamlit_app_upload_contract` FAILED because older app.py has `SUPPORTED_UPLOAD_TYPES=['docx']` only (PDF support added in Phase 7). This is a valid RED signal.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `pytest.ini` in place; all `@pytest.mark.slow` decorators now registered
- 4 RED test files committed; GREEN wiring handled in 08-02 (Makefile harness)
- 08-03 must write `08-DESIGN-REVIEW-ROLLUP.md` to make `test_sc4_rollup_exists` PASS

---
*Phase: 08-milestone-acceptance*
*Completed: 2026-05-15*
