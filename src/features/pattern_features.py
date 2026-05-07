from __future__ import annotations

import re
from typing import Any

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9]+")
LIST_MARKER_RE = re.compile(r"^\s*(?:[-—–•●■◦]|\d+[\.\)]|[A-Za-zА-Яа-я][\.\)])\s+")
NUMBERED_HEADING_RE = re.compile(r"^\s*\d+(?:\.\d+)*\s+")
FIGURE_CAPTION_RE = re.compile(r"^\s*(?:рисунок|рис\.)\b", re.IGNORECASE)
TABLE_CAPTION_RE = re.compile(r"^\s*таблица\b", re.IGNORECASE)
BIBLIO_CUE_RE = re.compile(
    r"(электронный ресурс|режим доступа|дата обращения|isbn|issn|doi|https?://|www\.|//|—\s*м\.|—\s*с\.)",
    re.IGNORECASE,
)
FORMULA_CUE_RE = re.compile(r"[=∑√±≤≥×]|\b(?:где|sin|cos|log|ln)\b", re.IGNORECASE)


def _as_text_series(values: Any) -> pd.Series:
    if isinstance(values, pd.DataFrame):
        source = values.iloc[:, 0]
    elif isinstance(values, pd.Series):
        source = values
    else:
        source = pd.Series(values).squeeze()
    return pd.Series(source).fillna("").astype(str)


def _word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def _upper_ratio(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    return sum(char.isupper() for char in letters) / len(letters)


class TextPatternFeatures(BaseEstimator, TransformerMixin):
    """Extract deterministic text-shape features available for both training and DOCX inference."""

    def fit(self, values: Any, y: Any = None) -> "TextPatternFeatures":
        return self

    def transform(self, values: Any) -> pd.DataFrame:
        text = _as_text_series(values)
        return pd.DataFrame(
            {
                "char_len": text.str.len(),
                "word_count": text.map(_word_count),
                "upper_ratio": text.map(_upper_ratio),
                "has_list_marker": text.map(lambda value: int(bool(LIST_MARKER_RE.search(value)))),
                "has_numbered_heading": text.map(lambda value: int(bool(NUMBERED_HEADING_RE.search(value)))),
                "starts_figure": text.map(lambda value: int(bool(FIGURE_CAPTION_RE.search(value)))),
                "starts_table": text.map(lambda value: int(bool(TABLE_CAPTION_RE.search(value)))),
                "has_biblio_cue": text.map(lambda value: int(bool(BIBLIO_CUE_RE.search(value)))),
                "has_formula_cue": text.map(lambda value: int(bool(FORMULA_CUE_RE.search(value)))),
                "ends_semicolon": text.map(lambda value: int(value.strip().endswith(";"))),
            }
        )
