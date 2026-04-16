"""Validation utilities for prepared block classification datasets."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from src.data.contracts import ALLOWED_SPLITS, REQUIRED_DATASET_COLUMNS, SPLIT_COLUMN, TARGET_COLUMN
from src.utils.exceptions import DataValidationError


def validate_required_columns(df: pd.DataFrame, required_columns: Iterable[str] | None = None) -> None:
    """Ensure the dataframe contains all required columns."""
    required = list(required_columns or REQUIRED_DATASET_COLUMNS)
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise DataValidationError(f"Missing required columns: {missing}")


def validate_non_empty_dataset(df: pd.DataFrame, dataset_name: str) -> None:
    """Ensure the dataframe contains at least one row."""
    if df.empty:
        raise DataValidationError(f"Dataset '{dataset_name}' is empty.")


def validate_text_column(df: pd.DataFrame) -> None:
    """Ensure text content exists and is not entirely blank."""
    if df["text"].isna().all():
        raise DataValidationError("Column 'text' contains only missing values.")
    non_blank_mask = df["text"].fillna("").astype(str).str.strip().ne("")
    if not non_blank_mask.any():
        raise DataValidationError("Column 'text' contains no non-empty rows after stripping whitespace.")


def validate_target_labels(df: pd.DataFrame) -> None:
    """Ensure the target column is present and populated."""
    if TARGET_COLUMN not in df.columns:
        raise DataValidationError(f"Target column '{TARGET_COLUMN}' is missing.")
    if df[TARGET_COLUMN].isna().any():
        raise DataValidationError(f"Target column '{TARGET_COLUMN}' contains missing labels.")
    if df[TARGET_COLUMN].astype(str).str.strip().eq("").any():
        raise DataValidationError(f"Target column '{TARGET_COLUMN}' contains blank labels.")


def validate_splits(df: pd.DataFrame) -> None:
    """Ensure split assignments are valid and usable."""
    if SPLIT_COLUMN not in df.columns:
        raise DataValidationError(f"Split column '{SPLIT_COLUMN}' is missing.")

    observed_splits = set(df[SPLIT_COLUMN].dropna().astype(str).str.strip())
    invalid = sorted(observed_splits - ALLOWED_SPLITS)
    if invalid:
        raise DataValidationError(f"Unsupported split values: {invalid}")

    for required_split in ("train", "val"):
        split_size = int((df[SPLIT_COLUMN] == required_split).sum())
        if split_size == 0:
            raise DataValidationError(f"Required split '{required_split}' is empty.")


def validate_identifier_uniqueness(df: pd.DataFrame) -> None:
    """Ensure block identifiers are unique within each document."""
    duplicated_mask = df.duplicated(subset=["doc_id", "block_id"], keep=False)
    if duplicated_mask.any():
        duplicate_count = int(duplicated_mask.sum())
        raise DataValidationError(
            f"Found {duplicate_count} duplicated ('doc_id', 'block_id') key rows."
        )


def validate_prepared_dataset(df: pd.DataFrame, dataset_name: str) -> None:
    """Run the complete prepared dataset validation suite."""
    validate_required_columns(df)
    validate_non_empty_dataset(df, dataset_name)
    validate_text_column(df)
    validate_target_labels(df)
    validate_splits(df)
    validate_identifier_uniqueness(df)
