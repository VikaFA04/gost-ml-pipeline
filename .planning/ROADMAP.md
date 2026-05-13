# Roadmap: gost-formatter

## Overview

This milestone has a single, measurable goal: **UI usability passes design review
AND critical-bug count = 0**. We sequence work so the engine becomes trustworthy
before the UI is rebuilt on top of it — fixing destructive autofix and rule-engine
cohesion first, then bibliography + heading semantics, then the regression gate
that keeps the corpus honest, then profile selection, then the UI redesign on a
stable backend. The PDF text-layer audit slice (locked by D-PDF-SCOPE) lands
after the UI is sound and before the final acceptance gate. The historical
operational state and the original Этапы 1–9 are preserved in
`.planning/intel/context.md` and are referenced by phase, not duplicated here.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work.
- Decimal phases (2.1, 2.2): Urgent insertions if needed (marked INSERTED).

- [x] **Phase 1: Engine guardrails & cohesion audit** *(completed 2026-05-12)* - Stop destructive autofix from styled paragraphs and verify the rule-engine dependency graph.
- [ ] **Phase 2: Bibliography & list semantics** - Recognise bibliography lists; single shared `numId`; conservative list autofix.
- [ ] **Phase 3: Heading signature & DOCX generator** - Extend heading signature and harden the DOCX writer for template-specific styles.
- [ ] **Phase 4: Regression gate** - Bring the negative corpus under a tracked baseline via the `audit-regression` CLI.
- [ ] **Phase 5: Rule profiles & methodical-profile ingestion** - Multiple selectable profiles + PPTX/PDF profile ingestion with diff.
- [ ] **Phase 6: Streamlit UI redesign** - Rebuild the UI around the audit flow and pass design review.
- [ ] **Phase 7: PDF text-layer audit slice** - Read-only PDF audit (no OCR, no autofix), reusing the audit CSV schema.
- [ ] **Phase 8: Milestone acceptance** - End-to-end MVP acceptance + success-metric verification.

## Phase Details

### Phase 1: Engine guardrails & cohesion audit
**Goal**: The rule engine stops applying `body_text` rules to heading/toc/caption/list-styled paragraphs, the previously-flagged INFERRED edges around the rule engine are verified, and the cohesion problem from the graphify audit is documented.
**Depends on**: Nothing (first phase of new milestone)
**Requirements**: REQ-fix-style-guards, REQ-fix-styled-paragraphs-no-direct-props, REQ-rule-engine-cohesion-audit
**Success Criteria** (what must be TRUE):
  1. Running `format-docx --apply-safe` on the GOST-decorated positive subset (`positive_examples/{1,4}.docx` plus any other GOST-decorated positives discoverable in the corpus) keeps `changed=0` modulo the Phase 2 bibliography-only exemption and produces no extra direct properties on Heading/TOC/List Paragraph/Caption-styled paragraphs. Practice reports `58.docx`/`59.docx` are excluded from the gate per Phase 3 D-08 (out of scope for the GOST profile).
  2. A documented audit of the Rule Engine community lists every INFERRED edge on `apply_rules_to_paragraph()` and `load_rules()` as either confirmed (kept) or removed; cohesion score after refactor is strictly higher than 0.06.
  3. Existing pytest baseline (21+ tests) still passes; new guard tests cover Heading/TOC/Caption-styled paragraph cases.
  4. No negative-corpus pair regresses relative to the FORMAT_FIX_PLAN Этап 8 baseline diff-rate (mean ≤ 0.4781).
**Plans:** 4 plans
Plans:
- [x] 01-01-test-scaffolding-red-PLAN.md — Wave 0 RED: stub style_signatures.py, write 13+ failing tests, build minimal DOCX fixture, extend positive-corpus regression list
- [x] 01-02-style-signatures-green-PLAN.md — Wave 1 GREEN: implement classify_style with 4 regexes; turn the 6 classify_style unit tests green
- [x] 01-03-rule-engine-guard-green-PLAN.md — Wave 2 GREEN: insert early-return style guard in apply_rules_to_paragraph; turn the 7 guard tests + integration + positive corpus + negative-corpus diff-rate ≤ 0.4781 gates green
- [x] 01-04-cohesion-audit-PLAN.md — Wave 3: enumerate 67 INFERRED edges in 01-COHESION-AUDIT.md, apply D-10 low-risk refactors, run /graphify --update and record cohesion before=0.06 after=<X> with X > 0.06

### Phase 2: Bibliography & list semantics
**Goal**: Bibliography lists are detected and unified under a single Word numbering; ambiguous lists are routed to `review` rather than auto-coerced; conservative list handling matches the positive corpus shape.
**Depends on**: Phase 1
**Requirements**: REQ-list-conservative-handling
**Success Criteria** (what must be TRUE):
  1. `СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ` (and `ИСПОЛЬЗУЕМЫХ` variant) is classified as `bibliography_title` even when the SVM returns `body_text`, by a deterministic postprocess override.
  2. After `audit-docx --apply-safe` on a real negative DOCX containing a bibliography, all bibliography entries share one `numId`, and `applied_fixes` includes `numbering`.
  3. Long text paragraphs without `numId` are not coerced into lists; marker-only lists without `numId` become `review`.
  4. Targeted pytest fixtures cover bibliography detection + single-`numId` enforcement + ambiguous-list `review` routing.
**Plans:** 4 plans
Plans:
- [x] 02-01-test-scaffolding-red-PLAN.md — Wave 0 RED: hand-crafted DOCX fixture + 19 failing tests across postprocess/profile_loader/bibliography_phase2/negative-corpus diff-rate.
- [x] 02-02-postprocess-and-profile-green-PLAN.md — Wave 1 GREEN: D-01 unconditional title override + D-04 heading-style subsection detection + D-03/D-11 profile schema (helpers + validator + gost_7_32_2017.json fields).
- [x] 02-03-multilevel-numbering-green-PLAN.md — Wave 2 GREEN: D-05 2-level multilevel abstract + per-subsection w:num with lvlOverride + D-06 first-valid-numId coercion + D-07 idempotent seed + stable cache key (id(paragraph.part.document.part)).
- [x] 02-04-ambiguous-routing-and-gate-green-PLAN.md — Wave 3 GREEN: D-09 ambiguous-list review routing + D-10 sanity + D-13 formatting_rules_v1.json strip + D-11 MAX_FALLBACK_LIST_* constant deletion + D-15 negative-corpus regression gate verification.
**UI hint**: yes

### Phase 3: Heading signature & DOCX generator
**Goal**: Heading rules check both font and paragraph-format Word parameters with explicit direct-vs-inherited separation. Inherited mismatches go to `review`; direct overrides on Heading-styled paragraphs are autofixed. Per-field heading rules.
**Depends on**: Phase 1
**Requirements**: REQ-heading-style-signature
**Success Criteria** (what must be TRUE):
  1. Extractor's heading signature includes font name/size/bold/italic/underline/color/CAPS plus alignment / first-line indent / left+right indent / space_before+after / line_spacing / keep_with_next / keep_lines_together / page_break_before / widow control.
  2. For paragraphs whose Heading style is inherited from `Heading 1/2/3`, autofix is blocked — mismatch routes to `review`. Direct overrides on Heading-styled paragraphs are autofixed.
  3. GOST-decorated positive subset stays `changed=0` for any heading rule (regression gate from Phase 2 extended with heading-direct-fix invariant); negative heading fixtures move toward target signatures with no text changes; TOC and list structure remain stable.
**Plans:** 4 plans
Plans:
- [ ] 03-01-PLAN.md — Wave 0 RED (TDD): 4+8 failing tests, heading_minimal.docx fixture+builder, D-07 invariant in positive-corpus regression
- [ ] 03-02-PLAN.md — Wave 1 GREEN: D-01..D-04 — _resolve_inherited_value + _extract_heading_format_signature + extract_paragraph_block wiring (lazy heading-only, JSON-serialized 18-key signature)
- [ ] 03-03-PLAN.md — Wave 2 GREEN: D-05/D-06/D-09 — remove blanket heading guard, add per-field source dispatcher (HEADING_SIG_FIELDS), apply_heading_scalar_fix, +17 heading_* rules in formatting_rules_v1.json (level-split + null-target load+skip per Open Question 2)
- [ ] 03-04-PLAN.md — Wave 3 verification: positive-corpus signature-presence assertion + full Phase 3 success-criteria empirical verification (negative-corpus diff-rate ≤ 0.4781 preserved)

> **Scope reduction (2026-05-13, Phase 3 discuss-phase D-08):** REQ-fix-docx-generator-custom-styles dropped from this milestone. 58.docx and 59.docx are practice reports (отчёт по практике), not GOST coursework — applying GOST rules to them produces spurious edits because the profile doesn't cover that doc type. Practice-doc support, if needed, lands via Phase 5 multi-profile + methodical-profile ingest. See `.planning/phases/03-heading-signature-and-docx-generator/03-CONTEXT.md` D-08.

### Phase 4: Regression gate
**Goal**: The negative-corpus diff-rate becomes a tracked, blocking metric. The `audit-regression` CLI is the gate for every subsequent change; the rules-quality acceptance rollup is enforced.
**Depends on**: Phase 2, Phase 3
**Requirements**: REQ-fix-negative-corpus-no-regression, REQ-audit-regression-cli, REQ-rules-quality-acceptance
**Success Criteria** (what must be TRUE):
  1. `audit-regression` CLI compares a corpus run against a saved baseline and emits per-pair CSV plus a summary JSON (already partly implemented per recent commits — bring under the gate).
  2. No negative-corpus pair regresses; `3.docx` pair returns to ≤ 0.318; mean negative diff-rate ≤ 0.4781.
  3. Audit report covers every rule in `RuleRecord` format; every violation surfaces; every applied fix surfaces; unsafe fixes blocked; low-confidence blocks become `manual_review_required` with reason.
  4. `audit-regression` is wired into CI / a documented local check so every fix-track PR is gated against the baseline.
**Plans**: TBD

### Phase 5: Rule profiles & methodical-profile ingestion
**Goal**: Multiple rule profiles (GOST + university-local) are selectable per audit run; a normcontrol presentation can be ingested as a methodological source and a profile diff is shown to the user before save.
**Depends on**: Phase 4
**Requirements**: REQ-rule-profiles, REQ-methodical-profile-extract
**Success Criteria** (what must be TRUE):
  1. User can pick a rule profile per audit; the chosen profile id is recorded in the report header.
  2. Profiles live outside code (e.g. `rules/gost_7_32_2017.json`, `rules/gost_r_7_0_100_2018_bibliography.json`, `rules/local_university_profile.json`).
  3. `extract-methodical-profile` CLI ingests a PPTX/PDF presentation, produces a draft profile, shows a diff against the chosen base profile, and requires explicit user confirmation before save.
  4. Ambiguous extracted requirements land as `needs_manual_review` with source/slide attribution; presentation never silently replaces GOST.
**Plans**: TBD

### Phase 6: Streamlit UI redesign
**Goal**: The Streamlit UI is rebuilt around the audit flow with consistent visual language across block statuses, profile selection is first-class, and the redesign passes a design-review pass by the project owner.
**Depends on**: Phase 5
**Requirements**: REQ-ui-main-flow, REQ-ui-problem-block-view, REQ-input-preflight, REQ-pipeline-logging, REQ-ui-design-review
**Success Criteria** (what must be TRUE):
  1. User can complete a full audit run from upload to download in one linear flow: upload `.docx` → pick profile → run audit → see summary counters (total / no_change / changed / review / error) → inspect per-block table → download audit CSV and (if safe fixes exist) corrected DOCX.
  2. `review` and `error` blocks are visually distinct from `no_change` and `changed`; per-block confidence is shown; manual-review reason is taken from `explanation`; original block text is always inspectable.
  3. Preflight failures (unreadable file, malformed paragraphs) surface as user-facing messages rather than tracebacks; logs do not leak full document text.
  4. The redesigned UI passes a design-review pass by the project owner; recorded defects fixed before close.
**Plans**: TBD
**UI hint**: yes

### Phase 7: PDF text-layer audit slice
**Goal**: PDF documents with an extractable text layer can be audited read-only: text-block extraction, basic layout features, ML classification, and an audit CSV — no OCR, no PDF writing.
**Depends on**: Phase 6
**Requirements**: REQ-pdf-text-only
**Success Criteria** (what must be TRUE):
  1. PDF upload is accepted only when a text layer is extractable; scanned/page-image PDFs are rejected with a user-facing message.
  2. Audit report for a PDF input uses the same CSV schema as DOCX; `applied_fixes` is always empty and no PDF is written.
  3. UI uploader supports `.pdf` alongside `.docx` and clearly labels PDF as audit-only.
  4. README + UI copy state the text-layer + read-only + no-OCR limits; no autofix code path runs on PDF input.
**Plans**: TBD
**UI hint**: yes

### Phase 8: Milestone acceptance
**Goal**: The two-part success metric is verified end-to-end: critical-bug count = 0, UI design review passed.
**Depends on**: Phase 7
**Requirements**: REQ-mvp-acceptance
**Success Criteria** (what must be TRUE):
  1. End-to-end acceptance run on a representative DOCX corpus: extraction → features → SVM prediction → rule audit → CSV report → safe corrected DOCX where applicable → Streamlit UI mirrors all CLI outputs.
  2. ML quality gate held: `weighted_f1 ≥ 0.94`, `macro_f1` not below 0.9414; 100% of blocks have explainable status; 100% of detected unsafe fixes blocked.
  3. Negative-corpus regression gate passes (Phase 4 baseline held or improved).
  4. UI design review sign-off recorded; critical-bug list (from FORMAT_FIX_PLAN open items + HEADING_AND_NORMCONTROL Block A/B + graphify follow-up) is empty.
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8.
Phases 2 and 3 are both gated by Phase 1 and may be planned in either order
once Phase 1 is complete; Phase 4 requires both.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Engine guardrails & cohesion audit | 4/4 | Complete | 2026-05-12 |
| 2. Bibliography & list semantics | 0/4 | Not started | - |
| 3. Heading signature & DOCX generator | 0/TBD | Not started | - |
| 4. Regression gate | 0/TBD | Not started | - |
| 5. Rule profiles & methodical-profile ingestion | 0/TBD | Not started | - |
| 6. Streamlit UI redesign | 0/TBD | Not started | - |
| 7. PDF text-layer audit slice | 0/TBD | Not started | - |
| 8. Milestone acceptance | 0/TBD | Not started | - |

## Historical Context

The previous ROADMAP.md tracked Этапы 1–6 of the original MVP build and is
preserved in `.planning/intel/context.md` under topics:

- "Current operational state (from historical ROADMAP)" — what is already DONE
  (SVM baseline, audit/fix end-to-end, UI default to baseline, CLI test
  coverage).
- "Critical pipeline defects — DOCX formatter (FORMAT_FIX_PLAN baseline)" —
  Этапы 1–9, of which 1–7 are DONE and the remainder feed Phase 1, Phase 3 and
  Phase 4 of this roadmap.
- "Headings, bibliography lists, normcontrol presentation (forward plan)" —
  HEADING_AND_NORMCONTROL Blocks A / B / C, which feed Phase 2, Phase 3 and
  Phase 5 of this roadmap.

Do not duplicate that content here.
