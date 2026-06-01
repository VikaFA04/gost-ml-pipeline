from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.inference.application_service import (
    REPORTS_DIR,
    ProcessingArtifacts,
    get_profile_options,
    list_model_options,
    process_document,
    save_uploaded_bytes,
)
from src.inference.pdf_loader import PdfNoTextLayer
from src.inference.run_log import RunLog
from src.rules.methodical_extractor import build_methodical_profile, save_methodical_profile
from src.rules.profile_diff import compute_profile_diff
from src.rules.profile_loader import PROFILES_DIR, list_available_profiles, load_profile

# Phase 7 contract preserved (REQ-pdf-text-only test guard) — the constant still
# advertises DOCX+PDF for backward-compatibility with tests/test_app_upload_contract.py
# and tests/test_streamlit_smoke.py. The v1.1 redesign deliberately surfaces ONLY
# DOCX in the uploader widget (UPLOADER_ACCEPT_TYPES below) for friendlier UX.
# PDF flow remains intact in src/inference/pdf_loader.py + application_service.py
# but is unreachable from the new UI.
SUPPORTED_UPLOAD_TYPES = ["docx", "pdf"]
UPLOADER_ACCEPT_TYPES = ["docx"]
SUPPORTED_METHODICAL_UPLOAD_TYPES = ["pdf", "docx", "txt", "md"]
CUSTOM_PROFILES_DIR = Path("results/generated_profiles")

# STATUS_CHIP carries the 5 Phase 6 statuses. v1.1 Editorial palette drops the
# emoji prefixes — anti-AI-slop dictates text-only chips with semantic color.
# Keys preserved (Phase 6 regression test test_status_chip_covers_all_five).
STATUS_CHIP: dict[str, tuple[str, str, str]] = {
    "no_change":              ("●",  "Без изменений",                                "badge-ok"),
    "changed":                ("●", "Изменено",                                     "badge-change"),
    "review":                 ("●", "Требует проверки",                             "badge-warn"),
    "error":                  ("●",  "Ошибка",                                       "badge-error"),
    "blocked_unsafe_autofix": ("●", "Небезопасное автоисправление заблокировано",   "badge-muted"),
}


def modal_reason_is_valid(reason: str) -> bool:
    """D-004 / T-05-01: reason must be ≥8 chars after strip AND contain at
    least one printable non-whitespace character."""
    stripped = (reason or "").strip()
    if len(stripped) < 8:
        return False
    return any(c.isprintable() and not c.isspace() for c in stripped)


def preflight_translate_error(exc: Exception) -> str:
    """Translate a backend exception into a fixed Russian user-message.

    Returns ONLY one of 5 fixed strings — never str(exc) (PII boundary per
    06-UI-SPEC §Error state copy + 06-RESEARCH.md §5). PdfNoTextLayer branch
    is defensive (v1.1 UI does not surface PDF uploads but the constant still
    advertises the type for backward-compat tests).
    """
    if isinstance(exc, (FileNotFoundError, zipfile.BadZipFile)):
        return (
            "Файл не читается. Проверьте, что это валидный DOCX (.docx, ZIP-архив). "
            "Откройте файл в Word и пересохраните, если нужно."
        )
    if isinstance(exc, PdfNoTextLayer):
        return "PDF без извлекаемого текстового слоя — OCR не поддерживается."
    if isinstance(exc, ValueError):
        msg = str(exc)
        if "extractable non-empty blocks" in msg:
            return "В документе нет извлекаемых непустых блоков. Проверьте, что документ содержит текст."
        if "Unsupported input format" in msg or "Only DOCX is currently supported" in msg:
            return "Расширение файла `.docx`, но содержимое не соответствует DOCX-формату."
        return "Не удалось обработать документ. См. журнал запуска."
    return "Не удалось обработать документ. См. журнал запуска."


st.set_page_config(page_title="ГОСТ Formatter", page_icon="·", layout="wide")


def inject_page_styles() -> None:
    """v1.1 Editorial-restraint palette per `interface/` baseline + anti-AI-slop principles.

    Design lineage: Pentagram / Michael Bierut + Information Architects content-first.
    - Monochrome base + one rust accent (#7C2D12) — no purple, no gradient.
    - Serif display (EB Garamond) + sans body (Inter) + mono numerics (JetBrains Mono).
    - Text-first stat cards. UPPERCASE letterspaced tabs.
    - All page-styling lives here; no inline styles in render_* helpers other than
      semantic class names.
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

        :root {
            --paper: #FAFAF7;
            --paper-soft: #F5F2EA;
            --ink: #1A1A1A;
            --ink-soft: #3A352F;
            --muted: #6B6155;
            --hairline: #E5E0D6;
            --accent: #7C2D12;
            --accent-hover: #9A3412;
            --review: #B45309;
            --error: #991B1B;
            --success: #14532D;
            --change: #1E40AF;
        }

        /* Global ------------------------------------------------------- */
        html, body, [class*="css"], .stApp {
            background: var(--paper) !important;
            color: var(--ink) !important;
            font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
            font-size: 15px;
            line-height: 1.55;
        }
        [data-testid="stHeader"] { background: transparent; }

        /* Tighter outer padding for academic feel */
        .main .block-container {
            padding-top: 2.2rem;
            padding-bottom: 4rem;
            max-width: 1180px;
        }

        /* Headings ----------------------------------------------------- */
        h1, h2, h3, h4 {
            font-family: 'EB Garamond', 'Times New Roman', serif !important;
            color: var(--ink) !important;
            font-weight: 500 !important;
            letter-spacing: -0.01em;
        }
        h1 { font-size: 2.6rem; line-height: 1.12; text-wrap: balance; }
        h2 { font-size: 1.7rem; line-height: 1.25; }
        h3 { font-size: 1.25rem; }
        p, li, label { text-wrap: pretty; }

        /* Hero (header strip) ----------------------------------------- */
        .hero {
            padding: 2.2rem 0 1.6rem 0;
            border-bottom: 1px solid var(--hairline);
            margin-bottom: 2.4rem;
        }
        .hero .eyebrow {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.22em;
            color: var(--accent);
            margin-bottom: 0.6rem;
        }
        .hero h1 {
            margin: 0 0 0.5rem 0;
            font-size: 2.4rem;
            font-weight: 500;
            font-style: italic;
        }
        .hero .lead {
            color: var(--muted);
            font-size: 1.02rem;
            max-width: 720px;
        }

        /* Sidebar ----------------------------------------------------- */
        [data-testid="stSidebar"] {
            background: var(--paper-soft) !important;
            border-right: 1px solid var(--hairline);
        }
        [data-testid="stSidebar"] .stMarkdown h2 {
            font-size: 1.05rem;
            margin: 0.4rem 0 1rem 0;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            color: var(--muted);
            font-family: 'Inter', sans-serif !important;
            font-weight: 600;
        }
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
            font-size: 0.8rem !important;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--muted) !important;
            font-weight: 600;
        }

        /* Uploader region --------------------------------------------- */
        section[data-testid="stFileUploader"] > section {
            background: transparent;
            border: 1.5px dashed var(--hairline);
            border-radius: 0;
            padding: 1.4rem 1.2rem;
        }
        section[data-testid="stFileUploader"] > section:hover {
            border-color: var(--accent);
        }
        section[data-testid="stFileUploader"] small {
            color: var(--muted);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            letter-spacing: 0.04em;
        }

        /* Primary CTA (rust filled, full width) ----------------------- */
        .stButton > button {
            font-family: 'Inter', sans-serif !important;
            font-weight: 600;
            border-radius: 0;
            border: 1px solid var(--ink);
            background: var(--paper);
            color: var(--ink);
            padding: 0.65rem 1.4rem;
            font-size: 0.92rem;
            transition: all 0.15s ease;
            box-shadow: none;
            letter-spacing: 0.02em;
        }
        .stButton > button:hover {
            background: var(--ink);
            color: var(--paper);
            border-color: var(--ink);
        }
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {
            background: var(--accent);
            border-color: var(--accent);
            color: var(--paper);
            font-size: 0.98rem;
            padding: 0.85rem 1.6rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .stButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="baseButton-primary"]:hover {
            background: var(--accent-hover);
            border-color: var(--accent-hover);
        }
        .stDownloadButton > button {
            background: var(--paper);
            border: 1px solid var(--hairline);
            color: var(--ink);
            border-radius: 0;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
        }
        .stDownloadButton > button:hover {
            border-color: var(--ink);
            background: var(--paper-soft);
        }

        /* Status banners ---------------------------------------------- */
        .stAlert {
            border-radius: 0 !important;
            border-left: 3px solid var(--accent);
            background: var(--paper-soft) !important;
        }
        div[data-testid="stAlert"][data-baseweb="notification"] {
            border-radius: 0 !important;
        }

        /* Editorial divider ------------------------------------------- */
        .divider {
            border: none;
            border-top: 1px solid var(--hairline);
            margin: 2rem 0;
        }
        .divider-strong {
            border: none;
            border-top: 2px solid var(--ink);
            margin: 2.2rem 0;
        }

        /* Stat cards (text-first, monochrome, anti-slop) -------------- */
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 1px;
            background: var(--hairline);
            border: 1px solid var(--hairline);
            margin: 1.4rem 0 1.2rem 0;
        }
        .stat-cell {
            background: var(--paper);
            padding: 1.4rem 1.2rem 1.2rem 1.2rem;
            min-height: 154px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .stat-cell .stat-label {
            font-family: 'Inter', sans-serif;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            color: var(--muted);
            font-weight: 600;
            margin-bottom: 0.8rem;
        }
        .stat-cell .stat-value {
            font-family: 'EB Garamond', serif;
            font-size: 3rem;
            line-height: 1;
            font-weight: 500;
            color: var(--ink);
            font-feature-settings: 'lnum';
        }
        .stat-cell .stat-value-mono {
            font-family: 'JetBrains Mono', monospace;
            font-size: 2.3rem;
            line-height: 1;
            font-weight: 500;
            color: var(--ink);
        }
        .stat-cell.accent .stat-value { color: var(--accent); }
        .stat-cell .stat-desc {
            font-size: 0.82rem;
            color: var(--muted);
            margin-top: 0.7rem;
            line-height: 1.4;
        }
        .stat-cell .stat-pct {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: var(--muted);
            letter-spacing: 0.04em;
            margin-top: 0.3rem;
        }

        /* Meta line (Профиль · Загружено · N блоков) ------------------ */
        .meta-line {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            color: var(--muted);
            letter-spacing: 0.05em;
            padding: 0.6rem 0;
            border-top: 1px solid var(--hairline);
            border-bottom: 1px solid var(--hairline);
            display: flex;
            gap: 1.6rem;
            flex-wrap: wrap;
        }
        .meta-line .meta-key {
            text-transform: uppercase;
            font-size: 0.68rem;
            letter-spacing: 0.16em;
            color: var(--muted);
            margin-right: 0.4rem;
        }
        .meta-line .meta-val {
            color: var(--ink);
        }

        /* Tabs (UPPERCASE letterspaced underline) --------------------- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1.6rem;
            background: transparent;
            border-bottom: 1px solid var(--hairline);
            padding-bottom: 0;
            margin-bottom: 1.6rem;
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent !important;
            color: var(--muted) !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            padding: 0.6rem 0 0.9rem 0 !important;
            border-radius: 0 !important;
            border: none !important;
            border-bottom: 2px solid transparent !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: var(--ink) !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: var(--ink) !important;
            border-bottom: 2px solid var(--accent) !important;
        }
        .stTabs [data-baseweb="tab-highlight"] { display: none !important; }

        /* DataFrames (table-first) ------------------------------------ */
        .stDataFrame {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.78rem;
        }
        .stDataFrame [data-testid="stTable"] th {
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-size: 0.7rem;
            color: var(--muted);
        }

        /* Status chips (text-only, anti-slop) ------------------------- */
        .status-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.18rem 0.6rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            border: 1px solid currentColor;
            font-weight: 500;
        }
        .badge-ok      { color: var(--success); }
        .badge-change  { color: var(--change); }
        .badge-warn    { color: var(--review); }
        .badge-error   { color: var(--error); }
        .badge-muted   { color: var(--muted); }

        /* Quality progress (Обзор tab) -------------------------------- */
        .quality-bar {
            margin: 1.6rem 0 0.8rem 0;
        }
        .quality-bar .ql-label {
            font-family: 'Inter', sans-serif;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            color: var(--muted);
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
        }
        .quality-bar .ql-value {
            color: var(--ink);
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.04em;
        }
        .quality-bar .ql-track {
            height: 4px;
            background: var(--paper-soft);
            border: 1px solid var(--hairline);
        }
        .quality-bar .ql-fill {
            height: 100%;
            background: var(--accent);
            transition: width 0.4s ease;
        }

        /* Artifact tile ---------------------------------------------- */
        .artifact-tile {
            border: 1px solid var(--hairline);
            padding: 1.2rem;
            background: var(--paper);
            margin-bottom: 1rem;
            transition: border-color 0.15s ease;
        }
        .artifact-tile:hover { border-color: var(--ink); }
        .artifact-tile h4 {
            margin: 0 0 0.3rem 0;
            font-size: 1rem;
            font-weight: 500;
            font-family: 'EB Garamond', serif;
        }
        .artifact-tile p {
            margin: 0 0 0.8rem 0;
            color: var(--muted);
            font-size: 0.85rem;
        }
        .artifact-tile .path-line {
            margin-top: 0.4rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
            color: var(--muted);
            letter-spacing: 0.02em;
            word-break: break-all;
        }

        /* Block table block-id link feel ------------------------------ */
        .block-row-meta {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            color: var(--muted);
            letter-spacing: 0.04em;
        }

        /* Footer signature -------------------------------------------- */
        .editorial-footer {
            margin-top: 3.5rem;
            padding-top: 1.4rem;
            border-top: 1px solid var(--hairline);
            color: var(--muted);
            font-size: 0.78rem;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.04em;
            display: flex;
            justify-content: space-between;
        }

        /* Empty state -------------------------------------------------- */
        .empty-state {
            padding: 3.2rem 0;
            text-align: center;
            border-top: 1px solid var(--hairline);
            border-bottom: 1px solid var(--hairline);
            margin: 2rem 0;
        }
        .empty-state .rule {
            display: inline-block;
            width: 36px;
            height: 1px;
            background: var(--ink);
            margin-bottom: 1.4rem;
        }
        .empty-state p {
            font-family: 'EB Garamond', serif;
            font-style: italic;
            font-size: 1.15rem;
            color: var(--ink-soft);
            margin: 0;
        }
        .empty-state .sub {
            font-family: 'Inter', sans-serif;
            font-style: normal;
            font-size: 0.82rem;
            color: var(--muted);
            margin-top: 0.6rem;
            letter-spacing: 0.04em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def normalize_table_values(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare dataframe values for UI display."""
    if df.empty:
        return df
    normalized = df.copy()
    for column in normalized.columns:
        normalized[column] = normalized[column].fillna("")
    return normalized


def format_profile_option(item: dict[str, str]) -> str:
    profile_name = item.get("profile_name", "Профиль")
    profile_id = item.get("profile_id", "unknown")
    profile_type = item.get("profile_type", "unknown")
    source_type = item.get("source_type", "unknown")
    return f"{profile_name} [{profile_id}] · {profile_type} · {source_type}"


def build_profile_options(profile_items: list[dict[str, str]], custom_items: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    seen_profile_ids: set[str] = set()
    for item in [*profile_items, *custom_items]:
        profile_id = str(item.get("profile_id", ""))
        if profile_id and profile_id in seen_profile_ids:
            continue
        if profile_id:
            seen_profile_ids.add(profile_id)
        merged.append(item)
    return merged


def render_hero() -> None:
    """Editorial hero: serif italic title + rust eyebrow + lead paragraph.

    No gradient, no glossy. One subtle border-bottom for academic feel.
    """
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">ГОСТ 7.32-2017 · Нормоконтроль</div>
            <h1>Аудит академического документа &mdash; блок за блоком.</h1>
            <p class="lead">
                Загрузите DOCX, выберите профиль ГОСТ, запустите анализ.
                Система извлечёт структурные блоки, классифицирует их,
                сверит с нормоконтролем и предложит безопасные правки.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    """Editorial empty-state — italic prompt + thin rule."""
    st.markdown(
        """
        <div class="empty-state">
            <div class="rule"></div>
            <p>Загрузите DOCX-документ для проверки.</p>
            <div class="sub">В левой панели выберите профиль ГОСТ &middot; справа &mdash; загрузка файла</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_meta_line(profile_label: str | None, filename: str | None, block_count: int | None) -> None:
    """Single mono-fonted line: Профиль · Загружено · N блоков."""
    parts = []
    if profile_label:
        parts.append(
            f'<span><span class="meta-key">Профиль</span><span class="meta-val">{profile_label}</span></span>'
        )
    if filename:
        parts.append(
            f'<span><span class="meta-key">Документ</span><span class="meta-val">{filename}</span></span>'
        )
    if block_count is not None:
        parts.append(
            f'<span><span class="meta-key">Блоков</span><span class="meta-val">{block_count}</span></span>'
        )
    if not parts:
        return
    st.markdown(
        f'<div class="meta-line">{" ".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def render_stat_grid(summary: dict[str, Any], report_df: pd.DataFrame | None) -> None:
    """5-card editorial stat grid. Text-first, monochrome with one accent on totals.

    Card 1 (totals) carries the accent. Cards 2-5 stay neutral.
    Each card: small uppercase letterspaced label · big serif numeral · description.

    HTML collapsed to a single line to dodge Streamlit's markdown code-fence detection
    (multi-line nested <div> with indentation gets wrapped in <code>).
    """
    blocks_total = int(summary.get("blocks_total", 0) or 0)
    no_change = int(summary.get("no_change", 0) or 0)
    changed = int(summary.get("changed", 0) or 0)
    review = int(summary.get("review", 0) or 0)
    error = int(summary.get("error", 0) or 0)
    # "Рекомендация" — count of rows where audit engine suggests a change that hasn't
    # been applied yet. Falls back to (blocks_total - no_change - review - error - changed)
    # when action column is missing.
    suggest_change = 0
    if report_df is not None and not report_df.empty and "action" in report_df.columns:
        try:
            suggest_change = int((report_df["action"].astype(str) == "suggest_change").sum())
        except Exception:
            suggest_change = 0
    if suggest_change == 0:
        suggest_change = max(0, blocks_total - no_change - review - error - changed)

    def pct(n: int) -> str:
        return f"{(100 * n / blocks_total):.1f}%" if blocks_total else "—"

    cells = [
        ("Блоки", blocks_total, "Выделенные структурные элементы документа", "", True),
        ("Без изменений", no_change, "Соответствуют ожидаемому профилю", pct(no_change), False),
        ("Рекомендация", suggest_change, "Можно скорректировать безопасно", pct(suggest_change), False),
        ("Ручная проверка", review, "Низкая уверенность модели", pct(review), False),
        ("Авто-исправлено", changed, "Безопасно применённые изменения", pct(changed), False),
    ]

    html_cells = []
    for label, value, desc, percent, is_accent in cells:
        accent_cls = " accent" if is_accent else ""
        pct_html = f'<div class="stat-pct">{percent}</div>' if percent else ""
        # Single-line per cell — no leading whitespace, no newlines inside.
        html_cells.append(
            f'<div class="stat-cell{accent_cls}"><div class="stat-label">{label}</div><div class="stat-value">{value}</div>{pct_html}<div class="stat-desc">{desc}</div></div>'
        )

    st.markdown(
        f'<div class="stat-grid">{"".join(html_cells)}</div>',
        unsafe_allow_html=True,
    )


def render_artifact_tile(title: str, description: str, path: Path, mime: str, key: str) -> None:
    """Editorial download tile: serif title, muted description, mono path,
    then a Streamlit download_button styled via injected CSS."""
    st.markdown(
        f"""
        <div class="artifact-tile">
            <h4>{title}</h4>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with open(path, "rb") as artifact_file:
        st.download_button(
            f"Скачать {path.name}",
            data=artifact_file.read(),
            file_name=path.name,
            mime=mime,
            use_container_width=True,
            key=key,
        )
    st.markdown(f'<div class="artifact-tile path-line">{path}</div>', unsafe_allow_html=True)


def _has(value: Any) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None


def compute_quality_score(summary: dict[str, Any]) -> float:
    """Quality bar value: (no_change + auto_fixed/2) / total. Heuristic — anchors the
    Обзор tab's progress bar so users have a single-number signal.

    Returns a float in [0, 1].
    """
    total = float(summary.get("blocks_total", 0) or 0)
    if total == 0:
        return 0.0
    no_change = float(summary.get("no_change", 0) or 0)
    auto = float(summary.get("changed", 0) or 0)
    return min(1.0, (no_change + auto * 0.5) / total)


def render_quality_bar(summary: dict[str, Any]) -> None:
    score = compute_quality_score(summary)
    pct = f"{score * 100:.1f}%"
    st.markdown(
        f"""
        <div class="quality-bar">
            <div class="ql-label">
                <span>Качество документа</span>
                <span class="ql-value">{pct}</span>
            </div>
            <div class="ql-track"><div class="ql-fill" style="width: {score * 100:.1f}%"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _select_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return only the requested columns that exist, in order."""
    available = [c for c in columns if c in df.columns]
    if not available:
        return df
    return df[available]


def render_tab_overview(result: ProcessingArtifacts, profile_label: str | None) -> None:
    """Обзор: text summary + quality progress bar. Quiet."""
    summary = result.summary
    total = int(summary.get("blocks_total", 0) or 0)
    no_change = int(summary.get("no_change", 0) or 0)
    changed = int(summary.get("changed", 0) or 0)
    review = int(summary.get("review", 0) or 0)

    sentences = []
    profile_phrase = f"Активный профиль: {profile_label}." if profile_label else ""
    sentences.append(profile_phrase)
    sentences.append(
        f"Извлечено блоков: {total}. Без изменений — {no_change}, "
        f"рекомендация на исправление — {changed}, на ручную проверку — {review}."
    )
    if review > 0:
        sentences.append("Есть блоки, требующие ручной проверки — посмотрите вкладку «Аудит».")
    if changed > 0:
        sentences.append("Есть рекомендации к исправлению — посмотрите вкладку «Форматирование».")

    body = " ".join([s for s in sentences if s])
    st.markdown(f"<p style='font-size: 1.02rem; color: var(--ink-soft); max-width: 720px;'>{body}</p>", unsafe_allow_html=True)
    render_quality_bar(summary)


def render_tab_predictions(result: ProcessingArtifacts) -> None:
    """Предсказания: filter dropdown + DataFrame.

    Columns prioritized per interface/4.jpg: block_id, kind, predicted_label,
    postprocessed_label, confidence_score, low_confidence, text.
    """
    df = result.predictions_df
    if df is None or df.empty:
        st.markdown('<p class="block-row-meta">Нет данных предсказаний.</p>', unsafe_allow_html=True)
        return

    df = normalize_table_values(df.copy())
    label_col = "postprocessed_label" if "postprocessed_label" in df.columns else "predicted_label"
    classes = ["Все"] + sorted({str(v) for v in df[label_col].unique() if str(v).strip()})
    pick = st.selectbox(
        "Фильтр по предсказанному классу",
        options=classes,
        index=0,
        key="predictions_class_filter",
    )
    filtered = df if pick == "Все" else df[df[label_col].astype(str) == pick]
    cols = ["block_id", "kind", "predicted_label", "postprocessed_label",
            "confidence_score", "low_confidence", "text"]
    st.dataframe(
        _select_columns(filtered, cols),
        use_container_width=True,
        hide_index=True,
        height=500,
    )
    st.markdown(
        f'<div class="block-row-meta">Показано {len(filtered)} из {len(df)} блоков.</div>',
        unsafe_allow_html=True,
    )


def render_tab_audit(result: ProcessingArtifacts) -> None:
    """Аудит: search + status filter + kind filter + low-confidence toggle + table.

    Columns per interface/5.jpg: block_id, kind, label, action, profile_id,
    confidence_score, low_confidence, changed_fields, uncertain_fields, reason.
    """
    df = result.report_df
    if df is None or df.empty:
        st.markdown('<p class="block-row-meta">Нет данных аудита.</p>', unsafe_allow_html=True)
        return

    df = normalize_table_values(df.copy())

    col_a, col_b, col_c = st.columns([1, 1, 0.8])
    status_options = ["Все"] + sorted({str(v) for v in df.get("status", pd.Series(dtype=str)).unique() if str(v).strip()}) if "status" in df.columns else ["Все"]
    kind_options = ["Все"] + sorted({str(v) for v in df.get("kind", pd.Series(dtype=str)).unique() if str(v).strip()}) if "kind" in df.columns else ["Все"]

    with col_a:
        status_pick = st.selectbox("Статус аудита", options=status_options, key="audit_status_filter")
    with col_b:
        kind_pick = st.selectbox("Тип блока", options=kind_options, key="audit_kind_filter")
    with col_c:
        only_low = st.checkbox("Только low confidence", key="audit_low_conf_toggle")

    search = st.text_input("Поиск по тексту блока", key="audit_search")

    filtered = df
    if status_pick != "Все" and "status" in filtered.columns:
        filtered = filtered[filtered["status"].astype(str) == status_pick]
    if kind_pick != "Все" and "kind" in filtered.columns:
        filtered = filtered[filtered["kind"].astype(str) == kind_pick]
    if only_low and "low_confidence" in filtered.columns:
        filtered = filtered[filtered["low_confidence"].apply(lambda v: bool(v) if pd.notna(v) else False)]
    if search:
        if "text" in filtered.columns:
            filtered = filtered[filtered["text"].astype(str).str.contains(search, case=False, na=False)]

    st.markdown(
        f'<div class="block-row-meta">Найдено строк: {len(filtered)}</div>',
        unsafe_allow_html=True,
    )
    cols = ["block_id", "kind", "label", "action", "profile_id", "confidence_score",
            "low_confidence", "changed_fields", "uncertain_fields", "reason"]
    st.dataframe(
        _select_columns(filtered, cols),
        use_container_width=True,
        hide_index=True,
        height=520,
    )


def render_tab_formatting(result: ProcessingArtifacts, uploaded_file, selected_profile_path: str) -> None:
    """Форматирование: trigger re-run in fix mode + download corrected DOCX.

    Editorial layout: serif intro paragraph → CTA → download tile.
    Mode 'fix' is triggered via a separate button here, NOT via a sidebar radio
    (v1.1 redesign — mode lives in the action, not in upfront config).
    """
    if result.input_extension == ".pdf":
        st.markdown(
            '<p class="block-row-meta">'
            'PDF режим аудита — исправленный документ не формируется.'
            '</p>',
            unsafe_allow_html=True,
        )
        return

    has_output = result.output_docx is not None and Path(result.output_docx).exists()
    if has_output:
        st.markdown(
            '<p style="font-family: \'EB Garamond\', serif; font-style: italic; font-size: 1.05rem; '
            'color: var(--ink-soft); max-width: 640px;">'
            'Исправленный DOCX уже сформирован. Скачайте файл ниже или '
            'примените форматирование заново — оригинал не изменяется.'
            '</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<p style="font-family: \'EB Garamond\', serif; font-style: italic; font-size: 1.05rem; '
            'color: var(--ink-soft); max-width: 640px;">'
            'Текущий запуск выполнен в режиме аудита. Чтобы сформировать DOCX с '
            'безопасными правками — нажмите кнопку ниже.'
            '</p>',
            unsafe_allow_html=True,
        )

    cta_label = "Применить безопасное форматирование заново" if has_output else "Применить безопасное форматирование"
    apply_clicked = st.button(cta_label, type="primary", key="formatting_apply_button", use_container_width=False)
    if apply_clicked and uploaded_file is not None:
        # Re-run process_document in fix mode. Single-shot, blocking — no extra RunLog
        # since the new run replaces the old result in session_state.
        with st.spinner("Применяем правки..."):
            input_path = save_uploaded_bytes(
                uploaded_file.getvalue(),
                suffix=Path(uploaded_file.name).suffix,
            )
            try:
                new_result = process_document(
                    input_path=input_path,
                    model_choice="baseline",
                    mode="fix",
                    profile_path=selected_profile_path,
                )
                st.session_state["last_result"] = new_result
                st.rerun()
            except Exception as exc:
                user_msg = preflight_translate_error(exc) if isinstance(exc, (FileNotFoundError, PdfNoTextLayer, ValueError, zipfile.BadZipFile)) else "Не удалось применить форматирование."
                st.error(user_msg)

    if has_output:
        st.markdown('<hr class="divider"/>', unsafe_allow_html=True)
        render_artifact_tile(
            "Исправленный DOCX",
            "Безопасные правки применены. Оригинал не изменён.",
            Path(result.output_docx),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "download_corrected_docx",
        )


def render_tab_artifacts(result: ProcessingArtifacts, run_log_path: Path | None) -> None:
    """Артефакты: 3 download tiles (Report CSV, Summary JSON, Run-log)."""
    if result.report_csv and Path(result.report_csv).exists():
        render_artifact_tile(
            "Отчёт CSV",
            "Таблица по блокам: статусы, нарушенные правила, исправления, объяснения.",
            Path(result.report_csv),
            "text/csv",
            "download_report_csv",
        )
    if result.summary_json and Path(result.summary_json).exists():
        render_artifact_tile(
            "Сводка JSON",
            "Счётчики статусов и технические данные запуска.",
            Path(result.summary_json),
            "application/json",
            "download_summary_json",
        )
    if run_log_path and Path(run_log_path).exists():
        render_artifact_tile(
            "Журнал запуска (JSON)",
            "Стадии пайплайна и статусы. PII-безопасный лог.",
            Path(run_log_path),
            "application/json",
            "download_run_log_json",
        )


def render_report(result: ProcessingArtifacts, filename: str | None, profile_label: str | None, uploaded_file, selected_profile_path: str) -> None:
    """v1.1 tabbed layout per interface/ baseline + Editorial palette.

    Top: stat grid + meta line.
    Tabs (5): Обзор · Предсказания · Аудит · Форматирование · Артефакты.
    """
    summary = result.summary
    block_count = int(summary.get("blocks_total", 0) or 0)

    st.markdown('<h2 style="margin-top: 0.2rem;">Сводка по аудиту</h2>', unsafe_allow_html=True)
    render_stat_grid(summary, result.report_df)
    render_meta_line(profile_label, filename, block_count)

    tab_overview, tab_pred, tab_audit, tab_format, tab_art = st.tabs([
        "Обзор", "Предсказания", "Аудит", "Форматирование", "Артефакты"
    ])
    with tab_overview:
        render_tab_overview(result, profile_label)
    with tab_pred:
        render_tab_predictions(result)
    with tab_audit:
        render_tab_audit(result)
    with tab_format:
        render_tab_formatting(result, uploaded_file, selected_profile_path)
    with tab_art:
        run_log_path = st.session_state.get("last_run_log_path")
        render_tab_artifacts(result, run_log_path)


def _persist_run_log(run_log: RunLog, input_filename: str) -> Path:
    """Dump `run_log` to a stable per-run JSON file under REPORTS_DIR."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(input_filename).stem
    log_path = REPORTS_DIR / f"{stem}_run_log_{timestamp}.json"
    run_log.dump_json(log_path)
    return log_path


def run_processing(uploaded_file, selected_model_key: str, selected_mode: str, selected_profile_path: str) -> None:
    """Execute the backend processing pipeline and store the last result."""
    if uploaded_file is None:
        st.warning("Сначала загрузите DOCX-документ.")
        return

    if selected_model_key == "baseline_unavailable" and Path(uploaded_file.name).suffix.lower() != ".pdf":
        st.error("Baseline-модель недоступна: в workspace нет сохранённого .joblib-артефакта.")
        return

    input_path = save_uploaded_bytes(uploaded_file.getvalue(), suffix=Path(uploaded_file.name).suffix)
    run_log = RunLog(uploaded_file.name)
    run_log.record("document-read", "ok")

    try:
        result = process_document(
            input_path=input_path,
            model_choice=selected_model_key,
            mode=selected_mode,
            profile_path=selected_profile_path,
        )
    except (FileNotFoundError, PdfNoTextLayer, ValueError, zipfile.BadZipFile) as exc:
        user_msg = preflight_translate_error(exc)
        run_log.record(
            "document-read",
            "error",
            error_class=type(exc).__name__,
            error_message=user_msg,
        )
        st.error(user_msg)
        st.session_state["last_run_log"] = run_log
        st.session_state["last_run_log_path"] = _persist_run_log(run_log, uploaded_file.name)
        st.session_state["last_uploaded_name"] = uploaded_file.name
        return
    except Exception as exc:
        run_log.record(
            "unknown",
            "error",
            error_class=type(exc).__name__,
            error_message="Не удалось обработать документ.",
        )
        st.error("Не удалось обработать документ: " + type(exc).__name__)
        st.session_state["last_run_log"] = run_log
        st.session_state["last_run_log_path"] = _persist_run_log(run_log, uploaded_file.name)
        st.session_state["last_uploaded_name"] = uploaded_file.name
        return

    run_log.record("classification", "ok")
    run_log.record("rule-apply", "ok")
    run_log.record("save", "ok")

    st.session_state["last_result"] = result
    st.session_state["last_uploaded_name"] = uploaded_file.name
    st.session_state["last_run_log"] = run_log
    st.session_state["last_run_log_path"] = _persist_run_log(run_log, uploaded_file.name)


@st.dialog("Создать профиль из методички", width="large")
def methodical_modal(available_profile_ids: list[str]) -> None:
    """Methodical-profile-extraction modal mirroring Phase 5 CLI contract."""
    uploaded = st.file_uploader(
        "Загрузите методичку",
        type=SUPPORTED_METHODICAL_UPLOAD_TYPES,
        key="modal_methodical_file",
    )
    if "gost_7_32_2017" in available_profile_ids:
        default_base = ["gost_7_32_2017"]
    elif available_profile_ids:
        default_base = available_profile_ids[:1]
    else:
        default_base = []
    base_ids = st.multiselect(
        "Базовые профили",
        options=available_profile_ids,
        default=default_base,
        key="modal_base_profiles",
    )
    preview_clicked = st.button("Сгенерировать предпросмотр", key="modal_preview_button")
    if preview_clicked:
        if uploaded is None:
            st.warning("Загрузите файл методички (PDF / DOCX / TXT / MD).")
        elif not base_ids:
            st.warning("Выберите хотя бы один базовый профиль.")
        else:
            try:
                tmp_path = save_uploaded_bytes(
                    uploaded.getvalue(),
                    suffix=Path(uploaded.name).suffix,
                )
                draft = build_methodical_profile(input_path=tmp_path, base_profile_ids=base_ids)
                base_profile = load_profile(profile_id=base_ids[0])
                diff_lines = compute_profile_diff(base_profile, draft)
                st.session_state["modal_diff_lines"] = diff_lines
                st.session_state["modal_draft_profile"] = draft
            except ValueError as exc:
                msg = str(exc)
                if "PDF" in msg or "text" in msg.lower():
                    st.error(
                        "PDF-файл не содержит извлекаемого текста. "
                        "Скан без OCR не поддерживается."
                    )
                else:
                    st.error("Не удалось извлечь методичку: " + type(exc).__name__)
            except Exception as exc:
                st.error("Не удалось извлечь методичку: " + type(exc).__name__)

    diff = st.session_state.get("modal_diff_lines")
    draft = st.session_state.get("modal_draft_profile")
    if diff is not None and draft is not None:
        st.code("\n".join(diff), language=None)
        profile_id = draft["profile_id"]
        target_path = CUSTOM_PROFILES_DIR / f"{profile_id}.json"
        target_exists = target_path.exists()
        shadowing_builtin = (PROFILES_DIR / f"{profile_id}.json").exists()
        if shadowing_builtin and not target_exists:
            st.info(
                f"`{profile_id}` совпадает с именем встроенного профиля — "
                "пользовательский профиль скроет встроенный в списке."
            )
        if not target_exists:
            apply_clicked = st.button(
                "Применить и сохранить",
                type="primary",
                key="modal_apply_button",
            )
            if apply_clicked:
                CUSTOM_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
                save_methodical_profile(draft, CUSTOM_PROFILES_DIR)
                new_items = list_available_profiles([PROFILES_DIR, CUSTOM_PROFILES_DIR])
                new_match = next(
                    (it for it in new_items if it.get("profile_id") == profile_id),
                    None,
                )
                if new_match is not None:
                    st.session_state["profile_selectbox"] = format_profile_option(new_match)
                for k in ("modal_diff_lines", "modal_draft_profile"):
                    st.session_state.pop(k, None)
                st.rerun()
        else:
            st.warning(
                f"Профиль `{profile_id}` уже существует. Чтобы перезаписать, "
                "отметьте чекбокс ниже и заполните поле «Причина» (минимум 8 символов)."
            )
            overwrite = st.checkbox(
                "Перезаписать существующий профиль",
                key="modal_overwrite_checkbox",
            )
            reason = st.text_area("Причина (минимум 8 символов)", key="modal_reason_textarea")
            reason_ok = modal_reason_is_valid(reason)
            if not reason_ok and reason:
                st.caption(
                    "Причина должна содержать минимум 8 непробельных символов "
                    "(D-004: no silent rewrites)."
                )
            apply_disabled = not (overwrite and reason_ok)
            apply_clicked = st.button(
                "Применить и сохранить",
                type="primary",
                disabled=apply_disabled,
                key="modal_apply_force_button",
            )
            if apply_clicked and not apply_disabled:
                draft.setdefault("extraction_meta", {})
                draft["extraction_meta"]["override_reason"] = reason.strip()
                CUSTOM_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
                save_methodical_profile(draft, CUSTOM_PROFILES_DIR)
                new_items = list_available_profiles([PROFILES_DIR, CUSTOM_PROFILES_DIR])
                new_match = next(
                    (it for it in new_items if it.get("profile_id") == profile_id),
                    None,
                )
                if new_match is not None:
                    st.session_state["profile_selectbox"] = format_profile_option(new_match)
                for k in ("modal_diff_lines", "modal_draft_profile"):
                    st.session_state.pop(k, None)
                st.rerun()

    cancel_clicked = st.button("Отмена", key="modal_cancel_button")
    if cancel_clicked:
        for k in ("modal_diff_lines", "modal_draft_profile"):
            st.session_state.pop(k, None)
        st.rerun()


def main() -> None:
    """v1.1 Editorial-restraint UI per `interface/` baseline.

    Layout — top to bottom:
      1. Sidebar (minimal): profile select + methodical-upload modal trigger.
      2. Hero: serif italic title + lead paragraph.
      3. Uploader + CTA (DOCX-only surface; PDF code remains unreachable from UI).
      4. Tabs (5) after a successful run.
    """
    inject_page_styles()

    # ----- Sidebar (minimal) -----
    with st.sidebar:
        st.markdown("## Панель управления")
        st.markdown(
            '<p style="font-size: 0.85rem; color: var(--muted); margin-bottom: 1.2rem; line-height: 1.5;">'
            'Выберите профиль ГОСТ или загрузите методичку, '
            'чтобы построить кастомный профиль проверки.'
            '</p>',
            unsafe_allow_html=True,
        )

        profile_items_raw = get_profile_options()
        custom_items_raw = list_available_profiles([CUSTOM_PROFILES_DIR]) if CUSTOM_PROFILES_DIR.exists() else []
        merged_items = build_profile_options(profile_items_raw, custom_items_raw)
        if not merged_items:
            st.error("Профили ГОСТ не найдены в src/rules/profiles.")
            return
        formatted_labels = [format_profile_option(item) for item in merged_items]

        st.markdown(
            '<div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.16em; '
            'color: var(--muted); font-weight: 600; margin-bottom: 0.3rem;">Базовый профиль</div>',
            unsafe_allow_html=True,
        )
        selected_label = st.selectbox(
            label="profile_selectbox_hidden_label",
            label_visibility="collapsed",
            options=formatted_labels,
            key="profile_selectbox",
        )
        selected_index = formatted_labels.index(selected_label)
        selected_item = merged_items[selected_index]
        selected_profile_id = selected_item.get("profile_id", "")
        profile_name = selected_item.get("profile_name", selected_profile_id)
        # profile_label used in meta-line + overview tab — short human-readable.
        profile_label = f"{profile_name} [{selected_profile_id}]"

        # Modal trigger
        open_modal_clicked = st.button(
            "+ Создать профиль из методички",
            key="open_methodical_modal",
            use_container_width=True,
        )
        if open_modal_clicked:
            st.session_state["methodical_modal_request"] = True

        # Resolve profile_path for downstream process_document
        selected_profile_path = ""
        if selected_profile_id:
            candidate_paths = [
                CUSTOM_PROFILES_DIR / f"{selected_profile_id}.json",
                PROFILES_DIR / f"{selected_profile_id}.json",
            ]
            for cp in candidate_paths:
                if cp.exists():
                    selected_profile_path = str(cp)
                    break

        # Model/mode defaults (hidden per v1.1 redesign — model='baseline', mode='audit'
        # by default; 'fix' triggered from the Форматирование tab button).
        model_options = list_model_options()
        if "baseline" in model_options:
            selected_model_key = "baseline"
        elif "baseline_unavailable" in model_options:
            selected_model_key = "baseline_unavailable"
        else:
            selected_model_key = next(iter(model_options.keys()))
        selected_mode = "audit"

    # ----- Methodical modal (if triggered) -----
    available_profile_ids = [item.get("profile_id", "") for item in merged_items if item.get("profile_id")]
    if st.session_state.pop("methodical_modal_request", False):
        methodical_modal(available_profile_ids)

    # ----- Hero -----
    render_hero()

    # ----- Uploader + CTA row -----
    col_upload, col_actions = st.columns([2, 1])
    with col_upload:
        st.markdown(
            '<div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.16em; '
            'color: var(--muted); font-weight: 600; margin-bottom: 0.4rem;">'
            'Загрузите DOCX-документ для проверки'
            '</div>',
            unsafe_allow_html=True,
        )
        # UPLOADER_ACCEPT_TYPES = ['docx'] — v1.1 DOCX-only surface.
        # SUPPORTED_UPLOAD_TYPES (the module constant) stays ['docx', 'pdf'] for
        # backward-compat with Phase 7 tests; the UI surface narrows here.
        uploaded_file = st.file_uploader(
            label="docx_uploader_hidden_label",
            label_visibility="collapsed",
            type=UPLOADER_ACCEPT_TYPES,
            key="docx_uploader",
        )

    with col_actions:
        st.markdown('<div style="height: 1.6rem;"></div>', unsafe_allow_html=True)
        run_disabled = uploaded_file is None
        run_clicked = st.button(
            "Запустить анализ документа",
            type="primary",
            disabled=run_disabled,
            key="run_audit_button",
            use_container_width=True,
        )
        clear_clicked = st.button(
            "Очистить экран",
            disabled=False,
            key="clear_screen_button",
            use_container_width=True,
        )

    if clear_clicked:
        for k in ("last_result", "last_run_log", "last_run_log_path", "last_uploaded_name"):
            st.session_state.pop(k, None)
        st.rerun()

    if run_clicked:
        run_processing(
            uploaded_file=uploaded_file,
            selected_model_key=selected_model_key,
            selected_mode=selected_mode,
            selected_profile_path=selected_profile_path,
        )

    # Status banner for current upload (between CTA and results)
    if uploaded_file is not None:
        st.markdown(
            f'<div class="meta-line" style="margin-top: 1.2rem;">'
            f'<span><span class="meta-key">Загружен DOCX</span>'
            f'<span class="meta-val">{uploaded_file.name}</span></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ----- Results section (after success) -----
    result = st.session_state.get("last_result")
    if result is None:
        render_empty_state()
    else:
        st.markdown('<hr class="divider-strong"/>', unsafe_allow_html=True)
        st.markdown(
            '<div class="meta-line" style="background: transparent; border: none; padding: 0; '
            'color: var(--success); font-family: \'EB Garamond\', serif; font-size: 1rem; '
            'font-style: italic; margin-bottom: 1.2rem;">'
            'Документ обработан успешно.'
            '</div>',
            unsafe_allow_html=True,
        )
        render_report(
            result=result,
            filename=st.session_state.get("last_uploaded_name"),
            profile_label=profile_label,
            uploaded_file=uploaded_file,
            selected_profile_path=selected_profile_path,
        )

    # ----- Footer signature -----
    st.markdown(
        """
        <div class="editorial-footer">
            <span>ГОСТ Formatter v1.1</span>
            <span>Local-only · No PII transmitted</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
