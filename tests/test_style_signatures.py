"""Unit tests for src/rules/style_signatures.classify_style.

RED-state tests written in Wave 0 (phase 01-engine-guardrails-cohesion-audit).
Plan 02 (Wave 1) implements style_signatures.py so these turn GREEN.
"""

from __future__ import annotations

from types import SimpleNamespace

from docx import Document

from src.rules.style_signatures import classify_style


def _paragraph_with_style_name(name: str):
    """Shim — classify_style only reads .style.name, so a SimpleNamespace suffices.

    Avoids the python-docx limitation that `paragraph.style = "Заголовок 1 Знак"`
    raises KeyError because the style is not registered in the document.
    """
    return SimpleNamespace(style=SimpleNamespace(name=name))


def test_classify_style_heading_en_ru() -> None:
    for name in [
        "Heading 1",
        "Heading 2",
        "Heading 3",
        "heading 1",
        "Заголовок 1",
        "Заголовок 2",
        "Заголовок 1 Знак",
        "Заголовок Первого уровня (ГОСТ)",
    ]:
        assert classify_style(_paragraph_with_style_name(name)) == "heading", name


def test_classify_style_toc_en_ru() -> None:
    for name in [
        "toc 1",
        "toc 2",
        "toc 3",
        "TOC Heading",  # must be "toc" not "heading" — check order pinned here
        "содержание",
        "содержание основной",
        'Название "Содержание" (ГОСТ)',
    ]:
        assert classify_style(_paragraph_with_style_name(name)) == "toc", name


def test_classify_style_caption_en_ru() -> None:
    for name in [
        "Caption",
        "caption",
        "ПодписьРисунка",
        "Подпись рисунка (ГОСТ)",
        "Подпись таблицы (ГОСТ)",
    ]:
        assert classify_style(_paragraph_with_style_name(name)) == "caption", name


def test_classify_style_list_en_ru() -> None:
    for name in [
        "List Paragraph",
        "список",
        "Маркированный список (ГОСТ)",
        "Номерованный список (ГОСТ)",
    ]:
        assert classify_style(_paragraph_with_style_name(name)) == "list", name


def test_classify_style_body_negatives() -> None:
    for name in [
        "Normal",
        "Обычный",
        "Body Text",
        "header",
        "Footer",
        "",
        "mw-headline",  # contains "head" but not "heading" → must NOT match HEADING_STYLE_RE
    ]:
        assert classify_style(_paragraph_with_style_name(name)) == "body", name


def test_classify_style_handles_none_style() -> None:
    # paragraph.style is None — must NOT raise, must return "body"
    paragraph = SimpleNamespace(style=None)
    assert classify_style(paragraph) == "body"

    # Also covers the real-Document path where style.name might be None.
    document = Document()
    real_paragraph = document.add_paragraph("default Normal")
    assert classify_style(real_paragraph) == "body"
