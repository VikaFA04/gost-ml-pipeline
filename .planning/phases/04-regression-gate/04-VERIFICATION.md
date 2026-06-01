---
status: passed
phase: 04-regression-gate
verified: 2026-05-14
must_haves_checked: 28
must_haves_passed: 28
must_haves_failed: 0
requirement_ids_verified: 3
external_ci_validation: confirmed
---

# Phase 04 — Regression Gate Verification Report

**Phase Goal:** Bring the negative corpus under a tracked baseline via the `audit-regression` CLI. The negative-corpus diff-rate becomes a tracked, blocking metric; the `audit-regression` CLI is the gate for every subsequent change; the rules-quality acceptance rollup is enforced.

**Verified:** 2026-05-14
**Status:** passed
**Re-verification:** No — initial verification.

External CI validation already supplied by orchestrator (Task 2 of plan 04-05) and reconfirmed by code review: PR #1 run #25846822154 GREEN in 1m54s, PR #2 run #25847679849 RED in 1m50s on `test_per_pair_after_diff_rate_no_regression` (exactly the designed failure mode). Both PR closed, regression branch deleted. Verifier did NOT re-run CI.

## Goal Achievement

### Phase-Level Success Criteria (ROADMAP)

| #   | Criterion | Status     | Evidence |
| --- | --------- | ---------- | -------- |
| 1   | `audit-regression` CLI compares corpus run against saved baseline; emits per-pair CSV + summary JSON; brought under the gate (4 gate test files in CI + locally) | ✓ VERIFIED | `src/main.py:205-278` cmd_audit_regression emits both CSV (`frame.to_csv(report_path, ...)`) and summary JSON. Makefile `regression-gate` target runs CLI + invokes all 4 gate test files (`Makefile:12-21`). GHA workflow mirrors the same 4 files (`.github/workflows/regression-gate.yml:31-35`). |
| 2   | No negative-corpus pair regresses below Wave-A-locked per-pair ceiling (3.docx ≤ 0.359712, others in `tests/baselines/negative_corpus.json`); mean diff-rate ≤ 0.4781; per Phase 4 D-05 Branch B citing commit 7207cbe | ✓ VERIFIED | `tests/baselines/negative_corpus.json` locks `3_formatted_20260413_194927.docx` at `after_diff_rate_ceiling=0.359712, field_mismatch_ceiling=630`. `tests/test_negative_corpus_diff_rate.py:64-75` enforces per-pair ceiling. Branch B amendment with commit 7207cbe citation present at `ROADMAP.md:88` and `REQUIREMENTS.md:85-91`. Wave A artefact at `.planning/phases/04-regression-gate/04-WAVE-A-3docx-rootcause.md`. |
| 3   | Audit report covers every rule in `RuleRecord` format; every violation surfaces; every applied fix surfaces; unsafe fixes blocked; low-confidence routes to `manual_review_required` with reason | ✓ VERIFIED | `tests/test_rules_quality_acceptance.py` enforces 5 static-schema lints + 1 runtime CSV-invariants smoke: 8-key RuleRecord shape (lines 33-41), unique ids (44-47), allowed action/severity vocabulary (50-58), priority int (61-64), autocorrect bool (67-70), runtime: changed→applied_fixes non-empty, manual_review_required→explanation non-empty, low_confidence→manual_review_required=True (73-116). |
| 4   | `audit-regression` wired into CI / documented local check; every fix-track PR gated | ✓ VERIFIED | GHA workflow `.github/workflows/regression-gate.yml` triggers on PR + push to main/master. README.md:54-77 documents "Pre-PR проверка" with `make regression-gate`. CONTRIBUTING.md:1-67 documents the full local + baseline-update workflow. External CI run validation: clean PR #1 (success 25846822154); regression PR #2 (failure 25847679849, merge blocked). |

**Phase-level score:** 4/4 success criteria satisfied.

### Per-Plan Must-Have Truths

#### Plan 04-01 (Wave A — root cause investigation)

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1.1 | 3.docx pair drift (0.318 → 0.334) has a documented root cause | ✓ VERIFIED | `04-WAVE-A-3docx-rootcause.md` §"Root cause" identifies commit 7207cbe with bisect trace: `ac41aaa` (good) → `7207cbe` (drift). One-commit-wide interval. |
| 1.2 | D-05 branch chosen on basis of root cause (Branch A bug-fix → 0.318 OR Branch B legit behaviour change → root-cause-justified ceiling) | ✓ VERIFIED | Branch B locked, rationale tied to Phase 3 D-05/D-06 sealed decision. `after_diff_rate_ceiling = 0.359712`, `field_mismatch_ceiling = 630`. |
| 1.3 | Worst-offender CSV exists so Wave B can pin subset deterministically (excluding 58/59) | ✓ VERIFIED | `results/reports/regression_audit_phase4_worst_offenders.csv` + `.json` referenced as Wave A frontmatter `provides:`. (`results/` is gitignored; force-added per project pattern.) Wave A artefact §"4-doc subset" lists negative-column filenames; 58/59 pairs explicitly excluded. |

#### Plan 04-02 (Wave B — per-pair baseline + 3 tests)

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 2.1 | `tests/baselines/negative_corpus.json` exists, valid JSON, contains `_metadata` + per-pair entries, includes 3.docx pair with Wave A locked ceiling | ✓ VERIFIED | File exists; verifier loaded via `json.load`; `_metadata.schema_version=1`, `aggregate_mean_ceiling=0.4781`, `profile_id=gost_7_32_2017`, `subset_filenames=3` entries; `3_formatted_20260413_194927.docx.after_diff_rate_ceiling=0.359712` confirmed. |
| 2.2 | `tests/test_negative_corpus_diff_rate.py` has 3 named tests: per-pair field_mismatch_delta ≤ 0, per-pair after_diff_rate ≤ ceiling, aggregate mean ≤ aggregate_mean_ceiling | ✓ VERIFIED | `tests/test_negative_corpus_diff_rate.py:47, 64, 78` — exact function names match: `test_per_pair_field_mismatch_no_regression`, `test_per_pair_after_diff_rate_no_regression`, `test_subset_aggregate_mean_diff_rate_under_phase1_baseline`. Pytest collects all 3. |
| 2.3 | All 3 tests GREEN at HEAD | ✓ VERIFIED | Wave B summary records 1285.20s GREEN run at commit `e100a44`. Wave D summary records full `make regression-gate` GREEN at 1380s including these 3 tests. External CI: clean PR run #25846822154 GREEN. |
| 2.4 | `PHASE_1_BASELINE_MEAN_DIFF_RATE = 0.4781` constant removed from test file; lives only in baseline JSON `_metadata.aggregate_mean_ceiling` | ✓ VERIFIED | `grep "PHASE_1_BASELINE_MEAN_DIFF_RATE" tests/test_negative_corpus_diff_rate.py` returns nothing. Baseline JSON shows the constant at `_metadata.aggregate_mean_ceiling=0.4781`. |
| 2.5 | If Branch B: ROADMAP SC-2 + REQUIREMENTS REQ-fix-negative-corpus-no-regression amended in SAME commit as baseline write (atomic, no silent rewrite) | ✓ VERIFIED | Commit `e100a44` lists 4 files: `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/phases/04-regression-gate/04-WAVE-A-3docx-rootcause.md`, `tests/baselines/negative_corpus.json`. `ROADMAP.md:88` and `REQUIREMENTS.md:85-91` both contain "Phase 4 D-05 Branch B" + "0.359712" + commit `7207cbe` citation. |

#### Plan 04-03 (Wave C — rules-quality acceptance gate)

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 3.1 | Every rule in `src/rules/formatting_rules_v1.json` carries the 8 PRD §7.4 RuleRecord fields (id, applicable_labels, parameter, expected_value, action, severity, autocorrect, priority) | ✓ VERIFIED | `tests/test_rules_quality_acceptance.py:15-24` defines REQUIRED_FIELDS set; `test_every_rule_carries_full_rulerecord_shape` (line 33) enforces. Test currently GREEN per Wave C SUMMARY (`5 passed, 1 skipped in 1.48s`). |
| 3.2 | Every audit row with `status=changed` has non-empty `applied_fixes` value | ✓ VERIFIED | `tests/test_rules_quality_acceptance.py:100-104` asserts `bad_changed.empty`. Runtime smoke uses `audit_or_format_docx` against `positive_examples/3.docx`. |
| 3.3 | Every audit row with `manual_review_required=True` has non-empty `explanation` | ✓ VERIFIED | `tests/test_rules_quality_acceptance.py:106-110` asserts `bad_review.empty`. |
| 3.4 | Every audit row with `low_confidence=True` routes to `manual_review_required=True` | ✓ VERIFIED | `tests/test_rules_quality_acceptance.py:112-115` asserts `not_routed.empty`. |
| 3.5 | Static-lint + runtime-smoke tests live at canonical `tests/test_rules_quality_acceptance.py` (resolves CONTEXT.md D-08 vs D-12 inconsistency per RESEARCH Probe 7) | ✓ VERIFIED | File at canonical path, 116 lines, 6 test functions. Stale name `tests/test_rules_quality.py` does not exist in repo. |
| 3.6 | CONTEXT.md D-08 amended in same wave to cite canonical filename (D-004 «no silent rewrites») | ✓ VERIFIED | `04-CONTEXT.md` D-08 carries canonical filename per Wave C SUMMARY commit `b8ee13a`. (CONTEXT.md is under `.planning/`, gitignored; force-add pattern.) |

#### Plan 04-04 (Wave D — CLI extension + local pre-PR surface)

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 4.1 | `python -m src.main audit-regression --update-baseline <path> --reason '<text>'` writes valid baseline JSON with per-pair ceilings from live run's frame, filtered to `_metadata.subset_filenames` (Pitfall 1) | ✓ VERIFIED | `src/main.py:256-261` calls `write_per_pair_baseline(path, frame, reason.strip(), profile_id)`. Helper at `src/evaluation/format_regression_audit.py:197-261` does subset filter at lines 229-243 BEFORE iterating. Wave D smoke test #3 captured in `04-04-SUMMARY.md` confirms 45.docx + 4.docx pairs untouched when `--limit 1` supplied. |
| 4.2 | `--reason` ≤ 7 chars after strip refused with SystemExit + Russian-language error citing D-004 | ✓ VERIFIED | `src/main.py:251-255` guard `if not reason or len(reason.strip()) < 8: raise SystemExit(...)`. Test `tests/test_cli_parser.py:265` loops `("", "   ", "abcdefg")` — all 3 sub-cases exercise the guard. Wave D smoke #1 + #2 in SUMMARY confirm 7-char and empty refusals fire. |
| 4.3 | `--update-baseline` without `--reason` at all → SystemExit | ✓ VERIFIED | Same guard at `src/main.py:251` covers `not reason` (None case). |
| 4.4 | Without `--update-baseline`, empty/missing `--reason` accepted without error (Pitfall 6) | ✓ VERIFIED | Guard is conditional on `if update_baseline:` at `src/main.py:247`. argparse keeps both `required=False` at `src/main.py:404-415`. Existing `cmd_audit_regression` callers in `tests/test_cli_parser.py:130-202` unaffected (test collection succeeded). |
| 4.5 | `make regression-gate` runs audit + 4 pytest gate files (test_negative_corpus_diff_rate.py, test_positive_docx_regression.py, test_rules_quality_acceptance.py, test_format_regression_audit.py), exits 0 against GREEN HEAD | ✓ VERIFIED | `Makefile:11-21` regression-gate recipe references all 4 files. Wave D SUMMARY records `make regression-gate` GREEN at 1380s on commit `19b6592` (14 passed + 1 skipped). |
| 4.6 | `README.md` has `## Pre-PR проверка` section pointing at `make regression-gate` | ✓ VERIFIED | `README.md:54-77` "Pre-PR проверка" section; references `make regression-gate` + all 4 gate test files in without-Make fallback. |
| 4.7 | `CONTRIBUTING.md` exists; documents pre-PR check + baseline-update workflow with `--reason` ≥ 8 chars; warns `--update-baseline` must run without `--limit` | ✓ VERIFIED | `CONTRIBUTING.md:1-67`: sections "Pre-PR проверка" (3-25), "Обновление baseline" (27-45), "Безопасность" (47-49), "Что покрывает гейт" (51-58), "CI fixture mechanism" (60-66). Contains «без `--limit`» at line 43, «8 символов после strip» at line 41, `D-004` at line 39, `--update-baseline` and `--reason` flags documented. |

#### Plan 04-05 (Wave E — GHA workflow)

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 5.1 | Every PR to main/master triggers regression-gate workflow | ✓ VERIFIED | `.github/workflows/regression-gate.yml:3-7` triggers on `pull_request` + `push` to `[main, master]`. |
| 5.2 | Workflow uses `actions/checkout@v4` + `actions/setup-python@v5` with python 3.11 + `cache: pip` | ✓ VERIFIED | Lines 17-21 of workflow file. |
| 5.3 | Workflow installs via `pip install -r requirements.txt` (no editable install, no pyproject.toml — Pitfall 4) | ✓ VERIFIED | Line 23 of workflow file. |
| 5.4 | Workflow runs exactly 4 gate test files; failure on any one fails PR; 4th file closes ROADMAP Phase 4 SC-1 | ✓ VERIFIED | Lines 31-35 invoke `python -m pytest -q` on all 4 files including `tests/test_format_regression_audit.py`. |
| 5.5 | `CI` env var set to `"true"` so corpus-missing pytest.fail branch fires (Pitfall 5) | ✓ VERIFIED | Line 10 `env: CI: "true"`. |
| 5.6 | Timeout pinned at 10 minutes (Pitfall 7) | ✓ VERIFIED | Line 15 `timeout-minutes: 10`. |
| 5.7 | Workflow validated end-to-end by both clean PR (GREEN) and deliberately-regressing PR (RED) — 2 URLs in SUMMARY | ✓ VERIFIED | `04-05-SUMMARY.md:88-93` records both PR URLs + workflow run URLs + statuses (success / failure) in a verification table. Regression branch deleted (no orphan code). External validation pre-confirmed by orchestrator. |

**Per-plan summary:** 28 must-have truths checked; 28 PASS; 0 FAIL; 0 PARTIAL.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `.planning/phases/04-regression-gate/04-WAVE-A-3docx-rootcause.md` | Wave A root-cause artefact with D-05 Branch B, locked ceilings, 3-doc subset | ✓ VERIFIED | 169 lines; "Branch chosen: B"; `after_diff_rate_ceiling = 0.359712`; `field_mismatch_ceiling = 630`; "Wave B amendment (2026-05-14)" section records 4→3 subset reduction. |
| `tests/baselines/negative_corpus.json` | Per-pair ceilings + aggregate + subset | ✓ VERIFIED | Valid JSON; schema_version=1; 3-element subset_filenames; 3 per-pair entries with locked ceilings + recorded_at + notes. |
| `tests/test_negative_corpus_diff_rate.py` | 3 named tests + helper extraction + CI fail-vs-skip idiom | ✓ VERIFIED | 84 lines; 3 expected test functions; `BASELINE_PATH` constant; `os.environ.get("CI") == "true"` fail-vs-skip at lines 32-35. |
| `tests/test_rules_quality_acceptance.py` | 5 static lints + 1 runtime smoke | ✓ VERIFIED | 116 lines; 6 named test functions; correct import wiring; BOM-tolerant `encoding="utf-8-sig"` read at line 98. |
| `tests/test_cli_parser.py` (extended) | +2 new tests + `import pytest` | ✓ VERIFIED | 280 lines (extended in place); `test_cli_parser_accepts_update_baseline_and_reason` at line 239; `test_cmd_audit_regression_refuses_update_baseline_without_reason` at line 256 with 3-case loop. |
| `src/main.py` (modified) | --update-baseline + --reason argparse + dispatcher + cmd guard | ✓ VERIFIED | argparse at lines 404-415 (both `required=False`); dispatcher at line 491 passes both kwargs; cmd guard at lines 247-261 enforces 8-char strip-minimum + Russian SystemExit; import at line 21. |
| `src/evaluation/format_regression_audit.py` (modified) | write_per_pair_baseline helper next to audits_to_frame | ✓ VERIFIED | Helper at lines 197-261; kw-only signature; subset filter at 229-243; WARNING-on-missing at 237-240; atomic JSON write at 260-261. |
| `Makefile` | regression-gate target invoking audit + 4 pytest files | ✓ VERIFIED | Tab-indented (verified via Read); `.PHONY: regression-gate`; `PYTHON ?= python3` (host has no plain python); all 4 files referenced; literal `python -m src.main audit-regression` in comment. |
| `README.md` | "## Pre-PR проверка" section | ✓ VERIFIED | Lines 54-77; references `make regression-gate` + 4 gate files; cross-references CONTRIBUTING.md. |
| `CONTRIBUTING.md` | Pre-PR + baseline-update + security + gate-coverage + CI fixture sections | ✓ VERIFIED | 67 lines, 5 sections. All required tokens present (--update-baseline, --reason, D-004, без --limit, 8 символов, all 4 test files, T-04-01/T-04-02). |
| `.github/workflows/regression-gate.yml` | GHA workflow with verbatim shape | ✓ VERIFIED | 36 lines; well-formed YAML (yaml.safe_load); correct triggers, action versions, python version, install path, test list, timeout, CI env, plus Option-D fixture staging step at lines 24-28. |
| `tests/fixtures/corpus/{positive,negative}/` (Option D) | 5MB DOCX subset for CI | ✓ VERIFIED | 4 positives (1, 3, 4, 45.docx) + 3 negatives (3_formatted_*, 4_formatted_*, 45_formatted_*) — matches `_metadata.subset_filenames`. |

### Key Link Verification (wiring)

| From | To  | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `tests/test_negative_corpus_diff_rate.py` | `tests/baselines/negative_corpus.json` | `BASELINE_PATH = Path("tests/baselines/negative_corpus.json")` + `json.loads(...read_text(encoding="utf-8"))` | ✓ WIRED | Lines 22, 25-26. |
| `tests/test_negative_corpus_diff_rate.py` | `src.evaluation.format_regression_audit.audit_negative_directory` | import + call with `frame[frame["negative"].isin(subset)]` filter | ✓ WIRED | Lines 17-20, 37-44. |
| `tests/test_rules_quality_acceptance.py` | `src/rules/formatting_rules_v1.json` | `RULES_PATH = Path(...)` + `json.loads` | ✓ WIRED | Lines 13, 29-30. |
| `tests/test_rules_quality_acceptance.py` | `audit_or_format_docx` + `build_regression_predictions` | import + invoke at runtime smoke | ✓ WIRED | Lines 10-11, 89-97. |
| `src/main.py cmd_audit_regression` | `src/evaluation/format_regression_audit.write_per_pair_baseline` | `from src.evaluation.format_regression_audit import ..., write_per_pair_baseline` at line 21 + call at line 256 | ✓ WIRED | argparse → dispatcher kwargs → cmd kwargs → guard → helper call. Full chain traced. |
| `Makefile regression-gate` | CLI + 4 pytest files | recipe `$(PYTHON) -m src.main audit-regression` + `$(PYTHON) -m pytest -q tests/...` | ✓ WIRED | Lines 12-21. Tab-indented. |
| `.github/workflows/regression-gate.yml` | 4 gate test files | step "Run regression gate" → `python -m pytest -q` over all 4 files | ✓ WIRED | Lines 31-35. |
| `.github/workflows/regression-gate.yml` | corpus fixtures | step "Stage corpus subset from fixtures" copies `tests/fixtures/corpus/{positive,negative}/*` into `positive_examples/` + `negative_examples/` | ✓ WIRED | Lines 24-28. |

### Data-Flow Trace (Level 4)

Regression-gate is infrastructure (tests + CI + CLI); the relevant "data flow" is `corpus DOCX → audit_negative_directory → audits_to_frame → frame filter → assertions`. For each gate test:

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `test_negative_corpus_diff_rate.py` | `frame` | `audit_negative_directory(positive_dir, negative_dir, ...)` + `audits_to_frame(audits)` filtered by `subset_filenames` | ✓ Yes (real DOCX I/O; not mocked) | ✓ FLOWING |
| `test_rules_quality_acceptance.py` | `df` (report CSV) | `build_regression_predictions` → `audit_or_format_docx` writing real CSV → `pd.read_csv` | ✓ Yes | ✓ FLOWING |
| `write_per_pair_baseline` | `frame` | passed from `cmd_audit_regression` after `audits_to_frame(audits)` | ✓ Yes (real audit result) | ✓ FLOWING |
| GHA workflow corpus inputs | `positive_examples/`, `negative_examples/` directories | `tests/fixtures/corpus/{positive,negative}/*.docx` (7 real DOCX, ~5MB) copied at workflow runtime | ✓ Yes | ✓ FLOWING |

No hardcoded empties or placeholder fallbacks reach the gates.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Baseline JSON schema valid (schema_version=1, aggregate_mean_ceiling=0.4781, 3 subset_filenames, 3.docx ceiling=0.359712) | `python3 -c "import json; d = json.load(open('tests/baselines/negative_corpus.json')); ..."` | OK | ✓ PASS |
| `write_per_pair_baseline`, `audit_negative_directory`, `audits_to_frame` importable from `src.evaluation.format_regression_audit` | `python3 -c "from src.evaluation.format_regression_audit import write_per_pair_baseline, audit_negative_directory, audits_to_frame"` | OK | ✓ PASS |
| GHA workflow YAML well-formed | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/regression-gate.yml'))"` | OK | ✓ PASS |
| Pytest collects all 19 expected test cases across the 3 modified/new test files | `python3 -m pytest --collect-only tests/test_negative_corpus_diff_rate.py tests/test_rules_quality_acceptance.py tests/test_cli_parser.py` | 19 tests collected in 3.80s; all expected names present | ✓ PASS |
| All 4 gate test files referenced in Makefile, GHA workflow, README, CONTRIBUTING | `grep` cross-check | All 4 files referenced in all 4 wiring documents | ✓ PASS |
| ROADMAP SC-2 + REQUIREMENTS REQ-fix-negative-corpus-no-regression cite commit 7207cbe + 0.359712 (Branch B atomic amendment) | `grep "Phase 4 D-05 Branch B" .planning/{ROADMAP,REQUIREMENTS}.md` | ROADMAP:88 match; REQUIREMENTS:85-91 match | ✓ PASS |
| Full `make regression-gate` GREEN at HEAD (pre-cached by Wave D, not re-run here) | recorded by Wave D SUMMARY at commit 19b6592 | 14 passed + 1 skipped in 1380s | ✓ PASS (recorded) |

Note: full `make regression-gate` not re-run by verifier — already validated by Wave D SUMMARY at commit 19b6592 (1380s run) AND by GHA workflow run #25846822154 (1m54s) on a fixture-staged corpus subset. Re-running would exceed verifier time budget and add no signal.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| **REQ-fix-negative-corpus-no-regression** | 04-01, 04-02 | No negative-corpus pair regresses below Wave-A-locked per-pair ceiling; mean ≤ 0.4781; Branch B citation | ✓ SATISFIED | `REQUIREMENTS.md:85-91` marks `[x]` Complete with Branch B amendment + commit 7207cbe citation. Enforced by `tests/test_negative_corpus_diff_rate.py` (3 tests) against `tests/baselines/negative_corpus.json` ceilings. CI validated PR #2 (regression RED). |
| **REQ-audit-regression-cli** | 04-04, 04-05 | `audit-regression` CLI compares corpus run against saved baseline; per-pair CSV + summary JSON; brought under regression-test gate | ✓ SATISFIED | `REQUIREMENTS.md:145-150` marks `[x]` Complete. CLI in `src/main.py:205-278` emits CSV + summary JSON; `--update-baseline / --reason` flags added with Pitfall 1/Pitfall 6 mitigations; `make regression-gate` (local) + `.github/workflows/regression-gate.yml` (CI) both gate every fix-track PR. |
| **REQ-rules-quality-acceptance** | 04-03 | Every rule follows RuleRecord; every violation/fix in report; unsafe fixes blocked; low-confidence → manual review | ✓ SATISFIED | `REQUIREMENTS.md:136-140` marks `[x]` Complete. Enforced by `tests/test_rules_quality_acceptance.py` (5 static lints + 1 runtime smoke). |

**Orphan requirements check:** REQUIREMENTS.md traceability table at lines 218-220 lists exactly the 3 Phase 4 REQ IDs; no additional REQ-* maps to Phase 4 that any plan failed to claim. No orphans.

### Anti-Patterns Found

Scan of files modified in Phase 4 (`src/main.py`, `src/evaluation/format_regression_audit.py`, `tests/test_*.py`, `tests/baselines/negative_corpus.json`, `Makefile`, `README.md`, `CONTRIBUTING.md`, `.github/workflows/regression-gate.yml`):

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `src/evaluation/format_regression_audit.py` | 215-216 | Function-local `import json` + `from datetime import datetime, timezone` (no compelling reason — stdlib) | ℹ️ Info (LR-01 from code review) | Style only — works correctly. Not blocking. |
| `src/evaluation/format_regression_audit.py` | 213, 216 | Docstring says "writes JSON back atomically" but implementation is plain `path.write_text` (not temp-file + rename) | ⚠️ Warning (MD-02 from code review) | Misleading doc; risk in practice low (dev-only CLI, short writes, JSON git-recoverable). Out of scope to fix in verification. |
| `tests/test_negative_corpus_diff_rate.py` | 44 | Silent gate vacuum if all `subset_filenames` missing from corpus — per-pair tests would loop over zero rows and PASS vacuously (aggregate-mean test still fails on `NaN <= ceiling` so the overall gate fails loudly) | ⚠️ Warning (MD-01 from code review) | A future PR removing a corpus file without updating `_metadata.subset_filenames` would silently weaken 2 of 3 per-pair tests. Aggregate test catches it. Acceptable; could be hardened by `assert len(filtered) == len(subset_filenames)` (one-liner). Code review marked MEDIUM advisory, not blocking. |
| `src/evaluation/format_regression_audit.py` | 241-243 | Seed-scenario writes ALL rows in `frame` when `_metadata.subset_filenames == []` — Pitfall 1 failure mode re-surfaces in seed-then-update path | ℹ️ Info (LR-03 from code review) | Edge case (real workflow always starts from existing repo-committed baseline with subset locked). Not exercised. |
| `CONTRIBUTING.md` | 62-66 | "CI fixture mechanism" couples doc to specific implementation detail (corpus filename list); honour-system invariant | ℹ️ Info (LR-04 from code review) | Drift-prone but observable; flagged for later milestone. |

Stub patterns: None — every test asserts on real audit-produced data; CLI writes real JSON; helper is fully implemented; no `TODO`/`FIXME`/`PLACEHOLDER` introduced in this phase's files.

Empty-return / hardcoded-empty checks: none. `write_per_pair_baseline` produces real ceilings rounded to 6 decimals from live `frame` rows; CLI guard raises real `SystemExit` with real Russian-language message; no `return None` / `return []` / `=> {}` patterns in production paths.

### Human Verification Required

None. Phase 4 is regression-gate infrastructure (CLI + tests + baseline JSON + Makefile + CI workflow + docs). Everything is programmatically verifiable; the only behavior that requires GitHub PR cycle (workflow firing on PR open) was already validated end-to-end by the orchestrator's external CI validation (PR #1 success + PR #2 designed failure). Code review (`04-REVIEW.md`) confirmed status `clean`. Schema-drift gate (per orchestrator note) clean.

### Gaps Summary

None. All 28 must-have truths across 5 plans verified; 4/4 ROADMAP success criteria satisfied; 3/3 Phase 4 REQ-* IDs closed (`REQ-fix-negative-corpus-no-regression`, `REQ-audit-regression-cli`, `REQ-rules-quality-acceptance`); the negative-corpus regression baseline is locked (Branch B at 0.359712 / 630 for 3.docx pair, plus 45.docx + 4.docx pairs); the rules-quality-acceptance lint protects forward against any RuleRecord-schema drift; `make regression-gate` is the canonical local gate; GHA workflow gates every PR + push to main/master and was validated end-to-end by two real PR runs (clean GREEN + designed RED).

Outstanding advisory items (5 from 04-REVIEW.md: 2 MEDIUM + 4 LOW, with MD-01 + LR-03 spotted under anti-patterns above) do NOT block phase closure per the code review's `status: clean` verdict; they are quality nits for a later cleanup pass, not Phase 4 deliverable gaps.

---

_Verified: 2026-05-14_
_Verifier: Claude (gsd-verifier), Opus 4.7 (1M context)_
