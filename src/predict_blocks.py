from __future__ import annotations

from pathlib import Path
from typing import Any
import joblib
import numpy as np
import pandas as pd
from src.config import (
    TEXT_COL,
    FEATURE_COLUMNS,
    CAT_COLS,
    NUM_COLS,
)


def load_blocks_csv(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Не найден CSV-файл: {path}")

    df = pd.read_csv(path)

    missing = set(FEATURE_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(
            f"Во входном CSV отсутствуют обязательные колонки: {sorted(missing)}"
        )

    df = df.copy()
    df[TEXT_COL] = df[TEXT_COL].fillna("").astype(str)

    for col in CAT_COLS:
        df[col] = df[col].fillna("missing").astype(str)

    for col in NUM_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _compute_confidence_scores(model: Any, x: pd.DataFrame) -> np.ndarray:
    """
    Возвращает confidence score для каждого блока.
    Для LinearSVC используем decision_function:
    - multiclass: max margin по классам
    - binary: abs(score)
    """
    classifier = model.named_steps["classifier"]

    # Берем преобразованные признаки после preprocess
    x_transformed = model.named_steps["preprocess"].transform(x)

    if not hasattr(classifier, "decision_function"):
        return np.full(shape=(len(x),), fill_value=np.nan)

    raw_scores = classifier.decision_function(x_transformed)

    if isinstance(raw_scores, list):
        raw_scores = np.asarray(raw_scores)

    if getattr(raw_scores, "ndim", 1) == 1:
        # binary case
        return np.abs(raw_scores).astype(float)

    # multiclass case
    return np.max(raw_scores, axis=1).astype(float)


def _mark_low_confidence(
    df: pd.DataFrame,
    threshold: float = 0.8,
) -> pd.DataFrame:
    """
    Помечает низкоуверенные предсказания.
    Порог можно позже вынести в config, если понадобится.
    """
    df = df.copy()
    df["low_confidence"] = df["confidence_score"] < threshold
    return df


def _apply_postprocess_if_available(df: pd.DataFrame) -> pd.DataFrame:
    """
    Применяет rule-based постобработку, если модуль доступен
    и его сигнатура совместима.
    """
    try:
        from src.postprocess.postprocess_rules import apply_postprocess_rules
    except Exception:
        df = df.copy()
        df["postprocessed_label"] = df["predicted_label"]
        return df

    df = df.copy()

    try:
        result = apply_postprocess_rules(
            df,
            pred_col="predicted_label",
            out_col="postprocessed_label",
        )
        if isinstance(result, pd.DataFrame):
            return result
    except TypeError:
        pass
    except Exception:
        pass

    try:
        result = apply_postprocess_rules(df)
        if isinstance(result, pd.DataFrame):
            if "postprocessed_label" not in result.columns and "predicted_label" in result.columns:
                result = result.copy()
                result["postprocessed_label"] = result["predicted_label"]
            return result
    except Exception:
        pass

    df["postprocessed_label"] = df["predicted_label"]
    return df


def predict_blocks(
    model_path: str | Path,
    blocks_df: pd.DataFrame,
    apply_rules: bool = False,
) -> pd.DataFrame:
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Не найдена модель: {model_path}")

    model = joblib.load(model_path)

    df = blocks_df.copy()

    missing = set(FEATURE_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(
            f"В DataFrame отсутствуют обязательные колонки: {sorted(missing)}"
        )

    x = df[FEATURE_COLUMNS].copy()
    df["predicted_label"] = model.predict(x)
    df["confidence_score"] = _compute_confidence_scores(model, x)
    df = _mark_low_confidence(df, threshold=0.8)

    if apply_rules:
        df = _apply_postprocess_if_available(df)
    else:
        df["postprocessed_label"] = df["predicted_label"]

    return df