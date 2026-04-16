"""Reproducibility helpers."""

from __future__ import annotations

import os
import random

import numpy as np

try:
    import torch
except ImportError:  # pragma: no cover - torch is optional for the baseline-only phase
    torch = None


def set_global_seed(seed: int) -> None:
    """Set deterministic seeds for supported baseline dependencies."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    if torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
