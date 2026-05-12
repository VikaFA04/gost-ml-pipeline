"""Style-class detection for rule_engine guards.

Stub created in Wave 0 of phase 01-engine-guardrails-cohesion-audit (per CLAUDE.md TDD).
Plan 02 (Wave 1) implements the real regex-based classify_style.
"""

from __future__ import annotations

import re
from typing import Literal

from docx.text.paragraph import Paragraph

StyleClass = Literal["heading", "toc", "caption", "list", "body"]

# Placeholder regex constants — Plan 02 replaces with real patterns.
LIST_STYLE_RE = re.compile(r"$^")
HEADING_STYLE_RE = re.compile(r"$^")
TOC_STYLE_RE = re.compile(r"$^")
CAPTION_STYLE_RE = re.compile(r"$^")


def classify_style(paragraph: Paragraph) -> StyleClass:
    """Stub — always returns 'body'. Plan 02 implements real classification."""
    return "body"
