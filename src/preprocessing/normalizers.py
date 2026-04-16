"""Field normalization helpers for structural features."""

from __future__ import annotations

import pandas as pd


def normalize_categorical(value: object, missing_token: str = "__MISSING__") -> str:
    """Normalize a categorical value into a clean string token."""
    if pd.isna(value):
        return missing_token

    normalized = str(value).strip()
    return normalized if normalized else missing_token


def normalize_numeric(value: object, default: float = 0.0) -> float:
    """Normalize a numeric value with an explicit fallback."""
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Unable to parse numeric value '{value}'") from exc
