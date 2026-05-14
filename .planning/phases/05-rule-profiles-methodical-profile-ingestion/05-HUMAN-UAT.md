---
status: partial
phase: 05-rule-profiles-methodical-profile-ingestion
source: ["05-VERIFICATION.md"]
started: 2026-05-14T17:10:00Z
updated: 2026-05-14T17:10:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Dry-run readability over Бергер PDF

expected: Running `python3 -m src.main extract-methodical-profile --input-path tests/fixtures/methodical/normocontrol_berger.pdf` (no `--apply`) prints a human-readable diff: `## document_rules` and `## labels` section headers appear, lines use U+2192 arrow (`<path>: <old> → <new>`), `_source` paths never appear in the diff body. Preview JSON + `.diff.txt` written to `/tmp/`, `src/rules/profiles/` unchanged.

result: [pending]

### 2. End-to-end `--apply` / `--force` / `--reason` audit trail

expected: Three consecutive runs against the Бергер fixture:
1. `extract-methodical-profile --input-path tests/fixtures/methodical/normocontrol_berger.pdf --apply` → writes new profile to `PROFILES_DIR/<id>.json`.
2. Same command again → refuses with a Russian error citing D-004 (target already exists).
3. `extract-methodical-profile --input-path tests/fixtures/methodical/normocontrol_berger.pdf --apply --force --reason 'test resync 2026'` → overwrites; saved JSON carries `extraction_meta.override_reason: 'test resync 2026'`.

result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
