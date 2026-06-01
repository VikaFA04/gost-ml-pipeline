# Phase 8: Milestone acceptance — Context

**Gathered:** 2026-05-16
**Amended:** 2026-05-16 (post-research OQ-1..OQ-5 + Phase 6 sign-off gap resolutions appended as D-E-01..D-E-07)
**Status:** Ready for planning
**Locked-by:** /gsd-discuss-phase 8 session 2026-05-16 + post-research resolution session 2026-05-16

<domain>
## Phase Boundary

Phase 8 is the milestone-v1.0 acceptance gate. It runs the four ROADMAP SC end-to-end on a representative DOCX corpus, captures pass/fail per criterion, consolidates prior-phase design reviews, and produces a sign-off VERDICT.md + `git tag v1.0` + CHANGELOG.md. Phase 8 is NOT new-feature work — strictly verification of what Phases 1-7+9 already shipped + milestone-close artifacts.

ROADMAP Phase 8 success criteria (verbatim):

1. End-to-end acceptance run on a representative DOCX corpus: extraction → features → SVM prediction → rule audit → CSV report → safe corrected DOCX where applicable → Streamlit UI mirrors all CLI outputs.
2. ML quality gate held: `weighted_f1 ≥ 0.94`, `macro_f1` not below 0.9414; 100% of blocks have explainable status; 100% of detected unsafe fixes blocked.
3. Negative-corpus regression gate passes (Phase 4 baseline held or improved).
4. UI design review sign-off recorded; critical-bug list (from FORMAT_FIX_PLAN open items + HEADING_AND_NORMCONTROL Block A/B + graphify follow-up) is empty.

SC-2 is **dual-source** per Phase 9 D-E-05:
- (a) zoo raw-ML floor: `linear_svm_production` row in `results/reports/classical_zoo_<ts>/results.csv` clears `weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.86` (raw-ML basis; the zoo does NOT include postprocess rules)
- (b) production after-rules floor: latest `results/metrics/<svm_run>.json["after_rules"]` clears `weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.9414` (full audit pipeline including postprocess)
- BOTH must pass for SC-2 acceptance.

**Out of scope for Phase 8** (strict — no scope creep, no re-opening prior phases):

- New ML training, new rule profiles, new CLI commands, new UI sections, new test fixtures (beyond what Phase 4/9 already shipped).
- Anything that re-touches `src/` code from Phases 1-7+9.
- Release engineering (PyPI packaging, install docs beyond README, demo recordings). Deferred to a v1.0-release follow-up phase if needed.

</domain>

<decisions>
## Implementation Decisions

### A — Acceptance harness shape

- **D-A-01:** Acceptance gate lives in the existing `Makefile` as a new `milestone-acceptance` target. Mirrors Phase 4 `regression-gate` + Phase 9 `compare-classical-acceptance` patterns (`PYTHON ?= python3`, real-tab indent, sub-target chaining). Single command: `make milestone-acceptance`. Exit 0 = milestone PASS; non-zero = FAIL with the first failing sub-target halting the chain.
- **D-A-02:** `make milestone-acceptance` chains FOUR sub-targets, one per SC, in order:
  1. **SC-1 sub-target** — invokes `tests/test_milestone_acceptance_sc1.py` via pytest. End-to-end run on representative DOCX corpus (extract → features → SVM predict → rule audit → CSV) using the production CLI pipeline (`python -m src.main audit-docx --apply-safe` on every fixture). Asserts: every fixture produces a report CSV, every report row has a non-empty `status` field, every `safe_fix` had a corresponding rule entry, no fixture crashed.
  2. **SC-2 sub-target** — invokes `make compare-classical-acceptance` (Phase 9 zoo raw-ML floor) AND new `tests/test_milestone_acceptance_sc2_after_rules.py` (production after-rules floor from `results/metrics/<svm_run>.json["after_rules"]`). Both must PASS.
  3. **SC-3 sub-target** — invokes `make regression-gate` (Phase 4 negative-corpus diff-rate against `tests/baselines/negative_corpus.json`). No re-implementation.
  4. **SC-4 sub-target** — invokes `tests/test_milestone_acceptance_sc4.py`. Aggregates prior-phase records: Phase 6 06-DESIGN-REVIEW.md verdict, Phase 7 07-UAT.md status=complete + 0 open gaps, Phase 9 09-UAT (via /gsd-audit-uat or direct read of 09-03-SUMMARY.md), asserts critical-bug-list empty per `/gsd-audit-uat` aggregate.
- **D-A-03:** Each sub-target is independently runnable for triage (`make milestone-acceptance-sc1`, etc.). The chain-version is the gate; the leaves are diagnostic.
- **D-A-04:** A new fast-tier smoke target `make milestone-smoke` (CI-friendly) runs ONLY: (a) SC-1 on the 5MB `tests/fixtures/corpus/{positive,negative}` subset, (b) `make compare-classical-acceptance` from Phase 9, (c) `make regression-gate` from Phase 4, (d) a Streamlit headless launch smoke (new — see C-04 below). The full `make milestone-acceptance` runs slow tier (D-B-01) and is local-only.

### B — SC-1 representative corpus

- **D-B-01:** Two-tier corpus strategy (mirrors Phase 4 Rule 4):
  - **Fast tier (CI-friendly):** `tests/fixtures/corpus/positive/{1.docx, 4.docx}` + `tests/fixtures/corpus/negative/{45.docx, …}` (the 4-file 5MB subset already shipped by Phase 4 Wave E for the GHA gate). Runs in ≤2 minutes.
  - **Slow tier (local-only):** full `positive_examples/` (≥4 DOCX) + full `negative_examples/` (40+ DOCX pairs) + `tests/fixtures/methodical/normocontrol_berger.pdf` (Phase 5 fixture, 1.5MB). Runs in 20-60 minutes depending on file count.
- **D-B-02:** Phase 8 SC-1 acceptance gate = SLOW tier. The fast tier is a smoke that runs in CI; the slow tier runs locally via `make milestone-acceptance`. ROADMAP SC-1 "representative DOCX corpus" is interpreted as the slow-tier full corpus.
- **D-B-03:** No new fixtures introduced by Phase 8. Reuses fixtures locked by Phase 4 + Phase 5 + Phase 7 only. Adding fixtures would constitute scope creep per the phase boundary.

### C — SC-4 design-review consolidation

- **D-C-01:** Consolidate prior-phase design reviews into ONE Phase 8 rollup document, `08-DESIGN-REVIEW-ROLLUP.md`, instead of running a fresh live design-review pass. Rollup sources:
  - Phase 6 `06-DESIGN-REVIEW.md` verdict (approved-with-followups; Phase 6 closed clean)
  - Phase 7 `07-UAT.md` status=complete + 0 open gaps (3 gaps were captured + closed in 07-04 + 07-05)
  - Phase 9 `09-03-SUMMARY.md` UAT 8/8 approved (also recorded informally — no `09-UAT.md` formal artifact exists since Phase 9 used inline UAT approval through 09-03 Task 3 checkpoint)
- **D-C-02:** SC-4 critical-bug-list = empty assertion is mechanised via `/gsd-audit-uat` aggregate output. `tests/test_milestone_acceptance_sc4.py` invokes the SDK's UAT-audit query and asserts the returned `open_critical_count == 0` and `open_high_count == 0` across all phases.
- **D-C-03:** Existing backlog phases 999.1 (ui-tabbed-layout-restoration) + 999.2 (docx-formatting-bugs-list-indent-formula-vars) are NOT critical-bug regressions — they are backlog items captured during Phase 7 UAT for future v1.1 work. SC-4 treats backlog (999.x) as informational, NOT a milestone-blocker. The rollup document explicitly enumerates them under "Deferred to v1.1" with the rationale that v1.0's success metric is "UI usability passes design review AND critical-bug count = 0" — and the 999.x items are cosmetic/feature-add, not critical bugs.
- **D-C-04 (USER ADDITION):** Fast CI tier `make milestone-smoke` ALSO includes a Streamlit headless launch smoke. New test `tests/test_streamlit_smoke.py`: imports app.py (forces `pytest.importorskip("streamlit")`), validates `app.SUPPORTED_UPLOAD_TYPES == ["docx", "pdf"]` (Phase 7 D-04 §3 — already covered by `tests/test_app_upload_contract.py` but echoed here as a milestone-smoke pass-through), and confirms `streamlit run app.py --server.headless=true --server.port 8501` boots to HTTP 200 within 30s before clean shutdown. Catches the regression class where app.py syntax-imports fine in pytest but Streamlit's reactive runtime trips at first reload. Lives in fast tier only.

### D — Milestone-close artifacts

- **D-D-01:** Phase 8 produces `08-VERDICT.md` capturing: 4 SC outcomes (PASS/FAIL + supporting metric + artifact-pointer per criterion), sign-off date (= `make milestone-acceptance` exit-0 timestamp), open follow-ups (= 999.x backlog snapshot), milestone version (`v1.0`). Template TBD by planner — minimal structure: frontmatter + 4 H2 sections (one per SC) + sign-off footer.
- **D-D-02:** Phase 8 also writes `CHANGELOG.md` at repo root. Aggregates Phase 1-9 deliverables by phase, mirroring ROADMAP completed phases. Format: Keep-a-Changelog 1.1.0 with sections `## [v1.0] — YYYY-MM-DD` + per-phase subsections (e.g., `### Phase 1: Engine guardrails & cohesion audit` + bullet list of plan deliverables). No "Added/Changed/Removed" Keep-a-Changelog buckets (the per-phase organisation IS the changelog).
- **D-D-03:** Phase 8 closes with `git tag -a v1.0 -m "Milestone v1.0 — milestone acceptance passed YYYY-MM-DD"` on the commit that lands 08-VERDICT.md + CHANGELOG.md. The tag is annotated (NOT a lightweight tag) so `git describe` works.
- **D-D-04:** NO `pyproject.toml` version bump — repository has no `pyproject.toml`, no `setup.py`, no `VERSION` file. v1.0 lives ONLY in the git tag + CHANGELOG.md + 08-VERDICT.md + ROADMAP milestone frontmatter (milestone: v1.0, milestone_name: milestone — already set). PyPI packaging is deferred to a v1.0-release follow-up phase if/when public distribution is on the table.

### E — Open Questions resolved post-research (amended 2026-05-16)

08-RESEARCH.md surfaced 5 open questions + 1 prior-phase gap that the original discuss-phase did not address. Resolutions:

- **D-E-01 (OQ-1 — SC-4 assertion mechanism):** Direct file-read assertions, NOT a non-existent `gsd-sdk query audit.uat-aggregate`. `tests/test_milestone_acceptance_sc4.py` reads each phase's `*-UAT.md` frontmatter (asserts `status: complete`) AND greps for any `severity: blocker` or `severity: high` lines (asserts zero matches). Separately reads `06-DESIGN-REVIEW.md` and asserts the verdict line per D-E-02 below. Phase 9 has no formal `09-UAT.md` (UAT was inline in 09-03 Task 3 checkpoint per 09-03-SUMMARY.md); SC-4 test reads `09-03-SUMMARY.md` for the UAT 8/8 record AND grep-asserts zero `severity: blocker|high` lines across the file. This amends D-C-02: the locked field names `open_critical_count == 0` + `open_high_count == 0` are now interpreted as the grep-counted-zero result on `severity: (blocker|high)` lines. No new GSD-tooling work introduced; no new CJS handlers.

- **D-E-02 (Phase 6 design-review sign-off gap):** Synthesise from `06-05-SUMMARY.md`. Phase 6 closed cleanly with the SUMMARY recording the design-review outcome as "approved-with-followups". `08-DESIGN-REVIEW-ROLLUP.md` documents this in a Phase 6 retroactive-sign-off subsection citing the SUMMARY's recorded verdict. No backfill commit on `06-DESIGN-REVIEW.md` (would touch a closed phase's artifact and risk scope creep). No fresh live design-review pass (D-C-01 consolidation decision preserved).

- **D-E-03 (OQ-2 — `make milestone-acceptance` sub-target order):** SC-3 → SC-1 → SC-2 → SC-4. Cheapest fail-fast first per researcher recommendation:
  - SC-3 (`make regression-gate`) is the cheapest existing target — runs in ~1380s but is purely diff-rate computation on a 3-pair Option D subset.
  - SC-1 next — full-corpus DOCX run is the most expensive operation (~20-60 min on slow tier); running second means an SC-3 failure short-circuits before SC-1 burns the budget.
  - SC-2 third — depends on Phase 9 zoo run + production training metrics file already on disk.
  - SC-4 last — pure file-read assertions, fastest (<1 min); placement at the end means signoff happens after the heavy work passes.

- **D-E-04 (OQ-4 — SC-2 after-rules sub-test strategy):** Conservative — read latest `results/metrics/evaluation_*.json` produced by an earlier `python -m src.main train` invocation. If no such file exists, sub-test skips with an informative `pytest.skip("Run 'python -m src.main train' first; SC-2 after-rules half requires production training metrics. See D-E-04.")`. Aggressive option (sub-test invokes `train` itself before asserting) rejected: training is slow + the milestone-acceptance harness should not retrain production models as a side-effect.

- **D-E-05 (OQ-3 — `08-VERDICT.md` template):** No template exists in `$HOME/.claude/get-shit-done/templates/`. Planner creates the template inline as part of Plan 08-Wave-N (the close wave). Minimal shape: frontmatter (phase: 08, milestone: v1.0, status: signed|unsigned, signoff_date: ISO8601) + 5 H2 sections (one per SC) + sign-off footer + open-followups appendix listing 999.x backlog. Planner may extract this as a reusable template at `$HOME/.claude/get-shit-done/templates/VERDICT.md` IF a future milestone repeats the pattern — out of scope for v1.0.

- **D-E-06 (OQ-5 — CHANGELOG.md phase ordering within v1.0 block):** Newest-first (Keep-a-Changelog 1.1.0 canonical). Inside `## [v1.0] — YYYY-MM-DD`, subsections by phase in reverse chronological order of phase-close date: Phase 9 (2026-05-16) → Phase 7 (2026-05-15) → Phase 6 (2026-05-15) → Phase 5 (2026-05-14) → Phase 4 (2026-05-14) → Phase 3 (2026-05-13) → Phase 2 (2026-05-12) → Phase 1 (2026-05-12). Phase 8 (this phase) appears as the milestone-close gate at the top, NOT as a separate phase entry — its deliverables ARE the VERDICT + CHANGELOG itself.

- **D-E-07 (pytest.mark.slow registration):** Add a 3-line `pytest.ini` at repo root (NOT pyproject.toml — D-D-04 preserves "no pyproject.toml"; NOT setup.cfg). Content:
  ```
  [pytest]
  markers =
      slow: marks tests as slow (deselect with '-m "not slow"')
  ```
  Phase 8 Wave 1 creates this file. Existing `@pytest.mark.slow` decorators on `test_per_model_metric_floor` (Plan 09-01) start being recognised; PytestUnknownMarkWarning disappears.

- **D-E-08 (SC-1 invocation correction — research finding):** D-A-02 said the SC-1 sub-target invokes `python -m src.main audit-docx --apply-safe` on every fixture. Research clarified that `audit-docx` does NOT have `--apply-safe` (that flag is on `format-docx`). The right Python abstraction is `src.inference.application_service.process_document(input_path, model_choice, mode, profile_path)` — wires extract → predict → audit → safe-format in one call. SC-1 sub-test calls `process_document` directly via Python (not subprocess), iterates over fixtures, asserts per-fixture artifacts exist + non-empty status fields. This amends D-A-02 sub-target 1 contract: SC-1 is a pytest test that calls the Python API, not a Make shell loop over CLI invocations.

### Claude's Discretion

The following implementation details are NOT locked. Researcher and planner have flexibility here:

- **`tests/test_milestone_acceptance_sc1.py` fixture iteration loop shape.** Pytest parametrization on the slow-tier fixture list OR a single-test that loops + asserts at the end. Planner picks per readability.
- **Streamlit headless smoke teardown.** subprocess.Popen with terminate-after-timeout vs uvicorn-style fixture. Researcher should benchmark which approach is more reliable in a 30s budget on CI runners.
- **CHANGELOG.md per-phase bullet density.** Coarse-grained (1 bullet per phase, citing the locked truths) vs fine-grained (1 bullet per plan deliverable). Planner picks; researcher should propose a length budget per phase.
- **Open-follow-ups extraction in 08-VERDICT.md.** Auto-extract from `999.x backlog` ROADMAP sections vs hand-curate a v1.1 priority list. Probably auto-extract with a Note section.
- **08-VERDICT.md template.** No template exists in `$HOME/.claude/get-shit-done/templates/`. Researcher should propose a structure that mirrors 06-DESIGN-REVIEW.md's verdict-checklist style + frontmatter.
- **Order of `make milestone-acceptance` sub-target chain.** Currently D-A-02 specifies SC-1 → SC-2 → SC-3 → SC-4. Planner may reorder for fail-fast efficiency (e.g., SC-3 regression-gate is the cheapest existing target; running it first short-circuits a full corpus run if regression is broken). Researcher should propose.
- **Whether SC-2 after-rules sub-test re-trains the production model.** Conservative: read latest `results/metrics/<svm_run>.json["after_rules"]` produced by an earlier `python -m src.main train` invocation. If no such file exists, sub-test skips with an informative message asking the operator to run `python -m src.main train` first. Aggressive: sub-test invokes `train` itself before asserting. Conservative is recommended (training is slow; milestone-acceptance shouldn't include a fresh training run).
- **Streamlit headless port handling.** Hardcode 8501 vs use a dynamic free port discovery to avoid CI flakes. Researcher should propose.

</decisions>

<specifics>
## Specific Ideas

- **Reuse `make regression-gate` verbatim for SC-3.** Per Phase 4 Wave E close, this gate is live and validated end-to-end via 2 PRs (clean + designed-regression). Phase 8 SC-3 sub-target literally executes `make regression-gate` and asserts exit 0. No re-implementation.
- **Reuse `make compare-classical-acceptance` verbatim for SC-2 raw-ML half.** Phase 9 already exposed this Make target. SC-2 sub-target invokes it + asserts exit 0 + reads the latest `results/reports/classical_zoo_<ts>/results.csv` for `linear_svm_production` row to cross-check.
- **After-rules SC-2 floor source-of-truth.** Per Phase 9 D-E-05: `results/metrics/<svm_run>.json["after_rules"]["weighted avg"]["f1-score"]` and `["macro avg"]["f1-score"]`. Latest file located via `sorted(METRICS_DIR.glob("evaluation_*.json"), reverse=True)[0]`. Skip if no file.
- **`/gsd-audit-uat` aggregate query.** Phase 8 SC-4 test invokes `gsd-sdk query audit.uat-aggregate --json` (or equivalent — researcher to confirm command exists, otherwise propose a wrapping CJS handler). Returns per-phase status + counts of open critical/high gaps. Assert `open_critical_count == 0`.
- **CHANGELOG.md per-phase entry sketch (researcher-tunable):**
  ```
  ## [v1.0] — 2026-05-XX

  ### Phase 1: Engine guardrails & cohesion audit (2026-05-12)
  - Stops body_text rules on Heading/TOC/List-Paragraph/Caption-styled paragraphs (REQ-fix-style-guards).
  - 67 INFERRED edges audited; cohesion score 0.06 → improved (REQ-rule-engine-cohesion-audit).

  ### Phase 2: Bibliography & list semantics (2026-05-12)
  - Bibliography lists detected + single shared numId enforced (REQ-list-conservative-handling).
  - Ambiguous lists routed to review.

  ...
  ```
  Per-phase prose paragraph + 2-3 bullet points of locked truths from each phase's CONTEXT/SUMMARY.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level

- `/Users/fedorova.van/experiments/gost_formatter/CLAUDE.md` — TDD discipline, minimal-code, no-orphan rules, no scope creep, no AI-attribution commit trailers
- `/Users/fedorova.van/experiments/gost_formatter/.planning/ROADMAP.md` — Phase 8 detail (line 170) + Success Criteria + Execution Order `7 → 9 → 8`
- `/Users/fedorova.van/experiments/gost_formatter/.planning/REQUIREMENTS.md` — REQ-mvp-acceptance is the existing requirement; REQ-classical-model-zoo (added Phase 9) is referenced by SC-2. No new REQs added by Phase 8.
- `/Users/fedorova.van/experiments/gost_formatter/.planning/PROJECT.md` — Core value statement; the success metric "UI usability passes design review AND critical-bug count = 0" is the milestone-close gate Phase 8 must verify
- `/Users/fedorova.van/experiments/gost_formatter/.planning/STATE.md` — current focus already set to Phase 8

### Prior-phase records (Phase 8 reads, does NOT modify)

- `.planning/phases/06-streamlit-ui-redesign/06-DESIGN-REVIEW.md` — Phase 6 design-review verdict (consolidate into 08-DESIGN-REVIEW-ROLLUP.md)
- `.planning/phases/07-pdf-text-layer-audit-slice/07-UAT.md` — status=complete, 7/7 pass, 3 gaps closed (consolidate)
- `.planning/phases/09-classical-model-zoo-lr-svm-complementnb-randomforest-histgbm/09-03-SUMMARY.md` — UAT 8/8 approved 2026-05-16 (consolidate)
- `.planning/phases/09-classical-model-zoo-lr-svm-complementnb-randomforest-histgbm/09-CONTEXT.md` D-E-05 — dual-source SC-2 acceptance design

### Codebase (read-only context for researcher)

- `Makefile` — existing `regression-gate` (Phase 4) + `compare-classical-acceptance` (Phase 9) targets to mirror; PYTHON ?= python3 variable
- `tests/test_rules_quality_acceptance.py` — Phase 4 schema-lint pattern (mirror)
- `tests/test_compare_classical_acceptance.py` — Phase 9 acceptance pattern (mirror)
- `tests/test_phase_8_sc2_acceptance.py` — Phase 9 standalone SC-2 gate (Phase 8 invokes this via the SC-2 sub-target)
- `src/main.py` — CLI dispatcher (the SC-1 sub-target invokes `python -m src.main audit-docx --apply-safe ...` on every fixture)
- `src/evaluate.py` — produces `results/metrics/<svm_run>.json` with `after_rules` block (SC-2 after-rules half reads this)
- `tests/fixtures/corpus/{positive,negative}/*.docx` — fast-tier SC-1 corpus
- `positive_examples/` + `negative_examples/` (gitignored) — slow-tier SC-1 corpus
- `tests/baselines/negative_corpus.json` — Phase 4 regression-gate baseline

### Backlog / out-of-scope reference

- `.planning/phases/999.1-ui-tabbed-layout-restoration/` + `.planning/phases/999.2-docx-formatting-bugs-list-indent-formula-vars/` — captured during Phase 7 UAT; informational to Phase 8 SC-4 (NOT critical-bug regressions; deferred to v1.1)

</canonical_refs>

<folded_todos>
## Folded Todos

None — no pending todos matched Phase 8 scope per typical `gsd-sdk query todo.match-phase 08` flow. (To be confirmed by researcher.)

</folded_todos>

<deferred>
## Deferred Ideas (Out of Scope for Phase 8)

Captured during discussion; do NOT pursue in Phase 8. Promote to v1.1 / 999.x backlog if persistent value:

- **PyPI packaging.** `pyproject.toml` authoring, build metadata, publishing — release-engineering work, not milestone-acceptance.
- **Public README polish for external users.** Current README is developer-facing; v1.0 release may want a separate user-onboarding README.
- **Demo recordings / screencast.** Visual demonstration of the audit flow; release marketing.
- **PyPI version sync via `pyproject.toml` or `__version__` constant.** No version-string source-of-truth in repo today. D-D-04 keeps it that way; if a future plan adds `pyproject.toml`, version syncing becomes part of that plan.
- **Fresh design-review pass on the integrated UI.** Considered in Area C; rejected (consolidation is sufficient; each phase's UI was already reviewed at close).
- **Backlog 999.1 (tabbed UI restoration) + 999.2 (DOCX formatter indent bugs).** Phase 8 SC-4 explicitly treats backlog as informational. v1.1 entry points.
- **`/gsd-audit-uat` wrapper if SDK query doesn't expose aggregate JSON.** If `gsd-sdk query audit.uat-aggregate --json` does not exist, researcher should propose a small CJS handler to add — but the implementation lands in a `.planning/`-tooling sub-plan within Phase 8 Wave 1, not as a new GSD-tool phase.
- **Full corpus regression-gate in CI.** Phase 4 Rule 4 already locks this OUT (subset in CI, full local-only); Phase 8 preserves that boundary.

</deferred>

<success_criteria_traceback>
## Phase 8 Success Criteria (locked, derived from ROADMAP + discuss-phase decisions)

The 4 ROADMAP SC + 1 milestone-close SC:

1. **SC-1 (end-to-end corpus run):** `make milestone-acceptance-sc1` (slow-tier full corpus) exits 0; every fixture produces a non-empty report CSV; every report row has a non-empty `status`; every `safe_fix` action has a corresponding rule; no fixture crashed.
2. **SC-2 (ML quality dual-source):** `make milestone-acceptance-sc2` exits 0 = BOTH (a) zoo CSV `linear_svm_production` row clears `weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.86` AND (b) production `results/metrics/<svm_run>.json["after_rules"]` clears `weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.9414`. 100% of test blocks have non-null `status`; 100% of `unsafe` rules carry the documented blocker reason.
3. **SC-3 (negative-corpus regression):** `make regression-gate` exits 0. Per-pair diff-rate ceilings held per `tests/baselines/negative_corpus.json`.
4. **SC-4 (design-review consolidation + critical-bug closure):** `08-DESIGN-REVIEW-ROLLUP.md` written + signed; `tests/test_milestone_acceptance_sc4.py` asserts `/gsd-audit-uat` aggregate reports `open_critical_count == 0 AND open_high_count == 0` across Phases 1-7 + 9.
5. **SC-5 (milestone-close artifacts — Phase-8-internal):** `08-VERDICT.md` written; `CHANGELOG.md` written at repo root; `git tag -a v1.0` created on the closing commit; ROADMAP Phase 8 marked complete; STATE.md milestone v1.0 marked closed.

All five must be GREEN for milestone-v1.0 close.

</success_criteria_traceback>
