from __future__ import annotations

import pandas as pd

from src.postprocess.postprocess_rules import apply_postprocess_rules


def _row(block_id: int, text: str, predicted_label: str) -> dict[str, object]:
    return {
        "doc_id": "doc_1",
        "block_id": block_id,
        "text": text,
        "style": "Normal",
        "predicted_label": predicted_label,
    }


def test_structural_list_paragraph_overrides_body_text_prediction() -> None:
    row = _row(1, "Проверить форматирование списка;", "body_text")
    row["style"] = "List Paragraph"
    row["list_type"] = "list"
    row["list_level"] = 0
    df = pd.DataFrame([row])

    result = apply_postprocess_rules(df)

    assert result.loc[0, "postprocessed_label"] == "list_item"


def test_formula_like_list_paragraph_stays_body_text() -> None:
    row = _row(1, ",\t(1.1)", "body_text")
    row["style"] = "List Paragraph"
    row["list_type"] = "list"
    row["list_level"] = 0
    df = pd.DataFrame([row])

    result = apply_postprocess_rules(df)

    assert result.loc[0, "postprocessed_label"] == "body_text"


def test_formula_like_list_prediction_becomes_body_text() -> None:
    row = _row(1, "\t,\t(1.1)", "list_item")
    row["style"] = "List Paragraph"
    row["list_type"] = "list"
    row["list_level"] = 0
    df = pd.DataFrame([row])

    result = apply_postprocess_rules(df)

    assert result.loc[0, "postprocessed_label"] == "body_text"


def test_tabbed_list_run_after_cue_sentence_becomes_list_items() -> None:
    df = pd.DataFrame(
        [
            _row(1, "Кластеризация решает несколько важных задач:", "body_text"),
            _row(2, "\tПервый пункт", "body_text"),
            _row(3, "\tВторой пункт", "body_text"),
            _row(4, "\tТретий пункт", "body_text"),
            _row(5, "Обычный текст после списка.", "body_text"),
        ]
    )

    result = apply_postprocess_rules(df)

    assert result["postprocessed_label"].tolist() == [
        "body_text",
        "list_item",
        "list_item",
        "list_item",
        "body_text",
    ]


def test_bibliography_context_overrides_body_text_and_list_predictions() -> None:
    df = pd.DataFrame(
        [
            _row(1, "СПИСОК ИСПОЛЬЗУЕМЫХ ИСТОЧНИКОВ", "body_text"),
            _row(2, "1 Теоретическая часть", "title_section"),
            _row(3, "\tИванов И. И. Учебник. — Москва, 2020. — 120 с.", "body_text"),
            _row(4, "2 Практическая часть", "title_section"),
            _row(5, "\tData normalization / URL: https://example.test", "list_item"),
            _row(6, "ЗАКЛЮЧЕНИЕ", "body_text"),
        ]
    )

    result = apply_postprocess_rules(df)

    assert result["postprocessed_label"].tolist() == [
        "bibliography_title",
        "title_section",
        "bibliography_item",
        "title_section",
        "bibliography_item",
        "body_text",
    ]
    assert result["bibliography_section_index"].tolist() == [None, 1, 1, 2, 2, None]


def test_tabbed_bibliography_entries_keep_section_indices() -> None:
    df = pd.DataFrame(
        [
            _row(1, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "body_text"),
            _row(2, "1 Теоретическая часть", "title_section"),
            _row(3, "\tИванов И. И. Учебник по анализу данных", "body_text"),
            _row(4, "2 Практическая часть", "title_section"),
            _row(5, "\tПетров П. П. Практика кластеризации", "body_text"),
        ]
    )

    result = apply_postprocess_rules(df)

    assert result["postprocessed_label"].tolist() == [
        "bibliography_title",
        "title_section",
        "bibliography_item",
        "title_section",
        "bibliography_item",
    ]
    assert result["bibliography_section_index"].tolist() == [None, 1, 1, 2, 2]


def test_numbered_bibliography_section_titles_keep_section_context() -> None:
    df = pd.DataFrame(
        [
            _row(1, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "body_text"),
            _row(2, "1 Теоретическая часть", "title_section"),
            _row(3, "\tIvanov I. I. Text. — Moscow, 2020. — 120 p.", "body_text"),
            _row(4, "2 Практическая часть", "title_section"),
            _row(5, "\tData normalization / URL: https://example.test", "body_text"),
        ]
    )

    result = apply_postprocess_rules(df)

    assert result["postprocessed_label"].tolist() == [
        "bibliography_title",
        "title_section",
        "bibliography_item",
        "title_section",
        "bibliography_item",
    ]
    assert result["bibliography_section_index"].tolist() == [None, 1, 1, 2, 2]


def test_long_numbered_list_run_becomes_bibliography_items() -> None:
    df = pd.DataFrame(
        [_row(1, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "bibliography_title")]
        + [_row(index + 2, f"{index + 1}. Источник {index + 1}", "list_item") for index in range(8)]
    )

    result = apply_postprocess_rules(df)

    assert result.loc[result["block_id"] == 1, "postprocessed_label"].item() == "bibliography_title"
    assert set(result.loc[result["block_id"] > 1, "postprocessed_label"]) == {"bibliography_item"}


def test_long_numbered_list_without_bibliography_context_stays_list_items() -> None:
    df = pd.DataFrame(
        [_row(1, "Перед списком:", "body_text")]
        + [_row(index + 2, f"{index + 1}. Пункт {index + 1}", "list_item") for index in range(8)]
    )

    result = apply_postprocess_rules(df)

    assert set(result.loc[result["block_id"] > 1, "postprocessed_label"]) == {"list_item"}


def test_short_numbered_list_run_stays_list_items() -> None:
    df = pd.DataFrame(
        [_row(1, "Перед списком:", "body_text")]
        + [_row(index + 2, f"{index + 1}. Пункт {index + 1}", "list_item") for index in range(3)]
    )

    result = apply_postprocess_rules(df)

    assert set(result.loc[result["block_id"] > 1, "postprocessed_label"]) == {"list_item"}


def test_postprocess_preserves_non_list_predictions() -> None:
    df = pd.DataFrame(
        [
            _row(1, "Рисунок 1 - Схема", "figure_caption"),
            _row(2, "Обычный текст", "body_text"),
            _row(3, "Таблица 1 - Данные", "table_caption"),
        ]
    )

    result = apply_postprocess_rules(df)

    assert result["postprocessed_label"].tolist() == ["figure_caption", "body_text", "table_caption"]


# ============================================================================
# Phase 02 RED tests — D-01 unconditional title override + D-04 heading style detection.
# Plans 02 implements; these MUST fail today.
# ============================================================================

def _row_with_style(block_id: int, text: str, predicted_label: str, style: str = "Normal") -> dict[str, object]:
    return {
        "doc_id": "doc_phase2",
        "block_id": block_id,
        "text": text,
        "style": style,
        "predicted_label": predicted_label,
    }


def test_bibliography_title_overrides_svm_body_text() -> None:
    """D-01: BIBLIOGRAPHY_TITLE_RE match unconditionally sets label=bibliography_title
    even when SVM returned body_text. Pitfall 3 — pin the asymmetry."""
    df = pd.DataFrame([
        _row_with_style(0, "Введение", "body_text"),
        _row_with_style(1, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "body_text"),
        _row_with_style(2, "Иванов И. И. Основы теории. — М., 2020.", "body_text"),
    ])
    result = apply_postprocess_rules(df)
    labels = result["postprocessed_label"].tolist()
    # Title row MUST become bibliography_title, NOT body_text.
    assert labels[1] == "bibliography_title", (
        f"D-01 override failed: row 1 label={labels[1]!r}, expected 'bibliography_title' "
        f"(SVM said body_text, override must fire unconditionally)"
    )


def test_bibliography_subsection_detected_by_heading_style() -> None:
    """D-04: Heading 1 style INSIDE bibliography context advances
    bibliography_section_index, even when the heading TEXT does NOT match
    BIBLIOGRAPHY_SUBHEADING_RE."""
    df = pd.DataFrame([
        _row_with_style(0, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "bibliography_title"),
        _row_with_style(1, "ТЕОРЕТИЧЕСКАЯ ЧАСТЬ", "body_text", style="Heading 1"),
        _row_with_style(2, "Иванов И. И. Основы теории. — М., 2020.", "body_text"),
        _row_with_style(3, "ИССЛЕДОВАТЕЛЬСКИЙ РАЗДЕЛ", "body_text", style="Heading 1"),
        _row_with_style(4, "Петров П. П. Введение. — СПб., 2019.", "body_text"),
    ])
    result = apply_postprocess_rules(df)
    section_indices = result["bibliography_section_index"].tolist()
    # After D-04: row 1 advances section to 1; row 3 advances to 2.
    # bibliography_section_index for entries 2 and 4 reflects the active section.
    assert section_indices[2] == 1, (
        f"D-04: entry under first Heading 1 subsection should have section_index=1, got {section_indices[2]!r}"
    )
    assert section_indices[4] == 2, (
        f"D-04: entry under second Heading 1 subsection should have section_index=2, got {section_indices[4]!r}"
    )


def test_bibliography_subsection_fallback_regex_still_works() -> None:
    """D-04 fallback: rows with Normal style whose TEXT matches the legacy
    BIBLIOGRAPHY_SUBHEADING_RE must still be classified as subsection headings.
    Per researcher Open Question 2: the legacy regex stays in the codebase
    because src/evaluation/format_regression_audit.py imports it.

    This test pins ONE non-numbered text that matches BIBLIOGRAPHY_SUBHEADING_RE.
    Implementer in Plan 02 must inspect the regex to pick a matching string;
    a safe choice is a section title that is literally listed in the regex
    alternation. If no clean matching text exists, this test SKIPS with a
    clear message rather than vacuously passing.
    """
    import re
    from src.postprocess.postprocess_rules import BIBLIOGRAPHY_SUBHEADING_RE

    # Pick the first non-empty literal alternation member from the regex pattern.
    # If pattern uses character classes/quantifiers, fall back to a known
    # working literal — implementer in Plan 02 may adjust the literal.
    candidates = ["Книги и брошюры", "Статьи", "Электронные ресурсы", "Стандарты"]
    matching = next((c for c in candidates if BIBLIOGRAPHY_SUBHEADING_RE.search(c)), None)
    if matching is None:
        import pytest
        pytest.skip("No literal candidate matches BIBLIOGRAPHY_SUBHEADING_RE — adjust candidate list in Plan 02")

    df = pd.DataFrame([
        _row_with_style(0, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "bibliography_title"),
        _row_with_style(1, matching, "body_text"),   # Normal style — falls back to regex
        _row_with_style(2, "Иванов И. И. Основы. — М., 2020.", "body_text"),
    ])
    result = apply_postprocess_rules(df)
    section_indices = result["bibliography_section_index"].tolist()
    assert section_indices[2] == 1, (
        f"D-04 fallback: entry under regex-detected subsection should have section_index=1, got {section_indices[2]!r}"
    )
