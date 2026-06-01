---
phase: 2
slug: bibliography-list-semantics
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-12
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini / pyproject.toml (Phase 1 baseline) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

> Filled by planner during plan generation. Each task in each PLAN.md must map to a row here with its automated command.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 0 | REQ-list-conservative-handling | — | N/A | unit | `pytest tests/ -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_bibliography_phase2.py` — RED stubs for D-01..D-15
- [ ] `tests/fixtures/_build_bibliography_minimal.py` — hand-crafted DOCX builder
- [ ] `tests/fixtures/bibliography_minimal.docx` — built fixture (1 bibliography_title + 2 subsections + 3 entries each + mixed numIds in one subsection)
- [ ] Discover ≥1 `negative_examples/*.docx` carrying `BIBLIOGRAPHY_TITLE_RE` match (researcher confirmed 17 candidates) — pin one as D-14 integration target
- [ ] Pin `3_formatted_*.docx` as D-06 mixed-numIds integration target

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Word renders bibliography entries as `<section>.<entry>` (e.g. `1.1`, `1.2`, `2.1`) | REQ-list-conservative-handling | Word's visual rendering of 2-level numbering abstract is not observable from Python — must open the DOCX in Word/LibreOffice | After integration test produces corrected DOCX, open in Word/LibreOffice and confirm bibliography entries display `<section_number>.<entry_number>` prefix. Record screenshot in phase verification artifact. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
