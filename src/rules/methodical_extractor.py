from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterator

from src.rules.profile_loader import PROFILES_DIR, deep_merge, load_profile


# ---------------------------------------------------------------------------
# Source attribution helpers (Phase 5 D-05)
# ---------------------------------------------------------------------------


def _clamp_confidence(c: float) -> float:
    """T-05-02 mitigation: clamp confidence to [0.0, 1.0] on emit."""
    if c < 0.0:
        return 0.0
    if c > 1.0:
        return 1.0
    return c


def _annotate(value: Any, file_name: str, loc: str, confidence: float) -> dict[str, Any]:
    """Wrap a leaf value with its `_source` sidecar. D-05 schema."""
    c = _clamp_confidence(confidence)
    return {
        "value": value,
        "_source": {
            "file": file_name,
            "loc": loc,
            "confidence": c,
            "needs_review": c < 0.7,
        },
    }


def _any_leaf_needs_review(node: Any) -> bool:
    """Walk profile dict; True if any leaf's _source.needs_review is True.
    The _source dict itself is NOT recursed into."""
    if isinstance(node, dict):
        if "_source" in node and isinstance(node["_source"], dict):
            if node["_source"].get("needs_review"):
                return True
        return any(_any_leaf_needs_review(v) for k, v in node.items() if k != "_source")
    if isinstance(node, list):
        return any(_any_leaf_needs_review(item) for item in node)
    return False


# ---------------------------------------------------------------------------
# Chunked text iteration (Phase 5 D-05 + Pitfall 2)
# ---------------------------------------------------------------------------


def iterate_text_chunks(path: Path) -> Iterator[tuple[str, str]]:
    """Yield (loc_label, text). PDF -> page_N, DOCX -> paragraph_N, TXT/MD -> line_N.
    Per Pitfall 2: strip Arabic-block noise from PDF text before yielding."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        import fitz
        doc = fitz.open(str(path))
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            text = re.sub(r"[؀-ۿ]", "", text)  # Pitfall 2
            if text.strip():
                yield (f"page_{i}", text)
    elif suffix == ".docx":
        from docx import Document
        document = Document(str(path))
        for i, p in enumerate(document.paragraphs, start=1):
            t = (p.text or "").strip()
            if t:
                yield (f"paragraph_{i}", t)
    elif suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), start=1):
            if line.strip():
                yield (f"line_{i}", line)
    else:
        raise ValueError(f"Неподдерживаемый формат методички: {path.suffix}")


def extract_text_from_file(path: str | Path) -> str:
    """Thin backwards-compat wrapper: joins chunks into a single string."""
    chunks = list(iterate_text_chunks(Path(path)))
    if Path(path).suffix.lower() == ".pdf" and not chunks:
        raise ValueError(
            f"PDF-файл не содержит извлекаемого текста: {path}. "
            "Если это скан, нужен OCR-проход перед извлечением профиля."
        )
    return "\n".join(text for _, text in chunks)


# ---------------------------------------------------------------------------
# Chunk-aware search primitives
# ---------------------------------------------------------------------------


def _search_float_chunks(
    chunks: list[tuple[str, str]],
    patterns: list[str],
    default: float,
) -> tuple[float, str, float]:
    """Return (value, loc, confidence). On regex hit: confidence=0.85, loc=chunk loc.
    On default fallback: confidence=0.0, loc='default'."""
    for loc, text in chunks:
        for pattern in patterns:
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if m:
                value = m.group(1).replace(",", ".")
                try:
                    return (float(value), loc, 0.85)
                except Exception:
                    continue
    return (default, "default", 0.0)


def _search_font_name_chunks(
    chunks: list[tuple[str, str]],
    default: str = "Times New Roman",
) -> tuple[str, str, float]:
    for loc, text in chunks:
        if re.search(r"Times\s+New\s+Roman", text, flags=re.IGNORECASE):
            return ("Times New Roman", loc, 0.85)
    return (default, "default", 0.0)


def _find_in_chunks(chunks: list[tuple[str, str]], pattern: str) -> tuple[bool, str]:
    """Return (matched, loc). Loc is the chunk's loc on hit, else 'default'."""
    for loc, text in chunks:
        if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            return (True, loc)
    return (False, "default")


# ---------------------------------------------------------------------------
# Extractors (chunk-aware, emit _annotate-wrapped leaves)
# ---------------------------------------------------------------------------


def _extract_document_rules(
    chunks: list[tuple[str, str]],
    profile: dict[str, Any],
    file_name: str,
) -> None:
    body = profile["labels"]["body_text"]["style_profile"]

    font_name, font_loc, font_conf = _search_font_name_chunks(chunks)
    font_size, fs_loc, fs_conf = _search_float_chunks(
        chunks,
        [r"кегль\s*(\d{1,2})", r"размер[^\d]{0,10}(\d{1,2})\s*пт"],
        14.0,
    )
    line_spacing_hit, ls_loc = _find_in_chunks(chunks, r"полутор")
    line_spacing = 1.5 if line_spacing_hit else 1.0
    ls_conf = 0.85 if line_spacing_hit else 0.0
    ls_loc_final = ls_loc if line_spacing_hit else "default"

    first_line_indent, fli_loc, fli_conf = _search_float_chunks(
        chunks,
        [r"абзац[^\d]{0,20}(\d+[.,]?\d*)\s*см", r"первая\s+строка[^\d]{0,20}(\d+[.,]?\d*)\s*см"],
        1.25,
    )
    margin_left_mm, ml_loc, ml_conf = _search_float_chunks(
        chunks,
        [r"левое\s*[—\-:]\s*(\d+[.,]?\d*)\s*мм"],
        30.0,
    )
    margin_right_mm, mr_loc, mr_conf = _search_float_chunks(
        chunks,
        [r"правое\s*[—\-:]\s*(\d+[.,]?\d*)\s*мм"],
        10.0,
    )
    margin_top_mm, mt_loc, mt_conf = _search_float_chunks(
        chunks,
        [r"верхн[ее]+\s*(?:и\s*нижн[ее]+\s*)?[—\-:]\s*(\d+[.,]?\d*)\s*мм"],
        20.0,
    )

    profile["document_rules"]["page"]["margin_left_cm"] = _annotate(
        round(margin_left_mm / 10.0, 2), file_name, ml_loc, ml_conf,
    )
    profile["document_rules"]["page"]["margin_right_cm"] = _annotate(
        round(margin_right_mm / 10.0, 2), file_name, mr_loc, mr_conf,
    )
    profile["document_rules"]["page"]["margin_top_cm"] = _annotate(
        round(margin_top_mm / 10.0, 2), file_name, mt_loc, mt_conf,
    )
    profile["document_rules"]["page"]["margin_bottom_cm"] = _annotate(
        round(margin_top_mm / 10.0, 2), file_name, mt_loc, mt_conf,
    )
    profile["document_rules"]["default_font"]["font_name"] = _annotate(
        font_name, file_name, font_loc, font_conf,
    )
    profile["document_rules"]["default_font"]["font_size_pt"] = _annotate(
        font_size, file_name, fs_loc, fs_conf,
    )
    profile["document_rules"]["default_line_spacing"] = _annotate(
        line_spacing, file_name, ls_loc_final, ls_conf,
    )

    body["font_size_pt"] = _annotate(font_size, file_name, fs_loc, fs_conf)
    body["line_spacing"] = _annotate(line_spacing, file_name, ls_loc_final, ls_conf)
    body["first_line_indent_cm"] = _annotate(
        first_line_indent, file_name, fli_loc, fli_conf,
    )


def _extract_structure_rules(
    chunks: list[tuple[str, str]],
    profile: dict[str, Any],
    file_name: str,
) -> None:
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
        hit, _ = _find_in_chunks(chunks, pattern)
        if hit:
            present_sections.append(section_name)

    merged_sections: list[str] = []
    for section_name in [*base_sections, *present_sections]:
        if section_name not in merged_sections:
            merged_sections.append(section_name)
    numbering_rules["unnumbered_sections"] = merged_sections
    nn_context["expected_section_keywords"] = [section.lower() for section in merged_sections]

    title_section_hit, _ = _find_in_chunks(chunks, r"^\s*\d+\s+[А-ЯA-ZЁ]")
    if title_section_hit:
        numbering_rules.setdefault("title_section", {})["enabled"] = True
        numbering_rules["title_section"]["pattern"] = r"^\d+\s+.+$"

    title_subsection_hit, _ = _find_in_chunks(chunks, r"^\s*\d+\.\d+\s+[А-ЯA-ZЁ]")
    if title_subsection_hit:
        numbering_rules.setdefault("title_subsection", {})["enabled"] = True
        numbering_rules["title_subsection"]["pattern"] = r"^\d+\.\d+\s+.+$"

    figure_hit, _ = _find_in_chunks(chunks, r"Рисунок\s+\d+\.\d+\s+—")
    if figure_hit:
        nn_context.setdefault("prefix_patterns", {})["figure_caption"] = r"^Рисунок\s+\d+\.\d+\s+—\s+.+"
    table_hit, _ = _find_in_chunks(chunks, r"Таблица\s+\d+\.\d+\s+—")
    if table_hit:
        nn_context.setdefault("prefix_patterns", {})["table_caption"] = r"^Таблица\s+\d+\.\d+\s+—\s+.+"
    appendix_hit, _ = _find_in_chunks(chunks, r"Приложение\s+[А-ЯA-Z]")
    if appendix_hit:
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


def _extract_bibliography_soft_features(
    chunks: list[tuple[str, str]],
    profile: dict[str, Any],
    file_name: str,
) -> None:
    bibliography_rules = profile.setdefault("bibliography_rules", {})
    soft_features = bibliography_rules.setdefault("soft_features", {})

    detected_soft_features: dict[str, list[str]] = {
        "book_markers": [],
        "journal_markers": [],
        "web_markers": [],
        "standard_markers": [],
    }

    book_checks = [
        (r"\bс\.", "с."),
        (r"\bизд\.", "изд."),
        (r"—\s*Москва", "— Москва"),
        (r"—\s*СПб\.", "— СПб."),
        (r"—\s*М\.", "— М."),
    ]
    for pattern, marker in book_checks:
        hit, _ = _find_in_chunks(chunks, pattern)
        if hit:
            detected_soft_features["book_markers"].append(marker)

    journal_checks = [
        (r"//", "//"),
        (r"\b№\b", "№"),
        (r"\bС\.", "С."),
        (r"\bТ\.", "Т."),
        (r"\bВып\.", "Вып."),
    ]
    for pattern, marker in journal_checks:
        hit, _ = _find_in_chunks(chunks, pattern)
        if hit:
            detected_soft_features["journal_markers"].append(marker)

    web_checks = [
        (r"Электронный\s+ресурс", "[Электронный ресурс]"),
        (r"\bURL:", "URL:"),
        (r"Режим\s+доступа", "Режим доступа:"),
    ]
    for pattern, marker in web_checks:
        hit, _ = _find_in_chunks(chunks, pattern)
        if hit:
            detected_soft_features["web_markers"].append(marker)

    standard_checks = [
        (r"\bГОСТ\s+Р\b", "ГОСТ Р"),
        (r"\bГОСТ\b", "ГОСТ"),
    ]
    for pattern, marker in standard_checks:
        hit, _ = _find_in_chunks(chunks, pattern)
        if hit:
            detected_soft_features["standard_markers"].append(marker)

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


def _extract_reference_rules(
    chunks: list[tuple[str, str]],
    profile: dict[str, Any],
    file_name: str,
) -> None:
    bibliography_rules = profile.setdefault("bibliography_rules", {})

    web_hit, _ = _find_in_chunks(chunks, r"Web[\-\s]?ссыл")
    if web_hit:
        bibliography_rules.setdefault("general", {})["require_url_for_web_resource"] = True

    bracket_hit, _ = _find_in_chunks(chunks, r"Ссылки\s+в\s+тексте.+квадратн")
    if bracket_hit:
        profile.setdefault("citation_rules", {})["enabled"] = True


# ---------------------------------------------------------------------------
# Public API (signatures kept stable for src/main.py)
# ---------------------------------------------------------------------------


def extract_methodical_profile(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    base_profile_ids: list[str] | None = None,
    profile_name: str | None = None,
) -> tuple[dict[str, Any], Path]:
    input_path = Path(input_path)

    profile = build_methodical_profile(
        input_path=input_path,
        base_profile_ids=base_profile_ids,
        profile_name=profile_name,
    )

    output_dir = Path(output_dir) if output_dir else PROFILES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = save_methodical_profile(profile=profile, output_dir=output_dir)
    return profile, output_path


def build_methodical_profile(
    input_path: str | Path,
    base_profile_ids: list[str] | None = None,
    profile_name: str | None = None,
) -> dict[str, Any]:
    input_path = Path(input_path)
    chunks = list(iterate_text_chunks(input_path))
    if input_path.suffix.lower() == ".pdf" and not chunks:
        raise ValueError(
            f"PDF-файл не содержит извлекаемого текста: {input_path}. "
            "Если это скан, нужен OCR-проход перед извлечением профиля."
        )
    file_name = input_path.name

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

    _extract_document_rules(chunks, profile, file_name)
    _extract_structure_rules(chunks, profile, file_name)
    _extract_bibliography_soft_features(chunks, profile, file_name)
    _extract_reference_rules(chunks, profile, file_name)
    _update_bibliography_context(profile)

    profile["extraction_meta"] = {
        "generated_automatically": True,
        "generated_from_methodical_guidelines": True,
        "source_file_name": input_path.name,
        "needs_manual_review": _any_leaf_needs_review(profile),
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
