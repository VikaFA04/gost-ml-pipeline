"""Dataset loading helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_csv_dataset(csv_path: Path) -> pd.DataFrame:
    """Load a CSV dataset into a dataframe."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset file was not found: {csv_path}")
    if csv_path.suffix.lower() != ".csv":
        raise ValueError(f"Expected a CSV dataset, got: {csv_path}")
    return pd.read_csv(csv_path)
