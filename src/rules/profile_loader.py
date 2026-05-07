from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

PROFILES_DIR = Path(__file__).resolve().parent / "profiles"


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result


def load_profile_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Профиль не найден: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_profile_path_by_id(
    profile_id: str,
    profiles_dir: str | Path | None = None,
) -> Path:
    base_dir = Path(profiles_dir) if profiles_dir else PROFILES_DIR
    path = base_dir / f"{profile_id}.json"

    if not path.exists():
        raise FileNotFoundError(f"Профиль с id='{profile_id}' не найден в {base_dir}")

    return path


def _resolve_base_profiles(
    profile: dict[str, Any],
    profiles_dir: str | Path | None = None,
    active_stack: tuple[str, ...] = (),
    cache: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Важно:
    - cycle detection должен работать только по текущему пути рекурсии
    - повторное использование одного и того же base_profile в другой ветке — это нормально
    """
    if cache is None:
        cache = {}

    current_profile_id = str(profile.get("profile_id", ""))

    if current_profile_id and current_profile_id in cache:
        return deepcopy(cache[current_profile_id])

    merged: dict[str, Any] = {}

    for base_profile_id in profile.get("base_profiles", []):
        if base_profile_id in active_stack:
            cycle_path = " -> ".join((*active_stack, base_profile_id))
            raise ValueError(f"Обнаружен циклический base_profiles: {cycle_path}")

        base_path = get_profile_path_by_id(
            base_profile_id,
            profiles_dir=profiles_dir,
        )
        base_profile = load_profile_file(base_path)

        resolved_base = _resolve_base_profiles(
            profile=base_profile,
            profiles_dir=profiles_dir,
            active_stack=(*active_stack, base_profile_id),
            cache=cache,
        )
        merged = deep_merge(merged, resolved_base)

    merged = deep_merge(merged, profile)

    if current_profile_id:
        cache[current_profile_id] = deepcopy(merged)

    return merged


def load_profile(
    profile_path: str | Path | None = None,
    profile_id: str | None = None,
    profiles_dir: str | Path | None = None,
) -> dict[str, Any]:
    if profile_path is None and profile_id is None:
        profile_id = "gost_7_32_2017"

    if profile_path is not None:
        profile = load_profile_file(profile_path)
    else:
        profile = load_profile_file(
            get_profile_path_by_id(profile_id, profiles_dir=profiles_dir)
        )

    resolved = _resolve_base_profiles(
        profile=profile,
        profiles_dir=profiles_dir,
        active_stack=(str(profile.get("profile_id", "")),),
        cache={},
    )

    from src.rules.profile_validator import assert_valid_profile

    assert_valid_profile(resolved)
    return resolved


def list_available_profiles(
    profiles_dir: str | Path | list[str | Path] | tuple[str | Path, ...] | None = None,
) -> list[dict[str, str]]:
    if profiles_dir is None:
        dirs = [PROFILES_DIR]
    elif isinstance(profiles_dir, (list, tuple)):
        dirs = [Path(item) for item in profiles_dir]
    else:
        dirs = [Path(profiles_dir)]

    items: list[dict[str, str]] = []

    seen_profile_ids: set[str] = set()

    for base_dir in dirs:
        if not base_dir.exists():
            continue

        for path in sorted(base_dir.glob("*.json")):
            try:
                raw = load_profile_file(path)
                profile_id = str(raw.get("profile_id", path.stem))
                if profile_id in seen_profile_ids:
                    continue
                items.append(
                    {
                        "profile_id": profile_id,
                        "profile_name": str(raw.get("profile_name", path.stem)),
                        "profile_type": str(raw.get("profile_type", "unknown")),
                        "source_type": str(raw.get("source_type", "unknown")),
                        "path": str(path),
                    }
                )
                seen_profile_ids.add(profile_id)
            except Exception:
                continue

    return items


def get_label_config(profile: dict[str, Any], label: str) -> dict[str, Any] | None:
    return profile.get("labels", {}).get(label)


def get_target_style_profile(
    profile: dict[str, Any],
    label: str,
) -> dict[str, Any] | None:
    cfg = get_label_config(profile, label)
    return None if not cfg else cfg.get("style_profile")


def get_audit_policy(profile: dict[str, Any], label: str) -> dict[str, Any]:
    cfg = get_label_config(profile, label) or {}
    return cfg.get("audit_policy", {})


def get_global_audit_policy(profile: dict[str, Any]) -> dict[str, Any]:
    return profile.get("global_audit_policy", {})
