# Phase 6: Streamlit UI redesign — Context

**Gathered:** 2026-05-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Rebuild the Streamlit UI around a linear audit flow (`upload → profile → run → summary → per-block table → download`) with consistent visual language for the 5 block statuses (`no_change` / `changed` / `review` / `error` / `blocked_unsafe_autofix`), first-class profile selection (Phase 5 GOST + custom + methodical-extracted), preflight + pipeline error surfacing that hides tracebacks and PII from end users, and a design-review sign-off by the project owner.

Out of scope: PDF text-layer audit (Phase 7), end-to-end milestone acceptance (Phase 8), backend changes beyond what the new UI needs from `application_service` / `methodical_extractor` / `profile_diff`.

Requirements addressed: REQ-ui-main-flow, REQ-ui-problem-block-view, REQ-input-preflight, REQ-pipeline-logging, REQ-ui-design-review.

</domain>

<decisions>
## Implementation Decisions

### Layout structure
- **D-01:** Dashboard pattern — **sidebar = config, main pane = results**. Sidebar persists across the whole flow and holds: profile picker, methodical-extraction trigger (see D-03), DOCX uploader, run button. Main pane shows summary counters → grouped per-block view → downloads (see D-02). No tabs in the main pane — the prior 5-tab structure (Overview/Predictions/Audit/Formatting/Artifacts in `app.py`) is dropped per ROADMAP SC-1 and PROJECT.md UI-01 («no orphaned tabs»). The flow stays linear because each main-pane section appears only when its prerequisite is satisfied (no DOCX → no run button enabled → no summary).

### Block status visual language
- **D-02:** Grouped sections by importance, not tabs and not one flat table:
  1. **«Требуют внимания»** — `error` + `review` + `blocked_unsafe_autofix` — expanded by default, drawn first.
  2. **«Изменены»** — `changed` — collapsed by default.
  3. **«Без изменений»** — `no_change` — collapsed by default.
  Each section is a table with a status chip column (icon + Russian label). Drill-in per row = inline `st.expander` showing per-block confidence + manual-review reason from `explanation` + original block text (REQ-ui-problem-block-view, UI-02, UI-03 satisfied). No modal, no side-panel — Streamlit inline expanders only.
- Summary counters (total / no_change / changed / review / error) live ABOVE the grouped sections per PROJECT.md UI-04. Counter placement details (cards vs row of metrics vs sticky header) are Claude's discretion during planning.
- `profile_id` is shown in the report header at the top of the main pane (above summary counters) per Phase 5 SC-1 and PROJECT.md UI-05.

### Profile selection + methodical extraction
- **D-03:** Profile picker = sidebar dropdown listing built-in GOST profiles + custom profiles from `results/generated_profiles/` (and `src/rules/profiles/` if applicable). Next to the dropdown sits a **«+» button that opens an `st.dialog` modal** for methodical-profile extraction. Modal flow mirrors the Phase 5 CLI contract verbatim:
  1. Upload PDF (also accept DOCX/TXT/MD per existing `SUPPORTED_METHODICAL_UPLOAD_TYPES`).
  2. Pick base profile(s) (`base_profile_ids` multiselect).
  3. Click «Сгенерировать предпросмотр» → runs the equivalent of `extract-methodical-profile --input-path ... --base-profile-ids ...` (no `--apply`) and renders the human-readable diff (U+2192 lines, `## section` headers, no `_source` paths in body, per Phase 5 plan 5-02) inside the modal.
  4. If diff acceptable → «Применить и сохранить» button = `--apply`. If a profile with the same `profile_id` already exists, the button is disabled and a checkbox «Перезаписать существующий профиль» appears + a textarea «Причина (минимум 8 символов)» that maps to `--force --reason`. Save is blocked until reason ≥ 8 chars after strip (D-004 contract from Phase 5 plan 5-03; T-05-01 whitespace-only rejection enforced client-side).
  5. After save, the modal closes and the new profile auto-selects in the sidebar dropdown.
- Preview JSON + `.diff.txt` written to `tempfile.gettempdir()` (matches the CLI dry-run behavior — no writes under `src/rules/profiles/` until explicit apply).

### Preflight + error surface
- **D-04:** **Inline friendly errors per stage + downloadable JSON run-log.**
  - Preflight failure (unreadable DOCX, malformed paragraphs, MIME mismatch) → `st.error` directly under the uploader with a plain-Russian message («Файл не читается — проверьте формат», never a Python traceback). No traceback in the UI by default.
  - Per-block rule-apply error → the block's row in «Требуют внимания» shows status=`error` with an `st.expander` containing the user-facing message + the technical error class name (no full traceback, no document content).
  - Save error → inline near the download buttons.
  - **Run log** is always available as a download button at the bottom of the downloads section: JSON array of stage records `{stage, ts, status, error_class, error_message, ...}` covering `document-read`, `classification`, `rule-apply`, `save`. **The log contains no document text** (no full paragraphs, no raw block content) — only filename, stage name, status, error class, technical context. PII boundary: filename + technical metadata IN; document content OUT (REQ-pipeline-logging).
  - Logger module is single-writer (one helper that all stages call); production logs (file-system log) are out of scope for Phase 6.

### Claude's Discretion
- Exact placement of summary counters (cards in row vs `st.metric` strip vs sticky banner).
- Download file naming policy (e.g., `{stem}_audited_{ts}.docx`, `{stem}.audit.csv`) — must satisfy PROJECT.md UI-06 «never overwrite original», concrete scheme picked during planning.
- Evolve `app.py` (1216 LoC, 5 tabs) vs full rewrite of the view layer keeping `src/inference/application_service.py` unchanged. Planner picks based on diff cost and risk; either way the 5-tab structure is dropped per D-01.
- Styling depth: keep current `inject_page_styles` CSS or extend; pure Streamlit primitives are sufficient (no `streamlit-elements` etc.).
- Russian copy details (button labels, error strings) — follow precedent already in `app.py` (Russian throughout).
- Block table widget choice: `st.dataframe` vs `st.data_editor` — picker decides based on whether inline status filter/row-expand needs are easier with one or the other.

</decisions>

<specifics>
## Specific Ideas

- The audit flow is the product — no orphan tabs, no dead-ends, no «Predictions» tab that exists only for debugging.
- Sidebar should feel like a control panel, main pane like a report.
- «Требуют внимания» is the section the user opens first 99% of the time — it must visually dominate.
- The methodical modal must enforce D-004 «no silent rewrites» exactly as the CLI does — UI and CLI present the same contract, no UI bypass.
- Run log download is sufficient for developer post-mortem — no need for a DEBUG toggle in this phase.
- Russian strings throughout (matches existing `app.py`).

</specifics>

<canonical_refs>
## Canonical References

Downstream agents (researcher, planner) MUST read these before producing RESEARCH.md / PLAN.md.

### Phase 5 contracts the UI must mirror
- `.planning/phases/05-rule-profiles-methodical-profile-ingestion/05-CONTEXT.md` — D-01..D-12, especially D-004 (no silent rewrites) and the dry-run / `--apply` / `--force --reason ≥8` flow that the methodical modal must mirror.
- `.planning/phases/05-rule-profiles-methodical-profile-ingestion/05-03-PLAN.md` — CLI behavior the modal must match (`cmd_extract_methodical_profile`, argument shape, error strings).
- `.planning/phases/05-rule-profiles-methodical-profile-ingestion/05-02-PLAN.md` — `compute_profile_diff` / `write_diff_sidecar` output shape (U+2192 arrows, `## section` headers, no `_source` paths). The modal renders this output verbatim.
- `.planning/phases/05-rule-profiles-methodical-profile-ingestion/05-01-PLAN.md` — `methodical_extractor.build_methodical_profile` return shape (per-leaf `_source` + derived `needs_manual_review`).

### Project-level docs
- `.planning/PROJECT.md` §Active — UI track (UI-01..UI-07) drives the success criteria for this phase.
- `.planning/REQUIREMENTS.md` — REQ-ui-main-flow, REQ-ui-problem-block-view, REQ-input-preflight, REQ-pipeline-logging, REQ-ui-design-review (PRD US-025/US-026/US-002/US-027 cross-refs).
- `.planning/ROADMAP.md` §«Phase 6» — 4 SC must be true at verification time.
- `CLAUDE.md` — execution principles (no silent rewrites; minimum-code principle; Russian-language UI consistent with existing app.py).

### Existing code the new UI consumes
- `src/inference/application_service.py` — `ProcessingArtifacts`, `get_profile_options`, `list_model_options`, `process_document`, `save_uploaded_bytes` — Phase 6 view-layer reuses these unchanged.
- `src/rules/methodical_extractor.py` — `build_methodical_profile`, `extract_text_from_file`, `save_methodical_profile` — modal calls these directly (or wraps the CLI).
- `src/rules/profile_diff.py` — `compute_profile_diff`, `write_diff_sidecar` — modal renders this output.
- `src/main.py` `cmd_extract_methodical_profile` — reference implementation for the modal flow.

No external ADR/spec docs exist in this repo — requirements are fully captured in the files listed above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/inference/application_service.py` (216 LoC) — backend service layer is clean and reusable as-is. Phase 6 changes the view layer only.
- `src/rules/methodical_extractor.py` — Phase 5 left this with per-leaf `_source` + derived `needs_manual_review`; the modal can call `build_methodical_profile(input_path, base_profile_ids)` directly.
- `src/rules/profile_diff.py` — pure-function module; `compute_profile_diff(base, candidate)` returns human-readable diff lines that the modal can stream into a `st.code` block.
- `results/generated_profiles/` (constant `CUSTOM_PROFILES_DIR` in `app.py`) — already the canonical store for user-saved methodical profiles.
- `app.py` `render_metric_card`, `render_status_badges`, `inject_page_styles` — reusable widgets for the new summary counters / status chips.

### Established Patterns
- Russian-language UI throughout existing `app.py` — Phase 6 continues this; Russian button labels, Russian error strings, Russian section headers.
- `st.set_page_config(layout="wide")` and sidebar-based config — already in place.
- `ProcessingArtifacts` dataclass return — the new main pane consumes this object; no JSON wire format invented.
- `tempfile.gettempdir()` for dry-run preview/diff output — Phase 5 precedent; modal mirrors it.

### Integration Points
- New view layer in `app.py` (or a refactored module if planner picks rewrite) → calls `application_service.process_document(...)` for audit runs.
- New view layer → calls `methodical_extractor.build_methodical_profile(...)` + `profile_diff.compute_profile_diff(...)` for the modal.
- Persisted profiles → `methodical_extractor.save_methodical_profile(profile, target_dir)` for the modal apply step (matches CLI's path).
- Run log → new helper module (location TBD by planner; suggested `src/inference/run_log.py` or `src/inference/application_service.py` extension).

### Risks / things the researcher should verify
- Streamlit `st.dialog` requires Streamlit ≥ 1.32 (verify `requirements.txt` pin).
- `st.expander` inside a `st.dataframe` row is not a native pattern — researcher should confirm whether row-expand needs a different widget (e.g., per-block `st.expander` rendered in a loop) and quantify performance for 260+ blocks.
- Existing `app.py` already references `methodical_extractor` — confirm the Phase 5 rewrite didn't break the existing import surface or the methodical-profile editor codepath at `tests/test_methodical_profile_editor.py` (currently failing on Python 3.9 dataclass issue per Phase 5 04 SUMMARY — not in Phase 6 scope to fix, but planner should note the collection-failure status).

</code_context>

<deferred>
## Deferred Ideas

- DEBUG toggle in the sidebar that reveals tracebacks — out of Phase 6 scope; the JSON run-log download covers developer post-mortem needs.
- Multi-document batch audit UI — separate capability, not in REQ-ui-main-flow.
- Live progress bar tied to internal rule-apply iteration counter — Streamlit can show a top-level spinner; finer-grained progress is deferred.
- Inline rule-engine debugging (which rule fired on which block) — Phase 1/Phase 2 surface this via `audit-docx` JSON; UI can link to the JSON download but does not render a rule trace view.
- File-system structured logger (alongside the in-UI JSON download) — deferred to Phase 8 or later if needed for production telemetry.

</deferred>

---

*Phase: 06-streamlit-ui-redesign*
*Context gathered: 2026-05-14*
