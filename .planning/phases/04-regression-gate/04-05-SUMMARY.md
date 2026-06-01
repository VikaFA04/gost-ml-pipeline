---
phase: 04-regression-gate
plan: 05
status: complete
subsystem: ci
tags: [ci, github-actions, pytest, regression-gate, gha, workflow, REQ-audit-regression-cli, D-08, D-09, T-04-03]

# Dependency graph
requires:
  - phase: 04-regression-gate
    provides: Makefile regression-gate target + 4 gate test files (04-04) — CI mirrors the same fast pytest invocation
  - phase: 04-regression-gate
    provides: tests/baselines/negative_corpus.json (04-02) — per-pair ceilings consumed by negative-corpus diff-rate test on CI
  - phase: 04-regression-gate
    provides: tests/test_rules_quality_acceptance.py (04-03) — invoked on CI as one of the four gate files
provides:
  - .github/workflows/regression-gate.yml (NEW; GHA workflow gates every PR/push to main/master with the fast pytest gate)
  - Corpus fixture mechanism (tests/fixtures/corpus/{positive,negative}/) — 7 DOCX files (~5MB) shipped in-repo so CI has the subset of positive_examples/ + negative_examples/ that the gate exercises (positive_examples/ + negative_examples/ are gitignored at ~107MB and not available in the GHA runner clean checkout)
  - Workflow staging step that mkdirs positive_examples/ + negative_examples/ at CI runtime and copies the in-repo fixtures into them, so the 4 gate test files see the same paths in CI as locally
  - CONTRIBUTING.md amendment — appended section describing the CI fixture mechanism (which subset is shipped, why, how to add files)
  - tests/test_rules_quality_acceptance.py runtime smoke path correction — was `Path("negative_examples") / "3.docx"`, no such file exists; corrected to `Path("positive_examples") / "3.docx"` (semantically equivalent — invariants assert on the report CSV, not on input-dir identity)
  - REQ-audit-regression-cli closed end-to-end (was already marked Complete in REQUIREMENTS traceability at 04-04; this plan validated the CI half of "wired into CI / a documented local check")
affects: [05-rule-profiles (will need to ensure new profile work doesn't regress the gate), 06-streamlit-ui (UI changes that touch report rendering must pass the gate)]

# Tech tracking
tech-stack:
  added:
    - GitHub Actions workflow (.github/workflows/regression-gate.yml)
    - actions/checkout@v4 (RESEARCH Probe 7 — WebFetch-verified 2026-05-13)
    - actions/setup-python@v5 (RESEARCH Probe 7 — v6 requires runner ≥ v2.327.1, not available on default ubuntu-latest 2026-05-13)
  patterns:
    - "GHA workflow + in-repo fixture pattern: gitignored heavy corpus stays out of repo; small per-test subset shipped under tests/fixtures/corpus/; workflow step stages fixtures into the canonical paths at CI runtime so tests see identical paths in CI and locally"
    - "`python -m pytest` rather than bare `pytest` in CI: bare `pytest` resolves the binary from PATH but does NOT auto-inject cwd into sys.path when no pyproject.toml/conftest.py/setup.py is present at repo root for pytest rootdir discovery. `python -m pytest` runs through the python entrypoint, which does inject cwd, so `import src.*` works in the gate test files."
    - "GHA action major-version pinning (`@v4`, `@v5`) — supply-chain mitigation T-04-03: get security patches automatically, but avoid breaking changes between major versions; bumping requires re-verifying runner version compatibility"

key-files:
  created:
    - .github/workflows/regression-gate.yml
    - tests/fixtures/corpus/positive/1.docx
    - tests/fixtures/corpus/positive/3.docx
    - tests/fixtures/corpus/positive/4.docx
    - tests/fixtures/corpus/positive/45.docx
    - tests/fixtures/corpus/negative/3_formatted_20260413_194927.docx
    - tests/fixtures/corpus/negative/4_formatted_20260413_185420.docx
    - tests/fixtures/corpus/negative/45_formatted_20260414_220339.docx
  modified:
    - tests/test_rules_quality_acceptance.py (runtime smoke path: negative_examples/3.docx → positive_examples/3.docx)
    - CONTRIBUTING.md (appended "CI fixture mechanism" section)

key-decisions:
  - "Option D added (deviation Rule 4 — architectural): plan assumed positive_examples/ + negative_examples/ would be present in CI, but those directories are gitignored (~107MB) and not available in a fresh GHA runner checkout. Resolution: ship a 5MB subset (4 positives + 3 negatives, matching tests/baselines/negative_corpus.json _metadata.subset_filenames) under tests/fixtures/corpus/{positive,negative}/, and add a workflow staging step that copies fixtures into the canonical paths at CI runtime. No production code path knows about the fixture dir — only the workflow."
  - "Workflow uses `python -m pytest` rather than `pytest -q` (deviation Rule 1 — bug discovered during Task 2): initial Task 1 commit used the verbatim shape from RESEARCH Example 4 with bare `pytest -q`. Initial PR run failed with `ModuleNotFoundError: No module named 'src'`. Root cause: this repo has no `pyproject.toml` / `conftest.py` at root for pytest rootdir discovery (the same configuration gap that produces pyright's pre-existing `src.* not resolved` diagnostic locally); bare pytest does not auto-add cwd to sys.path. `python -m pytest` does. One-token change unblocks the gate; we did NOT add pyproject.toml to fix this because the rest of the repo runs fine without it and adding it would expand scope."
  - "Plan-3 filename bug (Plan 04-03 hardcoded `Path('negative_examples') / '3.docx'` in the runtime smoke — but `3.docx` is a positive corpus file; `negative_examples/3.docx` does not exist). Amended to `Path('positive_examples') / '3.docx'` as part of the corpus fixture commit. Semantically equivalent — the runtime smoke asserts on the report CSV invariants, not on input-directory identity."

patterns-established:
  - "PR gate is the GHA workflow (.github/workflows/regression-gate.yml); local pre-PR gate is `make regression-gate` from Plan 04-04. Both invoke the same 4 test files; CI is a thin wrapper around the local recipe with the extra fixture-staging step."
  - "Future PRs touching rule engine, safe-formatter, regression audit, or rule JSON are gated automatically — no opt-in needed."
  - "When a new corpus file is added to the gate, it must be added to both tests/baselines/negative_corpus.json _metadata.subset_filenames AND tests/fixtures/corpus/{positive,negative}/ — CONTRIBUTING.md documents this."

requirements-completed:
  - REQ-audit-regression-cli

# Metrics
duration: ~120min (Task 1 < 5min + Task 2 ~2h including GitHub PR cycle, deviation diagnosis, fixture work, and two CI runs averaging 1m52s each)
completed: 2026-05-14
---

# Phase 4 Plan 05: GHA Regression Gate Summary

**Every PR to main/master is now gated by a GHA workflow that runs the same fast pytest gate as `make regression-gate` — validated end-to-end via two real GitHub PRs (clean GREEN + deliberately-regressing RED).**

## Performance

- **Duration:** ~120 min (Task 1 trivial; Task 2 dominated by GitHub PR cycle + deviation diagnosis + fixture amendment + two CI runs)
- **Completed:** 2026-05-14
- **Tasks:** 2 (1 auto, 1 checkpoint:human-verify)
- **Files created:** 8 (1 workflow + 7 fixture DOCX)
- **Files modified:** 2 (test path fix + CONTRIBUTING)

## Accomplishments

- `.github/workflows/regression-gate.yml` exists at the canonical path; pinned `actions/checkout@v4` + `actions/setup-python@v5` per RESEARCH Probe 7 (WebFetch-verified 2026-05-13); 10-min timeout; pip cache keyed on requirements.txt hash; runs all FOUR gate test files (`test_negative_corpus_diff_rate.py`, `test_positive_docx_regression.py`, `test_rules_quality_acceptance.py`, `test_format_regression_audit.py` — last closes ROADMAP Phase 4 SC-1 on CI).
- Workflow validated end-to-end with TWO real PRs against `VikaFA04/gost-ml-pipeline`: a clean PR (GREEN, allowed to merge) and a deliberately-regressing PR (RED, merge blocked, failing test matched the regression target exactly).
- Corpus fixture mechanism shipped (Option D deviation): tests/fixtures/corpus/ holds a 5MB subset (4 positives + 3 negatives matching _metadata.subset_filenames) so CI has the corpus files the gate needs without lugging the gitignored 107MB.
- Phase 4 D-08 ("every PR is gated by the regression-gate workflow") satisfied; gate is LIVE.

## Task 2 Verification Trail

| PR | URL | Run URL | Conclusion | Notes |
|----|-----|---------|------------|-------|
| Clean (initial Task 1 commit) | https://github.com/VikaFA04/gost-ml-pipeline/pull/1 | https://github.com/VikaFA04/gost-ml-pipeline/actions/runs/25846417404 | **failure** | `ModuleNotFoundError: No module named 'src'`. Root cause: bare `pytest -q` doesn't inject cwd into sys.path with no pyproject.toml/conftest.py/setup.py at repo root. Diagnosed → fixed in commit `5c6327d` (`pytest` → `python -m pytest`). |
| Clean (post-fix) | https://github.com/VikaFA04/gost-ml-pipeline/pull/1 | https://github.com/VikaFA04/gost-ml-pipeline/actions/runs/25846822154 | **success** / GREEN | 1m54s. All 4 gate test files passed. Workflow validated on clean code → merge allowed. |
| Regression (deliberate) | https://github.com/VikaFA04/gost-ml-pipeline/pull/2 | https://github.com/VikaFA04/gost-ml-pipeline/actions/runs/25847679849 | **failure** / RED | 1m50s. `tests/test_negative_corpus_diff_rate.py::test_per_pair_after_diff_rate_no_regression` failed exactly as designed: `AssertionError: 3_formatted_20260413_194927.docx: after_diff_rate=0.359712 > ceiling=0.100000` (regression PR tightened the 3.docx pair ceiling from 0.359712 → 0.100000). PR #2 closed without merge; remote + local `gsd/phase-04-deliberate-regression` branch deleted (no orphan code — CLAUDE.md "Удаляй orphans"). |

**Gate verified end-to-end:** workflow GREEN on clean code, RED on deliberate regression, merge blocked when regression introduced. Both branches of the gate fired in CI, not just locally.

## Task Commits

| Hash | Type | Description |
|------|------|-------------|
| `4831a8f` | feat | add .github/workflows/regression-gate.yml — fast pytest gate on PR (Task 1 verbatim shape from RESEARCH Example 4) |
| `7204698` | feat | CI corpus fixture (Option D) + workflow staging step + fix runtime smoke path + CONTRIBUTING update (deviation Rule 4 architectural — corpus dirs gitignored, ship 5MB subset) |
| `5c6327d` | fix | workflow uses 'python -m pytest' so cwd lands on sys.path (src.* import fix — deviation Rule 1, diagnosed from PR #1 initial-run failure) |
| _(this commit)_ | docs | summary — Wave E complete, GHA gate validated via 2 PRs |

## Files Created/Modified

- `.github/workflows/regression-gate.yml` — GHA workflow (NEW). Triggers on PR + push to main/master. Pins `actions/checkout@v4` + `actions/setup-python@v5`. 10-min timeout. `pip install -r requirements.txt` (no editable install — Pitfall 4). Corpus staging step. `python -m pytest -q` invocation against the 4 gate files.
- `tests/fixtures/corpus/positive/{1,3,4,45}.docx` — 4 positive corpus DOCX (NEW, ~5MB total).
- `tests/fixtures/corpus/negative/{3_formatted_20260413_194927,4_formatted_20260413_185420,45_formatted_20260414_220339}.docx` — 3 negative corpus DOCX matching `tests/baselines/negative_corpus.json` `_metadata.subset_filenames` (NEW).
- `tests/test_rules_quality_acceptance.py` — runtime smoke path fix: `Path("negative_examples") / "3.docx"` → `Path("positive_examples") / "3.docx"` (no behavioral change — assertions are on the report CSV; the original path didn't exist at all).
- `CONTRIBUTING.md` — appended "CI fixture mechanism" section: which subset is shipped, why corpus dirs are gitignored, how to add new files to the gate (update both `_metadata.subset_filenames` AND `tests/fixtures/corpus/`).

## Decisions Made

See `key-decisions` in frontmatter. Three decisions captured: Option D corpus fixture (architectural), `python -m pytest` over bare `pytest` (CI runtime fix), and plan 04-03 filename bug correction (orthogonal fix bundled with fixture commit).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 4 - Architectural — Option D corpus fixture] CI corpus dirs gitignored, must ship subset**
- **Found during:** Task 2 setup (preparing the clean PR)
- **Issue:** Plan 04-05 assumed `positive_examples/` + `negative_examples/` would be present on the CI runner. They are not — both directories are listed in `.gitignore` (~107MB combined) and a fresh GHA checkout starts empty. Without those dirs, the 4 gate test files cannot run.
- **Fix:** Shipped a 5MB subset under `tests/fixtures/corpus/{positive,negative}/`: 4 positives (1.docx, 3.docx, 4.docx, 45.docx) + 3 negatives matching `tests/baselines/negative_corpus.json` `_metadata.subset_filenames` (3_formatted_20260413_194927.docx, 4_formatted_20260413_185420.docx, 45_formatted_20260414_220339.docx). Added a workflow staging step that `mkdir`s `positive_examples/`/`negative_examples/` at CI runtime and copies the fixtures in. No production code path knows about `tests/fixtures/corpus/` — only the workflow.
- **Files modified:** `.github/workflows/regression-gate.yml` (added staging step), `tests/fixtures/corpus/positive/*.docx` (NEW), `tests/fixtures/corpus/negative/*.docx` (NEW), `CONTRIBUTING.md` (documentation).
- **Verification:** Clean-PR CI run #25846822154 = success — all 4 gate files saw their corpus inputs and passed.
- **Committed in:** `7204698`

**2. [Rule 1 - Bug] Bare `pytest` does not put cwd on sys.path; src.* imports fail in CI**
- **Found during:** Task 2 initial PR run (#25846417404 failed)
- **Issue:** Initial Task 1 commit used the verbatim RESEARCH Example 4 shape with `pytest -q ...`. CI run failed at collection time with `ModuleNotFoundError: No module named 'src'`. Root cause class: bare `pytest` (resolved from PATH) does NOT auto-inject cwd into `sys.path` when there is no `pyproject.toml` / `conftest.py` / `setup.py` at the repo root for pytest's rootdir discovery to anchor on. This repo runs pytest locally fine because we install pytest into a venv that has dev-helper conftest setups, but in CI the bare entrypoint hits the bare cwd, and import fails. Same root cause as the pre-existing pyright `src.* not resolved` diagnostic — both are downstream of "no package-roots configured at repo root".
- **Fix:** One-token change: `pytest` → `python -m pytest`. `python -m pytest` runs pytest through the Python entrypoint, which DOES inject cwd into sys.path before the test collector runs. We did NOT add `pyproject.toml` to fix this because: (a) it would expand scope, (b) the rest of the repo runs fine without it, (c) the gate-test layer is the only place this bites today and is now fixed at that layer.
- **Files modified:** `.github/workflows/regression-gate.yml` line 31 (`pytest -q` → `python -m pytest -q`)
- **Verification:** Clean-PR re-run #25846822154 = success; regression-PR run #25847679849 = failure on the expected test, no import errors.
- **Committed in:** `5c6327d`

**3. [Rule 1 - Bug] Plan 04-03 runtime smoke path references non-existent file**
- **Found during:** Task 2 fixture preparation (cross-check of what 04-03 actually reads)
- **Issue:** `tests/test_rules_quality_acceptance.py` runtime smoke hardcoded `Path("negative_examples") / "3.docx"`. But `3.docx` is a POSITIVE corpus file; `negative_examples/3.docx` does not exist (the negative corpus uses `3_formatted_*.docx`). The test happens to pass locally because its assertions are on the report CSV invariants, not on the input-dir identity — but the path is wrong and the test was effectively asserting on whatever `audit-docx` does with a missing input.
- **Fix:** `Path("negative_examples") / "3.docx"` → `Path("positive_examples") / "3.docx"`. Semantically the test still asserts on report CSV invariants; now the input path actually exists.
- **Files modified:** `tests/test_rules_quality_acceptance.py`
- **Verification:** Test passed locally and in CI (clean-PR run #25846822154); behavior of the test unchanged because the assertions never depended on which dir the file came from.
- **Committed in:** `7204698` (bundled with the corpus fixture commit since it's a co-located fix)

---

**Total deviations:** 3 auto-fixed (1 architectural Rule 4 — corpus fixture; 1 Rule 1 bug — CI sys.path; 1 Rule 1 bug — plan 04-03 path).
**Impact on plan:** All three deviations necessary to land a working gate. None expanded scope: Option D is the smallest possible fix (ship the subset, stage at runtime); `python -m pytest` is a one-token change; the 04-03 path fix is a one-line correction that didn't change test behavior. CI gate is live and proven.

## Issues Encountered

- Initial PR run failed at collection time before any gate test could run, with `ModuleNotFoundError: No module named 'src'`. Diagnosis path: local `make regression-gate` works → CI fails before pytest even starts → must be a sys.path issue specific to bare `pytest` on a clean runner with no `pyproject.toml`. Fix verified by re-running CI; resolution time was dominated by the 1m54s per CI run.
- Initial fixture omission: shipped only 4 positives + 3 negatives — caught before opening Task 2 PR by reading the plan's success criteria + `tests/baselines/negative_corpus.json` `_metadata.subset_filenames`.

## What This Enables

- Phase 4 is functionally complete; CI gate is LIVE on `VikaFA04/gost-ml-pipeline`.
- Every future PR touching the rule engine, safe-formatter, regression audit CLI, rule JSON, or any of the 4 gate test files will be auto-checked against the Wave-A-locked per-pair ceilings and the rules-quality invariants.
- Phase 5 (rule profiles & methodical-profile ingestion) and Phase 6 (UI redesign) inherit a working gate — no extra CI work required.
- ROADMAP Phase 4 SC-1 ("audit-regression CLI emits per-pair CSV + summary JSON, bring under the gate") satisfied on CI as well as locally (4th gate file `test_format_regression_audit.py` runs in the workflow).

## Next Phase Readiness

- Phase 4 awaiting verifier sign-off (orchestrator's next step). Roadmap Phase 4 checkbox stays `[ ]` until verifier closes it.
- Plan 04-05 itself fully complete; SUMMARY committed.
- No blockers for Phase 5.

## Self-Check: PASSED

- `.github/workflows/regression-gate.yml` — exists, verified via Read.
- `tests/fixtures/corpus/positive/{1,3,4,45}.docx` — all 4 verified via `ls`.
- `tests/fixtures/corpus/negative/{3_formatted_20260413_194927,4_formatted_20260413_185420,45_formatted_20260414_220339}.docx` — all 3 verified via `ls`.
- Commit `4831a8f` — verified via `git log --oneline -20`.
- Commit `7204698` — verified via `git log --oneline -20`.
- Commit `5c6327d` — verified via `git log --oneline -20`.
- PR #1 (clean) run #25846822154 = success (recorded in verification trail).
- PR #2 (regression) run #25847679849 = failure on expected test (recorded in verification trail).
- Regression branch deleted (no orphan code).

---
*Phase: 04-regression-gate*
*Plan: 05 — Wave E (final)*
*Completed: 2026-05-14*
