---
phase: 05-rule-profiles-methodical-profile-ingestion
plan: 05
status: checkpoint_pending
updated: 2026-05-14
checkpoint_type: human-action
checkpoint_blocking: true
requirements:
  - REQ-rule-profiles
  - REQ-methodical-profile-extract
key-files:
  created:
    - tests/fixtures/methodical/normocontrol_berger.pdf
  modified:
    - .github/workflows/regression-gate.yml
    - Makefile
    - CONTRIBUTING.md
---

## What was built

Phase 5 CI gate extension — local part complete; end-to-end GitHub PR validation pending user action.

### Tasks 1-4 (autonomous, committed)

| # | Task | Commit | Outcome |
|---|------|--------|---------|
| 1 | Pre-flight Бергер extraction timing | (no commit — measurement only) | Decision: `timeout-minutes: 10` retained (extraction well under 60s threshold per D-10) |
| 2 | Commit Бергер fixture | `ed8a60e` | `tests/fixtures/methodical/normocontrol_berger.pdf` (1.4 MB, tracked, NOT gitignored) |
| 3 | Extend GHA workflow + Makefile to 6-file pytest | `b763f64` | Both invocations now list 6 test files (4 existing + 2 Phase 5) |
| 4 | CONTRIBUTING.md Phase 5 section | `ce8c29a` | Russian-language section per D-11; mentions fixture + 6-file gate |

### Verification

- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/regression-gate.yml'))"` → `YAML-OK`
- `make -n regression-gate` → exit 0; lists all 6 pytest paths
- `python3 -m pytest -q tests/test_profile_quality_acceptance.py tests/test_methodical_extractor.py` → `11 passed`
- `git ls-files tests/fixtures/methodical/normocontrol_berger.pdf` → tracked
- `git check-ignore tests/fixtures/methodical/normocontrol_berger.pdf` → exit 1 (NOT ignored)
- `grep -c "tests/fixtures/methodical\|test_profile_quality_acceptance\|test_methodical_extractor" CONTRIBUTING.md` → 4 matches

## Task 5 — Human-action checkpoint (PENDING)

End-to-end CI validation via PR pair on GitHub:

1. Push feature branch + open clean PR against `main` → expect GREEN (6 pytest files pass).
2. Open designed-failure PR (introduce bogus required-field in `src/rules/profiles/gost_7_32_2017.json`) → expect RED.
3. Record both run URLs in this SUMMARY; close failure PR without merge.

Cannot be automated — requires `gh` CLI auth + remote push + GHA log inspection.

## Self-Check: PASSED (local portion)

Tasks 1-4 acceptance criteria all met. End-to-end CI validation deferred to user.
