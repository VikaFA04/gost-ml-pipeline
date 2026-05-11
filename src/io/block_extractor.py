from __future__ import annotations

from pathlib import Path
from typing import Any
import re

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.table import Table
from docx.text.paragraph import Paragraph

from src.io.docx_reader import iter_block_items


ALIGNMENT_MAP = {
    WD_ALIGN_PARAGRAPH.LEFT: "LEFT",
    WD_ALIGN_PARAGRAPH.CENTER: "CENTER",
    WD_ALIGN_PARAGRAPH.RIGHT: "RIGHT",
    WD_ALIGN_PARAGRAPH.JUSTIFY: "JUSTIFY",
    WD_ALIGN_PARAGRAPH.DISTRIBUTE: "DISTRIBUTE",
    WD_ALIGN_PARAGRAPH.JUSTIFY_MED: "JUSTIFY",
    WD_ALIGN_PARAGRAPH.JUSTIFY_HI: "JUSTIFY",
    WD_ALIGN_PARAGRAPH.JUSTIFY_LOW: "JUSTIFY",
    WD_ALIGN_PARAGRAPH.THAI_JUSTIFY: "JUSTIFY",
}

LIST_STYLE_RE = re.compile(r"list|список|маркирован|нумерован", re.IGNORECASE)
NUMBERED_MARKER_RE = re.compile(r"^\s*(?:\d+[\.\)]|[A-Za-zА-Яа-я][\.\)])\s+")
BULLET_MARKER_RE = re.compile(r"^\s*[-—–•●■◦]\s+")


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_alignment(paragraph: Paragraph) -> str | None:
    alignment = paragraph.alignment
    if alignment is None:
        return None
    return ALIGNMENT_MAP.get(alignment, str(alignment))


def get_style_name(paragraph: Paragraph) -> str:
    try:
        if paragraph.style is not None and paragraph.style.name is not None:
            return str(paragraph.style.name)
    except Exception:
        pass
    return "Normal"


def compute_bold_ratio_from_runs(paragraph: Paragraph) -> float:
    """
    Считает долю символов, набранных полужирным.
    Если run пустой, не учитываем его.
    """
    total_chars = 0
    bold_chars = 0

    for run in paragraph.runs:
        text = run.text or ""
        char_count = len(text.strip())
        if char_count == 0:
            continue

        total_chars += char_count
        if bool(run.bold):
            bold_chars += char_count

    if total_chars == 0:
        return 0.0

    return bold_chars / total_chars


def extract_list_metadata(paragraph: Paragraph) -> tuple[str | None, int | None]:
    """Extract conservative list metadata from paragraph numbering and visible markers."""
    list_type: str | None = None
    list_level: int | None = None
    has_numbering = False

    try:
        p_pr = paragraph._p.pPr
        if p_pr is not None and p_pr.numPr is not None and p_pr.numPr.ilvl is not None:
            list_level = int(p_pr.numPr.ilvl.val)
            has_numbering = True
    except Exception:
        list_level = None

    text = "" if paragraph.text is None else str(paragraph.text)
    style_name = get_style_name(paragraph)
    word_count = len(text.split())
    is_short_candidate = len(text) <= 300 and word_count <= 40

    if has_numbering and BULLET_MARKER_RE.match(text):
        list_type = "bullet"
    elif has_numbering and NUMBERED_MARKER_RE.match(text):
        list_type = "numbered"
    elif has_numbering:
        list_type = "list"
    elif BULLET_MARKER_RE.match(text) and is_short_candidate:
        list_type = "bullet"
    elif NUMBERED_MARKER_RE.match(text) and is_short_candidate:
        list_type = "numbered"
    elif LIST_STYLE_RE.search(style_name) and is_short_candidate and paragraph.paragraph_format.left_indent is not None:
        list_type = "list"

    if list_level is None and list_type is not None:
        leading_tabs = len(text) - len(text.lstrip("\t"))
        leading_spaces = len(text) - len(text.lstrip(" "))
        if leading_tabs > 0:
            list_level = min(1, leading_tabs)
        elif leading_spaces >= 4:
            list_level = min(1, leading_spaces // 4)
        elif re.match(r"^\s*\d+\.\d+", text):
            list_level = 1
        else:
            list_level = 0

    return list_type, list_level


def extract_paragraph_block(
    paragraph: Paragraph,
    doc_id: str,
    block_id: int,
    file_name: str,
) -> dict[str, Any]:
    text = "" if paragraph.text is None else str(paragraph.text)
    list_type, list_level = extract_list_metadata(paragraph)

    return {
        "doc_id": doc_id,
        "block_id": block_id,
        "text": text,
        "kind": "paragraph",
        "alignment": normalize_alignment(paragraph),
        "style": get_style_name(paragraph),
        "bold_ratio": round(compute_bold_ratio_from_runs(paragraph), 4),
        "list_type": list_type,
        "list_level": list_level,
        "file_name": file_name,
    }


def extract_table_text(table: Table) -> str:
    """
    Превращает таблицу в текстовое представление.
    Строки разделяем переносом, ячейки — символом ' | '.
    """
    rows = []

    for row in table.rows:
        cells = []
        for cell in row.cells:
            cell_text = "\n".join(
                p.text.strip() for p in cell.paragraphs if p.text and p.text.strip()
            ).strip()
            cells.append(cell_text)
        row_text = " | ".join(cells).strip()
        if row_text:
            rows.append(row_text)

    return "\n".join(rows).strip()


def extract_table_block(
    table: Table,
    doc_id: str,
    block_id: int,
    file_name: str,
) -> dict[str, Any]:
    text = extract_table_text(table)

    return {
        "doc_id": doc_id,
        "block_id": block_id,
        "text": text,
        "kind": "table",
        "alignment": None,
        "style": "Table",
        "bold_ratio": 0.0,
        "file_name": file_name,
    }


def extract_blocks_from_docx(
    input_docx: str | Path,
    doc_id: str | None = None,
    keep_empty: bool = False,
) -> pd.DataFrame:
    input_docx = Path(input_docx)
    document = Document(str(input_docx))

    if doc_id is None:
        doc_id = input_docx.stem

    file_name = input_docx.name
    records: list[dict[str, Any]] = []
    block_id = 1

    for block in iter_block_items(document):
        if isinstance(block, Paragraph):
            record = extract_paragraph_block(
                paragraph=block,
                doc_id=doc_id,
                block_id=block_id,
                file_name=file_name,
            )
        elif isinstance(block, Table):
            record = extract_table_block(
                table=block,
                doc_id=doc_id,
                block_id=block_id,
                file_name=file_name,
            )
        else:
            continue

        if keep_empty or record["text"]:
            records.append(record)
            block_id += 1

    df = pd.DataFrame(records)

    if df.empty:
        df = pd.DataFrame(
            columns=[
                "doc_id",
                "block_id",
                "text",
                "kind",
                "alignment",
                "style",
                "bold_ratio",
                "list_type",
                "list_level",
                "file_name",
            ]
        )

    return df
