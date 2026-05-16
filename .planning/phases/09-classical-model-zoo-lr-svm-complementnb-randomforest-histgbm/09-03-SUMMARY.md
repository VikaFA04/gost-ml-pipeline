---
phase: 09-classical-model-zoo-lr-svm-complementnb-randomforest-histgbm
plan: 03
subsystem: ml-acceptance
tags: [classical-zoo, ml-comparison, phase-8-acceptance, makefile, docs, checkpoint, uat]

requires:
  - phase: 09-classical-model-zoo-lr-svm-complementnb-randomforest-histgbm
    provides: compare-classical CLI + 6-row results.csv with linear_svm_production row (plan 09-02)
provides:
  - tests/test_phase_8_sc2_acceptance.py — standalone SC-2 acceptance gate on latest classical_zoo run
  - Makefile compare-classical-acceptance target — automates full zoo run + SC-2 test
  - README.md §Classical model comparison — CLI documentation + production-identity distinction
  - Manual UAT approval recorded — Phase 9 SC-1..SC-5 verified live on full annotations_test.csv
affects: [phase-8-milestone-acceptance]

tech-stack:
  added: []
  patterns:
    - "Dual-source Phase 8 acceptance: raw-ML floor from classical zoo CSV (D-E-05 0.94/0.86) + after-rules system floor from production training metrics JSON (0.94/0.9414). Two independent measurements separating ML-stage quality from full-pipeline quality."
    - "Artifact-level acceptance gate pattern: pytest test reads latest run via sorted glob, pytest.skip when run absent (informational, not unit). Mirrors Phase 4 audit-regression model."

key-files:
  created:
    - tests/test_phase_8_sc2_acceptance.py
  modified:
    - Makefile
    - README.md

key-decisions:
  - "Plan 09-03 floor sync — all SC-2 macro_f1 references in 09-03 (test threshold, Makefile, README copy, plan body) updated from 0.9414 to 0.86 per D-E-05. The 0.9414 figure remains the after-rules system gate in REQUIREMENTS.md REQ-ml-quality-acceptance + ROADMAP Phase 8 SC-2 — a different metric source. Phase 8 acceptance reads both."
  - "Manual UAT is the closing checkpoint of Phase 9. Project-owner approved 8 verification points: venv activation, full zoo run, results.csv shape (6 rows × 8 cols, model-name match), SC-2 floor verification, informational linear_svm row, summary.txt + per_class_f1.md sanity check, and make compare-classical-acceptance exit 0."

patterns-established:
  - "Standalone SC-2 acceptance test: tests/test_phase_8_sc2_acceptance.py reads latest results/reports/classical_zoo_<ts>/results.csv via sorted glob, asserts linear_svm_production row clears the raw-ML floor (weighted_f1 >= 0.94 AND macro_f1 >= 0.86). Skips gracefully when no zoo run exists — informational gate, not a unit test."
  - "make compare-classical-acceptance pattern — full zoo run + pytest assertion in one Makefile target. Mirrors Phase 4's regression-gate target structure (PYTHON ?= python3, real-tab recipe indent, $$(date +%Y%m%d_%H%M%S) for shell-time timestamp)."

requirements-completed: [REQ-classical-model-zoo]

duration: 2 tasks autonomous (~5 min) + manual UAT checkpoint (~10 min full zoo run + visual inspection)
completed: 2026-05-16T08:30:00Z
---

# Phase 09-03: Phase 8 SC-2 acceptance gate + Makefile + README + UAT

**Standalone Phase 8 SC-2 acceptance test reads the latest classical zoo CSV and asserts `linear_svm_production` row clears the raw-ML floor (`weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.86` per D-E-05); Makefile `compare-classical-acceptance` target wires it; README documents the 6-row output. Project-owner UAT approved live on the full corpus.**

## Performance

- **Duration:** Task 1+2 ~5 min autonomous. Task 3 manual UAT ~10 min (full zoo run + 8-point inspection).
- **Started:** 2026-05-16T08:00:00Z
- **Completed:** 2026-05-16T08:30:00Z
- **Tasks:** 3 (2 autonomous edits + 1 human-verify checkpoint)
- **Files modified:** 3 (1 NEW: `tests/test_phase_8_sc2_acceptance.py`; 2 MODIFIED: `Makefile`, `README.md`)

## Accomplishments

### Task 1 — SC-2 acceptance test + Makefile target (commit `0c032ba`)

- `tests/test_phase_8_sc2_acceptance.py` (NEW) — `test_linear_svm_production_clears_phase_8_sc2_floor`:
  - Locates most-recent `results/reports/classical_zoo_<ts>/results.csv` via `sorted(_REPORTS_DIR.glob("classical_zoo_*/results.csv"), reverse=True)[0]`
  - Skips gracefully when no zoo run exists (informational gate, not a unit test for src/)
  - Reads with pandas, finds `model == "linear_svm_production"` row, asserts `weighted_f1 >= 0.94 AND macro_f1 >= 0.86` (D-E-05 raw-ML floor)
- `Makefile` — appended `compare-classical-acceptance` target:
  - Recipe: `$(PYTHON) -m src.main compare-classical --output-dir results/reports/classical_zoo_$$(date +%Y%m%d_%H%M%S)/` then `$(PYTHON) -m pytest tests/test_phase_8_sc2_acceptance.py -v`
  - Real-tab indentation (Makefile syntax requirement)
  - `$$` for shell-time `date` expansion
  - Existing `regression-gate` target untouched

### Task 2 — README.md §Classical model comparison (commit `49407d4`)

- New H2 section appended after `## Limits`. 4 locked substrings present:
  - `compare-classical` — CLI name
  - `results/reports/classical_zoo_` — output path stem
  - `linear_svm_production` — Phase 8 SC-2 grep target (NOT `linear_svm`)
  - `six rows` — results.csv shape (D-E-01)
- Documents: invocation, the 6 rows + interpretation, `linear_svm` vs `linear_svm_production` distinction, reference to `.planning/phases/09-.../`
- Existing `## Streamlit UI` and `## Limits` sections unmodified

### Task 3 — Manual UAT (8-point checkpoint)

**APPROVED** by project owner 2026-05-16. All 8 verification points passed:

1. ✓ venv activation (`/tmp/gost-test-venv` per Phase 7 precedent; sklearn 1.6.1 + pandas + streamlit + fitz)
2. ✓ Full (non-quick) zoo run produced `results/reports/classical_zoo_<ts>/` with 4 expected files
3. ✓ `results.csv` shape: 8 columns in D-C-02 order, 6 rows, all 6 expected model names present
4. ✓ `linear_svm_production` row hits `weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.86` (D-E-05 floor)
5. ✓ `linear_svm` row informational below floor (apples-to-apples zoo baseline; documents the TextPatternFeatures contribution)
6. ✓ `summary.txt` documents per-model preprocessing_variant + metrics + SC-2 verdict for linear_svm_production
7. ✓ `per_class_f1.md` has `## <model_name>` heading per model + 5-column markdown table; `body_text` class appears in every successfully scored model section
8. ✓ `make compare-classical-acceptance` exits 0 (full run + acceptance test PASS end-to-end)

## Phase 9 SC closure (live verification)

| SC | Truth | Status |
|----|-------|--------|
| SC-1 | CLI exists and runs end-to-end; --quick smoke writes 4 artifacts, exits 0 | ✓ live (UAT Points 1-2, Make target) |
| SC-2 | results.csv has 6 rows (D-E-01), 8 columns (D-C-02 locked order), every row weighted_f1 > 0.5 | ✓ live (UAT Point 3) |
| SC-3 | linear_svm_production row clears raw-ML floor weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.86 (D-E-05) | ✓ live (UAT Point 4 + make compare-classical-acceptance exit 0) |
| SC-4 | Reproducibility: results.json records dataset_hashes, environment, cli_args, timestamps; RANDOM_STATE=42 | ✓ from Plan 09-02 (results.json schema asserted in test_cli_smoke_runs_end_to_end_quick) |
| SC-5 | Per-class coverage: per_class_f1.md contains every label_core class for every scored model | ✓ live (UAT Point 7 + test_per_class_f1_md_contains_every_label_core_class) |

## Commits

- `0c032ba` test(09-03): Phase 8 SC-2 acceptance gate + Makefile compare-classical-acceptance target
- `49407d4` docs(09-03): add Classical model comparison section to README.md

(Plus plan-sync commit `7d5f7cb` on main pre-Wave-3 dispatch and OQ-5 amendment commit `78187fb` on main pre-Wave-3 dispatch.)

## Self-Check

- [x] All 3 tasks executed (Task 1+2 autonomous + Task 3 checkpoint approved)
- [x] Each task committed individually
- [x] SUMMARY.md created and to be committed in this commit
- [x] No modifications to STATE.md or ROADMAP.md (orchestrator owns those writes post-merge)
- [x] D-E-05 floor (0.86) reflected in test + Makefile + README + plan body
- [x] Existing Makefile regression-gate target UNMODIFIED
- [x] Existing README §Streamlit UI + §Limits sections UNMODIFIED
- [x] Manual UAT approved by project owner — all 8 points pass on the full annotations_test.csv corpus
- [x] make compare-classical-acceptance exits 0 (zoo run + SC-2 test PASS end-to-end)

## Self-Check: PASSED
