from __future__ import annotations

import re

import pandas as pd

NUMBERED_LIST_ITEM_RE = re.compile(r"^\s*\d+[\.\)]\s+")
LIST_STYLE_RE = re.compile(r"list|список|маркирован|нумерован", re.IGNORECASE)
TEXT_LETTER_RE = re.compile(r"[A-Za-zА-Яа-яЁё]")
LIST_INTRO_RE = re.compile(r":\s*$")
LIST_MARKER_FRAGMENT_RE = re.compile(r"^\s*(?:[-—–•●■◦]|\d+[\.\)]|[A-Za-zА-Яа-я][\.\)])")
BIBLIOGRAPHY_TITLE_RE = re.compile(
    r"^(список\s+(использованных|используемых)\s+источников|библиографический\s+список|литература)$",
    re.IGNORECASE,
)
BIBLIOGRAPHY_SUBHEADING_RE = re.compile(
    r"^(?:\d+\s*)?(теоретическая\s+часть|практическая\s+часть)$",
    re.IGNORECASE,
)
BIBLIOGRAPHY_STOP_RE = re.compile(r"^(заключение|приложени[ея].*)$", re.IGNORECASE)
BIBLIOGRAPHY_ENTRY_RE = re.compile(
    r"(url:|https?://|//|\b(19|20)\d{2}\b|isbn|гост|—\s*\d+\s*с\.?)",
    re.IGNORECASE,
)
MIN_BIBLIOGRAPHY_RUN_LENGTH = 8


def _safe_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _is_numbered_list_item(text: str) -> bool:
    return bool(NUMBERED_LIST_ITEM_RE.search(text))


def _is_formula_like(text: str) -> bool:
    normalized = " ".join(text.split())
    if not normalized:
        return True
    if not TEXT_LETTER_RE.search(normalized):
        return True
    return bool(re.fullmatch(r"[,;.\-\s\(\)\d\.]+", normalized))


def _has_list_metadata(row: pd.Series) -> bool:
    list_type = row.get("list_type")
    if not pd.isna(list_type) and str(list_type).strip():
        return True
    return LIST_STYLE_RE.search(_safe_text(row.get("style"))) is not None


def _is_structural_list_item(row: pd.Series, text: str) -> bool:
    return _has_list_metadata(row) and not _is_formula_like(text)


def _is_bibliography_title(text: str) -> bool:
    return BIBLIOGRAPHY_TITLE_RE.search(text) is not None


def _is_bibliography_subheading(text: str) -> bool:
    return BIBLIOGRAPHY_SUBHEADING_RE.search(text) is not None


def _stops_bibliography_context(text: str, label: str) -> bool:
    if _is_bibliography_subheading(text):
        return False
    if label in {"appendix_title", "title_section", "title_subsection", "toc_title"}:
        return True
    return BIBLIOGRAPHY_STOP_RE.search(text) is not None


def _looks_like_bibliography_entry(row: pd.Series, text: str) -> bool:
    if _is_formula_like(text):
        return False
    return _has_list_metadata(row) or _looks_like_list_fragment(text)


def _looks_like_list_fragment(text: str) -> bool:
    if _is_formula_like(text):
        return False
    stripped = text.strip()
    if not stripped or len(stripped) > 180 or len(stripped.split()) > 20:
        return False
    if text.lstrip(" ").startswith("\t"):
        return True
    return LIST_MARKER_FRAGMENT_RE.search(text) is not None


def _is_list_intro(text: str) -> bool:
    stripped = text.strip()
    if not stripped or len(stripped) > 200:
        return False
    return LIST_INTRO_RE.search(stripped) is not None


def _has_bibliography_context(labels: list[str], index: int) -> bool:
    return any(label == "bibliography_title" for label in labels[:index])


def apply_postprocess_rules(
    df: pd.DataFrame,
    pred_col: str = "predicted_label",
    out_col: str = "postprocessed_label",
) -> pd.DataFrame:
    """Apply conservative sequence-level corrections to model predictions."""
    required = {"doc_id", "block_id", "text", pred_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Отсутствуют обязательные колонки: {sorted(missing)}")

    result_parts: list[pd.DataFrame] = []

    for _, group in df.groupby("doc_id", sort=False):
        group = group.copy().sort_values("block_id")
        labels = [str(value) for value in group[pred_col].tolist()]
        texts = ["" if pd.isna(value) else str(value) for value in group["text"].tolist()]
        section_indices: list[int | None] = [None] * len(labels)

        for position, (_, row) in enumerate(group.iterrows()):
            if labels[position] == "body_text" and _is_structural_list_item(row, texts[position]):
                labels[position] = "list_item"

        index = 0
        while index < len(labels):
            if labels[index] != "body_text" or not _is_list_intro(texts[index]):
                index += 1
                continue

            run_start = index + 1
            run_end = run_start
            while run_end < len(labels):
                next_text = texts[run_end]
                next_label = labels[run_end]
                if next_label != "body_text":
                    break
                if _is_bibliography_title(next_text) or _is_bibliography_subheading(next_text):
                    break
                if not _looks_like_list_fragment(next_text):
                    break
                run_end += 1

            if run_end - run_start >= 2:
                for position in range(run_start, run_end):
                    labels[position] = "list_item"

            index = max(run_end, index + 1)

        in_bibliography = False
        bibliography_section_index = 0
        for position, (_, row) in enumerate(group.iterrows()):
            text = texts[position]
            label = labels[position]
            if _is_bibliography_title(text):
                labels[position] = "bibliography_title"
                in_bibliography = True
                continue
            if in_bibliography and _stops_bibliography_context(text, label):
                in_bibliography = False
            if not in_bibliography:
                continue
            if _is_bibliography_subheading(text):
                bibliography_section_index += 1
                if label not in {"title_section", "title_subsection"}:
                    labels[position] = "bibliography_title"
                section_indices[position] = bibliography_section_index
            elif label in {"body_text", "list_item"} and _looks_like_bibliography_entry(row, text):
                labels[position] = "bibliography_item"
                section_indices[position] = bibliography_section_index or None

        index = 0
        while index < len(labels):
            if labels[index] == "list_item" and _is_numbered_list_item(texts[index]):
                end = index
                while (
                    end < len(labels)
                    and labels[end] == "list_item"
                    and _is_numbered_list_item(texts[end])
                ):
                    end += 1

                if end - index >= MIN_BIBLIOGRAPHY_RUN_LENGTH and _has_bibliography_context(labels, index):
                    for item_index in range(index, end):
                        labels[item_index] = "bibliography_item"

                index = end
            else:
                index += 1

        group[out_col] = labels
        group["bibliography_section_index"] = pd.Series(section_indices, dtype=object).to_numpy()
        result_parts.append(group)

    return pd.concat(result_parts, axis=0).sort_index()
