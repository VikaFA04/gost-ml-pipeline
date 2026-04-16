from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    precision_recall_fscore_support,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC

from src.config import (
    TRAIN_CSV,
    VAL_CSV,
    TEST_CSV,
    METRICS_DIR,
    MODELS_DIR,
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
)


COMPARE_DIR = METRICS_DIR / "model_comparison"
COMPARE_DIR.mkdir(parents=True, exist_ok=True)


def now_ts() -> str:
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
        raise ValueError(f"После фильтрации в файле {path.name} не осталось строк.")

    return df


def build_preprocess() -> ColumnTransformer:
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
            ("cat", cat_transformer, CAT_COLS),
            ("num", num_transformer, NUM_COLS),
        ],
        remainder="drop",
    )

    return preprocess


def build_models() -> dict[str, Pipeline]:
    preprocess = build_preprocess()

    lr_pipeline = Pipeline(
        steps=[
            ("preprocess", preprocess),
            (
                "classifier",
                LogisticRegression(
                    max_iter=3000,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )

    svm_pipeline = Pipeline(
        steps=[
            ("preprocess", build_preprocess()),
            (
                "classifier",
                LinearSVC(
                    C=SVM_C,
                    class_weight=SVM_CLASS_WEIGHT,
                    max_iter=SVM_MAX_ITER,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )

    return {
        "logistic_regression": lr_pipeline,
        "linear_svm": svm_pipeline,
    }


def calc_metrics(y_true, y_pred) -> dict:
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


def save_conf_matrix(y_true, y_pred, labels, model_name, split_name, timestamp):
    cm = confusion_matrix(y_true, y_pred, labels=labels, normalize="true")
    fig, ax = plt.subplots(figsize=(12, 10))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(ax=ax, xticks_rotation=45, values_format=".2f", colorbar=False)
    ax.set_title(f"{model_name} — {split_name}")
    plt.tight_layout()

    png_path = COMPARE_DIR / f"{model_name}_{split_name}_confusion_matrix_{timestamp}.png"
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close()

    csv_path = COMPARE_DIR / f"{model_name}_{split_name}_confusion_matrix_{timestamp}.csv"
    pd.DataFrame(cm, index=labels, columns=labels).to_csv(csv_path, encoding="utf-8-sig")

    return png_path, csv_path


def save_metric_plot(metrics_df: pd.DataFrame, timestamp: str) -> Path:
    plot_df = metrics_df[metrics_df["split"] == "test"].copy()

    fig, ax = plt.subplots(figsize=(10, 6))
    metrics_to_plot = ["accuracy", "f1_macro", "f1_weighted"]

    x = range(len(plot_df))
    width = 0.22

    for i, metric in enumerate(metrics_to_plot):
        ax.bar(
            [v + width * i for v in x],
            plot_df[metric],
            width=width,
            label=metric,
        )

    ax.set_xticks([v + width for v in x])
    ax.set_xticklabels(plot_df["model"], rotation=0)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Значение метрики")
    ax.set_title("Сравнение качества моделей на тестовой выборке")
    ax.legend()
    plt.tight_layout()

    out_path = COMPARE_DIR / f"model_metrics_comparison_{timestamp}.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    return out_path


def main():
    timestamp = now_ts()

    train_df = load_dataset(TRAIN_CSV)
    val_df = load_dataset(VAL_CSV)
    test_df = load_dataset(TEST_CSV)

    x_train = train_df[FEATURE_COLUMNS].copy()
    y_train = train_df[TARGET_COL].copy()

    x_val = val_df[FEATURE_COLUMNS].copy()
    y_val = val_df[TARGET_COL].copy()

    x_test = test_df[FEATURE_COLUMNS].copy()
    y_test = test_df[TARGET_COL].copy()

    labels = sorted(pd.concat([y_train, y_val, y_test]).unique())
    models = build_models()

    all_metrics_rows = []
    full_results = {
        "timestamp": timestamp,
        "labels": labels,
        "models": {},
    }

    for model_name, model in models.items():
        print(f"Обучение: {model_name}")
        model.fit(x_train, y_train)

        model_path = MODELS_DIR / f"{model_name}_{timestamp}.joblib"
        joblib.dump(model, model_path)

        model_results = {}

        for split_name, x_split, y_split in [
            ("val", x_val, y_val),
            ("test", x_test, y_test),
        ]:
            y_pred = model.predict(x_split)
            metrics = calc_metrics(y_split, y_pred)

            cm_png, cm_csv = save_conf_matrix(
                y_split, y_pred, labels, model_name, split_name, timestamp
            )

            report_txt_path = COMPARE_DIR / f"{model_name}_{split_name}_report_{timestamp}.txt"
            with open(report_txt_path, "w", encoding="utf-8") as f:
                f.write(metrics["classification_report_text"])

            model_results[split_name] = {
                "accuracy": metrics["accuracy"],
                "precision_macro": metrics["precision_macro"],
                "recall_macro": metrics["recall_macro"],
                "f1_macro": metrics["f1_macro"],
                "precision_weighted": metrics["precision_weighted"],
                "recall_weighted": metrics["recall_weighted"],
                "f1_weighted": metrics["f1_weighted"],
                "classification_report": metrics["classification_report"],
                "artifacts": {
                    "model_path": str(model_path),
                    "confusion_matrix_png": str(cm_png),
                    "confusion_matrix_csv": str(cm_csv),
                    "classification_report_txt": str(report_txt_path),
                },
            }

            all_metrics_rows.append(
                {
                    "model": model_name,
                    "split": split_name,
                    "accuracy": metrics["accuracy"],
                    "precision_macro": metrics["precision_macro"],
                    "recall_macro": metrics["recall_macro"],
                    "f1_macro": metrics["f1_macro"],
                    "precision_weighted": metrics["precision_weighted"],
                    "recall_weighted": metrics["recall_weighted"],
                    "f1_weighted": metrics["f1_weighted"],
                }
            )

        full_results["models"][model_name] = model_results

    metrics_df = pd.DataFrame(all_metrics_rows)
    metrics_csv_path = COMPARE_DIR / f"metrics_comparison_{timestamp}.csv"
    metrics_df.to_csv(metrics_csv_path, index=False, encoding="utf-8-sig")

    chart_path = save_metric_plot(metrics_df, timestamp)

    full_results["summary_artifacts"] = {
        "metrics_csv": str(metrics_csv_path),
        "metrics_chart_png": str(chart_path),
    }

    json_path = COMPARE_DIR / f"metrics_comparison_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_results, f, ensure_ascii=False, indent=2)

    print("Сравнение завершено.")
    print(f"CSV с метриками: {metrics_csv_path}")
    print(f"График сравнения: {chart_path}")
    print(f"JSON с результатами: {json_path}")


if __name__ == "__main__":
    main()