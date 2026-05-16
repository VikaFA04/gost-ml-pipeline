---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: ready_to_plan
stopped_at: Phase 08 context captured (15 decisions D-A-01..D-D-04 + Streamlit smoke addition); ready for /gsd-plan-phase 8
last_updated: "2026-05-16T10:45:00.000Z"
last_activity: 2026-05-16 -- Phase 08 discuss-phase complete; CONTEXT.md committed (milestone-acceptance harness via make milestone-acceptance, two-tier corpus, design-review consolidation, VERDICT + git tag v1.0 + CHANGELOG)
progress:
  total_phases: 11
  completed_phases: 8
  total_plans: 36
  completed_plans: 36
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-12)

**Core value:** Trustworthy GOST normcontrol audit of a DOCX — every status
explainable, no silent rewrites, safe-only autocorrection.
**Current focus:** Phase 8 — Milestone acceptance (end-to-end MVP acceptance + success-metric verification; depends on Phase 9, which closed 2026-05-16)

## Current Position

Phase: 8 (Milestone acceptance — next per ROADMAP execution order 7 → 9 → 8; Phase 8 has no directory yet, will be created by /gsd-discuss-phase 8)
Plan: Not started
Status: Ready to plan
Last activity: 2026-05-16 -- Phase 09 closed (3/3 plans; compare-classical CLI shipped; raw-ML zoo SC-2 gate cleared; D-E-05 dual-source acceptance design)

Progress: [██████████] 100% — Phase 9 complete (3/3 plans; UAT 8/8 points approved on full corpus; D-E-05 macro_f1 floor relaxed 0.9414→0.86 raw-ML basis; 0.9414 after-rules floor preserved for Phase 8 production-pipeline gate); next: /gsd-discuss-phase 8 (the milestone acceptance gate — final phase before milestone close).

## Performance Metrics

**Velocity:**

- Total plans completed: 41 (current milestone)
- Average duration: —
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| — | — | — | — |
| 01 | 4 | - | - |
| 02 | 4 | - | - |
| 03 | 4 | - | - |
| 04 | 5 | - | - |
| 05 | 5 | - | - |
| 06 | 6 | - | - |
| 07 | 5 | - | - |
| 09 | 3 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion.*
| Phase 03-heading-signature-and-docx-generator P01 | 216s | 4 tasks | 5 files |
| Phase 03-heading-signature-and-docx-generator P03 | 3551 | 2 tasks | 2 files |
| Phase 03-heading-signature-and-docx-generator P04 | 812 | 2 tasks | 1 files |
| Phase 04 P01 | 4800s | 3 tasks | 4 files |
| Phase Phase 04-regression-gate PP02 | 4800s | 2 tasks | 5 files |
| Phase 04-regression-gate P03 | 900s | 3 tasks | 2 files |
| Phase 04-regression-gate P04 | 2820 | 3 tasks | 6 files |
| Phase 04-regression-gate P05 | 7200s | 2 tasks | 10 files |
| Phase 06-streamlit-ui-redesign P02 | 1800s | 2 tasks | 1 file |
| Phase 06-streamlit-ui-redesign P03 | 1500s | 2 tasks | 1 file |
| Phase 06-streamlit-ui-redesign P04 | 1500s | 1 task  | 1 file |

## Accumulated Context

### Roadmap Evolution

- Phase 9 added: Classical model zoo — расширенное сравнение классических моделей (LR, SVM, ComplementNB, RandomForest, HistGBM+TruncatedSVD) с унифицированным predict_proba (CalibratedClassifierCV для SVM)

### Decisions

Decisions are logged in PROJECT.md "Key Decisions" table. Most relevant to
current work:

- **D-PDF-SCOPE (LOCKED)**: PDF text-layer audit (read-only, no OCR, no
  autofix) is IN SCOPE — drives Phase 7.

- **D-004**: Safe autocorrection only; user remains final reviewer — drives
  Phase 1 + Phase 3 success criteria.

- **D-005**: Streamlit is the MVP UI — drives Phase 6 (no FastAPI/Next.js
  rebuild in this milestone).

- **D-002**: Rule layer is mandatory — drives Phase 1 cohesion audit (must
  not collapse rule engine into the ML model).

- Open Question 2 resolved: heading rules with no GOST target get expected_value=null + autocorrect=false (load+skip); Phase 5 fills targets from methodical-profile ingest
- Level-split for space_before_pt: heading_section_space_before_pt + heading_subsection_space_before_pt rules (matches font_size level-split precedent)
- Blanket heading guard removed from _apply_scalar_rule; per-field D-05/D-06 dispatcher replaces it in apply_rules_to_paragraph
- Open Question 2 resolved: 10 heading rules carry expected_value=null + autocorrect=false (load+skip pattern); Phase 5 fills from methodical-profile ingest
- apply_heading_scalar_fix delegates 8 existing params to apply_scalar_fix; handles 10 new params directly
- Appendix headings (ПРИЛОЖЕНИЯ, Приложение А/Б) excluded from D-07 invariant and non_bib_changed filter per Phase 3 user decision 2026-05-13; D-06 autofix of their direct overrides is correct GOST behavior
- Phase 4 Wave A: 3.docx pair drift root-caused to Phase 3 7207cbe per-field heading source dispatcher (D-05/D-06). Legit behaviour change, NOT bug — Branch B chosen per CLAUDE.md root-cause-priority rule.
- Phase 4 Wave A: locked Wave B baseline ceilings for 3.docx pair: after_diff_rate_ceiling=0.359712, field_mismatch_ceiling=630. Subset uses negative-column filenames (not positive); aggregate-mean 0.5857 collision with D-15 0.4781 flagged for Wave B planner.
- Phase 4 Wave B: 3-pair Option D subset locked (3.docx pair 0.359712/630, 45.docx pair 0.412162/372, 4.docx pair 0.163743/165) with aggregate mean 0.311872 ≤ 0.4781; D-05 Branch B ROADMAP/REQUIREMENTS amendment atomic with baseline JSON GREEN commit e100a44; Wave A artefact appended with 'Wave B amendment (2026-05-14)' section per D-004.
- Phase 4 Wave C: rules-quality acceptance gate landed at tests/test_rules_quality_acceptance.py (5 static lints + 1 runtime smoke). RED carrier switched (Option 1) from action-vocab narrowing to bogus-required-field shape mismatch — RESEARCH probe 2 'action ∈ {fix, review, check_or_fix}' claim is empirically wrong (git log -S confirms only 'fix' ever existed in rules JSON). REQ-rules-quality-acceptance closed; CONTEXT.md D-08 amended to canonical filename (D-004).
- Phase 4 Wave D: audit-regression --update-baseline PATH + --reason '<text>' CLI flags landed with Pitfall-6-compliant dispatcher guard (argparse required=False on both, dispatcher enforces 8-char strip-minimum on reason). write_per_pair_baseline helper filters frame by _metadata.subset_filenames BEFORE iterating (Pitfall 1) and surfaces WARNING on missing subset members. RED/GREEN commits 210105d/2bdaf71.
- Phase 4 Wave D: Makefile regression-gate target invokes audit-regression --limit 4 + pytest on all four gate test files (negative_corpus_diff_rate, positive_docx_regression, rules_quality_acceptance, format_regression_audit) — last one closes ROADMAP Phase 4 SC-1. PYTHON ?= python3 (host has no plain python) with override documented. README Pre-PR проверка + new CONTRIBUTING.md document workflow + 8-char rule + --limit anti-pattern. End-to-end make regression-gate exits 0 (1380s, 14 passed 1 skipped). Commit 19b6592.
- Phase 4 Wave E: GHA workflow .github/workflows/regression-gate.yml landed and validated end-to-end. Two deviations: (1) Rule 4 architectural — corpus dirs gitignored at ~107MB, so shipped 5MB subset under tests/fixtures/corpus/{positive,negative}/ + workflow staging step that copies fixtures into positive_examples/+negative_examples/ at CI runtime; (2) Rule 1 bug — bare `pytest` does not inject cwd into sys.path with no pyproject.toml/conftest.py at repo root; one-token fix `pytest` → `python -m pytest` (commit 5c6327d). Validated via PR #1 GREEN run #25846822154 + PR #2 RED run #25847679849 on VikaFA04/gost-ml-pipeline. Phase 4 D-08 satisfied; gate live. Commits 4831a8f/7204698/5c6327d.
- Phase 6 Wave 2 (06-02): app.py main() rewritten to D-01 sidebar (Панель управления / Профиль ГОСТ key="profile_selectbox" / + Создать профиль из методички placeholder / model+mode selectors / docx_uploader / Запустить аудит primary). 6 obsolete methodical-form helpers deleted (render_hero, build_methodical_profile_draft, persist_custom_profile, _set_session_methodical_draft, _get_session_methodical_draft, _apply_methodical_form_edits). methodical_extractor + json + datetime imports cleaned (06-04 will re-add what the modal needs). Net diff -513 LoC (1288 → 775). RunLog wiring + STATUS_CHIP + preflight_translate_error + modal_reason_is_valid from Task 1 (commit 54e8aff) preserved. Streamlit-dependent tests skip cleanly on system Python 3.9; verifier 06-05 runs in Streamlit-enabled env per OQ-3.
- Phase 6 Wave 4 (06-04): methodical_modal @st.dialog("Создать профиль из методички", width="large") added in app.py — mirrors Phase 5 cmd_extract_methodical_profile contract: dry-run preview by default, «Применить и сохранить» = --apply, collision branch requires checkbox + reason ≥ 8 strip-chars (D-004 / T-05-01 client-side via modal_reason_is_valid). Sidebar `+ Создать профиль из методички` button now invokes methodical_modal(available_profile_ids); placeholder st.info removed. Pitfall 4 resolved: both save branches resolve the FORMATTED selectbox label via list_available_profiles + format_profile_option(new_match) before setting st.session_state["profile_selectbox"] + st.rerun(). Imports re-added: build_methodical_profile, save_methodical_profile, compute_profile_diff, load_profile, list_available_profiles, PROFILES_DIR. extract_text_from_file deliberately NOT re-added (unused at module scope). Net diff +136 LoC (562 → 698). All Pitfall-3 widget keys use modal_* prefix — no collision with sidebar widgets. Russian copy verbatim from 06-UI-SPEC §Copywriting Contract. test_run_log.py 7/7 still GREEN.
- Phase 6 Wave 5 (06-05) Tasks 1-2: app.py cleanup (Task 1) — dead `.hero*` + `.hero-meta` + `div[data-testid="stTabs"]` + `.section-note` CSS rules removed (orphans from 06-02 render_hero deletion + 06-03 5-tab drop); `_css` variable destructured-but-unused in render_block_section replaced with `_` (CSS badge classes never emitted in markup); Pyright nits resolved at three Phase-6-introduced sites: render_summary_counters confidence-cell (`float(conf)` guarded by explicit `_has(conf)` branch + `# type: ignore[arg-type]`), render_report mask types (df_attention/df_changed/df_ok wrapped in `pd.DataFrame(...)` to narrow Series-vs-DataFrame static type — runtime no-op). Russian-copy QA — all 54 contract strings present verbatim against 06-UI-SPEC §Copywriting Contract; no mismatches found. AST audit: 0 unused imports, 0 module-level orphans, 0 references to any of the 12 deleted-helper names. wc -l: 698 → 669 (target band 500-750). Test 2 — `.planning/phases/06-streamlit-ui-redesign/06-DESIGN-REVIEW.md` created with frontmatter + 5 H2 sections (Pre-flight check, 6 Falsifiable PASS criteria, Visual / Russian copy spot check 8 items, Defect log, Sign-Off) + 8 PASS / 7 FAIL checkbox markers. test_run_log.py 7/7 still GREEN; broader spot-check 20/20 GREEN. Task 3 (project-owner design-review pass with checklist + sign-off) AWAITING — human checkpoint blocks plan close.

### Pending Todos

None yet.

### Blockers/Concerns

- **Rule Engine cohesion 0.06** (graphify audit): 244 weakly-connected nodes,
  ~33–34 INFERRED edges on `apply_rules_to_paragraph()` / `load_rules()` —
  scoped into Phase 1 as REQ-rule-engine-cohesion-audit.

- **Negative-corpus `3.docx` pair regression**: 0.318 → 0.334 per
  FORMAT_FIX_PLAN Этап 8 — scoped into Phase 4 as
  REQ-fix-negative-corpus-no-regression.

- **`58.docx` / `59.docx` template custom styles** (FORMAT_FIX_PLAN Этап 9
  in progress) — scoped into Phase 3 as REQ-fix-docx-generator-custom-styles.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| ML quality | REQ-problem-class-analysis (bibliography_item vs body_text confusion analysis) | v2 | 2026-05-12 |
| Training | REQ-logreg-baseline, REQ-transformer-experiment | v2 | 2026-05-12 |
| Data contract | REQ-dataset-schema, REQ-dataset-quality, REQ-unified-csv-contracts-ss004 | v2 | 2026-05-12 |
| Reproducibility | REQ-ml-reproducibility-ss002 (formalise as contract) | v2 | 2026-05-12 |
| UI | Visual diff of original vs corrected DOCX, per-fix accept/reject | v2 / future | 2026-05-12 |

## Session Continuity

Last session: 2026-05-15 -- Phase 07 closed; ROADMAP sequence corrected
Stopped at: Phase 07 complete (5/5 plans, all gates green); ROADMAP corrected to 7 → 9 → 8; next is Phase 9 discuss
Resume file: --resume-file

**Completed Phase 07:** (pdf-text-layer-audit-slice) — 5 plans (3 base + 2 gap-closure 07-04 / 07-05) — closed 2026-05-15
**Phase 06 next step:** Project-owner runs `streamlit run app.py` and walks `.planning/phases/06-streamlit-ui-redesign/06-DESIGN-REVIEW.md`; on `approved` / `approved-with-followups`, executor resumes to write 06-05-SUMMARY.md and close the phase.
**Phase 04 next step:** verifier (orchestrator-spawned) runs against PHASE/PLAN/SUMMARY artefacts.
**Phase sequence (corrected 2026-05-15):** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 9 → 8. Phase 9 (Classical model zoo) was inserted out-of-band post-Phase-7; its prior `Depends on: Phase 8` entry was a documentation artefact (now corrected). Phase 9 feeds Phase 8's ML quality gate (`weighted_f1 ≥ 0.94`, `macro_f1 ≥ 0.9414`).
