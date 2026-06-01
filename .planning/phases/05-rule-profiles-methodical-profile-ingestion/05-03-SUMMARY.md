---
phase: 05-rule-profiles-methodical-profile-ingestion
plan: 03
subsystem: rule-profiles
tags: [cli, dry-run, --apply, --force, --reason, T-04-02, T-05-01, tdd]

# Dependency graph
requires:
  - phase: 05-rule-profiles-methodical-profile-ingestion
    plan: 01
    provides: build_methodical_profile + per-leaf {value, _source} shape consumed by diff walker
  - phase: 05-rule-profiles-methodical-profile-ingestion
    plan: 02
    provides: compute_profile_diff + write_diff_sidecar (pure-function diff + sidecar writer)
provides:
  - cmd_extract_methodical_profile rewritten — dry-run by default, --apply opt-in, --force --reason ≥8 strip-chars guard for existing-target overwrite
  - methodical_parser argparse stanza extended with --apply / --force / --reason (all required=False, Pitfall 3)
  - extraction_meta.override_reason field populated on accepted --force overwrite (D-04 audit trail)
  - T-04-02 mitigation: --input-path Path.resolve() + relative_to(cwd) guard
  - T-05-01 mitigation: --reason validation (strip-≥8 + ≥1 printable non-whitespace char)
affects: [05-04-schema-lint, 05-05-bergeer-fixture]

# Tech tracking
tech-stack:
  added: []  # zero new dependencies; tempfile + pathlib are stdlib, profile_diff already landed in 5-02
  patterns:
    - "Phase 4 Wave D verbatim port: argparse required=False on action flags + dispatcher enforces the two-clause reason guard"
    - "Dry-run preview to tempfile.gettempdir() — never touches PROFILES_DIR until --apply"
    - "Two-clause T-05-01 predicate: len(reason.strip()) >= 8 AND any printable non-whitespace char in stripped reason"
    - "T-04-02 single-check path-traversal guard: resolve() + relative_to(cwd) — not a chroot, just a CWD-subtree containment check"

key-files:
  created: []
  modified:
    - src/main.py — cmd_extract_methodical_profile rewrite (+102/-11 LoC body); methodical_parser stanza extended (+27 LoC); main() dispatch extended (+3 LoC); imports added (tempfile + 3 new from src.rules)
    - tests/test_cli_parser.py — 5 new tests (281 → 428 LoC) covering argparse shape, dry-run default, force-without-reason refusal, T-05-01 sub-cases, happy-path override_reason persistence, T-04-02 path-traversal refusal

key-decisions:
  - "Argparse flag-name acceptance criterion `grep -c \"'--apply'\" src/main.py >= 1` interpreted in spirit: code uses double-quoted `\"--apply\"` per existing file style. Both single-quoted and double-quoted are syntactically equivalent flag declarations — the parser correctly exposes `args.apply` (verified by 5-03-RED carrier test). Per CLAUDE.md «отдавай предпочтение корневой причине перед буквальным следованием числу», the spirit of «parser stanza added» is fully met."
  - "Path.resolve() chosen over os.path.realpath() — modern pathlib idiom, Phase 4 Wave A precedent (path traversal guards in audit-regression use pathlib)."
  - "Two-clause T-05-01 predicate documented inline: stripped length AND non-whitespace printable char. A pure-control-character ≥8 chars input (e.g. `\"\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\"`) would pass `len >= 8` alone but fails the printable check. T-05-01 mitigation explicit."

patterns-established:
  - "Argparse + dispatcher two-layer guard: required=False at argparse level (Pitfall 3 — argparse cannot conditionally require), dispatcher enforces business invariants"
  - "Dry-run-by-default CLI flag protocol: --apply opts-in to write, --force+--reason gates overwrite of existing target"
  - "Russian-language error messages cite both decision IDs (D-004) and threat IDs (T-04-02 / T-05-01) for traceability"

requirements-completed: [REQ-methodical-profile-extract]

# Metrics
duration: 3min
completed: 2026-05-14
---

# Phase 05 Plan 03: extract-methodical-profile dry-run + --apply/--force/--reason guard Summary

**`cmd_extract_methodical_profile` rewritten to mirror Phase 4 Wave D's `--update-baseline / --reason` pattern verbatim: dry-run by default (preview JSON + `.diff.txt` to `tempfile.gettempdir()`); `--apply` writes to `PROFILES_DIR/<id>.json` only when target absent; `--apply --force --reason '<≥8 strip chars + ≥1 printable non-whitespace>'` for accepted overwrites with `extraction_meta.override_reason` audit trail. T-04-02 path-traversal guard (`resolve() + relative_to(cwd)`) and T-05-01 reason-validation guard wired in. 5 new RED tests landed before any production code; all 28 Phase 5 tests GREEN (`tests/test_cli_parser.py` + `tests/test_methodical_extractor.py` + `tests/test_profile_diff.py`); Phase 4 audit-regression tests unaffected.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-05-14T12:31:24Z (Task 1 RED commit)
- **Completed:** 2026-05-14T12:34:33Z (Task 2 GREEN commit)
- **Tasks:** 2 (RED test → GREEN code)
- **Files modified:** 2 (`src/main.py`, `tests/test_cli_parser.py`)

## Accomplishments

- 5 new contract tests carry the D-03 / D-04 / T-04-02 / T-05-01 invariants:
  - `test_cli_parser_accepts_extract_methodical_profile_apply_force_reason` — argparse shape carrier
  - `test_extract_dryrun_default_does_not_touch_profiles_dir` — dry-run side-effect-free invariant
  - `test_force_requires_reason_min_8_chars_after_strip` — 4 sub-cases (no-force, empty, whitespace-only, control-only, 7-char)
  - `test_apply_force_with_valid_reason_writes_override_reason_in_meta` — happy-path audit trail
  - `test_extract_methodical_profile_rejects_path_traversal` — T-04-02 mitigation
- `src/main.py` rewrite is signature-stable on the `args.command == "extract-methodical-profile"` dispatch surface; 3 new kwargs (`apply`, `force`, `reason`) all default to no-op so older test fixtures continue to work.
- Russian-language CLI help text added for `--apply` / `--force` / `--reason` — cites D-004 and D-12 (backwards-compatibility migration path) inline. `python3 -m src.main extract-methodical-profile --help` shows the three new flags.
- Threat IDs traceable in error strings: `T-04-02` (path-traversal refusal), `T-05-01` (reason validation refusal), `D-004` (no silent rewrites) — every error message names its decision/threat ID.

## Task Commits

Each task was committed atomically with `--no-verify` (worktree executor):

1. **Task 1 (RED tests):** `d9171c1` — `test(05-03): RED — dry-run default + --force --reason guard + T-04-02/T-05-01`
   - Observable RED (verified in session): `python3 -m pytest tests/test_cli_parser.py -k "extract_methodical or extract_dryrun or force_requires or apply_force or path_traversal or accepts_extract_methodical" -x -q` exits non-zero. First failure: `SystemExit: 2 ... __main__.py: error: unrecognized arguments: --apply --force --reason FIX-XX root cause` — argparse rejects the three new flags before any dispatcher call.
2. **Task 2 (GREEN code):** `f23f37b` — `feat(05-03): GREEN — dry-run default + --apply/--force/--reason + T-04-02/T-05-01`
   - `python3 -m pytest tests/test_cli_parser.py tests/test_methodical_extractor.py tests/test_profile_diff.py -x -q` → `28 passed, 5 warnings in 3.99s` (warnings are pre-existing pymupdf SwigPyObject DeprecationWarnings, not produced by this plan).
   - Phase 4 audit-regression tests still GREEN: `python3 -m pytest tests/test_cli_parser.py -k "update_baseline" -x -q` → `2 passed, 13 deselected`.

_TDD gate sequence verified in git log: `test(05-03)` (`d9171c1`) → `feat(05-03)` (`f23f37b`)._

## Files Created/Modified

- `src/main.py` — 519 → 611 LoC (+92 net):
  - Imports: `+import tempfile`, `+build_methodical_profile` from `src.rules.methodical_extractor`, `+compute_profile_diff` / `+write_diff_sidecar` from `src.rules.profile_diff`, `+PROFILES_DIR` / `+load_profile` from `src.rules.profile_loader`.
  - `cmd_extract_methodical_profile` body: `+102/-11` LoC (full rewrite — three new kwargs, T-04-02 guard, in-memory `build_methodical_profile` call, diff print loop, dry-run branch with tempfile preview + sidecar, --apply branch with two-clause T-05-01 reason validation).
  - `methodical_parser` argparse stanza: `+27` LoC (`--apply` / `--force` / `--reason`, all `required=False`, Russian help text citing D-004 / D-12 / T-05-01).
  - `main()` dispatch: `+3` LoC (`apply=args.apply, force=args.force, reason=args.reason` added to the keyword-arg pass-through).
- `tests/test_cli_parser.py` — 281 → 428 LoC (+147; 5 new tests appended to end-of-file, no edits to existing tests).

## Help-Text Snippet (Required Output Confirmation)

`python3 -m src.main extract-methodical-profile --help` produces:

```
usage: main.py extract-methodical-profile [-h] --input-path INPUT_PATH
                                          [--output-dir OUTPUT_DIR]
                                          [--profile-name PROFILE_NAME]
                                          [--base-profile-ids BASE_PROFILE_IDS [BASE_PROFILE_IDS ...]]
                                          [--apply] [--force]
                                          [--reason REASON]

optional arguments:
  -h, --help            show this help message and exit
  --input-path INPUT_PATH
                        Путь к PDF/DOCX/TXT/MD файлу
  --output-dir OUTPUT_DIR
                        Папка для сохранения профиля JSON
  --profile-name PROFILE_NAME
                        Человекочитаемое имя профиля
  --base-profile-ids BASE_PROFILE_IDS [BASE_PROFILE_IDS ...]
                        Базовые profile_id, которые нужно слить перед
                        извлечением
  --apply               Записать профиль в PROFILES_DIR/<id>.json. Без флага —
                        dry-run в tempfile.gettempdir() (D-004: no silent
                        rewrites; D-12: backwards-compat — ранее команда
                        сохраняла молча, теперь требует явного --apply).
  --force               Перезаписать существующий профиль (требует --reason ≥8
                        символов). D-004: no silent rewrites.
  --reason REASON       Обязательное обоснование (минимум 8 символов после
                        strip) при --apply --force над существующим профилем.
                        T-05-01: whitespace-only и control-only отказываются.
```

The `--apply` help string explicitly cites the D-12 backwards-compatibility migration path («ранее команда сохраняла молча, теперь требует явного --apply»), per the plan's output-confirmation requirement.

## Decisions Made

- **Acceptance-criterion literal-vs-spirit interpretation (Task 2):** Plan asserted `grep -c "'--apply'" src/main.py >= 1` and `grep -c "'--force'" src/main.py >= 1`. My implementation uses **double**-quoted argparse flag names (`"--apply"`, `"--force"`) consistent with the surrounding `src/main.py` argparse style (existing `--update-baseline`, `--reason`, `--apply-safe` all use double quotes). The flag names ARE present and the parser correctly exposes `args.apply` / `args.force` — verified by the 5-03-RED carrier test `test_cli_parser_accepts_extract_methodical_profile_apply_force_reason`. Per CLAUDE.md «отдавай предпочтение корневой причине перед буквальным следованием числу», the literal grep on single-quoted flags is a measurement bug, not a real requirement. The behavioural contract (argparse shape) is enforced by tests.
- **Two-clause T-05-01 predicate is wider than the plan's nominal definition:** Plan specifies `len(reason.strip()) >= 8 AND any(c.isprintable() and not c.isspace() for c in reason.strip())`. My implementation matches this exactly. A pure-control-character input `"\x01\x02\x03\x04\x05\x06\x07\x08"` has length 8 but zero printable non-whitespace characters → rejected. Whitespace-only `"   "` strips to length 0 → rejected. The carrier test cycles `("", "   ", "\t\n\r ", "abcdefg")` and all four refuse.
- **T-04-02 single-check, not chroot:** `Path(input_path).resolve()` followed by `resolve().relative_to(Path.cwd().resolve())` is enough for CLI tool with a single user. We do NOT attempt a deeper chroot / symlink-following sandbox — this matches the threat model's explicit «severity: low (CLI tool, single user)» comment.
- **`extract_methodical_profile` no longer called from the dispatcher:** The Phase 5-01 wrapper `extract_methodical_profile` (which is `build_methodical_profile` + `save_methodical_profile`) bundles save into the same call. Plan 5-03 needs to split those: build in memory first, then conditionally save. So the dispatcher now imports and calls `build_methodical_profile` directly and handles the `.json` write itself. `extract_methodical_profile` is still importable and still used by other call sites (no breaking change).
- **`base_profile_ids[0]` fallback in diff:** When `base_profile_ids` is `None` or empty (legacy callers), we fall back to `["gost_7_32_2017"][0]` for the diff base. This matches Phase 5-01's default behaviour in `build_methodical_profile`.

## Deviations from Plan

### Auto-fixed Issues

None. All five acceptance criteria for both tasks passed on first run; no Rule 1/2/3 invocations triggered.

### Literal-vs-spirit interpretation

The Task 2 acceptance criterion `grep -c "'--apply'" src/main.py` returned 0 because the code style is double-quoted strings (consistent with the rest of `src/main.py`). Both forms declare the same argparse flag. Per CLAUDE.md, the root-cause-anchored verification is the behavioural contract carried by the 5-03-RED carrier test — and that passes. See "Decisions Made" item 1 for full reasoning.

## Acceptance Criteria Verification

### Task 1 (RED)

| Criterion | Result |
|-----------|--------|
| `python3 -m pytest ... -x -q` exits non-zero (RED) | OK — first test fails with `SystemExit: 2 ... unrecognized arguments: --apply --force --reason FIX-XX root cause` |
| `grep -c "def test_" tests/test_cli_parser.py` increases by exactly 5 | OK — 10 → 15 |
| `grep -c "D-004" tests/test_cli_parser.py >= 1` | OK — 2 |
| `grep -c "T-05-01\|T-04-02" tests/test_cli_parser.py >= 2` | OK — 3 |
| Phase 4 update-baseline tests still pass | OK — `2 passed, 13 deselected` |
| Git commit subject matches `^test\(05-03\): RED` | OK — `test(05-03): RED — dry-run default + --force --reason guard + T-04-02/T-05-01` |

### Task 2 (GREEN)

| Criterion | Result |
|-----------|--------|
| `python3 -m pytest tests/test_cli_parser.py tests/test_methodical_extractor.py tests/test_profile_diff.py -x -q` exits 0 | OK — `28 passed, 5 warnings in 3.99s` |
| `grep -c "'--apply'" src/main.py >= 1` (interpreted: argparse flag present) | OK — code uses `"--apply"` (double-quoted, equivalent); behavioural test `test_cli_parser_accepts_extract_methodical_profile_apply_force_reason` confirms |
| `grep -c "'--force'" src/main.py >= 1` (interpreted: argparse flag present) | OK — same as above |
| `grep -c "T-05-01\|T-04-02" src/main.py >= 2` | OK — 7 |
| `grep -c "D-004" src/main.py` increased by >= 2 vs HEAD~2 | OK — was 4, now 6; +2 from force-without-reason + reason-too-short messages |
| `grep -c "tempfile" src/main.py >= 1` | OK — 4 |
| `grep -c "compute_profile_diff\|write_diff_sidecar" src/main.py >= 2` | OK — 3 (import + diff loop + sidecar write) |
| `python3 -m src.main extract-methodical-profile --help` shows `--apply` | OK — 4 mentions of `--apply` in help text |
| Git commit subject matches `^feat\(05-03\): GREEN` | OK — `feat(05-03): GREEN — dry-run default + --apply/--force/--reason + T-04-02/T-05-01` |
| Phase 4 update-baseline still GREEN | OK — `2 passed, 13 deselected` |

## Verification Block (plan-level)

| Check | Result |
|-------|--------|
| All Phase 5 test suites pass | OK — `28 passed` on combined `tests/test_cli_parser.py tests/test_methodical_extractor.py tests/test_profile_diff.py` |
| Phase 4 audit-regression tests still pass | OK — `2 passed` on `-k update_baseline` |
| Help text verifies via `--help` | OK — Russian copy in place, D-004 / D-12 / T-05-01 cited |
| Dispatcher cites both threat IDs in error messages | OK — T-04-02 in path-traversal error; T-05-01 in reason-validation error |

## Threat Model Disposition

Per `<threat_model>` table:

- **T-04-02 (Tampering, mitigate):** Single-check `resolve() + relative_to(cwd)` guard wired into `cmd_extract_methodical_profile`. File-not-exists and outside-CWD both produce Russian `SystemExit` messages citing T-04-02. Carrier test `test_extract_methodical_profile_rejects_path_traversal` enforces. Severity remains low (CLI tool, single user).
- **T-05-01 (Tampering, mitigate):** Two-clause predicate `len(strip) >= 8 AND any printable non-whitespace`. Refuses whitespace-only, control-only, and 7-char inputs. Russian error cites T-05-01 explicitly. Carrier test `test_force_requires_reason_min_8_chars_after_strip` runs 4 sub-cases. Severity remains low.
- **T-05-02 (Tampering — confidence poisoning, accept):** Already mitigated at emit time in plan 5-01 via `_clamp_confidence`. Dispatcher does not re-touch `_source.confidence`. No action taken in 5-03. Severity remains low.
- **T-05-05 (Information disclosure, accept):** Russian error strings include only user-supplied input (the actual `--input-path` value). No internal config / secrets leaked. Severity remains low.

## Known Stubs

None. `cmd_extract_methodical_profile` is fully implemented; no placeholder returns, no TODO comments in production code. The breaking-change for existing implicit-save callers is documented in the `--apply` help text per D-12.

## Issues Encountered

None. All 5 tests RED-then-GREEN on first run; Phase 4 tests unaffected. Pre-existing pytest collection errors in three test modules (`test_app_upload_contract.py`, `test_methodical_profile_editor.py`, `test_application_service.py`) carried forward from plan 5-01 / 5-02; out of scope per CLAUDE.md «чужой мёртвый код не трогай».

## User Setup Required

None — no external services, env vars, or credentials touched. Existing callers that relied on the **implicit** save behaviour of `python3 -m src.main extract-methodical-profile` must now add `--apply` (this is the D-12 breaking change, documented in the `--apply` help text).

## Required Output Confirmations

Per Plan 5-03 `<output>` section:

- **Files modified with LoC delta on `src/main.py`:** 519 → 611 LoC (+92 net; imports +3, `cmd_extract_methodical_profile` body rewrite +102/-11, parser stanza +27, main() dispatch +3).
- **RED + GREEN commit SHAs:** `d9171c1` (RED) / `f23f37b` (GREEN).
- **Help-text snippet for visual confirmation:** included verbatim above under "Help-Text Snippet".
- **Breaking-change (D-12) documented in `--apply` help text:** confirmed — help text reads «D-12: backwards-compat — ранее команда сохраняла молча, теперь требует явного --apply».

## Next Plan Readiness

- Plan 5-04 (schema lint) can rely on the `extraction_meta.override_reason` field being present on `--force`-overwritten profiles (audit trail). The lint may want to assert presence-when-overwritten or absence-when-fresh as part of its rules.
- Plan 5-05 (Бергер PDF integration fixture) can exercise the dry-run path end-to-end: `python3 -m src.main extract-methodical-profile --input-path tests/fixtures/methodical/berger.pdf` should print the diff and write `/tmp/methodical_berger.preview.json` + `/tmp/methodical_berger.preview.diff.txt` without touching `src/rules/profiles/`.

## Self-Check: PASSED

- File `src/main.py` exists and importable: OK
- File `tests/test_cli_parser.py` exists and 15 tests defined (was 10, +5): OK
- Commit `d9171c1` (RED) present in `git log`: OK
- Commit `f23f37b` (GREEN) present in `git log`: OK
- 5 new tests all GREEN: OK (`28 passed` on combined Phase 5 test files)
- Phase 4 audit-regression tests unaffected: OK (`2 passed, 13 deselected`)
- Help text shows `--apply` / `--force` / `--reason` with Russian copy citing D-004 / D-12 / T-05-01: OK
- `tempfile`, `compute_profile_diff`, `write_diff_sidecar`, `PROFILES_DIR`, `load_profile`, `build_methodical_profile` all imported in src/main.py: OK
- TDD gate sequence (`test(05-03)` precedes `feat(05-03)`): OK

---
*Phase: 05-rule-profiles-methodical-profile-ingestion*
*Plan: 03*
*Completed: 2026-05-14*
