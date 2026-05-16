---
phase: 08
milestone: v1.0
created: 2026-05-16
type: design-review-rollup
sources:
  - .planning/phases/06-streamlit-ui-redesign/06-05-SUMMARY.md
  - .planning/phases/07-pdf-text-layer-audit-slice/07-UAT.md
  - .planning/phases/09-classical-model-zoo-lr-svm-complementnb-randomforest-histgbm/09-03-SUMMARY.md
---

# 08 Design-Review Rollup — Milestone v1.0

This document consolidates prior-phase design-review records for milestone
v1.0 acceptance. It is produced by Plan 08-03 Task 1 per D-C-01.
Source artifacts are READ ONLY — this rollup does not modify them.

## Phase 6: Streamlit UI redesign (retroactive sign-off)

**Source:** `.planning/phases/06-streamlit-ui-redesign/06-05-SUMMARY.md`
**Rationale per D-E-02:** Phase 6 closed cleanly; 06-05-SUMMARY.md records
the design-review outcome as `checkpoint_outcome: approved-with-followups
(no follow-ups recorded)`. The project owner approved the staged checklist
contents at the Wave 5 checkpoint (2026-05-15). No specific MEDIUM/LOW
follow-ups were recorded. This is the authoritative design-review verdict
for Phase 6.

**06-DESIGN-REVIEW.md status field** remains `status: pending` on disk;
it was intentionally left blank by Phase 6 (live Streamlit walk-through
was not possible in the orchestrator env). Per D-E-02, this file is NOT
backfilled or amended — the SUMMARY's recorded verdict stands as the
retroactive sign-off.

**Verdict: APPROVED-WITH-FOLLOWUPS (no open follow-ups)**

Key deliverables verified at sign-off:
- app.py 698 → 669 LoC (within 500–750 target band).
- Dead CSS orphans from 06-02/06-03 removed (`.hero`, `div[data-testid="stTabs"]`,
  `.section-note`).
- All 54 Russian contract strings from 06-UI-SPEC §Copywriting Contract
  verified verbatim via AST literal walk.
- `pytest tests/test_run_log.py -q` → 7 passed, no RunLog regression.

## Phase 7: PDF text-layer audit slice (UAT)

**Source:** `.planning/phases/07-pdf-text-layer-audit-slice/07-UAT.md`
**Status:** `status: complete` (frontmatter)

**UAT result: 7/7 PASS**

| # | Test | Result |
|---|------|--------|
| 1 | Sidebar uploader controls (label + caption) | PASS |
| 2 | Berger PDF upload runs audit pipeline | PASS (after G-07-01 gap closure) |
| 3 | PDF report header: audit-only badge + no DOCX download | PASS |
| 4 | Block counters + per-block PDF reason substring | PASS |
| 5 | Scanned PDF rejection — locked Russian banner | PASS |
| 6 | Run-log JSON records PdfNoTextLayer | PASS |
| 7 | DOCX regression — Phase 6 path still works | PASS |

**Gaps closed:**

- G-07-01 (severity: major) — PDF audit blocked when no .joblib artifact
  present. Resolved by Plan 07-04: run_processing widens baseline_unavailable
  guard to skip for .pdf uploads. Resolution confirmed in re-UAT 2026-05-15.
- G-07-02 (severity: cosmetic) — Main-pane empty-state copy mismatch.
  Resolved by Plan 07-05: string updated to «Загрузите документ (DOCX или
  PDF), чтобы начать аудит».
- G-07-03 (severity: cosmetic) — Per-block PDF reason not reviewer-facing.
  Resolved by Plan 07-05: text updated to «PDF блок — текстовый слой,
  требует ручной проверки».

Re-UAT verdict (2026-05-15): `re_uat_verdict: all_gaps_resolved`
Zero open severity: blocker or severity: high items.

**Verdict: COMPLETE — 7/7 PASS, 3/3 gaps resolved**

## Phase 9: Classical model zoo (inline UAT)

**Source:** `.planning/phases/09-classical-model-zoo-lr-svm-complementnb-randomforest-histgbm/09-03-SUMMARY.md`
**Inline UAT:** approved 2026-05-16 by project owner (no formal 09-UAT.md;
Phase 9 used the Plan 09-03 Task 3 checkpoint as the UAT gate per
key-decisions in 09-03-SUMMARY.md).

**UAT result: 8/8 PASS**

| # | Verification point | Result |
|---|-------------------|--------|
| 1 | venv activation + sklearn 1.6.1 available | PASS |
| 2 | Full zoo run writes 4 artifact files | PASS |
| 3 | results.csv: 8 columns (D-C-02 order), 6 rows, all model names | PASS |
| 4 | linear_svm_production weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.86 | PASS |
| 5 | linear_svm informational row (apples-to-apples zoo baseline) | PASS |
| 6 | summary.txt: per-model preprocessing + metrics + SC-2 verdict | PASS |
| 7 | per_class_f1.md: H2 per model + 5-column table + body_text class | PASS |
| 8 | make compare-classical-acceptance exits 0 end-to-end | PASS |

Phase 9 SC closure: SC-1 through SC-5 all verified live on full
annotations_test.csv corpus.
Zero open severity: blocker or severity: high items.

**Verdict: APPROVED — 8/8 PASS**

## Deferred to v1.1

Per D-C-03, the following backlog items are NOT critical-bug regressions.
They are cosmetic / feature-add items captured during Phase 7 UAT and
deferred to v1.1. SC-4 treats them as informational only.

**Phase 999.1 — ui-tabbed-layout-restoration**
Restore multi-tab navigation layout from the pre-Phase-6 Streamlit
interface. Current single-page layout collapses block-by-block review
into one scroll surface. Decide whether to re-introduce per-status tabs
or hybridise with the current audit-flow design.

**Phase 999.2 — docx-formatting-bugs-list-indent-formula-vars**
Four related DOCX formatter indent defects:
1. Bulleted-list items wrap to second line lose hanging-indent alignment.
2. Formula variable legends («где») need fixed tab stop and column alignment.
3. Bibliography wrapped-line indent does not align under first non-numeric character.
4. Section subheading «1 Теоретическая часть» inside bibliography uses
   inconsistent indent.

Neither 999.1 nor 999.2 constitutes a severity: blocker or severity: high
defect for milestone v1.0. They are v1.1 entry points.

---

*Rollup produced 2026-05-16 by Plan 08-03 Task 1.*
*Source artifacts unmodified per D-E-02 (06-DESIGN-REVIEW.md) and D-C-01.*
