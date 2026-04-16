"""Shared preprocessing for prepared block datasets."""

from __future__ import annotations

import pandas as pd

from src.preprocessing.cleaners import clean_text
from src.preprocessing.normalizers import normalize_categorical, normalize_numeric
from src.utils.exceptions import DataValidationError


def preprocess_blocks(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned dataframe ready for feature extraction."""
    processed = df.copy()
    processed["text"] = processed["text"].map(clean_text)
    processed["kind"] = processed["kind"].map(normalize_categorical)
    processed["alignment"] = processed["alignment"].map(normalize_categorical)
    processed["style"] = processed["style"].map(normalize_categorical)
    processed["bold_ratio"] = processed["bold_ratio"].map(normalize_numeric)
    processed["label_core"] = processed["label_core"].astype(str).str.strip()
    processed["split"] = processed["split"].astype(str).str.strip()

    non_empty_mask = processed["text"].str.len() > 0
    if not non_empty_mask.any():
        raise DataValidationError("All rows became empty after preprocessing.")

    processed = processed.loc[non_empty_mask].reset_index(drop=True)
    if processed.empty:
        raise DataValidationError("No rows remain after preprocessing.")

    return processed
