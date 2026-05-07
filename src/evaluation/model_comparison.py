"""Comparison utilities for saved baseline and transformer metrics."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd


SUMMARY_KEYS = ["accuracy", "weighted_precision", "weighted_recall", "weighted_f1"]


@dataclass(slots=True)
class ComparisonConfig:
    """Runtime configuration for saved-metrics comparison."""

    baseline_metrics_path: Path
    transformer_metrics_path: Path
    output_dir: Path


def load_summary_metrics(metrics_path: Path) -> dict[str, float]:
    """Load and validate one summary metrics JSON file."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file was not found: {metrics_path}")

    payload = json.loads(metrics_path.read_text(encoding="utf-8"))

    # Legacy baseline training reports store the requested summary values
    # inside the nested "test" section rather than at top level.
    if "test" in payload and isinstance(payload["test"], dict):
        test_payload = payload["test"]
        weighted_avg = test_payload.get("weighted avg", {})
        if "accuracy" in test_payload and all(
            key in weighted_avg for key in ("precision", "recall", "f1-score")
        ):
            return {
                "accuracy": float(test_payload["accuracy"]),
                "weighted_precision": float(weighted_avg["precision"]),
                "weighted_recall": float(weighted_avg["recall"]),
                "weighted_f1": float(weighted_avg["f1-score"]),
            }

    missing = [key for key in SUMMARY_KEYS if key not in payload]
    if missing:
        raise ValueError(f"Metrics file '{metrics_path}' is missing required keys: {missing}")

    return {key: float(payload[key]) for key in SUMMARY_KEYS}


def build_comparison_frame(
    baseline_metrics: dict[str, float],
    transformer_metrics: dict[str, float],
) -> pd.DataFrame:
    """Build a unified comparison dataframe."""
    rows: list[dict[str, object]] = []
    for metric_name in SUMMARY_KEYS:
        baseline_value = baseline_metrics[metric_name]
        transformer_value = transformer_metrics[metric_name]
        delta = transformer_value - baseline_value
        winner = "transformer" if delta > 0 else "baseline" if delta < 0 else "tie"
        rows.append(
            {
                "metric": metric_name,
                "baseline": baseline_value,
                "transformer": transformer_value,
                "delta_transformer_minus_baseline": delta,
                "winner": winner,
            }
        )
    return pd.DataFrame(rows)


def render_report(
    comparison_df: pd.DataFrame,
    baseline_metrics_path: Path,
    transformer_metrics_path: Path,
) -> str:
    """Render a concise human-readable comparison report."""
    lines = [
        "Baseline vs Transformer Comparison Report",
        f"baseline_metrics: {baseline_metrics_path}",
        f"transformer_metrics: {transformer_metrics_path}",
        "",
    ]
    for _, row in comparison_df.iterrows():
        lines.append(
            (
                f"- {row['metric']}: baseline={row['baseline']:.6f}, "
                f"transformer={row['transformer']:.6f}, "
                f"delta={row['delta_transformer_minus_baseline']:.6f}, "
                f"winner={row['winner']}"
            )
        )
    return "\n".join(lines)


def write_success_outputs(
    comparison_df: pd.DataFrame,
    config: ComparisonConfig,
    timestamp: str,
) -> dict[str, Path]:
    """Persist successful comparison outputs."""
    config.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = config.output_dir / f"baseline_vs_transformer_comparison_{timestamp}.json"
    csv_path = config.output_dir / f"baseline_vs_transformer_comparison_{timestamp}.csv"
    report_path = config.output_dir / f"baseline_vs_transformer_report_{timestamp}.txt"

    comparison_payload = {
        "baseline_metrics_path": str(config.baseline_metrics_path),
        "transformer_metrics_path": str(config.transformer_metrics_path),
        "rows": comparison_df.to_dict(orient="records"),
    }

    json_path.write_text(json.dumps(comparison_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    comparison_df.to_csv(csv_path, index=False, encoding="utf-8")
    report_path.write_text(
        render_report(
            comparison_df=comparison_df,
            baseline_metrics_path=config.baseline_metrics_path,
            transformer_metrics_path=config.transformer_metrics_path,
        ),
        encoding="utf-8",
    )

    return {
        "comparison_json": json_path,
        "comparison_csv": csv_path,
        "comparison_report": report_path,
    }


def write_blocked_outputs(
    config: ComparisonConfig,
    timestamp: str,
    error_message: str,
) -> dict[str, Path]:
    """Persist explicit blocker outputs when comparison cannot be computed."""
    config.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = config.output_dir / f"baseline_vs_transformer_comparison_blocked_{timestamp}.json"
    csv_path = config.output_dir / f"baseline_vs_transformer_comparison_blocked_{timestamp}.csv"
    report_path = config.output_dir / f"baseline_vs_transformer_report_blocked_{timestamp}.txt"

    status_rows = pd.DataFrame(
        [
            {
                "model": "baseline",
                "metrics_path": str(config.baseline_metrics_path),
                "exists": config.baseline_metrics_path.exists(),
            },
            {
                "model": "transformer",
                "metrics_path": str(config.transformer_metrics_path),
                "exists": config.transformer_metrics_path.exists(),
            },
        ]
    )

    payload = {
        "status": "blocked",
        "error": error_message,
        "baseline_metrics_path": str(config.baseline_metrics_path),
        "transformer_metrics_path": str(config.transformer_metrics_path),
        "baseline_exists": config.baseline_metrics_path.exists(),
        "transformer_exists": config.transformer_metrics_path.exists(),
    }

    report = "\n".join(
        [
            "Baseline vs Transformer Comparison Report",
            "status: blocked",
            f"error: {error_message}",
            f"baseline_metrics: {config.baseline_metrics_path}",
            f"transformer_metrics: {config.transformer_metrics_path}",
        ]
    )

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    status_rows.to_csv(csv_path, index=False, encoding="utf-8")
    report_path.write_text(report, encoding="utf-8")

    return {
        "comparison_json": json_path,
        "comparison_csv": csv_path,
        "comparison_report": report_path,
    }


def infer_latest_metrics_path(metrics_dir: Path, prefix: str) -> Path:
    """Infer the latest metrics file matching a prefix."""
    candidates = sorted(metrics_dir.glob(f"{prefix}_metrics_*.json"))
    if not candidates:
        return metrics_dir / f"{prefix}_metrics_MISSING.json"
    return candidates[-1]


def run_comparison(config: ComparisonConfig) -> dict[str, Path]:
    """Compute the comparison outputs or explicit blocker artifacts."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        baseline_metrics = load_summary_metrics(config.baseline_metrics_path)
        transformer_metrics = load_summary_metrics(config.transformer_metrics_path)
        comparison_df = build_comparison_frame(
            baseline_metrics=baseline_metrics,
            transformer_metrics=transformer_metrics,
        )
        return write_success_outputs(comparison_df=comparison_df, config=config, timestamp=timestamp)
    except (FileNotFoundError, ValueError) as exc:
        return write_blocked_outputs(config=config, timestamp=timestamp, error_message=str(exc))


def parse_args() -> ComparisonConfig:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Compare saved baseline and transformer metrics.")
    parser.add_argument(
        "--baseline-metrics-path",
        type=Path,
        default=None,
        help="Path to the saved baseline summary metrics JSON.",
    )
    parser.add_argument(
        "--transformer-metrics-path",
        type=Path,
        default=None,
        help="Path to the saved transformer summary metrics JSON.",
    )
    parser.add_argument(
        "--metrics-dir",
        type=Path,
        default=Path("results/metrics"),
        help="Directory used to infer latest metrics when explicit paths are omitted.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/comparisons"),
        help="Output directory for comparison artifacts.",
    )
    args = parser.parse_args()

    baseline_path = args.baseline_metrics_path or infer_latest_metrics_path(args.metrics_dir, "baseline")
    transformer_path = args.transformer_metrics_path or infer_latest_metrics_path(args.metrics_dir, "transformer")

    return ComparisonConfig(
        baseline_metrics_path=baseline_path,
        transformer_metrics_path=transformer_path,
        output_dir=args.output_dir,
    )


def main() -> None:
    """CLI entrypoint."""
    config = parse_args()
    outputs = run_comparison(config)
    serializable_paths = {key: str(value) for key, value in outputs.items()}
    print(json.dumps(serializable_paths, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
