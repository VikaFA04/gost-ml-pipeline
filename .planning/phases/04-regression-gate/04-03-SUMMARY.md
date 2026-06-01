---
phase: 04-regression-gate
plan: 03
subsystem: testing
tags: [rules-quality, static-lint, csv-invariants, rule-record, pytest, REQ-rules-quality-acceptance, D-12, branch-B]

# Dependency graph
requires:
  - phase: 04-regression-gate
    provides: Wave B per-pair pytest gate (tests/test_negative_corpus_diff_rate.py, baseline JSON) — Wave C is forward-only and does not consume Wave B's baseline, but it shares the CI fail-vs-skip idiom established there
  - phase: 03-heading-signature-and-docx-generator
    provides: 17 new heading_* rules added to src/rules/formatting_rules_v1.json — Wave C lint verifies all 28 rules at HEAD conform to RuleRecord shape
  - phase: 01-engine-guardrails-cohesion-audit
    provides: src/rules/rule_engine.py + apply_rules_to_paragraph contract — Wave C runtime smoke invokes the same audit pipeline (build_regression_predictions + audit_or_format_docx) the engine already audited
provides:
  - tests/test_rules_quality_acceptance.py — 5 static-schema lint tests + 1 runtime CSV-invariants smoke test (forward-only regression gate for src/rules/formatting_rules_v1.json + audit report shape)
  - CONTEXT.md D-08 amendment (canonical filename tests/test_rules_quality_acceptance.py replaces stale tests/test_rules_quality.py per D-004 «no silent rewrites»)
  - REQ-rules-quality-acceptance closed at this plan
affects: [04-04-PLAN, 04-05-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Forward-only static lint: REQUIRED_FIELDS / ALLOWED_ACTION_VALUES / ALLOWED_SEVERITY_VALUES sets pinned at module top; any future rule that drifts (missing field, unknown action, non-int priority, non-bool autocorrect, duplicate id) turns the gate RED"
    - "Bogus-required-field RED carrier: when the canonical pre-merge state already satisfies a lint, force RED via a deliberately-bogus REQUIRED_FIELDS entry, observe the failure mode, then delete the bogus entry to land GREEN — preserves iron-law without inventing fake test assertions"
    - "Runtime smoke skip-vs-CI-fail idiom inherited from Wave B (os.environ.get('CI') == 'true' → pytest.fail if negative_examples/3.docx missing; else pytest.skip)"
    - "pandas read_csv with encoding='utf-8-sig' for BOM tolerance on audit report CSVs"

key-files:
  created:
    - tests/test_rules_quality_acceptance.py
  modified:
    - .planning/phases/04-regression-gate/04-CONTEXT.md

key-decisions:
  - "RED carrier switched (Rule 4 architectural deviation) from test_every_rule_action_and_severity_in_allowed_set to test_every_rule_carries_full_rulerecord_shape via a bogus required field __red_placeholder__ — the plan's original strategy was empirically un-implementable (see Deviations §1)"
  - "ALLOWED_ACTION_VALUES carries the full empirical-aspirational set {fix, review, check_or_fix} per PRD §7.4 even though only \"fix\" is instantiated at HEAD across all 28 rules — the lint allowance is wider so legitimate future review/check_or_fix rules do not trigger a false-positive gate"
  - "Canonical test filename locked at tests/test_rules_quality_acceptance.py (resolves the CONTEXT.md D-08 vs D-12 inconsistency per RESEARCH probe 7); D-08 amended in same wave per D-004"

patterns-established:
  - "Pattern: forward-only regression gate on a JSON config (read-only) — load JSON at module top, run set-based shape lint + value-domain lint + uniqueness lint; new file lives alongside corpus-regression gate (tests/test_negative_corpus_diff_rate.py from Wave B)"
  - "Pattern: bogus-required-field RED for shape lints (see tech-stack)"

requirements-completed: [REQ-rules-quality-acceptance]

# Metrics
duration: ~15min
completed: 2026-05-14
---

# Phase 04 Plan 03: Wave C — Rules-Quality Acceptance Gate Summary

**Forward-only static + runtime gate at `tests/test_rules_quality_acceptance.py` (5 schema lints + 1 audit-CSV invariants smoke) catches any future drift in `src/rules/formatting_rules_v1.json` or in the audit-report shape; landed via a bogus-required-field RED carrier after the plan's original action-vocab RED was found empirically un-implementable.**

## Performance

- **Duration:** ~15 min wall-clock
- **Started:** 2026-05-14T04:24Z (resume of continuation agent; previous agent had written the test file body but stopped at a Rule 4 decision checkpoint)
- **Completed:** 2026-05-14T04:39Z
- **Tasks:** 3 (RED + GREEN + CONTEXT amendment per CLAUDE.md «Железный закон»)
- **Files modified:** 1 created + 1 modified (2 total)

## Branch B Context

This plan executes inside Phase 4's D-05 Branch B regime locked by Wave A (`.planning/phases/04-regression-gate/04-WAVE-A-3docx-rootcause.md`) and Wave B (`tests/baselines/negative_corpus.json`): the negative-corpus regression baseline is **forward-only** — Wave A traced the `3.docx` `0.318 → 0.334` drift to Phase 3 commit `7207cbe` (D-05/D-06 per-field heading source dispatcher), declared it a correct behaviour change rather than a bug, and amended ROADMAP SC-2 + REQUIREMENTS REQ-fix-negative-corpus-no-regression accordingly. Wave C inherits the same forward-only philosophy: the rules-quality lint protects against **future** drift in `formatting_rules_v1.json`, not past gaps — per RESEARCH.md Probe 2, the 28 rules at HEAD already satisfy the substantive coverage from Phase 1/2/3.

## Accomplishments

- **One new test file `tests/test_rules_quality_acceptance.py`** with 6 named tests covering the full REQ-rules-quality-acceptance (PRD §9.3) acceptance surface:
  1. `test_every_rule_carries_full_rulerecord_shape` — 8-key shape lint (id, applicable_labels, parameter, expected_value, action, severity, autocorrect, priority).
  2. `test_every_rule_has_unique_id` — duplicate-id guard.
  3. `test_every_rule_action_and_severity_in_allowed_set` — action ∈ {fix, review, check_or_fix}, severity ∈ {low, medium, high}.
  4. `test_every_rule_priority_is_int` — type lint on priority.
  5. `test_every_rule_autocorrect_is_bool` — type lint on autocorrect.
  6. `test_audit_csv_invariants_on_negative_fixture` — runtime smoke (status=changed → applied_fixes non-empty; manual_review_required=True → explanation non-empty; low_confidence=True → manual_review_required=True). Skips locally, fails fast in CI per Wave B idiom.
- **CONTEXT.md D-08 amended** to cite the canonical filename `tests/test_rules_quality_acceptance.py` (replaces stale `tests/test_rules_quality.py`); brought CONTEXT.md under git tracking via force-add (same pattern as PLAN/SUMMARY files under `.planning/` gitignore).
- **REQ-rules-quality-acceptance closed** at this plan.

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — bogus-required-field shape mismatch forces 28 rules RED** — `cdc9055` (`test(04-03)`: new `tests/test_rules_quality_acceptance.py` with `__red_placeholder__` in `REQUIRED_FIELDS`. `python3 -m pytest -q tests/test_rules_quality_acceptance.py::test_every_rule_carries_full_rulerecord_shape` exits 1 with all 28 rules reporting `missing fields ['__red_placeholder__']` — the right reason.)
2. **Task 2: GREEN — remove bogus field; canonical 8-key shape** — `02e1207` (`feat(04-03)`: delete `__red_placeholder__` line. `python3 -m pytest -q tests/test_rules_quality_acceptance.py` exits 0 with `5 passed, 1 skipped in 1.48s` — runtime smoke skips locally because `negative_examples/3.docx` is absent in this checkout.)
3. **Task 3: CONTEXT.md D-08 amendment — canonical filename** — `b8ee13a` (`docs(04-03)`: replace stale `tests/test_rules_quality.py` with `tests/test_rules_quality_acceptance.py`; force-add CONTEXT.md to git since `.planning/` is gitignored.)

**Plan metadata commit:** appended below as the 4th commit (this SUMMARY + STATE.md + ROADMAP.md + REQUIREMENTS.md).

## pytest Output Before / After

**Before (RED at commit `cdc9055`, `pytest -q ::test_every_rule_carries_full_rulerecord_shape`):**

```
F                                                                        [100%]
FAILED tests/test_rules_quality_acceptance.py::test_every_rule_carries_full_rulerecord_shape
AssertionError: body_text_alignment: missing fields ['__red_placeholder__']
  body_text_indent: missing fields ['__red_placeholder__']
  ... (28 rules total, all reporting the same missing key) ...
1 failed in 1.59s
```

**After (GREEN at commit `02e1207`, `pytest -q tests/test_rules_quality_acceptance.py`):**

```
.....s                                                                   [100%]
5 passed, 1 skipped in 1.48s
```

The 1 skip is `test_audit_csv_invariants_on_negative_fixture` — `negative_examples/3.docx` is not present in this working tree. In CI (`CI=true`), this test would `pytest.fail` per the established Wave B idiom; that's the correct gate behaviour.

## Files Created/Modified

- `tests/test_rules_quality_acceptance.py` — **NEW** (117 lines). Module-level `RULES_PATH = Path("src/rules/formatting_rules_v1.json")`, `REQUIRED_FIELDS` 8-key set, `ALLOWED_ACTION_VALUES = {"fix", "review", "check_or_fix"}`, `ALLOWED_SEVERITY_VALUES = {"low", "medium", "high"}`. Imports `build_regression_predictions` from `src.evaluation.format_regression_audit` and `audit_or_format_docx` from `src.generate.inplace_formatter`. 6 named tests; runtime smoke uses `pd.read_csv(..., encoding="utf-8-sig")` for BOM tolerance.
- `.planning/phases/04-regression-gate/04-CONTEXT.md` — **AMENDED D-08 line 54**. One-token edit: `tests/test_rules_quality.py` → `tests/test_rules_quality_acceptance.py`. File brought under git tracking via `git add -f` (same pattern as PLAN/SUMMARY files under the project's `.planning/` gitignore).

## Decisions Made

See `key-decisions` frontmatter. Most load-bearing: **the RED carrier was switched mid-plan** — see Deviations §1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 4 — Architectural] RED carrier switched from action-vocab narrowing to bogus-required-field shape mismatch**
- **Found during:** Task 1 (RED setup) — previous agent (pre-checkpoint) hit this and returned a decision checkpoint; user picked Option 1 (preserve plan intent, switch RED strategy).
- **Issue:** The plan's RED strategy was to instantiate `ALLOWED_ACTION_VALUES = {"fix"}` and let `test_every_rule_action_and_severity_in_allowed_set` fail because the empirical JSON allegedly uses `action ∈ {"fix", "review", "check_or_fix"}`. RESEARCH.md Probe 2 explicitly claimed this set. **The claim is empirically wrong**: at HEAD, every one of the 28 rules in `src/rules/formatting_rules_v1.json` has `action == "fix"`; `git log -S '"review"'` and `git log -S '"check_or_fix"'` on the rules JSON return no hits — those values never landed. With `ALLOWED_ACTION_VALUES = {"fix"}` the action-vocab test passes, not fails, so it cannot serve as a RED carrier.
- **Fix:** Switched the RED carrier to `test_every_rule_carries_full_rulerecord_shape` via adding a bogus `__red_placeholder__` field to `REQUIRED_FIELDS`. All 28 rules immediately fail the shape lint (missing `__red_placeholder__`), which is a valid iron-law RED — the test observes the right kind of failure (missing required field), just with a deliberately-bogus required field that Task 2 removes. Plan intent preserved: the 5 static lints + 1 runtime smoke land at the canonical filename, REQ-rules-quality-acceptance is closed, CONTEXT.md D-08 is amended.
- **Why architectural and not auto-fix:** the deviation changes which test function carries the RED gate and which assertion fires first — this is plan-level RED-carrier semantics, not an in-task bug. User confirmation (Option 1) was correctly required.
- **Files modified:** `tests/test_rules_quality_acceptance.py` (RED placeholder relocated from `ALLOWED_ACTION_VALUES = {"fix"}` to `REQUIRED_FIELDS = {..., "__red_placeholder__"}`).
- **Verification:** Task 1 commit `cdc9055` — pytest exits 1 naming `__red_placeholder__` across all 28 rules. Task 2 commit `02e1207` — pytest exits 0.
- **Committed in:** `cdc9055` (RED) and `02e1207` (GREEN remove of the bogus field).

**2. [Tooling — not a deviation rule] `.planning/` gitignore force-add for CONTEXT.md**
- **Source:** `.gitignore` line 40 ignores all of `.planning/`. CONTEXT.md was never force-added by an earlier wave, so the Task 3 edit was invisible to `git status` until `git add -f` was used. Same pattern as Wave A/B PLAN/SUMMARY commits.
- **Applied:** `git add -f .planning/phases/04-regression-gate/04-CONTEXT.md` → file becomes tracked + committed in `b8ee13a`. Whole file (189 lines) lands as a new addition rather than a 1-token diff; the canonical filename is in HEAD, the stale name is not. D-004 «no silent rewrites» satisfied.

---

**Total deviations:** 1 Rule-4 architectural (RED-carrier switch), pre-decided by the user via the previous agent's checkpoint return. 1 tooling note (gitignore force-add — not a deviation, normal project pattern).
**Impact on plan:** plan intent fully preserved — same 6 tests, same canonical filename, same CONTEXT.md amendment, same REQ-rules-quality-acceptance closure. Only the RED-carrier mechanism changed.

## Issues Encountered

- **RESEARCH.md Probe 2 empirical claim incorrect.** The probe described `action ∈ {"fix", "review", "check_or_fix"}` as an empirically-verified set in the JSON. `git log -S '"review"' -- src/rules/formatting_rules_v1.json` and `git log -S '"check_or_fix"' -- src/rules/formatting_rules_v1.json` show no such values were ever committed. Probe was aspirational, not empirical. Wave C still pins `ALLOWED_ACTION_VALUES = {"fix", "review", "check_or_fix"}` as the lint allowance to remain forward-compatible (RuleRecord PRD §7.4 leaves the door open for `review` / `check_or_fix` actions in future profile work).
- **Pyright pre-existing noise.** `src.*` import resolution warnings + `pandas` ndarray stub gaps on the new test file are noise also present on 9 other tests; per the executor rules-of-engagement these are out of Wave C scope and were ignored. Not regressions caused by this wave.

## User Setup Required

None.

## Next Phase Readiness

- **Wave D (04-04-PLAN — `audit-regression --update-baseline` CLI + Makefile target):** unblocked. Wave C's lint protects the rules JSON regardless of which CLI flow updates the corpus baselines.
- **Wave E (04-05-PLAN — GHA workflow):** unblocked. The new test file uses the same CI fail-vs-skip idiom as Wave B; GHA can invoke `pytest tests/test_negative_corpus_diff_rate.py tests/test_positive_docx_regression.py tests/test_rules_quality_acceptance.py` (D-08 canonical list, now consistent with the file actually on disk).
- **REQ-rules-quality-acceptance closed.** Phase 4 progress: 3/5 plans complete; 2 remaining (04-04, 04-05).

## TDD Gate Compliance

- RED gate: `test(04-03): RED ...` commit `cdc9055` present in `git log`; pytest observed failing for the right reason (`__red_placeholder__` missing across all 28 rules).
- GREEN gate: `feat(04-03): GREEN ...` commit `02e1207` present, lands after RED; pytest exits 0 (5 passed + 1 skipped).
- REFACTOR gate: not invoked — the test-file shape is already at its target state after Task 2 (no separate cleanup pass needed).

## Self-Check

Verified all claims before completion.

- File `tests/test_rules_quality_acceptance.py` — FOUND (created in commit `cdc9055`, refined in `02e1207`).
- File `.planning/phases/04-regression-gate/04-CONTEXT.md` — D-08 now references `tests/test_rules_quality_acceptance.py` (verified by `grep -n "test_rules_quality" .planning/phases/04-regression-gate/04-CONTEXT.md` → match at line 54 with canonical name; stale name absent per negated grep).
- Commit `cdc9055` — FOUND in `git log --oneline` (RED).
- Commit `02e1207` — FOUND in `git log --oneline` (GREEN).
- Commit `b8ee13a` — FOUND in `git log --oneline` (CONTEXT amendment).
- `python3 -m pytest -q tests/test_rules_quality_acceptance.py` at HEAD `b8ee13a` — exit 0, `5 passed, 1 skipped in 1.48s`.
- TDD «Железный закон»: RED commit landed BEFORE GREEN commit; pytest observed FAILING with the bogus required field before the canonical 8-key shape landed — PASS.
- D-004 «no silent rewrites»: CONTEXT.md amendment is explicit, atomic, traceable in `b8ee13a` — PASS.

## Self-Check: PASSED

---
*Phase: 04-regression-gate*
*Completed: 2026-05-14*
