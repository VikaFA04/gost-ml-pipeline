from __future__ import annotations

import pandas as pd

from src.features.pattern_features import TextPatternFeatures


def test_text_pattern_features_detect_document_markers() -> None:
    transformer = TextPatternFeatures()
    features = transformer.transform(
        pd.DataFrame(
            {
                "text": [
                    "— параметр модели;",
                    "1.2 Методы анализа",
                    "Рисунок 1 — Схема",
                    "URL: https://example.test",
                    "где x = y + 1",
                ]
            }
        )
    )

    assert features.loc[0, "has_list_marker"] == 1
    assert features.loc[0, "ends_semicolon"] == 1
    assert features.loc[1, "has_numbered_heading"] == 1
    assert features.loc[2, "starts_figure"] == 1
    assert features.loc[3, "has_biblio_cue"] == 1
    assert features.loc[4, "has_formula_cue"] == 1


def test_text_pattern_features_are_numeric_and_row_stable() -> None:
    transformer = TextPatternFeatures()
    features = transformer.transform(pd.Series(["СОДЕРЖАНИЕ", None]))

    assert len(features) == 2
    assert features.loc[0, "upper_ratio"] == 1.0
    assert features.loc[1, "char_len"] == 0
    assert set(features.dtypes.astype(str)) <= {"int64", "float64"}
