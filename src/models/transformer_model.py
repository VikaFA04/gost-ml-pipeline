"""Transformer model loading helpers."""

from __future__ import annotations

from pathlib import Path

from transformers import AutoModelForSequenceClassification, AutoTokenizer, PreTrainedTokenizerBase


def load_tokenizer(model_name_or_path: str) -> PreTrainedTokenizerBase:
    """Load a Hugging Face tokenizer."""
    return AutoTokenizer.from_pretrained(model_name_or_path)


def load_sequence_classifier(model_name_or_path: str, num_labels: int):
    """Load a sequence classification transformer model."""
    return AutoModelForSequenceClassification.from_pretrained(
        model_name_or_path,
        num_labels=num_labels,
    )


def save_tokenizer(tokenizer: PreTrainedTokenizerBase, output_dir: Path) -> None:
    """Persist tokenizer artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tokenizer.save_pretrained(output_dir)


def save_model(model, output_dir: Path) -> None:
    """Persist model artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
