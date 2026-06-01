---
phase: 04-regression-gate
plan: 02
subsystem: testing
tags: [regression-gate, pytest, baseline-json, per-pair-gate, D-05, branch-B, option-D]

# Dependency graph
requires:
  - phase: 04-regression-gate
    provides: Wave A D-05 Branch B locked ceilings + 4-doc subset + naming-convention gotcha (04-WAVE-A-3docx-rootcause.md)
  - phase: 03-heading-signature-and-docx-generator
    provides: Phase 3 D-05/D-06 per-field heading source dispatcher (commit 7207cbe — root cause of 3.docx +0.025 drift since FORMAT_FIX_PLAN Этап 8)
  - phase: 02-bibliography-and-list-semantics
    provides: Phase 2 D-15 negative-corpus diff-rate ≤ 0.4781 aggregate baseline (carried forward into _metadata.aggregate_mean_ceiling)
provides:
  - tests/baselines/negative_corpus.json (per-pair baseline ceilings, 3-pair Option D subset, profile_id=gost_7_32_2017)
  - 3 new pytest gate tests in tests/test_negative_corpus_diff_rate.py (D-03 triple metric: field_mismatch_delta, after_diff_rate, aggregate mean)
  - Branch B amendments to ROADMAP.md Phase 4 SC-2 + REQUIREMENTS.md REQ-fix-negative-corpus-no-regression citing Phase 3 D-05/D-06
  - Wave A artefact "Wave B amendment (2026-05-14)" section recording subset reduction 4→3 per Option D
affects: [04-03-PLAN, 04-04-PLAN, 04-05-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-pair baseline JSON loaded by pytest via BASELINE_PATH = Path('tests/baselines/...'); ceilings live ONLY in the JSON (no parallel constant in test source)"
    - "CI fail-vs-skip idiom: missing corpus → pytest.fail in CI, pytest.skip locally"
    - "Helper-extracted audit driver: _run_audit_for_subset(subset_filenames) filters frame['negative'].isin(...) after a full-corpus audit (Pitfall 1 mitigation — no audit_negative_directory whitelist param)"
    - "Atomic Branch B commit: baseline JSON + ROADMAP + REQUIREMENTS + Wave A artefact land together (Pitfall 3 audit trail; D-004 no silent rewrites)"

key-files:
  created:
    - tests/baselines/negative_corpus.json
  modified:
    - tests/test_negative_corpus_diff_rate.py
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
    - .planning/phases/04-regression-gate/04-WAVE-A-3docx-rootcause.md

key-decisions:
  - "Option D subset reduction from 4 to 3 pairs: tmp* generator-test artefacts (tmp5x0alx_2_baseline_*, tmp9dp7t40y_transformer_*) dropped — they are 1.docx duplicates from generator runs, not corpus regression candidates"
  - "Final 3-pair subset (negative-column filenames): 3_formatted_20260413_194927.docx, 45_formatted_20260414_220339.docx, 4_formatted_20260413_185420.docx — covers the 3 unique non-58/59 positives in the corpus"
  - "Per-pair ceilings = empirical HEAD values from regression_audit_phase4_worst_offenders.csv rounded to 6 decimals (Pitfall 2): 3.docx pair 0.359712/630, 45.docx pair 0.412162/372, 4.docx pair 0.163743/165"
  - "Aggregate mean ceiling stays at 0.4781 (D-15 unchanged): 3-pair subset mean 0.311872 ≤ 0.4781 — no aggregate-ceiling amendment needed"
  - "D-05 Branch B amendments atomic with baseline JSON GREEN commit: ROADMAP SC-2 + REQUIREMENTS line + Wave A artefact all land in commit e100a44"

patterns-established:
  - "Pattern: 3-pair per-pair gate (D-03 triple metric) — field_mismatch_delta ≤ 0 AND after_field_mismatches ≤ ceiling AND after_diff_rate ≤ ceiling, aggregate mean ≤ 0.4781"
  - "Pattern: subset_filenames + per-pair dict keys are negative-column filenames (formatted output names), NOT positive-column originating filenames — matches audits_to_frame() column semantics (Wave A flag #1)"

requirements-completed: [REQ-fix-negative-corpus-no-regression]

# Metrics
duration: ~80min
completed: 2026-05-14
---

# Phase 04 Plan 02: Wave B — Per-Pair Regression Gate (D-05 Branch B, Option D) Summary

**Locked 3-pair per-pair negative-corpus regression gate at tests/baselines/negative_corpus.json (D-03 triple metric, 0.359712/630 for 3.docx pair per Wave A Branch B) with atomic ROADMAP + REQUIREMENTS + Wave A artefact amendment; pytest -q exits 0 (3 passed in 1285.20s).**

## Performance

- **Duration:** ~80 min wall-clock (dominated by two ~16-21 min full-corpus pytest runs — one for RED observation, one for GREEN verification)
- **Started:** 2026-05-14T03:06:43Z
- **Completed:** 2026-05-14T04:24:24Z
- **Tasks:** 2 (RED + GREEN per CLAUDE.md «Железный закон»)
- **Files modified:** 1 created + 4 modified (5 total)

## Accomplishments
- **Phase-1 aggregate-only gate replaced by 3-metric per-pair gate** at `tests/test_negative_corpus_diff_rate.py`. Three named tests now enforce: `field_mismatch_delta ≤ 0` AND `after_field_mismatches ≤ ceiling` per pair, `after_diff_rate ≤ ceiling` per pair, and subset aggregate mean ≤ `_metadata.aggregate_mean_ceiling`. The Phase 1 baseline constant `PHASE_1_BASELINE_MEAN_DIFF_RATE = 0.4781` is deleted from source — it lives ONLY in the JSON now (D-06 no parallel duplicate).
- **Per-pair ceilings locked at `tests/baselines/negative_corpus.json`** with real Wave-A-locked empirical values rounded to 6 decimals (Pitfall 2): 3.docx pair `0.359712/630`, 45.docx pair `0.412162/372`, 4.docx pair `0.163743/165`. Subset mean `0.311872 ≤ 0.4781`.
- **D-05 Branch B amendments atomic with GREEN commit:** ROADMAP Phase 4 SC-2 + REQUIREMENTS REQ-fix-negative-corpus-no-regression both cite Phase 3 D-05/D-06 commit 7207cbe + reference the Wave A artefact. No silent rewrite (Pitfall 3, D-004).
- **Wave A artefact amended in same atomic commit** with a new "Wave B amendment (2026-05-14)" section recording the 4→3 subset reduction per Option D — full audit trail.
- **REQ-fix-negative-corpus-no-regression closed** via this plan (the requirement's «no negative-corpus pair regresses» bar is now enforced by the pytest gate).

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — failing per-pair tests against placeholder baseline** — `e457708` (test: new tests/baselines/negative_corpus.json with 0.0/0 placeholder ceilings + 3-pair subset; new tests/test_negative_corpus_diff_rate.py body with helper extraction + CI fail-vs-skip; old aggregate-only test + Phase-1 baseline constant deleted. `pytest -q` exits non-zero with 3 failures for the right reasons.)
2. **Task 2: GREEN — real Wave A ceilings + Branch B amendments + Wave A artefact amendment** — `e100a44` (feat: 4-file atomic commit — baseline JSON real values + ROADMAP SC-2 + REQUIREMENTS line + Wave A artefact "Wave B amendment" section. `pytest -q` exits 0 with 3 passed in 1285.20s.)

**Plan metadata commit:** (this SUMMARY + STATE.md + ROADMAP.md plan-progress) — appended below.

## Files Created/Modified
- `tests/baselines/negative_corpus.json` — **NEW**. Per-pair regression baseline: `_metadata` (schema_version=1, aggregate_mean_ceiling=0.4781, profile_id=gost_7_32_2017, subset_filenames=3-element list) + 3 per-pair entries with `after_diff_rate_ceiling`, `field_mismatch_ceiling`, `recorded_at`, `profile_id`, `notes`.
- `tests/test_negative_corpus_diff_rate.py` — **REWRITTEN body**. Old aggregate-only `test_negative_corpus_diff_rate_phase2_baseline` + `PHASE_1_BASELINE_MEAN_DIFF_RATE` removed; new module-level `BASELINE_PATH`, `_load_baseline()`, `_run_audit_for_subset()` helpers + 3 named tests covering D-03 triple metric.
- `.planning/ROADMAP.md` — **AMENDED Phase 4 SC-2 line**. "`3.docx` pair returns to ≤ 0.318" → "`3.docx` pair ≤ 0.359712, others tracked in tests/baselines/negative_corpus.json" + citation of Phase 3 D-05/D-06 commit 7207cbe + reference to Wave A artefact.
- `.planning/REQUIREMENTS.md` — **AMENDED REQ-fix-negative-corpus-no-regression line**. Mirrors ROADMAP wording with same citation.
- `.planning/phases/04-regression-gate/04-WAVE-A-3docx-rootcause.md` — **APPENDED "Wave B amendment (2026-05-14)" section** documenting subset reduction 4→3 (tmp* artefacts dropped per Option D), final subset, and resulting mean 0.311872 ≤ 0.4781 (no aggregate amendment needed).

## Decisions Made
See `key-decisions` frontmatter. Most load-bearing:
- **Option D subset reduction (4 → 3 pairs)**: rationale — the two `tmp*` candidates in Wave A's original subset (`tmp5x0alx_2_baseline_*`, `tmp9dp7t40y_transformer_*`) are 1.docx duplicates from generator-test runs, not corpus regression candidates. Removing them brings the subset mean (0.311872) under the aggregate ceiling (0.4781), making aggregate-ceiling amendment unnecessary and keeping the gate consistent with corpus reality.
- **Subset / dict-key convention = negative-column filenames** (Wave A flag #1 mitigation): `audits_to_frame` puts formatted-output names in `frame["negative"]`. The pytest gate does `frame[frame["negative"].isin(subset_filenames)]`; per-pair lookups do `baseline[row["negative"]]`. Both must match negative-column filenames — `"3.docx"` would never match either. This contradicts plan 04-02's literal `"3.docx"` example but was explicitly flagged in the Wave A artefact and BINDING in the executor prompt's overrides.

## Deviations from Plan

### Auto-fixed Issues

None — all deviations were pre-resolved by the executor prompt's `<plan_overrides_BINDING>` section (subset 4→3 per Option D; subset_filenames + per-pair keys use negative-column filenames; per-pair ceiling table per Wave A artefact; atomic 4-file commit with Wave A artefact amendment per override #6).

### Plan-vs-Override Reconciliation (applied per executor prompt)

**1. [Override #1/#2 — Subset reduction 4 → 3 pairs (Option D)]**
- **Source:** executor prompt `<plan_overrides_BINDING>` items 1 + 2, citing Wave A flag #4 (aggregate-mean collision) and Wave A flag #1 (naming-convention gotcha).
- **Plan said:** 4-doc subset with literal `"3.docx"` example.
- **Override said:** 3-doc subset with formatted-negative filenames; tmp* artefacts dropped.
- **Applied:** subset_filenames = `["3_formatted_20260413_194927.docx", "45_formatted_20260414_220339.docx", "4_formatted_20260413_185420.docx"]`; per-pair dict keys match.
- **Impact:** Aggregate-mean amendment to ROADMAP avoided (0.311872 ≤ 0.4781).

**2. [Override #3 — Per-pair ceilings per CSV rounded to 6 decimals]**
- **Source:** override #3 table + Pitfall 2 (round to 6 decimals).
- **Applied:** 3.docx pair `0.359712/630`; 45.docx pair `0.412162/372`; 4.docx pair `0.163743/165`. Verified by `python3 csv` reader: every value matches the CSV exactly with no rounding needed at 6 decimals.

**3. [Override #5 + #6 — Atomic 4-file commit (baseline + ROADMAP + REQUIREMENTS + Wave A artefact)]**
- **Source:** override #5 (Branch B amendments same commit) + override #6 (Wave A artefact amendment same commit per D-004).
- **Applied:** commit `e100a44` lists exactly these 4 files (verified via `git log -1 --name-only`).
- **Rationale:** D-004 «no silent rewrites» — subset reduction 4→3 is visible in the same audit trail as the gate it constrains.

**4. [Override #7 — Task 1 verify clause adjustments]**
- **Plan said:** `assert len(subset_filenames) == 4`, `subset_filenames[0] == "3.docx"`.
- **Override said:** `len == 3`, `subset_filenames[0] == "3_formatted_20260413_194927.docx"`.
- **Applied:** inline JSON shape checks ran against override values; baseline JSON written to match.

---

**Total deviations:** 0 auto-fixed (Rules 1–3 not triggered). 4 reconciliations applied verbatim from binding overrides (informational — these were pre-resolved by the orchestrator review, not discovered during execution).
**Impact on plan:** All reconciliations preserve plan intent (per-pair gate, D-03 triple metric, Branch B atomic amendment). The 4→3 subset reduction strictly improves the gate (no aggregate-ceiling lift required).

## Issues Encountered

- **Bash background pytest output capture quirk:** initial `python3 -m pytest > /tmp/log 2>&1; echo "EXIT=$?"` chain reported `EXIT=0` after the RED run because the trailing `echo` always exits 0; the pytest verdict `3 failed` was the load-bearing signal. Resolved by reading the captured `tail` output (showed 3 failures with correct error messages: `after_diff_rate=0.359712 > ceiling=0.000000` etc.). Pytest's own exit code for GREEN was confirmed `0` via task-notification `summary` field.
- **`.planning/` gitignore force-add:** `.planning/` is in `.gitignore` (line 40 of `.gitignore`) so `git add .planning/...` returns "paths are ignored". Same pattern as Wave A — resolved via `git add -f`. Tooling pattern, not a deviation.
- **pytest runtime ~16-21 min/run:** RED 983s, GREEN 1285s. Each test triggers a full negative-corpus audit (`audit_negative_directory` with no `limit`). RESEARCH.md Pitfall 1 mitigation (full-corpus audit + frame filter) is the intentional trade-off — no whitelist param exists. Acceptable for a gate that runs once per fix-track PR; not a candidate for local TDD iteration.

## User Setup Required

None.

## Next Phase Readiness

- **Wave C (04-03-PLAN — rules-quality-acceptance tests) can start immediately.** No blockers from Wave B.
- **Wave D (04-04-PLAN — `audit-regression --update-baseline` CLI):** Wave B's baseline JSON shape is the canonical artefact Wave D's `--update-baseline` flag will write. `_metadata.schema_version = 1` pins the contract.
- **Wave E (04-05-PLAN — CI gate):** the pytest gate is now CI-ready (CI-fail-vs-skip idiom in place — `os.environ.get("CI") == "true"` → `pytest.fail` if corpus missing, else `skip`).
- **REQ-fix-negative-corpus-no-regression closed** at this plan — see ROADMAP/REQUIREMENTS amendment.

## Self-Check

Verified all claims before completion.

- File `tests/baselines/negative_corpus.json` — FOUND (created in commit `e457708`, updated in `e100a44`).
- File `tests/test_negative_corpus_diff_rate.py` — FOUND (body replaced in commit `e457708`).
- File `.planning/ROADMAP.md` — Phase 4 SC-2 amended in commit `e100a44` (verified by `grep -n "Phase 4 D-05 Branch B" .planning/ROADMAP.md` → match at line 88).
- File `.planning/REQUIREMENTS.md` — REQ-fix-negative-corpus-no-regression amended in commit `e100a44` (verified by `grep -n "Phase 4 D-05 Branch B" .planning/REQUIREMENTS.md` → match at line 89).
- File `.planning/phases/04-regression-gate/04-WAVE-A-3docx-rootcause.md` — "Wave B amendment (2026-05-14)" appended in commit `e100a44` (verified by `grep -n "Wave B amendment (2026-05-14)"` → match at line 157).
- Commit `e457708` — FOUND in `git log` (RED).
- Commit `e100a44` — FOUND in `git log` (GREEN).
- `git log -1 --name-only e100a44` lists all 4 files: `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/phases/04-regression-gate/04-WAVE-A-3docx-rootcause.md`, `tests/baselines/negative_corpus.json` — confirmed.
- `pytest -q tests/test_negative_corpus_diff_rate.py` at HEAD `e100a44` — exit 0, "3 passed in 1285.20s" (full output captured at `/tmp/green_pytest.txt`).
- Inline JSON shape check: 3-element subset_filenames; first element = `3_formatted_20260413_194927.docx`; every name in subset present as top-level dict key; per-pair ceilings match override #3 table exactly — PASS.
- TDD «Железный закон»: RED commit landed BEFORE GREEN commit; pytest observed FAILING for the right reason (placeholder ceilings 0.0 vs real values) before any production-value baseline was written — PASS.

## TDD Gate Compliance

- RED gate: `test(04-02): RED ...` commit `e457708` present in `git log`.
- GREEN gate: `feat(04-02): GREEN ...` commit `e100a44` present, lands after RED.
- REFACTOR gate: not invoked — the new test file shape is already at its target state (helper extraction + 3 tests + CI idiom done in Task 1 RED), no refactor needed at GREEN.

## Self-Check: PASSED

---
*Phase: 04-regression-gate*
*Completed: 2026-05-14*
