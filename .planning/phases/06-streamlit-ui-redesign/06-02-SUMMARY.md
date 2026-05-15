---
phase: 06-streamlit-ui-redesign
plan: 02
status: complete
subsystem: streamlit-ui
tags: [ui, sidebar, d-01, refactor, deletion]
wave: 2
requirements:
  - REQ-ui-main-flow
  - REQ-input-preflight
  - REQ-pipeline-logging
commits:
  - 54e8aff feat(06-02): STATUS_CHIP + preflight_translate_error + modal_reason_is_valid + RunLog wiring (Task 1)
  - "<task2 commit hash pending orchestrator>"
key-files:
  modified:
    - app.py
key-decisions:
  - Model + mode selectors retained inline in sidebar below profile picker (06-UI-SPEC §"Claude's Discretion" — Russian copy details). Plain st.selectbox / st.radio kept short.
  - methodical_extractor import line removed entirely (all three names unused after sidebar form deletion). 06-04 will re-add what the modal needs.
  - Empty-state body uses st.caption (not st.info) so the heading st.info line is visually dominant per UI-SPEC §Empty state copy.
  - Open-modal placeholder is an inline st.info on click — keeps the wiring testable without depending on 06-04.
metrics:
  app_py_loc_before: 1288
  app_py_loc_after: 775
  app_py_net_delta_loc: -513
  functions_deleted: 6
  primary_buttons: 1
duration_estimate: 30m
completed: 2026-05-14
---

# 06-02 SUMMARY — Sidebar redesigned to D-01; obsolete methodical helpers removed

## What was built (Task 2)

`app.py` `main()` rewritten to the D-01 control-panel shape:

1. **Sidebar**:
   - `st.header("Панель управления")`
   - `st.caption("Выберите профиль ГОСТ, загрузите DOCX-документ и запустите аудит.")`
   - `st.selectbox("Профиль ГОСТ", ..., key="profile_selectbox")` — D-03 modal-close anchor
   - `st.button("+ Создать профиль из методички", key="open_methodical_modal", use_container_width=True)` with placeholder `st.info` body (06-04 swaps the body)
   - `st.selectbox("Модель", ..., key="model_selectbox")`
   - `st.radio("Режим", ["audit", "fix"], key="mode_radio")` with copy «Только аудит» / «Применить безопасные исправления»
   - `st.file_uploader("Загрузите DOCX", type=SUPPORTED_UPLOAD_TYPES, key="docx_uploader")`
   - `st.button("Запустить аудит", type="primary", disabled=run_disabled, key="run_audit_button", use_container_width=True)` — only `type="primary"` button in the file (UI-SPEC §Color accent reserved for)
2. **Main pane** when `last_result is None`: empty state copy from UI-SPEC §Empty state copy verbatim (`st.info("Загрузите DOCX-документ, чтобы начать аудит") + st.caption("В левой панели выберите профиль ГОСТ и загрузите файл. После запуска аудита здесь появятся счётчики и блоки.")`).
3. **Main pane** when `last_result` exists: `render_results(result)` legacy renderer kept intact — 06-03 will replace with `render_report(result)`.
4. Run dispatch: `if run_clicked and not run_disabled` → `with st.spinner("Идёт аудит документа..."):` → `run_processing(...)`.
5. Session state defaults via `setdefault`: `custom_profile_items`, `last_run_log`, `modal_diff_lines`, `modal_draft_profile`.

## Functions deleted (orphans per CLAUDE.md «Удаляй orphans»)

| Function                          | Prior LoC | Reason                                                        |
| --------------------------------- | --------- | ------------------------------------------------------------- |
| `render_hero`                     | 158-175   | Replaced by interim empty state in `main()` (D-01)            |
| `build_methodical_profile_draft`  | 239-249   | Sidebar form removed; modal in 06-04 calls extractor directly |
| `persist_custom_profile`          | 252-261   | Same — modal will call `save_methodical_profile` directly     |
| `_set_session_methodical_draft`   | 264-267   | Modal will use `modal_*` session keys directly                |
| `_get_session_methodical_draft`   | 270-272   | Same                                                          |
| `_apply_methodical_form_edits`    | 275-386   | Old sidebar form editor removed; modal takes its place        |

## Imports cleaned

- Removed `from src.rules.methodical_extractor import build_methodical_profile, extract_text_from_file, save_methodical_profile` — all three unused after sidebar form deletion. Added a comment marker so 06-04 knows to re-add.
- Removed `import json` — unused after `_apply_methodical_form_edits` deletion.
- Removed `from datetime import datetime, timezone` — added by Task 1's Step A but never referenced from `app.py` (RunLog uses datetime internally). Per CLAUDE.md «Удаляй orphans, появившиеся из-за твоих изменений» these were plan-level orphans introduced and orphaned within 06-02, so cleaned up here.

## Verification

| Check                                                                  | Result                                                              |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------- |
| AST parse `app.py`                                                     | OK                                                                  |
| `wc -l app.py`                                                         | 775 (in 700-950 range)                                              |
| Net diff                                                               | +62 / -575 = -513 LoC                                               |
| `grep -c 'type="primary"' app.py`                                      | 1 (only run-audit button)                                           |
| All 6 deleted-helper greps                                             | exit 1 (function defs absent)                                       |
| `grep -c 'key="profile_selectbox"' app.py`                             | 1                                                                   |
| `grep -c 'key="docx_uploader"' app.py`                                 | 1                                                                   |
| `grep -c 'key="run_audit_button"' app.py`                              | 1                                                                   |
| Russian-copy greps (run-audit / + modal trigger / Профиль ГОСТ / Панель управления / empty-state head / empty-state body) | each 1 |
| `STATUS_CHIP`, `modal_reason_is_valid`, `preflight_translate_error` still at module scope | all PRESENT (Task 1 surface preserved)         |
| AST module-level constants                                             | `['SUPPORTED_UPLOAD_TYPES', 'SUPPORTED_METHODICAL_UPLOAD_TYPES', 'CUSTOM_PROFILES_DIR', 'STATUS_CHIP']` |
| AST function presence check                                            | required 4 present, 6 forbidden absent — OK                         |
| `python3 -m pytest tests/test_run_log.py -q`                           | 7 passed in 0.09s — no regression                                   |
| `python3 -m pytest tests/test_profile_diff.py -q`                      | 8 passed (broader-suite spot-check)                                 |

### Streamlit-dependent tests (env-skipped per OQ-3)

`tests/test_app_ui.py`, `tests/test_render_block_section.py`, `tests/test_preflight.py`,
`tests/test_app_upload_contract.py` all require Streamlit (not installed in the system
Python 3.9 used here; `.venv` holds Windows binaries unusable on macOS host).
- `test_app_ui.py` collects 4 tests then skips them cleanly via the `app_test`
  fixture's `pytest.importorskip("streamlit")`.
- `test_render_block_section.py` and `test_preflight.py` use module-level
  `pytest.importorskip("streamlit")` so the entire file is skipped at collection
  time (0 tests collected, no error).
- `test_app_upload_contract.py` does a top-level `import app` without an importorskip
  guard — collection ERRORs on this host. This is a pre-existing condition
  unchanged by this plan; will pass on a Streamlit-enabled venv. Plan note OQ-3
  acknowledges this acceptable.

These cannot be verified locally on this orchestrator host. Wave 6 (verifier
plan 06-05) is expected to run on a Streamlit-enabled environment and will
confirm GREEN/RED status of the AppTest assertions and the contract tests.

## Acceptance-criteria mapping

All Task 2 acceptance criteria from `06-02-PLAN.md` checked off; see
"Verification" table above.

## Deviations from Plan

### Auto-fixed Issues (Rule 1 / Rule 2 / Rule 3)

None. Plan executed verbatim except for the discretionary import-cleanup
described above (which the plan explicitly directed as Step A of Task 2:
"For tempfile / json False values, REMOVE the top-level import").

### Architectural decisions surfaced (Rule 4 — none triggered)

None.

### CLAUDE.md compliance

- «Удаляй orphans, появившиеся из-за твоих изменений» — applied to
  `methodical_extractor` import + `json` import + `datetime`/`timezone` imports.
- «Минимум кода» — no helper functions for the sidebar; everything inline.
- «Не рефактори то, что работает» — `inject_page_styles`, `render_metric_card`,
  `render_status_badges`, `normalize_table_values`, `render_results`,
  `render_artifact_download_card`, `render_manual_decision_table`,
  `filter_audit_df`, `filter_predictions_df` left intact for legacy compat
  (06-03 / 06-05 will trim further).

## Threat model

T-6-01 (PII leak via run-log) mitigation from Task 1 unchanged; sidebar
redesign does not touch the error/log surface.

T-6-02 (UI traceback leak) Task 1 already removed the `st.exception(exc)`
call. New sidebar does not introduce new exception sinks — the only
exception path is still through `run_processing` → `preflight_translate_error`.

## Note for 06-03 executor

- Replace the final `render_results(result)` call in `main()` (line ~771) with `render_report(result)`. The empty-state branch above it is the contracted UI for `result is None` — leave intact.
- `render_results`, `render_metric_card`, `render_status_badges`, `filter_audit_df`, `filter_predictions_df`, `render_manual_decision_table` are kept callable but orphaned by 06-03's `render_report` — delete them in this plan or 06-05.
- `STATUS_CHIP` is already module-level. Wire it into `render_block_section`.
- Session keys `last_run_log`, `modal_diff_lines`, `modal_draft_profile` are
  initialised in `main()` so any helper can read them.

## Note for 06-04 executor

- Re-add the methodical_extractor import: `from src.rules.methodical_extractor import build_methodical_profile, extract_text_from_file, save_methodical_profile` (and any other names the modal needs — `compute_profile_diff`, `load_profile`).
- Replace the body of the `if open_modal_clicked:` placeholder block (in `main()` sidebar) with the `methodical_modal(available_profile_ids)` invocation. Use `st.session_state["profile_selectbox"] = new_profile_id` + `st.rerun()` for programmatic close per 06-RESEARCH §1.

## Self-Check: PASSED

- `app.py` modified — 1 file changed, 62 insertions(+), 575 deletions(-)
- AST function presence check OK (4 required present, 6 forbidden absent)
- All Russian-copy greps return 1 occurrence each
- Only one `type="primary"` button (the run-audit button)
- Final wc -l = 775, within 700-950 range
- `tests/test_run_log.py` 7/7 GREEN — no regression
- Self-check artefacts: see `.planning/phases/06-streamlit-ui-redesign/06-02-SUMMARY.md` (this file) and the saved commit messages at `/tmp/06-02-task2-commit.txt`, `/tmp/06-02-summary-commit.txt`, `/tmp/06-02-state-commit.txt`.
