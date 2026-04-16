"""Text feature configuration for the baseline model."""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer


def build_tfidf_vectorizer() -> TfidfVectorizer:
    """Create the TF-IDF vectorizer used in the baseline pipeline."""
    return TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.98,
        sublinear_tf=True,
        strip_accents=None,
    )
