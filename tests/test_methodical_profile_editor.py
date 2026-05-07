from __future__ import annotations

from src.rules.profile_loader import load_profile
from app import _apply_methodical_form_edits


def test_methodical_profile_form_edits_structure_and_bibliography() -> None:
    profile = load_profile(profile_id="gost_7_32_2017")
    edited = _apply_methodical_form_edits(
        profile,
        {
            "profile_name": "Локальный профиль",
            "base_profiles": ["gost_7_32_2017"],
            "margin_left_cm": 3.5,
            "margin_right_cm": 1.2,
            "margin_top_cm": 2.2,
            "margin_bottom_cm": 2.4,
            "font_name": "Arial",
            "font_size_pt": 13,
            "default_line_spacing": 1.25,
            "body_first_line_indent_cm": 1.0,
            "body_line_spacing": 1.5,
            "title_left_indent_cm": 1.0,
            "title_font_size_pt": 19,
            "title_space_after_pt": 8.0,
            "title_bold": False,
            "list_left_indent_cm": 1.5,
            "list_line_spacing": 1.25,
            "figure_alignment": "CENTER",
            "figure_font_size_pt": 11,
            "bibliography_title_left_indent_cm": 1.0,
            "bibliography_title_font_size_pt": 15,
            "title_section_numbering_enabled": False,
            "title_section_numbering_pattern": r"^\d+\s+.+$",
            "title_subsection_numbering_enabled": True,
            "title_subsection_numbering_pattern": r"^\d+\.\d+\s+.+$",
            "unnumbered_sections": "ВВЕДЕНИЕ\nЗАКЛЮЧЕНИЕ",
            "bibliography_enabled": True,
            "bibliography_separate_profile_required": False,
            "bibliography_require_url": True,
            "bibliography_book_markers": "с.\nизд.\n— Москва",
            "bibliography_journal_markers": "//\n№\nС.",
            "bibliography_web_markers": "[Электронный ресурс]\nURL:\nРежим доступа:",
            "bibliography_standard_markers": "ГОСТ\nГОСТ Р",
            "bibliography_book_patterns": "^.+\\s+[–—]\\s+.+,\\s+\\d{4}\\.\\s+[–—]\\s+\\d+\\s*с\\.?$",
            "bibliography_journal_patterns": "^.+\\s*/\\s*.+\\s*(//|\\/\\/)\\s*.+\\.\\s+[–—]\\s+\\d{4}\\.\\s+[–—]\\s*№\\s*.+\\.\\s+[–—]\\s*С\\.\\s*.+$",
            "bibliography_web_patterns": "^.+URL:\\s*https?://.+$",
            "bibliography_standard_patterns": "^ГОСТ\\s+.+$",
            "bibliography_law_patterns": "^.+\\s+от\\s+\\d{2}\\.\\d{2}\\.\\d{4}.+$",
            "bibliography_thesis_patterns": "^.+\\s*:\\s*автореф\\..+$",
            "nn_expected_bibliography_keywords": "URL\nЭлектронный ресурс\nГОСТ",
            "citation_enabled": True,
            "citation_patterns": [
                r"^\[[0-9]+\]$",
                r"^\[[0-9]+\.[0-9]+,\s*с\.\s*[0-9\-]+\]$",
            ],
        },
    )

    assert edited["profile_name"] == "Локальный профиль"
    assert edited["document_rules"]["page"]["margin_left_cm"] == 3.5
    assert edited["document_rules"]["default_font"]["font_name"] == "Arial"
    assert edited["labels"]["title_section"]["style_profile"]["bold"] is False
    assert edited["numbering_rules"]["title_section"]["enabled"] is False
    assert edited["numbering_rules"]["unnumbered_sections"] == ["ВВЕДЕНИЕ", "ЗАКЛЮЧЕНИЕ"]
    assert edited["bibliography_rules"]["enabled"] is True
    assert edited["bibliography_rules"]["general"]["require_url_for_web_resource"] is True
    assert edited["bibliography_rules"]["soft_features"]["book_markers"] == ["с.", "изд.", "— Москва"]
    assert edited["bibliography_rules"]["soft_features"]["journal_markers"] == ["//", "№", "С."]
    assert edited["bibliography_rules"]["soft_features"]["web_markers"] == ["[Электронный ресурс]", "URL:", "Режим доступа:"]
    assert edited["bibliography_rules"]["soft_features"]["standard_markers"] == ["ГОСТ", "ГОСТ Р"]
    assert edited["bibliography_rules"]["entry_patterns"]["book"] == [r"^.+\s+[–—]\s+.+,\s+\d{4}\.\s+[–—]\s+\d+\s*с\.?$"]
    assert edited["bibliography_rules"]["entry_patterns"]["web_resource"] == [r"^.+URL:\s*https?://.+$"]
    assert edited["nn_context"]["expected_bibliography_keywords"] == ["URL", "Электронный ресурс", "ГОСТ"]
    assert edited["citation_rules"]["enabled"] is True
    assert edited["citation_rules"]["in_text_reference_patterns"] == [
        r"^\[[0-9]+\]$",
        r"^\[[0-9]+\.[0-9]+,\s*с\.\s*[0-9\-]+\]$",
    ]
