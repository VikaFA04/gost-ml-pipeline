"""Text cleanup helpers."""

from __future__ import annotations

import re
import unicodedata


WHITESPACE_PATTERN = re.compile(r"\s+")


def clean_text(text: object) -> str:
    """Normalize text into a stable string representation."""
    if text is None:
        return ""

    normalized = unicodedata.normalize("NFKC", str(text))
    normalized = normalized.replace("\u00a0", " ")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = WHITESPACE_PATTERN.sub(" ", normalized)
    return normalized.strip()
