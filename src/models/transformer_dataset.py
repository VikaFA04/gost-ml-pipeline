"""Dataset definitions for transformer fine-tuning."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import torch
from torch.utils.data import Dataset
from transformers import PreTrainedTokenizerBase


@dataclass(slots=True)
class EncodedBatch:
    """Container for encoded batch tensors."""

    input_ids: torch.Tensor
    attention_mask: torch.Tensor
    labels: torch.Tensor


class BlockClassificationDataset(Dataset[dict[str, torch.Tensor]]):
    """PyTorch dataset for block-level transformer classification."""

    def __init__(
        self,
        df: pd.DataFrame,
        tokenizer: PreTrainedTokenizerBase,
        max_length: int,
        label_ids: pd.Series,
    ) -> None:
        self.df = df.reset_index(drop=True)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.label_ids = label_ids.reset_index(drop=True)

        if len(self.df) != len(self.label_ids):
            raise ValueError("Feature rows and label ids must have identical lengths.")

    def __len__(self) -> int:
        """Return the dataset size."""
        return len(self.df)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        """Return one encoded sample."""
        row = self.df.iloc[index]
        encoded = self.tokenizer(
            row["text"],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "labels": torch.tensor(int(self.label_ids.iloc[index]), dtype=torch.long),
        }
