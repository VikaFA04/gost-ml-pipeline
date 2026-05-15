"""Document input validation and loading for the application layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SUPPORTED_EXTENSIONS = {".docx", ".pdf"}


@dataclass(slots=True)
class DocumentInput:
    """Validated document input metadata."""

    path: Path
    extension: str


def validate_document_input(path: str | Path) -> DocumentInput:
    """Validate supported input formats for the MVP."""
    document_path = Path(path)
    if not document_path.exists():
        raise FileNotFoundError(f"Input document was not found: {document_path}")

    extension = document_path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported input format '{extension}'. Supported formats: .docx, .pdf")

    return DocumentInput(path=document_path, extension=extension)
