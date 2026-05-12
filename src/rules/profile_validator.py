from __future__ import annotations

from typing import Any

REQUIRED_TOP_LEVEL_KEYS = {
    "profile_id",
    "profile_name",
    "profile_type",
    "source_type",
    "source_name",
    "description",
    "version",
    "language",
    "is_default",
    "base_profiles",
    "document_rules",
    "labels",
    "numbering_rules",
    "bibliography_rules",
    "citation_rules",
    "global_audit_policy",
    "nn_context",
    "extraction_meta",
}

REQUIRED_STYLE_KEYS = {
    "alignment",
    "first_line_indent_cm",
    "left_indent_cm",
    "line_spacing",
    "space_before_pt",
    "space_after_pt",
    "font_size_pt",
    "bold",
}

ALLOWED_ALIGNMENTS = {"LEFT", "CENTER", "RIGHT", "JUSTIFY", "DISTRIBUTE"}

ALLOWED_BIBLIOGRAPHY_SCOPES: set[str] = {"per_document", "per_section", "per_subsection_pattern"}


def validate_profile(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing_top = REQUIRED_TOP_LEVEL_KEYS - set(profile.keys())
    if missing_top:
        errors.append(f"Отсутствуют обязательные верхнеуровневые ключи: {sorted(missing_top)}")

    if not isinstance(profile.get("base_profiles", []), list):
        errors.append("Поле base_profiles должно быть списком")

    labels = profile.get("labels", {})
    if not isinstance(labels, dict):
        errors.append("Поле labels должно быть словарем")
        return errors

    for label_name, label_cfg in labels.items():
        if not isinstance(label_cfg, dict):
            errors.append(f"Конфигурация label '{label_name}' должна быть словарем")
            continue

        style_profile = label_cfg.get("style_profile")
        if not isinstance(style_profile, dict):
            errors.append(f"В label '{label_name}' отсутствует корректный style_profile")
            continue

        missing_style = REQUIRED_STYLE_KEYS - set(style_profile.keys())
        if missing_style:
            errors.append(f"В style_profile label '{label_name}' отсутствуют ключи: {sorted(missing_style)}")

        alignment = style_profile.get("alignment")
        if alignment not in ALLOWED_ALIGNMENTS:
            errors.append(f"В label '{label_name}' недопустимое alignment='{alignment}'")

        for key in [
            "first_line_indent_cm",
            "left_indent_cm",
            "line_spacing",
            "space_before_pt",
            "space_after_pt",
            "font_size_pt",
        ]:
            if not isinstance(style_profile.get(key), (int, float)):
                errors.append(f"В label '{label_name}' поле '{key}' должно быть числом")

        if not isinstance(style_profile.get("bold"), bool):
            errors.append(f"В label '{label_name}' поле 'bold' должно быть bool")

    # D-11 — list_detection (optional). If present, must be dict with int fields.
    list_detection = profile.get("list_detection")
    if list_detection is not None:
        if not isinstance(list_detection, dict):
            errors.append("Поле list_detection должно быть словарем")
        else:
            for key in ("max_fallback_words", "max_fallback_chars"):
                if key in list_detection and not isinstance(list_detection[key], int):
                    errors.append(f"В list_detection поле '{key}' должно быть целым числом")

    # D-03 — numbering.bibliography.scope (optional).
    numbering = profile.get("numbering")
    if numbering is not None:
        if not isinstance(numbering, dict):
            errors.append("Поле numbering должно быть словарем")
        else:
            bibliography_cfg = numbering.get("bibliography")
            if bibliography_cfg is not None:
                if not isinstance(bibliography_cfg, dict):
                    errors.append("Поле numbering.bibliography должно быть словарем")
                else:
                    scope = bibliography_cfg.get("scope")
                    if scope is not None and scope not in ALLOWED_BIBLIOGRAPHY_SCOPES:
                        errors.append(
                            f"Недопустимое numbering.bibliography.scope='{scope}'; "
                            f"допустимые: {sorted(ALLOWED_BIBLIOGRAPHY_SCOPES)}"
                        )

    return errors


def assert_valid_profile(profile: dict[str, Any]) -> None:
    errors = validate_profile(profile)
    if errors:
        raise ValueError("Профиль не прошел валидацию:\n- " + "\n- ".join(errors))
