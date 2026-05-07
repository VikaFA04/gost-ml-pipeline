from __future__ import annotations

from src.inference import application_service


def test_model_options_prefer_baseline_when_available(monkeypatch) -> None:
    monkeypatch.setattr(application_service, "find_latest_baseline_artifacts", lambda: object())

    options = application_service.list_model_options()

    assert list(options.keys())[:2] == ["baseline", "transformer"]
    assert options["baseline"] == "Baseline"


def test_profile_options_include_generated_profiles_dir(monkeypatch) -> None:
    captured = {}

    def fake_list_available_profiles(profiles_dir=None):
        captured["profiles_dir"] = profiles_dir
        return [{"profile_id": "gost_7_32_2017", "profile_name": "ГОСТ 7.32-2017", "profile_type": "gost", "source_type": "standard", "path": "base.json"}]

    monkeypatch.setattr(application_service, "list_available_profiles", fake_list_available_profiles)

    options = application_service.get_profile_options()

    assert captured["profiles_dir"] == [
        application_service.PROFILES_DIR,
        application_service.GENERATED_PROFILES_DIR,
    ]
    assert options[0]["profile_id"] == "gost_7_32_2017"
