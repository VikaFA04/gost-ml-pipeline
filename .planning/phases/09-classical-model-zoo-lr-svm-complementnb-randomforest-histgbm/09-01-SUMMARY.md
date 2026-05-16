---
phase: "09"
plan: "01"
subsystem: classical-model-zoo
tags: [tdd, red-phase, requirements, classical-zoo, ml-comparison]

dependency_graph:
  requires: []
  provides:
    - REQ-classical-model-zoo in REQUIREMENTS.md
    - tests/test_compare_classical_acceptance.py (4 RED TDD gates)
  affects:
    - .planning/REQUIREMENTS.md (Quality gates subsection updated)

tech_stack:
  added: []
  patterns:
    - TDD RED phase — import-fail trigger pattern (module-level import as RED trigger)
    - Phase 4/5 artifact-schema lint test pattern mirrored

key_files:
  created:
    - tests/test_compare_classical_acceptance.py
  modified:
    - .planning/REQUIREMENTS.md

decisions:
  - REQ-classical-model-zoo inserted immediately before REQ-mvp-acceptance (line 152)
  - SC2 floor gated on `linear_svm_production` row (not `linear_svm`) per D-E-01 resolution
  - `test_per_model_metric_floor` marked `@pytest.mark.slow` for full-dataset run
  - `test_cli_smoke_runs_end_to_end_quick` covers both file-existence and results.json key-shape

metrics:
  duration: "~3 minutes"
  completed: "2026-05-16T05:08:39Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 1
  files_created: 1
---

# Phase 09 Plan 01: Classical Model Zoo — RED Phase Summary

**One-liner:** 4 RED TDD acceptance tests for 6-classifier zoo CLI, gated on `src.compare_classical` import failure, with locked D-C-02 schema and Phase 8 SC-2 floor assertions.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add REQ-classical-model-zoo to REQUIREMENTS.md | 660ec45 | `.planning/REQUIREMENTS.md` |
| 2 | Write 4 RED acceptance tests | 328b3e7 | `tests/test_compare_classical_acceptance.py` |

## RED Test Functions

1. `test_cli_smoke_runs_end_to_end_quick` — CLI smoke: produces 4 artifacts, exits 0, validates `results.json` top-level keys (`models/environment/timestamps/dataset_hashes/cli_args`)
2. `test_results_csv_has_locked_8_column_schema` — D-C-02 column order locked (8 cols), 6 model rows, no null `weighted_f1`
3. `test_per_model_metric_floor` — `@pytest.mark.slow`: every row `weighted_f1 > 0.5`; `linear_svm_production` clears Phase 8 SC-2 floor (`weighted_f1 >= 0.94 AND macro_f1 >= 0.9414`)
4. `test_per_class_f1_md_contains_every_label_core_class` — `per_class_f1.md` contains all `label_core` classes from `annotations_test.csv`

## Pytest RED State Confirmation

```
ERROR collecting tests/test_compare_classical_acceptance.py
tests/test_compare_classical_acceptance.py:16: in <module>
    from src.compare_classical import run_compare_classical  # noqa: F401
E   ModuleNotFoundError: No module named 'src.compare_classical'
```

All 4 tests fail at collection time — import-level RED trigger confirmed. TDD iron law satisfied.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `.planning/REQUIREMENTS.md`: FOUND — REQ-classical-model-zoo at line 152, before REQ-mvp-acceptance at line 164
- `tests/test_compare_classical_acceptance.py`: FOUND — 150 lines, 4 test functions
- Commit `660ec45`: FOUND (REQUIREMENTS.md update)
- Commit `328b3e7`: FOUND (RED test file)
- pytest RED state: CONFIRMED — ModuleNotFoundError on `src.compare_classical`
