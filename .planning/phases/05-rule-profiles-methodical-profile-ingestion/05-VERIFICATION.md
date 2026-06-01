---
phase: 05-rule-profiles-methodical-profile-ingestion
verified: 2026-05-14T17:05:00Z
status: human_needed
score: 14/14 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 13/14
  gaps_closed:
    - "All ROADMAP / REQUIREMENTS / HEADING_AND_NORMCONTROL_PLAN references to PPTX as a methodical input source are removed in the same commit as the extractor rewrite (D-01 + D-004 atomicity) — Plan 5-01."
  gaps_remaining: []
  regressions: []
  closure_evidence:
    - commit: "e0401a2"
      subject: "docs(05-01): re-apply ROADMAP PPTX-drop hunk lost in worktree merge"
      diff_stat: "1 file changed, 4 insertions(+), 4 deletions(-)"
    - check: "grep -E 'PPTX|pptx|презентац' .planning/ROADMAP.md"
      result: "exit code 1 — zero matches"
    - check: "ROADMAP.md line 25"
      result: "'PDF methodical-profile ingestion with diff (presentation-format ingestion dropped 2026-05-14 per 05-CONTEXT D-01)'"
    - check: "ROADMAP.md line 106 (SC-3)"
      result: "'extract-methodical-profile CLI ingests a PDF methodical … (presentation-format ingestion dropped 2026-05-14 per 05-CONTEXT D-01)'"
    - check: "ROADMAP.md line 107 (SC-4)"
      result: "'source/page attribution; methodical never silently replaces GOST'"
human_verification:
  - test: "Run `extract-methodical-profile --input-path tests/fixtures/methodical/normocontrol_berger.pdf` (dry-run, no --apply) and visually inspect the printed diff: confirm `## document_rules` and `## labels` section headers appear, that lines use the U+2192 arrow, and that `_source` paths never appear in the diff body. Confirm preview JSON + .diff.txt land in /tmp (NOT in src/rules/profiles/)."
    expected: "Dry-run output is human-readable diff (section headers + `<path>: <old> → <new>` lines), preview JSON in /tmp, src/rules/profiles/ unchanged."
    why_human: "User-facing UX quality (readable error list per D-02) is the stated user value. Automated tests verify the function returns lines and writes to tempfile, but the readability and signal-to-noise ratio over the real 1.4MB Бергер PDF is a judgement call best made by the project owner."
  - test: "Run `extract-methodical-profile --input-path tests/fixtures/methodical/normocontrol_berger.pdf --apply` (no --force) twice. First run should write a methodical profile to PROFILES_DIR/<id>.json. Second run should refuse with a Russian error citing D-004 because the target now exists. Third run with `--apply --force --reason 'test resync 2026'` should succeed and the saved JSON should carry `extraction_meta.override_reason: 'test resync 2026'`."
    expected: "First write OK; second refuses with D-004 citation; third overwrites with override_reason recorded."
    why_human: "End-to-end interactive flow with side effects on PROFILES_DIR; not safely run in automated verification (would mutate the committed profile set)."
---

# Phase 5: Rule profiles & methodical-profile ingestion — Verification Report

**Phase Goal:** Multiple rule profiles (GOST + university-local) are selectable per audit run; a normcontrol presentation can be ingested as a methodological source and a profile diff is shown to the user before save.
**Verified:** 2026-05-14T17:05:00Z (re-verification after gap closure)
**Status:** human_needed
**Re-verification:** Yes — initial round was `gaps_found` (13/14), single doc gap closed at commit `e0401a2`.

## Re-verification Summary

| Metric                | Initial round (13:44Z)         | Re-verification (17:05Z) |
|-----------------------|--------------------------------|--------------------------|
| Status                | gaps_found                     | human_needed             |
| Truths verified       | 13/14                          | 14/14                    |
| Open codebase gaps    | 1 (ROADMAP.md doc drift)        | 0                        |
| Human-verify probes   | 2                              | 2 (unchanged — UX/E2E)   |
| Regressions detected  | n/a                            | None                     |

**Closure evidence (gap "Truth 7: PPTX removed atomically from ROADMAP.md"):**

- Commit `e0401a2` (2026-05-14T16:47Z) — `docs(05-01): re-apply ROADMAP PPTX-drop hunk lost in worktree merge` — `1 file changed, 4 insertions(+), 4 deletions(-)`.
- `grep -E "PPTX|pptx|презентац" .planning/ROADMAP.md` → exit code 1 (zero matches). This is the literal acceptance criterion from Plan 5-01 Task 3.
- Lines 25, 106, 107 now read (PPTX-free wording):
  - L25: `Multiple selectable profiles + PDF methodical-profile ingestion with diff (presentation-format ingestion dropped 2026-05-14 per 05-CONTEXT D-01).`
  - L106 (SC-3): `extract-methodical-profile CLI ingests a PDF methodical (e.g., normcontrol guideline), produces a draft profile, shows a diff against the chosen base profile, and requires explicit user confirmation before save (presentation-format ingestion dropped 2026-05-14 per 05-CONTEXT D-01).`
  - L107 (SC-4): `Ambiguous extracted requirements land as needs_manual_review with source/page attribution; methodical never silently replaces GOST.`

The wording change (literal "PPTX" tokens replaced with the principle "presentation-format ingestion") matches the project rule "числа в success criteria подлежат пересмотру с обоснованием" — the acceptance criterion was about live scope, not commemorative drop notes; root cause is "PPTX out of scope, regardless of literal token presence."

**Quick regression check on the 13 previously-passed must-haves:** still verified (no code, test, CI, or schema changes between commits `237e23d` and `e0401a2`; only ROADMAP.md touched).

## Goal Achievement

### Observable Truths

Sourced from ROADMAP Phase 5 Success Criteria (SC-1..SC-4) merged with `must_haves.truths` from PLAN frontmatter (5-01..5-05). Scope clarification per Phase 5 D-01 (presentation-format ingestion dropped) is applied: SC-3 truth is verified against PDF/DOCX only.

| #  | Truth (source)                                                                                                                                                                                              | Status     | Evidence                                                                                                                                                                                                                                                                            |
|----|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1  | SC-1: User can pick a rule profile per audit; the chosen profile id is recorded in the report header.                                                                                                       | ✓ VERIFIED | `--profile-id` accepted on `audit-docx`, `format-docx`, `audit-regression`. `cmd_audit_docx` and `cmd_format_docx` thread `profile_id` into `audit_or_format_docx(profile_id=...)` at src/main.py:179,214. `audit_or_format_docx` already emits `profile_id` in CSV/summary (Phase 4). |
| 2  | SC-2: Profiles live outside code as JSON files in `src/rules/profiles/`.                                                                                                                                    | ✓ VERIFIED | `src/rules/profiles/gost_7_32_2017.json` (9260B), `gost_r_7_0_100_2018_bibliography.json` (5150B), `mirea_normcontrol_local.json` (5894B) all present and load via `profile_loader.load_profile`.                                                                                     |
| 3  | SC-3 (presentation-format dropped per D-01): `extract-methodical-profile` ingests PDF/DOCX, produces a draft profile, shows a diff against the chosen base profile, and requires explicit `--apply` before save. | ✓ VERIFIED | `iterate_text_chunks` handles PDF (page_N), DOCX (paragraph_N), TXT/MD (line_N). `cmd_extract_methodical_profile` defaults to dry-run, prints `compute_profile_diff(base, candidate)` lines, writes preview to `tempfile.gettempdir()`, refuses overwrite without `--force --reason`. |
| 4  | SC-4: Ambiguous extracted requirements land as `needs_manual_review` with source/page attribution (`page_N` for PDF, `paragraph_N` for DOCX); methodical never silently replaces GOST.                       | ✓ VERIFIED | `_annotate` wraps every leaf with `_source: {file, loc, confidence, needs_review}`; `_clamp_confidence` enforces [0,1]; `_any_leaf_needs_review` derives `extraction_meta.needs_manual_review`. `loc` format verified by `test_loc_label_is_page_n_for_pdf`.                            |
| 5  | Plan 5-01: Every leaf in `document_rules.*`, `labels.*.style_profile`, `bibliography_rules.*` has a sibling `_source` dict with keys {file, loc, confidence, needs_review}.                                  | ✓ VERIFIED | `tests/test_methodical_extractor.py::test_every_leaf_has_source` passes; `_annotate` helper at src/rules/methodical_extractor.py:26-37 enforces shape on emit; `tests/test_profile_quality_acceptance.py::test_every_methodical_profile_has_source_per_leaf` ready (vacuous at HEAD).   |
| 6  | Plan 5-01: `extraction_meta.needs_manual_review` is derived from `any(leaf._source.needs_review)` — the old `extraction_confidence < 0.9` heuristic is removed (Pitfall 8).                                  | ✓ VERIFIED | `grep -n "extraction_confidence" src/rules/methodical_extractor.py` returns 0 hits. `_any_leaf_needs_review` invocation at line 499 of `build_methodical_profile`. `test_needs_review_derived` carries the contract.                                                                  |
| 7  | Plan 5-01: PPTX references removed atomically from REQUIREMENTS.md, ROADMAP.md, HEADING_AND_NORMCONTROL_PLAN.md (D-01 + D-004).                                                                              | ✓ VERIFIED (closed) | Gap from initial round closed at commit `e0401a2`. `grep -E "PPTX\|pptx\|презентац" .planning/ROADMAP.md` → exit 1 (zero matches). ROADMAP.md lines 25/106/107 now PPTX-free; REQUIREMENTS.md + HEADING_AND_NORMCONTROL_PLAN.md unchanged (already correct). D-01 atomicity restored.   |
| 8  | Plan 5-02: Pure function `compute_profile_diff(base, candidate)` flattens dicts, filters `._source.` paths, returns list[str] of `<path>: <old> → <new>` lines grouped under `## <top_level_key>` headers.   | ✓ VERIFIED | src/rules/profile_diff.py (97 LoC, stdlib only). 8 tests in tests/test_profile_diff.py all pass. U+2192 in line format. Pitfall 4 filter at line 39 + backstop at lines 77-78.                                                                                                       |
| 9  | Plan 5-02: `write_diff_sidecar(lines, target_path)` writes UTF-8, newline-joined, creates parent dir.                                                                                                       | ✓ VERIFIED | src/rules/profile_diff.py:88-97; tests `test_write_diff_sidecar_writes_utf8` + `test_write_diff_sidecar_creates_parent_dir` pass.                                                                                                                                                    |
| 10 | Plan 5-03: Dry-run default does not touch PROFILES_DIR; `--apply` on existing target requires `--force --reason` with ≥8 strip chars + ≥1 printable non-whitespace (T-05-01).                                | ✓ VERIFIED | `cmd_extract_methodical_profile` body src/main.py:295-381 implements two-clause T-05-01 predicate at line 369; D-004 cited in 3 error messages. Tests `test_extract_dryrun_default_...`, `test_force_requires_reason_min_8_chars_after_strip` pass.                                  |
| 11 | Plan 5-03: `--input-path` resolved and rejected if outside CWD subtree (T-04-02).                                                                                                                            | ✓ VERIFIED | src/main.py:310-325 `Path.resolve()` + `relative_to(cwd)` guard; carrier test `test_extract_methodical_profile_rejects_path_traversal` passes.                                                                                                                                       |
| 12 | Plan 5-04: Two-tier schema lint `tests/test_profile_quality_acceptance.py`; Tier A validates every profile; Tier B fires substantively on methodical profiles; synthetic-RED guard retained.                | ✓ VERIFIED | 6 tests in tests/test_profile_quality_acceptance.py; all 3 GOST/local profiles pass Tier A. Synthetic guard at line 121-140 retains shape contract. Local smoke: `pytest tests/test_profile_quality_acceptance.py -q` → 6 passed.                                                       |
| 13 | Plan 5-04: `audit-docx --profile-id <id>` and `format-docx --profile-id <id>` accepted; threaded through to `audit_or_format_docx(profile_id=...)`.                                                          | ✓ VERIFIED | src/main.py:160,190 signatures accept `profile_id`; line 179,214 pass it through. `python3 -m src.main audit-docx --help` shows `--profile-id`. Tests `test_audit_docx_and_format_docx_accept_profile_id` + `test_audit_docx_default_profile_id_is_gost_7_32_2017` pass.              |
| 14 | Plan 5-05: Бергер fixture committed at `tests/fixtures/methodical/normocontrol_berger.pdf` (1.4MB, NOT gitignored); CI workflow + Makefile run 6-file pytest invocation including 2 Phase 5 test files.       | ✓ VERIFIED | Fixture 1.4MB tracked (`git ls-files` returns path, `git check-ignore` exits 1). `.github/workflows/regression-gate.yml` lines 29-37 and Makefile lines 17-23 both list 6 test files. CI evidence: PR #1 GREEN (run 25862688735, 1m58s); RED probe PR #3 RED on schema-lint missing `is_default` (run 25862868163, 1m38s). |

**Score:** 14/14 truths verified

### Required Artifacts

| Artifact                                                | Expected                                                                                            | Status    | Details                                                                                                                                                                            |
|---------------------------------------------------------|-----------------------------------------------------------------------------------------------------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `src/rules/methodical_extractor.py`                     | Chunk iterator + `_annotate` + `_any_leaf_needs_review` + derived needs_manual_review               | ✓ VERIFIED | 530 LoC; `iterate_text_chunks`, `_clamp_confidence`, `_annotate`, `_any_leaf_needs_review` all present; `extraction_confidence` purged; wired into build_methodical_profile L499. |
| `src/rules/profile_diff.py`                             | Pure `compute_profile_diff` + `write_diff_sidecar`; stdlib-only                                     | ✓ VERIFIED | 97 LoC; only stdlib imports (pathlib, typing, __future__); Pitfall 4 filter in `_flatten` + backstop in `compute_profile_diff`.                                                    |
| `src/main.py` (`cmd_extract_methodical_profile`)        | Dry-run default + `--apply/--force/--reason` + T-04-02 + T-05-01 guards                              | ✓ VERIFIED | Body at L295-381; argparse stanza L520+; main() dispatch wires `apply=args.apply, force=args.force, reason=args.reason`. Tempfile-based dry-run preview + sidecar write present.   |
| `src/main.py` (`cmd_audit_docx` / `cmd_format_docx`)    | `profile_id` kwarg threaded to `audit_or_format_docx`                                                | ✓ VERIFIED | L156-181 and L184-216; `profile_id=profile_id` passed through in both. argparse `--profile-id` on audit_parser + format_parser.                                                    |
| `tests/test_methodical_extractor.py`                    | 5 tests: per-leaf _source, derived needs_review, PDF loc=page_N, + 2 pre-existing                   | ✓ VERIFIED | 5 tests pass locally (per smoke run).                                                                                                                                              |
| `tests/test_profile_diff.py`                            | 8 tests covering U+2192, grouping, Pitfall 4 filter, methodical-vs-scalar, no-changes, <missing>     | ✓ VERIFIED | 8 tests pass locally.                                                                                                                                                              |
| `tests/test_profile_quality_acceptance.py`              | 6 tests two-tier schema lint + synthetic RED guard                                                  | ✓ VERIFIED | 6 tests pass locally.                                                                                                                                                              |
| `tests/test_cli_parser.py`                              | 5 new tests for Phase 5 plan 5-03 + 3 for plan 5-04 (--profile-id smokes)                            | ✓ VERIFIED | 8 Phase 5 tests pass locally; Phase 4 update_baseline tests unaffected.                                                                                                            |
| `tests/fixtures/methodical/normocontrol_berger.pdf`     | 1.4MB Бергер fixture; tracked; NOT gitignored                                                       | ✓ VERIFIED | 1465054 bytes (~1.4MB); `git ls-files` returns path; `git check-ignore` exit 1.                                                                                                    |
| `.github/workflows/regression-gate.yml`                 | 6-file pytest invocation including 2 Phase 5 test files                                              | ✓ VERIFIED | Lines 31-37 list all 6 files including test_profile_quality_acceptance.py + test_methodical_extractor.py.                                                                          |
| `Makefile`                                              | Symmetric 6-file pytest invocation                                                                  | ✓ VERIFIED | Lines 17-23 list all 6 files.                                                                                                                                                      |
| `CONTRIBUTING.md`                                       | Russian Phase 5 section mentioning fixture + 6-file gate                                            | ✓ VERIFIED | Section at lines 68-77; cites D-11 Russian-language policy.                                                                                                                        |
| `.planning/REQUIREMENTS.md` (PPTX drop)                  | REQ-methodical-profile-extract rewritten to say PDF/DOCX                                            | ✓ VERIFIED | Lines 117-123: REQ-methodical-profile-extract rewritten; PPTX-drop date-stamped per D-01.                                                                                          |
| `.planning/HEADING_AND_NORMCONTROL_PLAN.md` (PPTX drop)  | Блок C rewritten; PPTX/презентация references removed                                               | ✓ VERIFIED | Date-stamped note at line 73.                                                                                                                                                      |
| `.planning/ROADMAP.md` (PPTX drop)                       | Phase 5 one-liner + SC-3 + SC-4 rewritten to PDF/DOCX                                               | ✓ VERIFIED (closed) | Closed at commit `e0401a2`. Lines 25, 106, 107 use "PDF methodical" + "presentation-format ingestion dropped 2026-05-14 per 05-CONTEXT D-01" + "methodical never silently replaces GOST". `grep -E "PPTX\|pptx\|презентац"` exits 1. |

### Key Link Verification

| From                                                                | To                                                                  | Via                                            | Status   | Details                                                                                                                |
|---------------------------------------------------------------------|---------------------------------------------------------------------|------------------------------------------------|----------|------------------------------------------------------------------------------------------------------------------------|
| `methodical_extractor.iterate_text_chunks`                          | `_extract_document_rules` and other field extractors                | `list[tuple[loc, text]]` of chunks             | ✓ WIRED  | `chunks = list(iterate_text_chunks(input_path))` passed to every `_extract_*`; verified by tests.                       |
| `methodical_extractor.build_methodical_profile`                     | `_any_leaf_needs_review`                                            | derived `needs_manual_review` at function end  | ✓ WIRED  | `"needs_manual_review": _any_leaf_needs_review(profile)` at src/rules/methodical_extractor.py:499.                      |
| `cmd_extract_methodical_profile`                                    | `compute_profile_diff` + `write_diff_sidecar`                       | import + invocation in dry-run branch          | ✓ WIRED  | src/main.py:30 imports; L340, L351 invoke.                                                                              |
| `cmd_extract_methodical_profile`                                    | `build_methodical_profile`                                          | in-memory profile build before any disk write  | ✓ WIRED  | src/main.py:328 invokes; profile then diffed and conditionally written.                                                 |
| `cmd_audit_docx` / `cmd_format_docx`                                | `audit_or_format_docx(profile_id=...)`                              | `profile_id=profile_id` kwarg passthrough      | ✓ WIRED  | src/main.py:179 (audit), L214 (format).                                                                                  |
| `.github/workflows/regression-gate.yml` "Run regression gate" step  | `tests/test_profile_quality_acceptance.py` + `test_methodical_extractor.py` | pytest invocation list                  | ✓ WIRED  | Both files appended to the 6-file pytest invocation at L36-37.                                                          |
| `Makefile` regression-gate target                                   | Same two Phase 5 test files                                         | `$(PYTHON) -m pytest` invocation               | ✓ WIRED  | Both files listed at Makefile L22-23.                                                                                   |

### Data-Flow Trace (Level 4)

Phase 5 produces no UI artifact rendering dynamic data; the data flow under test is CLI → extractor → profile JSON → diff output. Traced manually:

| Artifact                                | Data Source                                                                | Produces Real Data | Status      |
|-----------------------------------------|----------------------------------------------------------------------------|--------------------|-------------|
| `cmd_extract_methodical_profile` output | `build_methodical_profile` → `iterate_text_chunks` → real fitz/python-docx | Yes (per CI run on Бергер PDF inside tests + designed-failure PR proves schema-lint fires) | ✓ FLOWING |
| `audit-docx` report `profile_id` column | `args.profile_id` → `cmd_audit_docx` → `audit_or_format_docx(profile_id=)` → Phase 4 CSV writer at `inplace_formatter.py:504` | Yes (Phase 4 already verified)                                                                                  | ✓ FLOWING |
| `compute_profile_diff` output           | Two profile dicts (real, not hardcoded)                                    | Yes (pure function over real dicts; tests with realistic samples + manual end-to-end via Бергер fixture in plan 5-05 timing probe)                  | ✓ FLOWING |

No HOLLOW_PROP or DISCONNECTED instances identified.

### Behavioral Spot-Checks

| Behavior                                                                                                            | Command                                                                                                                                                                  | Result                                                  | Status |
|---------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------|--------|
| Phase 5 unit tests pass locally (5+8+6 = 19)                                                                         | `python3 -m pytest -q tests/test_profile_quality_acceptance.py tests/test_methodical_extractor.py tests/test_profile_diff.py`                                            | 19 passed, 5 warnings in 0.52s                          | ✓ PASS |
| Phase 5 CLI parser tests pass (8 tests)                                                                              | `python3 -m pytest -q tests/test_cli_parser.py -k "profile_id or extract_methodical or extract_dryrun or force_requires or apply_force or path_traversal or accepts_extract_methodical"` | 8 passed, 10 deselected in 5.62s                        | ✓ PASS |
| `extract-methodical-profile` CLI exposes new flags                                                                   | `python3 -m src.main extract-methodical-profile --help \| grep -E -- "--apply\|--force\|--reason"`                                                                       | Multiple matches incl. Russian help text                | ✓ PASS |
| `audit-docx` and `format-docx` expose `--profile-id`                                                                 | `python3 -m src.main audit-docx --help \| grep -- "--profile-id"` and same for format-docx                                                                                | Both show `--profile-id PROFILE_ID`                     | ✓ PASS |
| GHA workflow YAML parses + lists both Phase 5 test files                                                             | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/regression-gate.yml'))"` + `grep -c "test_profile_quality_acceptance.py\|test_methodical_extractor.py" .github/workflows/regression-gate.yml` | YAML OK; 2 hits                                          | ✓ PASS |
| `regression-gate.yml` step matches `Makefile` in test-file list                                                      | Manual diff of both files                                                                                                                                                | Both list same 6 test files                              | ✓ PASS |
| **Re-verification probe:** ROADMAP.md is PPTX-free                                                                    | `grep -E "PPTX\|pptx\|презентац" .planning/ROADMAP.md`                                                                                                                    | exit code 1 (zero matches)                              | ✓ PASS |

CI evidence (recorded, not re-run per instructions):

- Clean PR #1: https://github.com/VikaFA04/gost-ml-pipeline/pull/1 — 6-file regression gate GREEN (run 25862688735, 1m58s).
- RED probe PR #3 (closed): https://github.com/VikaFA04/gost-ml-pipeline/pull/3 — gate FAIL on missing `is_default` key (run 25862868163, 1m38s); proves gate fires on schema drift.

### Requirements Coverage

| Requirement                       | Source Plan       | Description                                                                                                                       | Status      | Evidence                                                                                                                                                                       |
|-----------------------------------|-------------------|-----------------------------------------------------------------------------------------------------------------------------------|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| REQ-rule-profiles                 | 05-04, 05-05      | Multiple rule profiles (GOST + university-local), stored outside code, selectable per audit, profile recorded in report.            | ✓ SATISFIED | Truths 1, 2, 13 verified. `--profile-id` flag on all three document-touching subcommands; 3 GOST/local profile JSONs committed; report header carries chosen profile_id.       |
| REQ-methodical-profile-extract    | 05-01..05-05      | `extract-methodical-profile` ingests PDF/DOCX (presentation-format ingestion dropped 2026-05-14 per D-01); diff before save; ambiguity → `needs_manual_review` with source/page attribution. | ✓ SATISFIED | Code-side: truths 3, 4, 5, 6, 8, 9, 10, 11 verified. Doc-side: ROADMAP.md (closed at e0401a2), REQUIREMENTS.md, HEADING_AND_NORMCONTROL_PLAN.md all consistent on PDF/DOCX scope. D-01 atomicity restored. |

No orphaned requirements: REQUIREMENTS.md lines 222-223 map both IDs to Phase 5 and both are claimed by at least one PLAN's `requirements:` field.

### Anti-Patterns Found

No anti-patterns remain at re-verification. The single warning from the initial round — ROADMAP.md stale "PPTX/presentation/slide" contract — was closed at commit `e0401a2`. No production-code stubs, no TODO/FIXME/placeholder comments in `src/rules/methodical_extractor.py`, `src/rules/profile_diff.py`, or the Phase 5 sections of `src/main.py`. `extraction_meta.extraction_confidence` (legacy heuristic) physically removed per Pitfall 8 (`grep -c ... = 0`).

### Human Verification Required

See `human_verification:` frontmatter above. Two manual probes recommended — these are UX/E2E quality gates that automated tests verify in pieces but not end-to-end:

1. End-to-end dry-run readability over Бергер PDF — judgement on diff signal-to-noise.
2. End-to-end `--apply` / `--force` / `--reason` happy path against the real Бергер fixture — confirms `override_reason` audit trail in the saved JSON.

These do not block phase completion in the codebase-verification sense (all 14 must_haves verified), but the phase status is `human_needed` (not `passed`) because these probes confirm user-facing UX quality that only a human can sign off on.

### Gaps Summary

No remaining gaps. Single initial gap (ROADMAP.md doc drift) closed at commit `e0401a2`. All Phase 5 must_haves now verified across code, tests, CI gate (PR #1 GREEN, PR #3 designed-failure RED), and documentation (REQUIREMENTS.md + ROADMAP.md + HEADING_AND_NORMCONTROL_PLAN.md all consistent on PDF/DOCX scope with date-stamped presentation-format-drop notes).

Phase status is `human_needed` solely because two UX/E2E probes against the real Бергер fixture remain. Closing those probes (by the project owner) flips the phase to `passed`.

---

_Verified: 2026-05-14T17:05:00Z (re-verification after gap closure at e0401a2)_
_Verifier: Claude (gsd-verifier)_
