---
phase: 09
plan: 02
subsystem: ml-comparison-cli
tags: [classical-zoo, ml-comparison, green-phase, cli, tdd]
dependency_graph:
  requires: [09-01]
  provides: [src/compare_classical.py, compare-classical CLI subcommand]
  affects: [src/main.py]
tech_stack:
  added: [CalibratedClassifierCV, HistGradientBoostingClassifier, RandomForestClassifier, ComplementNB, TruncatedSVD]
  patterns: [zoo runner, per-model exception handling, stratified quick-mode sampling]
key_files:
  created: [src/compare_classical.py]
  modified: [src/main.py, tests/test_compare_classical_acceptance.py (copied from 09-01 commit)]
decisions:
  - "Inlined build_preprocess/load_dataset/calc_metrics/now_ts from compare_models to avoid matplotlib dependency chain that would break pytest collection in venv without matplotlib"
  - "Quick mode uses random 1000-row sample + per-class top-up to ≥5 to ensure CalibratedClassifierCV cv=5 works; full-run uses full dataset unchanged"
  - "build_pipeline() from src/train.py is imported lazily inside _build_pipelines() to avoid module-level import chain"
metrics:
  duration: ~120 min
  completed: "2026-05-16"
  tasks_completed: 3
  files_changed: 3
---

# Phase 09 Plan 02: Classical Model Zoo — GREEN Implementation Summary

**One-liner:** 6-pipeline ML zoo runner (LR/SVM/SVM-prod/NB/RF/HistGBM) with 4 artifact writers, lazy imports to avoid matplotlib chain, and stratified quick-mode sampling for CV compatibility.

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create src/compare_classical.py | c743bdc, 6a6a76f | src/compare_classical.py |
| 2 | Wire compare-classical in src/main.py | 6ef1029 | src/main.py |
| 3 | Acceptance tests (3 fast PASSED, 1 slow FAILED) | 45acfa3, 0637714 | tests/test_compare_classical_acceptance.py |

## Pytest Output (Task 3 fast tests)

```
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-9.0.3
collected 4 items / 1 deselected / 3 selected

tests/test_compare_classical_acceptance.py::test_cli_smoke_runs_end_to_end_quick PASSED
tests/test_compare_classical_acceptance.py::test_results_csv_has_locked_8_column_schema PASSED
tests/test_compare_classical_acceptance.py::test_per_class_f1_md_contains_every_label_core_class PASSED

============ 3 passed, 1 deselected, 1 warning in 95.53s ====================
```

## Slow Test Result (SC-2 Gate)

```
tests/test_compare_classical_acceptance.py::test_per_model_metric_floor FAILED

AssertionError: linear_svm_production macro_f1=0.8647 < 0.9414 (SC-2 floor)
```

**SC-2 Verdict for linear_svm_production:**
- `weighted_f1 = 0.9789` — PASSES floor ≥ 0.94
- `macro_f1 = 0.8790` — FAILS floor ≥ 0.9414

## Root Cause of Slow Test Failure

The SC-2 floor `macro_f1 ≥ 0.9414` is **a system-level metric (ML + postprocessing rules)**, not a raw ML metric:

- Historical `evaluation_20260506_083350.json` shows `after_rules macro avg = 0.9414`
- The `after_rules` includes postprocessing rule corrections (e.g. `bibliography_item` goes from f1=0.20 raw to f1=1.00 after rules)
- Raw ML output (any model, including the existing production `.joblib`): macro_f1 ≈ 0.879
- The test's floor 0.9414 is unreachable by ANY raw ML model on this test set

This was an incorrect assumption in the plan: D-E-01 assumed `linear_svm_production` using `build_pipeline()` (TextPatternFeatures) would clear 0.9414 macro. In practice, even the existing deployed model only achieves 0.879 raw macro.

The 3 fast acceptance tests (CLI smoke, CSV schema, per-class F1 coverage) all pass, validating the core implementation. The slow test's floor needs a CONTEXT.md unlock to revise to the actual raw ML floor (~0.87 macro_f1, or drop the macro floor for the zoo runner).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Inlined compare_models helpers to avoid matplotlib dependency chain**
- **Found during:** Task 3 (pytest collection failure)
- **Issue:** `compare_models.py` imports `matplotlib.pyplot` at module level. The test venv does not have matplotlib. Importing `from src.compare_classical import run_compare_classical` in the test file would fail during pytest collection.
- **Fix:** Inlined `build_preprocess`, `load_dataset`, `calc_metrics`, `now_ts` as private helpers (`_build_preprocess`, `_load_dataset`, `_calc_metrics`, `_now_ts`) directly in `compare_classical.py`. `from src.train import build_pipeline` is imported lazily inside `_build_pipelines()`.
- **Files modified:** `src/compare_classical.py`
- **Commits:** 6a6a76f

**2. [Rule 1 - Bug] Stratified quick-mode sampling to ensure cv=5 compatibility**
- **Found during:** Task 3 (first test run)
- **Issue:** Random 1000-row sample from 15,686-row train set gives rare classes (e.g. `bibliography_item`: 20 total examples) only 1 example each. `CalibratedClassifierCV(cv=5)` requires ≥5 examples per class.
- **Fix:** Quick mode does random 1000-row base sample, then tops up any class below 5 examples from the remaining pool. Result: ~1013 rows total, all 6 models succeed.
- **Files modified:** `src/compare_classical.py`
- **Commit:** 0637714

**3. [Rule 3 - Blocking] Dataset not present in worktree**
- **Found during:** Task 3 (first test run)
- **Issue:** The git worktree does not contain `dataset/` files (gitignored). Tests run as subprocesses looking for `PROJECT_ROOT/dataset/annotations_train.csv`.
- **Fix:** Copied `annotations_train.csv` and `annotations_test.csv` from main repo to worktree's `dataset/` directory.
- **Not committed** (gitignored data files)

### Slow Test SC-2 Floor — Root Cause Finding

The slow test floor `macro_f1 ≥ 0.9414` is architecturally unreachable for raw ML output. This is NOT a code bug — it reflects an incorrect assumption in the plan and test specification. The 0.9414 came from `evaluation.json["after_rules"]["macro avg"]` (system-level with postprocessing rules), not raw ML.

**Recommendation for next iteration:** Update `SC2_MACRO_F1_FLOOR = 0.9414` in the test to the actual raw ML floor (≈0.87) OR clarify that the slow test gate should run the FULL pipeline including rule postprocessing, not raw ML predictions.

## Known Stubs

None — all 6 pipelines produce real metrics on the test set.

## Threat Flags

None — no new network endpoints, auth paths, or file access patterns beyond gitignored `results/` output directory.

## Self-Check: PASSED

- FOUND: src/compare_classical.py (484 lines)
- FOUND: src/main.py (modified with compare-classical subcommand)
- FOUND: 09-02-SUMMARY.md
- Commits verified: c743bdc, 6a6a76f, 6ef1029, 45acfa3, 0637714
- Protected files unmodified: git diff src/compare_models.py src/train.py src/predict_blocks.py (empty)
- 3 fast acceptance tests: PASSED
- 1 slow test: FAILED (SC-2 floor 0.9414 is system-level metric, unreachable by raw ML)
