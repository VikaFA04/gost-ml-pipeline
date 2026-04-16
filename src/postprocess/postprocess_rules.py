from __future__ import annotations

import re
from typing import List

import pandas as pd


RE_WORD = re.compile(r"[A-Za-zА-Яа-яЁё0-9]+")
RE_YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")
RE_URL = re.compile(r"(https?://|www\.|doi\.org|doi:|URL:)", re.IGNORECASE)
RE_CITATION = re.compile(r"\[[^\]]+\]")
RE_INITIALS = re.compile(r"\b[А-ЯA-Z]\.\s?[А-ЯA-Z]\.")
RE_NUMBERED_HEADING = re.compile(r"^\s*\d+(\.\d+)*[\.)]?\s+")
RE_LIST_MARKER = re.compile(r"^\s*(?:[-—–•]|\d+[\.\)])\s+")

RE_BIBLIO_TITLE = re.compile(
    r"(список\s+использованных\s+источников|список\s+литературы|библиографический\s+список)",
    re.IGNORECASE,
)
RE_APPENDIX = re.compile(r"^\s*приложени[ея]\b", re.IGNORECASE)
RE_TABLE = re.compile(r"^\s*таблица\b", re.IGNORECASE)
RE_FIGURE = re.compile(r"^\s*(рисунок|рис\.)\b", re.IGNORECASE)
RE_LISTING = re.compile(r"^\s*листинг\b", re.IGNORECASE)
RE_GRAPH = re.compile(r"^\s*график\b", re.IGNORECASE)


def safe_text(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()


def word_count(text: str) -> int:
    return len(RE_WORD.findall(text))


def upper_ratio(text: str) -> float:
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return 0.0
    upper = [ch for ch in letters if ch.isupper()]
    return len(upper) / len(letters)


def is_short(text: str, limit: int = 12) -> bool:
    return word_count(text) <= limit


def contains_biblio_cues(text: str) -> bool:
    t = text.lower()
    cues = [
        "электронный ресурс",
        "режим доступа",
        "дата обращения",
        "дата доступа",
        "isbn",
        "issn",
        "doi",
        "//",
        "— м.:",
        "— спб.:",
        "— м.",
        "— с.",
        "url:",
    ]
    return (
        bool(RE_URL.search(text))
        or bool(RE_YEAR.search(text))
        or bool(RE_INITIALS.search(text))
        or bool(RE_CITATION.search(text))
        or any(cue in t for cue in cues)
    )


def is_main_text_style(style: str) -> bool:
    s = style.lower()
    return any(
        key in s
        for key in [
            "основной текст",
            "body text",
            "normal",
            "база",
            "текст обычный",
            "гост_осн_текст",
            "paragraph",
        ]
    )


def is_list_style(style: str) -> bool:
    s = style.lower()
    return "list" in s


def is_heading1_style(style: str) -> bool:
    s = style.lower()
    return any(key in s for key in ["heading 1", "заг_ур1", "heading1"])


def is_heading2_style(style: str) -> bool:
    s = style.lower()
    return any(key in s for key in ["heading 2", "заг_ур2", "heading2"])


def is_all_caps_heading(text: str) -> bool:
    wc = word_count(text)
    return wc > 0 and wc <= 8 and upper_ratio(text) >= 0.75


def starts_with_table(text: str) -> bool:
    return bool(RE_TABLE.search(text))


def starts_with_figure_like(text: str) -> bool:
    return bool(RE_FIGURE.search(text) or RE_LISTING.search(text) or RE_GRAPH.search(text))


def starts_with_biblio_title(text: str) -> bool:
    return bool(RE_BIBLIO_TITLE.search(text))


def starts_with_appendix(text: str) -> bool:
    return bool(RE_APPENDIX.search(text))


def starts_with_numbered_heading(text: str) -> bool:
    return bool(RE_NUMBERED_HEADING.search(text))


def is_probable_list_item(text: str, style: str) -> bool:
    if is_list_style(style):
        return True
    return bool(RE_LIST_MARKER.search(text))


def apply_postprocess_rules(
    df: pd.DataFrame,
    pred_col: str = "predicted_label",
    out_col: str = "postprocessed_label",
) -> pd.DataFrame:
    """
    Применяет набор детерминированных правил к предсказаниям базовой модели.
    Рассчитано на таблицу блоков документа с колонками:
    doc_id, block_id, text, style, alignment, predicted_label
    """
    required = {"doc_id", "block_id", "text", "style", pred_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Отсутствуют обязательные колонки: {sorted(missing)}")

    result_parts: List[pd.DataFrame] = []

    for doc_id, grp in df.groupby("doc_id", sort=False):
        grp = grp.copy().sort_values("block_id")
        new_labels = []

        in_biblio_section = False
        in_appendix_section = False

        for row in grp.itertuples(index=False):
            text = safe_text(getattr(row, "text", ""))
            style = safe_text(getattr(row, "style", ""))
            pred = getattr(row, pred_col)

            wc = word_count(text)
            t_low = text.lower()

            # Сильные текстовые триггеры разделов
            if starts_with_biblio_title(text):
                label = "bibliography_title"
                in_biblio_section = True
                new_labels.append(label)
                continue

            if starts_with_appendix(text) and is_short(text, 4):
                label = "appendix_title"
                in_appendix_section = True
                new_labels.append(label)
                continue

            # Начало приложений может завершать библиографический раздел
            if in_biblio_section and starts_with_appendix(text):
                in_biblio_section = False
                in_appendix_section = True

            # Сильные триггеры подписей
            if starts_with_table(text):
                label = "table_caption"
                new_labels.append(label)
                continue

            if starts_with_figure_like(text):
                label = "figure_caption"
                new_labels.append(label)
                continue

            # Явные заголовки
            if is_heading1_style(style) or (is_all_caps_heading(text) and wc <= 4):
                label = "title_section"
                new_labels.append(label)
                continue

            if is_heading2_style(style) or starts_with_numbered_heading(text):
                # По количеству точек грубо различаем раздел/подраздел
                if text.strip().startswith(tuple(str(i) for i in range(10))):
                    dot_count = text.split(" ")[0].count(".")
                    label = "title_section" if dot_count <= 0 else "title_subsection"
                else:
                    label = "title_subsection"
                new_labels.append(label)
                continue

            # Библиография по контексту + признакам
            if in_biblio_section:
                if contains_biblio_cues(text) or is_list_style(style) or wc <= 30:
                    label = "bibliography_item"
                else:
                    label = "body_text"
                new_labels.append(label)
                continue

            # Постобработка по предсказанному классу
            label = pred

            # bibliography_item вне раздела библиографии обычно ложный
            if pred == "bibliography_item":
                if contains_biblio_cues(text) and (is_list_style(style) or wc <= 25):
                    label = "bibliography_item"
                else:
                    label = "body_text"

            # figure_caption без явного маркера чаще обычный текст
            elif pred == "figure_caption":
                if not starts_with_figure_like(text):
                    label = "body_text"

            # table_caption без слова "Таблица" чаще обычный текст
            elif pred == "table_caption":
                if not starts_with_table(text):
                    label = "body_text"

            # title_section/title_subsection на длинных абзацах — почти всегда ошибка
            elif pred in {"title_section", "title_subsection"}:
                if is_main_text_style(style) and wc > 10 and not starts_with_numbered_heading(text):
                    label = "body_text"

            # list_item без маркеров списка на длинных абзацах — почти всегда ошибка
            elif pred == "list_item":
                if not is_probable_list_item(text, style) and wc > 10:
                    label = "body_text"

            # Для body_text усиливаем некоторые эвристики
            elif pred == "body_text":
                if is_probable_list_item(text, style) and wc <= 25:
                    label = "list_item"

            new_labels.append(label)

        grp[out_col] = new_labels
        result_parts.append(grp)

    return pd.concat(result_parts, axis=0).sort_index()