from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.inference.application_service import (
    ProcessingArtifacts,
    get_profile_options,
    list_model_options,
    process_document,
    save_uploaded_bytes,
)
from src.rules.methodical_extractor import build_methodical_profile, extract_text_from_file, save_methodical_profile

SUPPORTED_UPLOAD_TYPES = ["docx"]
SUPPORTED_METHODICAL_UPLOAD_TYPES = ["pdf", "docx", "txt", "md"]
CUSTOM_PROFILES_DIR = Path("results/generated_profiles")

st.set_page_config(page_title="ГОСТ Formatter", page_icon="📄", layout="wide")


def inject_page_styles() -> None:
    """Apply lightweight styling for the restored dashboard structure."""
    st.markdown(
        """
        <style>
        .stApp {
            background: #f4f6fb;
        }
        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid rgba(17, 24, 39, 0.08);
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #111827;
        }
        div[data-testid="stFileUploader"] section {
            border: 1px solid rgba(17, 24, 39, 0.10);
            border-radius: 10px;
            background: #ffffff;
        }
        .stButton > button[kind="primary"] {
            background: #ff1f1f;
            border: 1px solid #e01616;
            border-radius: 8px;
            color: #ffffff;
            font-weight: 700;
            transition: transform 180ms ease, background 180ms ease;
        }
        .stButton > button[kind="primary"]:hover {
            background: #e81717;
            border-color: #d21414;
            color: #ffffff;
            transform: translateY(-1px);
        }
        .stButton > button[kind="secondary"] {
            border-radius: 8px;
        }
        .hero {
            padding: 1.6rem 1.85rem;
            border-radius: 8px;
            background: linear-gradient(135deg, #10192f 0%, #1a2750 55%, #281f62 100%);
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16);
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0 0 0.35rem 0;
            font-size: 1.85rem;
            line-height: 1.15;
            color: #ffffff;
        }
        .hero p {
            margin: 0;
            color: rgba(255, 255, 255, 0.78);
            font-size: 0.96rem;
            max-width: 86ch;
        }
        .hero-meta {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 0.9rem;
        }
        .badge {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            border-radius: 7px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .badge-neutral { background: #eef2ff; color: #243447; }
        .badge-ok { background: #dff7ea; color: #166534; }
        .badge-warn { background: #fff3db; color: #8a5a00; }
        .badge-change { background: #fff1dd; color: #9a4d00; }
        .badge-error { background: #fde7ef; color: #9f1239; }
        .badge-muted { background: #ede9fe; color: #5b21b6; }
        .metric-card {
            border-left: 4px solid #2f67ff;
            border-radius: 10px;
            padding: 1rem 1.1rem;
            background: #ffffff;
            min-height: 110px;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.07);
        }
        .metric-card .label {
            color: #6b7280;
            font-size: 0.85rem;
            margin-bottom: 0.5rem;
        }
        .metric-card .value {
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.1;
            color: #111827;
        }
        .metric-card .meta {
            margin-top: 0.55rem;
            color: #6b7280;
            font-size: 0.85rem;
        }
        .artifact-card {
            border: 1px solid rgba(17, 24, 39, 0.10);
            border-radius: 10px;
            padding: 1rem;
            background: #ffffff;
            height: 100%;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
        }
        .artifact-card h4 {
            margin: 0 0 0.35rem 0;
            font-size: 1rem;
        }
        .artifact-card p {
            margin: 0 0 0.75rem 0;
            color: #6b7280;
            font-size: 0.88rem;
        }
        .section-note {
            color: #6b7280;
            font-size: 0.92rem;
            margin-bottom: 0.75rem;
        }
        div[data-testid="stTabs"] button p {
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    """Render the top hero block."""
    st.markdown(
        """
        <div class="hero">
            <h1>ГОСТ Formatter — интеллектуальный нормоконтроль документов</h1>
            <p>Выбери профиль ГОСТ и загрузи DOCX-документ. Система извлечет блоки,
            классифицирует их, выполнит нормативный аудит и подготовит безопасные исправления.</p>
            <div class="hero-meta">
                <span class="badge badge-neutral">Профиль: ГОСТ 7.32-2017</span>
                <span class="badge badge-neutral">DOCX</span>
                <span class="badge badge-neutral">Аудит и безопасные правки</span>
                <span class="badge badge-neutral">Объяснения по правилам</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: int | str, meta: str) -> None:
    """Render a summary card."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="meta">{meta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badges(summary: dict[str, Any]) -> None:
    """Render status counters as badges."""
    st.markdown(
        (
            '<div class="hero-meta">'
            f'<span class="badge badge-ok">Без изменений: {int(summary.get("no_change", 0))}</span>'
            f'<span class="badge badge-warn">Проверить: {int(summary.get("review", 0))}</span>'
            f'<span class="badge badge-change">Исправить: {int(summary.get("changed", 0))}</span>'
            f'<span class="badge badge-error">Ошибки: {int(summary.get("error", 0))}</span>'
            f'<span class="badge badge-muted">Заблокировано: {int(summary.get("blocked_unsafe_autofix", 0))}</span>'
            "</div>"
        ),
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


def build_methodical_profile_draft(uploaded_file, profile_name: str, base_profile_ids: list[str]) -> dict[str, Any]:
    temp_input = save_uploaded_bytes(uploaded_file.getvalue(), suffix=Path(uploaded_file.name).suffix)
    text = extract_text_from_file(temp_input)
    profile = build_methodical_profile(
        input_path=temp_input,
        text=text,
        base_profile_ids=base_profile_ids or None,
        profile_name=profile_name or f"Методичка: {uploaded_file.name}",
    )
    profile["extraction_meta"]["source_file_name"] = uploaded_file.name
    return profile


def persist_custom_profile(profile: dict[str, Any]) -> dict[str, str]:
    CUSTOM_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = save_methodical_profile(profile=profile, output_dir=CUSTOM_PROFILES_DIR)
    return {
        "profile_id": output_path.stem,
        "profile_name": str(profile.get("profile_name", output_path.stem)),
        "profile_type": str(profile.get("profile_type", "methodical_guidelines")),
        "source_type": str(profile.get("source_type", "user_uploaded")),
        "path": str(output_path),
    }


def _set_session_methodical_draft(profile: dict[str, Any], source_name: str, source_type: str) -> None:
    st.session_state["methodical_profile_draft"] = profile
    st.session_state["methodical_profile_source_name"] = source_name
    st.session_state["methodical_profile_source_type"] = source_type


def _get_session_methodical_draft() -> dict[str, Any] | None:
    draft = st.session_state.get("methodical_profile_draft")
    return draft if isinstance(draft, dict) else None


def _apply_methodical_form_edits(profile: dict[str, Any], form_data: dict[str, Any]) -> dict[str, Any]:
    edited = json.loads(json.dumps(profile, ensure_ascii=False))
    edited["profile_name"] = form_data["profile_name"].strip()
    edited["base_profiles"] = form_data["base_profiles"]

    document_rules = edited.setdefault("document_rules", {})
    page_rules = document_rules.setdefault("page", {})
    default_font = document_rules.setdefault("default_font", {})

    page_rules["margin_left_cm"] = float(form_data["margin_left_cm"])
    page_rules["margin_right_cm"] = float(form_data["margin_right_cm"])
    page_rules["margin_top_cm"] = float(form_data["margin_top_cm"])
    page_rules["margin_bottom_cm"] = float(form_data["margin_bottom_cm"])
    default_font["font_name"] = form_data["font_name"].strip()
    default_font["font_size_pt"] = float(form_data["font_size_pt"])
    document_rules["default_line_spacing"] = float(form_data["default_line_spacing"])

    labels = edited.setdefault("labels", {})
    body_style = labels.setdefault("body_text", {}).setdefault("style_profile", {})
    body_style["first_line_indent_cm"] = float(form_data["body_first_line_indent_cm"])
    body_style["line_spacing"] = float(form_data["body_line_spacing"])

    title_style = labels.setdefault("title_section", {}).setdefault("style_profile", {})
    title_style["left_indent_cm"] = float(form_data["title_left_indent_cm"])
    title_style["font_size_pt"] = float(form_data["title_font_size_pt"])
    title_style["space_after_pt"] = float(form_data["title_space_after_pt"])
    title_style["bold"] = bool(form_data["title_bold"])

    list_style = labels.setdefault("list_item", {}).setdefault("style_profile", {})
    list_style["left_indent_cm"] = float(form_data["list_left_indent_cm"])
    list_style["line_spacing"] = float(form_data["list_line_spacing"])

    figure_style = labels.setdefault("figure_caption", {}).setdefault("style_profile", {})
    figure_style["font_size_pt"] = float(form_data["figure_font_size_pt"])
    figure_style["alignment"] = form_data["figure_alignment"]

    bibliography_title_style = labels.setdefault("bibliography_title", {}).setdefault("style_profile", {})
    bibliography_title_style["font_size_pt"] = float(form_data["bibliography_title_font_size_pt"])
    bibliography_title_style["left_indent_cm"] = float(form_data["bibliography_title_left_indent_cm"])

    numbering_rules = edited.setdefault("numbering_rules", {})
    numbering_rules["title_section"] = {
        "enabled": bool(form_data["title_section_numbering_enabled"]),
        "pattern": str(form_data["title_section_numbering_pattern"]).strip(),
    }
    numbering_rules["title_subsection"] = {
        "enabled": bool(form_data["title_subsection_numbering_enabled"]),
        "pattern": str(form_data["title_subsection_numbering_pattern"]).strip(),
    }
    numbering_rules["unnumbered_sections"] = [
        line.strip()
        for line in str(form_data["unnumbered_sections"]).splitlines()
        if line.strip()
    ]
    bibliography_rules = edited.setdefault("bibliography_rules", {})
    bibliography_rules["enabled"] = bool(form_data["bibliography_enabled"])
    bibliography_rules["separate_profile_required"] = bool(form_data["bibliography_separate_profile_required"])
    bibliography_rules.setdefault("general", {})["require_url_for_web_resource"] = bool(
        form_data["bibliography_require_url"]
    )
    entry_patterns = bibliography_rules.setdefault("entry_patterns", {})
    for field_name, entry_key in [
        ("bibliography_book_patterns", "book"),
        ("bibliography_journal_patterns", "journal_article"),
        ("bibliography_web_patterns", "web_resource"),
        ("bibliography_standard_patterns", "standard"),
        ("bibliography_law_patterns", "law"),
        ("bibliography_thesis_patterns", "thesis"),
    ]:
        patterns = [
            line.strip()
            for line in str(form_data.get(field_name, "")).splitlines()
            if line.strip()
        ]
        entry_patterns[entry_key] = patterns
    soft_features = bibliography_rules.setdefault("soft_features", {})
    for field_name, soft_key in [
        ("bibliography_book_markers", "book_markers"),
        ("bibliography_journal_markers", "journal_markers"),
        ("bibliography_web_markers", "web_markers"),
        ("bibliography_standard_markers", "standard_markers"),
    ]:
        markers = [
            line.strip()
            for line in str(form_data.get(field_name, "")).splitlines()
            if line.strip()
        ]
        soft_features[soft_key] = markers
    citation_rules = edited.setdefault("citation_rules", {})
    citation_rules["enabled"] = bool(form_data["citation_enabled"])
    citation_patterns = [
        str(pattern).strip()
        for pattern in form_data.get("citation_patterns", [])
        if str(pattern).strip()
    ]
    if citation_patterns:
        citation_rules["in_text_reference_patterns"] = citation_patterns
        citation_rules["in_text_reference_pattern"] = citation_patterns[0]
    else:
        citation_rules.pop("in_text_reference_patterns", None)
        citation_rules.pop("in_text_reference_pattern", None)

    nn_context = edited.setdefault("nn_context", {})
    expected_keywords = [
        line.strip()
        for line in str(form_data.get("nn_expected_bibliography_keywords", "")).splitlines()
        if line.strip()
    ]
    if expected_keywords:
        nn_context["expected_bibliography_keywords"] = expected_keywords

    return edited


def filter_audit_df(report_df: pd.DataFrame) -> pd.DataFrame:
    """Apply sidebar-like audit filters within the audit tabs."""
    filtered = normalize_table_values(report_df)
    status_options = sorted(filtered["status"].unique().tolist()) if "status" in filtered.columns else []
    preferred_statuses = ["review", "changed", "error"]
    default_statuses = [status for status in preferred_statuses if status in status_options]
    if not default_statuses:
        default_statuses = status_options
    filter_col1, filter_col2, filter_col3 = st.columns([1.1, 1.1, 1.6])
    with filter_col1:
        statuses = st.multiselect(
            "Статус аудита",
            options=status_options,
            default=default_statuses,
            key="audit_status_filter",
        )
    with filter_col2:
        labels = st.multiselect(
            "Тип блока",
            options=sorted(filtered["label"].unique().tolist()) if "label" in filtered.columns else [],
            default=[],
            key="audit_label_filter",
        )
    with filter_col3:
        text_query = st.text_input("Поиск по тексту, объяснению или правилу", key="audit_text_filter").strip().lower()

    if statuses and "status" in filtered.columns:
        filtered = filtered[filtered["status"].isin(statuses)]
    if labels and "label" in filtered.columns:
        filtered = filtered[filtered["label"].isin(labels)]
    if text_query:
        mask = pd.Series(False, index=filtered.index)
        for column in ["text", "explanation", "violated_rules", "applied_fixes", "reason"]:
            if column in filtered.columns:
                mask = mask | filtered[column].astype(str).str.lower().str.contains(text_query, na=False)
        filtered = filtered[mask]
    return filtered


def filter_predictions_df(predictions_df: pd.DataFrame) -> pd.DataFrame:
    """Apply prediction-specific filters."""
    filtered = normalize_table_values(predictions_df)
    filter_col1, filter_col2, filter_col3 = st.columns([1.1, 1.1, 1.2])
    with filter_col1:
        labels = st.multiselect(
            "Предсказанный тип",
            options=sorted(filtered["postprocessed_label"].unique().tolist()) if "postprocessed_label" in filtered.columns else [],
            default=[],
            key="prediction_label_filter",
        )
    with filter_col2:
        kinds = st.multiselect(
            "Физический блок",
            options=sorted(filtered["kind"].unique().tolist()) if "kind" in filtered.columns else [],
            default=[],
            key="prediction_kind_filter",
        )
    with filter_col3:
        low_confidence_only = st.checkbox("Только низкая уверенность", key="prediction_low_confidence_only")

    if labels and "postprocessed_label" in filtered.columns:
        filtered = filtered[filtered["postprocessed_label"].isin(labels)]
    if kinds and "kind" in filtered.columns:
        filtered = filtered[filtered["kind"].isin(kinds)]
    if low_confidence_only and "low_confidence" in filtered.columns:
        filtered = filtered[filtered["low_confidence"] == True]
    return filtered


def render_artifact_download_card(title: str, description: str, path: Path, mime: str, key: str) -> None:
    """Render one artifact download card."""
    st.markdown(
        f"""
        <div class="artifact-card">
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
    st.caption(str(path))


def render_manual_decision_table(report_df: pd.DataFrame) -> pd.DataFrame:
    """Render manual decision support for uncertain blocks."""
    manual_df = report_df.copy()
    if "manual_review_required" not in manual_df.columns:
        st.info("Для этого запуска нет данных ручной проверки.")
        return pd.DataFrame()

    manual_df = manual_df[
        (manual_df["manual_review_required"] == True)
        | (manual_df.get("blocked_unsafe_autofix", False) == True)
    ].copy()
    if manual_df.empty:
        st.info("Нет спорных блоков, требующих ручного решения.")
        return pd.DataFrame()

    manual_df["apply_suggested_fix"] = False
    decision_columns = [
        column
        for column in [
            "apply_suggested_fix",
            "block_id",
            "label",
            "confidence_score",
            "blocked_unsafe_autofix",
            "suggested_fix",
            "suggested_rule_ids",
            "unsafe_auto_fix_reason",
            "recommendation",
            "text",
        ]
        if column in manual_df.columns
    ]
    edited_df = st.data_editor(
        manual_df[decision_columns],
        use_container_width=True,
        height=320,
        hide_index=True,
        disabled=[column for column in decision_columns if column != "apply_suggested_fix"],
        key="manual_decision_editor",
    )
    selected_df = edited_df[edited_df["apply_suggested_fix"] == True].copy()
    st.caption(f"Выбрано ручных решений: {len(selected_df)}")
    return selected_df


def render_results(result: ProcessingArtifacts) -> None:
    """Render the restored UI around current backend outputs."""
    summary = result.summary
    report_df = normalize_table_values(result.report_df)
    predictions_df = normalize_table_values(result.predictions_df)

    st.success("Документ обработан успешно.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Всего блоков", int(summary.get("blocks_total", 0)), "Извлеченные структурные элементы")
    with c2:
        render_metric_card("Ручная проверка", int(summary.get("review", 0)), "Низкая уверенность или спорный случай")
    with c3:
        render_metric_card("Предложить исправления", int(summary.get("changed", 0)), "Обнаружены параметры для правки")
    with c4:
        render_metric_card(
            "Заблокировано",
            int(summary.get("blocked_unsafe_autofix", 0)),
            "Небезопасные автоисправления не применены",
        )

    render_status_badges(summary)

    tab_overview, tab_predictions, tab_audit, tab_formatting, tab_artifacts = st.tabs(
        ["Обзор", "Предсказания", "Аудит", "Форматирование", "Артефакты"]
    )

    with tab_overview:
        left_col, right_col = st.columns([1.05, 1.35])
        with left_col:
            st.subheader("Сводка запуска")
            summary_view = {
                "input_docx": summary.get("input_docx"),
                "profile_name": summary.get("profile_name"),
                "model_type": summary.get("model_type"),
                "mode": summary.get("mode"),
                "blocks_total": summary.get("blocks_total"),
                "no_change": summary.get("no_change"),
                "review": summary.get("review"),
                "changed": summary.get("changed"),
                "error": summary.get("error"),
                "output_docx": summary.get("output_docx"),
            }
            st.json(summary_view)

        with right_col:
            st.subheader("Проблемные блоки")
            problematic_df = report_df[report_df["status"].isin(["review", "changed", "error"])] if "status" in report_df.columns else report_df
            overview_columns = [
                column
                for column in ["block_id", "label", "status", "violated_rules", "applied_fixes", "explanation", "text"]
                if column in problematic_df.columns
            ]
            st.dataframe(problematic_df[overview_columns], use_container_width=True, height=420)

    with tab_predictions:
        st.subheader("Предсказанные блоки")
        st.caption("Показаны типы блоков, уверенность модели и признаки списков.")
        filtered_predictions = filter_predictions_df(predictions_df)
        prediction_columns = [
            column
            for column in [
                "block_id",
                "kind",
                "list_type",
                "list_level",
                "predicted_label",
                "postprocessed_label",
                "confidence_score",
                "low_confidence",
                "text",
            ]
            if column in filtered_predictions.columns
        ]
        st.dataframe(filtered_predictions[prediction_columns], use_container_width=True, height=520)

    with tab_audit:
        st.subheader("Отчет аудита")
        st.caption("Фильтры применяются к проблемным блокам и полной таблице аудита.")
        filtered_audit = filter_audit_df(report_df)
        focused_columns = [
            column
            for column in [
                "block_id",
                "label",
                "status",
                "blocked_unsafe_autofix",
                "violated_rules",
                "suggested_fix",
                "applied_fixes",
                "explanation",
                "recommendation",
                "text",
            ]
            if column in filtered_audit.columns
        ]
        st.markdown("**Проблемные блоки**")
        focused_df = filtered_audit[filtered_audit["status"].isin(["review", "changed", "error"])] if "status" in filtered_audit.columns else filtered_audit
        st.dataframe(focused_df[focused_columns], use_container_width=True, height=280)
        st.markdown("**Полная таблица аудита**")
        st.dataframe(filtered_audit, use_container_width=True, height=320)

    with tab_formatting:
        st.subheader("Действия форматирования")
        st.caption("Объяснения по правилам и список безопасных исправлений.")
        st.markdown("**Ручные решения**")
        selected_manual_df = render_manual_decision_table(report_df)
        formatting_df = report_df.copy()
        if "status" in formatting_df.columns:
            formatting_df = formatting_df[formatting_df["status"].isin(["changed", "review", "error"])]
        formatting_columns = [
            column
            for column in [
                "block_id",
                "label",
                "status",
                "action",
                "blocked_unsafe_autofix",
                "manual_review_required",
                "violated_rules",
                "suggested_rule_ids",
                "applied_fixes",
                "suggested_fix",
                "changed_fields",
                "unsafe_auto_fix_reason",
                "reason",
                "explanation",
                "text",
            ]
            if column in formatting_df.columns
        ]
        st.dataframe(formatting_df[formatting_columns], use_container_width=True, height=520)
        if result.output_docx is not None and result.output_docx.exists():
            st.info(f"Исправленный DOCX сформирован: {result.output_docx.name}")
        else:
            st.info("В режиме аудита исправленный DOCX не создается.")

    with tab_artifacts:
        st.subheader("Артефакты")
        st.caption("Все файлы сформированы текущим pipeline и доступны для скачивания.")
        a1, a2, a3 = st.columns(3)
        with a1:
            render_artifact_download_card(
                title="Отчет аудита CSV",
                description="Таблица по блокам: статусы, нарушенные правила, исправления и объяснения.",
                path=result.report_csv,
                mime="text/csv",
                key="download_report_csv",
            )
        with a2:
            render_artifact_download_card(
                title="Отчет аудита JSON",
                description="Машиночитаемый экспорт результатов проверки.",
                path=result.report_json,
                mime="application/json",
                key="download_report_json",
            )
        with a3:
            render_artifact_download_card(
                title="Сводка",
                description="Краткое описание результатов текущей обработки.",
                path=result.summary_txt,
                mime="text/plain",
                key="download_summary_txt",
            )

        b1, b2, b3 = st.columns(3)
        with b1:
            render_artifact_download_card(
                title="Предсказания CSV",
                description="Предсказанные типы блоков, уверенность модели и признаки списков.",
                path=result.predictions_csv,
                mime="text/csv",
                key="download_predictions_csv",
            )
        with b2:
            render_artifact_download_card(
                title="Сводка JSON",
                description="Счетчики статусов и технические данные запуска.",
                path=result.summary_json,
                mime="application/json",
                key="download_summary_json",
            )
        with b3:
            if not selected_manual_df.empty:
                st.markdown(
                    """
                    <div class="artifact-card">
                        <h4>Ручные решения CSV</h4>
                        <p>Выбранные пользователем решения для спорных блоков.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.download_button(
                    "Скачать manual_decisions.csv",
                    data=selected_manual_df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="manual_decisions.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="download_manual_decisions_csv",
                )
            else:
                st.markdown(
                    """
                    <div class="artifact-card">
                        <h4>Ручные решения CSV</h4>
                        <p>Появится после выбора спорных блоков для ручной обработки.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        if result.output_docx is not None and result.output_docx.exists():
            st.markdown("---")
            render_artifact_download_card(
                title="Исправленный DOCX",
                description="Редактируемый DOCX, созданный после безопасных исправлений.",
                path=result.output_docx,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="download_output_docx",
            )


def run_processing(uploaded_file, selected_model_key: str, selected_mode: str, selected_profile_path: str) -> None:
    """Execute the backend processing pipeline and store the last result."""
    if uploaded_file is None:
        st.warning("Сначала загрузите DOCX-документ.")
        return

    if selected_model_key == "baseline_unavailable":
        st.error("Baseline-модель недоступна: в workspace нет сохраненного .joblib-артефакта.")
        return

    input_path = save_uploaded_bytes(uploaded_file.getvalue(), suffix=Path(uploaded_file.name).suffix)

    try:
        result = process_document(
            input_path=input_path,
            model_choice=selected_model_key,
            mode=selected_mode,
            profile_path=selected_profile_path,
        )
    except NotImplementedError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.exception(exc)
        return

    st.session_state["last_result"] = result
    st.session_state["last_uploaded_name"] = uploaded_file.name


def main() -> None:
    """Render the Streamlit application."""
    inject_page_styles()
    render_hero()

    profile_items = get_profile_options()
    if not profile_items:
        st.error("Профили ГОСТ не найдены в src/rules/profiles.")
        st.stop()

    st.session_state.setdefault("custom_profile_items", [])
    st.session_state.setdefault("methodical_profile_draft", None)
    st.session_state.setdefault("methodical_profile_source_name", "")
    st.session_state.setdefault("methodical_profile_source_type", "")
    custom_profile_items = st.session_state.get("custom_profile_items", [])
    all_profile_items = build_profile_options(profile_items, custom_profile_items)
    profile_label_to_path = {format_profile_option(item): item["path"] for item in all_profile_items}
    model_options = list_model_options()
    available_profile_ids = [item["profile_id"] for item in profile_items]

    with st.sidebar:
        st.header("Панель управления")
        st.caption("Выберите профиль проверки, при необходимости создайте локальный профиль из методички, затем загрузите DOCX-документ.")
        with st.expander("Методичка и локальный профиль", expanded=False):
            methodical_file = st.file_uploader(
                "Загрузите методичку для извлечения правил",
                type=SUPPORTED_METHODICAL_UPLOAD_TYPES,
                key="methodical_file_uploader",
            )
            methodical_profile_name = st.text_input(
                "Название локального профиля",
                value="",
                placeholder="Например: МИРЭА нормоконтроль",
                key="methodical_profile_name",
            )
            methodical_base_profiles = st.multiselect(
                "Базовые профили",
                options=available_profile_ids,
                default=["gost_7_32_2017", "gost_r_7_0_100_2018_bibliography"],
                key="methodical_base_profiles",
            )
            create_profile_clicked = st.button(
                "Извлечь правила",
                use_container_width=True,
                key="create_methodical_profile",
            )
            if create_profile_clicked:
                if methodical_file is None:
                    st.warning("Сначала загрузите PDF, DOCX, TXT или MD файл методички.")
                else:
                    try:
                        draft_profile = build_methodical_profile_draft(
                            uploaded_file=methodical_file,
                            profile_name=methodical_profile_name.strip(),
                            base_profile_ids=methodical_base_profiles,
                        )
                        _set_session_methodical_draft(
                            profile=draft_profile,
                            source_name=methodical_file.name,
                            source_type=methodical_file.type or "application/octet-stream",
                        )
                        st.success("Черновик профиля извлечен.")
                    except Exception as exc:
                        st.error(str(exc))

            draft_profile = _get_session_methodical_draft()
            if draft_profile is not None:
                st.markdown("**Черновик профиля**")
                st.caption(
                    f"Источник: {st.session_state.get('methodical_profile_source_name', 'неизвестно')} · "
                    f"confidence: {draft_profile.get('extraction_meta', {}).get('extraction_confidence', 'n/a')}"
                )
                draft_summary = {
                    "profile_id": draft_profile.get("profile_id"),
                    "profile_name": draft_profile.get("profile_name"),
                    "profile_type": draft_profile.get("profile_type"),
                    "base_profiles": draft_profile.get("base_profiles", []),
                    "needs_manual_review": draft_profile.get("extraction_meta", {}).get("needs_manual_review"),
                }
                st.json(draft_summary)
                with st.form("methodical_profile_editor", clear_on_submit=False):
                    edited_profile_name = st.text_input(
                        "Название профиля",
                        value=str(draft_profile.get("profile_name", "")),
                    )
                    edited_base_profiles = st.multiselect(
                        "Базовые профили",
                        options=available_profile_ids,
                        default=[item for item in draft_profile.get("base_profiles", []) if item in available_profile_ids],
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        margin_left_cm = st.number_input(
                            "Левое поле, см",
                            min_value=0.0,
                            max_value=10.0,
                            value=float(draft_profile.get("document_rules", {}).get("page", {}).get("margin_left_cm", 3.0)),
                            step=0.1,
                        )
                        margin_right_cm = st.number_input(
                            "Правое поле, см",
                            min_value=0.0,
                            max_value=10.0,
                            value=float(draft_profile.get("document_rules", {}).get("page", {}).get("margin_right_cm", 1.0)),
                            step=0.1,
                        )
                        margin_top_cm = st.number_input(
                            "Верхнее поле, см",
                            min_value=0.0,
                            max_value=10.0,
                            value=float(draft_profile.get("document_rules", {}).get("page", {}).get("margin_top_cm", 2.0)),
                            step=0.1,
                        )
                        margin_bottom_cm = st.number_input(
                            "Нижнее поле, см",
                            min_value=0.0,
                            max_value=10.0,
                            value=float(draft_profile.get("document_rules", {}).get("page", {}).get("margin_bottom_cm", 2.0)),
                            step=0.1,
                        )
                        font_name = st.text_input(
                            "Шрифт",
                            value=str(draft_profile.get("document_rules", {}).get("default_font", {}).get("font_name", "Times New Roman")),
                        )
                        font_size_pt = st.number_input(
                            "Размер шрифта, pt",
                            min_value=8.0,
                            max_value=24.0,
                            value=float(draft_profile.get("document_rules", {}).get("default_font", {}).get("font_size_pt", 14.0)),
                            step=1.0,
                        )
                        default_line_spacing = st.number_input(
                            "Интервал по умолчанию",
                            min_value=1.0,
                            max_value=2.5,
                            value=float(draft_profile.get("document_rules", {}).get("default_line_spacing", 1.5)),
                            step=0.1,
                        )
                    with c2:
                        body_first_line_indent_cm = st.number_input(
                            "Абзацный отступ body_text, см",
                            min_value=0.0,
                            max_value=3.0,
                            value=float(draft_profile.get("labels", {}).get("body_text", {}).get("style_profile", {}).get("first_line_indent_cm", 1.25)),
                            step=0.05,
                        )
                        body_line_spacing = st.number_input(
                            "Интервал body_text",
                            min_value=1.0,
                            max_value=2.5,
                            value=float(draft_profile.get("labels", {}).get("body_text", {}).get("style_profile", {}).get("line_spacing", 1.5)),
                            step=0.1,
                        )
                        title_left_indent_cm = st.number_input(
                            "Отступ title_section слева, см",
                            min_value=0.0,
                            max_value=3.0,
                            value=float(draft_profile.get("labels", {}).get("title_section", {}).get("style_profile", {}).get("left_indent_cm", 1.25)),
                            step=0.05,
                        )
                        title_font_size_pt = st.number_input(
                            "Размер title_section, pt",
                            min_value=10.0,
                            max_value=24.0,
                            value=float(draft_profile.get("labels", {}).get("title_section", {}).get("style_profile", {}).get("font_size_pt", 18.0)),
                            step=1.0,
                        )
                        title_space_after_pt = st.number_input(
                            "Интервал после title_section, pt",
                            min_value=0.0,
                            max_value=24.0,
                            value=float(draft_profile.get("labels", {}).get("title_section", {}).get("style_profile", {}).get("space_after_pt", 10.0)),
                            step=1.0,
                        )
                        title_bold = st.checkbox(
                            "title_section жирный",
                            value=bool(draft_profile.get("labels", {}).get("title_section", {}).get("style_profile", {}).get("bold", True)),
                        )
                        list_left_indent_cm = st.number_input(
                            "Отступ list_item слева, см",
                            min_value=0.0,
                            max_value=3.0,
                            value=float(draft_profile.get("labels", {}).get("list_item", {}).get("style_profile", {}).get("left_indent_cm", 1.25)),
                            step=0.05,
                        )
                        list_line_spacing = st.number_input(
                            "Интервал list_item",
                            min_value=1.0,
                            max_value=2.5,
                            value=float(draft_profile.get("labels", {}).get("list_item", {}).get("style_profile", {}).get("line_spacing", 1.5)),
                            step=0.1,
                        )
                        figure_alignment = st.selectbox(
                            "Выравнивание figure_caption",
                            options=["LEFT", "CENTER", "RIGHT", "JUSTIFY"],
                            index=["LEFT", "CENTER", "RIGHT", "JUSTIFY"].index(
                                str(draft_profile.get("labels", {}).get("figure_caption", {}).get("style_profile", {}).get("alignment", "CENTER"))
                            ),
                        )
                        figure_font_size_pt = st.number_input(
                            "Размер figure_caption, pt",
                            min_value=8.0,
                            max_value=24.0,
                            value=float(draft_profile.get("labels", {}).get("figure_caption", {}).get("style_profile", {}).get("font_size_pt", 12.0)),
                            step=1.0,
                        )
                        bibliography_title_left_indent_cm = st.number_input(
                            "Отступ bibliography_title слева, см",
                            min_value=0.0,
                            max_value=3.0,
                            value=float(draft_profile.get("labels", {}).get("bibliography_title", {}).get("style_profile", {}).get("left_indent_cm", 1.25)),
                            step=0.05,
                        )
                        bibliography_title_font_size_pt = st.number_input(
                            "Размер bibliography_title, pt",
                            min_value=8.0,
                            max_value=24.0,
                            value=float(draft_profile.get("labels", {}).get("bibliography_title", {}).get("style_profile", {}).get("font_size_pt", 14.0)),
                            step=1.0,
                        )

                    st.markdown("**Структурные правила**")
                    title_section_numbering_enabled = st.checkbox(
                        "Нумерация для title_section",
                        value=bool(draft_profile.get("numbering_rules", {}).get("title_section", {}).get("enabled", True)),
                    )
                    title_section_numbering_pattern = st.text_input(
                        "Шаблон title_section",
                        value=str(draft_profile.get("numbering_rules", {}).get("title_section", {}).get("pattern", r"^\d+\s+.+$")),
                    )
                    title_subsection_numbering_enabled = st.checkbox(
                        "Нумерация для title_subsection",
                        value=bool(draft_profile.get("numbering_rules", {}).get("title_subsection", {}).get("enabled", True)),
                    )
                    title_subsection_numbering_pattern = st.text_input(
                        "Шаблон title_subsection",
                        value=str(draft_profile.get("numbering_rules", {}).get("title_subsection", {}).get("pattern", r"^\d+\.\d+\s+.+$")),
                    )
                    unnumbered_sections = st.text_area(
                        "Секции без нумерации",
                        value="\n".join(draft_profile.get("numbering_rules", {}).get("unnumbered_sections", [])),
                        height=120,
                    )
                    bibliography_enabled = st.checkbox(
                        "Включить bibliography_rules",
                        value=bool(draft_profile.get("bibliography_rules", {}).get("enabled", True)),
                    )
                    bibliography_separate_profile_required = st.checkbox(
                        "Требуется отдельный профиль библиографии",
                        value=bool(draft_profile.get("bibliography_rules", {}).get("separate_profile_required", False)),
                    )
                    bibliography_require_url = st.checkbox(
                        "Требовать URL для web_resource",
                        value=bool(draft_profile.get("bibliography_rules", {}).get("general", {}).get("require_url_for_web_resource", True)),
                    )
                    bibliography_soft_features = draft_profile.get("bibliography_rules", {}).get("soft_features", {})
                    st.markdown("**Мягкие признаки библиографии**")
                    bibliography_book_markers = st.text_area(
                        "book_markers",
                        value="\n".join(bibliography_soft_features.get("book_markers", [])),
                        height=90,
                    )
                    bibliography_journal_markers = st.text_area(
                        "journal_markers",
                        value="\n".join(bibliography_soft_features.get("journal_markers", [])),
                        height=90,
                    )
                    bibliography_web_markers = st.text_area(
                        "web_markers",
                        value="\n".join(bibliography_soft_features.get("web_markers", [])),
                        height=90,
                    )
                    bibliography_standard_markers = st.text_area(
                        "standard_markers",
                        value="\n".join(bibliography_soft_features.get("standard_markers", [])),
                        height=90,
                    )
                    bibliography_entry_patterns = draft_profile.get("bibliography_rules", {}).get("entry_patterns", {})
                    st.markdown("**Шаблоны библиографических описаний**")
                    bibliography_book_patterns = st.text_area(
                        "book",
                        value="\n".join(bibliography_entry_patterns.get("book", [])),
                        height=90,
                    )
                    bibliography_journal_patterns = st.text_area(
                        "journal_article",
                        value="\n".join(bibliography_entry_patterns.get("journal_article", [])),
                        height=90,
                    )
                    bibliography_web_patterns = st.text_area(
                        "web_resource",
                        value="\n".join(bibliography_entry_patterns.get("web_resource", [])),
                        height=90,
                    )
                    bibliography_standard_patterns = st.text_area(
                        "standard",
                        value="\n".join(bibliography_entry_patterns.get("standard", [])),
                        height=90,
                    )
                    bibliography_law_patterns = st.text_area(
                        "law",
                        value="\n".join(bibliography_entry_patterns.get("law", [])),
                        height=90,
                    )
                    bibliography_thesis_patterns = st.text_area(
                        "thesis",
                        value="\n".join(bibliography_entry_patterns.get("thesis", [])),
                        height=90,
                    )
                    nn_expected_bibliography_keywords = st.text_area(
                        "expected_bibliography_keywords",
                        value="\n".join(draft_profile.get("nn_context", {}).get("expected_bibliography_keywords", [])),
                        height=90,
                    )
                    citation_enabled = st.checkbox(
                        "Включить citation_rules",
                        value=bool(draft_profile.get("citation_rules", {}).get("enabled", True)),
                    )
                    citation_patterns_value = draft_profile.get("citation_rules", {}).get("in_text_reference_patterns", [])
                    if not citation_patterns_value:
                        single_citation_pattern = draft_profile.get("citation_rules", {}).get("in_text_reference_pattern", "")
                        citation_patterns_value = [single_citation_pattern] if single_citation_pattern else []
                    citation_patterns = st.text_area(
                        "Шаблоны ссылок в тексте",
                        value="\n".join(str(item) for item in citation_patterns_value if str(item).strip()),
                        height=120,
                    )
                    save_profile_clicked = st.form_submit_button("Сохранить профиль")
                    if save_profile_clicked:
                        try:
                            citation_patterns_list = [
                                line.strip()
                                for line in str(citation_patterns).splitlines()
                                if line.strip()
                            ]
                            edited_profile = _apply_methodical_form_edits(
                                draft_profile,
                                {
                                    "profile_name": edited_profile_name,
                                    "base_profiles": edited_base_profiles,
                                    "margin_left_cm": margin_left_cm,
                                    "margin_right_cm": margin_right_cm,
                                    "margin_top_cm": margin_top_cm,
                                    "margin_bottom_cm": margin_bottom_cm,
                                    "font_name": font_name,
                                    "font_size_pt": font_size_pt,
                                    "default_line_spacing": default_line_spacing,
                                    "body_first_line_indent_cm": body_first_line_indent_cm,
                                    "body_line_spacing": body_line_spacing,
                                    "title_left_indent_cm": title_left_indent_cm,
                                    "title_font_size_pt": title_font_size_pt,
                                    "title_space_after_pt": title_space_after_pt,
                                    "title_bold": title_bold,
                                    "list_left_indent_cm": list_left_indent_cm,
                                    "list_line_spacing": list_line_spacing,
                                    "figure_alignment": figure_alignment,
                                    "figure_font_size_pt": figure_font_size_pt,
                                    "bibliography_title_left_indent_cm": bibliography_title_left_indent_cm,
                                    "bibliography_title_font_size_pt": bibliography_title_font_size_pt,
                                    "title_section_numbering_enabled": title_section_numbering_enabled,
                                    "title_section_numbering_pattern": title_section_numbering_pattern,
                                    "title_subsection_numbering_enabled": title_subsection_numbering_enabled,
                                    "title_subsection_numbering_pattern": title_subsection_numbering_pattern,
                                    "unnumbered_sections": unnumbered_sections,
                                    "bibliography_enabled": bibliography_enabled,
                                    "bibliography_separate_profile_required": bibliography_separate_profile_required,
                                    "bibliography_require_url": bibliography_require_url,
                                    "bibliography_book_markers": bibliography_book_markers,
                                    "bibliography_journal_markers": bibliography_journal_markers,
                                    "bibliography_web_markers": bibliography_web_markers,
                                    "bibliography_standard_markers": bibliography_standard_markers,
                                    "bibliography_book_patterns": bibliography_book_patterns,
                                    "bibliography_journal_patterns": bibliography_journal_patterns,
                                    "bibliography_web_patterns": bibliography_web_patterns,
                                    "bibliography_standard_patterns": bibliography_standard_patterns,
                                    "bibliography_law_patterns": bibliography_law_patterns,
                                    "bibliography_thesis_patterns": bibliography_thesis_patterns,
                                    "nn_expected_bibliography_keywords": nn_expected_bibliography_keywords,
                                    "citation_enabled": citation_enabled,
                                    "citation_patterns": citation_patterns_list,
                                },
                            )
                            custom_profile = persist_custom_profile(edited_profile)
                            st.session_state["custom_profile_items"] = [
                                *st.session_state.get("custom_profile_items", []),
                                custom_profile,
                            ]
                            st.session_state["methodical_profile_draft"] = edited_profile
                            st.success(f"Профиль сохранен: {custom_profile['profile_name']}")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
        uploaded_file = st.file_uploader("Загрузите DOCX-документ для проверки", type=SUPPORTED_UPLOAD_TYPES)
        selected_model_key = st.selectbox(
            "Модель",
            options=list(model_options.keys()),
            format_func=lambda key: {
                "baseline": "SVM baseline",
                "transformer": "Transformer",
                "baseline_unavailable": "Baseline недоступен",
            }.get(key, model_options[key]),
        )
        selected_mode = st.radio(
            "Режим",
            options=["audit", "fix"],
            format_func=lambda value: "Только аудит" if value == "audit" else "Аудит и безопасное форматирование",
        )
        selected_profile_label = st.selectbox(
            "Профиль ГОСТ",
            options=list(profile_label_to_path.keys()),
            key="profile_selectbox",
        )
        process_clicked = st.button("Запустить анализ документа", type="primary", use_container_width=True)
        st.markdown("---")
        st.caption("Поддерживаемый формат MVP: DOCX.")

    if process_clicked:
        selected_profile_path = profile_label_to_path[selected_profile_label]
        run_processing(
            uploaded_file=uploaded_file,
            selected_model_key=selected_model_key,
            selected_mode=selected_mode,
            selected_profile_path=selected_profile_path,
        )

    result = st.session_state.get("last_result")
    if result is None:
        st.info("Загрузите документ и запустите анализ, чтобы увидеть сводку, аудит и артефакты.")
        return

    current_upload = st.session_state.get("last_uploaded_name", result.input_path.name)
    st.caption(f"Последний запуск: {current_upload}")
    render_results(result)


if __name__ == "__main__":
    main()
