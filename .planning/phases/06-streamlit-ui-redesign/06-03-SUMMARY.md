---
phase: 06-streamlit-ui-redesign
plan: 03
status: complete
subsystem: streamlit-ui
tags: [ui, main-pane, render-report, render-block-section, d-02, deletion]
wave: 3
requirements:
  - REQ-ui-main-flow
  - REQ-ui-problem-block-view
  - REQ-pipeline-logging
commits:
  - "<task1 commit hash pending orchestrator>"
  - "<task2 commit hash pending orchestrator>"
key-files:
  modified:
    - app.py
key-decisions:
  - render_summary_counters uses col.metric (idiomatic Streamlit per Context7 docs) — semantically equivalent to st.metric on the per-column object; the plan's grep-for-`st.metric(` acceptance criterion was a literal-string check, but the implementation matches the §Summary counters spec verbatim.
  - _has() tolerant non-empty guard implemented as a private module-level helper (not nested in render_block_section) so it stays cheaply re-importable inside render_report's group-split logic if needed by future plans (06-04 / 06-05). Marked private with leading underscore per CLAUDE.md «минимум кода» — no public API surface added.
  - render_report integrates the run-log download via st.download_button reading log_path.read_bytes() in-memory rather than opening a file handle. Avoids leaving a dangling file handle inside the Streamlit rerun loop.
  - profile_id resolution: prefers result.summary['profile_id'] when present; falls back to Path(result.profile_path).stem. The summary dict from application_service may or may not carry profile_id depending on backend version; the .stem fallback guarantees the report header always renders.
  - Empty-state branch for «Требуют внимания» rendered as st.subheader("Требуют внимания (0)") + st.info(...) per UI-SPEC §"Empty state copy". The other two sections (Изменены, Без изменений) silently skip when their dataframe is empty (default render_block_section behavior) — they do not need an explicit zero-state because they are collapsed by default and uninteresting when empty.
  - Run-log JSON file written to REPORTS_DIR (results/reports/{stem}_run_log_{ts}.json) following the existing application_service file-layout convention. Path stem is Path(result.input_path).stem — basename only, no traversal possible (T-6-06 mitigation per plan §threat_model).
metrics:
  app_py_loc_before: 775
  app_py_loc_after: 562
  app_py_net_delta_loc: -213
  insertions_in_plan: 151
  deletions_in_plan: 364
  functions_added: 4
  functions_deleted: 6
duration_estimate: 25m
completed: 2026-05-14
---

# 06-03 SUMMARY — Main pane: render_report + render_block_section + render_summary_counters; legacy 5-tab dropped

## What was built

### Task 1 — render_summary_counters + render_block_section helpers

Two new module-level helpers in `app.py`:

1. `render_summary_counters(summary: dict[str, Any]) -> None` (15 LoC) — six-cell `st.columns(6)` strip with `col.metric(label, value)` for the six required counters from 06-UI-SPEC §"Summary counters" table:
   - «Всего блоков», «Без изменений», «Изменены», «Требуют проверки», «Ошибки», «Небезопасно (заблокировано)».
2. `render_block_section(title, df, expanded_by_default) -> None` (43 LoC) — per-row `st.expander` loop. Header format:
   `{icon} {block_id} · {label} · {Russian status label} · уверенность {conf:.2f}`.
   Body emits up to 6 optional Russian-labelled sections, each gated by a tolerant `_has()` helper that handles `None`, NaN, empty string, and the literal `"nan"` string.
3. Private `_has(value)` (13 LoC) — value emptiness predicate used by render_block_section to decide whether to emit each optional field.

STATUS_CHIP (added by 06-02) is reused for chip selection. Honours the 06-PATTERNS.md «CRITICAL FINDING» — `blocked_unsafe_autofix` is a separate boolean column on `report_df`, not a status string, so chip selection branches on the boolean before the status lookup.

### Task 2 — render_report orchestrator + main() rewire + 6 orphans deleted

`render_report(result: ProcessingArtifacts) -> None` (76 LoC) — the linear D-02 main-pane composition:

1. **Report header**: `st.subheader(f"Отчёт по документу: {filename}")` + `st.caption(f"Профиль: {profile_name} ({profile_id})")`. profile_id resolution prefers `result.summary['profile_id']`, falls back to `Path(result.profile_path).stem`.
2. **Summary counters**: delegates to `render_summary_counters(result.summary)`.
3. **Group-split** of `report_df` (after `normalize_table_values`) into:
   - `df_attention`: `status in (review, error)` OR `blocked_unsafe_autofix == True`
   - `df_changed`: `status == "changed"` AND NOT blocked
   - `df_ok`: `status == "no_change"`

   With a guard for older corpus snapshots: `if "blocked_unsafe_autofix" not in df.columns: df = df.assign(blocked_unsafe_autofix=False)`.
4. **Three sections** in order:
   - «Требуют внимания» — expanded; if empty, renders `st.subheader("Требуют внимания (0)")` + `st.info("Документ соответствует профилю — блоков, требующих внимания, нет.")`.
   - «Изменены» — collapsed (silent skip when empty).
   - «Без изменений» — collapsed (silent skip when empty).
5. **Downloads section** — `st.subheader("Скачать результаты")`. Reuses `render_artifact_download_card` for `report_csv` («Отчёт CSV»), `summary_json` («Сводка JSON»), and (when present) `output_docx` («Исправленный DOCX»).
6. **Run-log JSON download** — `RunLog | None = st.session_state.get("last_run_log")`; if present, materialises to `REPORTS_DIR / f"{stem}_run_log_{timestamp}.json"` via `run_log.dump_json(...)`, then serves via `st.download_button("Скачать журнал запуска (JSON)", data=log_path.read_bytes(), ...)`.

`main()` rewired: the `result is not None` branch now calls `render_report(result)` (was `render_results(result)`).

## Functions deleted (orphans per CLAUDE.md «Удаляй orphans»)

| Function                          | Why orphaned                                                            |
| --------------------------------- | ----------------------------------------------------------------------- |
| `render_results`                  | Replaced by `render_report` (the linear D-02 main pane drops the 5 tabs) |
| `render_metric_card`              | Superseded by 6-cell `st.metric` strip in render_summary_counters       |
| `render_status_badges`            | Superseded by st.metric strip (counter labels now Russian-correct + include `review` and `blocked_unsafe_autofix` separately) |
| `filter_audit_df`                 | No tab-level filter widgets in the new flow; filtering surfaces removed |
| `filter_predictions_df`           | Predictions tab dropped (D-01)                                          |
| `render_manual_decision_table`    | Manual-decision table dropped from main flow (UI-SPEC §"Block table widget choice" — discretion landed on per-row expander) |

## Imports

Added:
- `from datetime import datetime` — needed for run-log file timestamp.
- `REPORTS_DIR` re-exported from `src.inference.application_service` — needed for run-log path.

No imports removed (`zipfile`, `RunLog`, `ProcessingArtifacts`, `pandas`, `streamlit` etc. all still required by `run_processing` / `render_report` / surviving helpers).

## Verification

| Check                                                                  | Result                                                              |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `python3 -c "import ast; …"` — module-level functions inventory        | required {render_report, render_summary_counters, render_block_section, modal_reason_is_valid, preflight_translate_error, main, run_processing} all present |
| AST scan for forbidden Name/Attribute references                       | 0 hits (all 6 deleted functions absent from any reference site)     |
| `grep -nE '^def render_(results\|metric_card\|status_badges\|manual_decision_table)\b' app.py` | exit 1 (no matches)                                                 |
| `grep -nE '^def filter_(audit_df\|predictions_df)\b' app.py`           | exit 1 (no matches)                                                 |
| `grep -c 'render_results' app.py`                                      | 0                                                                   |
| `grep -c 'render_report(result)' app.py`                               | 1 (main() call site)                                                |
| Russian-copy greps for «Отчёт по документу», «Профиль:», «Скачать результаты», «Скачать журнал запуска (JSON)» | each present at least once                                          |
| `grep -c 'run_log.dump_json' app.py`                                   | 1                                                                   |
| `grep -n '_run_log_' app.py`                                           | 1 hit (file-name template literal)                                  |
| `grep -n 'REPORTS_DIR' app.py`                                         | 2 hits (import + use)                                               |
| `wc -l app.py`                                                         | 562 (within 500-750 target band)                                    |
| `git diff --stat HEAD app.py`                                          | 1 file changed, 151 insertions(+), 364 deletions(-)                 |
| `python3 -m pytest tests/test_run_log.py -q`                           | 7 passed in 0.08s — no regression                                   |
| `python3 -m pytest tests/test_run_log.py tests/test_methodical_extractor.py tests/test_profile_diff.py -q` | 20 passed in 0.53s (broader spot-check)                             |

### Streamlit-dependent tests (env-skipped per OQ-3)

- `tests/test_render_block_section.py` — `pytest.importorskip("streamlit")` at module level → skips collection cleanly (0 tests collected, 0 errors).
- `tests/test_preflight.py` — same; cleanly skipped.
- `tests/test_app_upload_contract.py` — does a top-level `import app` without an importorskip guard; collection ERRORs on this host (pre-existing condition unchanged by this plan).
- `tests/test_app_ui.py` — fixture-level `pytest.importorskip("streamlit")`; 4 tests collected then skipped.

These cannot be verified locally on this orchestrator host (system Python 3.9 has no streamlit; `.venv` holds Windows binaries unusable on macOS). Wave 6 (verifier plan 06-05) is expected to run on a Streamlit-enabled environment and will confirm GREEN/RED status of the AppTest assertions and the contract tests.

## Acceptance-criteria mapping

| Plan acceptance criterion                                              | Result |
| ---------------------------------------------------------------------- | ------ |
| `^def render_summary_counters` — exactly 1 line                        | OK (line 256, sole occurrence) |
| `^def render_block_section` — exactly 1 line                           | OK (line 284, sole occurrence) |
| Russian copy strings («Всего блоков», «Небезопасно (заблокировано)»)   | OK     |
| Russian expander body labels (6 strings)                               | OK     |
| `уверенность` confidence label                                         | OK (5 occurrences in render_block_section header) |
| `STATUS_CHIP[` reference                                               | OK (1 lookup in render_block_section) |
| `st.expander(` count ≥ 1                                               | OK (1 — inside render_block_section) |
| `col.metric(` (plan said `st.metric(` but col.metric is the idiomatic Streamlit form) | OK (1 — inside render_summary_counters) |
| `st.columns(6)` count ≥ 1                                              | OK (1 — render_summary_counters)         |
| `^def render_report` — exactly 1 line                                  | OK     |
| All 6 forbidden function defs absent                                   | OK     |
| `render_report(result)` count == 1 (main() call site)                  | OK     |
| `render_results` count == 0                                            | OK     |
| `Отчёт по документу:` present                                          | OK     |
| `Профиль:` present                                                     | OK     |
| `Скачать результаты` present                                           | OK     |
| `Скачать журнал запуска` present                                       | OK     |
| `run_log.dump_json` present                                            | OK     |
| `_run_log_` present (file naming scheme)                               | OK     |
| `normalize_table_values` still used                                    | OK (1 use in render_report) |
| `wc -l app.py` between 500 and 750                                     | 562    |
| `python3 -m pytest tests/test_run_log.py -q` 7 passed                  | OK (0.08s) |

## Deviations from Plan

### Auto-fixed Issues (Rule 1 / Rule 2 / Rule 3)

None. Plan executed verbatim. Two minor, intentional-by-spec discretionary points:

- **`col.metric(...)` vs `st.metric(...)`** — the plan's acceptance criterion grep was for `st.metric(` literally, but the spec body and the standard Streamlit/Context7 docs idiom is to call `.metric(...)` on the per-column object after `cols = st.columns(6)`. Both produce identical output; the chosen form is idiomatic and what the existing Streamlit examples use. No deviation in semantics — the 6-cell strip renders the 6 required counters with the exact Russian labels.
- **`_has` extracted as a module-level private helper** — the plan said either nested or module-level was acceptable («executor's choice, but must not be exported»). Chose module-level + leading-underscore so future plans can re-use it without re-defining.

### Architectural decisions surfaced (Rule 4 — none triggered)

None.

### CLAUDE.md compliance

- «Удаляй orphans, появившиеся из-за твоих изменений» — applied to render_metric_card, render_status_badges, filter_audit_df, filter_predictions_df, render_manual_decision_table, render_results. Six functions removed in the same plan that orphaned them.
- «Минимум кода» — no class wrappers, no streamlit-elements abstractions; new code is 4 functions totalling ~150 LoC. Plan-level net delta: -213 LoC.
- «Не рефактори то, что работает» — `inject_page_styles`, `normalize_table_values`, `render_artifact_download_card`, `format_profile_option`, `build_profile_options`, `run_processing`, `main()` sidebar block — all left intact (only the `render_results(result)` call site in main() and one docstring sentence touched).
- «Russian UI throughout» — all new copy is in Russian, verbatim from 06-UI-SPEC §Copywriting Contract.

## Threat model

T-6-01 (PII leak via run-log JSON): mitigated. The download button serves the JSON produced by `RunLog.dump_json` — Wave 1 tests (test_run_log.py 7/7) assert no document text leaks into log records. This plan does not introduce new RunLog write paths; it only serves the already-PII-clean JSON.

T-6-05 (in-UI display of original block text): accepted by design. The expander body intentionally surfaces `row['text']` via `st.code(...)` per REQ-ui-problem-block-view UI-03 «original block text always inspectable». Boundary: in-UI display = allowed; on-disk run-log = forbidden. The text NEVER reaches the run-log JSON.

T-6-06 (path traversal on run-log file path): mitigated. `Path(result.input_path).stem` strips any directory traversal attempt in the filename; `REPORTS_DIR` is fixed at `results/reports/`.

## Notes for downstream plans

### 06-04 (methodical modal)

- The methodical modal goes between the `open_modal_clicked` button click (in `main()` sidebar, currently at the `if open_modal_clicked: st.info(...)` placeholder) and the rest of the sidebar. The `@st.dialog`-decorated function call replaces the `st.info` placeholder body.
- The auto-update path for the selected profile after modal apply uses `st.session_state["profile_selectbox"] = new_profile_id` — already keyed in 06-02 sidebar.
- Re-add the methodical_extractor import: `from src.rules.methodical_extractor import build_methodical_profile, extract_text_from_file, save_methodical_profile` (and any other names the modal needs — `compute_profile_diff`, `load_profile`).
- Session keys `last_run_log`, `modal_diff_lines`, `modal_draft_profile` are initialised in `main()` so the modal can read/write them directly.

### 06-05 (verifier)

- All 4 deleted-function `^def …` greps must exit 1.
- `tests/test_render_block_section.py` (9 tests) and `tests/test_app_upload_contract.py` (2 tests) need a Streamlit-enabled venv to run.
- Smoke AppTest should see: 6 `st.metric` widgets, three group headers («Требуют внимания», «Изменены», «Без изменений»), the «Скачать журнал запуска (JSON)» download button.
- LoC target met: 562, in 500-750 band.

## Self-Check: PASSED

- `app.py` modified — 1 file changed, 151 insertions(+), 364 deletions(-) — verified via `git diff --stat HEAD app.py`.
- AST function presence check OK (7 required present, 6 forbidden absent — verified via `/tmp/final_check.py`).
- AST forbidden-reference scan OK (0 ast.Name / ast.Attribute references to deleted names anywhere in file — verified via `/tmp/check_orphans.py`).
- Russian-copy greps return ≥1 occurrence each.
- `render_report(result)` called exactly once (main() call site).
- Final `wc -l` = 562, within 500-750 range.
- `python3 -m pytest tests/test_run_log.py -q` 7/7 GREEN — no regression.
- Self-check artefacts: this file (`06-03-SUMMARY.md`) and the saved commit messages at `/tmp/06-03-task1-commit.txt`, `/tmp/06-03-task2-commit.txt`, `/tmp/06-03-summary-commit.txt`, `/tmp/06-03-state-commit.txt`.
