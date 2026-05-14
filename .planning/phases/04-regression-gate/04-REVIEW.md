---
status: clean
phase: 04-regression-gate
review_date: 2026-05-14
depth: standard
findings_critical: 0
findings_high: 0
findings_medium: 2
findings_low: 4
---

# Phase 04 Code Review

Scope: source changes in commits `e457708..HEAD` (Waves B/C/D/E). Lens order per CLAUDE.md: Correctness → Security → Architecture → Maintainability. No CRITICAL/HIGH findings — Phase 4 lands clean.

## Lens 1 — Correctness

All advertised acceptance criteria land and are wired end-to-end. Spot checks:

- **Pitfall 1 defence** (`--update-baseline` + `--limit` does not silently overwrite pinned subset with lexicographic-first-N) — `src/evaluation/format_regression_audit.py:229-243` filters `frame` by `_metadata.subset_filenames` BEFORE iterating; missing subset members trigger a `WARNING:` print. Validated by Wave D smoke test #3 (`tmp/wave_d_smoke_baseline.json` left 45.docx/4.docx pairs untouched when `--limit 1` was supplied).
- **Pitfall 2 ordering** (field-level integer gate fires before round-off-vulnerable diff-rate gate) — `tests/test_negative_corpus_diff_rate.py` lines 47 / 64 / 78 are in the prescribed order; default pytest file-order discovery preserves it.
- **Pitfall 6 (`--reason` 8-char strip-minimum)** — `src/main.py:251` `if not reason or len(reason.strip()) < 8` is precise: covers empty, whitespace-only and 7-char in one branch. argparse keeps both flags `required=False` (`src/main.py:403-415`), so non-baseline-update invocations remain unaffected. `tests/test_cli_parser.py:265` loops `("", "   ", "abcdefg")` — all three sub-cases exercise the guard.
- **CI skip-vs-fail idiom** consistent across the two corpus-reading test files: `tests/test_negative_corpus_diff_rate.py:32-35` and `tests/test_rules_quality_acceptance.py:81-84` both do `os.environ.get("CI") == "true"` → `pytest.fail`, else `pytest.skip`. GHA sets `env: CI: "true"` at workflow level (`.github/workflows/regression-gate.yml:9-10`) so the gate cannot silently no-op in CI.
- **CSV BOM handling** consistent: writes use `encoding="utf-8-sig"` (`src/main.py:263`, `build_regression_predictions`), the rules-quality smoke reads back with the same encoding (`tests/test_rules_quality_acceptance.py:98`).
- **Backward compatibility** of `cmd_audit_regression(...)`: new `update_baseline` and `reason` kwargs default to `None` — existing positional/kwarg test callsites in `tests/test_cli_parser.py:130-202` continue to pass.

## Lens 2 — Security (OWASP within diff)

- **T-04-01 (path-traversal via `--update-baseline <path>`)** — `Path(update_baseline)` is consumed by `path.parent.mkdir(parents=True, exist_ok=True)` + `path.write_text(...)`. No `subprocess`, `os.system`, `eval`, `exec`, or shell interpolation anywhere on the path. Operator-supplied path can create arbitrary directories the user has write access to — dev-only utility per CONTRIBUTING.md threat-model note; acceptable.
- **T-04-02 (log/JSON injection via `--reason "<text>"`)** — `reason` is consumed in three places: stored as opaque string in `data[name]["notes"]`, written via `json.dumps(..., ensure_ascii=False)` (control characters auto-escaped by stdlib), and substituted into the WARNING print (`{name}` substitution, not `{reason}`). Never interpolated into a shell command, never `eval`'d.
- **GHA workflow supply chain** — `actions/checkout@v4` + `actions/setup-python@v5` pinned to major versions (RESEARCH Probe 7 WebFetch-verified). Acceptable per T-04-03 medium-severity disposition.
- **Hardcoded secrets / PII / credentials** — none introduced.

## Lens 3 — Architecture

- `write_per_pair_baseline` lives next to `audits_to_frame` in the evaluation layer; the `--reason` length guard lives in the CLI dispatcher (`cmd_audit_regression`) — correct layer split.
- Tests use real `audit_negative_directory` + `audits_to_frame` (no mocked frames or DOCX). Honours CLAUDE.md "избегай мок-БД".
- Makefile `PYTHON ?= python3` portable; CI overrides to ubuntu-latest's system python. GHA stages fixtures from `tests/fixtures/corpus/` into hardcoded `positive_examples/` / `negative_examples/` — couples CI to local test paths, but the trade-off avoids env-var indirection in every corpus-reading test. Acceptable.

## Lens 4 — Maintainability

No functions > 60 lines; no real duplication; no commented-out blocks; no dead code introduced in Phase 4. Imports clean (Wave D added `write_per_pair_baseline` import to `src/main.py` and used it on every invocation). No orphans.

---

## Findings

### MEDIUM

**MD-01: `tests/test_negative_corpus_diff_rate.py:44` — silent gate vacuum when subset filenames don't exist in corpus.**

`frame[frame["negative"].isin(subset_filenames)].reset_index(drop=True)` returns an empty frame if every name in `subset_filenames` is missing from the audited corpus. All three per-pair tests then loop over zero rows, build empty `failures` lists, and pass vacuously. The aggregate-mean test computes `frame["after_diff_rate"].mean()` on an empty Series — returns `NaN`, and `NaN <= ceiling` is `False`, so that one test would actually fail loudly. But the two per-pair tests would silently pass — same class of failure as Pitfall 5 (corpus missing → gate vacuous), at file granularity instead of directory granularity. A future PR that renames a corpus file or removes it from `tests/fixtures/corpus/negative/` without updating `_metadata.subset_filenames` would silently weaken the gate.

Fix: in `_run_audit_for_subset`, after filtering, assert `len(filtered) == len(subset_filenames)` (or `pytest.fail` listing the missing names) — symmetric to the `WARNING:` already in `write_per_pair_baseline:233`. One-liner.

**MD-02: `src/evaluation/format_regression_audit.py:215-216` — docstring claims "writes JSON back atomically", implementation is a plain `write_text`.**

`path.write_text(...)` is a single-syscall write of the whole buffer, but NOT crash-safe in the temp-file-and-rename sense the word "atomic" usually implies. If the dev-only CLI is killed mid-write (Ctrl-C between `mkdir` and `write_text` completion is fine; mid-`write_text` on a non-tmpfs is the risk), `tests/baselines/negative_corpus.json` could be truncated/corrupted. Risk in practice is low (dev-only CLI, short writes, JSON is human-recoverable from git history), but the docstring is misleading and the Wave D summary tech-stack pattern entry repeats it.

Fix: either implement temp-file-and-`os.replace` (real atomic write — 2-3 extra lines), or drop the word "atomic" from the docstring + Wave D summary. The doc fix is the lower-effort path.

### LOW

**LR-01: `src/evaluation/format_regression_audit.py:215-216` — function-local `import json` + `from datetime import datetime, timezone` for no reason.**

Neither `json` nor `datetime` is imported at module top of `format_regression_audit.py`. The inner imports work, but the file has no compelling reason for lazy loading (these are stdlib). Hoist to module top for consistency with `src/main.py` style.

**LR-02: `tests/test_negative_corpus_diff_rate.py:29-44` — `_run_audit_for_subset` is called from each of three tests; each call runs `audit_negative_directory` from scratch over the full ~59-doc corpus (~16-21 min/run per Wave B summary).**

The three tests duplicate ~45-60 min of work locally. Wave B summary acknowledges the trade-off ("not a candidate for local TDD iteration"). For maintainability, an `@pytest.fixture(scope="module")` wrapping the audit call would cut total runtime to one full audit + three cheap frame filters. Not blocking — Wave B explicitly chose this trade-off to avoid a `filenames=[...]` whitelist param on `audit_negative_directory`.

**LR-03: `src/evaluation/format_regression_audit.py:241-243` — seed-scenario branch writes ALL rows in `frame` when `_metadata.subset_filenames` is empty.**

If an operator runs `audit-regression --update-baseline /path/to/new.json --reason "seed" --limit 4`, the helper writes 4 per-pair entries but leaves `_metadata.subset_filenames` empty `[]`. On the next `--update-baseline` against the same file the subset is still empty so EVERY row in the new frame gets written — Pitfall 1's "lexicographic-first-N silently overwrites" failure mode re-surfaces in the seed-then-update path. Real workflow always starts from the existing repo-committed baseline (which already has subset_filenames locked), so this is an edge case. If `--update-baseline` is ever extended to bootstrap fresh baselines, the helper should require an explicit `--subset-filenames` arg or refuse to write when `_metadata.subset_filenames == []`.

**LR-04: `CONTRIBUTING.md:62-66` ("CI fixture mechanism" section) — couples a project-level doc to a specific implementation detail (corpus filename list).**

The doc says "If you change the Wave B `_metadata.subset_filenames`... update `tests/fixtures/corpus/negative/` to match" — this is an honour-system invariant. A pre-commit / CI check that diffs the two sources of truth would close the gap. Out of Phase 4 scope; flagged for a later milestone if drift is observed.

---

_Reviewed: 2026-05-14_
_Reviewer: gsd-code-reviewer_
_Depth: standard_
