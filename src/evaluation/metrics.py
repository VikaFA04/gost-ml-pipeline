"""Metrics computation for classification models."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support


def compute_summary_metrics(y_true: list[str], y_pred: list[str]) -> dict[str, float]:
    """Compute top-level metrics for a classification run."""
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "weighted_precision": float(precision),
        "weighted_recall": float(recall),
        "weighted_f1": float(f1),
    }


def compute_per_class_metrics(y_true: list[str], y_pred: list[str]) -> pd.DataFrame:
    """Return per-class metrics as a dataframe."""
    report: dict[str, Any] = classification_report(
        y_true,
        y_pred,
        output_dict=True,
        zero_division=0,
    )
    per_class_rows = []
    for label, values in report.items():
        if label in {"accuracy", "macro avg", "weighted avg"}:
            continue
        per_class_rows.append(
            {
                "label": label,
                "precision": float(values["precision"]),
                "recall": float(values["recall"]),
                "f1": float(values["f1-score"]),
                "support": int(values["support"]),
            }
        )
    return pd.DataFrame(per_class_rows).sort_values("label").reset_index(drop=True)
