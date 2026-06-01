---
phase: 5
slug: rule-profiles-methodical-profile-ingestion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-14
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from `05-RESEARCH.md` § Validation Architecture. Planner fills the
> Per-Task Verification Map once PLAN.md files exist.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` (existing — `[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest tests/test_methodical_extractor.py tests/test_profile_diff.py tests/test_profile_quality_acceptance.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~10s (quick) / ~60s (full incl. PDF parse on Бергер fixture) |

---

## Sampling Rate

- **After every task commit:** Run quick command for the touched test files.
- **After every plan wave (A/B/C/D/E):** Run full suite (`pytest tests/ -x -q`).
- **Before `/gsd-verify-work`:** Full suite must be green AND `make regression-gate` must pass against the committed Бергер fixture.
- **Max feedback latency:** 10 seconds for quick; 60 seconds for full.

---

## Per-Task Verification Map

> Planner populates this table from PLAN.md `<acceptance_criteria>` blocks during
> /gsd-plan-phase. The rows below are the RED signatures derived from RESEARCH.md
> §Validation Architecture — planner must keep them and add `<automated>` commands.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 5-01-RED | 01 | A | REQ-methodical-profile-extract | — | Annotated profile carries `_source` per leaf | unit | `pytest tests/test_methodical_extractor.py::test_every_leaf_has_source -x` | ❌ W0 | ⬜ pending |
| 5-01-GREEN | 01 | A | REQ-methodical-profile-extract | — | `extraction_meta.needs_manual_review` derived from `any(leaf._source.needs_review)` | unit | `pytest tests/test_methodical_extractor.py::test_needs_review_derived -x` | ❌ W0 | ⬜ pending |
| 5-02-RED | 02 | B | REQ-methodical-profile-extract | — | `profile_diff.diff_profiles(a,b)` raises on missing path arg | unit | `pytest tests/test_profile_diff.py::test_diff_missing_arg -x` | ❌ W0 | ⬜ pending |
| 5-02-GREEN | 02 | B | REQ-methodical-profile-extract | — | Diff filters `._source.` paths; emits `path: old → new` | unit | `pytest tests/test_profile_diff.py::test_diff_filters_source_paths -x` | ❌ W0 | ⬜ pending |
| 5-03-RED | 03 | C | REQ-methodical-profile-extract | — | `extract-methodical-profile` without `--apply` does NOT touch `PROFILES_DIR/<id>.json` | integration | `pytest tests/test_cli_parser.py::test_extract_dryrun_default -x` | ❌ W0 | ⬜ pending |
| 5-03-FORCE | 03 | C | REQ-methodical-profile-extract | T-04-02 (path traversal — inherits) | `--apply --force` without `--reason` of ≥8 chars exits non-zero with Russian message | integration | `pytest tests/test_cli_parser.py::test_force_requires_reason -x` | ❌ W0 | ⬜ pending |
| 5-04-LINT | 04 | D | REQ-rule-profiles | — | All `src/rules/profiles/*.json` validate via `profile_validator.validate()` | unit | `pytest tests/test_profile_quality_acceptance.py::test_all_profiles_valid -x` | ❌ W0 | ⬜ pending |
| 5-04-SC1 | 04 | D | REQ-rule-profiles | — | `audit-docx --profile-id <id>` argparse accepts flag; report header carries profile_id | unit | `pytest tests/test_cli_parser.py::test_audit_docx_profile_id -x` | ❌ W0 | ⬜ pending |
| 5-05-CI | 05 | E | REQ-rule-profiles, REQ-methodical-profile-extract | — | GHA workflow includes Бергер fixture stage + 6-file pytest invocation; runs GREEN on PR | e2e | `make regression-gate` + designed-failure PR | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_methodical_extractor.py` — NEW. Stubs for `_source` annotation + derived `needs_manual_review` (plan 5-01 RED).
- [ ] `tests/test_profile_diff.py` — NEW. Stubs for flattened-path diff + `_source` filtering (plan 5-02 RED).
- [ ] `tests/test_profile_quality_acceptance.py` — NEW. Stubs for two-tier schema lint (Tier A all profiles, Tier B methodical-only `_source` enforcement) (plan 5-04 RED).
- [ ] `tests/test_cli_parser.py` — EXISTS, extend with `test_extract_dryrun_default`, `test_force_requires_reason`, `test_audit_docx_profile_id` (plans 5-03, 5-04).
- [ ] `tests/fixtures/methodical/normocontrol_berger.pdf` — NEW (1.4MB, committed binary). Loaded by 5-01 GREEN + 5-05 CI gate.
- [ ] pytest 8.x — already on stack. No framework install required.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Russian-language error message wording in `--force --reason` guard | REQ-methodical-profile-extract / D-11 | Wording quality (clarity, no anglicisms) is subjective; the EXIT CODE + STDERR REGEX are automated, but wording polish is manual. | Run `python -m src.main extract-methodical-profile <pdf> --apply --force --reason "x"` and read the stderr message; confirm it cites D-004 in Russian. |
| Бергер profile spot-check after 5-01 GREEN | REQ-methodical-profile-extract / SC-4 | Per-field `_source` accuracy (loc=page_N pointing to the right page) cannot be asserted en masse; manual sample of 5 leaves. | After `extract-methodical-profile tests/fixtures/methodical/normocontrol_berger.pdf --apply`, open the candidate JSON, pick 5 random leaves with `_source.loc`, open the PDF at that page and confirm the value is sourced from there. |
| End-to-end designed-failure PR validation for 5-05 CI gate | REQ-rule-profiles / SC-1..SC-4 | Phase 4 lesson — GHA workflow can pass locally but fail in real PR run (matrix differences). | Open a throwaway PR that introduces a bogus required-field in `src/rules/profiles/gost_7_32_2017.json`; confirm `regression-gate.yml` job goes RED with the schema-lint test name in the GHA summary. Close PR without merge. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags (pytest `-x -q`, no `--watch`)
- [ ] Feedback latency < 10s for quick / < 60s for full
- [ ] `nyquist_compliant: true` set in frontmatter once planner fills the Per-Task Verification Map and the checker verifies coverage

**Approval:** pending
