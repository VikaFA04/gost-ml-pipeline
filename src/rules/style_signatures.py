"""Style-class detection for rule_engine guards.

Plan 02 (Wave 1) of phase 01-engine-guardrails-cohesion-audit.
"""

from __future__ import annotations

import re
from typing import Literal

from docx.text.paragraph import Paragraph

StyleClass = Literal["heading", "toc", "caption", "list", "body"]

# Regex constants — mirror rule_engine.LIST_STYLE_RE / HEADING_STYLE_RE so the guard
# uses the same vocabulary as the existing autofix paths.
LIST_STYLE_RE = re.compile(r"list|список|маркирован|нумерован", re.IGNORECASE)
HEADING_STYLE_RE = re.compile(r"heading|заголов", re.IGNORECASE)
TOC_STYLE_RE = re.compile(r"toc|содержание", re.IGNORECASE)
CAPTION_STYLE_RE = re.compile(r"caption|подпись", re.IGNORECASE)


def classify_style(paragraph: Paragraph) -> StyleClass:
    """Return the StyleClass for a paragraph by matching its style name.

    Check order is toc → heading → caption → list → body so that names like
    "TOC Heading" classify as "toc" (the more specific match), not "heading".
    Follows the rule_engine._paragraph_has_*_style try/except → "body" idiom.
    """
    try:
        if paragraph.style is None or paragraph.style.name is None:
            return "body"
        name = str(paragraph.style.name)
    except Exception:
        return "body"

    if TOC_STYLE_RE.search(name):
        return "toc"
    if HEADING_STYLE_RE.search(name):
        return "heading"
    if CAPTION_STYLE_RE.search(name):
        return "caption"
    if LIST_STYLE_RE.search(name):
        return "list"
    return "body"
