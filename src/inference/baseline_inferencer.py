"""Baseline inference using saved classical ML artifacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.predict_blocks import predict_blocks


def run_baseline_inference(model_path: Path, blocks_df: pd.DataFrame) -> pd.DataFrame:
    """Run baseline inference using an existing saved joblib model."""
    return predict_blocks(model_path=model_path, blocks_df=blocks_df, apply_rules=True)
