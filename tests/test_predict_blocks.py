from __future__ import annotations

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC

from src.config import FEATURE_COLUMNS
from src.features.pattern_features import TextPatternFeatures
from src.predict_blocks import predict_blocks


def _build_small_model() -> Pipeline:
    train_df = pd.DataFrame(
        [
            {"text": "Обычный текст", "kind": "paragraph", "alignment": "JUSTIFY", "style": "Body Text", "bold_ratio": 0.0},
            {"text": "1. Пункт списка", "kind": "paragraph", "alignment": "LEFT", "style": "Normal", "bold_ratio": 0.0},
            {"text": "Рисунок 1 - Схема", "kind": "paragraph", "alignment": "CENTER", "style": "Normal", "bold_ratio": 0.0},
            {"text": "Таблица 1 - Данные", "kind": "paragraph", "alignment": "CENTER", "style": "Normal", "bold_ratio": 1.0},
        ]
    )
    labels = ["body_text", "list_item", "figure_caption", "table_caption"]

    model = Pipeline(
        steps=[
            (
                "preprocess",
                ColumnTransformer(
                    transformers=[
                        ("text", TfidfVectorizer(min_df=1), "text"),
                        ("patterns", TextPatternFeatures(), ["text"]),
                        ("cat", OneHotEncoder(handle_unknown="ignore"), ["kind", "alignment", "style"]),
                        ("num", "passthrough", ["bold_ratio"]),
                    ]
                ),
            ),
            ("classifier", LinearSVC(max_iter=10000, random_state=42)),
        ]
    )
    model.fit(train_df[FEATURE_COLUMNS], labels)
    return model


def test_predict_blocks_returns_audit_contract_columns(tmp_path) -> None:
    model_path = tmp_path / "model.joblib"
    joblib.dump(_build_small_model(), model_path)
    blocks_df = pd.DataFrame(
        [
            {"text": "1. Пункт списка", "kind": "paragraph", "alignment": "LEFT", "style": "Normal", "bold_ratio": 0.0}
        ]
    )

    result = predict_blocks(model_path=model_path, blocks_df=blocks_df, apply_rules=True)

    assert len(result) == 1
    assert {"predicted_label", "confidence_score", "low_confidence", "postprocessed_label"}.issubset(result.columns)
    assert result["predicted_label"].notna().all()
    assert result["confidence_score"].notna().all()
