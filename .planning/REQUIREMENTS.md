# Requirements: gost-formatter

**Defined:** 2026-05-12
**Core Value:** A trustworthy GOST normcontrol audit of a DOCX — every status
explainable, no silent rewrites, safe-only autocorrection.

REQ-IDs in this document are 1:1 with the intel set at
`.planning/intel/requirements.md`. The intel file is the source of truth for
acceptance language; this file adds the milestone framing (v1 vs v2 vs validated),
the UI-redesign and critical-bugfix tracks, and the phase traceability.

## Validated (already shipped — not in current roadmap)

These were satisfied by Этапы 1–6 of the legacy ROADMAP (see
`.planning/intel/context.md` "Current operational state"). They are listed here
for traceability and are excluded from v1 below.

- ✓ **REQ-svm-primary-training** — `results/models/svm_block_classifier_20260506_082307.joblib`
- ✓ **REQ-tfidf-text-features** — vectorizer persisted with model
- ✓ **REQ-format-feature-fusion** — categorical + numeric + TF-IDF combined
- ✓ **REQ-cli-modes** — `train` / `evaluate` / `predict` / `extract-docx` /
  `audit-docx` / `format-docx` all implemented
- ✓ **REQ-cli-output-dirs** — outputs under `results/{models,metrics,predictions,
  extracted_blocks,reports,formatted_docs}`
- ✓ **REQ-docx-upload** — uploader restricted to `.docx`
- ✓ **REQ-docx-block-extraction** — `block_id`/`doc_id` preserved
- ✓ **REQ-format-feature-extraction** — text + kind/alignment/style/bold_ratio
  + indent/spacing where available
- ✓ **REQ-model-evaluation** — accuracy + precision/recall/F1 + weighted/macro
  + confusion matrix + error CSV
- ✓ **REQ-predict-blocks** — `predicted_label`, `confidence_score`,
  `low_confidence`, `postprocessed_label`
- ✓ **REQ-low-confidence-routing** — manual_review flag in pipeline
- ✓ **REQ-audit-report** — per-document CSV with required fields
- ✓ **REQ-audit-summary** — five counters available in CLI
- ✓ **REQ-corrected-docx** — separate file, original preserved, idempotent
- ✓ **REQ-rule-schema** — JSON rule storage with required fields
- ✓ **REQ-rule-selection-by-class** — class-driven rule subset
- ✓ **REQ-check-vs-fix-modes** — `safe_fix` vs `review_required`
- ✓ **REQ-safe-autocorrection-ss001** — pre-autofix confidence + autocorrect +
  ambiguity guards
- ✓ **REQ-error-containment-ss003** — low confidence never auto-corrected
- ✓ **REQ-ml-quality-acceptance** — `weighted_f1=0.9829`, `macro_f1=0.9414`
- ✓ **REQ-nlp-stack-confirmation** — TF-IDF + format features + Linear SVM,
  rule layer mandatory

## v1 Requirements

Scope for the next milestone. Success metric: UI usability passes design review
AND critical-bug count = 0 (all critical logic bugs fixed, regression tests pass).

### UI Redesign (Streamlit)

- [ ] **REQ-ui-main-flow** — Streamlit UI supports DOCX upload, profile
      selection, run audit, progress, summary, per-block results, violations /
      recommendations, download report and corrected DOCX. (PRD US-025)
- [ ] **REQ-ui-problem-block-view** — UI highlights `review` and `error`
      blocks, shows per-block confidence, shows manual-review reason, exposes
      original block text. (PRD US-026)
- [ ] **REQ-ui-design-review** *(new)* — UI passes a design-review pass by the
      project owner; defects fixed before close.

### Rule profiles & bibliography (HEADING_AND_NORMCONTROL Block A)

- [ ] **REQ-rule-profiles** — Multiple rule profiles (GOST + university-local),
      stored outside code, selectable per audit, profile recorded in report.
      (PRD US-028)
- [ ] **REQ-list-conservative-handling** — Conservative list handling; ambiguous
      lists routed to `review`; bibliography lists share a single `numId`.
      (PRD US-019 + HEADING_AND_NORMCONTROL Block A)

### DOCX formatter — critical-bug fixes (FORMAT_FIX_PLAN open items)

These map to the unfinished tail of FORMAT_FIX_PLAN. Each must keep the
positive corpus (`1.docx`, `4.docx`, `58.docx`, `59.docx`) at `changed=0`
and must not regress any negative-corpus pair below its FORMAT_FIX_PLAN Этап 8
baseline diff-rate.

- [ ] **REQ-fix-style-guards** *(new — FORMAT_FIX_PLAN Этап 3 remainder)* —
      Full Heading-style guard, TOC guard, Caption guard before applying
      `body_text` rules.
- [ ] **REQ-fix-styled-paragraphs-no-direct-props** *(new — FORMAT_FIX_PLAN
      Этап 2 open item)* — Heading / toc / List Paragraph / Caption-styled
      paragraphs stop receiving extra direct formatting from autofix.
- [ ] **REQ-fix-negative-corpus-no-regression** *(new — FORMAT_FIX_PLAN
      Этап 8 open)* — No negative-corpus pair regresses; `3.docx` pair returns
      to ≤ 0.318; mean diff-rate ≤ 0.4781.
- [ ] **REQ-fix-docx-generator-custom-styles** *(deferred to v2 — Phase 3
      discuss-phase D-08, 2026-05-13)* — Originally scoped as
      `src/generate/docx_writer.py` handling template-specific custom styles
      for `58.docx` / `59.docx`. Dropped from this milestone: 58/59 are
      practice reports (отчёт по практике), not GOST coursework, so the
      "fix" is doc-type detection + skip GOST autofix or per-template
      profile selection — both belong in Phase 5 multi-profile + methodical
      ingest, not Phase 3 writer changes. See
      `.planning/phases/03-heading-signature-and-docx-generator/03-CONTEXT.md`
      D-08 for full rationale.
- [ ] **REQ-rule-engine-cohesion-audit** *(new — graphify follow-up)* —
      Verify the 244 weakly-connected nodes around the Rule Engine community
      and the ~33–34 INFERRED edges on `apply_rules_to_paragraph()` /
      `load_rules()`; document the dependency graph; refactor where the
      verification finds dead/dangerous edges (cohesion 0.06 → improved).

### Headings & normcontrol presentation (HEADING_AND_NORMCONTROL Block B + C)

- [ ] **REQ-heading-style-signature** *(new — HEADING_AND_NORMCONTROL Block B)*
      — Heading style signature extended (font name/size/bold/italic/underline/
      color/CAPS + alignment/indents/spacing/keep_with_next/keep_lines/
      page_break/widow) with direct-vs-inherited separation. Positive corpus
      stays `changed=0`; negative heading fixtures move toward target signature
      with no text changes.
- [ ] **REQ-methodical-profile-extract** *(new — HEADING_AND_NORMCONTROL Block C)*
      — `extract-methodical-profile` CLI ingests PPTX/PDF normcontrol
      presentation as a methodological source (not as a checked document);
      synthesised profile shown as a diff over `gost_7_32_2017` /
      `gost_r_7_0_100_2018_bibliography` before save; ambiguous requirements
      marked `needs_manual_review` with source/slide attribution.

### PDF audit slice (D-PDF-SCOPE locked)

- [ ] **REQ-pdf-text-only** — PDF support requires a text layer; OCR/scanned
      PDF/page-images explicitly out of scope; PDF is not edited (no
      autocorrection); only text-block extraction, basic layout features, ML
      classification, audit report. (PRD addendum)

### Quality gates / regression infrastructure

- [ ] **REQ-pipeline-logging** — Pipeline logs document-read, classification,
      rule-apply and save errors without leaking unnecessary PII beyond
      filename/path/technical context. (PRD US-027)
- [ ] **REQ-rules-quality-acceptance** — Every rule follows RuleRecord; every
      violation in report; every fix in report; unsafe fixes blocked;
      low-confidence blocks become manual review. (PRD §9.3)
- [ ] **REQ-input-preflight** — Preflight verifies readability and tolerates
      malformed paragraphs; empty blocks recorded for exclusion. (PRD US-002 —
      legacy partial coverage; ensure the new UI surfaces preflight failures
      without crashing.)
- [ ] **REQ-audit-regression-cli** *(new)* — `audit-regression` CLI compares a
      corpus run against a saved baseline (style-diff harness from
      FORMAT_FIX_PLAN Этап 1 + progressive limit support already in repo);
      output is a per-pair CSV plus a summary JSON. (Already partly implemented
      per recent commits — bring under the regression-test gate for FIX-tracks.)
- [ ] **REQ-mvp-acceptance** — End-to-end acceptance roll-up: the system
      accepts DOCX, extracts blocks, builds features, predicts, runs the rule
      audit, emits CSV report, blocks unsafe autofix, produces corrected DOCX
      only on safe changes, CLI modes run independently, Streamlit UI covers
      the main scenario.

## v2 Requirements

Deferred. Not in current roadmap.

### Dataset & schema work

- **REQ-dataset-schema** — Unified dataset schema (required + optional columns,
  `label_core` is training target, `split` controls routing). Currently relies
  on `dataset/annotations_*.csv` and is implicit; surfacing as a documented
  contract is a v2 task.
- **REQ-dataset-quality** — Validate annotation quality, surface class + split
  distributions, flag rare classes, preserve problematic rows.
- **REQ-problem-class-analysis** — Surface low-precision/recall classes;
  bibliography_item vs body_text confusion analysed separately.
- **REQ-logreg-baseline** — Logistic-regression baseline command + separate
  metrics report.
- **REQ-transformer-experiment** — Optional RuBERT-class experiment with
  AdamW + cross-entropy + early stopping; SVM stays primary unless robust gain.
- **REQ-ml-reproducibility-ss002** — Fixed split + metrics-per-run + persisted
  significant models + retained misclassifications + recoverable config.
  (Partially in place; formalise as a v2 contract.)
- **REQ-unified-csv-contracts-ss004** — Block identifiers aligned across
  extracted_blocks / predictions / reports; CSVs pandas-readable without
  manual cleanup.

### Future scope (post-MVP)

- OCR for scanned documents.
- Layout / coordinate analysis.
- Cross-block rules (heading hierarchy, caption sequence, numbering continuity).
- Visual diff of original vs corrected DOCX.
- Per-fix accept/reject UI.
- Feedback-loop dataset growth.
- Server / web UI with auth + history.
- FastAPI + Next.js + PostgreSQL production stack.

## Out of Scope

| Feature | Reason |
|---------|--------|
| OCR / scanned PDF / page images | Excluded by PRD §3.2 and TECH_STACK §15; only text-layer PDF is in scope. |
| LayoutLM / multimodal core model | Excluded by TECH_STACK §15; resource cost; not justified by current corpus. |
| FastAPI + Next.js + PostgreSQL production stack | Documented as future direction only (D-005, C-FUTURE-PRODUCTION-STACK); introducing now would derail the success metric. |
| External Document AI / cloud APIs | Privacy / local-only constraint (D-007, C-NFR-PRIVACY). |
| Auth / multi-user collaboration / accounts | Explicit C-UI-CONTRACT exclusion for the MVP UI. |
| In-browser DOCX editing | Explicit C-UI-CONTRACT exclusion. |
| Full visual diff of original vs corrected | Explicit C-UI-CONTRACT exclusion; tracked as v2 idea. |
| Substantive text rewrites by autocorrection | REQ-corrected-docx + D-004; only safe formatting fixes. |
| Replacing the rule layer with an end-to-end ML model | D-002 + REQ-nlp-stack-confirmation; rule layer is mandatory. |
| Transformer as the default UI model | D-006; SVM stays default, transformer opt-in. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-fix-style-guards | Phase 1 | Pending |
| REQ-fix-styled-paragraphs-no-direct-props | Phase 1 | Pending |
| REQ-rule-engine-cohesion-audit | Phase 1 | Pending |
| REQ-list-conservative-handling | Phase 2 | Pending |
| REQ-heading-style-signature | Phase 3 | Pending |
| REQ-fix-docx-generator-custom-styles | v2 (deferred from Phase 3) | Deferred — see Phase 3 D-08 |
| REQ-fix-negative-corpus-no-regression | Phase 4 | Pending |
| REQ-audit-regression-cli | Phase 4 | Pending |
| REQ-rules-quality-acceptance | Phase 4 | Pending |
| REQ-rule-profiles | Phase 5 | Pending |
| REQ-methodical-profile-extract | Phase 5 | Pending |
| REQ-ui-main-flow | Phase 6 | Pending |
| REQ-ui-problem-block-view | Phase 6 | Pending |
| REQ-input-preflight | Phase 6 | Pending |
| REQ-pipeline-logging | Phase 6 | Pending |
| REQ-ui-design-review | Phase 6 | Pending |
| REQ-pdf-text-only | Phase 7 | Pending |
| REQ-mvp-acceptance | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0 ✓

Validated requirements (legacy, not re-mapped): 21 — see "Validated" section.

---
*Requirements defined: 2026-05-12*
*Last updated: 2026-05-12 after ingest synthesis + roadmap regeneration*
