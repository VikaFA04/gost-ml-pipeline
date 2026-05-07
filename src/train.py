from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC

from src.config import (
    TRAIN_CSV,
    VAL_CSV,
    TEST_CSV,
    MODELS_DIR,
    METRICS_DIR,
    TEXT_COL,
    TARGET_COL,
    FEATURE_COLUMNS,
    CAT_COLS,
    NUM_COLS,
    TFIDF_MAX_FEATURES,
    TFIDF_NGRAM_RANGE,
    TFIDF_MIN_DF,
    TFIDF_SUBLINEAR_TF,
    SVM_C,
    SVM_CLASS_WEIGHT,
    SVM_MAX_ITER,
    RANDOM_STATE,
    MODEL_FILENAME_PREFIX,
)
from src.features.pattern_features import TextPatternFeatures


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_dataset(path: str | Path) -> pd.DataFrame:
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
        raise ValueError(f"После фильтрации в файле {path.name} не осталось строк для обучения.")

    return df


def build_pipeline() -> Pipeline:
    text_transformer = TfidfVectorizer(
        max_features=TFIDF_MAX_FEATURES,
        ngram_range=TFIDF_NGRAM_RANGE,
        min_df=TFIDF_MIN_DF,
        sublinear_tf=TFIDF_SUBLINEAR_TF,
        lowercase=True,
    )

    cat_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    num_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value=0.0)),
        ]
    )

    preprocess = ColumnTransformer(
        transformers=[
            ("text", text_transformer, TEXT_COL),
            ("patterns", TextPatternFeatures(), [TEXT_COL]),
            ("cat", cat_transformer, CAT_COLS),
            ("num", num_transformer, NUM_COLS),
        ],
        remainder="drop",
    )

    classifier = LinearSVC(
        C=SVM_C,
        class_weight=SVM_CLASS_WEIGHT,
        max_iter=SVM_MAX_ITER,
        random_state=RANDOM_STATE,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocess", preprocess),
            ("classifier", classifier),
        ]
    )

    return pipeline


def evaluate_split(model: Pipeline, df: pd.DataFrame) -> tuple[dict, str, pd.DataFrame]:
    x = df[FEATURE_COLUMNS].copy()
    y_true = df[TARGET_COL].copy()
    y_pred = model.predict(x)

    report_dict = classification_report(
        y_true,
        y_pred,
        output_dict=True,
        zero_division=0,
    )
    report_text = classification_report(
        y_true,
        y_pred,
        digits=4,
        zero_division=0,
    )

    eval_df = df.copy()
    eval_df["predicted_label"] = y_pred
    eval_df["is_correct"] = eval_df[TARGET_COL] == eval_df["predicted_label"]

    return report_dict, report_text, eval_df


def run_training() -> dict:
    timestamp = _timestamp()

    train_df = load_dataset(TRAIN_CSV)
    val_df = load_dataset(VAL_CSV)
    test_df = load_dataset(TEST_CSV)

    model = build_pipeline()

    x_train = train_df[FEATURE_COLUMNS].copy()
    y_train = train_df[TARGET_COL].copy()

    model.fit(x_train, y_train)

    val_report, val_report_text, val_eval_df = evaluate_split(model, val_df)
    test_report, test_report_text, test_eval_df = evaluate_split(model, test_df)

    model_path = MODELS_DIR / f"{MODEL_FILENAME_PREFIX}_{timestamp}.joblib"
    metrics_path = METRICS_DIR / f"training_metrics_{timestamp}.json"
    report_path = METRICS_DIR / f"training_report_{timestamp}.txt"
    val_errors_path = METRICS_DIR / f"val_errors_{timestamp}.csv"
    test_errors_path = METRICS_DIR / f"test_errors_{timestamp}.csv"

    joblib.dump(model, model_path)

    metrics_payload = {
        "timestamp": timestamp,
        "model_name": "LinearSVC",
        "target_column": TARGET_COL,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_columns": CAT_COLS,
        "numeric_columns": NUM_COLS,
        "tfidf": {
            "max_features": TFIDF_MAX_FEATURES,
            "ngram_range": TFIDF_NGRAM_RANGE,
            "min_df": TFIDF_MIN_DF,
            "sublinear_tf": TFIDF_SUBLINEAR_TF,
        },
        "classifier": {
            "C": SVM_C,
            "class_weight": SVM_CLASS_WEIGHT,
            "max_iter": SVM_MAX_ITER,
            "random_state": RANDOM_STATE,
        },
        "train_rows": int(len(train_df)),
        "val_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "val": val_report,
        "test": test_report,
    }

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, ensure_ascii=False, indent=2)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=== VALIDATION ===\n")
        f.write(val_report_text)
        f.write("\n\n=== TEST ===\n")
        f.write(test_report_text)

    val_eval_df.loc[~val_eval_df["is_correct"]].to_csv(
        val_errors_path,
        index=False,
        encoding="utf-8-sig",
    )
    test_eval_df.loc[~test_eval_df["is_correct"]].to_csv(
        test_errors_path,
        index=False,
        encoding="utf-8-sig",
    )

    return {
        "timestamp": timestamp,
        "model_path": str(model_path),
        "metrics_path": str(metrics_path),
        "report_path": str(report_path),
        "val_errors_path": str(val_errors_path),
        "test_errors_path": str(test_errors_path),
        "val_accuracy": val_report["accuracy"],
        "val_weighted_f1": val_report["weighted avg"]["f1-score"],
        "test_accuracy": test_report["accuracy"],
        "test_weighted_f1": test_report["weighted avg"]["f1-score"],
    }


if __name__ == "__main__":
    result = run_training()
    print(json.dumps(result, ensure_ascii=False, indent=2))