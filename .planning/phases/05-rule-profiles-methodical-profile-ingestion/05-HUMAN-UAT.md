---
status: resolved
phase: 05-rule-profiles-methodical-profile-ingestion
source: ["05-VERIFICATION.md"]
started: 2026-05-14T17:10:00Z
updated: 2026-05-14T17:35:00Z
---

## Current Test

[all tests passed 2026-05-14T17:35:00Z]

## Tests

### 1. Dry-run readability over Бергер PDF

expected: Running `python3 -m src.main extract-methodical-profile --input-path tests/fixtures/methodical/normocontrol_berger.pdf` (no `--apply`) prints a human-readable diff: `## document_rules` and `## labels` section headers appear, lines use U+2192 arrow (`<path>: <old> → <new>`), `_source` paths never appear in the diff body. Preview JSON + `.diff.txt` written to `/tmp/`, `src/rules/profiles/` unchanged.

result: passed

evidence: Section headers observed (`## document_rules`, `## labels`, `## bibliography_rules`, `## numbering_rules`, `## nn_context`, `## extraction_meta`, `## global_audit_policy`, `## profile_id`, `## profile_name`, `## profile_type`, `## source_name`, `## source_type`, `## base_profiles`, `## description`, `## is_default`). U+2192 (→) arrow used consistently. No `_source` paths in diff body. Preview written to `/var/folders/v1/.../T/methodical_normocontrol_berger.preview.json` + `.preview.diff.txt` (`$TMPDIR` on macOS, equivalent to `/tmp/` on Linux per `tempfile.gettempdir()`). `src/rules/profiles/` untouched on dry-run.

### 2. End-to-end `--apply` / `--force` / `--reason` audit trail

expected: Three consecutive runs against the Бергер fixture:
1. `extract-methodical-profile --input-path tests/fixtures/methodical/normocontrol_berger.pdf --apply` → writes new profile to `PROFILES_DIR/<id>.json`.
2. Same command again → refuses with a Russian error citing D-004 (target already exists).
3. `extract-methodical-profile --input-path tests/fixtures/methodical/normocontrol_berger.pdf --apply --force --reason 'test resync 2026'` → overwrites; saved JSON carries `extraction_meta.override_reason: 'test resync 2026'`.

result: passed

evidence:
- Run 1: "Профиль сохранен в: /Users/.../src/rules/profiles/methodical_normocontrol_berger.json"
- Run 2: stderr "Профиль /Users/.../methodical_normocontrol_berger.json уже существует. Используй --apply --force --reason '<text>' (минимум 8 символов; D-004: no silent rewrites)." — Russian, cites D-004, hints --force --reason ≥8 chars
- Run 3: "Профиль сохранен в: /Users/.../methodical_normocontrol_berger.json"; saved JSON `extraction_meta.override_reason == 'test resync 2026'` (verified via `json.load`)
- Test artifact `src/rules/profiles/methodical_normocontrol_berger.json` removed after UAT (not a production profile)

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

(none)
