# Phase 4: Regression gate - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Convert the negative-corpus diff-rate and rules-quality acceptance signals into a tracked, blocking gate that fires on every fix-track change. Reverse the `3.docx` drift (`0.318 → 0.334`) found in `FORMAT_FIX_PLAN` Этап 8 — either by root-cause fix to `≤ 0.318` or by amending `ROADMAP` success criterion 2 if the drift is a legitimate Phase 2 / Phase 3 behaviour change.

In scope:
1. **Per-pair baseline file** — `tests/baselines/negative_corpus.json`, versioned, one entry per negative-corpus pair, machine-readable, diff-friendly in PR review.
2. **Per-pair pytest gate** — extend `tests/test_negative_corpus_diff_rate.py` to read baseline JSON and enforce per-pair `after_diff_rate ≤ ceiling`, per-pair `field_mismatch_delta ≤ 0`, and aggregate `mean ≤ 0.4781` on a pinned subset that includes `3.docx`.
3. **3.docx investigation wave** — root-cause hunt on the `0.318 → 0.334` drift before locking the per-pair ceiling. Outcome decides between a fix landing in Phase 4 and a `ROADMAP` amendment.
4. **RuleRecord acceptance** — static lint of `formatting_rules_v1.json` + runtime test on negative corpus that every violation surfaces, every `applied_fix` surfaces, low-confidence blocks carry `manual_review_required=true` with non-empty reason.
5. **`audit-regression --update-baseline --reason "<text>"`** — CLI flag for intentional baseline updates with mandatory rationale; commit message references the change. Compliant with D-004 (no silent rewrites).
6. **Local invocation surface** — `make regression-gate` Makefile target wrapping the CLI + pytest run; documented in `README.md` / `CONTRIBUTING.md` as "run before every fix-track PR".
7. **CI gate** — `.github/workflows/` GitHub Actions workflow that runs the fast pytest gate on every PR. Pinned subset only; full-corpus stays manual via Makefile.

Out of scope for Phase 4:
- Full-corpus nightly cron / scheduled CI runs (later milestone).
- Multi-Python-version matrix in GHA (single supported version only).
- Rewriting `audit-regression` CLI internals — only additive `--update-baseline` / `--reason` flags + per-pair baseline read path.
- Rewriting `format_regression_audit.py` columns — gate reads existing `after_diff_rate`, `field_mismatch_delta`, `diff_delta`.
- 58.docx / 59.docx — practice reports, excluded from GOST gate per Phase 3 D-08.
- New rule additions or rule-engine refactor — gate verifies existing rules; doesn't redesign them.

</domain>

<decisions>
## Implementation Decisions

### Area 1 — Baseline storage + per-pair gate shape

- **D-01:** **Per-pair JSON baseline at `tests/baselines/negative_corpus.json`.** Schema per entry keyed by negative-corpus filename: `after_diff_rate_ceiling`, `field_mismatch_ceiling`, `recorded_at`, `profile_id`, `notes`. Versioned in git, diff-friendly in PR review, machine-readable by both pytest gate and `audit-regression --update-baseline`. Rejected: CSV snapshot (column-ordering diff noise), inline pytest constants (data and gate logic conflated, baseline updates touch test code).
- **D-02:** **Pinned explicit subset for fast pytest gate, must include `3.docx`.** Replace Phase 2 `limit=4` first-by-filename pattern (brittle, doesn't guarantee `3.docx` is in subset) with an explicit list pinned by purpose: `3.docx` (the regression target), 1–2 worst offenders by current `after_diff_rate`, 1 sanity-stable doc. Researcher enumerates the worst-offender candidates during plan-phase from a full-corpus run. Full corpus runs only via Makefile target / nightly cron later.
- **D-03:** **Triple metric per pair, all enforced in the fast pytest gate.**
  - Per-pair `after_diff_rate ≤ baseline[name].after_diff_rate_ceiling`.
  - Per-pair `field_mismatch_delta ≤ 0` (no field-level regression even when `diff_rate` rounds flat — addresses CLAUDE.md "сверяй её формулу и округление" rule).
  - Aggregate `mean(after_diff_rate) ≤ 0.4781` carry-forward from Phase 2 D-15 as a cheap smoke check on the subset.
  Rejected: `diff_delta < 0` (must-improve gate) — too strict for non-format-fix PRs.

### Area 2 — 3.docx remediation route

- **D-04:** **Dedicated investigation wave inside Phase 4 — root cause before lock.** Wave A: targeted audit on `3.docx` (`audit-regression --limit 1` against pinned negative + before/after style-diff dump) + git bisect of FORMAT_FIX_PLAN Этап 2–7 commits to identify which fix-track change introduced the `+0.016` drift. Wave B: outcome-driven action (D-05). Rejected: accept `0.334` silently (contradicts ROADMAP success criterion 2 verbatim), decimal phase 4.1 split (risk of slip while gate locks bad baseline), offline-only spike (loses traceability).
- **D-05:** **Conditional success bar driven by root cause** — mirrors Phase 3 D-08 precedent for amending requirements rather than papering over them.
  - **Root cause is a bug** → land targeted fix; `3.docx` baseline ceiling locked at `0.318`; ROADMAP success criterion 2 untouched.
  - **Root cause is a correct Phase 2 (bibliography `numId`) or Phase 3 (heading signature) behaviour change** → amend `ROADMAP` success criterion 2 with rationale (cite the Phase 2/3 decision that changed semantics); lock baseline at the root-cause-justified ceiling (e.g. `0.334`); update `REQUIREMENTS.md` REQ-fix-negative-corpus-no-regression. D-004 (no silent rewrites) applies to ROADMAP too — amendment requires explicit commit with rationale, never an implicit relax of the gate.

### Area 3 — Gate execution surface (triple enforcement)

- **D-06:** **pytest gate is the authoritative enforcement layer.** Extend `tests/test_negative_corpus_diff_rate.py` to read `tests/baselines/negative_corpus.json` and run the three D-03 assertions. Pinned subset per D-02. Existing Phase 2 mean-only test becomes a sub-assertion of the new shape (no parallel duplicate test).
- **D-07:** **Makefile target `make regression-gate`** — wrapper that runs `audit-regression` CLI (with `--limit` matching the pinned subset size) + the pytest gate. Documented in `README.md` and a new `CONTRIBUTING.md` as the canonical pre-PR step for any fix-track change. Cheap to add, easy to invoke locally.
- **D-08:** **GitHub Actions workflow at `.github/workflows/regression-gate.yml`** runs the **fast pytest gate only** on every PR. Action checks out repo, installs Python deps, runs `pytest tests/test_negative_corpus_diff_rate.py tests/test_positive_docx_regression.py tests/test_rules_quality_acceptance.py`. No full-corpus CI runs in Phase 4 — those stay manual via Makefile and may move to nightly cron in a later milestone. Single supported Python version; no matrix.
- **D-09:** **GHA wiring lands in the LAST wave of Phase 4.** Wave order: (Wave A) `3.docx` investigation → (Wave B) per-pair baseline JSON + pytest gate extension → (Wave C) RuleRecord static-lint + runtime test → (Wave D) Makefile target + README/CONTRIBUTING wiring → (Wave E) GHA workflow. Each prior wave produces something locally runnable; CI only wires what's already proven.
- **D-10:** **Rejected: pre-commit hook.** Multi-minute audit slows commits, can't enforce cross-machine. Doc-only checklist is honour-system, weaker still. Both worse than pytest + Make.

### Area 4 — REQ-rules-quality-acceptance + baseline-update workflow

- **D-11:** **Pre-plan researcher audit of current rules-quality coverage** before plan-phase locks wave count. Researcher reads `src/rules/formatting_rules_v1.json` + `src/rules/rule_engine.py` + sample audit CSVs from `results/reports/` and reports: which rules already match the `RuleRecord` schema, which don't; whether `low_confidence → manual_review_required` already wires through `apply_rules_to_paragraph`; whether `applied_fixes` already includes every fix path. Phase 1/2/3 may already cover most of REQ-rules-quality-acceptance — Phase 4 only fills the gaps.
- **D-12:** **Static lint + runtime test, both required.**
  - **Static** (new `tests/test_rules_quality_acceptance.py` or extension of an existing test file — plan-phase decides): load `formatting_rules_v1.json`, assert every entry has full `RuleRecord` shape per `intel/requirements.md` §REQ-rule-schema / PRD §7.4 (`parameter`, `expected_value` or null, `autocorrect` bool, `selector_class`, etc.).
  - **Runtime**: run audit on a curated fixture or negative corpus subset, assert every violation surfaces in the per-block CSV, every `applied_fixes` field is non-empty when status=`changed`, every `manual_review_required=true` row has non-empty `explanation`.
  Rejected: static-only (doesn't prove low-conf wiring), runtime-only (misses rules that don't fire on the corpus).
- **D-13:** **`audit-regression --update-baseline <path> --reason "<text>"` for intentional baseline changes.** CLI reads current run's per-pair results, writes new JSON at `<path>`, prints a diff (old ceiling → new ceiling per pair), refuses to run if `--reason` is empty or missing. Commit message must reference the baseline change and the `--reason` text. Compliant with D-004 (no silent rewrites) and the CLAUDE.md rule "Сохраняй regression-audit summary в JSON для автоматизации". Rejected: hand-edit JSON (no guard against accidental loosening), `pytest --regenerate-baselines` snapshot pattern (a flaky audit run becomes baseline — too easy to weaken the gate).

### Claude's Discretion
- Exact JSON field names in `negative_corpus.json` (`after_diff_rate_ceiling` vs `ceiling`, `recorded_at` vs `timestamp`) — plan-phase / researcher decide.
- Pinned subset's exact composition beyond `3.docx` — researcher enumerates worst offenders from a full-corpus run before plan-phase locks the list.
- GHA workflow filename (`regression-gate.yml` vs `ci.yml`) and job naming — plan-phase decides.
- Static-lint test file location (`tests/test_rules_quality_acceptance.py` vs extending `tests/test_rules.py` if it exists) — researcher decides after scanning current tests.
- Whether `--update-baseline` adds an interactive `[y/N]` confirm prompt in addition to `--reason`, or only the flag — plan-phase decides.
- Exact `--reason` minimum length / format check (free-text vs `<TICKET-ID>: <text>`) — plan-phase decides.
- Whether the Makefile target also runs `tests/test_positive_docx_regression.py` (Phase 3 invariant) or only the negative gate — researcher decides; defaulting to "run both" is the safer call.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & success criteria
- `.planning/ROADMAP.md` §"Phase 4: Regression gate" — phase goal, depends-on (Phase 2 + Phase 3), success criteria 1–4. **Note: success criterion 2 may be amended in Phase 4 Wave B per D-05 if `3.docx` root cause is a legit behaviour change.**
- `.planning/REQUIREMENTS.md` REQ-fix-negative-corpus-no-regression, REQ-audit-regression-cli, REQ-rules-quality-acceptance.

### Project-level
- `.planning/PROJECT.md` §"Key Decisions" — D-004 (safe-only autocorrection: no silent rewrites — load-bearing for D-05 and D-13).
- `CLAUDE.md` "Принципы исполнения" — "Выноси долгий regression-аудит в отдельную CLI-команду с CSV-отчетом" (CLI already exists, Phase 4 only extends), "Сохраняй regression-audit summary в JSON для автоматизации" (baseline JSON design), "Перед опорой на численную метрику стороннего инструмента сверяй её формулу и округление" (motivates per-pair `field_mismatch_delta ≤ 0` in D-03), "При выборе gate-варианта по success criterion из ROADMAP/REQUIREMENTS отдавай предпочтение опции, обусловленной выявлением корневой причины" (motivates D-05).
- `.planning/intel/decisions.md` D-001…D-007.
- `.planning/intel/constraints.md` C-NFR-EXPLAINABILITY — drives D-12 runtime test (every status explainable).
- `.planning/intel/requirements.md` §REQ-rules-quality-acceptance (PRD §9.3), §REQ-rule-schema (PRD §7.4 RuleRecord) — drives D-12 static-lint schema.
- `.planning/intel/context.md` "Critical pipeline defects — DOCX formatter (FORMAT_FIX_PLAN baseline)" — Этапы 1–9, particularly Этап 8 (`3.docx` drift, baseline diff_rate 0.4781).

### Phase 1 / 2 / 3 carry-forward
- `.planning/phases/01-engine-guardrails-cohesion-audit/01-CONTEXT.md` — Phase 1 root cause A semantics (`None == inherited`, no direct rewrite). Phase 4 audit must not regress this.
- `.planning/phases/02-bibliography-list-semantics/02-CONTEXT.md` D-15 — existing automated mean-only gate at `0.4781` on `limit=4` subset. D-03 extends this.
- `.planning/phases/02-bibliography-list-semantics/02-VERIFICATION.md` — Phase 2 positive-baseline relaxation rationale (which the per-pair gate inherits).
- `.planning/phases/03-heading-signature-and-docx-generator/03-CONTEXT.md` D-07 (positive-corpus heading invariant, runs alongside negative gate) and D-08 (precedent for amending REQUIREMENTS/ROADMAP when a requirement turns out to be wrong-scope — mirrored by D-05).
- `.planning/phases/03-heading-signature-and-docx-generator/03-VERIFICATION.md` — Phase 3 success-criteria empirical verification (negative-corpus diff-rate `≤ 0.4781` preserved).

### Defect catalog
- `.planning/FORMAT_FIX_PLAN.md` Этап 8 — `3.docx` pair `0.318 → 0.334` drift; the Wave A investigation target.
- `.planning/HEADING_AND_NORMCONTROL_PLAN.md` — historical heading defect catalog; relevant only if Wave A bisect lands on a Phase 3 commit.

### Source code (read before modifying)
- `src/main.py` `cmd_audit_regression` (line 201) and argparse setup (line 350) — extend with `--update-baseline <path>` and `--reason <text>` flags (D-13). Reuse existing `audits_to_frame`, `default_regression_audit_report_path`, summary-JSON write path.
- `src/evaluation/format_regression_audit.py` `audit_negative_directory` + `audits_to_frame` (line 1–194) — gate reads existing frame columns: `after_diff_rate`, `field_mismatch_delta`, `diff_delta`, `formatter_changed`, `formatter_error`. **Do NOT redesign columns.**
- `src/rules/formatting_rules_v1.json` — D-12 static-lint target. Researcher reads first to enumerate current `RuleRecord` coverage.
- `src/rules/rule_engine.py` `apply_rules_to_paragraph` — D-12 runtime test reads its output for `manual_review_required` wiring. Phase 3 D-05/D-06 already shaped the heading-rule branch — Phase 4 must not regress.
- `tests/test_negative_corpus_diff_rate.py` — Phase 2 D-15 gate; D-06 extends in place (no parallel duplicate test). Existing `PHASE_1_BASELINE_MEAN_DIFF_RATE = 0.4781` constant moves into the baseline-JSON `aggregate_mean_ceiling` field.
- `tests/test_positive_docx_regression.py` — Phase 3-extended; D-07 runs it as part of `make regression-gate` (per discretion default). Phase 4 leaves it intact.

### Test corpus
- `positive_examples/{1,4}.docx` — GOST-decorated subset, confirmed in Phase 3. Phase 4 doesn't widen this.
- `negative_examples/3.docx`, `negative_examples/3_formatted_*.docx` — primary investigation target.
- Worst-offender candidates beyond `3.docx` — researcher enumerates from `audit-regression` full-corpus run pre-plan-phase.

### New artefacts Phase 4 introduces
- `tests/baselines/negative_corpus.json` (NEW) — per-pair ceiling JSON, schema per D-01.
- `tests/test_rules_quality_acceptance.py` (NEW, name tentative) — static lint + runtime test per D-12.
- `Makefile` (NEW or extended) — `regression-gate` target per D-07.
- `.github/workflows/regression-gate.yml` (NEW) — fast pytest gate on PR per D-08.
- `CONTRIBUTING.md` (NEW or extended) — pre-PR step documented per D-07.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cmd_audit_regression` in `src/main.py` — emits per-pair CSV + summary JSON, supports `--limit`, `--profile-id`, `--progress`. Phase 4 only adds `--update-baseline` + `--reason`; no rewrite.
- `audits_to_frame` columns (`after_diff_rate`, `field_mismatch_delta`, `diff_delta`, `formatter_changed`, `formatter_error`) — gate reads these directly. No new columns needed.
- Phase 2 D-15 pytest gate (`tests/test_negative_corpus_diff_rate.py`) — extended in place by D-06, not replaced. Existing `PHASE_1_BASELINE_MEAN_DIFF_RATE = 0.4781` moves into baseline JSON aggregate field.
- Phase 3 D-07 positive-corpus invariant (`tests/test_positive_docx_regression.py`) — runs alongside negative gate inside `make regression-gate` per discretion default.

### Established Patterns
- "Long audit → CLI with CSV + summary JSON" — CLAUDE.md mandate, already shipped. Phase 4 inherits.
- "Pinned subset gate at `limit=4` for fast feedback" — Phase 2 D-15 pattern. D-02 hardens it from filename-sorted to explicit pinned list.
- "Inherited mismatch → review, direct mismatch → autofix" — Phase 3 D-05/D-06 rule-engine policy. D-12 runtime test verifies this still holds after Phase 4 changes.
- "Amend REQUIREMENTS/ROADMAP when discussion reveals wrong premise" — Phase 3 D-08 precedent. D-05 inherits.

### Integration Points
- `src/main.py` argparse — new flags wire through the existing subparser stack.
- `tests/baselines/` — new directory; sibling to `tests/fixtures/`.
- `Makefile`, `.github/workflows/`, `CONTRIBUTING.md` — new top-level project files. Phase 4 introduces these for the first time in this project.

### Creative Options the Architecture Enables
- Per-pair `notes` field in baseline JSON can carry the `--reason` text of the last update — full audit trail without grep-ing git log.
- Researcher's pre-plan rules-quality audit (D-11) could surface that REQ-rules-quality-acceptance is mostly satisfied by Phase 1/2/3 already, shrinking Phase 4 scope by one wave.

</code_context>

<specifics>
## Specific Ideas

- Per-pair baseline JSON entry shape (sketch, plan-phase finalizes exact keys):
  ```json
  {
    "3.docx": {
      "after_diff_rate_ceiling": 0.318,
      "field_mismatch_ceiling": 12,
      "recorded_at": "2026-05-13T00:00:00Z",
      "profile_id": "gost_7_32_2017",
      "notes": "Phase 1 baseline (FORMAT_FIX_PLAN Этап 8). Phase 4 Wave A target if drift unresolved."
    }
  }
  ```
- `--update-baseline` CLI sketch: `python -m src.main audit-regression --positive-dir positive_examples --negative-dir negative_examples --limit 4 --update-baseline tests/baselines/negative_corpus.json --reason "FIX-03 Wave B: revert 3.docx drift to 0.318 (root cause: ...)"`
- GHA workflow sketch: single job, `runs-on: ubuntu-latest`, install deps, run only the three pytest files, fail PR if any assertion fires.

</specifics>

<deferred>
## Deferred Ideas

- **Full-corpus nightly cron in GHA** — D-08 explicitly scopes Phase 4 GHA to fast pytest only. Nightly full-corpus run is a later-milestone CI hardening.
- **Multi-Python-version matrix in GHA** — out of scope; single supported version only.
- **`--regenerate-baselines` pytest snapshot mode** — rejected in D-13 (too easy to silently weaken). Could be revisited if `--update-baseline` proves too friction-heavy in practice.
- **Pre-commit hook for the gate** — rejected in D-10 (slow, hard to enforce cross-machine).
- **Visual regression dashboard / drift trend over time** — out of scope; v2.
- **Auto-bisect tool that finds the regressing commit when a pair drifts** — out of scope; Wave A does this by hand for `3.docx` only.

</deferred>

---

*Phase: 04-regression-gate*
*Context gathered: 2026-05-13*
