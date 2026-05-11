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
