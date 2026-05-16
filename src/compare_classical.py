from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    precision_recall_fscore_support,
)
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC
from sklearn.utils.class_weight import compute_sample_weight

from src.config import (
    TRAIN_CSV, TEST_CSV, REPORTS_DIR, TEXT_COL, TARGET_COL, FEATURE_COLUMNS,
    CAT_COLS, NUM_COLS,
    TFIDF_MAX_FEATURES, TFIDF_NGRAM_RANGE, TFIDF_MIN_DF, TFIDF_SUBLINEAR_TF,
    SVM_C, SVM_CLASS_WEIGHT, SVM_MAX_ITER, RANDOM_STATE,
)


# ---------------------------------------------------------------------------
# Local helpers (inlined from compare_models to avoid matplotlib dependency)
# ---------------------------------------------------------------------------

def _now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _load_dataset(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Не найден файл датасета: {path}")
    df = pd.read_csv(path)
    required_columns = set(FEATURE_COLUMNS + [TARGET_COL])
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(
            f"В файле {path.name} отсутствуют обязательные колонки: {sorted(missing)}"
        )
    df = df.copy()
    df[TEXT_COL] = df[TEXT_COL].fillna("").astype(str)
    for col in CAT_COLS:
        df[col] = df[col].fillna("missing").astype(str)
    for col in NUM_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[df[TARGET_COL].notna()].copy()
    if df.empty:
        raise ValueError(f"После фильтрации в файле {path.name} не осталось строк.")
    return df


def _calc_metrics(y_true, y_pred) -> dict:
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_macro": precision_macro,
        "recall_macro": recall_macro,
        "f1_macro": f1_macro,
        "precision_weighted": precision_weighted,
        "recall_weighted": recall_weighted,
        "f1_weighted": f1_weighted,
        "classification_report": classification_report(
            y_true, y_pred, output_dict=True, zero_division=0
        ),
        "classification_report_text": classification_report(
            y_true, y_pred, digits=4, zero_division=0
        ),
    }


def _build_preprocess() -> ColumnTransformer:
    """TF-IDF + structural features preprocessor (mirrors compare_models.build_preprocess)."""
    text_transformer = TfidfVectorizer(
        max_features=TFIDF_MAX_FEATURES, ngram_range=TFIDF_NGRAM_RANGE,
        min_df=TFIDF_MIN_DF, sublinear_tf=TFIDF_SUBLINEAR_TF, lowercase=True,
    )
    cat_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    num_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value=0.0)),
    ])
    return ColumnTransformer(
        transformers=[
            ("text", text_transformer, TEXT_COL),
            ("cat", cat_transformer, CAT_COLS),
            ("num", num_transformer, NUM_COLS),
        ],
        remainder="drop",
    )


# ---------------------------------------------------------------------------
# HistGBM-specific preprocessor (TF-IDF -> SVD256)
# ---------------------------------------------------------------------------

def _build_tfidf_svd_preprocess() -> ColumnTransformer:
    tfidf_svd = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=TFIDF_MAX_FEATURES, ngram_range=TFIDF_NGRAM_RANGE,
            min_df=TFIDF_MIN_DF, sublinear_tf=TFIDF_SUBLINEAR_TF, lowercase=True,
        )),
        ("svd", TruncatedSVD(n_components=256, random_state=RANDOM_STATE)),
    ])
    cat_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    num_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value=0.0)),
    ])
    return ColumnTransformer(
        transformers=[
            ("text", tfidf_svd, TEXT_COL),
            ("cat", cat_transformer, ["kind", "alignment", "style"]),
            ("num", num_transformer, ["bold_ratio"]),
        ],
        remainder="drop",
    )


# ---------------------------------------------------------------------------
# Pipeline zoo builder
# ---------------------------------------------------------------------------

def _build_pipelines(seed: int) -> list[dict]:
    from sklearn.linear_model import LogisticRegression
    from src.train import build_pipeline  # production pipeline (TextPatternFeatures)

    # 1. logistic_regression
    lr_pipeline = Pipeline([
        ("preprocess", _build_preprocess()),
        ("classifier", LogisticRegression(
            max_iter=3000, class_weight="balanced", random_state=seed)),
    ])

    # 2. linear_svm (zoo apples-to-apples)
    linear_svm_pipeline = Pipeline([
        ("preprocess", _build_preprocess()),
        ("classifier", CalibratedClassifierCV(
            LinearSVC(C=SVM_C, class_weight=SVM_CLASS_WEIGHT,
                      max_iter=SVM_MAX_ITER, random_state=seed),
            method="sigmoid", cv=5)),
    ])

    # 3. linear_svm_production — uses build_pipeline() from src/train.py (D-E-01)
    prod_inner = build_pipeline()
    linear_svm_production_pipeline = Pipeline([
        ("preprocess", prod_inner.named_steps["preprocess"]),
        ("classifier", CalibratedClassifierCV(
            LinearSVC(C=SVM_C, class_weight=SVM_CLASS_WEIGHT,
                      max_iter=SVM_MAX_ITER, random_state=seed),
            method="sigmoid", cv=5)),
    ])

    # 4. complement_nb (tfidf_only per D-B-02)
    complement_nb_pipeline = Pipeline([
        ("preprocess", ColumnTransformer(
            [("text", TfidfVectorizer(
                max_features=TFIDF_MAX_FEATURES, ngram_range=TFIDF_NGRAM_RANGE,
                min_df=TFIDF_MIN_DF, sublinear_tf=TFIDF_SUBLINEAR_TF, lowercase=True,
            ), TEXT_COL)],
            remainder="drop")),
        ("classifier", ComplementNB()),
    ])

    # 5. random_forest (tfidf_struct per D-E-03, n_jobs=-1)
    random_forest_pipeline = Pipeline([
        ("preprocess", _build_preprocess()),
        ("classifier", RandomForestClassifier(
            class_weight="balanced", n_jobs=-1, random_state=seed)),
    ])

    # 6. histgbm_svd256 (tfidf_struct_svd256 per D-B-03/D-B-04)
    # NOTE: fit_kwargs NOT in spec dict per plan-checker W2 resolution.
    # classifier__sample_weight pass-through happens in run_compare_classical step 6.
    histgbm_pipeline = Pipeline([
        ("preprocess", _build_tfidf_svd_preprocess()),
        ("classifier", HistGradientBoostingClassifier(random_state=seed)),
    ])

    return [
        {
            "name": "logistic_regression",
            "preprocessing_variant": "tfidf_struct",
            "pipeline": lr_pipeline,
        },
        {
            "name": "linear_svm",
            "preprocessing_variant": "tfidf_struct",
            "pipeline": linear_svm_pipeline,
        },
        {
            "name": "linear_svm_production",
            "preprocessing_variant": "tfidf_struct_textpatterns",
            "pipeline": linear_svm_production_pipeline,
        },
        {
            "name": "complement_nb",
            "preprocessing_variant": "tfidf_only",
            "pipeline": complement_nb_pipeline,
        },
        {
            "name": "random_forest",
            "preprocessing_variant": "tfidf_struct",
            "pipeline": random_forest_pipeline,
        },
        {
            "name": "histgbm_svd256",
            "preprocessing_variant": "tfidf_struct_svd256",
            "pipeline": histgbm_pipeline,
        },
    ]


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

def run_compare_classical(cli_args: argparse.Namespace) -> int:
    # 1. Resolve output_dir
    output_dir = (
        Path(cli_args.output_dir)
        if cli_args.output_dir
        else REPORTS_DIR / f"classical_zoo_{_now_ts()}"
    )
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 2. Load data
    train_df = _load_dataset(TRAIN_CSV)
    test_df = _load_dataset(TEST_CSV)
    if cli_args.quick:
        train_df = train_df.sample(
            n=min(1000, len(train_df)), random_state=cli_args.seed
        )
    X_train = train_df[FEATURE_COLUMNS].copy()
    y_train = train_df[TARGET_COL].copy()
    X_test = test_df[FEATURE_COLUMNS].copy()
    y_test = test_df[TARGET_COL].copy()

    # 3. Filter to requested models
    ALIAS_MAP = {
        "lr": "logistic_regression",
        "svm": "linear_svm",
        "svm_production": "linear_svm_production",
        "nb": "complement_nb",
        "rf": "random_forest",
        "hgb": "histgbm_svd256",
    }
    requested = {
        ALIAS_MAP.get(m.strip(), m.strip())
        for m in cli_args.models.split(",")
    }
    specs = [s for s in _build_pipelines(cli_args.seed) if s["name"] in requested]

    # 4. Compute dataset hashes (SHA-256)
    def _sha256(path: Path | str) -> str:
        return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()

    # 5. Record started_at
    started_at = datetime.now(timezone.utc).isoformat()

    # 6. Train and evaluate each model with per-model exception handling (D-E-02)
    model_records = []
    for spec in specs:
        try:
            t0_fit = time.perf_counter()
            if spec["name"] == "histgbm_svd256":
                sw = compute_sample_weight("balanced", y_train)
                # CRITICAL (P1): must use classifier__sample_weight=sw
                # pipeline.fit(X, y, sample_weight=sw) raises ValueError in sklearn 1.6
                spec["pipeline"].fit(X_train, y_train, classifier__sample_weight=sw)
            else:
                spec["pipeline"].fit(X_train, y_train)
            train_time_sec = time.perf_counter() - t0_fit

            # Warmup predict — result discarded (D-C-03)
            spec["pipeline"].predict(X_test[:10])
            t0_inf = time.perf_counter()
            y_pred = spec["pipeline"].predict(X_test)
            inference_time_ms = (time.perf_counter() - t0_inf) * 1000 / len(X_test)

            metrics = _calc_metrics(y_test, y_pred)
            model_size_mb = len(pickle.dumps(spec["pipeline"])) / (1024 * 1024)

            model_record = {
                "name": spec["name"],
                "preprocessing_variant": spec["preprocessing_variant"],
                "metrics": {
                    "accuracy": metrics["accuracy"],
                    "weighted_f1": metrics["f1_weighted"],
                    "macro_f1": metrics["f1_macro"],
                },
                "performance": {
                    "train_time_sec": round(train_time_sec, 3),
                    "inference_time_ms_per_block": round(inference_time_ms, 4),
                    "model_size_mb": round(model_size_mb, 3),
                },
                "per_class": metrics["classification_report"],
                "error": None,
            }
        except Exception as exc:
            model_record = {
                "name": spec["name"],
                "preprocessing_variant": spec["preprocessing_variant"],
                "metrics": None,
                "performance": None,
                "per_class": None,
                "error": {
                    "class": type(exc).__name__,
                    "message": str(exc)[:200],
                },
            }
        model_records.append(model_record)

    # 7. Build results.json
    results_json = {
        "phase": "09",
        "cli_args": {
            "models": cli_args.models,
            "output_dir": str(output_dir),
            "seed": cli_args.seed,
            "quick": cli_args.quick,
        },
        "timestamps": {
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        },
        "environment": {
            "python": sys.version,
            "sklearn": sklearn.__version__,
            "platform": platform.platform(),
        },
        "dataset_hashes": {
            "annotations_train.csv": _sha256(TRAIN_CSV),
            "annotations_test.csv": _sha256(TEST_CSV),
        },
        "models": model_records,
    }
    (Path(output_dir) / "results.json").write_text(
        json.dumps(results_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 8. Write results.csv — D-C-02 locked 8-column order
    csv_rows = []
    for rec in model_records:
        if rec["error"] is None:
            csv_rows.append({
                "model": rec["name"],
                "preprocessing_variant": rec["preprocessing_variant"],
                "accuracy": rec["metrics"]["accuracy"],
                "weighted_f1": rec["metrics"]["weighted_f1"],
                "macro_f1": rec["metrics"]["macro_f1"],
                "train_time_sec": rec["performance"]["train_time_sec"],
                "inference_time_ms_per_block": rec["performance"]["inference_time_ms_per_block"],
                "model_size_mb": rec["performance"]["model_size_mb"],
            })
        else:
            csv_rows.append({
                "model": rec["name"],
                "preprocessing_variant": rec["preprocessing_variant"],
                "accuracy": float("nan"),
                "weighted_f1": float("nan"),
                "macro_f1": float("nan"),
                "train_time_sec": float("nan"),
                "inference_time_ms_per_block": float("nan"),
                "model_size_mb": float("nan"),
            })
    csv_columns = [
        "model", "preprocessing_variant", "accuracy", "weighted_f1", "macro_f1",
        "train_time_sec", "inference_time_ms_per_block", "model_size_mb",
    ]
    pd.DataFrame(csv_rows, columns=csv_columns).to_csv(
        Path(output_dir) / "results.csv", index=False, encoding="utf-8"
    )

    # 9. Write summary.txt
    _write_summary_txt(Path(output_dir) / "summary.txt", model_records, cli_args)

    # 10. Write per_class_f1.md (D-E-04)
    _write_per_class_f1_md(Path(output_dir) / "per_class_f1.md", model_records)

    # 11. Return 0 if no model had an error, else 1
    has_error = any(rec["error"] is not None for rec in model_records)
    return 1 if has_error else 0


def _write_summary_txt(path: Path, model_records: list[dict], cli_args) -> None:
    lines = []
    if cli_args.quick:
        lines.append(
            "QUICK RUN (train subsampled to 1000 rows) — not gated by Phase 8 SC-2\n"
        )
    lines.append("=== Classical Model Zoo — Comparison Summary ===\n")
    for rec in model_records:
        lines.append(f"\n--- {rec['name']} ---")
        lines.append(f"  preprocessing_variant: {rec['preprocessing_variant']}")
        if rec["error"] is None:
            m = rec["metrics"]
            p = rec["performance"]
            lines.append(f"  weighted_f1:                {m['weighted_f1']:.4f}")
            lines.append(f"  macro_f1:                   {m['macro_f1']:.4f}")
            lines.append(f"  accuracy:                   {m['accuracy']:.4f}")
            lines.append(f"  train_time_sec:             {p['train_time_sec']}")
            lines.append(f"  inference_time_ms_per_block:{p['inference_time_ms_per_block']}")
            lines.append(f"  model_size_mb:              {p['model_size_mb']}")
            if rec["name"] == "linear_svm_production":
                wf1 = m["weighted_f1"]
                mf1 = m["macro_f1"]
                sc2_ok = wf1 >= 0.94 and mf1 >= 0.9414
                verdict = "PASS" if sc2_ok else "FAIL"
                lines.append(
                    f"  Phase 8 SC-2 verdict: {verdict} "
                    f"(weighted_f1={wf1:.4f} >= 0.94, macro_f1={mf1:.4f} >= 0.9414)"
                )
            if rec["name"] == "linear_svm":
                lines.append(
                    "  Note: train_time reflects CalibratedClassifierCV (5 CV folds); "
                    "production SVM is faster"
                )
            if rec["name"] == "histgbm_svd256":
                lines.append(
                    "  Note: HistGBM early_stopping='auto' uses 10% of train data internally"
                )
            if rec["name"] == "complement_nb":
                lines.append(
                    "  Note: tfidf_only preprocessing (structural features dropped per D-B-02)"
                )
        else:
            lines.append(f"  ERROR: {rec['error']['class']}: {rec['error']['message']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_per_class_f1_md(path: Path, model_records: list[dict]) -> None:
    lines = []
    # Skip aggregate keys; only label classes
    _SKIP_KEYS = {"accuracy", "macro avg", "weighted avg"}
    for rec in model_records:
        if rec["error"] is not None:
            continue
        lines.append(f"## {rec['name']}\n")
        lines.append("| class | precision | recall | f1 | support |")
        lines.append("|-------|-----------|--------|----|---------|")
        per_class = rec["per_class"]
        for label, stats in per_class.items():
            if label in _SKIP_KEYS:
                continue
            if not isinstance(stats, dict):
                continue
            prec = stats.get("precision", 0.0)
            rec_val = stats.get("recall", 0.0)
            f1 = stats.get("f1-score", 0.0)
            sup = stats.get("support", 0)
            lines.append(
                f"| {label} | {prec:.4f} | {rec_val:.4f} | {f1:.4f} | {sup} |"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
