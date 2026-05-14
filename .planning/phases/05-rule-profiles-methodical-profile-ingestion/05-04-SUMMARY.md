---
phase: 05-rule-profiles-methodical-profile-ingestion
plan: 04
subsystem: rule-profiles
tags: [schema-lint, two-tier, cli-dispatcher, profile-id, tdd, sc-1, pitfall-5]

# Dependency graph
requires:
  - phase: 04-regression-gate
    provides: Phase 4 Wave C analog tests/test_rules_quality_acceptance.py (bogus-required-field RED carrier pattern)
  - phase: 05-rule-profiles-methodical-profile-ingestion
    provides: 05-01 _source-per-leaf shape on methodical profiles; 05-02 profile_diff.compute_profile_diff
provides:
  - tests/test_profile_quality_acceptance.py — two-tier schema lint (Tier A all profiles + Tier B methodical-only, vacuous at HEAD)
  - synthetic-profile RED guard (test_red_carrier_fires_on_synthetic_methodical_profile) — permanent regression guard against divergent required-key sets
  - --profile-id flag on audit-docx and format-docx subparsers (Pitfall 5 closure)
  - cmd_audit_docx / cmd_format_docx signatures thread profile_id through to audit_or_format_docx
  - main() dispatch wires args.profile_id at three sites (regression + audit + format)
affects:
  - 05-05-CI-gate — plan 5-05 CI runs the new schema lint; Tier B fires substantively once a methodical profile lands

# Tech tracking
tech-stack:
  added: []   # No new dependencies
  patterns:
    - "Two-tier schema-lint design: Tier A guards all profiles, Tier B guards methodical-only (vacuous-by-design until methodical profile lands)"
    - "Synthetic-profile RED carrier: empirically observable RED at HEAD without relying on a methodical profile being committed (Phase 4 Wave C Option 1 extension)"
    - "Subparser flag mirroring: audit_parser / format_parser stanzas copied verbatim from regression_parser to keep the three subcommands at parity on --profile-id"

key-files:
  created:
    - tests/test_profile_quality_acceptance.py (+177 LoC) — 6 tests
  modified:
    - src/main.py (+24/-1 LoC) — --profile-id stanza on audit_parser + format_parser; profile_id kwarg threaded through cmd_audit_docx + cmd_format_docx + main() dispatch
    - tests/test_cli_parser.py (+44 LoC) — three smokes for new flag (explicit value on both subcommands + default-value preservation on both)

key-decisions:
  - "Synthetic-profile guard test retained post-GREEN as a permanent regression guard against future re-introduction of a divergent REQUIRED_TOP_LEVEL_KEYS_FOR_METHODICAL — bogus-required-field shape mismatch would otherwise stay invisible until a methodical profile lands on disk"
  - "Explicit acceptance-criterion read: `grep -c \"__red_placeholder__\"` must return 0 post-GREEN — so docstrings/comments were also purged of the literal token (not just the set entry); test semantics unchanged"
  - "Default --profile-id value held at 'gost_7_32_2017' across all three subcommands (regression + audit + format) for predictable behavior — no per-subcommand defaults"

requirements-completed:
  - REQ-rule-profiles
  - REQ-methodical-profile-extract

# Metrics
duration: 262s
completed: 2026-05-14
---

# Phase 5 Plan 4: Profile Schema Lint + SC-1 CLI Closure Summary

Two-tier profile schema lint shipped (Tier A all-profile validation + Tier B methodical-only-vacuous-at-HEAD), plus the `--profile-id` flag wired through `audit-docx` and `format-docx` so SC-1 holds end-to-end for every document-touching subcommand.

## What Was Built

### Tier A schema lint (all profiles)

`tests/test_profile_quality_acceptance.py` adds two Tier A tests that iterate every `src/rules/profiles/*.json`:

1. `test_every_profile_passes_validator` — every profile must pass `src.rules.profile_validator.validate_profile`.
2. `test_every_profile_has_required_top_level_keys` — every profile must carry `profile_id`, `profile_name`, `profile_type`, `is_default`.

At HEAD the three GOST/local profiles (`gost_7_32_2017.json`, `gost_r_7_0_100_2018_bibliography.json`, `mirea_normcontrol_local.json`) all pass both Tier A tests.

### Tier B schema lint (methodical-only)

Four Tier B tests fire substantively only on profiles with `profile_type == "methodical_guidelines"`:

3. `test_red_carrier_bogus_required_field` — iterates real methodical profiles; vacuous over real profiles at HEAD (no methodical profile committed).
4. `test_red_carrier_fires_on_synthetic_methodical_profile` — injects a synthetic methodical profile in-test, gives the lint an empirically observable RED carrier without waiting for a methodical profile on disk.
5. `test_every_methodical_profile_has_source_per_leaf` — walks `document_rules.*`, `labels.*.style_profile.*`, `bibliography_rules.*` and asserts every leaf carries `_source` (D-05); vacuous at HEAD.
6. `test_methodical_needs_manual_review_consistent_with_per_leaf_sources` — derived-field consistency (D-05 + Pitfall 8); vacuous at HEAD.

### SC-1 CLI closure (Pitfall 5)

`src/main.py` was extended at three sites:

- Subparsers `audit_parser` and `format_parser` add a `--profile-id` argument (default `gost_7_32_2017`), matching the existing `regression_parser` stanza verbatim.
- Functions `cmd_audit_docx` and `cmd_format_docx` add `profile_id: str = "gost_7_32_2017"` to their signatures and forward it as `profile_id=profile_id` to `audit_or_format_docx(...)`. The backing API already accepts the kwarg and emits the chosen `profile_id` into the per-row CSV column + summary JSON key.
- `main()` dispatch wires `profile_id=args.profile_id` for both subcommands.

SC-1 ("chosen profile id is recorded in the report header") now holds for all three document-touching subcommands (`audit-docx`, `format-docx`, `audit-regression`).

## Files Created / Modified

| File | Delta | Notes |
|------|-------|-------|
| `tests/test_profile_quality_acceptance.py` | NEW, +177 LoC | 6 tests (2 Tier A + 4 Tier B incl. synthetic guard) |
| `src/main.py` | +24/-1 LoC | 2 argparse stanzas + 2 function signatures + 2 inner kwargs + 2 dispatch sites |
| `tests/test_cli_parser.py` | +44 LoC | 3 smokes for the new flag |

## Commit Sequence (TDD RED → GREEN + SC-1)

| Commit | Subject | Notes |
|--------|---------|-------|
| `c30e7b2` | `test(05-04): RED — profile schema lint (two-tier, bogus-required-field carrier)` | 5 passed / 1 failed observed; failing test is `test_red_carrier_fires_on_synthetic_methodical_profile`, reason: `synthetic methodical profile missing ['__red_placeholder__']` |
| `6e89eff` | `feat(05-04): GREEN — schema lint (remove RED carrier)` | All 6 tests GREEN; `grep -c "__red_placeholder__"` returns 0 |
| `8088e3e` | `feat(05-04): SC-1 — --profile-id on audit-docx and format-docx (Pitfall 5)` | All 24 tests across both new files pass |

## Tier A Pass Confirmation at HEAD

```
$ python3 -m pytest tests/test_profile_quality_acceptance.py::test_every_profile_passes_validator -q
.                                                                        [100%]
1 passed
```

The three existing profile JSONs (`gost_7_32_2017.json`, `gost_r_7_0_100_2018_bibliography.json`, `mirea_normcontrol_local.json`) all pass `validate_profile` and the top-level-keys check.

## Tier B Vacuous Confirmation at HEAD

```
$ ls src/rules/profiles/
gost_7_32_2017.json
gost_r_7_0_100_2018_bibliography.json
mirea_normcontrol_local.json

$ python3 -c 'import json,glob; print(sorted({json.load(open(p))["profile_type"] for p in glob.glob("src/rules/profiles/*.json")}))'
['gost', 'university_local']
```

No `profile_type == "methodical_guidelines"` profile is committed. Tests 3, 5, 6 iterate empty and pass vacuously; the synthetic guard test 4 fires substantively post-GREEN.

## Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| `python3 -m pytest tests/test_profile_quality_acceptance.py -x -q` exits 0 with 6 passing | PASS |
| `grep -c "def test_" tests/test_profile_quality_acceptance.py` returns 6 | PASS |
| `grep -c "__red_placeholder__" tests/test_profile_quality_acceptance.py` returns 0 (post-GREEN) | PASS |
| `python3 -m src.main audit-docx --help` shows `--profile-id` | PASS (2 hits in help) |
| `python3 -m src.main format-docx --help` shows `--profile-id` | PASS (2 hits in help) |
| `grep -c '"--profile-id"' src/main.py` >= 3 | PASS (3) |
| `grep -c "profile_id=args.profile_id" src/main.py` >= 3 | PASS (3) |
| `grep -c "def cmd_audit_docx\|def cmd_format_docx" src/main.py` returns 2 | PASS |
| Existing `test_cli_parser_accepts_update_baseline_and_reason` still GREEN | PASS |
| 24 tests across `tests/test_cli_parser.py + tests/test_profile_quality_acceptance.py` pass | PASS |

## Deviations from Plan

None. The plan was executed exactly as written. The only judgement call was on the literal reading of acceptance criterion `grep -c "__red_placeholder__" tests/test_profile_quality_acceptance.py` returns 0 — I purged the token from docstrings/comments as well as the required-key set, so the count is 0 (not just the set entry). Test semantics are unchanged; the synthetic guard retains its semantic role as a regression carrier against future divergent required-key sets.

## TDD Gate Compliance

| Gate | Commit | Verified |
|------|--------|----------|
| RED  | `c30e7b2` | 5 passed / 1 failed on `test_red_carrier_fires_on_synthetic_methodical_profile`, observed failure message `synthetic methodical profile missing ['__red_placeholder__']` |
| GREEN | `6e89eff` | 6 passed / 0 failed; bogus key removed from `REQUIRED_TOP_LEVEL_KEYS_FOR_METHODICAL` |
| REFACTOR | (none) | No separate refactor commit — GREEN minimum was sufficient |

The SC-1 CLI commit (`8088e3e`) is a feat commit that adds new tests in the same commit as the implementation. This follows the plan's bundled-task design (the new argparse flag and its CLI parser tests are inseparable: argparse can be probed without an end-to-end test, so the smokes capture the contract).

## Known Stubs

None.

## Threat Flags

No new security-relevant surface introduced. The new `--profile-id` argv value on `audit-docx` / `format-docx` reuses the existing `load_profile(profile_id=...)` resolver, which is path-confined to `PROFILES_DIR/<id>.json` (T-04-02 mitigation already in place from Phase 4).

## Self-Check: PASSED

Files asserted:
- `tests/test_profile_quality_acceptance.py` — FOUND (177 LoC).
- `src/main.py` — FOUND (633 LoC; +24/-1 from base).
- `tests/test_cli_parser.py` — FOUND (472 LoC; +44 from base).

Commits asserted:
- `c30e7b2` — FOUND.
- `6e89eff` — FOUND.
- `8088e3e` — FOUND.
