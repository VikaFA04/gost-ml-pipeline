"""Dataset schema contracts for the new pipeline."""

from __future__ import annotations

from typing import Final

TARGET_COLUMN: Final[str] = "label_core"
TEXT_COLUMN: Final[str] = "text"
SPLIT_COLUMN: Final[str] = "split"

IDENTIFIER_COLUMNS: Final[list[str]] = ["doc_id", "block_id", "file_name"]
STRUCTURAL_COLUMNS: Final[list[str]] = ["kind", "alignment", "style", "bold_ratio"]
OPTIONAL_METADATA_COLUMNS: Final[list[str]] = [
    "label_detailed",
    "label_baseline",
    "confidence",
    "notes",
]

REQUIRED_DATASET_COLUMNS: Final[list[str]] = [
    "doc_id",
    "block_id",
    "text",
    "label_core",
    "kind",
    "alignment",
    "style",
    "bold_ratio",
    "file_name",
    "split",
]

ALLOWED_SPLITS: Final[set[str]] = {"train", "val", "test"}
