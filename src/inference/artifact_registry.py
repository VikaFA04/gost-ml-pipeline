"""Saved artifact discovery for application-time inference."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"


@dataclass(slots=True)
class BaselineArtifactBundle:
    """Saved baseline inference artifacts."""

    model_path: Path
    source: str


@dataclass(slots=True)
class TransformerArtifactBundle:
    """Saved transformer inference artifacts."""

    checkpoint_dir: Path
    tokenizer_dir: Path
    label_mapping_path: Path
    source: str


def find_latest_baseline_artifacts() -> BaselineArtifactBundle | None:
    """Return the latest baseline artifact bundle if one exists."""
    candidates = sorted((ARTIFACTS_DIR / "baseline").glob("*.joblib"))
    if candidates:
        model_path = candidates[-1]
        return BaselineArtifactBundle(model_path=model_path, source="artifacts/baseline")

    legacy_candidates = sorted((PROJECT_ROOT / "results" / "models").glob("*.joblib"))
    if legacy_candidates:
        model_path = legacy_candidates[-1]
        return BaselineArtifactBundle(model_path=model_path, source="results/models")

    return None


def find_latest_transformer_artifacts() -> TransformerArtifactBundle | None:
    """Return the latest transformer artifact bundle if one exists."""
    run_dirs = sorted((ARTIFACTS_DIR / "transformer").glob("transformer_run_*"))
    for run_dir in reversed(run_dirs):
        timestamp = run_dir.name.removeprefix("transformer_run_")
        checkpoint_dir = run_dir / "best_checkpoint"
        tokenizer_dir = run_dir / "tokenizer"
        label_mapping_path = ARTIFACTS_DIR / "label_mappings" / f"transformer_labels_{timestamp}.json"
        if checkpoint_dir.exists() and tokenizer_dir.exists() and label_mapping_path.exists():
            return TransformerArtifactBundle(
                checkpoint_dir=checkpoint_dir,
                tokenizer_dir=tokenizer_dir,
                label_mapping_path=label_mapping_path,
                source=str(run_dir),
            )
    return None
