"""Style-class detection for rule_engine guards.

Stub created in Wave 0 of phase 01-engine-guardrails-cohesion-audit (per CLAUDE.md TDD).
Plan 02 (Wave 1) implements the real regex-based classify_style.
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
    """Stub — always returns 'body'. Plan 02 implements real classification."""
    return "body"
