from __future__ import annotations

from typing import Iterator, Union

from docx.document import Document as DocumentType
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


BlockItem = Union[Paragraph, Table]


def iter_block_items(document: DocumentType) -> Iterator[BlockItem]:
    """
    Возвращает блоки документа в исходном порядке:
    Paragraph и Table.
    """
    parent_element = document.element.body

    for child in parent_element.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)