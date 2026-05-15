# Phase 6 Wave 0 RED stubs for app.STATUS_CHIP and app.modal_reason_is_valid
# (which do not yet exist in app.py).
#
# Module-level `pytest.importorskip("streamlit")` lets collection succeed on
# system Python — every test then skips cleanly. On a Streamlit-enabled venv
# the imports of `app.STATUS_CHIP` / `app.modal_reason_is_valid` raise
# AttributeError, which is the deliberate RED signal until Wave 2/4.
#
# Coverage matches plan §Task 2 behavior list:
#   1. STATUS_CHIP covers all 5 statuses
#   2. STATUS_CHIP reuses one of the existing `.badge-*` CSS classes
#   3. STATUS_CHIP carries the Russian labels from UI-SPEC §Color status-chip
#   4-7. modal_reason_is_valid rejects empty / short / whitespace, accepts 8
#   8.   modal_reason_is_valid strips before counting
#   9.   SUPPORTED_UPLOAD_TYPES regression guard during Wave 2 sidebar redesign

from __future__ import annotations

import pytest

pytest.importorskip("streamlit")

import app  # noqa: E402  — gated by importorskip above


def test_status_chip_covers_all_five_statuses() -> None:
    from app import STATUS_CHIP

    assert set(STATUS_CHIP) == {
        "no_change",
        "changed",
        "review",
        "error",
        "blocked_unsafe_autofix",
    }


def test_status_chip_uses_existing_badge_classes() -> None:
    from app import STATUS_CHIP

    allowed_classes = {"badge-ok", "badge-change", "badge-warn", "badge-error", "badge-muted"}
    for status, value in STATUS_CHIP.items():
        # Each value is a tuple of (icon, label, css_class). Third element
        # must reuse one of the 5 existing inject_page_styles classes per
        # CLAUDE.md «не рефактори то, что работает».
        assert len(value) == 3, f"STATUS_CHIP[{status!r}] must be a 3-tuple (icon, label, css_class)"
        assert value[2] in allowed_classes, (
            f"STATUS_CHIP[{status!r}] css class {value[2]!r} not in {allowed_classes}"
        )


def test_status_chip_russian_labels_are_present() -> None:
    from app import STATUS_CHIP

    expected_labels = {
        "no_change": "Без изменений",
        "changed": "Изменено",
        "review": "Требует проверки",
        "error": "Ошибка",
        "blocked_unsafe_autofix": "Небезопасное автоисправление заблокировано",
    }
    for status, label in expected_labels.items():
        assert STATUS_CHIP[status][1] == label, (
            f"STATUS_CHIP[{status!r}] label {STATUS_CHIP[status][1]!r} != {label!r}"
        )


def test_modal_reason_is_valid_rejects_empty() -> None:
    from app import modal_reason_is_valid

    assert modal_reason_is_valid("") is False


def test_modal_reason_is_valid_rejects_short() -> None:
    from app import modal_reason_is_valid

    assert modal_reason_is_valid("abcdefg") is False  # 7 chars


def test_modal_reason_is_valid_rejects_whitespace_only() -> None:
    from app import modal_reason_is_valid

    assert modal_reason_is_valid("       ") is False
    assert modal_reason_is_valid("\t\n\r ") is False


def test_modal_reason_is_valid_accepts_exactly_8() -> None:
    from app import modal_reason_is_valid

    assert modal_reason_is_valid("abcdefgh") is True


def test_modal_reason_is_valid_strips_before_count() -> None:
    from app import modal_reason_is_valid

    assert modal_reason_is_valid("  abcdefgh  ") is True  # 8 chars after strip


def test_app_upload_contract_unchanged() -> None:
    """Phase 7 D-04 §3 contract: uploader accepts DOCX and PDF (PDF audit-only)."""
    assert app.SUPPORTED_UPLOAD_TYPES == ["docx", "pdf"]
