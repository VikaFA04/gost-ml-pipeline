"""Structural feature encoders for the baseline model."""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.features.text_features import build_tfidf_vectorizer


def build_feature_union() -> ColumnTransformer:
    """Combine text and structural features into one transformer."""
    return ColumnTransformer(
        transformers=[
            ("text", build_tfidf_vectorizer(), "text"),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                ["kind", "alignment", "style"],
            ),
            (
                "numeric",
                Pipeline([("scaler", StandardScaler())]),
                ["bold_ratio"],
            ),
        ],
        remainder="drop",
        sparse_threshold=0.3,
    )
