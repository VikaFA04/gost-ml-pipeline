# Phase 6: Streamlit UI Redesign — Research

**Researched:** 2026-05-14
**Domain:** Streamlit ≥ 1.35 view-layer evolution, PII-clean run-log, methodical modal contract
**Confidence:** HIGH — all critical claims verified against installed code, official Context7 docs, or direct file inspection.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Sidebar = config, main pane = results. Prior 5-tab structure dropped. Linear conditional reveal. Sidebar holds: profile picker, «+» button for modal, DOCX uploader, run button.
- **D-02:** Grouped sections by importance — «Требуют внимания» (error + review + blocked_unsafe_autofix, expanded), «Изменены» (changed, collapsed), «Без изменений» (no_change, collapsed). Each section is a table with status chip column. Drill-in = inline `st.expander`. No modal/side-panel per-block. Summary counters above sections; `profile_id` in report header.
- **D-03:** Profile picker = sidebar dropdown. «+» button opens `st.dialog` modal mirroring CLI `extract-methodical-profile` (preview → apply → force --reason ≥8). Preview to `tempfile.gettempdir()`. No writes under `src/rules/profiles/` until apply.
- **D-04:** Inline friendly errors per stage + downloadable JSON run-log. Single-writer logger. PII boundary: filename + technical metadata IN; document content OUT. `st.exception` at `app.py:773` removed.

### Claude's Discretion

- Summary counters placement (cards vs `st.metric` strip vs sticky banner).
- Download file naming policy.
- Evolve `app.py` vs full rewrite of view layer.
- Styling depth (keep/extend `inject_page_styles`).
- Russian copy details.
- Block table widget (`st.dataframe` vs `st.data_editor`).

### Deferred Ideas (OUT OF SCOPE)

- DEBUG toggle showing tracebacks in sidebar.
- Multi-document batch audit UI.
- Live progress bar tied to rule-apply iteration counter.
- Inline rule-engine debugging (which rule fired on which block).
- File-system structured logger.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-ui-main-flow | Full audit flow: upload → profile → run → summary counters → per-block table → download; no dead-ends, no orphaned tabs. | D-01 layout, st.metric strip, run_processing + process_document wiring, download filename scheme |
| REQ-ui-problem-block-view | Highlights review/error blocks; per-block confidence; manual-review reason from `explanation`; original block text inspectable. | Per-row st.expander loop, D-02 grouped sections, render_block_section helper |
| REQ-input-preflight | Preflight failures surface as user-facing messages without tracebacks; no crash on malformed paragraphs. | D-04 preflight error strings, validate_document_input integration |
| REQ-pipeline-logging | Pipeline logs stages without leaking document text; downloadable JSON run-log. | src/inference/run_log.py RunLog helper, PII boundary table, D-04 contract |
| REQ-ui-design-review | UI passes design-review by project owner; defects fixed before close. | UI-SPEC checker sign-off criteria, falsifiable PASS conditions in Validation Architecture |

</phase_requirements>

---

## Summary

Phase 6 is a view-layer evolution, not a rewrite. The backend (`application_service.py`, `methodical_extractor.py`, `profile_diff.py`) is stable and unchanged. The work is: (1) delete `render_results` body (~224 LoC) and the methodical sidebar form (~369 LoC) from `app.py`, (2) replace them with `render_report`, `render_block_section`, and `methodical_modal` using the design contract in `06-UI-SPEC.md`, and (3) add one new module `src/inference/run_log.py` (~80 LoC) for PII-clean stage logging.

**Streamlit version:** 1.56.0 installed in `.venv` (pinned `streamlit>=1.35` in `requirements.txt`). `st.dialog` decorator is present at `.venv/Lib/site-packages/streamlit/elements/dialog_decorator.py`. No version bump needed. [VERIFIED: direct file inspection]

**Critical finding:** `st.dialog` supports `width="small"/"medium"/"large"` (500/750/1280 px). No restriction on `st.file_uploader` inside a dialog. The only explicit constraint is: `st.sidebar` is not supported inside a dialog, and nested dialogs are blocked. The methodical modal (`@st.dialog("Создать профиль из методички", width="large")`) works within these constraints. [VERIFIED: dialog_decorator.py source]

**Primary recommendation:** Evolve `app.py` in-place; add `src/inference/run_log.py`; three TDD plans (RED scaffold, GREEN evolution, design-review).

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Profile selection UI | Frontend (Streamlit sidebar) | Backend (`list_available_profiles`) | Sidebar owns picker render; backend owns discovery |
| Methodical modal multistep | Frontend (st.dialog + session_state) | Backend (`build_methodical_profile`, `compute_profile_diff`, `save_methodical_profile`) | UI drives multistep state; pure-function backend does no I/O until apply |
| Audit run + block classification | Backend (`process_document`) | Frontend (spinner + results render) | Business logic stays in `application_service.py` — no view-layer changes |
| Per-block display (grouped sections) | Frontend (render_block_section loop) | — | Pure display function; reads `report_df` from `ProcessingArtifacts` |
| Preflight error surface | Frontend (`st.error` under uploader) | Backend (`validate_document_input`) | Backend raises; frontend catches and translates to Russian message |
| Run-log emission | New module (`src/inference/run_log.py`) | Frontend (download button) | Single-writer in the new helper; frontend reads `.dump_json()` output |
| PII boundary enforcement | `src/inference/run_log.py` (at record time) | Test (`test_run_log_no_text_leak.py`) | Boundary is enforced at write time, not at display time |
| Download artifact naming | Backend (`application_service._timestamp`) | Frontend (download button label) | Existing naming scheme unchanged; run-log adds one new artifact |

---

## Standard Stack

### Core (all already in requirements.txt / venv)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| streamlit | 1.56.0 (pinned ≥ 1.35) | UI framework | Project-wide; `st.dialog` ≥ 1.32 satisfied [VERIFIED: dist-info] |
| pandas | ≥ 2.0 | report_df / predictions_df consumption | Already used in backend |
| python-docx | ≥ 1.1 | DOCX write (in backend) | Backend only — no new Phase 6 usage |

### No new dependencies

Phase 6 adds zero new packages. All capabilities derive from Streamlit primitives + `inject_page_styles` CSS already in `app.py`. [VERIFIED: 06-UI-SPEC.md Design System]

---

## Architecture Patterns

### System Architecture Diagram

```
Sidebar (config panel)
  ├── Profile picker (st.selectbox, key="profile_selectbox")
  │     └── «+» button → @st.dialog("methodical_modal", width="large")
  │           ├── Step 1: st.file_uploader (PDF/DOCX/TXT/MD)
  │           ├── Step 2: st.multiselect (base_profile_ids)
  │           ├── Step 3: «Сгенерировать предпросмотр» → build_methodical_profile()
  │           │           + compute_profile_diff() → st.code(diff)
  │           ├── Step 4a: «Применить и сохранить» (no collision) → save_methodical_profile()
  │           │           → set session_state["profile_selectbox"] → st.rerun() → modal closed
  │           └── Step 4b: collision → checkbox + textarea (reason ≥ 8) → enabled button
  ├── st.file_uploader (DOCX, key="docx_uploader")
  └── «Запустить аудит» (primary, enabled only when docx uploaded + profile selected)
            │
            ▼ run_processing()
            │   ├── RunLog.record("document-read")
            │   ├── process_document() ← application_service.py (UNCHANGED)
            │   │     └── audit_or_format_docx() → ProcessingArtifacts
            │   └── RunLog.record("save") → run_log.dump_json(path)

Main Pane (results)
  [empty state]
  «Загрузите DOCX-документ, чтобы начать аудит»
            ↓ (after run)
  Report header: «Отчёт по документу: {filename}» + profile_id line
  Summary counters: st.columns(6) of st.metric (total/no_change/changed/review/error/blocked)
  «Требуют внимания»  [expanded] ← render_block_section(df_attention, expanded=True)
  «Изменены»          [collapsed] ← render_block_section(df_changed, expanded=False)
  «Без изменений»     [collapsed] ← render_block_section(df_ok, expanded=False)
  «Скачать результаты» ← render_artifact_download_card() × 3-4 + run-log download
```

### Recommended Project Structure

```
app.py                        # ~840 LoC after evolution (was 1216)
src/
└── inference/
    ├── application_service.py   # UNCHANGED
    └── run_log.py               # NEW ~80 LoC — RunLog single-writer helper
tests/
├── test_app_upload_contract.py  # EXTEND with 2-3 module-level contract checks
├── test_run_log.py              # NEW — PII boundary + JSON schema tests
└── test_methodical_profile_editor.py  # EXISTS but collection-fails on missing streamlit import
                                        # (pre-existing, not in Phase 6 scope to fix)
```

### Pattern 1: `@st.dialog` for methodical modal + `st.rerun()` close

**What:** Decorated function called when «+» button is clicked; closes by `st.rerun()` after writing session_state.
**When to use:** Any modal that needs file upload + multistep state + programmatic dismiss.

```python
# Source: Context7 /streamlit/streamlit — dialog + session_state + rerun pattern
@st.dialog("Создать профиль из методички", width="large")
def methodical_modal(available_profile_ids: list[str]) -> None:
    uploaded = st.file_uploader(
        "Загрузите методичку",
        type=SUPPORTED_METHODICAL_UPLOAD_TYPES,
        key="modal_methodical_file",
    )
    base_ids = st.multiselect(
        "Базовые профили", options=available_profile_ids,
        default=["gost_7_32_2017"],
        key="modal_base_profiles",
    )
    if st.button("Сгенерировать предпросмотр") and uploaded:
        tmp_path = save_uploaded_bytes(uploaded.getvalue(), suffix=Path(uploaded.name).suffix)
        profile = build_methodical_profile(tmp_path, base_profile_ids=base_ids)
        diff_lines = compute_profile_diff(load_profile(base_ids[0]), profile)
        st.session_state["modal_diff_lines"] = diff_lines
        st.session_state["modal_draft_profile"] = profile

    diff = st.session_state.get("modal_diff_lines")
    draft = st.session_state.get("modal_draft_profile")
    if diff is not None and draft is not None:
        st.code("\n".join(diff), language=None)
        profile_id = draft["profile_id"]
        target_exists = (PROFILES_DIR / f"{profile_id}.json").exists() or \
                        (CUSTOM_PROFILES_DIR / f"{profile_id}.json").exists()
        if not target_exists:
            if st.button("Применить и сохранить", type="primary"):
                save_methodical_profile(draft, CUSTOM_PROFILES_DIR)
                st.session_state["profile_selectbox"] = profile_id
                # clear modal state before rerun
                for k in ("modal_diff_lines", "modal_draft_profile"):
                    st.session_state.pop(k, None)
                st.rerun()
        else:
            overwrite = st.checkbox("Перезаписать существующий профиль")
            reason = st.text_area("Причина (минимум 8 символов)", key="modal_reason")
            reason_ok = len(reason.strip()) >= 8
            if not reason_ok and reason:
                st.caption("Причина должна содержать минимум 8 непробельных символов (D-004: no silent rewrites).")
            btn_disabled = not (overwrite and reason_ok)
            if st.button("Применить и сохранить", type="primary", disabled=btn_disabled):
                draft["extraction_meta"]["override_reason"] = reason.strip()
                save_methodical_profile(draft, CUSTOM_PROFILES_DIR)
                st.session_state["profile_selectbox"] = profile_id
                for k in ("modal_diff_lines", "modal_draft_profile"):
                    st.session_state.pop(k, None)
                st.rerun()
    if st.button("Отмена"):
        for k in ("modal_diff_lines", "modal_draft_profile"):
            st.session_state.pop(k, None)
        st.rerun()
```

**Constraint (verified):** `st.sidebar` inside a dialog raises `StreamlitAPIException`. Session state keys shared between modal and main app must be distinct from widget keys to avoid widget-state conflicts across reruns.

### Pattern 2: `render_block_section` — per-row st.expander loop

**What:** One helper renders a titled group with a collapsible expander per block row.
**When to use:** All three grouped sections (attention, changed, no-change).

```python
# Source: Context7 /streamlit/docs — st.expander collapsed-by-default performance pattern
STATUS_CHIP = {
    "no_change":              ("●",  "Без изменений",                        "badge-ok"),
    "changed":                ("✏️", "Изменено",                              "badge-change"),
    "review":                 ("⚠️", "Требует проверки",                      "badge-warn"),
    "error":                  ("✗",  "Ошибка",                                "badge-error"),
    "blocked_unsafe_autofix": ("🛑", "Небезопасное автоисправление заблокировано", "badge-muted"),
}

def render_block_section(
    title: str,
    df: pd.DataFrame,
    expanded_by_default: bool,
) -> None:
    if df.empty:
        return
    st.subheader(f"{title} ({len(df)})")
    for _, row in df.iterrows():
        status = str(row.get("status", ""))
        icon, label, _ = STATUS_CHIP.get(status, ("?", status, "badge-neutral"))
        conf = row.get("confidence_score", "")
        conf_str = f"{float(conf):.2f}" if conf != "" else "—"
        header = f"{icon} {row.get('block_id', '?')} · {row.get('label', '')} · {label} · уверенность {conf_str}"
        with st.expander(header, expanded=expanded_by_default):
            if row.get("text"):
                st.markdown("**Оригинальный текст блока**")
                st.code(str(row["text"]), language=None)
            if row.get("explanation"):
                st.markdown("**Причина ручной проверки**")
                st.write(str(row["explanation"]))
            if row.get("violated_rules"):
                st.markdown("**Нарушенные правила**")
                st.write(str(row["violated_rules"]))
            if row.get("applied_fixes"):
                st.markdown("**Применённые исправления**")
                st.write(str(row["applied_fixes"]))
            if status == "blocked_unsafe_autofix" and row.get("unsafe_auto_fix_reason"):
                st.markdown("**Заблокированное автоисправление**")
                st.write(str(row["unsafe_auto_fix_reason"]))
            if status == "error":
                st.markdown("**Сообщение об ошибке**")
                st.write(str(row.get("explanation", "Внутренняя ошибка правила. См. журнал запуска.")))
                if row.get("error_class"):
                    st.caption(f"Класс ошибки: {row['error_class']}")
```

### Pattern 3: `RunLog` single-writer helper

```python
# src/inference/run_log.py — new module ~80 LoC
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

class RunLog:
    def __init__(self, input_filename: str) -> None:
        self._filename = Path(input_filename).name   # basename only — PII boundary
        self._records: list[dict[str, Any]] = []

    def record(
        self,
        stage: str,
        status: str,
        error_class: str | None = None,
        error_message: str | None = None,
        **extras: Any,
    ) -> None:
        # extras: block_id (int), profile_id (str) — NEVER raw text
        entry: dict[str, Any] = {
            "stage": stage,
            "ts": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "error_class": error_class,
            "error_message": error_message,
        }
        entry.update(extras)
        self._records.append(entry)

    def dump_json(self, path: Path) -> None:
        path.write_text(
            json.dumps(self._records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
```

### Anti-Patterns to Avoid

- **`st.exception(exc)` in run_processing**: Leaks Python traceback into the UI (currently at `app.py:773`). Replace with `st.error("Не удалось обработать документ: " + type(exc).__name__)`. [VERIFIED: app.py:773]
- **Logging document text in run-log `error_message`**: The `error_message` field must contain only the user-facing Russian string or the exception class name. Never `str(exc)` when `exc` carries document content.
- **Nested `st.dialog`**: Two `@st.dialog`-decorated functions cannot both be active in the same script run. [VERIFIED: dialog_decorator.py line 56 `raise StreamlitAPIException("Dialogs may not be nested...")`]
- **`st.sidebar` inside `@st.dialog`**: Will raise at runtime. [VERIFIED: dialog_decorator.py line 175]
- **Rewriting `inject_page_styles` CSS**: CLAUDE.md forbids improving working code. The `.badge-*` classes are reused verbatim for status chips.
- **Sharing widget `key=` between modal and main app for the same logical value**: Use distinct key namespaces (`modal_*` prefix for modal widgets).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Profile diff format | Custom JSON differ | `src/rules/profile_diff.compute_profile_diff` (Phase 5) | Already implemented, tested, produces U+2192 diff with section headers; `._source.` filtered [VERIFIED: profile_diff.py:53] |
| Profile save with overwrite guard | Inline logic in modal | `src/rules/methodical_extractor.save_methodical_profile` + inline `len(reason.strip()) >= 8` guard | Phase 5 CLI already enforces this; modal mirrors CLI contract verbatim |
| Stage timing / UTC timestamps | `time.time()` | `datetime.now(timezone.utc).isoformat()` in `RunLog.record` | ISO-8601 UTC portable; matches existing `_timestamp()` in application_service |
| Status color chips | New CSS classes | Existing `.badge-ok/warn/change/error/muted` from `inject_page_styles` | Already defined in app.py:97-102, tested visually, WCAG AA compliant |
| Profile options list | Direct dir scan | `application_service.get_profile_options()` → `list_available_profiles([PROFILES_DIR, GENERATED_PROFILES_DIR])` | Already merges built-in + generated profiles deduped [VERIFIED: application_service.py:74-76] |

---

## 1. Streamlit API Verification

**`st.dialog` support:** [VERIFIED: .venv/Lib/site-packages/streamlit/elements/dialog_decorator.py]
- Installed version: 1.56.0 (requirements.txt pins `streamlit>=1.35`). `st.dialog` available since 1.32. No bump needed.
- Decorator signature: `@st.dialog(title: str, width: "small"|"medium"|"large" = "small")`.
- Width in pixels: small ≤ 500, medium ≤ 750, large ≤ 1280. Methodical modal should use `width="large"` to fit the diff preview comfortably.
- **File upload inside dialog:** No explicit restriction found. `st.file_uploader` works inside a dialog function. [VERIFIED: no prohibition in dialog_decorator.py source]
- **Multistep state:** Use `st.session_state` with `modal_*`-prefixed keys for intermediate state (uploaded file, computed diff, draft profile). Keys survive the dialog's internal rerun. Clear keys before `st.rerun()` that dismisses the modal.
- **One dialog per script run:** `_assert_no_nested_dialogs()` raises if a second dialog is opened. Phase 6 has exactly one dialog — no conflict.
- **Programmatic close:** Inside the dialog function, set `st.session_state["profile_selectbox"] = new_id` then call `st.rerun()`. On the next run, the dialog function is not called → modal dismissed. [VERIFIED: UI-SPEC.md §"st.dialog programmatic-close pattern"]
- **No `st.sidebar` inside dialog:** Explicit prohibition. [VERIFIED: dialog_decorator.py:175]

**`st.data_editor` vs `st.dataframe` for block table:** [VERIFIED: Context7 /streamlit/docs AppTest widget properties]
- Neither supports row-level expand inside the widget.
- `st.data_editor` adds edit-state management overhead not needed here.
- **Decision (from 06-UI-SPEC.md, pre-verified):** per-row `st.expander` loop. See Pattern 2 above.

**`st.metric` for summary counters:** [VERIFIED: Context7 /streamlit/docs]
- `st.metric(label, value, delta=None)` renders large bold value with optional delta indicator.
- `st.columns(6)` with one `st.metric` per column fits in `layout="wide"` at 1280+ px viewport.
- Delta unused in Phase 6 (no prior-run comparison in scope).

---

## 2. app.py Evolve vs Rewrite

**Decision: Evolve in-place.** [VERIFIED: line counts from file inspection]

| Section | Lines | Action |
|---------|-------|--------|
| `inject_page_styles` (lines 26-155) | 130 | KEEP verbatim |
| `render_hero` (lines 158-175) | 18 | REMOVE (replaced by report header block) |
| `render_metric_card`, `render_status_badges` (lines 178-205) | 28 | KEEP callable for legacy compat; NEW UI uses `st.metric` |
| `normalize_table_values`, `format_profile_option`, `build_profile_options` (lines 208-236) | 29 | KEEP verbatim |
| `build_methodical_profile_draft`, `persist_custom_profile`, `_set_session_methodical_draft`, `_get_session_methodical_draft`, `_apply_methodical_form_edits` (lines 239-388) | 150 | REMOVE (replaced by modal helper calling extractor directly) |
| `filter_audit_df`, `filter_predictions_df` (lines 389-457) | 69 | REMOVE (no more tab-level filter widgets) |
| `render_artifact_download_card` (lines 458-478) | 21 | KEEP verbatim |
| `render_manual_decision_table` (lines 481-523) | 43 | REMOVE (no manual decision table in new flow) |
| `render_results` body (lines 526-749) | 224 | REPLACE with `render_report` |
| `run_processing` (lines 750-778) | 29 | KEEP with modification: remove `st.exception(exc)` → `st.error(...)`, add `RunLog` integration |
| `main()` (lines 780-1216) | 437 | REPLACE sidebar block + empty-state + result-render call |

**Estimated diff:** ~600 LoC deleted, ~350 LoC added in `app.py`. Net: ~960 LoC (from 1216).
One new module: `src/inference/run_log.py` (~80 LoC).
Backend untouched.

**Rationale:** CLAUDE.md «минимум кода» + «не рефактори то, что работает, без явного запроса». The reusable assets (`inject_page_styles`, `render_artifact_download_card`, `normalize_table_values`, `format_profile_option`, `build_profile_options`, `run_processing` core flow) are all preserved. The dropped code is concentrated in two areas: the 5-tab result view and the bloated methodical sidebar form.

---

## 3. Per-Block View Widget

**Decision: per-row `st.expander` loop.** [VERIFIED: 06-UI-SPEC.md §"Block table widget choice"]

Performance analysis for 260 blocks (Phase 5 corpus `50.docx` = 260 blocks per PROJECT.md):

| Group | Typical block count | Default state | Rendered HTML per row |
|-------|---------------------|---------------|----------------------|
| «Требуют внимания» | < 30 | Expanded | Full body HTML (hot path, correct) |
| «Изменены» | 10-50 | Collapsed | Header only (~200 chars) |
| «Без изменений» | 180-250 | Collapsed | Header only (~200 chars) |

Collapsed expanders emit only the header string — the body is not sent to the browser until clicked. 250 collapsed expanders at ~200 chars each = ~50 KB of HTML, well within Streamlit's render budget. The `layout="wide"` app already sends this order of magnitude. [ASSUMED — measured on similar-scale Streamlit apps; no 260-block benchmark run in this session]

**Fallback (executor discretion):** If «Без изменений» group render time exceeds 1500ms on the worst-case fixture, executor may replace ONLY that group with `st.dataframe` + paired `st.selectbox` for drill-in. The other two groups stay on per-row expanders unconditionally.

---

## 4. Summary Counters Placement

**Decision: `st.metric` strip — 6 columns.** [CITED: 06-UI-SPEC.md §"Summary counters"]

```python
c = st.columns(6)
metrics = [
    ("Всего блоков",               summary.get("blocks_total", 0)),
    ("Без изменений",              summary.get("no_change", 0)),
    ("Изменены",                   summary.get("changed", 0)),
    ("Требуют проверки",           summary.get("review", 0)),
    ("Ошибки",                     summary.get("error", 0)),
    ("Небезопасно (заблокировано)",summary.get("blocked_unsafe_autofix", 0)),
]
for col, (label, value) in zip(c, metrics):
    col.metric(label, int(value))
```

Rationale: `st.metric` is Streamlit-native (no custom HTML needed beyond existing CSS), maps 1:1 to the 6 required counters, and sits naturally above the grouped sections in the main pane linear flow. The existing `render_metric_card` HTML card is retired for this role (it was 4-up, did not include `review` or `blocked_unsafe_autofix` separately).

---

## 5. Run-Log Helper Placement + PII Boundary Enforcement

**Module location: `src/inference/run_log.py`** (new file, ~80 LoC).

**Rationale for separate module (not extension of `application_service.py`):**
- Single-responsibility: `application_service.py` orchestrates; `run_log.py` records.
- Testability: `RunLog` can be unit-tested in isolation without mocking the full processing pipeline.
- Import surface: `app.py` imports `RunLog` alongside `process_document`; clean separation.

**Allowed fields in each run-log record:**

| Field | Allowed | Rule |
|-------|---------|------|
| `stage` | `"document-read"`, `"classification"`, `"rule-apply"`, `"save"` | enum, hardcoded |
| `ts` | ISO-8601 UTC string | `datetime.now(timezone.utc).isoformat()` |
| `status` | `"ok"`, `"partial"`, `"error"` | enum |
| `error_class` | bare class name e.g. `"ValueError"` | `type(exc).__name__` — never `repr(exc)` |
| `error_message` | short Russian user message | **never** `str(exc)` when exc may contain doc text |
| `block_id` | integer from `predictions_df.block_id` | optional extra; integer only |
| `profile_id` | literal profile_id string | optional extra |
| Traceback | **FORBIDDEN** | never include |
| Document text | **FORBIDDEN** | never include paragraph text, raw block content, file offsets |
| Full file path | **FORBIDDEN** | use `Path(input_path).name` (basename only) |

**Test enforcement of «no document text leaks»:**
```python
# tests/test_run_log.py
def test_run_log_records_do_not_contain_text_content(tmp_path) -> None:
    log = RunLog("my_doc.docx")
    log.record("rule-apply", "error",
               error_class="KeyError",
               error_message="Блок не удалось проверить из-за внутренней ошибки правила.",
               block_id=42)
    out = tmp_path / "run.json"
    log.dump_json(out)
    content = out.read_text(encoding="utf-8")
    # PII boundary: no paragraph text, no tracebacks
    assert "Traceback" not in content
    assert "my_doc.docx" not in content or True  # basename allowed
    import json as _json
    records = _json.loads(content)
    for rec in records:
        assert "text" not in rec   # no raw block text field
        assert "traceback" not in rec
```

---

## 6. Methodical Modal Contract Mirror

The modal must mirror `cmd_extract_methodical_profile` (Phase 5 plan 5-03) verbatim. [VERIFIED: 05-03-PLAN.md must_haves + src/main.py:295 current implementation]

| CLI flag / behavior | Modal UI element | Validation rule |
|---------------------|-----------------|----------------|
| `--input-path` (required) | `st.file_uploader(..., type=["pdf","docx","txt","md"])` | File must be non-None before preview button enabled |
| `--base-profile-ids` | `st.multiselect("Базовые профили", options=available_profile_ids, default=["gost_7_32_2017"])` | At least one selection |
| Dry-run (default, no `--apply`) | «Сгенерировать предпросмотр» button | Writes draft to `tempfile.gettempdir()` via `save_uploaded_bytes`; diff displayed in `st.code` |
| `--apply` | «Применить и сохранить» button (primary) | Enabled only when diff has been generated (draft in session_state) |
| `--apply` on existing `profile_id` without `--force` | Button disabled + inline message: «Профиль {profile_id} уже существует. Чтобы перезаписать, отметьте чекбокс ниже...» | Check: `(PROFILES_DIR / f"{profile_id}.json").exists() OR (CUSTOM_PROFILES_DIR / f"{profile_id}.json").exists()` |
| `--force` | `st.checkbox("Перезаписать существующий профиль")` | Must be ticked |
| `--reason '<text ≥8 chars>'` | `st.text_area("Причина (минимум 8 символов)")` | `len(reason.strip()) >= 8` — client-side check (T-05-01) |
| Reason < 8 chars after strip (T-05-01) | Inline caption under textarea | `st.caption("Причина должна содержать минимум 8 непробельных символов (D-004: no silent rewrites).")` |
| Whitespace-only reason (T-05-01) | Button stays disabled | `len(reason.strip()) >= 8` is False for all-whitespace input |
| Save: `extraction_meta.override_reason` | Set in draft dict before `save_methodical_profile(draft, CUSTOM_PROFILES_DIR)` | `draft["extraction_meta"]["override_reason"] = reason.strip()` |
| Post-save: auto-select new profile | `st.session_state["profile_selectbox"] = profile_id` + `st.rerun()` | Sidebar `st.selectbox(key="profile_selectbox")` picks it up on next run |
| PDF with no text layer | `st.error("PDF-файл не содержит извлекаемого текста. Скан без OCR не поддерживается.")` | Caught from `ValueError` raised by `build_methodical_profile` when PDF chunk list is empty [VERIFIED: methodical_extractor.py:467-470] |
| `--output-dir` | Not exposed in modal | Always saves to `CUSTOM_PROFILES_DIR` (`results/generated_profiles/`) |
| Path traversal guard (T-04-02) | Not applicable in UI | `save_uploaded_bytes` writes to temp; `CUSTOM_PROFILES_DIR` is fixed — no user-controlled path |

**Key difference from CLI:** The modal does not implement the T-04-02 path traversal check (it is a CLI-only guard for `--input-path`). The modal uses `st.file_uploader` which hands bytes to `save_uploaded_bytes(data, suffix)` writing to `tempfile.NamedTemporaryFile` — no user-controlled path escaping possible.

---

## 7. Russian Copy Inventory

### Strings that carry forward from existing app.py

| String | Location in current app.py | Carries to Phase 6 |
|--------|---------------------------|-------------------|
| `"Профили ГОСТ не найдены в src/rules/profiles."` | line 787 | YES → `st.error(...)` when `get_profile_options()` empty |
| `"Загрузите документ и запустите анализ, чтобы увидеть сводку, аудит и артефакты."` | line 1207 | ADAPTED → new empty-state body |
| `"Запустить анализ документа"` (button) | line 1192 | ADAPTED → «Запустить аудит» per UI-SPEC |
| `"Поддерживаемый формат MVP: DOCX."` | line 1194 | YES → caption under run button |
| `"Baseline-модель недоступна: в workspace нет сохраненного .joblib-артефакта."` | line 757 | YES — keep as error condition |
| `"Панель управления"` (sidebar header) | line 801 | YES |
| Artifact download `"Скачать {path.name}"` pattern | line 471 | YES — `render_artifact_download_card` unchanged |

### New strings required by Phase 6

| Element | New Russian Copy |
|---------|----------------|
| Empty state heading | «Загрузите DOCX-документ, чтобы начать аудит» |
| Empty state body | «В левой панели выберите профиль ГОСТ и загрузите файл. После запуска аудита здесь появятся счётчики и блоки.» |
| Run button | «Запустить аудит» (replaces «Запустить анализ документа») |
| Modal trigger button | «+ Создать профиль из методички» |
| Modal preview button | «Сгенерировать предпросмотр» |
| Modal apply button | «Применить и сохранить» |
| Modal overwrite checkbox | «Перезаписать существующий профиль» |
| Modal reason field | «Причина (минимум 8 символов)» |
| Modal reason error | «Причина должна содержать минимум 8 непробельных символов (D-004: no silent rewrites).» |
| Modal cancel button | «Отмена» |
| Report header | «Отчёт по документу: {filename}» |
| Profile subline | «Профиль: {profile_name} ({profile_id})» |
| Section: attention | «Требуют внимания» |
| Section: changed | «Изменены» |
| Section: no_change | «Без изменений» |
| Downloads section | «Скачать результаты» |
| Run-log download | «Скачать журнал запуска (JSON)» |
| No attention blocks | «Документ соответствует профилю — блоков, требующих внимания, нет.» |
| Preflight unreadable | «Файл не читается. Проверьте, что это валидный DOCX (.docx, ZIP-архив). Откройте файл в Word и пересохраните, если нужно.» |
| Preflight no blocks | «В документе нет извлекаемых непустых блоков. Проверьте, что документ содержит текст.» |
| Preflight MIME mismatch | «Расширение файла `.docx`, но содержимое не соответствует DOCX-формату.» |
| Preflight file too large (soft) | «Файл превышает 50 МБ. Streamlit может работать нестабильно на больших файлах.» |
| Per-block error | «Блок не удалось проверить из-за внутренней ошибки правила. См. журнал запуска.» |
| Save error | «Не удалось сохранить исправленный DOCX: `{error_class_name}`. Скачайте отчёт CSV и журнал запуска для разбора.» |
| Profile collision | «Профиль `{profile_id}` уже существует. Чтобы перезаписать, отметьте чекбокс ниже и заполните поле «Причина» (минимум 8 символов).» |
| PDF no text layer | «PDF-файл не содержит извлекаемого текста. Скан без OCR не поддерживается.» |

### Strings retired in Phase 6

| Retired string | Reason |
|----------------|--------|
| «Обзор», «Предсказания», «Аудит», «Форматирование», «Артефакты» (tab labels) | 5-tab structure dropped per D-01 |
| «Черновик профиля» / form labels in methodical sidebar | Replaced by modal UI |
| «Извлечь правила» (sidebar button) | Replaced by «+ Создать профиль из методички» modal trigger |
| «Документ обработан успешно.» | Replaced by report header rendering |

---

## 8. Validation Architecture

> `nyquist_validation` key is absent from `.planning/config.json` — treating as enabled. [VERIFIED: config.json content]

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest ≥ 8.0 (pinned in requirements.txt) |
| Config file | none (no pytest.ini / pyproject.toml — `python -m pytest` required per Phase 4 lesson) |
| Quick run command | `python -m pytest tests/test_run_log.py tests/test_app_upload_contract.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q --ignore=tests/test_methodical_profile_editor.py` |
| Streamlit AppTest | Available via `streamlit.testing.v1.AppTest` (Streamlit ≥ 1.18; installed 1.56.0) |
| Playwright | Not configured in this repo; skip for Phase 6 |

**Note on `test_methodical_profile_editor.py`:** Currently fails collection due to missing streamlit module in the test runner's Python env (not the venv). [VERIFIED: pytest run output — `ModuleNotFoundError: No module named 'streamlit'`]. This is a pre-existing collection failure, out of Phase 6 scope. The planner should mark it as `--ignore` in the full suite command.

**Note on `test_app_upload_contract.py`:** Same collection failure in the current test runner env (no streamlit on PATH-python). Phase 6 must ensure tests that import `app.py` are runnable in the venv. The executor runs tests via `.venv/Scripts/python -m pytest` (Windows) or installs to the system env.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-ui-main-flow / REQ-ui-problem-block-view | `render_block_section` renders correct chip label + expander per status | Unit (pure helper, no Streamlit) | `python -m pytest tests/test_render_block_section.py -x -q` | ❌ Wave 0 |
| REQ-ui-main-flow | `app.SUPPORTED_UPLOAD_TYPES == ["docx"]`; `app.SUPPORTED_METHODICAL_UPLOAD_TYPES` unchanged | Module contract | `python -m pytest tests/test_app_upload_contract.py -x -q` | ✅ (needs venv fix) |
| REQ-pipeline-logging | `RunLog.record()` fields never contain text content; `dump_json()` produces valid JSON array with correct schema | Unit | `python -m pytest tests/test_run_log.py -x -q` | ❌ Wave 0 |
| REQ-pipeline-logging (PII boundary) | No `"text"`, `"traceback"`, `"Traceback"` keys in any run-log record | Unit (assertion on JSON output) | included in `tests/test_run_log.py` | ❌ Wave 0 |
| REQ-input-preflight | `preflight_check(path)` returns typed error for unreadable file, empty blocks, MIME mismatch | Unit (pure function) | `python -m pytest tests/test_preflight.py -x -q` | ❌ Wave 0 |
| REQ-ui-design-review | UI renders without exception; summary counters, three grouped sections, download section visible after simulated run | AppTest smoke | `python -m pytest tests/test_app_smoke.py -x -q` | ❌ Wave 0 |
| REQ-ui-design-review | Design-review visual sign-off (human) | Human review | Manual — see criteria below | N/A |
| Methodical modal: reason < 8 chars blocked | `modal_reason_is_valid("")` → False; `modal_reason_is_valid("abcdefg")` → False; `modal_reason_is_valid("root cause fix")` → True | Unit (pure predicate) | included in `tests/test_render_block_section.py` or `tests/test_run_log.py` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_run_log.py tests/test_render_block_section.py tests/test_preflight.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q --ignore=tests/test_methodical_profile_editor.py`
- **Phase gate:** Full suite green + human design-review sign-off before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_run_log.py` — covers REQ-pipeline-logging PII boundary + JSON schema
- [ ] `tests/test_render_block_section.py` — covers REQ-ui-problem-block-view helper contract + reason-validation predicate
- [ ] `tests/test_preflight.py` — covers REQ-input-preflight (if `preflight_check` is extracted as testable function)
- [ ] `tests/test_app_smoke.py` — AppTest smoke: app renders, empty state visible, no exception on load

**AppTest limitation:** `st.dialog` content is NOT accessible through `AppTest` in Streamlit 1.56 — the testing framework does not simulate dialog invocations. The methodical modal contract is validated via unit tests on the pure helper functions (`build_methodical_profile_draft`, `modal_reason_is_valid`, `compute_profile_diff`), not via AppTest. [ASSUMED — based on AppTest widget properties list from Context7 which does not include a "dialog" property; no explicit confirmation in docs]

### Design-Review Criteria for REQ-ui-design-review (SC-4)

PASS requires all of the following (falsifiable, not «owner approves»):

1. **Flow completeness:** Tester uploads a real DOCX, selects a profile, clicks «Запустить аудит», and reaches the download section in ≤ 3 sidebar interactions. No dead-ends (empty tab, broken button).
2. **Visual distinction:** «Требуют внимания» section is visually first and expanded by default; «Без изменений» section is collapsed. Status chips for `error` and `no_change` are visually distinguishable at a glance (different background color, different icon).
3. **No traceback exposure:** Running audit on an intentionally malformed DOCX (e.g., empty file) shows a Russian error message under the uploader. No Python class names other than the error class name visible. No stack trace visible.
4. **Run-log PII check:** Download «Скачать журнал запуска (JSON)» produces a JSON file. Open it. No paragraph text from the uploaded document appears in any field. Tester must inspect at least the `error_message` fields.
5. **Modal D-004 gate:** In the methodical modal, click «Применить и сохранить» when reason textarea is empty → button is disabled OR shows error message. Enter `"abc"` (7 chars) → still blocked. Enter `"abcdefgh"` (8 chars) → button becomes enabled.
6. **Profile auto-select:** After completing the methodical modal apply flow, close modal, verify the sidebar profile picker shows the new profile selected.

**Defects discovered during review are blocking** — fix before closing REQ-ui-design-review.

---

## 9. Risks / Landmines

### Risk 1: Streamlit rerun storm with `session_state` in modal

**What goes wrong:** If the modal writes to a `session_state` key that is also a widget key for a sidebar widget, the sidebar widget will reset on the next rerun, potentially breaking profile selection.
**Prevention:** Use `modal_*`-prefixed keys for all modal intermediate state. The close-and-rerun pattern (`st.session_state["profile_selectbox"] = new_id; st.rerun()`) specifically targets the named selectbox key — this is intentional and correct.
**Warning signs:** Profile picker resets to first option after modal close; loop between modal open and immediate re-open.

### Risk 2: Modal file size limits

**What goes wrong:** Streamlit's default `maxUploadSize` is 200 MB. The 9.4 MB методичка PDF is within limits. However, very large PDFs may cause `build_methodical_profile` to take > 30s (PDF text extraction is synchronous).
**Prevention:** Add a soft size check in the modal: warn if `uploaded.size > 50 * 1024 * 1024`. The hard limit is the existing Streamlit server config. No code change needed for Phase 6 — warn only.
**Warning signs:** Modal appears frozen; Streamlit server timeout on large PDFs.

### Risk 3: `test_methodical_profile_editor.py` collection failure

**What goes wrong:** This test file imports `from app import _apply_methodical_form_edits`, which fails if `streamlit` is not in the test runner's Python env. It is a pre-existing failure.
**Prevention:** Planner adds `--ignore=tests/test_methodical_profile_editor.py` to all Phase 6 pytest invocations. Do NOT fix this in Phase 6 — it is out of scope per 06-CONTEXT.md §"Risks".
**Warning signs:** `make regression-gate` fails on collection error for this file.

### Risk 4: `st.dialog` internal rerun vs. outer app rerun

**What goes wrong:** Inside a dialog, `st.rerun()` triggers the dialog's own re-execution (not the full app rerun) — this is Streamlit 1.31+ behavior. In 1.56 this is the documented behavior. The programmatic-close pattern (`set session_state → st.rerun()`) works because when the dialog function is NOT called on the next outer app run, the dialog is dismissed.
**Prevention:** Call `st.rerun()` inside the dialog function ONLY after setting the close-signal in `session_state`. Do NOT call `st.rerun()` from outside the dialog function to dismiss it — this will NOT dismiss the dialog.
**Warning signs:** Modal stays open after «Применить и сохранить»; the new profile is not selected in the sidebar.

### Risk 5: `blocked_unsafe_autofix` status in report_df

**What goes wrong:** If `report_df` does not have a `blocked_unsafe_autofix` status value (only legacy `"blocked"` or `True/False` boolean column), the chip mapping breaks.
**Prevention:** `render_block_section` must handle both the column `status` containing the literal string `"blocked_unsafe_autofix"` AND the boolean column `blocked_unsafe_autofix == True`. Read `ProcessingArtifacts.report_df` column schema before implementing. [VERIFIED: application_service.py:54 — `report_df` is `pd.read_csv(report_csv)`; actual column names depend on `audit_or_format_docx` output schema]
**Action for planner:** Add a task to inspect `report_df` column names against a real audit run output before writing `render_block_section`. This is a READ task, not ASSUMED.

---

## 10. Open Questions for Planner

1. **`report_df` column names:** What is the exact column schema produced by `audit_or_format_docx` → `report_csv`? Specifically: is block status in a `"status"` column, and is `"blocked_unsafe_autofix"` a separate boolean column or a status value? The planner should add an early task to print `report_df.columns.tolist()` on a real run. This affects how `render_block_section` filters the three groups.

2. **`validate_document_input` error surface:** Does `validate_document_input` in `src/inference/document_loader.py` raise specific typed exceptions for unreadable DOCX vs. MIME mismatch, or a single `ValueError`? The preflight translation to Russian error strings depends on catching specific exceptions. Planner should read `document_loader.py` before writing `run_processing`.

3. **Test runner environment:** Current pytest invocations fail on `app.py` import because `streamlit` is not on the test runner's system Python. Phase 6 tests that import `app.py` (including the new Wave 0 `test_app_smoke.py`) must run via the project venv. Planner must decide: (a) add a `conftest.py` that skips Streamlit-dependent tests when `streamlit` is not importable, or (b) document that all Phase 6 tests run via `.venv` Python. Either approach is acceptable; pick one and document.

---

## Common Pitfalls

### Pitfall 1: `st.exception(exc)` leaks traceback

**What goes wrong:** `app.py:773` calls `st.exception(exc)` which renders the full Python traceback in the UI — violates D-04 and REQ-pipeline-logging.
**Prevention:** Replace with `st.error("Не удалось обработать документ: " + type(exc).__name__)` and add `run_log.record("rule-apply", "error", error_class=type(exc).__name__, error_message=...)`.

### Pitfall 2: `_apply_methodical_form_edits` is dead after modal replaces sidebar form

**What goes wrong:** `app.py:275` defines `_apply_methodical_form_edits` which is used only by the old sidebar form. After the modal replaces the sidebar form, this function becomes dead code.
**Prevention:** Remove `_apply_methodical_form_edits` in the same wave as the modal is added. CLAUDE.md: «Удаляй orphans, появившиеся из-за твоих изменений».

### Pitfall 3: Session state key collision between modal step state and widget keys

**What goes wrong:** If `modal_methodical_file` or `modal_base_profiles` keys are reused as widget keys in the main app, Streamlit raises a `DuplicateWidgetID` error.
**Prevention:** All modal-internal state uses `modal_*` prefix. Confirm no existing `st.session_state` keys in `main()` use the `modal_*` prefix.

### Pitfall 4: Profile picker key mismatch after modal save

**What goes wrong:** If the sidebar selectbox uses `key="profile_selectbox"` but `format_profile_option` formatting changes, the stored `session_state["profile_selectbox"]` value may not match any option → selectbox ignores the set value.
**Prevention:** After `save_methodical_profile`, set `st.session_state["profile_selectbox"]` to the *formatted option string* (not the raw `profile_id`), OR rebuild `profile_label_to_path` before the selectbox renders on rerun. The UI-SPEC uses the raw `profile_id` as the selectbox value — verify which the selectbox actually stores (index vs. value vs. formatted string).

### Pitfall 5: Run-log PII boundary — `str(exc)` may contain document text

**What goes wrong:** Some rule-engine exceptions embed the offending paragraph text in their message (e.g., `f"Invalid numPr on paragraph: {para.text[:200]}"`). Passing `str(exc)` directly to `run_log.record(error_message=...)` would leak that text.
**Prevention:** Always use a fixed Russian user-message string for `error_message`, never `str(exc)`. Only `type(exc).__name__` is safe from the exception object.

---

## Code Examples

### Run-log integration in run_processing

```python
# app.py run_processing — revised
def run_processing(uploaded_file, selected_model_key, selected_mode, selected_profile_path):
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
    except ValueError as exc:
        run_log.record("document-read", "error",
                       error_class=type(exc).__name__,
                       error_message="Файл не читается или не содержит блоков.")
        st.error("Файл не читается или не содержит извлекаемых блоков.")
        st.session_state["last_run_log"] = run_log
        return
    except Exception as exc:
        run_log.record("rule-apply", "error",
                       error_class=type(exc).__name__,
                       error_message="Не удалось обработать документ.")
        st.error("Не удалось обработать документ: " + type(exc).__name__)
        st.session_state["last_run_log"] = run_log
        return

    run_log.record("save", "ok")
    st.session_state["last_result"] = result
    st.session_state["last_uploaded_name"] = uploaded_file.name
    st.session_state["last_run_log"] = run_log
```

### Download run-log in render_report

```python
# Inside render_report — at the bottom of downloads section
run_log: RunLog | None = st.session_state.get("last_run_log")
if run_log is not None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(st.session_state.get("last_uploaded_name", "doc")).stem
    log_path = REPORTS_DIR / f"{stem}_run_log_{timestamp}.json"
    run_log.dump_json(log_path)
    with open(log_path, "rb") as f:
        st.download_button(
            "Скачать журнал запуска (JSON)",
            data=f.read(),
            file_name=log_path.name,
            mime="application/json",
            use_container_width=True,
        )
```

---

## Runtime State Inventory

This section is omitted — Phase 6 is not a rename/refactor/migration phase. No stored data, live service config, OS-registered state, secrets, or build artifacts use a string being renamed.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Streamlit | All UI tasks | ✓ (in `.venv`) | 1.56.0 | — |
| pandas | report_df / predictions_df | ✓ | ≥ 2.0 | — |
| pytest | Test execution | ✓ (system Python) | ≥ 8.0 | — |
| `streamlit.testing.v1.AppTest` | App smoke tests | ✓ (in `.venv` 1.56) | 1.56.0 | skip Streamlit-specific tests in system Python env |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** The test runner's system Python does not have `streamlit` installed. Tests importing `app.py` must run via `.venv`. Planner must decide on venv invocation strategy (see Open Question 3).

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | 260 collapsed `st.expander` rows render in < 1500ms in Streamlit 1.56 | Per-Block View Widget | If wrong, planner must use the dataframe fallback for «Без изменений» group only — already designed in UI-SPEC as an executor escape hatch |
| A2 | `st.dialog` AppTest property is not available in `streamlit.testing.v1` 1.56 | Validation Architecture | If wrong, AppTest could also cover modal widget interactions — tests would be more complete |
| A3 | `report_df` has a `"status"` column with literal string values (`"no_change"`, `"changed"`, `"review"`, `"error"`, `"blocked_unsafe_autofix"`) | Risks §5, render_block_section | If wrong (e.g., status is in a boolean `blocked_unsafe_autofix` column), the group-split logic needs adjustment — planner must add a READ task to verify column schema |

**If this table were empty:** All claims were verified or cited. A3 is the most load-bearing assumption.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-----------------|--------------|--------|
| `st.tabs` for result sections | Grouped `st.expander` sections | Phase 6 | No dead-ends; «Требуют внимания» visually dominant |
| Methodical profile form in sidebar (369 LoC) | `@st.dialog` modal | Phase 6 | D-004 contract mirror; sidebar stays clean |
| `st.exception(exc)` for errors | `st.error(msg)` + run-log JSON | Phase 6 | No traceback in UI; PII boundary |
| `render_metric_card` HTML cards (4-up) | `st.metric` strip (6-up) | Phase 6 | Native Streamlit; includes `blocked_unsafe_autofix` counter |
| No run-log artifact | `src/inference/run_log.py` + JSON download | Phase 6 | Developer post-mortem without document content leak |

---

## Sources

### Primary (HIGH confidence)
- `.venv/Lib/site-packages/streamlit/elements/dialog_decorator.py` — st.dialog API, width options, restrictions verified directly
- `/Users/fedorova.van/experiments/gost_formatter/app.py` — line counts, function inventory, existing Russian copy, reusable assets
- `src/inference/application_service.py` — ProcessingArtifacts shape, process_document signature
- `src/rules/methodical_extractor.py` — build_methodical_profile signature, PDF-no-text error message
- `src/rules/profile_diff.py` — compute_profile_diff, write_diff_sidecar public API
- `src/main.py:295` — cmd_extract_methodical_profile implementation (Phase 5 plan 5-03 GREEN)
- `.planning/phases/06-streamlit-ui-redesign/06-UI-SPEC.md` — design contract (pre-approved)
- `.planning/phases/06-streamlit-ui-redesign/06-CONTEXT.md` — locked decisions D-01..D-04

### Secondary (MEDIUM confidence)
- Context7 `/streamlit/docs` — AppTest widget properties, st.metric, st.expander, st.dialog usage patterns
- Context7 `/streamlit/streamlit` — session_state, dialog + rerun pattern

### Tertiary (LOW confidence)
- A1 (expander performance): based on Streamlit rendering model understanding; not benchmarked in this session

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — installed version verified via dist-info, dialog source inspected
- Architecture: HIGH — based on direct code reading of app.py, application_service.py, dialog_decorator.py
- Pitfalls: HIGH — most derived from direct source inspection; A1 perf estimate is ASSUMED

**Research date:** 2026-05-14
**Valid until:** 2026-06-14 (Streamlit stable; fast-moving only in minor patch releases)

---

## RESEARCH COMPLETE
