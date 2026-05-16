# Changelog

All notable changes are documented here by milestone and phase.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

Planned for v1.1 — see `.planning/phases/999.*-*/` for detail.

- **999.1 — UI tabbed layout restoration:** Restore multi-tab navigation
  from pre-Phase-6 Streamlit interface; decide tabs vs hybrid design.
- **999.2 — DOCX formatter indent bugs:** Four indent defects (bulleted-
  list wrap, formula variable tab stop, bibliography indent, subheading
  indent inside bibliography section).

## [v1.0] — 2026-05-16

### Phase 9: Classical model zoo (2026-05-16)

- Extended classical-model comparison (LR / LinearSVM / ComplementNB /
  RandomForest / HistGBM+TruncatedSVD) with unified `predict_proba` on
  TF-IDF + structural-feature pipeline; new `compare-classical` CLI writes
  `results/reports/classical_zoo_<ts>/` with 6-row results.csv + summary +
  per-class F1 markdown.
- `linear_svm_production` row clears Phase 8 SC-2 raw-ML floor
  (weighted_f1 ≥ 0.94, macro_f1 ≥ 0.86); `make compare-classical-acceptance`
  exits 0 end-to-end; dual-source SC-2 gate feeds milestone acceptance.

### Phase 7: PDF text-layer audit slice (2026-05-15)

- PDF documents with extractable text layer accepted for read-only audit:
  extraction → classification → audit CSV; scanned PDFs rejected with
  locked Russian banner; no OCR, no corrected PDF written.
- Streamlit UI accepts `.pdf` alongside `.docx`, labels PDF as audit-only;
  all 7 UAT points pass (3 gaps closed in Plans 07-04 + 07-05); README
  §Limits documents text-layer + no-OCR + no-autofix constraints.

### Phase 6: Streamlit UI redesign (2026-05-15)

- Full audit flow rebuilt end-to-end: upload DOCX → pick profile → run
  audit → summary counters → per-block table → download CSV / corrected
  DOCX; `review` and `error` blocks visually distinct; confidence shown.
- Preflight failures surface as user-facing messages (no traceback leak);
  RunLog single-writer logger enforces PII boundary; design-review
  approved-with-followups by project owner 2026-05-15.

### Phase 5: Rule profiles & methodical-profile ingestion (2026-05-14)

- Multiple selectable rule profiles (`gost_7_32_2017.json`,
  `gost_r_7_0_100_2018_bibliography.json`, `local_university_profile.json`);
  chosen profile ID recorded in every report header.
- `extract-methodical-profile` CLI ingests a normcontrol PDF, produces a
  draft profile, shows diff against base profile, requires explicit
  `--apply --force --reason` confirmation; ambiguous requirements land as
  `needs_manual_review` with source/page attribution.

### Phase 4: Regression gate (2026-05-14)

- `audit-regression` CLI tracks negative-corpus diff-rate against a
  per-pair baseline JSON (`tests/baselines/negative_corpus.json`); 3.docx
  pair ceiling 0.359712 root-cause-justified per D-05 Branch B;
  `make regression-gate` exits 0 on the Option D subset.
- GHA workflow `.github/workflows/regression-gate.yml` gates every fix-track
  PR; designed-regression PR validated end-to-end (runs #25846822154 GREEN +
  #25847679849 RED); gate live on VikaFA04/gost-ml-pipeline.

### Phase 3: Heading signature & DOCX generator (2026-05-13)

- Heading signature extended to 18 fields (font name/size/bold/italic/
  underline/color/CAPS + 10 paragraph-format fields); inherited vs direct
  source separated — inherited mismatches route to `review`, direct
  overrides on Heading-styled paragraphs are autofixed.
- GOST-decorated positive subset stays `changed=0` for heading rules
  (regression gate extended); negative heading fixtures move toward target
  signatures with no text changes; TOC and list structure stable.

### Phase 2: Bibliography & list semantics (2026-05-12)

- Bibliography title (`СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ` and
  `ИСПОЛЬЗУЕМЫХ` variant) classified by deterministic postprocess override
  even when SVM returns `body_text`; bibliography entries unified under one
  Word `numId` after `audit-docx --apply-safe`.
- Long text paragraphs without `numId` not coerced into lists; marker-only
  lists without `numId` route to `review`; conservative list handling
  matches positive corpus shape.

### Phase 1: Engine guardrails & cohesion audit (2026-05-12)

- Rule engine stops applying `body_text` rules to Heading / TOC /
  List Paragraph / Caption-styled paragraphs (`format-docx --apply-safe`
  on GOST-decorated positive subset produces `changed=0`).
- 67 INFERRED edges in the rule-engine dependency graph audited; cohesion
  score 0.06 → improved after D-10 low-risk refactors; existing 21+ test
  baseline preserved.

[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
