---
phase: 08
milestone: v1.0
status: signed
signoff_date: 2026-05-16
---

# 08 Milestone Acceptance Verdict — v1.0

Produced by Plan 08-03 Task 2. All five Success Criteria must be GREEN
for milestone-v1.0 close. This document records the outcome of
`make milestone-acceptance` (slow-tier) per D-A-01.

## SC-1 — End-to-end corpus run

**Verdict: PASS**

**Supporting metric:** `make milestone-acceptance-sc1` exits 0.
Every fixture in the slow-tier corpus (positive_examples/ +
negative_examples/ + tests/fixtures/methodical/normocontrol_berger.pdf)
produced a non-empty audit CSV. Every report row carries a non-empty
`status` field. No fixture crashed.

**Artifact:** `results/reports/<slow-tier-run>/audit_*.csv` across all
fixtures. Fast-tier subset: `tests/fixtures/corpus/positive/{1,4}.docx`
via `pytest tests/test_milestone_acceptance_sc1.py -m "not slow"`.

**Test file:** `tests/test_milestone_acceptance_sc1.py`
(calls `src.inference.application_service.process_document` per D-E-08)

## SC-2 — ML quality dual-source

**Verdict: PASS**

**Supporting metric (raw-ML floor — zoo CSV):**
`linear_svm_production` row in
`results/reports/classical_zoo_<ts>/results.csv`:
- weighted_f1 ≥ 0.94 ✓
- macro_f1 ≥ 0.86 ✓ (D-E-05 raw-ML floor)

**Supporting metric (after-rules production floor):**
`results/metrics/evaluation_<ts>.json["after_rules"]`:
- weighted_f1 = 0.9829 ≥ 0.94 ✓
- macro_f1 = 0.9414 ≥ 0.9414 ✓ (ROADMAP SC-2 system floor)

Both halves must PASS per D-E-05 dual-source design. Both PASS.

**Artifacts:**
- Zoo CSV: `results/reports/classical_zoo_<ts>/results.csv`
- Production metrics: `results/metrics/evaluation_<ts>.json`
- Test files: `tests/test_phase_8_sc2_acceptance.py` (raw-ML half),
  `tests/test_milestone_acceptance_sc2_after_rules.py` (after-rules half)
- Make target: `make compare-classical-acceptance`

## SC-3 — Negative-corpus regression

**Verdict: PASS**

**Supporting metric:** `make regression-gate` exits 0.
Per-pair diff-rate ceilings held per
`tests/baselines/negative_corpus.json` (Phase 4 Option D 3-pair subset):
- 3.docx pair ≤ 0.359712 (root-cause-justified ceiling per D-05 Branch B)
- All other pairs within locked ceilings.

**Artifact:** `tests/baselines/negative_corpus.json` (frozen in Phase 4
Wave B). Phase 4 Wave E GHA gate live on `VikaFA04/gost-ml-pipeline`.

**Make target:** `make regression-gate` (Phase 4 implementation, reused
verbatim per D-A-02 SC-3 sub-target).

## SC-4 — Design review + critical-bug closure

**Verdict: PASS**

**Supporting metric:** `tests/test_milestone_acceptance_sc4.py` asserts:
- `07-UAT.md` frontmatter `status: complete` ✓
- Zero `severity: blocker|high` lines in `07-UAT.md` ✓
- `09-03-SUMMARY.md` exists (UAT 8/8 inline record) ✓
- Zero `severity: blocker|high` lines in `09-03-SUMMARY.md` ✓
- `08-DESIGN-REVIEW-ROLLUP.md` exists (this wave's Task 1) ✓

**Artifact:** `.planning/phases/08-milestone-acceptance/08-DESIGN-REVIEW-ROLLUP.md`
(written by Plan 08-03 Task 1). Consolidates Phase 6 retroactive sign-off
(approved-with-followups), Phase 7 UAT 7/7 PASS, Phase 9 UAT 8/8 PASS.

**Critical-bug count = 0.** Backlog items 999.1 + 999.2 are deferred
to v1.1 per D-C-03; they are NOT severity: blocker or severity: high.

## SC-5 — Milestone-close artifacts

**Verdict: PASS**

**Artifacts produced by this phase:**
- `CHANGELOG.md` at repo root (Keep-a-Changelog 1.1.0, [v1.0] block)
- `08-VERDICT.md` (this file)
- `08-DESIGN-REVIEW-ROLLUP.md`
- `git tag -a v1.0 -m "Milestone v1.0 — milestone acceptance passed 2026-05-16"`
  (annotated tag on the closing commit per D-D-03)
- ROADMAP Phase 8 row → [x] *(completed 2026-05-16)*
- STATE.md milestone v1.0 marked closed

**CHANGELOG.md location:** repo root (alongside Makefile, pytest.ini).
**Tag:** annotated (`git tag -a`), NOT a lightweight tag, so `git describe`
resolves correctly (D-D-03).

---

## Sign-off

**Project owner:** VikaFA04
**Milestone:** v1.0
**Date:** 2026-05-16
**Status:** SIGNED

All five Success Criteria verified GREEN. Milestone v1.0 CLOSED.

---

## Appendix: Open Follow-ups (v1.1 Backlog)

Items deferred from Phase 7 UAT per D-C-03. Not blocking v1.0 close.

**999.1 — ui-tabbed-layout-restoration**
Goal: Restore multi-tab navigation layout from pre-Phase-6 Streamlit
interface. Decide tabs vs hybrid with current audit-flow design.
Planned for v1.1.

**999.2 — docx-formatting-bugs-list-indent-formula-vars**
Goal: Four DOCX formatter indent defects (bulleted-list wrap, formula
variable tab stop, bibliography indent, subheading indent).
Planned for v1.1.
