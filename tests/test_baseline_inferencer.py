from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.inference import baseline_inferencer


def test_baseline_inference_applies_conservative_postprocess(monkeypatch) -> None:
    calls: list[dict[str, object]] = []
    blocks_df = pd.DataFrame({"text": ["1. Heading"]})
    expected_df = pd.DataFrame({"postprocessed_label": ["body_text"]})

    def fake_predict_blocks(model_path: Path, blocks_df: pd.DataFrame, apply_rules: bool = False) -> pd.DataFrame:
        calls.append(
            {
                "model_path": model_path,
                "blocks_df": blocks_df,
                "apply_rules": apply_rules,
            }
        )
        return expected_df

    monkeypatch.setattr(baseline_inferencer, "predict_blocks", fake_predict_blocks)

    result = baseline_inferencer.run_baseline_inference(Path("model.joblib"), blocks_df)

    assert result is expected_df
    assert calls == [
        {
            "model_path": Path("model.joblib"),
            "blocks_df": blocks_df,
                "apply_rules": True,
            }
        ]
