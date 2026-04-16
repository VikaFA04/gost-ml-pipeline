"""Baseline classifier construction."""

from __future__ import annotations

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.features.structural_features import build_feature_union


def build_baseline_pipeline(random_state: int) -> Pipeline:
    """Create the TF-IDF + structural feature baseline pipeline."""
    return Pipeline(
        steps=[
            ("features", build_feature_union()),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=random_state,
                ),
            ),
        ]
    )
