# Phase 5: Rule profiles & methodical-profile ingestion — Context

**Gathered:** 2026-05-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Convert the partially-built methodical-profile extractor (`src/rules/methodical_extractor.py` + `cmd_extract_methodical_profile` already wired) into a production tool that satisfies ROADMAP Phase 5 SC-1..SC-4 — minus the PPTX requirement. The user has a real PDF методичка (`normocontrol/Нормоконтроль 2026.pdf`, 9.4MB current + `Нормоконтроль Бергер.pdf` 1.4MB Феврал 2026), the extractor will be exercised against it end-to-end.

The work is **gap closure**, not greenfield. Phases 1-4 already shipped: 3 profile JSON files (`gost_7_32_2017`, `gost_r_7_0_100_2018_bibliography`, `mirea_normcontrol_local`), `profile_loader.deep_merge`, `profile_validator`, PDF/DOCX/TXT/MD text extraction, regex-based field extraction, `--profile-id` flag on audit commands, whole-profile `extraction_meta.needs_manual_review` flag.

In scope (six concrete gaps surfaced by Area A codebase audit):

1. **Diff generator** — unified text diff over flattened JSON paths between the extracted candidate profile and base profile(s). Output: stdout + sidecar `.diff.txt` next to candidate JSON. Format per-line: `document_rules.page.margin_left_cm: 3.0 → 2.5`. Section headers group paths by top-level key.
2. **Dry-run-by-default + `--apply` flag** — `extract-methodical-profile` writes the candidate profile to temp/preview path, prints diff, refuses to overwrite an existing `PROFILES_DIR/<id>.json`. With `--apply --force --reason "<text ≥8 chars>"`, overwrites (mirrors Phase 4 D-13 `--update-baseline / --reason` pattern + 8-char strip-minimum per Phase 4 RESEARCH Probe 6).
3. **Per-field source attribution** — every extracted field carries `_source: {file, loc, confidence, needs_review}`. `loc` = `"page_N"` for PDF, `"paragraph_N"` for DOCX. Whole-profile `needs_manual_review` becomes **derived**: `any(field._source.needs_review for field in profile) → true`.
4. **Profile schema lint test** — `tests/test_profile_quality_acceptance.py` mirrors Phase 4 Wave C: every JSON in `src/rules/profiles/` validates through `profile_validator`; every methodical-extracted profile carries `_source` per leaf field; computed `needs_manual_review` is consistent with per-field flags.
5. **SC-1 verification** — audit-regression / audit-docx report header / summary JSON carries `profile_id`. Single verify task; one-line addition if missing.
6. **CI gate extension** — bring Phase 5 test files (`test_profile_quality_acceptance.py`, `test_methodical_extractor.py`) into `.github/workflows/regression-gate.yml`. Fixture committed at `tests/fixtures/methodical/normocontrol_berger.pdf` (1.4MB Бергер version — CI uses, local devs use current 9.4MB).

Out of scope for Phase 5:

- **PPTX input** — DROPPED per user direction 2026-05-14. PRD US-028 phrasing updated atomically with first plan commit (D-004 no-silent-rewrites). PDF + DOCX (already supported) + TXT/MD (already supported) cover the user's reality.
- **OCR / image-only PDF** — methодичка must have an extractable text layer (existing `extract_text_from_file` already raises if PDF text is empty). Scan-only PDFs deferred to v2.
- **Rule engine changes** — Phase 5 only produces profile JSONs; it does NOT touch `apply_rules_to_paragraph`, rule loading, or scalar/list dispatchers.
- **UI integration** — profile selection in Streamlit UI belongs to Phase 6.
- **Multi-profile per audit** — single `--profile-id` per run, no profile chaining at run-time (the extractor already supports `--base-profile-ids` list for ingestion; that's separate).
- **GHA full-corpus nightly + matrix** — Phase 4 out-of-scope items carry forward.
- **58.docx / 59.docx practice reports** — Phase 3 D-08 carries forward.

</domain>

<decisions>
## Locked Decisions

**D-01** — Phase 5 input scope: PDF + DOCX (+ existing TXT/MD). PPTX DROPPED. Methодичка at `normocontrol/Нормоконтроль 2026.pdf` is the local reference; `Нормоконтроль Бергер.pdf` (1.4MB Феврал) is the CI fixture. PRD US-028 SC-3 amendment lands atomically with plan 5-01 commit per D-004.

**D-02** — Diff format: unified text diff over flattened JSON paths. One line per change: `<dotted.path>: <old> → <new>`. Grouped under top-level section headers (`## document_rules`, `## labels`, `## bibliography_rules`, etc.). Both stdout and sidecar `.diff.txt` next to candidate JSON. NOT JSONpatch RFC 6902. Rationale: user value = "readable error list"; consistent ethos.

**D-03** — Dispatcher pattern: dry-run by default (write candidate to temp/preview path, print diff, exit 0 without touching `PROFILES_DIR`). `--apply` writes to `PROFILES_DIR/<profile_id>.json`. If target file already exists: refuse unless `--force --reason "<text>"` with `len(reason.strip()) >= 8`. Mirrors Phase 4 D-13 audit-trail pattern.

**D-04** — Overwrite policy: refuse silent overwrite of any existing profile JSON. `--force --reason` required. Russian-language error citing D-004. Reason recorded in profile's `extraction_meta.override_reason` field for audit trail.

**D-05** — Per-field source attribution schema:
```json
{
  "_source": {
    "file": "Нормоконтроль 2026.pdf",
    "loc": "page_7",
    "confidence": 0.85,
    "needs_review": false
  }
}
```
- `loc` = `"page_N"` for PDF, `"paragraph_N"` for DOCX, `"line_N"` for TXT/MD.
- `confidence` ∈ [0.0, 1.0]; threshold for `needs_review: true` is `confidence < 0.7` (single sentinel — adjustable in code, not config).
- Annotation attached at the LEAF level (e.g. `document_rules.page.margin_left_cm._source`), not on parent dicts.
- Whole-profile `extraction_meta.needs_manual_review` becomes derived: `any(field._source.needs_review for leaf in profile) → true`. The hand-set heuristic boolean (current `extraction_confidence < 0.9`) is removed.

**D-06** — Test fixture: `tests/fixtures/methodical/normocontrol_berger.pdf` (1.4MB Феврал 2026 Бергер version). CI gate uses it. Current `Нормоконтроль 2026.pdf` (9.4MB) stays in `normocontrol/` outside the repo (already gitignored OR added to `.gitignore` in plan 5-01); local devs verify against it via `make` target. No synthetic fixture; real PDF provides realistic edge cases.

**D-07** — SC-1 verification: read `cmd_audit_regression` + `cmd_audit_docx` report writers; confirm `profile_id` is present in either CSV header column or summary JSON. If missing, add a single-line write. Treat as verify task, not implementation task.

**D-08** — Profile schema lint test (`tests/test_profile_quality_acceptance.py`):
- Every `src/rules/profiles/*.json` validates through `profile_validator.validate()`.
- Every profile carries top-level `profile_id`, `profile_name`, `profile_type`, `is_default`.
- Every methodical-extracted profile (`profile_type == "methodical_guidelines"`) carries `_source` annotation on every leaf field in `document_rules.*`, `labels.*.style_profile`, `bibliography_rules.*`.
- Computed `extraction_meta.needs_manual_review` matches `any(leaf._source.needs_review)`.
- Mirrors Phase 4 Wave C structure (RED via bogus required field, GREEN via removing it).

**D-09** — TDD discipline mandatory per CLAUDE.md «Железный закон». Each plan with code changes has explicit RED commit (`test(05-NN): RED — ...`) before GREEN (`feat(05-NN): GREEN — ...`). Observable failures captured in SUMMARY.md.

**D-10** — CI gate extension reuses Phase 4 Option D pattern: workflow step copies `tests/fixtures/methodical/*.pdf` into a known path before pytest. New test files added to `regression-gate.yml`'s 4-file pytest invocation → 6-file invocation (existing 4 + `test_profile_quality_acceptance.py` + `test_methodical_extractor.py`). Makefile `regression-gate` target updated symmetrically. Workflow `timeout-minutes: 10` likely sufficient (PDF parse ~1s); bump to 15 only if Бергер extraction exceeds 60s.

**D-11** — Russian-language UX preserved per existing code (`print(f"Профиль сохранен в: {output_path}")`, error messages, README sections). Extends to new CLI flags' help text and error messages.

**D-12** — Backwards compatibility: existing `extract-methodical-profile` CLI without `--apply` becomes dry-run by default. Existing callers that depended on immediate write must add `--apply`. No silent breakage — argparse help text + first-run banner cite D-004. Plan 5-03 RED commit captures the breaking-change test.

</decisions>

<plans_shape>
## Proposed Plan Breakdown (orchestrator to confirm in /gsd-plan-phase 5)

| Plan | Wave | Type | What | Files Modified (estimate) |
|------|------|------|------|---------------------------|
| 5-01 | A | TDD | Per-field `_source` annotation + derived `needs_manual_review` in `methodical_extractor.py`. RED: failing schema test. GREEN: rewrite extractor to emit annotated profile. Also: update PRD US-028 + REQUIREMENTS REQ-methodical-profile-extract to drop PPTX. | `src/rules/methodical_extractor.py`, `tests/test_methodical_extractor.py` (NEW), `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, PRD (if tracked) |
| 5-02 | B | TDD | Profile diff generator (`src/rules/profile_diff.py`) — unified text diff over flattened JSON paths. Sidecar `.diff.txt` writer. | `src/rules/profile_diff.py` (NEW), `tests/test_profile_diff.py` (NEW) |
| 5-03 | C | TDD | CLI dispatcher rewrite: dry-run default + `--apply` + `--force --reason "<text ≥8>"`. Mirrors Phase 4 D-13 pattern (argparse `required=False`, dispatcher-level guard, Russian error msg). | `src/main.py`, `tests/test_cli_parser.py` (extend) |
| 5-04 | D | execute | Profile schema lint (`tests/test_profile_quality_acceptance.py`) + SC-1 report-header verify (add `profile_id` to CSV/JSON if missing). | `tests/test_profile_quality_acceptance.py` (NEW), `src/main.py` or `src/evaluation/format_regression_audit.py` (small addition if SC-1 gap exists) |
| 5-05 | E | execute (checkpoint) | CI gate extension: copy Бергер fixture into `tests/fixtures/methodical/`, extend `.github/workflows/regression-gate.yml` + Makefile to include new 2 test files. End-to-end PR validation mirrors Phase 4 plan 04-05 Task 2 (clean PR + designed-failure PR). | `tests/fixtures/methodical/normocontrol_berger.pdf` (NEW, 1.4MB), `.github/workflows/regression-gate.yml`, `Makefile`, `CONTRIBUTING.md` |

Dependencies: 5-02 depends on 5-01 (needs annotated profile shape). 5-03 depends on 5-02 (uses diff for dry-run output). 5-04 depends on 5-01 (schema lint covers annotation). 5-05 depends on 5-01..5-04 (CI runs all).

Strict sequential execution likely (per Phase 4 lesson — letter-waves do not parallelize cleanly when `depends_on` chain exists).

</plans_shape>

<specifics>
## User-Provided References

- `/Users/fedorova.van/experiments/gost_formatter/normocontrol/Нормоконтроль 2026.pdf` — 9.4MB, current нормоконтроль методичка. Local verification target. Likely stays gitignored.
- `/Users/fedorova.van/experiments/gost_formatter/normocontrol/Нормоконтроль Бергер.pdf` — 1.4MB, Феврал 2026 Бергер version. Committed as CI fixture at `tests/fixtures/methodical/normocontrol_berger.pdf` in plan 5-05.

## Patterns to Reuse from Phase 4

- `--apply --force --reason "<text ≥8>"` CLI guard pattern (Phase 4 D-13, plan 04-04).
- Dry-run-by-default + sidecar diff file (new for Phase 5, but conceptually similar to Phase 4 candidate-write-and-verify).
- TDD RED commit forced by bogus-required-field / narrow-allowed-set placeholder (Phase 4 Wave C deviation, learned: probe-derived empirical sets may be wrong — extractor builds real annotation, GREEN removes placeholder).
- CI fixture stage step (Phase 4 Option D, plan 04-05): workflow `cp` from `tests/fixtures/` into hardcoded test path before pytest.
- Russian-language error messages (Phase 4 04-04, citing D-004).

</specifics>

<open_questions>
None — all decisions locked. Planner can proceed.

</open_questions>

<success_criteria>
Phase 5 success criteria from ROADMAP (unchanged):
1. User can pick a rule profile per audit; the chosen profile id is recorded in the report header.
2. Profiles live outside code (e.g. `rules/gost_7_32_2017.json`, `rules/gost_r_7_0_100_2018_bibliography.json`, `rules/local_university_profile.json`).
3. `extract-methodical-profile` CLI ingests a **PDF/DOCX** (PPTX dropped per D-01) presentation, produces a draft profile, shows a diff against the chosen base profile, and requires explicit `--apply` confirmation before save.
4. Ambiguous extracted requirements land as `needs_manual_review` with source/page attribution (`page_N` for PDF, `paragraph_N` for DOCX); presentation never silently replaces GOST.

Phase 5 closes when:
- All 5 plans complete with SUMMARY.md.
- Phase 5 VERIFICATION.md confirms all 4 SC verified against the actual Бергер fixture + real `Нормоконтроль 2026.pdf` extraction.
- CI gate runs `tests/test_profile_quality_acceptance.py` + `tests/test_methodical_extractor.py` GREEN on PR.

</success_criteria>

<next_steps>
1. `/gsd-plan-phase 5` — produce 5 detailed PLAN files matching the shape above.
2. `/gsd-execute-phase 5` — run waves sequentially per `depends_on` chain.
3. After Phase 5 verifier passes → `/gsd-discuss-phase 6` (UI redesign) where user value moves to UX.

</next_steps>
