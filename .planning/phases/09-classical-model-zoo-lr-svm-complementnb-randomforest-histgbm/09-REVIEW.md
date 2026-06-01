---
phase: 09-classical-model-zoo-lr-svm-complementnb-randomforest-histgbm
reviewed: 2026-05-15T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/compare_classical.py
  - src/main.py
  - tests/test_compare_classical_acceptance.py
  - tests/test_phase_8_sc2_acceptance.py
  - Makefile
findings:
  critical: 0
  high: 1
  medium: 1
  low: 1
  total: 3
status: issues_found
---

# Phase 9: Code Review Report

**Reviewed:** 2026-05-15
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

---

## Summary

Five files reviewed: the new 503-line `src/compare_classical.py` (6-model zoo runner), additions to `src/main.py` (subcommand dispatcher), two new acceptance test files, and the Makefile extension.

**Overall quality is high.** Security mitigations (T-09-W2-01 `.resolve()`, T-09-W2-02 `str(exc)[:200]`) are in place and correctly applied. The locked CSV column order (D-C-02), six model names (D-E-01), artifact set (D-C-01), CalibratedClassifierCV fresh-instance pattern (P4), and P1 `classifier__sample_weight=` pass-through are all correctly implemented.

Three issues found: one HIGH (the SC-2 verdict in `summary.txt` uses the stale `0.9414` after-rules floor instead of the locked raw-ML floor `0.86` per D-E-05 OQ-5 amendment — this will print a misleading FAIL verdict on valid runs), one MEDIUM (hardcoded column lists in `_build_tfidf_svd_preprocess` diverge from the `CAT_COLS`/`NUM_COLS` config constants used everywhere else — silent breakage if config changes), and one LOW (stale threshold mention in a test docstring — test logic is correct but misleading to future readers).

---

## High Issues

### H-01: `summary.txt` SC-2 verdict uses stale `0.9414` after-rules floor — will FAIL on valid runs

**File:** `src/compare_classical.py:454-458`

**Issue:** `_write_summary_txt` computes the SC-2 verdict using `mf1 >= 0.9414`, which is the after-rules system-level floor. Per D-E-05 (OQ-5 amendment 2026-05-16), the zoo gate floor was relaxed to `macro_f1 >= 0.86` (raw-ML). The acceptance tests in both `test_compare_classical_acceptance.py:44` and `test_phase_8_sc2_acceptance.py:25` correctly use `0.86`. The `summary.txt` verdict is the only place still using `0.9414`. A production zoo run where `macro_f1` is in `[0.86, 0.9413]` (the measured baseline is `0.8647`) will write `FAIL` to `summary.txt` while all tests pass — misleading to operators and contradicting the locked decision.

**Fix:**
```python
# src/compare_classical.py:454 — replace:
sc2_ok = wf1 >= 0.94 and mf1 >= 0.9414
# and line 458 — replace:
f"(weighted_f1={wf1:.4f} >= 0.94, macro_f1={mf1:.4f} >= 0.9414)"

# with:
sc2_ok = wf1 >= 0.94 and mf1 >= 0.86
# and:
f"(weighted_f1={wf1:.4f} >= 0.94, macro_f1={mf1:.4f} >= 0.86)"
```

---

## Medium Issues

### M-01: `_build_tfidf_svd_preprocess` hardcodes column names instead of using `CAT_COLS`/`NUM_COLS`

**File:** `src/compare_classical.py:141-142`

**Issue:** The SVD preprocessor (used by `histgbm_svd256`) passes literal `["kind", "alignment", "style"]` and `["bold_ratio"]` to the ColumnTransformer instead of the imported `CAT_COLS` and `NUM_COLS` config constants. The sibling function `_build_preprocess()` (lines 112-113) correctly uses the config constants. If `CAT_COLS` or `NUM_COLS` change in `src/config.py`, `_build_preprocess()` will pick up the change automatically but `_build_tfidf_svd_preprocess` will silently diverge — the HistGBM model will train on different structural features than all other zoo models, and no error will be raised (ColumnTransformer silently drops unknown columns via `remainder='drop'`).

**Fix:**
```python
# src/compare_classical.py:141-142 — replace hardcoded literals with config constants:
return ColumnTransformer(
    transformers=[
        ("text", tfidf_svd, TEXT_COL),
        ("cat", cat_transformer, CAT_COLS),   # was ["kind", "alignment", "style"]
        ("num", num_transformer, NUM_COLS),   # was ["bold_ratio"]
    ],
    remainder="drop",
)
```
`CAT_COLS` and `NUM_COLS` are already imported at the top of the file (line 35).

---

## Low Issues

### L-01: Stale `0.9414` threshold in `test_per_model_metric_floor` docstring contradicts the assertion

**File:** `tests/test_compare_classical_acceptance.py:104`

**Issue:** The docstring for `test_per_model_metric_floor` reads `"clears Phase 8 SC-2 floor (weighted_f1 >= 0.94 AND macro_f1 >= 0.9414)"`. The actual assertion on line 135 correctly uses `SC2_MACRO_F1_FLOOR = 0.86`. The docstring is a misleading dead reference to the pre-OQ-5 floor. Test reliability is unaffected, but it will confuse a future reader diagnosing a test failure.

**Fix:** Update the docstring to match the actual assertion:
```python
"""
D-D-04 gate 3: every row weighted_f1 > 0.5; linear_svm_production row
clears Phase 8 SC-2 floor (weighted_f1 >= 0.94 AND macro_f1 >= 0.86).
FULL dataset run — marked slow, skipped in fast CI.
"""
```

---

## Skipped (out of scope)

- `prod_inner` classifier object (original `LinearSVC` from `build_pipeline()`) is orphaned after line 175 — this is correct by design; no concern.
- `_build_tfidf_svd_preprocess` vs `_build_preprocess` code duplication — both are short and the SVD variant genuinely differs in the text leg; not a refactor target per CLAUDE.md.
- `_find_latest_zoo_csv()` in `test_phase_8_sc2_acceptance.py` uses `reverse=True` sort on glob paths — relies on the `classical_zoo_YYYYMMDD_HHMMSS` timestamp prefix sorting lexicographically as chronologically, which is correct.
- Makefile tab indentation: verified correct (all recipe lines start with `\t`).
- Makefile `$$(date +%Y%m%d_%H%M%S)` escaping: correctly double-`$` for Make, expands to a single `$` in the recipe shell.
- Trailing slash on `--output-dir results/reports/classical_zoo_.../`: `Path(...).resolve()` strips it correctly.
- `sys.exit(exit_code)` in `main.py:664` vs `return` pattern for other subcommands: this is intentional (compare-classical returns a non-zero exit code on model failure); consistent with D-E-02.
- `precision_recall_fscore_support` called twice (macro + weighted) in `_calc_metrics`: minor redundancy, not a bug.

---

_Reviewed: 2026-05-15_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
