"""Transformer inference using saved Hugging Face artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import torch

from src.postprocess.postprocess_rules import apply_postprocess_rules
from src.preprocessing.cleaners import clean_text
from src.preprocessing.normalizers import normalize_categorical, normalize_numeric
from transformers import AutoModelForSequenceClassification, AutoTokenizer


@dataclass(slots=True)
class TransformerInferenceArtifacts:
    """Loaded transformer inference dependencies."""

    tokenizer: object
    model: object
    id_to_label: dict[int, str]
    device: torch.device


def preprocess_inference_blocks(blocks_df: pd.DataFrame) -> pd.DataFrame:
    """Apply inference-time preprocessing without requiring training labels."""
    required_columns = {"doc_id", "block_id", "text", "kind", "alignment", "style", "bold_ratio", "file_name"}
    missing = required_columns - set(blocks_df.columns)
    if missing:
        raise ValueError(f"Inference dataframe is missing required columns: {sorted(missing)}")

    result = blocks_df.copy()
    result["model_text"] = result["text"].map(clean_text)
    result["kind"] = result["kind"].map(normalize_categorical)
    result["alignment"] = result["alignment"].map(normalize_categorical)
    result["style"] = result["style"].map(normalize_categorical)
    result["bold_ratio"] = result["bold_ratio"].map(normalize_numeric)
    result = result.loc[result["model_text"].str.len() > 0].reset_index(drop=True)

    if result.empty:
        raise ValueError("No non-empty blocks remain after inference preprocessing.")

    return result


def load_transformer_artifacts(
    checkpoint_dir: Path,
    tokenizer_dir: Path,
    label_mapping_path: Path,
) -> TransformerInferenceArtifacts:
    """Load saved transformer artifacts for deterministic inference."""
    label_mapping = json.loads(label_mapping_path.read_text(encoding="utf-8"))
    id_to_label = {int(idx): label for label, idx in label_mapping.items()}

    tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint_dir))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    return TransformerInferenceArtifacts(
        tokenizer=tokenizer,
        model=model,
        id_to_label=id_to_label,
        device=device,
    )


def run_transformer_inference(
    blocks_df: pd.DataFrame,
    artifacts: TransformerInferenceArtifacts,
    max_length: int = 256,
    low_confidence_threshold: float = 0.8,
) -> pd.DataFrame:
    """Run transformer block classification and postprocessing."""
    preprocessed_df = preprocess_inference_blocks(blocks_df)
    predicted_labels: list[str] = []
    confidence_scores: list[float] = []

    with torch.no_grad():
        for text in preprocessed_df["model_text"].tolist():
            encoded = artifacts.tokenizer(
                text,
                truncation=True,
                padding="max_length",
                max_length=max_length,
                return_tensors="pt",
            )
            encoded = {key: value.to(artifacts.device) for key, value in encoded.items()}
            logits = artifacts.model(**encoded).logits
            probabilities = torch.softmax(logits, dim=-1).squeeze(0)
            predicted_id = int(torch.argmax(probabilities).item())
            predicted_labels.append(artifacts.id_to_label[predicted_id])
            confidence_scores.append(float(torch.max(probabilities).item()))

    result = preprocessed_df.copy()
    result["predicted_label"] = predicted_labels
    result["confidence_score"] = confidence_scores
    result["low_confidence"] = result["confidence_score"] < low_confidence_threshold
    result = result.drop(columns=["model_text"])
    result = apply_postprocess_rules(result, pred_col="predicted_label", out_col="postprocessed_label")
    return result
