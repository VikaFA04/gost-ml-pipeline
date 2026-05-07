from __future__ import annotations

import json
from pathlib import Path

from src.rules.methodical_extractor import extract_methodical_profile


def test_extract_methodical_profile_from_text_file(tmp_path) -> None:
    source_file = tmp_path / "guideline.txt"
    source_file.write_text(
        "\n".join(
                [
                    "Левое — 30 мм",
                    "Правое — 10 мм",
                    "Верхнее — 20 мм",
                    "Times New Roman",
                    "полуторный межстрочный интервал",
                    "абзац 1.25 см",
                    "Ссылки в тексте оформляются в квадратных скобках",
                    "Режим доступа: URL: https://example.com",
                    "ГОСТ Р 7.0.100-2018",
                ]
            ),
            encoding="utf-8",
        )

    output_dir = tmp_path / "profiles"
    profile, output_path = extract_methodical_profile(
        input_path=source_file,
        output_dir=output_dir,
        base_profile_ids=["gost_7_32_2017", "gost_r_7_0_100_2018_bibliography"],
        profile_name="Локальная методичка",
    )

    assert output_path.exists()
    assert output_path.parent == output_dir
    assert profile["profile_id"] == f"methodical_{source_file.stem}"
    assert profile["profile_name"] == "Локальная методичка"
    assert profile["profile_type"] == "methodical_guidelines"
    assert profile["source_name"] == source_file.name
    assert profile["extraction_meta"]["generated_from_methodical_guidelines"] is True
    assert round(profile["document_rules"]["page"]["margin_left_cm"], 2) == 3.0
    assert round(profile["document_rules"]["default_font"]["font_size_pt"], 2) == 14.0
    assert profile["document_rules"]["default_line_spacing"] == 1.5
    assert round(profile["labels"]["body_text"]["style_profile"]["first_line_indent_cm"], 2) == 1.25
    assert profile["citation_rules"]["enabled"] is True
    assert profile["citation_rules"]["in_text_reference_patterns"] == [
        r"^\[[0-9]+\]$",
        r"^\[[0-9]+,\s*с\.\s*[0-9\-]+\]$",
        r"^\[[0-9]+\.[0-9]+\]$",
        r"^\[[0-9]+\.[0-9]+,\s*с\.\s*[0-9\-]+\]$",
    ]
    assert r"^\[[^\]]+\]$" not in profile["citation_rules"].get("in_text_reference_patterns", [])
    assert isinstance(profile["numbering_rules"]["unnumbered_sections"], list)
    assert "ВВЕДЕНИЕ" in profile["numbering_rules"]["unnumbered_sections"]
    assert "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ" in profile["numbering_rules"]["unnumbered_sections"]
    assert profile["numbering_rules"]["title_section"]["pattern"] == "^\\d+\\s+.+$"
    assert profile["extraction_meta"]["extraction_confidence"] >= 0.65
    assert isinstance(profile["extraction_meta"]["needs_manual_review"], bool)
    assert profile["labels"]["list_item"]["text_constraints"]["allowed_markers"] == ["-", "—", "●", "■", "○", "1.", "а)"]
    assert profile["bibliography_rules"]["general"]["require_source_title_for_articles"] is True
    assert "web_markers" in profile["bibliography_rules"]["soft_features"]
    assert "standard_markers" in profile["bibliography_rules"]["soft_features"]
    assert "book" in profile["bibliography_rules"]["entry_patterns"]
    assert "web_resource" in profile["bibliography_rules"]["entry_patterns"]
    assert "Режим доступа" in profile["nn_context"]["expected_bibliography_keywords"]

    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded["profile_id"] == profile["profile_id"]


def test_extract_methodical_profile_from_pdf_file(tmp_path) -> None:
    import fitz

    source_file = tmp_path / "guideline.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Левое — 30 мм\nПравое — 10 мм\nTimes New Roman\nполуторный межстрочный интервал")
    doc.save(str(source_file))
    doc.close()

    profile, output_path = extract_methodical_profile(
        input_path=source_file,
        output_dir=tmp_path / "profiles",
        base_profile_ids=["gost_7_32_2017"],
        profile_name="PDF методичка",
    )

    assert output_path.exists()
    assert profile["profile_name"] == "PDF методичка"
    assert profile["document_rules"]["default_font"]["font_name"] == "Times New Roman"
