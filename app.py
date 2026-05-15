from __future__ import annotations

import zipfile
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
from src.inference.run_log import RunLog
# methodical_extractor imports (build_methodical_profile, extract_text_from_file,
# save_methodical_profile) will be re-added by 06-04 when the methodical modal
# lands. Removed here per CLAUDE.md «Удаляй orphans» since the sidebar form
# that consumed them is deleted in this plan.

SUPPORTED_UPLOAD_TYPES = ["docx"]
SUPPORTED_METHODICAL_UPLOAD_TYPES = ["pdf", "docx", "txt", "md"]
CUSTOM_PROFILES_DIR = Path("results/generated_profiles")

# STATUS_CHIP: maps the 5 Phase 6 block statuses to (icon, Russian-label, badge-css-class).
# NOTE per 06-PATTERNS.md §"CRITICAL FINDING: report_df schema": `blocked_unsafe_autofix`
# is a separate boolean column in report_df, not a `status` value. The key here is used
# only for display when that boolean is True.
STATUS_CHIP: dict[str, tuple[str, str, str]] = {
    "no_change":              ("●",  "Без изменений",                                "badge-ok"),
    "changed":                ("✏️", "Изменено",                                     "badge-change"),
    "review":                 ("⚠️", "Требует проверки",                             "badge-warn"),
    "error":                  ("✗",  "Ошибка",                                       "badge-error"),
    "blocked_unsafe_autofix": ("🛑", "Небезопасное автоисправление заблокировано",   "badge-muted"),
}


def modal_reason_is_valid(reason: str) -> bool:
    """D-004 / T-05-01: reason must be ≥ 8 non-whitespace chars after strip."""
    return len(reason.strip()) >= 8


def preflight_translate_error(exc: Exception) -> str:
    """Translate a backend exception into a fixed Russian user-message.

    Returns ONLY one of 5 fixed strings — never str(exc) (PII boundary per
    06-UI-SPEC §Error state copy + 06-RESEARCH.md §5).
    """
    if isinstance(exc, (FileNotFoundError, zipfile.BadZipFile)):
        return (
            "Файл не читается. Проверьте, что это валидный DOCX (.docx, ZIP-архив). "
            "Откройте файл в Word и пересохраните, если нужно."
        )
    if isinstance(exc, NotImplementedError):
        return "PDF аудит ещё не поддерживается в этой версии."
    if isinstance(exc, ValueError):
        msg = str(exc)
        if "extractable non-empty blocks" in msg:
            return "В документе нет извлекаемых непустых блоков. Проверьте, что документ содержит текст."
        if "Unsupported input format" in msg or "Only DOCX is currently supported" in msg:
            return "Расширение файла `.docx`, но содержимое не соответствует DOCX-формату."
        return "Не удалось обработать документ. См. журнал запуска."
    return "Не удалось обработать документ. См. журнал запуска."

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
    """Execute the backend processing pipeline and store the last result.

    Wires `RunLog` (06-01) for the 4 pipeline stages and translates backend
    exceptions through `preflight_translate_error` so no traceback / no
    document text reaches the UI surface (D-04 PII boundary).
    """
    if uploaded_file is None:
        st.warning("Сначала загрузите DOCX-документ.")
        return

    if selected_model_key == "baseline_unavailable":
        st.error("Baseline-модель недоступна: в workspace нет сохраненного .joblib-артефакта.")
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
    except (FileNotFoundError, NotImplementedError, ValueError, zipfile.BadZipFile) as exc:
        user_msg = preflight_translate_error(exc)
        run_log.record(
            "document-read",
            "error",
            error_class=type(exc).__name__,
            error_message=user_msg,
        )
        st.error(user_msg)
        st.session_state["last_run_log"] = run_log
        st.session_state["last_uploaded_name"] = uploaded_file.name
        return
    except Exception as exc:
        run_log.record(
            "rule-apply",
            "error",
            error_class=type(exc).__name__,
            error_message="Не удалось обработать документ.",
        )
        st.error("Не удалось обработать документ: " + type(exc).__name__)
        st.session_state["last_run_log"] = run_log
        st.session_state["last_uploaded_name"] = uploaded_file.name
        return

    run_log.record("classification", "ok")
    run_log.record("rule-apply", "ok")
    run_log.record("save", "ok")

    st.session_state["last_result"] = result
    st.session_state["last_uploaded_name"] = uploaded_file.name
    st.session_state["last_run_log"] = run_log


def main() -> None:
    """Render the Streamlit application — D-01 sidebar (config) + main pane (report).

    Sidebar holds: profile picker (key='profile_selectbox' is the modal-close
    anchor for 06-04), modal trigger placeholder (06-04 swaps the body),
    model + mode selectors, DOCX uploader (key='docx_uploader'), primary
    «Запустить аудит» button (key='run_audit_button'). Main pane shows the
    interim empty state (06-03 replaces with render_report) or — when a
    result exists — delegates to legacy render_results for the time being.
    """
    inject_page_styles()

    profile_items = get_profile_options()
    if not profile_items:
        st.error("Профили ГОСТ не найдены в src/rules/profiles.")
        st.stop()

    st.session_state.setdefault("custom_profile_items", [])
    st.session_state.setdefault("last_run_log", None)
    st.session_state.setdefault("modal_diff_lines", None)
    st.session_state.setdefault("modal_draft_profile", None)
    custom_profile_items = st.session_state.get("custom_profile_items", [])
    all_profile_items = build_profile_options(profile_items, custom_profile_items)
    profile_label_to_path = {format_profile_option(item): item["path"] for item in all_profile_items}
    model_options = list_model_options()

    with st.sidebar:
        st.header("Панель управления")
        st.caption("Выберите профиль ГОСТ, загрузите DOCX-документ и запустите аудит.")
        selected_profile_label = st.selectbox(
            "Профиль ГОСТ",
            options=list(profile_label_to_path.keys()),
            key="profile_selectbox",
        )
        open_modal_clicked = st.button(
            "+ Создать профиль из методички",
            key="open_methodical_modal",
            use_container_width=True,
        )
        if open_modal_clicked:
            # Placeholder — 06-04 replaces this body with the methodical st.dialog call.
            st.info("Модал создания профиля из методички будет доступен после плана 06-04.")
        model_key = st.selectbox(
            "Модель",
            options=list(model_options.keys()),
            format_func=lambda k: model_options.get(k, k),
            key="model_selectbox",
        )
        mode_key = st.radio(
            "Режим",
            options=["audit", "fix"],
            format_func=lambda k: "Только аудит" if k == "audit" else "Применить безопасные исправления",
            key="mode_radio",
        )
        uploaded_file = st.file_uploader(
            "Загрузите DOCX",
            type=SUPPORTED_UPLOAD_TYPES,
            key="docx_uploader",
        )
        run_disabled = uploaded_file is None or selected_profile_label is None
        run_clicked = st.button(
            "Запустить аудит",
            type="primary",
            disabled=run_disabled,
            use_container_width=True,
            key="run_audit_button",
        )

    if run_clicked and not run_disabled:
        selected_profile_path = profile_label_to_path[selected_profile_label]
        with st.spinner("Идёт аудит документа..."):
            run_processing(
                uploaded_file=uploaded_file,
                selected_model_key=model_key,
                selected_mode=mode_key,
                selected_profile_path=selected_profile_path,
            )

    result = st.session_state.get("last_result")
    if result is None:
        st.info("Загрузите DOCX-документ, чтобы начать аудит")
        st.caption(
            "В левой панели выберите профиль ГОСТ и загрузите файл. "
            "После запуска аудита здесь появятся счётчики и блоки."
        )
        return

    # Interim: 06-03 replaces this with render_report(result).
    render_results(result)


if __name__ == "__main__":
    main()
