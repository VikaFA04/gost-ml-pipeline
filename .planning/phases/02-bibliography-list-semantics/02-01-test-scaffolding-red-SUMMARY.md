---
plan: 02-01-test-scaffolding-red
phase: 02-bibliography-list-semantics
status: complete
completed_at: 2026-05-13
tasks_completed: 5
commits: 5
---

# Plan 02-01 — Test Scaffolding RED — Summary

Wave 0 (RED) complete. Every Phase 2 D-NN decision now has a pinned failing
test. Per CLAUDE.md "Железный закон", Waves 1–3 may now write production code
against this contract.

## Commits

- `e6962d8` test(02-01): add bibliography_minimal.docx fixture builder + binary DOCX
- `08283cc` test(02-01): append D-01 + D-04 RED tests to test_postprocess_rules.py
- `bbbd2b6` test(02-01): create test_profile_loader.py with D-11 + D-03 RED tests
- `550491e` test(02-01): create test_bibliography_phase2.py with 11 RED tests for D-01..D-15
- `a309155` test(02-01): add D-15 negative corpus diff-rate regression gate

## Tasks

| # | File | Tests | Decisions Pinned |
|---|------|-------|------------------|
| 1 | `tests/fixtures/_build_bibliography_minimal.py` + `tests/fixtures/bibliography_minimal.docx` | fixture builder | D-14 (hand-crafted DOCX) |
| 2 | `tests/test_postprocess_rules.py` (appended) | 2 RED + 1 sanity | D-01, D-04 |
| 3 | `tests/test_profile_loader.py` (new) | 2 ImportError RED + 1 assertion RED + 1 GREEN | D-03, D-11 |
| 4 | `tests/test_bibliography_phase2.py` (new) | 11 (≥9 RED) | D-01, D-04, D-05, D-06, D-07, D-09, D-10, D-11, D-13, D-14 |
| 5 | `tests/test_negative_corpus_diff_rate.py` (new) | 1 (PASS or RED with diff-rate data) | D-15 |

Total new tests added: ~19 (matches plan verification expected count).

## Hand-off Contract for Waves 1–3

- **Wave 1 — Plan 02-02 (postprocess + profile)** turns GREEN:
  - `test_postprocess_rules.py` D-01, D-04 cases.
  - `test_profile_loader.py` D-03, D-11 cases.
- **Wave 2 — Plan 02-03 (multilevel numbering)** turns GREEN:
  - `test_bibliography_phase2.py` D-05 abstract + override, D-06 coercion, D-07 idempotency, D-05 ilvl=1 cases.
- **Wave 3 — Plan 02-04 (ambiguous routing + gate)** turns GREEN:
  - `test_bibliography_phase2.py` D-09 routing, D-13 alignment cases.
  - `test_negative_corpus_diff_rate.py` D-15 gate stays ≤ 0.4781.

## Notes / Deviations

- Plan was executed in two passes — initial parallel agent committed Tasks 1–3
  then the spawning runtime returned a stream-idle timeout. Tasks 4–5 + this
  SUMMARY were completed inline by the orchestrator inside the same worktree
  to preserve the existing 3 commits and avoid re-creating the fixture binary.
- Pyright import-resolution warnings on `src.*` imports inside the worktree
  are workspace-config artifacts (Pyright is configured against the main repo
  root, not isolated worktrees). They disappear after the worktree merges.
- `python` is not on PATH in this shell; tests will run via `python3` /
  `pytest` once the worktree merges into main and the orchestrator runs the
  full suite.
