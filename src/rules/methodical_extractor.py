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
        raise ImportError("Для извлечения текста из PDF нужен пакет pypdf. Установи: pip install pypdf") from e

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
        return _read_pdf_text(path)
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


def _extract_reference_rules(text: str, profile: dict[str, Any]) -> None:
    if re.search(r"Web[\-\s]?ссыл", text, flags=re.IGNORECASE):
        profile["bibliography_rules"].setdefault("general", {})["require_url_for_web_resource"] = True

    if re.search(r"Ссылки\s+в\s+тексте.+квадратн", text, flags=re.IGNORECASE):
        profile["citation_rules"]["enabled"] = True
        profile["citation_rules"]["in_text_reference_patterns"] = [
            r"^\[[0-9]+\]$",
            r"^\[[0-9]+\.[0-9]+\]$",
            r"^\[[0-9]+\.[0-9]+,\s*с\.[0-9\-]+\]$",
            r"^\[[0-9]+,\s*с\.[0-9\-]+\]$",
        ]


def extract_methodical_profile(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    base_profile_ids: list[str] | None = None,
    profile_name: str | None = None,
) -> tuple[dict[str, Any], Path]:
    input_path = Path(input_path)
    text = extract_text_from_file(input_path)

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
    _extract_reference_rules(text, profile)

    profile["extraction_meta"] = {
        "generated_automatically": True,
        "generated_from_methodical_guidelines": True,
        "source_file_name": input_path.name,
        "extraction_confidence": 0.65,
        "needs_manual_review": True,
    }

    output_dir = Path(output_dir) if output_dir else PROFILES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{profile['profile_id']}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    return profile, output_path
