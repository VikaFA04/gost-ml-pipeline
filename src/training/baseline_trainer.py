"""End-to-end baseline training entrypoint."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

from src.data.loaders import load_csv_dataset
from src.data.validators import validate_prepared_dataset
from src.evaluation.confusion import build_confusion_matrix_frame
from src.evaluation.metrics import compute_per_class_metrics, compute_summary_metrics
from src.evaluation.report_writer import write_csv_report, write_json_report, write_text_report
from src.models.baseline_model import build_baseline_pipeline
from src.models.label_encoder import fit_label_encoder
from src.preprocessing.block_preprocessor import preprocess_blocks
from src.training.reproducibility import set_global_seed
from src.utils.exceptions import DataValidationError


@dataclass(slots=True)
class BaselineConfig:
    """Runtime configuration for the baseline trainer."""

    dataset_path: Path
    output_root: Path
    random_seed: int = 42


def _split_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the prepared dataset using the explicit split column."""
    train_df = df.loc[df["split"] == "train"].reset_index(drop=True)
    val_df = df.loc[df["split"] == "val"].reset_index(drop=True)

    if train_df.empty or val_df.empty:
        raise DataValidationError("Both 'train' and 'val' splits must be non-empty.")

    return train_df, val_df


def _build_prediction_frame(
    df: pd.DataFrame,
    y_true: list[str],
    y_pred: list[str],
    probabilities: list[float],
) -> pd.DataFrame:
    """Assemble row-level validation predictions."""
    return pd.DataFrame(
        {
            "doc_id": df["doc_id"],
            "block_id": df["block_id"],
            "text": df["text"],
            "true_label": y_true,
            "predicted_label": y_pred,
            "confidence": probabilities,
        }
    )


def _render_text_report(
    summary_metrics: dict[str, float],
    per_class_metrics: pd.DataFrame,
    train_size: int,
    val_size: int,
    labels: list[str],
) -> str:
    """Build a plain text baseline summary."""
    lines = [
        "Baseline Training Report",
        f"train_rows: {train_size}",
        f"val_rows: {val_size}",
        f"labels: {', '.join(labels)}",
        "",
        "Summary Metrics:",
    ]
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


def run_baseline_training(config: BaselineConfig) -> dict[str, Path]:
    """Train, evaluate, and persist the baseline model."""
    set_global_seed(config.random_seed)

    raw_df = load_csv_dataset(config.dataset_path)
    validate_prepared_dataset(raw_df, dataset_name=config.dataset_path.name)
    processed_df = preprocess_blocks(raw_df)

    train_df, val_df = _split_dataset(processed_df)

    label_encoder = fit_label_encoder(train_df["label_core"])
    y_train = label_encoder.transform(train_df["label_core"])
    y_val = label_encoder.transform(val_df["label_core"])

    model = build_baseline_pipeline(random_state=config.random_seed)
    model.fit(train_df[["text", "kind", "alignment", "style", "bold_ratio"]], y_train)

    val_pred_ids = model.predict(val_df[["text", "kind", "alignment", "style", "bold_ratio"]])
    predicted_probabilities = model.predict_proba(
        val_df[["text", "kind", "alignment", "style", "bold_ratio"]]
    ).max(axis=1)

    y_true = label_encoder.inverse_transform(y_val.tolist())
    y_pred = label_encoder.inverse_transform(val_pred_ids.tolist())

    summary_metrics = compute_summary_metrics(y_true=y_true, y_pred=y_pred)
    per_class_metrics = compute_per_class_metrics(y_true=y_true, y_pred=y_pred)
    confusion_df = build_confusion_matrix_frame(
        y_true=y_true,
        y_pred=y_pred,
        labels=sorted(label_encoder.label_to_id),
    )
    predictions_df = _build_prediction_frame(
        df=val_df,
        y_true=y_true,
        y_pred=y_pred,
        probabilities=predicted_probabilities.tolist(),
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_dir = config.output_root / "artifacts" / "baseline"
    metrics_dir = config.output_root / "results" / "metrics"

    model_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / f"baseline_model_{timestamp}.joblib"
    labels_path = config.output_root / "artifacts" / "label_mappings" / f"baseline_labels_{timestamp}.json"
    summary_path = metrics_dir / f"baseline_metrics_{timestamp}.json"
    per_class_path = metrics_dir / f"baseline_per_class_{timestamp}.csv"
    confusion_path = metrics_dir / f"baseline_confusion_{timestamp}.csv"
    predictions_path = metrics_dir / f"baseline_val_predictions_{timestamp}.csv"
    report_path = metrics_dir / f"baseline_report_{timestamp}.txt"
    config_path = metrics_dir / f"baseline_config_{timestamp}.json"

    joblib.dump(model, model_path)
    label_encoder.save(labels_path)

    write_json_report(summary_metrics, summary_path)
    write_csv_report(per_class_metrics, per_class_path)
    write_csv_report(confusion_df, confusion_path)
    write_csv_report(predictions_df, predictions_path)
    write_text_report(
        _render_text_report(
            summary_metrics=summary_metrics,
            per_class_metrics=per_class_metrics,
            train_size=len(train_df),
            val_size=len(val_df),
            labels=sorted(label_encoder.label_to_id),
        ),
        report_path,
    )
    write_json_report(
        {
            "dataset_path": str(config.dataset_path),
            "output_root": str(config.output_root),
            "random_seed": config.random_seed,
        },
        config_path,
    )

    return {
        "model_path": model_path,
        "labels_path": labels_path,
        "summary_metrics_path": summary_path,
        "per_class_metrics_path": per_class_path,
        "confusion_matrix_path": confusion_path,
        "predictions_path": predictions_path,
        "report_path": report_path,
        "config_path": config_path,
    }


def parse_args() -> BaselineConfig:
    """Parse CLI arguments into a trainer config."""
    parser = argparse.ArgumentParser(description="Train the fresh TF-IDF baseline model.")
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
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    args = parser.parse_args()
    return BaselineConfig(
        dataset_path=args.dataset_path,
        output_root=args.output_root,
        random_seed=args.random_seed,
    )


def main() -> None:
    """CLI entrypoint."""
    config = parse_args()
    output_paths = run_baseline_training(config)
    serializable_paths = {key: str(value) for key, value in output_paths.items()}
    print(json.dumps(serializable_paths, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
