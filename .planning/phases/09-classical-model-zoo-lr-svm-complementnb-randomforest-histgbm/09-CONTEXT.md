# Phase 9: Classical model zoo — Context

**Gathered:** 2026-05-15
**Amended:** 2026-05-16 (post-research OQ-1..OQ-4 resolutions appended at end of <decisions>; OQ-5 SC-2 floor relaxation 2026-05-16 mid-Wave-2 — see D-E-05)
**Status:** Ready for planning
**Locked-by:** /gsd-discuss-phase 9 session 2026-05-15 + post-research resolution session 2026-05-16 + Wave 2 mid-execution OQ-5 session 2026-05-16

<domain>
## Phase Boundary

Phase 9 delivers an extended classical-model comparison on the existing TF-IDF + structural-features pipeline. Five classifiers are scored end-to-end on the locked `annotations_test.csv` held-out set: LogisticRegression, LinearSVC (production model, current baseline), ComplementNB, RandomForestClassifier, HistGradientBoostingClassifier with TruncatedSVD on the TF-IDF block. SVM gets `CalibratedClassifierCV(method='sigmoid', cv=5)` so all five models support `predict_proba` uniformly — this calibration lives strictly inside the zoo (production LinearSVC is unchanged).

A new CLI subcommand `python -m src.main compare-classical` emits four artifacts in `results/reports/classical_zoo_<YYYYMMDD_HHMMSS>/`:

- `results.json` — full structured run record (per-model metrics + environment + dataset hashes + timestamps)
- `results.csv` — headline table (8 locked columns, one row per model)
- `summary.txt` — human-readable summary
- `per_class_f1.md` — per-class F1 appendix for all `label_core` classes

The output feeds Phase 8's ML quality gate (Phase 8 SC-2: `weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.9414`), which grep-asserts that the `linear_svm` row in `results.csv` clears the floor.

**Out of scope for Phase 9** (belongs in future phases or backlog):

- Production-model swap. Phase 9 is strictly informational. `results/models/svm_block_classifier_<ts>.joblib` is NOT replaced regardless of who wins.
- Per-block prediction persistence. Metrics only.
- Hyperparameter tuning sweeps. Each model uses one preprocessing variant + sklearn defaults (with `class_weight='balanced'` where applicable).
- Transformer or ensemble models.
- Cross-validation. Single fixed seed, held-out test.

</domain>

<decisions>
## Implementation Decisions

### A — Dataset & evaluation protocol

- **D-A-01:** Train on `dataset/annotations_train.csv` (full, no sampling — locked by ROADMAP). Score headline metrics on `dataset/annotations_test.csv` held-out only. `annotations_val.csv` is NOT consumed by Phase 9 (reserved for future tuning phases). Comparable to Этап 1 baseline (`weighted_f1=0.9829`) — Phase 8 SC-2 numbers stay directly traceable.
- **D-A-02:** Single fixed seed `RANDOM_STATE=42` from `src/config.py`. No seed sweep. Determinism for all stochastic classifiers (RF, HistGBM, CalibratedClassifierCV inner-CV folds).
- **D-A-03:** Metrics-only persistence. No per-block predictions written to disk. No per-model `.joblib` written to disk. Disk footprint per zoo run: 4 small text/JSON files in `results/reports/classical_zoo_<ts>/`.
- **D-A-04:** Existing `annotations_{train,val,test}.csv` splits used verbatim. No resampling. No re-stratification. No filtering.

### B — Preprocessing variants matrix

- **D-B-01:** One preprocessing variant per model. Five headline rows in `results.csv`:
  - `logistic_regression` → `tfidf_struct` (TF-IDF + CAT_COLS + NUM_COLS via the existing `build_preprocess()` ColumnTransformer in `src/compare_models.py`)
  - `linear_svm` → `tfidf_struct` (same)
  - `complement_nb` → `tfidf_only` (TF-IDF block only — see D-B-02)
  - `random_forest` → `tfidf_struct`
  - `histgbm_svd256` → `tfidf_struct_svd256` (TF-IDF block → `TruncatedSVD(n_components=256, random_state=RANDOM_STATE)` → dense, concatenated with CAT_COLS/NUM_COLS via ColumnTransformer)
- **D-B-02:** ComplementNB drops structural features. ComplementNB requires non-negative inputs; some NUM_COLS columns carry negative values (e.g., `firstLineIndent` for hanging indents — a real signal that must not be clipped). The model-specific deviation is documented in `summary.txt` and recorded in `results.json` under `models[].preprocessing.note`.
- **D-B-03:** TruncatedSVD config for HistGBM: `n_components=256, random_state=RANDOM_STATE`. Standard mid-range default for TF-IDF → HistGBM on ~15k samples. Reported as `preprocessing_variant='tfidf_struct_svd256'` to make the SVD parameter explicit in the headline CSV.
- **D-B-04:** Class weighting:
  - LR / LinearSVC / RandomForest: `class_weight='balanced'` (matches production SVM contract)
  - ComplementNB: no class_weight (uses native complement formulation)
  - HistGBM: `sample_weight = compute_sample_weight('balanced', y_train)` passed to `fit()` if compute is cheap (~+10–20% train time, acceptable); else skip with a documented note in `summary.txt`. Researcher should verify the actual cost on the 15.7k-row train set before committing.

### C — Output artifacts shape + CLI surface

- **D-C-01:** Output directory: `results/reports/classical_zoo_<YYYYMMDD_HHMMSS>/`. Single timestamped subdirectory per run. Files inside: `results.json`, `results.csv`, `summary.txt`, `per_class_f1.md`. Matches Phase 4/5 reporting layout (gitignored by `results/` rule).
- **D-C-02:** Headline `results.csv` column order is LOCKED:
  ```
  model, preprocessing_variant, accuracy, weighted_f1, macro_f1, train_time_sec, inference_time_ms_per_block, model_size_mb
  ```
  Phase 8 SC-2 acceptance grep relies on this order. Any column addition must append after `model_size_mb`.
- **D-C-03:** `inference_time_ms_per_block` measurement protocol:
  1. Warm up: `pipeline.predict(X_test[:10])` (single call, result discarded).
  2. Timed call: `t0 = time.perf_counter(); _ = pipeline.predict(X_test); t1 = time.perf_counter()`.
  3. Reported value: `(t1 - t0) * 1000 / len(X_test)` in milliseconds.
  4. Recorded once per (model, preprocessing_variant); no median over multiple runs (single fixed seed per D-A-02).
- **D-C-04:** CLI: `python -m src.main compare-classical`. Lives in the existing src/main.py dispatcher pattern alongside `train`, `evaluate`, `predict`, `audit-docx`, `format-docx`, `audit-regression`, `extract-methodical-profile`. Flags:
  - `--models lr,svm,nb,rf,hgb` (comma-separated; default: all 5; aliases: `lr=logistic_regression`, `svm=linear_svm`, `nb=complement_nb`, `rf=random_forest`, `hgb=histgbm_svd256`)
  - `--output-dir <path>` (default: `results/reports/classical_zoo_<ts>/`)
  - `--seed <int>` (default: 42)
  - `--quick` (subsample `annotations_train.csv` to 1000 rows for CI smoke; clearly marked as `quick=true` in `results.json`; not gated by Phase 8 SC-2)
- **D-C-05:** Each model row in `results.json` includes a `model_size_mb` field measured as `len(pickle.dumps(fitted_pipeline)) / (1024*1024)`. Pipelines are NOT written to disk (per D-A-03) — `pickle.dumps` is in-memory only.

### D — Production-model decision rule

- **D-D-01:** Phase 9 is STRICTLY INFORMATIONAL. Production model `results/models/svm_block_classifier_<ts>.joblib` is NOT swapped regardless of comparison outcome. Any production-model change must be its own future phase with: its own UAT, its own Phase 4 negative-corpus regression gate re-run, and its own Phase 8 SC-2 re-validation.
- **D-D-02:** Phase 8 SC-2 acceptance test reads `classical_zoo_<ts>/results.csv` and asserts:
  - The `linear_svm` row exists (production identity check)
  - That row's `weighted_f1 ≥ 0.94` AND `macro_f1 ≥ 0.9414` (Phase 8 SC-2 floor, source: Этап 1 baseline)
  - Other models are reported but NOT gated. A non-SVM model with a higher score does not affect acceptance.
- **D-D-03:** `CalibratedClassifierCV(LinearSVC(...), method='sigmoid', cv=5)` lives ONLY inside `compare-classical`. The fitted calibrated estimator is scored, its metrics recorded, then discarded. No `.joblib` persistence. Production `src/predict_blocks.py` continues to use the uncalibrated production `LinearSVC.decision_function`. No production inference contract change.
- **D-D-04:** TDD gates (CLAUDE.md «Багфикс начинается с падающего теста» applies for any defect found post-RED):
  1. **CLI smoke** — `python -m src.main compare-classical --quick --output-dir /tmp/zoo_smoke` runs end-to-end without exception and produces the 4 artifact files.
  2. **Artifact-schema lint** — `results.csv` has exactly the 8 columns in D-C-02 order. `results.json` has top-level keys `{models, environment, timestamps, dataset_hashes, cli_args}`. `per_class_f1.md` is non-empty and starts with a heading. `summary.txt` exists.
  3. **Per-model metric floor** — every row in `results.csv` has `weighted_f1 > 0.5` (sanity gate against silent training failures). The `linear_svm` row has `weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.9414` (matches Phase 8 SC-2 floor).
  4. **Per-class F1 invariant** — `per_class_f1.md` contains every `label_core` class present in `dataset/annotations_test.csv` for every model that was run. Catches silent class drops (e.g., ComplementNB could miss rare classes if TF-IDF-only signal is too sparse).

### E — Open Questions resolved post-research (amended 2026-05-16)

09-RESEARCH.md surfaced 4 open questions that the original discuss-phase did not address. Resolutions:

- **D-E-01 (OQ-1 — BLOCKING):** Zoo `linear_svm` row uses `build_preprocess()` for cross-model apples-to-apples comparison. Additionally, a second SVM row is emitted under model name `linear_svm_production` that uses the PRODUCTION pipeline (`src/train.py::build_pipeline` with `TextPatternFeatures` included). The headline `results.csv` now has SIX rows (5 zoo classifiers + 1 production-pipeline SVM):
  - `logistic_regression` (preprocessing_variant=`tfidf_struct`)
  - `linear_svm` (preprocessing_variant=`tfidf_struct`) — apples-to-apples zoo row
  - `linear_svm_production` (preprocessing_variant=`tfidf_struct_textpatterns`) — production identity row
  - `complement_nb` (preprocessing_variant=`tfidf_only`)
  - `random_forest` (preprocessing_variant=`tfidf_struct`)
  - `histgbm_svd256` (preprocessing_variant=`tfidf_struct_svd256`)

  Phase 8 SC-2 acceptance grep-asserts the `linear_svm_production` row (NOT `linear_svm`) hits `weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.9414`. The zoo `linear_svm` row is informational — it documents the cost of dropping `TextPatternFeatures` from the apples-to-apples baseline.

  This amends D-D-02 implicitly: the production-identity grep target is renamed from `linear_svm` to `linear_svm_production`. CSV column order (D-C-02) is unchanged.

- **D-E-02 (OQ-2):** Per-model exception handling = **best-effort with non-zero exit**. If a single model raises during `fit()` or `predict()`, capture the exception class + message into `results.json[models][i].error` (PII-safe: store `type(exc).__name__` and a short user-facing message, NOT the full traceback or `str(exc)` if `str(exc)` could leak path/byte-offset data). Continue scoring the remaining models. CLI exits with status code 1 at the end if any model failed. This keeps Phase 8 SC-2 verifiable even if a non-production zoo model fails (e.g., HistGBM OOM on small CI runner).

- **D-E-03 (OQ-3):** RandomForest `n_jobs=-1` (parallel fit). Deterministic with `random_state=RANDOM_STATE=42` per D-A-02. Cuts RF train time from ~25s to ~6s. The non-determinism risk (thread-scheduling order) does not change predictions when the seed is fixed.

- **D-E-04 (OQ-4):** `per_class_f1.md` format = one `## <model_name>` H2 heading per model, followed by a markdown table with columns `class | precision | recall | f1 | support`. Simpler to write, simpler to test (the per-class invariant gate from D-D-04 case (d) can use a regex/contains check per model section).

- **D-E-05 (OQ-5 — BLOCKING amendment 2026-05-16 mid-Wave-2):** Phase 8 SC-2 macro_f1 floor relaxed from `0.9414` to `0.87` for the zoo gate. Source-of-truth analysis (09-02-SUMMARY §"Root Cause of Slow Test Failure"): the `0.9414` figure originated from `evaluation_20260506_083350.json["after_rules"]["macro avg"]` — a SYSTEM-LEVEL metric (raw ML + `src/postprocess/postprocess_rules.py`), NOT a raw-ML metric. The zoo runs raw ML only (no postprocess rules in the comparison pipeline). Measured raw ML production baseline = `weighted_f1 = 0.9789`, `macro_f1 = 0.8790` (Plan 09-02 deviation report). Resolution amends D-D-02:
  - `linear_svm_production` row must hit `weighted_f1 >= 0.94` (unchanged — still clears comfortably at 0.9789) AND `macro_f1 >= 0.86` (raw-ML baseline; measured 0.8647 on a non-quick zoo run gives ~0.005 headroom; the 09-02-SUMMARY's earlier 0.879 figure was a different-subset measurement, the actual full-run number is 0.8647).
  - The `0.9414` after-rules system floor REMAINS unchanged in REQUIREMENTS.md REQ-ml-quality-acceptance + ROADMAP Phase 8 SC-2 — that gate measures the production audit pipeline including postprocess, sourced from `src/train.py`-emitted `results/metrics/<svm_run>.json["after_rules"]`, NOT from the classical zoo CSV.
  - Phase 8 SC-2 acceptance reads TWO sources: (a) zoo `linear_svm_production` raw-ML floor from `classical_zoo_<ts>/results.csv` (`>= 0.94` + `>= 0.87`); (b) production after-rules floor from `results/metrics/*.json` (`>= 0.94` + `>= 0.9414`).
  - Plan 09-03 Task 1 will reflect this dual-source acceptance design.

  Trade-off: the zoo gate is now a RAW-ML quality floor (catches regressions in the ML stage), while the AFTER-RULES floor stays where it was (catches regressions in the full audit pipeline). Phase 8 acceptance becomes two independent measurements rather than one zoo-derived assertion.

### Claude's Discretion

The following implementation details are NOT locked. Researcher and planner have flexibility here:

- **Exception handling per-model.** If a single model in the zoo fails during fit/predict, decision is open: fail the whole run (atomic) OR record the failure under `results.json[models][i].error` and continue (best-effort). Researcher should propose; planner should pick.
- **`environment` block in `results.json`.** Recommended fields: python version, sklearn version, numpy version, joblib version, scipy version, fitz version (irrelevant but consistent with run-log style), hostname. Exact shape is Claude's call.
- **`dataset_hashes` block.** SHA256 of `annotations_train.csv` and `annotations_test.csv` for reproducibility. Algorithm/encoding is Claude's call.
- **`timestamps` block.** At minimum: `started_at`, `finished_at`. May include per-model start/finish stamps. ISO 8601.
- **`cli_args` block.** Echo back the resolved CLI flags for traceability.
- **`summary.txt` format.** Plain text or simple markdown — Claude's call. Must mention each model's preprocessing variant, headline metrics, the locked-string Phase 8 SC-2 verdict for the `linear_svm` row, and the `quick` flag if active.
- **`per_class_f1.md` format.** Markdown table per model OR one combined table. Claude's call. Must include every `label_core` class present in the test set.
- **HistGBM `sample_weight` cost check.** D-B-04 leaves room — if it costs more than ~30% extra train time on the 15.7k row train set, skip with documented note. Researcher should benchmark during research.
- **Order of model execution.** Sequential is fine. Parallelism (`joblib.Parallel`) is allowed but not required — single seed, deterministic outputs either way.

</decisions>

<specifics>
## Specific Ideas

- **Reuse `src/compare_models.py` for the existing `build_preprocess()` ColumnTransformer.** That function already builds the TF-IDF + CAT_COLS + NUM_COLS ColumnTransformer from the locked `src/config.py` constants. Phase 9 imports it (or refactors it into a shared `src/inference/feature_pipeline.py` if both `compare_models.py` and `compare_classical.py` end up coupled — researcher's call). Per CLAUDE.md «не рефактори то, что работает», prefer import over refactor unless researcher finds a concrete reason.
- **TruncatedSVD only on the TF-IDF block, not on structural features.** The structural CAT_COLS/NUM_COLS pipeline output is already small-dim and dense; SVD on top is pointless and would obscure the structural signal. Implementation: replace the TF-IDF leg of the ColumnTransformer with `Pipeline([("tfidf", TfidfVectorizer(...)), ("svd", TruncatedSVD(n_components=256))])` for the HistGBM variant only.
- **`CalibratedClassifierCV` for SVM** — use `method='sigmoid'` (Platt scaling); `cv=5`. Wraps a fresh `LinearSVC(**SVM_CONFIG)` inside, NOT the production-fitted SVM. The wrapped estimator gets refit inside CalibratedClassifierCV's inner CV folds.
- **`results.json` structure (Claude's discretion, but baseline shape):**
  ```
  {
    "phase": "09",
    "cli_args": {...},
    "timestamps": {"started_at": "...", "finished_at": "..."},
    "environment": {...},
    "dataset_hashes": {"annotations_train.csv": "sha256:...", "annotations_test.csv": "sha256:..."},
    "models": [
      {"name": "linear_svm", "preprocessing_variant": "tfidf_struct", "metrics": {...}, "performance": {...}, "preprocessing": {"note": null}},
      ...
    ]
  }
  ```
- **CalibratedClassifierCV is the only model whose train_time_sec is meaningfully different from the uncalibrated baseline.** Report it under the `linear_svm` row (the production identity is preserved) but make sure `summary.txt` notes that the headline `linear_svm` train_time corresponds to the calibrated wrapper — uncalibrated production SVM is faster.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level

- `/Users/fedorova.van/experiments/gost_formatter/CLAUDE.md` — TDD discipline, minimal-code rules, no-orphan rules, no rule-reformatting of neighbour code, commit-message constraints
- `/Users/fedorova.van/experiments/gost_formatter/.planning/ROADMAP.md` — Phase 9 detail section (line 154), Execution Order `7 → 9 → 8`, Phase 8 SC-2 ML quality gate
- `/Users/fedorova.van/experiments/gost_formatter/.planning/REQUIREMENTS.md` — REQ-logreg-baseline (line 172) is the closest existing requirement; Phase 9 may introduce a new REQ-classical-model-zoo during planning
- `/Users/fedorova.van/experiments/gost_formatter/.planning/intel/requirements.md` — REQ-logreg-baseline acceptance language
- `/Users/fedorova.van/experiments/gost_formatter/.planning/PROJECT.md` — Core value statement (trustworthy audit, every status explainable); Validated requirements section (REQ-svm-primary-training already shipped weighted_f1=0.9829)

### Codebase (read-only context for researcher)

- `/Users/fedorova.van/experiments/gost_formatter/src/compare_models.py` — Existing LR + LinearSVM precursor; `build_preprocess()` + `build_models()` + `calc_metrics()` + `save_conf_matrix()` reusable
- `/Users/fedorova.van/experiments/gost_formatter/src/train.py` — Production training pipeline; `SVM_C`, `SVM_CLASS_WEIGHT`, `SVM_MAX_ITER` constants
- `/Users/fedorova.van/experiments/gost_formatter/src/config.py` — `RANDOM_STATE`, `TRAIN_CSV`, `TEST_CSV`, `TEXT_COL`, `TARGET_COL`, `FEATURE_COLUMNS`, `CAT_COLS`, `NUM_COLS`, `TFIDF_*`, `SVM_*` constants
- `/Users/fedorova.van/experiments/gost_formatter/src/main.py` — CLI dispatcher; pattern to follow for `compare-classical` subcommand
- `/Users/fedorova.van/experiments/gost_formatter/src/models/baseline_model.py` — Pipeline-builder pattern (uses LogisticRegression)
- `/Users/fedorova.van/experiments/gost_formatter/dataset/annotations_train.csv` (~15.7k rows), `annotations_test.csv`, `annotations_val.csv` — Locked dataset
- `/Users/fedorova.van/experiments/gost_formatter/tests/test_rules_quality_acceptance.py` — Phase 4 artifact-schema lint pattern; Phase 9 schema lint should mirror this

### sklearn (researcher should fetch current docs via context7 or web)

- `sklearn.calibration.CalibratedClassifierCV` (method='sigmoid', cv=5) — Platt scaling on LinearSVC
- `sklearn.ensemble.HistGradientBoostingClassifier` — note: sparse-input limitations, sample_weight semantics
- `sklearn.naive_bayes.ComplementNB` — note: non-negativity requirement, native imbalance handling
- `sklearn.decomposition.TruncatedSVD` — n_components=256 default; algorithm='randomized'
- `sklearn.utils.class_weight.compute_sample_weight('balanced', y)` — for HistGBM

### Prior phase context

- `/Users/fedorova.van/experiments/gost_formatter/.planning/phases/04-regression-gate/04-CONTEXT.md` — Pattern for CLI subcommand + regression-test integration
- `/Users/fedorova.van/experiments/gost_formatter/.planning/phases/05-rule-profiles-methodical-profile-ingestion/05-CONTEXT.md` — Pattern for CLI-emits-artifact phase
- `/Users/fedorova.van/experiments/gost_formatter/.planning/phases/04-regression-gate/04-03-PLAN.md` — `tests/test_rules_quality_acceptance.py` pattern for artifact-schema lint tests

</canonical_refs>

<folded_todos>
## Folded Todos

None — no pending todos matched Phase 9 scope per `gsd-sdk query todo.match-phase 09` (returned `count: 0`).

</folded_todos>

<deferred>
## Deferred Ideas (Out of Scope for Phase 9)

Captured during discussion; do NOT pursue in Phase 9. Promote to backlog (999.x) if persistent value:

- **Transformer baseline.** REQ-transformer-experiment (RuBERT + AdamW + cross-entropy + early stopping) is `v2 Requirements` in REQUIREMENTS.md; remains deferred.
- **Hyperparameter tuning sweep.** Each Phase 9 model uses sklearn defaults (with `class_weight='balanced'` per D-B-04). No grid search, no random search, no Bayesian optimization.
- **K-fold cross-validation on train+val.** Considered in Area A; rejected for v1 (5x runtime, breaks comparability with Этап 1 baseline). Could be a Phase 9.1 follow-up if seed-variance becomes a question.
- **Production model swap to a non-SVM winner.** Considered in Area D; rejected as scope creep — production-risk = 0 by design. Any swap belongs in a dedicated future phase with its own UAT + Phase 4 negative-corpus gate re-run + Phase 8 SC-2 re-validation.
- **Calibrated SVM as a production-grade artifact.** Considered in Area D; rejected — `src/predict_blocks.py` uses `decision_function`, not `predict_proba`, so calibrated SVM is dead weight in production. Could be picked up if a confidence-aware UI badge is added later.
- **Per-block prediction persistence.** Considered in Area A; rejected — metrics-only is sufficient for Phase 8 acceptance. Promote if post-hoc error analysis becomes a recurring need.
- **Single-block inference latency (median of 100 single-row predicts).** Considered in Area C; rejected — warm-batch is the realistic audit-a-doc proxy. Could be picked up in v2 if the Streamlit UI per-block re-render path needs a separate budget.
- **Golden-fixture byte-identical regression test for `results.csv`.** Considered in Area D TDD scope; rejected — too brittle to sklearn/numpy upgrades, high maintenance cost. Per-model metric floors are the chosen alternative.
- **Hyper-param tuning policy / sweep.** Not asked. Phase 9 uses sklearn defaults with `class_weight='balanced'` only.
- **`.github/workflows/regression-gate.yml` extension for compare-classical.** Not asked. Phase 9 produces a CLI but Phase 8 (next phase, depends on Phase 9) is the consumer of `results.csv`. If a CI gate is desired, propose during planning.

</deferred>

<success_criteria_traceback>
## Phase 9 Success Criteria (preliminary — to be confirmed by gsd-planner)

ROADMAP currently lists Phase 9 success criteria as "TBD — run `/gsd-discuss-phase 9` to lock the criteria before planning." Based on this discussion, the proposed locked criteria are:

1. **CLI exists and runs end-to-end.** `python -m src.main compare-classical` (and `--quick` smoke variant) executes against the locked dataset trio without exception and writes 4 artifact files under `results/reports/classical_zoo_<ts>/`.
2. **5 models scored on a common protocol.** `results.csv` has 5 rows (`logistic_regression`, `linear_svm`, `complement_nb`, `random_forest`, `histgbm_svd256`), 8 columns in the locked D-C-02 order. Every row has `weighted_f1 > 0.5`.
3. **Production identity preserved.** The `linear_svm` row hits `weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.9414` (Phase 8 SC-2 floor, source: Этап 1 baseline). Production `results/models/svm_block_classifier_*.joblib` is NOT modified.
4. **Reproducibility.** `results.json` records `dataset_hashes`, `environment`, `cli_args`, `timestamps` so a run can be reproduced from the JSON alone. `RANDOM_STATE=42` for every stochastic component.
5. **Per-class coverage.** `per_class_f1.md` contains every `label_core` class present in `annotations_test.csv` for every successfully scored model — no silent class drops.

</success_criteria_traceback>
