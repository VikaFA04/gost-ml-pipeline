from __future__ import annotations

import re

import pandas as pd

NUMBERED_LIST_ITEM_RE = re.compile(r"^\s*\d+[\.\)]\s+")
LIST_STYLE_RE = re.compile(r"list|список|маркирован|нумерован", re.IGNORECASE)
TEXT_LETTER_RE = re.compile(r"[A-Za-zА-Яа-яЁё]")
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
        texts = [_safe_text(value) for value in group["text"].tolist()]

        for position, (_, row) in enumerate(group.iterrows()):
            if labels[position] == "body_text" and _is_structural_list_item(row, texts[position]):
                labels[position] = "list_item"

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
        result_parts.append(group)

    return pd.concat(result_parts, axis=0).sort_index()
