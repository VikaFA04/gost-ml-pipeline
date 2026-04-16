from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report

from src.config import TARGET_COL


def evaluate_predictions(df: pd.DataFrame) -> dict:
    if TARGET_COL not in df.columns:
        raise ValueError(f"Для оценки нужна колонка {TARGET_COL}")

    if "predicted_label" not in df.columns:
        raise ValueError("Для оценки нужна колонка predicted_label")

    if "postprocessed_label" not in df.columns:
        raise ValueError("Для оценки нужна колонка postprocessed_label")

    y_true = df[TARGET_COL]
    y_pred_before = df["predicted_label"]
    y_pred_after = df["postprocessed_label"]

    return {
        "before_rules": classification_report(
            y_true, y_pred_before, output_dict=True, zero_division=0
        ),
        "after_rules": classification_report(
            y_true, y_pred_after, output_dict=True, zero_division=0
        ),
    }


def save_evaluation(result: dict, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)