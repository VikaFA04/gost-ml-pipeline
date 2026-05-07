from __future__ import annotations

from docx.document import Document as DocumentType
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt


def setup_document_page(document: DocumentType) -> None:
    section = document.sections[0]

    # Формат A4
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)

    # Поля страницы
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(1.5)


def configure_document_styles(document: DocumentType) -> None:
    # Keep generated documents on the default Word style definitions unless
    # a block needs explicit direct formatting to match the positive corpus.
    _ = document


def apply_run_font(run, font_name: str = "Times New Roman", font_size: int = 14, bold: bool = False) -> None:
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.bold = bold


def style_body_paragraph(paragraph) -> None:
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Cm(1.25)
    fmt.line_spacing = 1.5
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(0)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def style_section_title(paragraph) -> None:
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Cm(0)
    fmt.left_indent = Cm(1.25)
    fmt.line_spacing = 1.5
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(10)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT


def style_subsection_title(paragraph) -> None:
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Cm(0)
    fmt.left_indent = Cm(1.25)
    fmt.line_spacing = 1.5
    fmt.space_before = Pt(15)
    fmt.space_after = Pt(10)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT


def style_figure_caption(paragraph) -> None:
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Cm(0)
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(6)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


def style_table_caption(paragraph) -> None:
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Cm(0)
    fmt.space_before = Pt(6)
    fmt.space_after = Pt(0)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT


def style_bibliography_item(paragraph) -> None:
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Cm(0)
    fmt.left_indent = Cm(0)
    fmt.line_spacing = 1.5
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(0)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def style_list_item(paragraph) -> None:
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Cm(0)
    fmt.left_indent = Cm(1.25)
    fmt.line_spacing = 1.5
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(0)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
