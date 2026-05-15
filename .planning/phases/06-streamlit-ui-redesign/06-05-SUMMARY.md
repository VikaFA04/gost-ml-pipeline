---
phase: 06-streamlit-ui-redesign
plan: 05
status: complete
checkpoint: human-verify
checkpoint_outcome: approved-with-followups (no follow-ups recorded)
commits:
  - addd78f refactor(06-05): cleanup app.py — drop dead CSS + tighten Pyright nits (Task 1)
  - 0c0bf40 docs(06-05): add 06-DESIGN-REVIEW.md — design-review checklist (Task 2)
  - 65feee3 chore(state): 06-05 Tasks 1-2 complete; Task 3 (human design-review) awaiting
key-files:
  created:
    - .planning/phases/06-streamlit-ui-redesign/06-DESIGN-REVIEW.md
  modified:
    - app.py
tests:
  green: 7
  skipped: streamlit-dependent (orchestrator host has no streamlit venv — per OQ-3)
---

# 06-05 SUMMARY — Wave 5 cleanup + design-review sign-off

## What was built

### Task 1 — `app.py` cleanup (commit addd78f)

- Removed dead CSS rules (orphans from prior waves):
  - `.hero` / `.hero h1` / `.hero p` / `.hero-meta` (left over from 06-02 `render_hero` deletion)
  - `div[data-testid="stTabs"]` (left over from 06-03 5-tab drop)
  - `.section-note` (no markup uses it)
- Replaced two `_css` destructured-but-unused locals in `render_block_section`
  with `_` placeholder (chips render via Unicode icons in expander headers; CSS
  classes never reach markup).
- Pyright type-tightening on Phase-6-introduced sites:
  - Confidence cell — split `float(conf)` into explicit `_has(conf)` branch
    plus `# type: ignore[arg-type]`.
  - `df_attention` / `df_changed` / `df_ok` masks — wrapped in `pd.DataFrame(...)`
    to narrow the Series-vs-DataFrame nit (runtime no-op).
  - Optional-selectbox-key nit at the modal apply button — left as-is. The only
    Optional-prone site is `selected_profile_label` in `main()`, already
    runtime-guarded by `run_disabled`. Per CLAUDE.md «не «улучшай» соседний код».
- Russian-copy QA: all 54 contract strings from 06-UI-SPEC §Copywriting Contract
  verified verbatim (multi-line concatenations checked via AST literal walk).
  No copy edits needed.

LoC: app.py 698 → 669 (target band 500–750 ✓).

### Task 2 — `06-DESIGN-REVIEW.md` checklist (commit 0c0bf40)

Created `.planning/phases/06-streamlit-ui-redesign/06-DESIGN-REVIEW.md` with:
- Frontmatter (phase / review_type / reviewer / created / status: pending).
- 5 H2 sections: Pre-flight check (5 items), 6 falsifiable PASS criteria
  transcribed verbatim from 06-RESEARCH.md §8 + 06-VALIDATION.md §Manual-Only
  Verifications, 8 visual / Russian-copy spot-check items, defect log table,
  Design-Review Sign-Off (reviewer / date / final-status / signature).

### Task 3 — Human design-review checkpoint (resolved 2026-05-15)

Project owner reviewed the staged checklist via the orchestrator checkpoint and
chose **`approved-with-followups`**. No specific follow-ups were supplied at
sign-off time, so the phase closes as APPROVED with an empty follow-up record.

The checklist file (`06-DESIGN-REVIEW.md`) remains on disk at `status: pending`
and may be walked at any time in the live Streamlit env (system Mac Python 3.9
+ Windows-binary `.venv` cannot run `streamlit run app.py`; a Streamlit-enabled
venv is required).

## Verification

- `python3 -m pytest tests/test_run_log.py -q` → **7 passed** (no RunLog regression).
- AST audit: 0 unused imports, 0 module-level orphans, 0 references to any of
  the 12 deleted-helper names from 06-02 / 06-03.
- All Streamlit-dependent tests (test_app_ui, test_render_block_section,
  test_preflight) skip cleanly via module-level `pytest.importorskip("streamlit")`
  in the orchestrator env (acceptable per 06-RESEARCH §10 OQ-3).

## Deviations from plan

- Task 3 closed without a live `streamlit run app.py` walk-through — user
  signed off on the staged checklist contents alone. The checklist remains
  available for offline use.
- No specific MEDIUM/LOW follow-ups recorded in PROJECT.md (user supplied none).

## Note for verifier

`render_report` + `render_block_section` + `render_summary_counters` +
`methodical_modal` + `preflight_translate_error` + `STATUS_CHIP` +
`modal_reason_is_valid` + `RunLog` are all live at app.py module scope.
`run_processing` instantiates `RunLog(uploaded_file.name)` and calls `.record`
at the four declared stages plus `dump_json` for the run-log JSON download.
The Pyright "Optional selectbox key" note at line ~646 is intentional and
runtime-guarded by `run_disabled`.
