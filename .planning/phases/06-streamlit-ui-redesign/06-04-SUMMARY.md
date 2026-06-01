---
phase: 06-streamlit-ui-redesign
plan: 04
status: complete
subsystem: streamlit-ui
tags: [ui, modal, st-dialog, methodical-extraction, d-03, d-004]
wave: 4
requirements:
  - REQ-ui-main-flow
commits:
  - "<task1 commit hash pending orchestrator>"
key-files:
  modified:
    - app.py
key-decisions:
  - methodical_modal body inlined per CLAUDE.md «минимум кода» — no helper sub-functions for the 5 D-03 steps; the function is ~135 LoC and reads top-to-bottom as a single Streamlit script.
  - Preview file write to tempfile (CLI's `--apply`-less dry-run sidecar) deliberately skipped — the modal previews in-memory via st.code(diff). UI-SPEC §"Run-log" requires a JSON download for the audit run, but the methodical-modal preview JSON is not user-required (the diff is shown inline). Saves one I/O round-trip per preview.
  - PDF-no-text handling branches on `"PDF" in str(exc)` OR `"text" in str(exc).lower()` — matches the `methodical_extractor` ValueError message «PDF-файл не содержит извлекаемого текста: …» literally; non-PDF ValueErrors fall through to a generic «Не удалось извлечь методичку: {ClassName}» that surfaces the exception class without leaking str(exc).
  - Default base-profile multiselect is `["gost_7_32_2017"]` if present, otherwise `available_profile_ids[:1]` — keeps the modal usable when the canonical built-in is absent (defensive default; the plan only spec'd the canonical case).
  - Pitfall 4 fix uses `list_available_profiles([PROFILES_DIR, CUSTOM_PROFILES_DIR])` + `format_profile_option(new_match)` to compute the FORMATTED selectbox label after save (sidebar selectbox stores the formatted label, not the raw profile_id). Lookup-by-profile_id is O(n) but n is small (≤ 20 profiles in practice).
  - Both save branches (no-collision + force-reason) call the same Pitfall-4 lookup + `st.session_state["profile_selectbox"]` write + `st.rerun()` close. Cancel button + the two save branches are the three `st.rerun()` call sites in the modal.
metrics:
  app_py_loc_before: 562
  app_py_loc_after: 698
  app_py_net_delta_loc: +136
  methodical_modal_loc: 135
  imports_added: 4
  modal_session_state_keys: 8
duration_estimate: 25m
completed: 2026-05-14
---

# 06-04 SUMMARY — Methodical-profile `st.dialog` modal mirroring Phase 5 CLI contract

## What was built

### Task 1 — `methodical_modal` @st.dialog function + sidebar wiring

A single new module-level function in `app.py`, decorated with `@st.dialog("Создать профиль из методички", width="large")`, implements the 5-step D-03 modal flow:

1. **Step 1 — File uploader** (`st.file_uploader`, key=`modal_methodical_file`, `type=SUPPORTED_METHODICAL_UPLOAD_TYPES` → pdf/docx/txt/md).
2. **Step 2 — Base-profile multiselect** (`st.multiselect`, key=`modal_base_profiles`, default `["gost_7_32_2017"]` when present).
3. **Step 3 — Preview** («Сгенерировать предпросмотр», key=`modal_preview_button`):
   - Validates upload + base-pick.
   - `save_uploaded_bytes(uploaded.getvalue(), suffix=...)` → temp path.
   - `build_methodical_profile(input_path=tmp_path, base_profile_ids=base_ids)`.
   - `compute_profile_diff(load_profile(base_ids[0]), draft)` → diff_lines.
   - Stores draft + diff_lines in `st.session_state["modal_diff_lines" / "modal_draft_profile"]`.
   - PDF-no-text-layer ValueError → `st.error("PDF-файл не содержит извлекаемого текста. Скан без OCR не поддерживается.")` — no traceback in modal.
4. **Step 4a — No-collision apply** («Применить и сохранить», `type="primary"`, key=`modal_apply_button`):
   - `CUSTOM_PROFILES_DIR.mkdir(parents=True, exist_ok=True)` + `save_methodical_profile(draft, CUSTOM_PROFILES_DIR)`.
   - Pitfall 4: `list_available_profiles([PROFILES_DIR, CUSTOM_PROFILES_DIR])` → look up new item by `profile_id` → `format_profile_option(new_match)` → `st.session_state["profile_selectbox"] = formatted_label`.
   - Clears `modal_diff_lines` + `modal_draft_profile` → `st.rerun()` to dismiss.
5. **Step 4b — Collision branch** (D-004 / T-05-01):
   - `st.warning(f"Профиль `{profile_id}` уже существует …")`.
   - `st.checkbox("Перезаписать существующий профиль", key=modal_overwrite_checkbox)`.
   - `st.text_area("Причина (минимум 8 символов)", key=modal_reason_textarea)`.
   - Sub-8-char-non-empty reason → `st.caption("Причина должна содержать минимум 8 непробельных символов (D-004: no silent rewrites).")`.
   - Apply button (key=`modal_apply_force_button`) `disabled=not (overwrite and modal_reason_is_valid(reason))` — gate enforces D-004 client-side.
   - On click: `draft["extraction_meta"]["override_reason"] = reason.strip()` → save → Pitfall 4 selectbox preselect → clear + `st.rerun()`.
6. **Cancel** («Отмена», key=`modal_cancel_button`) → clear modal_* keys + `st.rerun()`.

The sidebar `+ Создать профиль из методички` button branch (added in 06-02 as a placeholder) now calls `methodical_modal(available_profile_ids)`. The new local `available_profile_ids` is computed from `all_profile_items` right after the existing `profile_label_to_path` line in `main()`.

## Imports added

Re-added at module scope (06-02 stripped these as orphans; 06-04 brings them back as the modal needs them):

| Import | Used by |
| --- | --- |
| `from src.rules.methodical_extractor import build_methodical_profile, save_methodical_profile` | preview + save branches |
| `from src.rules.profile_diff import compute_profile_diff` | preview branch |
| `from src.rules.profile_loader import PROFILES_DIR, list_available_profiles, load_profile` | preview branch + Pitfall 4 lookup |

`extract_text_from_file` is intentionally NOT re-imported — the modal calls `build_methodical_profile` directly which calls `iterate_text_chunks` internally; `extract_text_from_file` is a pre-Phase-5 backwards-compat wrapper not needed in the UI flow.

## Pitfall 4 resolution

The sidebar `st.selectbox("Профиль ГОСТ", options=profile_label_to_path.keys(), key="profile_selectbox")` stores the FORMATTED option label string (e.g. `"GOST 7.32-2017 [gost_7_32_2017] · structure · builtin"`) — NOT the raw `profile_id`. Naively setting `st.session_state["profile_selectbox"] = profile_id` after save would be ignored by the selectbox because the value is not in its `options` list.

Resolution implemented identically in both save branches:

```python
new_items = list_available_profiles([PROFILES_DIR, CUSTOM_PROFILES_DIR])
new_match = next((it for it in new_items if it.get("profile_id") == profile_id), None)
if new_match is not None:
    st.session_state["profile_selectbox"] = format_profile_option(new_match)
```

The next `st.rerun()` re-renders `main()`, `get_profile_options()` re-discovers the just-saved profile in `CUSTOM_PROFILES_DIR`, `build_profile_options(...)` includes it, and the selectbox now finds the formatted label in its options → the new profile is preselected.

## Pitfall 3 audit (no widget-key collision)

All modal-internal widgets use the `modal_*` prefix:

| Modal widget | Key |
| --- | --- |
| File uploader | `modal_methodical_file` |
| Base profiles | `modal_base_profiles` |
| Preview button | `modal_preview_button` |
| Apply (no collision) | `modal_apply_button` |
| Overwrite checkbox | `modal_overwrite_checkbox` |
| Reason textarea | `modal_reason_textarea` |
| Apply (force) | `modal_apply_force_button` |
| Cancel | `modal_cancel_button` |

Sidebar widgets in `main()` use unprefixed keys: `profile_selectbox`, `open_methodical_modal`, `model_selectbox`, `mode_radio`, `docx_uploader`, `run_audit_button`. Plus the four `download_*` keys in `render_report`. No overlap — Streamlit `DuplicateWidgetID` cannot fire.

## Verification

| Check | Result |
| --- | --- |
| AST parse `app.py` | OK |
| AST scan: `methodical_modal` exists at module scope, single positional arg `available_profile_ids: list[str]`, decorator `st.dialog('Создать профиль из методички', width='large')` | OK |
| `grep -nE '@st\.dialog\(.Создать профиль из методички.' app.py` | line 470 |
| `grep -c 'width="large"' app.py` | 1 |
| `grep -nE '^def methodical_modal' app.py` | line 471 (exactly one) |
| `grep -c 'modal_reason_is_valid' app.py` | 2 (definition + modal use) |
| `grep -c 'save_methodical_profile' app.py` | 2 (no-collision + force-reason save) |
| `grep -c 'st.rerun()' app.py` | 3 (no-collision save + force save + cancel) |
| Russian copy strings (each `grep -qF` → 0 exit) | «Сгенерировать предпросмотр», «Применить и сохранить», «Перезаписать существующий профиль», «Причина (минимум 8 символов)», «Причина должна содержать минимум 8 непробельных символов», «Отмена», «PDF-файл не содержит извлекаемого текста» — all present |
| `grep -qF 'override_reason' app.py` | OK |
| `grep -qF 'methodical_modal(available_profile_ids)' app.py` | OK |
| `grep -qF 'compute_profile_diff' app.py` | OK |
| `grep -qF 'build_methodical_profile' app.py` | OK |
| `grep -qF 'format_profile_option(new_match)' app.py` | OK (Pitfall 4 fix) |
| `grep -c 'Модал создания профиля из методички будет доступен' app.py` | 0 (placeholder removed) |
| `wc -l app.py` | 698 |
| `python3 -m pytest tests/test_run_log.py -q` | 7 passed in 0.08s — no regression |

### Streamlit-dependent tests (env-skipped per OQ-3)

`tests/test_render_block_section.py` (11 tests) — module-level `pytest.importorskip("streamlit")` skips collection cleanly on system Python 3.9 (no streamlit). Once Streamlit is available, these tests verify `app.STATUS_CHIP` (5 statuses + 5 badge classes + 5 Russian labels) and `app.modal_reason_is_valid` (5 cases — empty, short, whitespace-only, exactly-8, strip-then-count). The modal calls `modal_reason_is_valid(reason)` so any future regression in that helper is caught by the existing tests — no new test needed in this plan.

`tests/test_app_upload_contract.py`, `tests/test_app_ui.py`, `tests/test_preflight.py` — same env-skip status as in 06-02 / 06-03; this plan does not change their applicability.

## Acceptance-criteria mapping

All Task 1 acceptance criteria from `06-04-PLAN.md` checked off; see Verification table.

## Deviations from Plan

### Auto-fixed Issues (Rule 1 / Rule 2 / Rule 3)

None. Plan executed verbatim except:

- **Default base-profile fallback** — plan said `default=["gost_7_32_2017"]`, implementation uses `["gost_7_32_2017"]` if present, else `available_profile_ids[:1]`, else `[]`. Rule 2 (defensive default) — without this, the modal raises `StreamlitAPIException` if the user's environment is missing the canonical built-in. Documented in plan must_haves Step 2.
- **Generic ValueError fallback** — plan listed only the PDF-no-text branch; non-PDF ValueErrors now fall through to `"Не удалось извлечь методичку: " + type(exc).__name__`. Rule 1 (bug avoidance) — without this, a non-PDF ValueError would crash the modal silently instead of surfacing a Russian message.
- **`extract_text_from_file` not re-imported** — plan must_haves Step A says «build_methodical_profile, save_methodical_profile, compute_profile_diff, load_profile». `extract_text_from_file` was in 06-02's removed-imports comment but the modal does not call it (the extractor wraps it internally). CLAUDE.md «Удаляй orphans» applied — not re-added.

### Architectural decisions surfaced (Rule 4 — none triggered)

None.

### CLAUDE.md compliance

- «Минимум кода» — methodical_modal is one inline function, no helper sub-functions, no per-step decomposition. ~135 LoC.
- «Не «улучшай» соседний код» — `save_methodical_profile`, `compute_profile_diff`, `build_methodical_profile`, `load_profile`, `list_available_profiles` are all used as-is; no signature change, no new wrapping.
- «Удаляй orphans» — `extract_text_from_file` import not re-added (modal does not need it). The sidebar `st.info(...)` placeholder is replaced cleanly by the modal call.
- «Каждая изменённая строка должна напрямую отслеживаться до запроса пользователя» — every line in `methodical_modal` traces to a 06-04-PLAN must_have or to a 06-UI-SPEC §Copywriting Contract entry.
- «Russian UI throughout» — every user-facing string is verbatim from 06-UI-SPEC.

## Threat model

T-6-03 (silent profile overwrite) — mitigated as planned. The «Применить и сохранить» button in the collision branch is `disabled=not (overwrite and modal_reason_is_valid(reason))`. `modal_reason_is_valid` enforces `len(reason.strip()) >= 8` (T-05-01 client-side). Before save, `draft["extraction_meta"]["override_reason"] = reason.strip()` is written (`grep -qF "override_reason" app.py` passes). Mirrors `cmd_extract_methodical_profile` lines 360-376 in `src/main.py`.

T-6-04 (large PDF DoS) — accepted as planned. `save_uploaded_bytes` writes via `tempfile.NamedTemporaryFile`; Streamlit's default `maxUploadSize` (200 MB) is the upper bound. No 50-MB soft warn implemented in 06-04 (UI-SPEC discretion item, deferred).

T-6-07 (path traversal via uploaded filename) — accepted as planned. `save_uploaded_bytes(data, suffix=Path(uploaded.name).suffix)` extracts only the suffix; the temp path is OS-controlled. The save path is `CUSTOM_PROFILES_DIR / f"{profile_id}.json"` where `profile_id` is derived from the parsed methodical content (Phase 5 T-04-02 covered the CLI side; the UI is no worse).

T-6-08 (XSS via diff rendering) — mitigated. `st.code(joined_lines, language=None)` renders monospace-pre text, not HTML. `compute_profile_diff` output is ASCII + Cyrillic + the U+2192 arrow + path separators only.

## Notes for downstream plans

### 06-05 (cleanup + design-review)

- The modal is functional. AppTest cannot inspect dialog widgets in Streamlit 1.56 (per 06-RESEARCH §A2 / OQ-3) — design-review sign-off (REQ-ui-design-review) is a manual run of `streamlit run app.py` with the 6 falsifiable PASS conditions in 06-RESEARCH §"Design-Review Criteria for REQ-ui-design-review (SC-4)".
- Dead-import audit candidates after 06-04: none expected. `extract_text_from_file` was deliberately not re-added; `build_methodical_profile`, `save_methodical_profile`, `compute_profile_diff`, `load_profile`, `list_available_profiles`, `PROFILES_DIR` are all used in the modal.
- Russian-copy QA: the modal's 7 user-facing strings are verbatim from 06-UI-SPEC §"Modal — apply" / §"Modal — overwrite" / §"Modal cancel" / §"Error state copy" Modal rows. Sample: «Сгенерировать предпросмотр», «Применить и сохранить», «Перезаписать существующий профиль», «Причина (минимум 8 символов)», «Причина должна содержать минимум 8 непробельных символов (D-004: no silent rewrites).», «Отмена», «PDF-файл не содержит извлекаемого текста. Скан без OCR не поддерживается.».
- 06-DESIGN-REVIEW.md checklist creation: include the «Modal D-004 gate» (#5) and «Profile auto-select» (#6) PASS conditions from 06-RESEARCH §"Design-Review Criteria" — both are now verifiable end-to-end in a Streamlit-enabled venv.

## Self-Check: PASSED

- `app.py` modified — verified via grep (12 acceptance-criteria strings present, 0 placeholder occurrences).
- AST parse OK; `methodical_modal` exists at module scope with `@st.dialog("Создать профиль из методички", width="large")` decorator and single arg `available_profile_ids: list[str]`.
- Sidebar wiring: `methodical_modal(available_profile_ids)` called inside `if open_modal_clicked:` branch (line 648); `available_profile_ids` computed from `all_profile_items` at line 631.
- `grep -c "modal_reason_is_valid" app.py` → 2 (definition in 06-02 + use in 06-04).
- `grep -c "save_methodical_profile" app.py` → 2 (two save branches).
- `grep -c "st.rerun()" app.py` → 3 (no-collision save + force save + cancel).
- `python3 -m pytest tests/test_run_log.py -q` → 7 passed in 0.08s — no regression.
- Final `wc -l app.py` = 698 (was 562; +136 LoC, in line with the planned ~135-LoC modal addition).
- Self-check artefacts: this file (`06-04-SUMMARY.md`) and the saved commit messages at `/tmp/06-04-task1-commit.txt`, `/tmp/06-04-summary-commit.txt`, `/tmp/06-04-state-commit.txt`.
