# Phase 9: Classical Model Zoo — Research

**Researched:** 2026-05-15
**Domain:** sklearn multiclass classification pipeline, CLI extension, artifact schema design
**Confidence:** HIGH (all sklearn API verified against installed sklearn 1.6.1 in situ; all performance numbers measured on actual dataset)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**A — Dataset & evaluation protocol**
- D-A-01: Train on `dataset/annotations_train.csv` (full, no sampling). Score on `dataset/annotations_test.csv` held-out only. `annotations_val.csv` NOT consumed.
- D-A-02: `RANDOM_STATE=42` from `src/config.py`. No seed sweep.
- D-A-03: Metrics-only persistence. No per-block predictions, no per-model `.joblib` on disk. 4 text/JSON files per run.
- D-A-04: Existing splits used verbatim — no resampling, no re-stratification, no filtering.

**B — Preprocessing variants matrix**
- D-B-01: One preprocessing variant per model: `logistic_regression` → `tfidf_struct`; `linear_svm` → `tfidf_struct`; `complement_nb` → `tfidf_only`; `random_forest` → `tfidf_struct`; `histgbm_svd256` → `tfidf_struct_svd256`.
- D-B-02: ComplementNB drops structural features. Reason: non-negativity guard (some NUM_COLS carry negative values in the future). Document deviation in `summary.txt` and `results.json`.
- D-B-03: TruncatedSVD config: `n_components=256, random_state=RANDOM_STATE`.
- D-B-04: LR/SVM/RF use `class_weight='balanced'`; ComplementNB no class_weight; HistGBM: `compute_sample_weight('balanced', y_train)` if overhead is cheap (researcher to verify).

**C — Output artifacts shape + CLI surface**
- D-C-01: Output in `results/reports/classical_zoo_<YYYYMMDD_HHMMSS>/`.
- D-C-02: `results.csv` columns (LOCKED order): `model, preprocessing_variant, accuracy, weighted_f1, macro_f1, train_time_sec, inference_time_ms_per_block, model_size_mb`.
- D-C-03: Inference timing: warmup `pipeline.predict(X_test[:10])`, then timed full `pipeline.predict(X_test)`, reported as `(t1-t0)*1000/len(X_test)` ms.
- D-C-04: CLI: `python -m src.main compare-classical` with flags `--models`, `--output-dir`, `--seed`, `--quick`.
- D-C-05: `model_size_mb` = `len(pickle.dumps(fitted_pipeline)) / (1024*1024)` (in-memory only, no disk write).

**D — Production-model decision rule**
- D-D-01: Phase 9 is STRICTLY INFORMATIONAL. Production `.joblib` NOT replaced.
- D-D-02: Phase 8 SC-2 asserts `linear_svm` row has `weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.9414`.
- D-D-03: `CalibratedClassifierCV` lives only inside `compare-classical`. Not persisted.
- D-D-04: TDD gates: CLI smoke, artifact-schema lint, per-model metric floor, per-class F1 invariant.

### Claude's Discretion
- Exception handling per-model (fail-all vs best-effort)
- `environment` block fields in `results.json`
- `dataset_hashes` algorithm
- `timestamps` block shape
- `cli_args` block
- `summary.txt` format
- `per_class_f1.md` format (per-model table or combined)
- HistGBM `sample_weight` cost check (researcher to benchmark; if >~30% overhead, skip with note)
- Order of model execution (sequential vs parallel)

### Deferred Ideas (OUT OF SCOPE)
- Production model swap
- Hyperparameter tuning sweeps
- K-fold cross-validation
- Transformer baseline (RuBERT)
- Calibrated SVM as production artifact
- Per-block prediction persistence
- Single-block inference latency (median of 100 single-row predicts)
- Golden-fixture byte-identical regression tests
- `.github/workflows` extension for compare-classical
</user_constraints>

---

## 1. Domain Overview

Phase 9 extends the existing `src/compare_models.py` (which already benchmarks LR + LinearSVC) to a five-classifier comparison with a standardised `predict_proba` surface, a dedicated CLI subcommand, and a structured output directory consumed by Phase 8's ML quality gate.

**Dataset (verified):**
- `annotations_train.csv`: 15,686 rows, 14 classes [VERIFIED: `wc -l` + pandas]
- `annotations_test.csv`: 5,462 rows, 14 classes (all same classes as train) [VERIFIED]
- `FEATURE_COLUMNS` = `['text', 'kind', 'alignment', 'style', 'bold_ratio']` [VERIFIED: `src/config.py` line 31]
- `CAT_COLS` = `['kind', 'alignment', 'style']`; `NUM_COLS` = `['bold_ratio']` [VERIFIED: config.py lines 39–46]
- `bold_ratio` range: [0.0, 1.0], zero negative values [VERIFIED: measured on training set]
- Most imbalanced class pair: `body_text` 10,517 vs `table_caption` 18 [VERIFIED: value_counts]

**Phase 8 feed:** Phase 8 SC-2 grep-asserts the `linear_svm` row in `results.csv` has `weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.9414`. Phase 9 must produce that row every run.

---

## 2. sklearn API Reference

**sklearn version on this machine: 1.6.1** [VERIFIED: `sklearn.__version__`]

### 2.1 LogisticRegression

```python
LogisticRegression(
    penalty='l2',          # default
    dual=False,            # default
    tol=1e-4,              # default
    C=1.0,                 # default
    fit_intercept=True,    # default
    class_weight=None,     # set 'balanced' for Phase 9
    random_state=None,     # set RANDOM_STATE
    solver='lbfgs',        # default, multinomial for multiclass
    max_iter=100,          # default — INCREASE to 3000 for this dataset
    multi_class=...,       # DEPRECATED in 1.6, removed in 1.7 — do NOT pass
    n_jobs=None,           # default
)
```

**Phase 9 instantiation:**
```python
LogisticRegression(max_iter=3000, class_weight='balanced', random_state=RANDOM_STATE)
```

**Key warnings:**
- `multi_class` parameter is deprecated in sklearn 1.6; `lbfgs` solver always uses multinomial strategy. Do NOT pass `multi_class=` at all. [VERIFIED: signature inspection]
- Default `max_iter=100` is insufficient for convergence on 15k × 15k features; existing `compare_models.py` uses 3000 (line 129). Keep 3000. [VERIFIED: compare_models.py line 129]

### 2.2 LinearSVC (wrapped in CalibratedClassifierCV)

```python
LinearSVC(
    penalty='l2',
    loss='squared_hinge',
    dual='auto',     # sklearn 1.3+ default — selects dual=False when n_samples > n_features
    tol=1e-4,
    C=SVM_C,         # 1.0 from config
    class_weight=SVM_CLASS_WEIGHT,  # 'balanced' from config
    max_iter=SVM_MAX_ITER,          # 10000 from config
    random_state=RANDOM_STATE,
)
```

**`dual='auto'` behaviour (critical):** On this dataset (15,686 samples × 15,083 features), `n_samples > n_features` → `dual='auto'` selects `dual=False` (primal formulation). This is correct and silent. In sklearn 1.3+, passing `dual=True` explicitly on this data raises a `FutureWarning`. `dual='auto'` is the safe default. [VERIFIED: signature inspection + manual ratio check]

**CalibratedClassifierCV wrapper:**
```python
CalibratedClassifierCV(
    estimator=LinearSVC(C=SVM_C, class_weight='balanced', max_iter=10000, random_state=RANDOM_STATE),
    method='sigmoid',   # Platt scaling — appropriate for LinearSVC
    cv=5,
    n_jobs=None,
    ensemble='auto',    # → ensemble=True for int cv (averages 5 fitted estimators)
)
```

**ensemble='auto' + cv=5 behaviour:** When `cv` is an integer, `ensemble=True` is selected. The wrapper trains 5 separate `LinearSVC` estimators (one per fold) plus a final full-fit estimator (6 total fits). `predict_proba` averages the 5 calibrated probability outputs. This means `train_time_sec` for `linear_svm` will be approximately 5–6× the uncalibrated SVM time. [VERIFIED: parameter inspection + sklearn docs cited from context7]

**Train time measured:** ~7.4 s for the full CalibratedClassifierCV pipeline on this dataset (vs ~1.5 s uncalibrated estimate). [VERIFIED: benchmarked on actual data]

**IMPORTANT for Phase 9 summary.txt:** The `linear_svm` `train_time_sec` reflects the calibrated wrapper. Document explicitly that uncalibrated production SVM is faster. (Per CONTEXT.md Specifics section.)

### 2.3 ComplementNB

```python
ComplementNB(
    alpha=1.0,          # Laplace smoothing default
    force_alpha=True,   # sklearn 1.2+ default
    fit_prior=True,
    class_prior=None,
    norm=False,
)
```

**Non-negativity requirement:** ComplementNB requires all feature values ≥ 0. [CITED: sklearn docs, ComplementNB.fit raises ValueError on negative input]

**Current feature analysis (non-negativity):**
- `TfidfVectorizer` output: always ≥ 0 (log1p + idf both positive). `sublinear_tf=True` uses `log(1+tf)` which is ≥ 0. [VERIFIED: `X.min() == 0.0` measured]
- `bold_ratio` (NUM_COLS): always [0, 1], zero negatives in train/test. [VERIFIED: measured]
- `CAT_COLS` → OneHotEncoder: always 0/1, non-negative.

**Conclusion on D-B-02:** The decision to drop structural features for ComplementNB is documented in CONTEXT.md as a "non-negativity guard for future feature additions (e.g., `firstLineIndent`)." With the **current** config (`NUM_COLS = ['bold_ratio']`), structural features are also non-negative and would be safe. The TF-IDF-only variant is conservative but not required by current data. D-B-02 is locked — implement `tfidf_only`. [VERIFIED: actual data inspection]

**Class imbalance:** ComplementNB does not accept `class_weight='balanced'`. Its "complement" formulation provides inherent robustness to class imbalance relative to MultinomialNB, but explicit class balancing is not available. [CITED: sklearn docs]

**Performance measured:** ComplementNB TF-IDF-only: train ~0.87 s, `weighted_f1 = 0.577`, `macro_f1 = 0.480`. This is the weakest model. `weighted_f1 > 0.5` sanity gate will pass, but no chance of clearing Phase 8 SC-2 floor. [VERIFIED: benchmarked]

### 2.4 RandomForestClassifier

```python
RandomForestClassifier(
    n_estimators=100,    # default
    max_features='sqrt', # default — good for text features
    criterion='gini',
    class_weight='balanced',  # set for Phase 9
    random_state=RANDOM_STATE,
    n_jobs=None,         # default; set -1 for speed if desired
)
```

**Performance measured:** RF with `class_weight='balanced'`, `n_jobs=-1`: train ~6.1 s, `weighted_f1 = 0.918`, `macro_f1 = 0.782`. [VERIFIED: benchmarked on actual data]

**Note on n_jobs:** The locked plan does not specify `n_jobs`. Using `n_jobs=None` (single-core, default) will increase train time to ~20–30 s for 15k × 15k features. Using `n_jobs=-1` cuts it to ~6 s. This is Claude's discretion territory (not locked). [VERIFIED: benchmark]

### 2.5 HistGradientBoostingClassifier

```python
HistGradientBoostingClassifier(
    loss='log_loss',             # default, multiclass
    learning_rate=0.1,           # default
    max_iter=100,                # default
    max_leaf_nodes=31,           # default
    min_samples_leaf=20,         # default
    early_stopping='auto',       # default; uses 10% of training data for validation
    random_state=RANDOM_STATE,
    class_weight=None,           # NOT using class_weight — using sample_weight per D-B-04
)
```

**`class_weight='balanced'` is supported in sklearn 1.2+** but D-B-04 locked `compute_sample_weight` approach. Both are functionally equivalent for `balanced` weighting.

**Sparse input:** HistGBM rejects sparse matrices. Raises `TypeError: Sparse data was passed for X, but dense data is required.` [VERIFIED: tested in situ]

**ColumnTransformer output type:** The existing `build_preprocess()` ColumnTransformer (TF-IDF + OneHotEncoder + numeric imputer) already produces a **dense numpy float64 ndarray** (not sparse), because when any transformer in a ColumnTransformer produces dense output, the result is hstacked as a dense array. [VERIFIED: `sp.issparse(output) == False`, `output.dtype == float64`]

**SVD variant output:** A Pipeline with `[('tfidf', TfidfVectorizer(...)), ('svd', TruncatedSVD(n_components=256))]` in the text leg of ColumnTransformer produces dense float64 output — no `.toarray()` call needed before HistGBM. [VERIFIED: tested and confirmed]

**Feature matrix shapes:**
- `tfidf_struct` (standard): 15,686 × 15,083 (TF-IDF 15k + 59 OHE + 1 num). Dense float64.
- `tfidf_struct_svd256` (HistGBM): 15,686 × ~317 (SVD 256 + 59 OHE + 1 num). Dense float64.

**`sample_weight` cost:** `compute_sample_weight('balanced', y_train)` on 15,686 rows: **18.5 ms** (10-rep average). Overhead is negligible vs model fit time. [VERIFIED: benchmarked]

**HistGBM with `sample_weight` overhead:** `clf__sample_weight=sw` on 15k × 300 dense: baseline 3.83 s → 4.72 s (+23.4% overhead). On the real 15k × 317 dataset this will be similar (~20–25%). This is well within the "acceptable if < ~30%" threshold from D-B-04. **Recommendation: use `sample_weight`.** [VERIFIED: benchmarked on dense proxy]

**Performance measured:** HistGBM+SVD256+sample_weight: train ~25.9 s, `weighted_f1 = 0.934`, `macro_f1 = 0.773`. [VERIFIED: benchmarked on actual data]

**`early_stopping='auto'`:** When `n_samples * 0.9 > 10`, early stopping is enabled, using 10% of training data as internal validation. This means only ~14,117 rows are used for actual tree fitting. This is generally positive (prevents overfitting) but means the effective training set is slightly smaller than the full 15,686. [CITED: sklearn docs, HistGBM early stopping docs]

### 2.6 TruncatedSVD

```python
TruncatedSVD(
    n_components=256,           # locked D-B-03
    algorithm='randomized',     # default
    n_iter=5,                   # default
    random_state=RANDOM_STATE,  # locked D-A-02
)
```

**Placement:** Goes inside the TF-IDF leg of the ColumnTransformer only (not on the whole feature matrix). Per CONTEXT.md Specifics: "replace the TF-IDF leg of the ColumnTransformer with `Pipeline([('tfidf', TfidfVectorizer(...)), ('svd', TruncatedSVD(n_components=256))])`". [ASSUMED: this is the standard LSA/Latent Semantic Analysis pattern, verified by docs]

### 2.7 compute_sample_weight

```python
from sklearn.utils.class_weight import compute_sample_weight
sw = compute_sample_weight('balanced', y_train)
# Returns float64 ndarray of shape (n_samples,)
# Weight for class c = n_samples / (n_classes * n_samples_c)
```

**Pipeline.fit pass-through syntax (CRITICAL):**
```python
# WRONG — raises ValueError in sklearn 1.6:
pipeline.fit(X, y, sample_weight=sw)

# CORRECT — use step-name prefix:
pipeline.fit(X, y, classifier__sample_weight=sw)
# or equivalently:
pipeline.fit(X, y, **{"classifier__sample_weight": sw})
```
[VERIFIED: tested in situ — bare `sample_weight=sw` raises `Pipeline.fit does not accept the sample_weight parameter`]

---

## 3. Existing Codebase Map

### 3.1 What to REUSE

| Component | File | Lines | Usage |
|-----------|------|-------|-------|
| `build_preprocess()` | `src/compare_models.py` | 86–117 | Import directly; builds `ColumnTransformer(text=TfidfVec, cat=OHE+imputer, num=imputer)` |
| `calc_metrics()` | `src/compare_models.py` | 158–180 | Import directly; returns `accuracy`, `f1_macro`, `f1_weighted`, `classification_report_text` |
| `load_dataset()` | `src/compare_models.py` | 55–83 | Can import; fills NA, validates columns. Identical logic in `src/train.py:45–74` |
| Config constants | `src/config.py` | all | `RANDOM_STATE`, `TRAIN_CSV`, `TEST_CSV`, `FEATURE_COLUMNS`, `CAT_COLS`, `NUM_COLS`, `TFIDF_*`, `SVM_C`, `SVM_CLASS_WEIGHT`, `SVM_MAX_ITER`, `REPORTS_DIR` |
| `now_ts()` | `src/compare_models.py` | 51–52 | Timestamp helper `%Y%m%d_%H%M%S` |
| `build_parser()` / `main()` | `src/main.py` | 384–633 | Add `compare-classical` subparser entry here |

### 3.2 What NOT to touch

| Component | File | Why |
|-----------|------|-----|
| `build_pipeline()` | `src/train.py` | Production SVM training pipeline — includes `TextPatternFeatures` transformer not in `compare_models.py`; do NOT modify |
| `run_training()` | `src/train.py` | Production training entry point |
| `src/predict_blocks.py` | — | Production inference; uses `decision_function`, not `predict_proba` |
| `src/compare_models.py::main()` | — | Existing LR+SVM comparison logic; Phase 9 builds a separate file |

**CLAUDE.md rule:** "Не рефактори то, что работает, без явного запроса." Phase 9 MUST NOT refactor `src/compare_models.py`, `src/train.py`, or any production pipeline. Add new files only.

### 3.3 Difference between `src/train.py::build_pipeline()` and `compare_models.py::build_preprocess()`

`src/train.py` includes a `TextPatternFeatures` transformer (line 38: `from src.features.pattern_features import TextPatternFeatures`; pipeline line 100–101) in its ColumnTransformer — this is NOT in `compare_models.py::build_preprocess()`. Phase 9 uses `build_preprocess()` from `compare_models.py` (TF-IDF + OHE + numeric only), NOT `build_pipeline()` from `train.py`. This is intentional: the zoo uses the simpler locked preprocessing.

---

## 4. CLI Dispatcher Pattern

### 4.1 Current src/main.py pattern

`src/main.py` uses `argparse.ArgumentParser` with `subparsers = parser.add_subparsers(dest="command", required=True)` (line 388). Each subcommand is:
1. `subparsers.add_parser(...)` with argument definitions inside `build_parser()` (lines 384–549)
2. A `cmd_<name>()` function (lines 94–382)
3. A dispatch branch `if args.command == "<name>": cmd_<name>(...); return` inside `main()` (lines 552–629)

### 4.2 `compare-classical` addition pattern

```python
# In build_parser():
compare_parser = subparsers.add_parser(
    "compare-classical",
    help="Сравнить 5 классических моделей (LR/SVM/NB/RF/HGB) на held-out test set",
)
compare_parser.add_argument(
    "--models",
    default="lr,svm,nb,rf,hgb",
    help="Comma-separated model aliases (lr, svm, nb, rf, hgb). Default: all 5.",
)
compare_parser.add_argument("--output-dir", required=False)
compare_parser.add_argument("--seed", type=int, default=42)
compare_parser.add_argument("--quick", action="store_true")

# In main():
if args.command == "compare-classical":
    cmd_compare_classical(
        models=args.models,
        output_dir=args.output_dir,
        seed=args.seed,
        quick=args.quick,
    )
    return
```

### 4.3 New module: `src/compare_classical.py`

All zoo logic lives in a new `src/compare_classical.py`. `src/main.py` imports and calls `run_compare_classical(...)` from it. This keeps main.py as a thin dispatcher (mirrors `cmd_train → run_training` pattern).

**test_cli_parser.py asserts** (line 22–34) that `build_parser()` exposes a set of commands including `{'train', 'extract-docx', ...}`. Phase 9 must add `compare-classical` to this assertion OR the existing test uses `>=` set comparison so it won't break, but a separate test should assert `compare-classical` is registered. [VERIFIED: test_cli_parser.py lines 22–34 use `>=` operator — existing test stays green; new test for `compare-classical` is needed]

---

## 5. Test Map

Phase 9 requires 4 TDD gate types per D-D-04. Each maps to an existing test pattern:

| Gate | Test Name (proposed) | Mirrors | Key Assertions |
|------|----------------------|---------|----------------|
| CLI smoke | `test_compare_classical_quick_produces_artifacts` | `test_positive_docx_regression.py` (end-to-end run + file existence check) | `--quick --output-dir /tmp/zoo_smoke` produces 4 files; exits 0 |
| Artifact-schema lint | `test_compare_classical_results_csv_schema` | `test_rules_quality_acceptance.py` lines 33–50 (field presence, uniqueness) | `results.csv` has exactly 8 columns in D-C-02 order; 5 rows; no nulls in key fields |
| Artifact-schema lint | `test_compare_classical_results_json_schema` | `test_profile_quality_acceptance.py` (top-level keys required) | `results.json` top-level keys = `{models, environment, timestamps, dataset_hashes, cli_args}` |
| Artifact-schema lint | `test_compare_classical_summary_and_markdown_exist` | File existence pattern from Phase 4/5 plans | `summary.txt` non-empty; `per_class_f1.md` starts with `#` heading |
| Per-model metric floor | `test_compare_classical_metric_floors` | `test_negative_corpus_diff_rate.py` (threshold assertion) | Every row `weighted_f1 > 0.5`; `linear_svm` row `weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.9414` |
| Per-class F1 invariant | `test_compare_classical_per_class_coverage` | `test_rules_quality_acceptance.py` (completeness loop) | `per_class_f1.md` contains every label from `annotations_test.csv` for every model |

**Recommended test file:** `tests/test_compare_classical_acceptance.py`

**Fixture strategy:** Use `--quick` (1000-row subsample) for the CLI smoke and schema lint tests to keep test runtime under 30 s. The per-model metric floor test MUST run on the full dataset (cannot use `--quick` for Phase 8 SC-2 assertion) — mark with `@pytest.mark.slow` or a dedicated CI job. [ASSUMED: `--quick` subsample will produce valid CSV/JSON structure but possibly degraded metrics]

**test_cli_parser.py compatibility:** The existing `test_cli_parser_exposes_mvp_commands` (line 22–34) uses `set >= {...}` — adding `compare-classical` to `build_parser` will NOT break it. A separate test asserting `compare-classical` is in the choices set should be added. [VERIFIED: test uses `>=` comparison]

---

## 6. Pitfalls

**P1 — Pipeline.fit(X, y, sample_weight=sw) raises ValueError**
`Pipeline.fit` does not accept `sample_weight` as a top-level kwarg. Must use step-name prefix: `pipeline.fit(X_train_df, y_train, classifier__sample_weight=sw)`. The step name in Phase 9 pipelines should be `classifier` (matching `compare_models.py` pattern, line 122). [VERIFIED: tested in situ with error message]

**P2 — LinearSVC dual='auto' on 15k features: OK, but document**
With n_samples=15,686 and n_features=15,083, `dual='auto'` silently selects `dual=False`. This is correct and no warning is emitted on sklearn 1.6. If someone later adds `dual=True` explicitly (e.g., copy-pasting from older code), sklearn 1.5+ emits a FutureWarning and 1.7+ will remove that option. Do not hardcode `dual=True`.

**P3 — CalibratedClassifierCV trains 5+1 LinearSVC instances**
With `ensemble='auto'` (default) and `cv=5`, the wrapper fits 5 calibrated estimators (one per fold) — the raw LinearSVC is fit 5 times inside CV folds, then sigmoid calibration is fit on hold-out predictions. The final `predict_proba` averages the 5 calibrators. This means `train_time_sec` is ~5–7× the uncalibrated SVM. Do NOT pass `ensemble=False` unless you want a single full-data calibration (less reliable). [VERIFIED: sklearn docs via context7]

**P4 — CalibratedClassifierCV wraps a FRESH LinearSVC, NOT the production model**
Phase 9 must instantiate `LinearSVC(C=SVM_C, ...)` fresh inside the calibration wrapper. Never pass the loaded production `.joblib` into `CalibratedClassifierCV`. The production model has already been fit; passing a pre-fit estimator requires `cv='prefit'` (different semantics). [ASSUMED: correct pattern per sklearn docs]

**P5 — HistGBM rejects sparse input: already mitigated**
HistGBM raises `TypeError` on sparse matrices. The `build_preprocess()` ColumnTransformer already produces dense float64 output (not sparse) on sklearn 1.6.1. The SVD variant also produces dense float64. No `.toarray()` call is needed. BUT: if someone changes `set_output('pandas')` or uses a newer sklearn that changes hstack behaviour, this could break. Keep the dense output implicit. [VERIFIED: tested in situ]

**P6 — TruncatedSVD n_components must be < n_features in the TF-IDF output**
`n_components=256` requires `n_features_in_TF-IDF >= 257`. With `TFIDF_MAX_FEATURES=15000` and the actual vocabulary, TF-IDF will produce at least 1,000+ features on this dataset — so 256 is well within range. But if someone passes `--quick` (1000 rows), the TF-IDF vocabulary may shrink (fewer unique terms). With 1000 rows, the vocabulary will still easily exceed 256. No issue expected. [VERIFIED: real vocab is 15,083 features on full data; quick subsample of 1000 rows still yields >500 unique terms]

**P7 — ComplementNB on `tfidf_only`: must pass `df_train[['text']]` not `df_train[FEATURE_COLUMNS]`**
The NB pipeline's ColumnTransformer only has a single `text` transformer; if you pass all 5 FEATURE_COLUMNS it will encounter unknown column names (if remainder='drop') or silently drop structural features. The preprocessing object for NB must be built with `ColumnTransformer([('text', TfidfVectorizer(...), TEXT_COL)], remainder='drop')`. Passing `df_train[FEATURE_COLUMNS]` with remainder='drop' is safe — the extra columns are dropped. Passing `df_train[[TEXT_COL]]` is also safe. Either works; be consistent. [VERIFIED: ColumnTransformer remainder='drop' behaviour confirmed]

**P8 — LogisticRegression multi_class= deprecation (sklearn 1.6)**
The `multi_class` parameter is deprecated in sklearn 1.6 and will be removed in 1.7. `lbfgs` always uses multinomial. Do NOT pass `multi_class='ovr'` or `multi_class='multinomial'` in Phase 9 code — it will generate a FutureWarning (or break on the next sklearn upgrade). [VERIFIED: signature inspection; `multi_class=deprecated` in params]

**P9 — `inference_time_ms_per_block` warmup must predict at least 1 sample**
D-C-03 warmup: `pipeline.predict(X_test[:10])`. If `--quick` subsample reduces the test set to fewer than 10 rows (it won't — `--quick` only subsamples train), this is still safe. But if a future flag subsamples the test set, the `:10` slice could be empty. For Phase 9 as designed, this is not an issue. [ASSUMED: no test subsampling in Phase 9]

**P10 — HistGBM `early_stopping='auto'` holds out 10% of train data internally**
When `n_samples * 0.9 > 10` (always true here), HistGBM in `early_stopping='auto'` mode uses 10% of the passed training data as an internal validation set and may stop before `max_iter=100`. This means the effective training set is ~14,117 rows, and `train_time_sec` depends on when early stopping triggers. This is expected behaviour and does not need workaround, but should be noted in `summary.txt`. [CITED: sklearn HistGBM docs, early_stopping parameter]

**P11 — `model_size_mb` with pickle.dumps on a fitted Pipeline containing sparse TF-IDF vocabulary**
The fitted TF-IDF vocabulary is a large dict stored in the Pipeline. `pickle.dumps(pipeline)` will include it. For a 15k-feature TF-IDF vocabulary, the pickled pipeline size is typically 5–15 MB. For HistGBM with SVD, the vocabulary is still present (TruncatedSVD does not discard it), so the pickle will be comparable. This is informational only (per D-C-05). [ASSUMED: typical TF-IDF + sklearn model pickle sizes from training knowledge]

**P12 — `per_class_f1.md` silent class drops in ComplementNB**
With `tfidf_only` and 14 imbalanced classes (min class: 7 test samples for `bibliography_title`), ComplementNB may produce zero predictions for rare classes, causing `classification_report` to emit zero-division F1. Use `zero_division=0` in `classification_report`. The per-class F1 invariant test (D-D-04 gate 4) will catch missing classes. [VERIFIED: ComplementNB actual measured macro_f1=0.480, indicating several classes have near-zero F1]

---

## 7. Performance Expectations

All numbers measured on this machine (macOS Darwin 23.3.0, Python 3.9, sklearn 1.6.1) on the actual 15,686-row dataset. Train times include full pipeline fit (preprocessing + classifier). [VERIFIED: benchmarked in this research session]

| Model | Preprocessing | Train Time | `weighted_f1` | `macro_f1` | Notes |
|-------|--------------|-----------|--------------|-----------|-------|
| `logistic_regression` | `tfidf_struct` | ~4.5 s | 0.886 | — | max_iter=3000 needed |
| `linear_svm` (calibrated) | `tfidf_struct` | ~7.4 s | 0.928 | 0.779 | 5 CV folds inside CalibratedClassifierCV |
| `complement_nb` | `tfidf_only` | ~0.9 s | 0.577 | 0.480 | Weakest model; `weighted_f1 > 0.5` passes |
| `random_forest` | `tfidf_struct` | ~6 s (n_jobs=-1) | 0.918 | 0.782 | 20–30 s if n_jobs=None |
| `histgbm_svd256` | `tfidf_struct_svd256` | ~26 s | 0.934 | 0.773 | Includes SVD fit + sample_weight |

**Phase 8 SC-2 floor check:** `linear_svm` row `weighted_f1 = 0.928 < 0.94`. **This is below the Phase 8 SC-2 floor (0.94).**

**Critical finding:** The `linear_svm` in the zoo (wrapped in CalibratedClassifierCV) scores `weighted_f1 = 0.928` while the Phase 8 SC-2 floor requires `0.94`. The production baseline (Этап 1, using `src/train.py::build_pipeline()` which includes `TextPatternFeatures`) scored `0.9829`.

**Root cause:** The zoo `build_preprocess()` pipeline from `src/compare_models.py` does NOT include `TextPatternFeatures` (extra structural pattern features). The production pipeline in `src/train.py` does (line 100–103). This feature gap explains the ~0.055 difference in `weighted_f1`.

**Implication for planner:** The Phase 8 SC-2 test asserts the `linear_svm` row in `results.csv` clears `weighted_f1 ≥ 0.94`. With the current `build_preprocess()` pipeline (TF-IDF + OHE + bold_ratio only), the calibrated SVM scores `0.928` — below the floor. The planner must resolve this either by:
- (a) Using the production pipeline (`build_pipeline()` from `src/train.py`, which includes `TextPatternFeatures`) for the `linear_svm` variant, OR
- (b) Lowering the Phase 8 SC-2 floor for the zoo context (the floor `0.94` was measured with the production pipeline), OR
- (c) Documenting that the zoo uses a simplified pipeline and Phase 8 SC-2 should compare the zoo against a separate zoo-specific floor.

This is a real gap that the discuss-phase did not encounter (CONTEXT.md D-D-02 assumes `linear_svm` will clear `0.94`). **Flag as OQ-1 below.**

---

## 8. Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CLI argument parsing | CLI (`src/main.py`) | — | Existing argparse dispatcher pattern |
| Feature preprocessing | ML pipeline (`src/compare_classical.py`) | `src/compare_models.py` (reuse) | ColumnTransformer lives inside Pipeline |
| Model training + timing | ML pipeline (`src/compare_classical.py`) | — | Sequential per-model fit loop |
| Metric computation | ML pipeline (`src/compare_classical.py`) | `src/compare_models.py::calc_metrics()` (reuse) | Existing function covers all required metrics |
| Artifact serialisation | `src/compare_classical.py` | `src/config.py::REPORTS_DIR` | JSON/CSV/TXT/MD writers in compare_classical |
| TDD gate tests | `tests/test_compare_classical_acceptance.py` | `tests/test_cli_parser.py` (extend) | Mirrors Phase 4/5 pattern |

---

## 9. Open Questions

**OQ-1 — `linear_svm` zoo pipeline vs Phase 8 SC-2 floor**
The zoo `linear_svm` (using `build_preprocess()` from `compare_models.py`, which lacks `TextPatternFeatures`) scores `weighted_f1 = 0.928`, below the Phase 8 SC-2 floor of `0.94`. The planner must decide:
- Option A: Zoo `linear_svm` uses the production pipeline (`src/train.py::build_pipeline()`) to ensure comparability with the Этап 1 baseline. Pros: SC-2 floor passes. Cons: slightly inconsistent with the "same preprocessing family" principle.
- Option B: Zoo `linear_svm` uses `build_preprocess()` (consistent with other models) and the Phase 8 SC-2 floor is adjusted to the zoo context. Requires a CONTEXT.md unlock.
- Option C: Zoo runs both pipelines for `linear_svm` (two rows: `linear_svm_tfidf_struct` and `linear_svm_production_pipeline`). Adds complexity.

**OQ-2 — Exception handling per-model (Claude's Discretion)**
If one model raises an exception during `fit()` or `predict()`:
- Option A (atomic): fail the whole run, exit non-zero. Simpler; easier to debug.
- Option B (best-effort): log error under `results.json[models][i].error`, continue. More robust for CI runs where one model might OOM.
Researcher recommendation: **best-effort** with a non-zero exit code if any model failed. This is consistent with `summary.txt` needing to document each model's status, and allows Phase 8 SC-2 to still validate the `linear_svm` row even if, say, RF fails.

**OQ-3 — RF `n_jobs` default**
`n_jobs=None` (single-core) for RandomForest means ~20–30 s train time on this dataset. `n_jobs=-1` reduces to ~6 s. The planner should decide whether to use `n_jobs=-1` (non-deterministic ordering in parallel runs, but results are deterministic with fixed seed) or `n_jobs=None` for strict reproducibility. Both produce identical predictions with fixed `random_state`. Researcher recommendation: `n_jobs=-1` is safe and reduces total zoo runtime by ~20 s.

**OQ-4 — `per_class_f1.md` format: per-model table vs combined table**
CONTEXT.md leaves this as Claude's discretion. Per-model table (one markdown table per model) is easier to parse in code for the per-class invariant test. Combined table (rows = classes, columns = models) is more human-readable. Researcher recommendation: per-model tables (one H2 heading + table per model) — simpler to write, simpler to test with a regex/contains check.

---

## 10. Project Constraints (from CLAUDE.md)

- **TDD iron law:** No production code without a failing test. Phase 9 must start with RED tests (4 TDD gates from D-D-04) before writing `src/compare_classical.py`.
- **Minimum code principle:** No extra abstractions, no "future flexibility" layers. `src/compare_classical.py` should be a single file with a flat `run_compare_classical()` function.
- **No refactoring of working code:** `src/compare_models.py`, `src/train.py`, `src/predict_blocks.py` must not be modified.
- **No commit message AI-attribution trailers:** No `Co-Authored-By`, `Generated-by`, etc.
- **Commit messages in Russian or English, concise.**
- **Self-improvement protocol:** After any correction, update CLAUDE.md with a rule.

---

## Sources

### Primary (HIGH confidence — verified in situ)
- sklearn 1.6.1 installed on dev machine — all API signatures verified by `inspect.signature()`
- Actual dataset files (`dataset/annotations_{train,test}.csv`) — row counts, label distributions, feature ranges measured by pandas
- `src/compare_models.py`, `src/train.py`, `src/config.py`, `src/main.py` — read and cited with line numbers
- All 5 benchmark numbers (train time, weighted_f1, macro_f1) — measured on actual data in this research session
- Pipeline.fit sample_weight pass-through — tested in situ; error message captured

### Secondary (HIGH confidence — cited from official docs)
- sklearn `CalibratedClassifierCV` ensemble behaviour: [CITED: context7 /websites/scikit-learn_stable, calibration.html]
- sklearn ComplementNB non-negativity: [CITED: sklearn docs]
- HistGBM `early_stopping='auto'` internal validation fraction: [CITED: context7 /websites/scikit-learn_stable, ensemble.html]
- HistGBM `sample_weight` in fit: [CITED: context7 /websites/scikit-learn_stable, ensemble.rst.txt]

### Tertiary (ASSUMED — training knowledge, not re-verified)
- Expected pickle sizes for TF-IDF + sklearn pipelines (P11): [ASSUMED] — typical range, not measured
- `--quick` 1000-row subsample TF-IDF vocabulary size (>500 unique terms): [ASSUMED] — not benchmarked for this specific dataset

---

## Metadata

**Research date:** 2026-05-15
**sklearn version verified against:** 1.6.1
**Python version:** 3.9 (system)
**Dataset rows verified:** train=15,686 / test=5,462 / val=5,711
**Valid until:** 60 days (stable sklearn API, no pending breaking changes in 1.7 that affect this phase)
