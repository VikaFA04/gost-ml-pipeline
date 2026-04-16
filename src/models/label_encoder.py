"""Stable label encoding for block roles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.utils.exceptions import LabelMappingError


@dataclass(slots=True)
class LabelEncoderArtifact:
    """Serializable label encoder artifact."""

    label_to_id: dict[str, int]

    @property
    def id_to_label(self) -> dict[int, str]:
        """Return the inverse mapping."""
        return {idx: label for label, idx in self.label_to_id.items()}

    def transform(self, labels: pd.Series) -> pd.Series:
        """Map labels to ids and fail explicitly on unknown values."""
        unknown = sorted(set(labels.astype(str)) - set(self.label_to_id))
        if unknown:
            raise LabelMappingError(f"Unknown labels encountered: {unknown}")
        return labels.astype(str).map(self.label_to_id)

    def inverse_transform(self, label_ids: list[int]) -> list[str]:
        """Map ids back to labels."""
        mapping = self.id_to_label
        unknown = sorted(set(label_ids) - set(mapping))
        if unknown:
            raise LabelMappingError(f"Unknown label ids encountered: {unknown}")
        return [mapping[label_id] for label_id in label_ids]

    def save(self, output_path: Path) -> None:
        """Save the mapping as JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(self.label_to_id, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def fit_label_encoder(labels: pd.Series) -> LabelEncoderArtifact:
    """Create a deterministic label-to-id mapping."""
    unique_labels = sorted(labels.astype(str).unique())
    if not unique_labels:
        raise LabelMappingError("Cannot fit a label encoder on an empty label set.")
    return LabelEncoderArtifact(label_to_id={label: idx for idx, label in enumerate(unique_labels)})
