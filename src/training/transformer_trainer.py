"""End-to-end transformer fine-tuning entrypoint."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import shutil

import pandas as pd
import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader
from transformers import get_linear_schedule_with_warmup

from src.data.loaders import load_csv_dataset
from src.data.validators import validate_prepared_dataset
from src.evaluation.confusion import build_confusion_matrix_frame
from src.evaluation.metrics import compute_per_class_metrics, compute_summary_metrics
from src.evaluation.report_writer import write_csv_report, write_json_report, write_text_report
from src.models.label_encoder import fit_label_encoder
from src.models.transformer_dataset import BlockClassificationDataset
from src.models.transformer_model import (
    load_sequence_classifier,
    load_tokenizer,
    save_model,
    save_tokenizer,
)
from src.preprocessing.block_preprocessor import preprocess_blocks
from src.training.reproducibility import set_global_seed
from src.utils.exceptions import DataValidationError


FEATURE_COLUMNS = ["text", "kind", "alignment", "style", "bold_ratio"]


@dataclass(slots=True)
class TransformerConfig:
    """Runtime configuration for transformer fine-tuning."""

    dataset_path: Path
    output_root: Path
    model_name: str = "cointegrated/rubert-tiny2"
    random_seed: int = 42
    max_length: int = 256
    batch_size: int = 16
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    max_epochs: int = 8
    min_epochs: int = 2
    early_stopping_patience: int = 2
    warmup_ratio: float = 0.1
    selection_metric: str = "weighted_f1"


def _split_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the prepared dataset using the declared split column."""
    train_df = df.loc[df["split"] == "train"].reset_index(drop=True)
    val_df = df.loc[df["split"] == "val"].reset_index(drop=True)

    if train_df.empty or val_df.empty:
        raise DataValidationError("Both 'train' and 'val' splits must be non-empty.")

    return train_df, val_df


def _get_device() -> torch.device:
    """Select the runtime device."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _compute_class_weights(label_ids: pd.Series) -> torch.Tensor:
    """Compute inverse-frequency class weights for imbalanced labels."""
    counts = label_ids.value_counts().sort_index()
    total = float(counts.sum())
    weights = total / (len(counts) * counts.astype(float))
    return torch.tensor(weights.to_numpy(), dtype=torch.float32)


def _build_dataloader(
    df: pd.DataFrame,
    label_ids: pd.Series,
    tokenizer,
    max_length: int,
    batch_size: int,
    shuffle: bool,
) -> DataLoader:
    """Create a dataloader for one split."""
    dataset = BlockClassificationDataset(
        df=df[FEATURE_COLUMNS],
        tokenizer=tokenizer,
        max_length=max_length,
        label_ids=label_ids,
    )
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        pin_memory=torch.cuda.is_available(),
    )


def _run_training_epoch(
    model,
    dataloader: DataLoader,
    optimizer: AdamW,
    scheduler,
    device: torch.device,
    class_weights: torch.Tensor,
) -> float:
    """Run one training epoch and return average loss."""
    model.train()
    loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights.to(device))
    total_loss = 0.0

    for batch in dataloader:
        optimizer.zero_grad(set_to_none=True)
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        loss = loss_fn(outputs.logits, labels)
        loss.backward()
        optimizer.step()
        scheduler.step()
        total_loss += float(loss.item())

    return total_loss / max(len(dataloader), 1)


def _run_evaluation(model, dataloader: DataLoader, device: torch.device) -> tuple[list[int], list[int], list[float], float]:
    """Evaluate the model and return predictions, labels, confidences, and mean loss."""
    model.eval()
    loss_fn = torch.nn.CrossEntropyLoss()
    total_loss = 0.0
    all_predictions: list[int] = []
    all_labels: list[int] = []
    all_confidences: list[float] = []

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            total_loss += float(loss_fn(logits, labels).item())

            probabilities = torch.softmax(logits, dim=-1)
            predictions = torch.argmax(probabilities, dim=-1)

            all_predictions.extend(predictions.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())
            all_confidences.extend(probabilities.max(dim=-1).values.cpu().tolist())

    mean_loss = total_loss / max(len(dataloader), 1)
    return all_predictions, all_labels, all_confidences, mean_loss


def _prediction_frame(
    val_df: pd.DataFrame,
    true_labels: list[str],
    predicted_labels: list[str],
    confidences: list[float],
) -> pd.DataFrame:
    """Build row-level validation predictions."""
    return pd.DataFrame(
        {
            "doc_id": val_df["doc_id"],
            "block_id": val_df["block_id"],
            "text": val_df["text"],
            "true_label": true_labels,
            "predicted_label": predicted_labels,
            "confidence": confidences,
        }
    )


def _epoch_metric_row(
    epoch_index: int,
    train_loss: float,
    val_loss: float,
    summary_metrics: dict[str, float],
    is_best: bool,
) -> dict[str, float | int | bool]:
    """Build one per-epoch metrics row."""
    return {
        "epoch": epoch_index,
        "train_loss": train_loss,
        "val_loss": val_loss,
        "accuracy": summary_metrics["accuracy"],
        "weighted_precision": summary_metrics["weighted_precision"],
        "weighted_recall": summary_metrics["weighted_recall"],
        "weighted_f1": summary_metrics["weighted_f1"],
        "is_best": is_best,
    }


def _render_text_report(
    config: TransformerConfig,
    summary_metrics: dict[str, float],
    per_class_metrics: pd.DataFrame,
    train_size: int,
    val_size: int,
    epoch_metrics: pd.DataFrame,
    device_name: str,
    best_epoch: int,
) -> str:
    """Render a human-readable training report."""
    lines = [
        "Transformer Training Report",
        f"model_name: {config.model_name}",
        f"device: {device_name}",
        f"train_rows: {train_size}",
        f"val_rows: {val_size}",
        f"max_epochs: {config.max_epochs}",
        f"min_epochs: {config.min_epochs}",
        f"early_stopping_patience: {config.early_stopping_patience}",
        f"batch_size: {config.batch_size}",
        f"learning_rate: {config.learning_rate}",
        f"best_epoch: {best_epoch}",
        "",
        "Epoch Metrics:",
    ]
    for _, row in epoch_metrics.iterrows():
        lines.append(
            (
                f"- epoch_{int(row['epoch'])}: train_loss={row['train_loss']:.6f}, "
                f"val_loss={row['val_loss']:.6f}, accuracy={row['accuracy']:.6f}, "
                f"weighted_f1={row['weighted_f1']:.6f}, is_best={bool(row['is_best'])}"
            )
        )

    lines.extend(["", "Summary Metrics:"])
    for key, value in summary_metrics.items():
        lines.append(f"- {key}: {value:.6f}")

    lines.extend(["", "Per-class Metrics:"])
    for _, row in per_class_metrics.iterrows():
        lines.append(
            (
                f"- {row['label']}: precision={row['precision']:.6f}, "
                f"recall={row['recall']:.6f}, f1={row['f1']:.6f}, support={int(row['support'])}"
            )
        )

    return "\n".join(lines)


def run_transformer_training(config: TransformerConfig) -> dict[str, Path]:
    """Train, evaluate, and persist the transformer classifier."""
    set_global_seed(config.random_seed)

    raw_df = load_csv_dataset(config.dataset_path)
    validate_prepared_dataset(raw_df, dataset_name=config.dataset_path.name)
    processed_df = preprocess_blocks(raw_df)
    train_df, val_df = _split_dataset(processed_df)

    label_encoder = fit_label_encoder(train_df["label_core"])
    train_label_ids = label_encoder.transform(train_df["label_core"])
    val_label_ids = label_encoder.transform(val_df["label_core"])

    tokenizer = load_tokenizer(config.model_name)
    model = load_sequence_classifier(config.model_name, num_labels=len(label_encoder.label_to_id))

    device = _get_device()
    model.to(device)
    device_name = str(device)

    train_loader = _build_dataloader(
        df=train_df,
        label_ids=train_label_ids,
        tokenizer=tokenizer,
        max_length=config.max_length,
        batch_size=config.batch_size,
        shuffle=True,
    )
    val_loader = _build_dataloader(
        df=val_df,
        label_ids=val_label_ids,
        tokenizer=tokenizer,
        max_length=config.max_length,
        batch_size=config.batch_size,
        shuffle=False,
    )

    optimizer = AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    total_training_steps = len(train_loader) * config.max_epochs
    warmup_steps = math.ceil(total_training_steps * config.warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(
        optimizer=optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_training_steps,
    )
    class_weights = _compute_class_weights(train_label_ids)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = config.output_root / "artifacts" / "transformer" / f"transformer_run_{timestamp}"
    best_checkpoint_dir = run_dir / "best_checkpoint"
    tokenizer_dir = run_dir / "tokenizer"
    metrics_dir = config.output_root / "results" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)

    save_tokenizer(tokenizer, tokenizer_dir)

    epoch_rows: list[dict[str, float | int | bool]] = []
    best_metric = float("-inf")
    best_epoch = 0
    epochs_without_improvement = 0
    best_summary_metrics: dict[str, float] | None = None
    best_per_class_metrics: pd.DataFrame | None = None
    best_confusion_df: pd.DataFrame | None = None
    best_predictions_df: pd.DataFrame | None = None

    for epoch_index in range(1, config.max_epochs + 1):
        train_loss = _run_training_epoch(
            model=model,
            dataloader=train_loader,
            optimizer=optimizer,
            scheduler=scheduler,
            device=device,
            class_weights=class_weights,
        )
        predicted_ids, true_ids, confidences, val_loss = _run_evaluation(
            model=model,
            dataloader=val_loader,
            device=device,
        )

        predicted_labels = label_encoder.inverse_transform(predicted_ids)
        true_labels = label_encoder.inverse_transform(true_ids)
        summary_metrics = compute_summary_metrics(y_true=true_labels, y_pred=predicted_labels)
        summary_metrics["validation_loss"] = float(val_loss)
        per_class_metrics = compute_per_class_metrics(y_true=true_labels, y_pred=predicted_labels)
        confusion_df = build_confusion_matrix_frame(
            y_true=true_labels,
            y_pred=predicted_labels,
            labels=sorted(label_encoder.label_to_id),
        )
        predictions_df = _prediction_frame(
            val_df=val_df,
            true_labels=true_labels,
            predicted_labels=predicted_labels,
            confidences=confidences,
        )

        current_metric = float(summary_metrics[config.selection_metric])
        is_best = current_metric > best_metric
        epoch_rows.append(
            _epoch_metric_row(
                epoch_index=epoch_index,
                train_loss=train_loss,
                val_loss=val_loss,
                summary_metrics=summary_metrics,
                is_best=is_best,
            )
        )

        if is_best:
            best_metric = current_metric
            best_epoch = epoch_index
            epochs_without_improvement = 0
            best_summary_metrics = {
                **summary_metrics,
                "best_epoch": float(best_epoch),
                "selection_metric_value": current_metric,
            }
            best_per_class_metrics = per_class_metrics.copy()
            best_confusion_df = confusion_df.copy()
            best_predictions_df = predictions_df.copy()
            if best_checkpoint_dir.exists():
                shutil.rmtree(best_checkpoint_dir)
            save_model(model, best_checkpoint_dir)
        else:
            epochs_without_improvement += 1

        if epoch_index >= config.min_epochs and epochs_without_improvement >= config.early_stopping_patience:
            break

    if best_summary_metrics is None or best_per_class_metrics is None or best_confusion_df is None or best_predictions_df is None:
        raise RuntimeError("Transformer training did not produce a best checkpoint.")

    labels_path = config.output_root / "artifacts" / "label_mappings" / f"transformer_labels_{timestamp}.json"
    label_encoder.save(labels_path)

    summary_path = metrics_dir / f"transformer_metrics_{timestamp}.json"
    per_class_path = metrics_dir / f"transformer_per_class_{timestamp}.csv"
    confusion_path = metrics_dir / f"transformer_confusion_{timestamp}.csv"
    predictions_path = metrics_dir / f"transformer_val_predictions_{timestamp}.csv"
    epoch_metrics_path = metrics_dir / f"transformer_epoch_metrics_{timestamp}.csv"
    report_path = metrics_dir / f"transformer_report_{timestamp}.txt"
    config_path = metrics_dir / f"transformer_config_{timestamp}.json"

    epoch_metrics_df = pd.DataFrame(epoch_rows)

    write_json_report(best_summary_metrics, summary_path)
    write_csv_report(best_per_class_metrics, per_class_path)
    write_csv_report(best_confusion_df, confusion_path)
    write_csv_report(best_predictions_df, predictions_path)
    write_csv_report(epoch_metrics_df, epoch_metrics_path)
    write_text_report(
        _render_text_report(
            config=config,
            summary_metrics=best_summary_metrics,
            per_class_metrics=best_per_class_metrics,
            train_size=len(train_df),
            val_size=len(val_df),
            epoch_metrics=epoch_metrics_df,
            device_name=device_name,
            best_epoch=best_epoch,
        ),
        report_path,
    )
    write_json_report(
        {
            "dataset_path": str(config.dataset_path),
            "output_root": str(config.output_root),
            "model_name": config.model_name,
            "random_seed": config.random_seed,
            "max_length": config.max_length,
            "batch_size": config.batch_size,
            "learning_rate": config.learning_rate,
            "weight_decay": config.weight_decay,
            "max_epochs": config.max_epochs,
            "min_epochs": config.min_epochs,
            "early_stopping_patience": config.early_stopping_patience,
            "warmup_ratio": config.warmup_ratio,
            "selection_metric": config.selection_metric,
            "device": device_name,
            "effective_epochs": int(len(epoch_metrics_df)),
            "best_epoch": int(best_epoch),
        },
        config_path,
    )

    return {
        "run_dir": run_dir,
        "best_checkpoint_dir": best_checkpoint_dir,
        "tokenizer_dir": tokenizer_dir,
        "labels_path": labels_path,
        "summary_metrics_path": summary_path,
        "per_class_metrics_path": per_class_path,
        "confusion_matrix_path": confusion_path,
        "predictions_path": predictions_path,
        "epoch_metrics_path": epoch_metrics_path,
        "report_path": report_path,
        "config_path": config_path,
    }


def parse_args() -> TransformerConfig:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Fine-tune the transformer classifier.")
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=Path("dataset/annotations_train_ready.csv"),
        help="Path to the prepared CSV dataset.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("."),
        help="Workspace root used for artifacts and results output.",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="cointegrated/rubert-tiny2",
        help="Hugging Face model name or local path for fine-tuning.",
    )
    parser.add_argument("--random-seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--max-length", type=int, default=256, help="Maximum token length.")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size.")
    parser.add_argument("--learning-rate", type=float, default=2e-5, help="Learning rate.")
    parser.add_argument("--weight-decay", type=float, default=0.01, help="Weight decay.")
    parser.add_argument(
        "--max-epochs",
        type=int,
        default=8,
        help="Upper bound on fine-tuning epochs; early stopping selects the effective epoch count.",
    )
    parser.add_argument(
        "--min-epochs",
        type=int,
        default=2,
        help="Minimum number of epochs to run before early stopping can trigger.",
    )
    parser.add_argument(
        "--early-stopping-patience",
        type=int,
        default=2,
        help="Number of non-improving validation epochs allowed before early stopping.",
    )
    parser.add_argument("--warmup-ratio", type=float, default=0.1, help="Warmup ratio.")
    parser.add_argument(
        "--selection-metric",
        type=str,
        default="weighted_f1",
        choices=["accuracy", "weighted_precision", "weighted_recall", "weighted_f1"],
        help="Validation metric used to select the best checkpoint.",
    )
    args = parser.parse_args()

    return TransformerConfig(
        dataset_path=args.dataset_path,
        output_root=args.output_root,
        model_name=args.model_name,
        random_seed=args.random_seed,
        max_length=args.max_length,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        max_epochs=args.max_epochs,
        min_epochs=args.min_epochs,
        early_stopping_patience=args.early_stopping_patience,
        warmup_ratio=args.warmup_ratio,
        selection_metric=args.selection_metric,
    )


def main() -> None:
    """CLI entrypoint."""
    config = parse_args()
    output_paths = run_transformer_training(config)
    serializable_paths = {key: str(value) for key, value in output_paths.items()}
    print(json.dumps(serializable_paths, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
