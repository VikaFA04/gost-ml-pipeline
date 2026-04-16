"""Confusion matrix data helpers."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import confusion_matrix


def build_confusion_matrix_frame(
    y_true: list[str],
    y_pred: list[str],
    labels: list[str],
) -> pd.DataFrame:
    """Return confusion matrix data in tabular form."""
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    rows: list[dict[str, object]] = []
    for actual_index, actual_label in enumerate(labels):
        for predicted_index, predicted_label in enumerate(labels):
            rows.append(
                {
                    "actual_label": actual_label,
                    "predicted_label": predicted_label,
                    "count": int(matrix[actual_index, predicted_index]),
                }
            )
    return pd.DataFrame(rows)
