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
from src.inference.run_log import RunLog
from src.rules.methodical_extractor import build_methodical_profile, save_methodical_profile
from src.rules.profile_diff import compute_profile_diff
from src.rules.profile_loader import PROFILES_DIR, list_available_profiles, load_profile

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
    """D-004 / T-05-01: reason must be ≥8 chars after strip AND contain at
    least one printable non-whitespace character. Mirrors the CLI predicate
    in src/main.py:367-374 verbatim — UI must not accept what CLI rejects."""
    stripped = (reason or "").strip()
    if len(stripped) < 8:
        return False
    return any(c.isprintable() and not c.isspace() for c in stripped)


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


def render_summary_counters(summary: dict[str, Any]) -> None:
    """Render the 6-cell st.metric strip above the grouped sections (UI-SPEC §Summary counters)."""
    cols = st.columns(6)
    metrics = [
        ("Всего блоков",                int(summary.get("blocks_total", 0) or 0)),
        ("Без изменений",               int(summary.get("no_change", 0) or 0)),
        ("Изменены",                    int(summary.get("changed", 0) or 0)),
        ("Требуют проверки",            int(summary.get("review", 0) or 0)),
        ("Ошибки",                      int(summary.get("error", 0) or 0)),
        ("Небезопасно (заблокировано)", int(summary.get("blocked_unsafe_autofix", 0) or 0)),
    ]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)


def _has(value: Any) -> bool:
    """Tolerant non-empty check used by render_block_section to gate optional fields."""
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    s = str(value).strip()
    return bool(s) and s.lower() != "nan"


def render_block_section(title: str, df: pd.DataFrame, expanded_by_default: bool) -> None:
    """Render one grouped section as a per-row st.expander loop (UI-SPEC §Block table widget)."""
    if df.empty:
        return
    st.subheader(f"{title} ({len(df)})")
    for _, row in df.iterrows():
        if bool(row.get("blocked_unsafe_autofix", False)) is True:
            icon, label, _ = STATUS_CHIP["blocked_unsafe_autofix"]
        else:
            key = str(row.get("status", ""))
            icon, label, _ = STATUS_CHIP.get(key, ("?", key or "—", "badge-neutral"))

        conf = row.get("confidence_score")
        if _has(conf):
            try:
                conf_str = f"{float(conf):.2f}"  # type: ignore[arg-type]
            except (TypeError, ValueError):
                conf_str = "—"
        else:
            conf_str = "—"

        header = (
            f"{icon} {row.get('block_id', '?')} · {row.get('label', '')} · "
            f"{label} · уверенность {conf_str}"
        )
        with st.expander(header, expanded=expanded_by_default):
            if _has(row.get("text")):
                st.markdown("**Оригинальный текст блока**")
                st.code(str(row["text"]), language=None)
            if _has(row.get("explanation")):
                st.markdown("**Причина ручной проверки**")
                st.write(str(row["explanation"]))
            if _has(row.get("violated_rules")):
                st.markdown("**Нарушенные правила**")
                st.write(str(row["violated_rules"]))
            if _has(row.get("applied_fixes")):
                st.markdown("**Применённые исправления**")
                st.write(str(row["applied_fixes"]))
            if bool(row.get("blocked_unsafe_autofix", False)) and _has(row.get("unsafe_auto_fix_reason")):
                st.markdown("**Заблокированное автоисправление**")
                st.write(str(row["unsafe_auto_fix_reason"]))
            if str(row.get("status", "")) == "error":
                st.markdown("**Сообщение об ошибке**")
                st.write(str(row.get("explanation") or "Внутренняя ошибка правила. См. журнал запуска."))


def render_report(result: ProcessingArtifacts) -> None:
    """Render the linear main-pane report (06-UI-SPEC §Section headings 1-6).

    Sections:
      1. Report header («Отчёт по документу: {filename}» + profile sub-line)
      2. Summary counters (6-cell st.metric strip)
      3. «Требуют внимания» (expanded) — review + error + blocked_unsafe_autofix
      4. «Изменены» (collapsed) — changed & not blocked
      5. «Без изменений» (collapsed) — no_change
      6. «Скачать результаты» — report CSV + summary JSON + corrected DOCX
         + run-log JSON (D-04)
    """
    # 1. Report header.
    filename = Path(result.input_path).name
    profile_name = result.summary.get("profile_name", "—")
    profile_id = result.summary.get("profile_id") or Path(result.profile_path).stem
    st.subheader(f"Отчёт по документу: {filename}")
    st.caption(f"Профиль: {profile_name} ({profile_id})")

    # 2. Summary counters.
    render_summary_counters(result.summary)

    # 3. Group-split report_df.
    df = normalize_table_values(result.report_df)
    if "blocked_unsafe_autofix" not in df.columns:
        df = df.assign(blocked_unsafe_autofix=False)
    blocked_mask = df["blocked_unsafe_autofix"].astype(bool)
    attention_mask = df["status"].isin(["review", "error"]) | blocked_mask
    df_attention = pd.DataFrame(df[attention_mask])
    df_changed = pd.DataFrame(df[(df["status"] == "changed") & ~blocked_mask])
    df_ok = pd.DataFrame(df[df["status"] == "no_change"])

    # 4. Render groups in order.
    if df_attention.empty:
        st.subheader("Требуют внимания (0)")
        st.info("Документ соответствует профилю — блоков, требующих внимания, нет.")
    else:
        render_block_section("Требуют внимания", df_attention, expanded_by_default=True)
    render_block_section("Изменены", df_changed, expanded_by_default=False)
    render_block_section("Без изменений", df_ok, expanded_by_default=False)

    # 5. Downloads section.
    st.subheader("Скачать результаты")
    render_artifact_download_card(
        title="Отчёт CSV",
        description="Таблица по блокам: статусы, нарушенные правила, исправления, объяснения.",
        path=result.report_csv,
        mime="text/csv",
        key="download_report_csv",
    )
    render_artifact_download_card(
        title="Сводка JSON",
        description="Счётчики статусов и технические данные запуска.",
        path=result.summary_json,
        mime="application/json",
        key="download_summary_json",
    )
    if result.output_docx is not None and result.output_docx.exists():
        render_artifact_download_card(
            title="Исправленный DOCX",
            description="Редактируемый DOCX, созданный после безопасных исправлений.",
            path=result.output_docx,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="download_output_docx",
        )

    # 6. Run-log JSON download (D-04).
    run_log: RunLog | None = st.session_state.get("last_run_log")
    if run_log is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = Path(result.input_path).stem
        log_path = REPORTS_DIR / f"{stem}_run_log_{timestamp}.json"
        run_log.dump_json(log_path)
        st.download_button(
            "Скачать журнал запуска (JSON)",
            data=log_path.read_bytes(),
            file_name=log_path.name,
            mime="application/json",
            use_container_width=True,
            key="download_run_log",
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


@st.dialog("Создать профиль из методички", width="large")
def methodical_modal(available_profile_ids: list[str]) -> None:
    """Methodical-profile-extraction modal mirroring Phase 5 CLI contract.

    Mirrors `cmd_extract_methodical_profile`: dry-run preview by default,
    «Применить и сохранить» = `--apply`, collision branch requires both the
    overwrite checkbox AND a reason ≥ 8 non-whitespace chars after strip
    (D-004 «no silent rewrites» / T-05-01 client-side enforcement).
    """
    # Step 1 — file uploader.
    uploaded = st.file_uploader(
        "Загрузите методичку",
        type=SUPPORTED_METHODICAL_UPLOAD_TYPES,
        key="modal_methodical_file",
    )
    # Step 2 — base-profile multiselect.
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
    # Step 3 — preview.
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

    # Step 4 — render diff + apply branch (no-collision OR collision/force-reason).
    diff = st.session_state.get("modal_diff_lines")
    draft = st.session_state.get("modal_draft_profile")
    if diff is not None and draft is not None:
        st.code("\n".join(diff), language=None)
        profile_id = draft["profile_id"]
        target_paths = [
            PROFILES_DIR / f"{profile_id}.json",
            CUSTOM_PROFILES_DIR / f"{profile_id}.json",
        ]
        target_exists = any(p.exists() for p in target_paths)
        if not target_exists:
            apply_clicked = st.button(
                "Применить и сохранить",
                type="primary",
                key="modal_apply_button",
            )
            if apply_clicked:
                CUSTOM_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
                save_methodical_profile(draft, CUSTOM_PROFILES_DIR)
                # Pitfall 4: sidebar selectbox stores the FORMATTED label, not the
                # raw profile_id. Compute the formatted label for the new item.
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

    # Cancel — clear modal state and dismiss.
    cancel_clicked = st.button("Отмена", key="modal_cancel_button")
    if cancel_clicked:
        for k in ("modal_diff_lines", "modal_draft_profile"):
            st.session_state.pop(k, None)
        st.rerun()


def main() -> None:
    """Render the Streamlit application — D-01 sidebar (config) + main pane (report).

    Sidebar holds: profile picker (key='profile_selectbox' is the modal-close
    anchor for 06-04), modal trigger placeholder (06-04 swaps the body),
    model + mode selectors, DOCX uploader (key='docx_uploader'), primary
    «Запустить аудит» button (key='run_audit_button'). Main pane shows the
    empty state when no result is in session_state, otherwise delegates to
    `render_report` for the linear D-02 report composition.
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
    available_profile_ids = [str(item["profile_id"]) for item in all_profile_items if item.get("profile_id")]
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
            st.session_state["methodical_modal_request"] = True
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

    if st.session_state.pop("methodical_modal_request", False):
        methodical_modal(available_profile_ids)

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

    render_report(result)


if __name__ == "__main__":
    main()
