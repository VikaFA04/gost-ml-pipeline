from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.rules.profile_loader import PROFILES_DIR, deep_merge, load_profile


def _read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception as e:
        try:
            import fitz  # PyMuPDF
        except Exception as fitz_exc:
            raise ImportError(
                "Для извлечения текста из PDF нужен пакет pypdf или PyMuPDF. "
                "Установи: pip install pypdf pymupdf"
            ) from fitz_exc

        document = fitz.open(str(path))
        return "\n".join((page.get_text("text") or "") for page in document)

    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _read_docx_text(path: Path) -> str:
    from docx import Document
    document = Document(str(path))
    return "\n".join(p.text.strip() for p in document.paragraphs if p.text and p.text.strip())


def extract_text_from_file(path: str | Path) -> str:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = _read_pdf_text(path)
        if not text.strip():
            raise ValueError(
                f"PDF-файл не содержит извлекаемого текста: {path}. "
                "Если это скан, нужен OCR-проход перед извлечением профиля."
            )
        return text
    if suffix == ".docx":
        return _read_docx_text(path)
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    raise ValueError(f"Неподдерживаемый формат методички: {path.suffix}")


def _search_float(text: str, patterns: list[str], default: float) -> float:
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            value = m.group(1).replace(",", ".")
            try:
                return float(value)
            except Exception:
                pass
    return default


def _search_font_name(text: str, default: str = "Times New Roman") -> str:
    return "Times New Roman" if re.search(r"Times\s+New\s+Roman", text, flags=re.IGNORECASE) else default


def _has_pattern(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE))


def _extract_document_rules(text: str, profile: dict[str, Any]) -> None:
    body = profile["labels"]["body_text"]["style_profile"]

    font_name = _search_font_name(text)
    font_size = _search_float(text, [r"кегль\s*(\d{1,2})", r"размер[^\d]{0,10}(\d{1,2})\s*пт"], 14.0)
    line_spacing = 1.5 if re.search(r"полутор", text, flags=re.IGNORECASE) else 1.0
    first_line_indent = _search_float(text, [r"абзац[^\d]{0,20}(\d+[.,]?\d*)\s*см", r"первая\s+строка[^\d]{0,20}(\d+[.,]?\d*)\s*см"], 1.25)
    margin_left_mm = _search_float(text, [r"левое\s*[—\-:]\s*(\d+[.,]?\d*)\s*мм"], 30.0)
    margin_right_mm = _search_float(text, [r"правое\s*[—\-:]\s*(\d+[.,]?\d*)\s*мм"], 10.0)
    margin_top_mm = _search_float(text, [r"верхн[ее]+\s*(?:и\s*нижн[ее]+\s*)?[—\-:]\s*(\d+[.,]?\d*)\s*мм"], 20.0)

    profile["document_rules"]["page"]["margin_left_cm"] = round(margin_left_mm / 10.0, 2)
    profile["document_rules"]["page"]["margin_right_cm"] = round(margin_right_mm / 10.0, 2)
    profile["document_rules"]["page"]["margin_top_cm"] = round(margin_top_mm / 10.0, 2)
    profile["document_rules"]["page"]["margin_bottom_cm"] = round(margin_top_mm / 10.0, 2)
    profile["document_rules"]["default_font"]["font_name"] = font_name
    profile["document_rules"]["default_font"]["font_size_pt"] = font_size
    profile["document_rules"]["default_line_spacing"] = line_spacing

    body["font_size_pt"] = font_size
    body["line_spacing"] = line_spacing
    body["first_line_indent_cm"] = first_line_indent


def _extract_structure_rules(text: str, profile: dict[str, Any]) -> None:
    numbering_rules = profile.setdefault("numbering_rules", {})
    nn_context = profile.setdefault("nn_context", {})
    labels = profile.setdefault("labels", {})

    base_sections = [
        "СОДЕРЖАНИЕ",
        "ВВЕДЕНИЕ",
        "ЗАКЛЮЧЕНИЕ",
        "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
        "ПРИЛОЖЕНИЯ",
    ]
    present_sections: list[str] = []
    for section_name, pattern in [
        ("СОДЕРЖАНИЕ", r"\bСОДЕРЖАНИЕ\b"),
        ("ВВЕДЕНИЕ", r"\bВВЕДЕНИЕ\b"),
        ("ЗАКЛЮЧЕНИЕ", r"\bЗАКЛЮЧЕНИЕ\b"),
        ("СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", r"\bСПИСОК\s+ИСПОЛЬЗОВАННЫХ\s+ИСТОЧНИКОВ\b"),
        ("ПРИЛОЖЕНИЯ", r"\bПРИЛОЖЕНИЯ\b"),
    ]:
        if _has_pattern(text, pattern):
            present_sections.append(section_name)

    merged_sections: list[str] = []
    for section_name in [*base_sections, *present_sections]:
        if section_name not in merged_sections:
            merged_sections.append(section_name)
    numbering_rules["unnumbered_sections"] = merged_sections
    nn_context["expected_section_keywords"] = [section.lower() for section in merged_sections]

    if _has_pattern(text, r"^\s*\d+\s+[А-ЯA-ZЁ]"):
        numbering_rules.setdefault("title_section", {})["enabled"] = True
        numbering_rules["title_section"]["pattern"] = r"^\d+\s+.+$"

    if _has_pattern(text, r"^\s*\d+\.\d+\s+[А-ЯA-ZЁ]"):
        numbering_rules.setdefault("title_subsection", {})["enabled"] = True
        numbering_rules["title_subsection"]["pattern"] = r"^\d+\.\d+\s+.+$"

    if _has_pattern(text, r"Рисунок\s+\d+\.\d+\s+—"):
        nn_context.setdefault("prefix_patterns", {})["figure_caption"] = r"^Рисунок\s+\d+\.\d+\s+—\s+.+"
    if _has_pattern(text, r"Таблица\s+\d+\.\d+\s+—"):
        nn_context.setdefault("prefix_patterns", {})["table_caption"] = r"^Таблица\s+\d+\.\d+\s+—\s+.+"
    if _has_pattern(text, r"Приложение\s+[А-ЯA-Z]"):
        nn_context.setdefault("prefix_patterns", {})["appendix_title"] = r"^Приложение\s+[А-ЯA-Z]"

    list_item_cfg = labels.setdefault("list_item", {}).setdefault("text_constraints", {})
    list_item_cfg["list_marker_expected"] = True
    list_item_cfg["allowed_markers"] = ["-", "—", "●", "■", "○", "1.", "а)"]
    numbering_rules["list_items"] = {
        "allowed_markers": ["-", "—", "●", "■", "○", "1.", "а)"],
        "marker_indent_cm": 1.25,
        "text_indent_cm": 2.25,
    }

    bibliography_keywords = [
        "Список использованных источников",
        "URL",
        "Режим доступа",
        "Автор",
        "Год",
        "Журнал",
        "Электронный ресурс",
        "ГОСТ",
    ]
    nn_context["expected_bibliography_keywords"] = bibliography_keywords
    bibliography_rules = profile.setdefault("bibliography_rules", {})
    bibliography_rules["enabled"] = True
    bibliography_rules["separate_profile_required"] = True
    bibliography_rules.setdefault("general", {})["require_source_title_for_articles"] = True
    bibliography_rules["general"]["require_author_or_title"] = True
    bibliography_rules["general"]["require_year"] = True
    bibliography_rules["general"]["require_url_for_web_resource"] = True
    bibliography_rules["general"]["allow_double_slash_for_article_source"] = True
    bibliography_rules["general"]["allow_dash_separators"] = True
    bibliography_rules["entry_patterns"] = {
        "book": [
            r"^.+\s+[–—]\s+.+,\s+\d{4}\.\s+[–—]\s+\d+\s*с\.?$",
            r"^.+\s*:\s*.+\s*/\s*.+\s+[–—]\s+.+,\s+\d{4}\.\s+[–—]\s+\d+\s*с\.?$",
        ],
        "journal_article": [
            r"^.+\s*/\s*.+\s*(//|\/\/)\s*.+\.\s+[–—]\s+\d{4}\.\s+[–—]\s*№\s*.+\.\s+[–—]\s*С\.\s*.+$",
        ],
        "web_resource": [
            r"^.+\[Электронный ресурс\].+URL:\s*.+$",
            r"^.+URL:\s*https?://.+$",
        ],
        "standard": [
            r"^ГОСТ\s+.+$",
            r"^ГОСТ\s+Р\s+.+$",
        ],
        "law": [
            r"^.+\s+от\s+\d{2}\.\d{2}\.\d{4}.+$",
        ],
        "thesis": [
            r"^.+\s*:\s*дис\..+$",
            r"^.+\s*:\s*автореф\..+$",
        ],
    }


def _extract_bibliography_soft_features(text: str, profile: dict[str, Any]) -> None:
    bibliography_rules = profile.setdefault("bibliography_rules", {})
    soft_features = bibliography_rules.setdefault("soft_features", {})

    detected_soft_features: dict[str, list[str]] = {
        "book_markers": [],
        "journal_markers": [],
        "web_markers": [],
        "standard_markers": [],
    }

    if _has_pattern(text, r"\bс\."):
        detected_soft_features["book_markers"].append("с.")
    if _has_pattern(text, r"\bизд\."):
        detected_soft_features["book_markers"].append("изд.")
    if _has_pattern(text, r"—\s*Москва"):
        detected_soft_features["book_markers"].append("— Москва")
    if _has_pattern(text, r"—\s*СПб\."):
        detected_soft_features["book_markers"].append("— СПб.")
    if _has_pattern(text, r"—\s*М\."):
        detected_soft_features["book_markers"].append("— М.")

    if _has_pattern(text, r"//"):
        detected_soft_features["journal_markers"].append("//")
    if _has_pattern(text, r"\b№\b"):
        detected_soft_features["journal_markers"].append("№")
    if _has_pattern(text, r"\bС\."):
        detected_soft_features["journal_markers"].append("С.")
    if _has_pattern(text, r"\bТ\."):
        detected_soft_features["journal_markers"].append("Т.")
    if _has_pattern(text, r"\bВып\."):
        detected_soft_features["journal_markers"].append("Вып.")

    if _has_pattern(text, r"Электронный\s+ресурс"):
        detected_soft_features["web_markers"].append("[Электронный ресурс]")
    if _has_pattern(text, r"\bURL:"):
        detected_soft_features["web_markers"].append("URL:")
    if _has_pattern(text, r"Режим\s+доступа"):
        detected_soft_features["web_markers"].append("Режим доступа:")

    if _has_pattern(text, r"\bГОСТ\s+Р\b"):
        detected_soft_features["standard_markers"].append("ГОСТ Р")
    if _has_pattern(text, r"\bГОСТ\b"):
        detected_soft_features["standard_markers"].append("ГОСТ")

    for key, markers in detected_soft_features.items():
        if not markers:
            continue
        existing = soft_features.get(key)
        merged: list[str] = []
        for marker in [*(existing if isinstance(existing, list) else []), *markers]:
            if marker not in merged:
                merged.append(marker)
        soft_features[key] = merged


def _update_bibliography_context(profile: dict[str, Any]) -> None:
    bibliography_rules = profile.get("bibliography_rules", {})
    soft_features = bibliography_rules.get("soft_features", {})
    entry_patterns = bibliography_rules.get("entry_patterns", {})
    nn_context = profile.setdefault("nn_context", {})

    keywords: list[str] = ["Список использованных источников"]
    if soft_features.get("book_markers"):
        keywords.extend(["с.", "изд.", "— Москва", "— СПб.", "— М."])
    if soft_features.get("journal_markers"):
        keywords.extend(["//", "№", "С.", "Т.", "Вып."])
    if soft_features.get("web_markers"):
        keywords.extend(["URL", "Электронный ресурс", "Режим доступа"])
    if soft_features.get("standard_markers"):
        keywords.extend(["ГОСТ", "ГОСТ Р"])

    deduped_keywords: list[str] = []
    for keyword in keywords:
        if keyword not in deduped_keywords:
            deduped_keywords.append(keyword)
    nn_context["expected_bibliography_keywords"] = deduped_keywords

    reference_entry_types = [entry_type for entry_type, patterns in entry_patterns.items() if patterns]
    if reference_entry_types:
        nn_context["reference_entry_types"] = reference_entry_types


def _extract_reference_rules(text: str, profile: dict[str, Any]) -> None:
    bibliography_rules = profile.setdefault("bibliography_rules", {})

    if _has_pattern(text, r"Web[\-\s]?ссыл"):
        bibliography_rules.setdefault("general", {})["require_url_for_web_resource"] = True

    if _has_pattern(text, r"Ссылки\s+в\s+тексте.+квадратн"):
        profile.setdefault("citation_rules", {})["enabled"] = True


def extract_methodical_profile(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    base_profile_ids: list[str] | None = None,
    profile_name: str | None = None,
) -> tuple[dict[str, Any], Path]:
    input_path = Path(input_path)
    text = extract_text_from_file(input_path)

    profile = build_methodical_profile(
        input_path=input_path,
        text=text,
        base_profile_ids=base_profile_ids,
        profile_name=profile_name,
    )

    output_dir = Path(output_dir) if output_dir else PROFILES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = save_methodical_profile(profile=profile, output_dir=output_dir)
    return profile, output_path


def build_methodical_profile(
    input_path: str | Path,
    text: str,
    base_profile_ids: list[str] | None = None,
    profile_name: str | None = None,
) -> dict[str, Any]:
    input_path = Path(input_path)

    base_profile_ids = base_profile_ids or ["gost_7_32_2017", "gost_r_7_0_100_2018_bibliography"]

    profile = load_profile(profile_id=base_profile_ids[0])
    for extra_base in base_profile_ids[1:]:
        profile = deep_merge(profile, load_profile(profile_id=extra_base))

    profile = deepcopy(profile)
    profile["profile_id"] = f"methodical_{input_path.stem}"
    profile["profile_name"] = profile_name or f"Методические указания: {input_path.stem}"
    profile["profile_type"] = "methodical_guidelines"
    profile["source_type"] = "user_uploaded"
    profile["source_name"] = input_path.name
    profile["description"] = "Профиль, автоматически извлеченный из пользовательской методички"
    profile["is_default"] = False
    profile["base_profiles"] = base_profile_ids

    _extract_document_rules(text, profile)
    _extract_structure_rules(text, profile)
    _extract_bibliography_soft_features(text, profile)
    _extract_reference_rules(text, profile)
    _update_bibliography_context(profile)

    match_score = 0
    match_score += 1 if _has_pattern(text, r"Times\s+New\s+Roman") else 0
    match_score += 1 if _has_pattern(text, r"полутор") else 0
    match_score += 1 if _has_pattern(text, r"СОДЕРЖАНИЕ") else 0
    match_score += 1 if _has_pattern(text, r"Рисунок\s+\d+\.\d+\s+—") else 0
    match_score += 1 if _has_pattern(text, r"Таблица\s+\d+\.\d+\s+—") else 0
    extraction_confidence = round(min(1.0, 0.45 + match_score * 0.1), 2)

    profile["extraction_meta"] = {
        "generated_automatically": True,
        "generated_from_methodical_guidelines": True,
        "source_file_name": input_path.name,
        "extraction_confidence": extraction_confidence,
        "needs_manual_review": extraction_confidence < 0.9,
    }

    return profile


def save_methodical_profile(
    profile: dict[str, Any],
    output_dir: str | Path | None = None,
) -> Path:
    output_dir = Path(output_dir) if output_dir else PROFILES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{profile['profile_id']}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    return output_path
