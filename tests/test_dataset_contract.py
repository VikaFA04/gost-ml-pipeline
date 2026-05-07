from __future__ import annotations

import pytest

from src import config
from src.train import load_dataset


def test_training_config_uses_dataset_folder() -> None:
    assert config.TRAIN_CSV == config.PROJECT_ROOT / "dataset" / "annotations_train.csv"
    assert config.VAL_CSV == config.PROJECT_ROOT / "dataset" / "annotations_val.csv"
    assert config.TEST_CSV == config.PROJECT_ROOT / "dataset" / "annotations_test.csv"
    assert config.DOCUMENT_SPLITS_CSV == config.PROJECT_ROOT / "dataset" / "document_splits.csv"


def test_training_target_is_dataset_label_core() -> None:
    assert config.TARGET_COL == "label_core"


def test_load_dataset_accepts_dataset_train_csv() -> None:
    if not config.TRAIN_CSV.exists():
        pytest.skip(f"Local dataset fixture is not available: {config.TRAIN_CSV}")

    df = load_dataset(config.TRAIN_CSV)

    assert not df.empty
    assert config.TARGET_COL in df.columns
    assert set(config.FEATURE_COLUMNS).issubset(df.columns)
