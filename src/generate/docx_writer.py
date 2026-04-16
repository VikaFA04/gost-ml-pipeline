from __future__ import annotations
from pathlib import Path
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from src.generate.docx_styles import (
    apply_run_font,
    setup_document_page,
    style_bibliography_item,
    style_body_paragraph,
    style_caption,
    style_list_item,
    style_section_title,
    style_subsection_title,
)

LABEL_COL_CANDIDATES = ["postprocessed_label", "predicted_label"]

def resolve_label_column(df: pd.DataFrame) -> str:
    for col in LABEL_COL_CANDIDATES:
        if col in df.columns:
            return col
    raise ValueError("В DataFrame нет ни 'postprocessed_label', ни 'predicted_label'")


def add_styled_paragraph(document: Document, text: str, label: str):
    paragraph = document.add_paragraph()
    run = paragraph.add_run(text)

    if label in {"title_section", "bibliography_title", "appendix_title"}:
        apply_run_font(run, font_size=14, bold=True)
        style_section_title(paragraph)

    elif label in {"title_subsection"}:
        apply_run_font(run, font_size=14, bold=True)
        style_subsection_title(paragraph)

    elif label in {"figure_caption", "table_caption"}:
        apply_run_font(run, font_size=12, bold=False)
        style_caption(paragraph)

    elif label in {"bibliography_item"}:
        apply_run_font(run, font_size=14, bold=False)
        style_bibliography_item(paragraph)

    elif label in {"list_item"}:
        apply_run_font(run, font_size=14, bold=False)
        style_list_item(paragraph)

    else:
        apply_run_font(run, font_size=14, bold=False)
        style_body_paragraph(paragraph)

    return paragraph

def parse_table_text(table_text: str) -> list[list[str]]:
    """
    Восстанавливает таблицу из текстового представления:
    строки разделены '\\n', ячейки — ' | '.
    """
    rows = []
    for line in str(table_text).splitlines():
        line = line.strip()
        if not line:
            continue
        cells = [cell.strip() for cell in line.split(" | ")]
        rows.append(cells)
    return rows


def add_table_from_text(document: Document, table_text: str) -> None:
    rows = parse_table_text(table_text)
    if not rows:
        return

    max_cols = max(len(row) for row in rows)
    table = document.add_table(rows=len(rows), cols=max_cols)
    table.style = "Table Grid"

    for i, row in enumerate(rows):
        for j in range(max_cols):
            value = row[j] if j < len(row) else ""
            cell_par = table.cell(i, j).paragraphs[0]
            run = cell_par.add_run(value)
            apply_run_font(run, font_size=12, bold=False)
            cell_par.alignment = WD_ALIGN_PARAGRAPH.LEFT


def generate_docx_from_predictions(
    predictions_csv: str | Path,
    output_docx: str | Path,
) -> None:
    predictions_csv = Path(predictions_csv)
    output_docx = Path(output_docx)

    df = pd.read_csv(predictions_csv)
    if "block_id" in df.columns:
        df = df.sort_values("block_id").reset_index(drop=True)

    label_col = resolve_label_column(df)

    document = Document()
    setup_document_page(document)

    for _, row in df.iterrows():
        text = str(row.get("text", "")).strip()
        kind = str(row.get("kind", "paragraph"))
        label = str(row.get(label_col, "body_text"))

        if not text:
            continue

        if kind == "table":
            add_table_from_text(document, text)
            continue

        add_styled_paragraph(document, text, label)

    output_docx.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(output_docx))