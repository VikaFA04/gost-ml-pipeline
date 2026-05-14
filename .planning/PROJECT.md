# gost-formatter

## What This Is

A local Python application that audits and (where safe) auto-corrects Russian academic
`.docx` documents against GOST normcontrol rules. It splits a DOCX into structural
blocks, classifies each block with a Linear SVM + TF-IDF + format-features pipeline,
applies a JSON-driven rule engine, emits a CSV audit report, and optionally writes a
corrected DOCX. Users interact via a local Streamlit UI or a CLI; documents never
leave the machine.

## Core Value

The system must produce a trustworthy audit of a DOCX against GOST rules — every
status explainable, no silent rewrites of correct content, and a downloadable
corrected DOCX only when the change is provably safe.

If everything else fails, the audit + safe-fix pipeline must remain correct: a
beautiful UI on a destructive engine is worse than a working CLI on an honest engine.

## Requirements

### Validated

<!-- Already shipped and verified in current repo / ROADMAP history -->

- ✓ Linear SVM + TF-IDF + format-features baseline trained — `weighted_f1=0.9829`,
  `macro_f1=0.9414` on `dataset/annotations_test.csv`. (legacy Этап 1)
- ✓ Audit-only and safe-format end-to-end on `50.docx`:
  `blocks_total=260`, `error=0`, unsafe autofix blocked, idempotent on rerun. (legacy Этап 2)
- ✓ Streamlit UI defaults to SVM baseline; uploader restricted to `.docx`. (legacy Этап 3)
- ✓ CLI parser smoke + dataset contract + predict schema tests; 21+ passing tests. (legacy Этап 4)
- ✓ FORMAT_FIX_PLAN Этап 1–7: regression harness for DOCX style-diff; `None`-inheritance
  no longer auto-fixed; List Paragraph guard; list rules re-tuned to positive corpus
  (level 0 `2.25/-1.0/2.25`, level 1 `2.5/-1.0/2.5`); heading/caption autofix softened
  to review; positive corpus `1/4/58/59.docx` all `changed=0`.
- ✓ README documents current CLI flow + known limitations.
- ✓ Phase 04 (regression-gate): negative-corpus per-pair diff-rate baseline locked in `tests/baselines/negative_corpus.json` (3-pair Option D subset); `audit-regression --update-baseline / --reason` CLI; `make regression-gate` local check + `.github/workflows/regression-gate.yml` GHA gate validated via two PRs (clean PR run #25846822154 PASS, designed-regression PR run #25847679849 FAIL). Per Phase 4 D-05 Branch B — 3.docx pair ceiling 0.359712, root cause = Phase 3 D-05/D-06 dispatcher commit 7207cbe.
- ✓ Phase 05 (rule-profiles-methodical-profile-ingestion): per-leaf `_source` annotation + derived `needs_manual_review` in `methodical_extractor.py`; `profile_diff` module (U+2192 readable diff over flattened JSON paths); `extract-methodical-profile` CLI rewrite (dry-run default + `--apply`/`--force --reason ≥8` D-004 audit trail, T-04-02/T-05-01 guards); two-tier profile schema lint (`tests/test_profile_quality_acceptance.py`); SC-1 `--profile-id` threaded through `audit-docx`/`format-docx`/`audit-regression`; 6-file CI regression gate (Phase 4 4-file → +2 Phase 5) validated via clean PR #1 GREEN (run 25862688735) + RED probe PR #3 FAIL (run 25862868163, missing `is_default` schema lint catch). Бергер 1.4MB PDF fixture committed at `tests/fixtures/methodical/normocontrol_berger.pdf`. Presentation-format ingestion dropped 2026-05-14 per 05-CONTEXT D-01.

### Active

<!-- Current milestone scope. The success metric: UI usability + critical-bug count = 0. -->

UI redesign track:
- [ ] **UI-01**: Streamlit UI restructured around the audit flow (upload → profile
      select → run → results → download), no dead-ends, no orphaned tabs.
- [ ] **UI-02**: Per-block result view distinguishes `no_change`, `changed`, `review`,
      `error`, `blocked_unsafe_autofix` with consistent visual language.
- [ ] **UI-03**: Low-confidence and `review` blocks are visually surfaced with the
      reason from `explanation`, and the original block text is always inspectable.
- [ ] **UI-04**: Summary counters (total / no_change / changed / review / error) are
      visible above the per-block table.
- [ ] **UI-05**: Profile selection includes GOST profile(s) + any local profile;
      chosen profile is shown in the report header.
- [ ] **UI-06**: Downloads (audit CSV + corrected DOCX when safe fixes exist) work
      and never overwrite the original.
- [ ] **UI-07**: Design-review pass on UI by the project owner.

Critical-bugfix track (FORMAT_FIX_PLAN open items + HEADING_AND_NORMCONTROL Block A/B):
- [ ] **FIX-01**: Full Heading-style guard, TOC guard, Caption guard before applying
      `body_text` rules (FORMAT_FIX_PLAN Этап 3 remainder).
- [ ] **FIX-02**: Heading/toc/List Paragraph/Caption styled paragraphs stop receiving
      extra direct properties (FORMAT_FIX_PLAN Этап 2 open item).
- [x] **FIX-03**: Negative-corpus regression gate live; per Phase 4 D-05 Branch B,
      `3.docx` pair ≤ 0.359712 (root cause = Phase 3 D-05/D-06 dispatcher, see
      `.planning/phases/04-regression-gate/04-WAVE-A-3docx-rootcause.md`). Validated.
- [ ] **FIX-04**: DOCX generator (`src/generate/docx_writer.py`) handles
      template-specific custom styles for `58.docx`/`59.docx`
      (FORMAT_FIX_PLAN Этап 9).
- [ ] **FIX-05**: Bibliography list — recognise
      `СПИСОК ИСПОЛЬЗОВАННЫХ/ИСПОЛЬЗУЕМЫХ ИСТОЧНИКОВ` as `bibliography_title`,
      apply a single `numPr` across the whole list, single shared `numId`
      (HEADING_AND_NORMCONTROL Block A).
- [ ] **FIX-06**: Heading style signature extended (font name/size/bold/italic/
      underline/color/CAPS + alignment/indents/spacing/keep_with_next/keep_lines/
      page_break/widow) with style-inheritance vs direct-formatting separation
      (HEADING_AND_NORMCONTROL Block B).
- [ ] **FIX-07**: Rule Engine cohesion audit follow-up — verify the 244
      weakly-connected nodes and ~33–34 INFERRED edges around
      `apply_rules_to_paragraph()` / `load_rules()` flagged by the graphify report.
- [ ] **FIX-08**: Regression test suite covers every fixed bug (positive corpus
      `changed=0`, negative corpus monotonically improving).

PDF audit slice (locked, see Key Decisions D-PDF-SCOPE):
- [ ] **PDF-01**: PDF accepted only when a text layer is extractable; no OCR.
- [ ] **PDF-02**: Read-only — no PDF writing, no autocorrection on PDF input.
- [ ] **PDF-03**: Audit report generated for PDF input on the same CSV schema as
      DOCX.

Methodical-profile slice (HEADING_AND_NORMCONTROL Block C, partly already CLI-wired):
- [ ] **PROF-01**: `extract-methodical-profile` CLI ingests a normcontrol
      presentation (PPTX/PDF) as a methodological source, not as a checked document.
- [ ] **PROF-02**: Synthesised profile is shown as a diff over
      `gost_7_32_2017` / `gost_r_7_0_100_2018_bibliography` before save; ambiguous
      requirements are marked `needs_manual_review` with source/slide attribution.

### Out of Scope

- FastAPI + Next.js + PostgreSQL production stack — post-MVP only, documented as
  future direction; introducing it now would derail the success metric.
- OCR / scanned-PDF / LayoutLM / multimodal models — explicitly excluded by PRD
  and TECH_STACK; required PDF support is text-layer only.
- Cloud Document AI services — privacy/local-only constraint (D-007).
- Authentication, user accounts, multi-user collaboration, in-browser DOCX editing,
  full visual diff of original vs corrected — out of current UI scope per
  C-UI-CONTRACT.
- Substantive text rewrites by autocorrection — only safe formatting fixes
  (D-004, REQ-corrected-docx).
- Replacing the rule-based GOST layer with a single end-to-end ML model —
  rule layer is mandatory (D-002, REQ-nlp-stack-confirmation).
- Transformer model as the default UI choice — SVM is primary; transformer is
  opt-in experimental (D-006).

## Context

- **Existing system**: Pipeline is functional and tested
  (DOCX extraction → TF-IDF + Linear SVM → postprocess → JSON rule engine →
  CSV audit → optional safe DOCX → Streamlit UI). Baseline artifact:
  `results/models/svm_block_classifier_20260506_082307.joblib`. 21+ tests pass.
- **Active dataset path**: `dataset/annotations_{train,val,test}.csv`. Do NOT use
  `data/prepared/` for training without an explicit request — see
  C-DATA-PATHS conflict note.
- **CLI surface**: `train`, `evaluate`, `predict`, `extract-docx`, `audit-docx`,
  `format-docx`, `audit-regression`, `extract-methodical-profile`. (PRD/SPEC list five;
  the remaining three are implementation extensions required by REQ-corrected-docx,
  the FORMAT_FIX_PLAN regression harness, and HEADING_AND_NORMCONTROL Block C.)
- **Known UI weakness**: User flagged the current Streamlit UI as poor quality and
  has commissioned a redesign. UI redesign and critical bug fixes are the next
  milestone.
- **Known engine weakness — graphify audit**: `Rule Engine` community has cohesion
  score 0.06; 244 weakly-connected nodes; `apply_rules_to_paragraph()` and
  `load_rules()` each carry ~33–34 INFERRED edges that need verification. This
  informs the FIX-07 requirement.
- **Open PRD §12 questions** (carried for downstream planning; not blocking the
  current milestone):
  - Minimum confidence threshold for autocorrection.
  - Severity-level expansion (`info` / `minor` / `major` / `critical`).
  - Whether MVP labels are the core set or `label_detailed`.
  - Visual navigation across problem blocks inside the UI.
  - Manual class-override per block in the UI.
  - Feedback-loop dataset growth strategy.
  - Whether original + corrected DOCX should be persisted or streamed-only.

## Constraints

- **Tech stack — runtime**: Python 3.10+ (3.11+ recommended), venv + pip,
  `requirements.txt` pinned. OS: Windows / Linux / WSL. (C-PYTHON-RUNTIME)
- **Tech stack — DOCX**: `python-docx` ≥ 1.1, `lxml` allowed for low-level OOXML
  when python-docx is insufficient. PDF parsing: PyMuPDF / pdfplumber (read-only,
  text-layer only). OCR explicitly excluded. (C-DOCX-STACK + PDF scope lock)
- **Tech stack — ML**: scikit-learn `TfidfVectorizer` + `LinearSVC` (primary),
  logistic regression as baseline experiment, transformer (RuBERT-class)
  experimental only, `joblib` ≥ 1.3 for persistence. (C-ML-STACK, D-001)
- **Tech stack — UI**: Streamlit ≥ 1.35; FastAPI + Next.js + PostgreSQL is future
  direction, NOT MVP. (D-005, C-UI-CONTRACT, C-OUT-OF-MVP-STACK)
- **Tech stack — runtime targets**: Local Streamlit UI + CLI commands
  (`extract-docx`, `audit-docx`, `format-docx`, `predict`, `train`,
  `audit-regression`, `extract-methodical-profile`). No server deployment in this
  milestone.
- **Rule engine schema**: each rule is JSON with `id`, `applicable_labels`,
  `parameter`, `expected_value`, `action`, `severity`, `autocorrect`, `priority`.
  Block audit status enum: `no_change`, `changed`, `review`, `error`. (C-RULE-ENGINE)
- **Label taxonomy**: SPEC taxonomy of 16 classes is the authoritative label set;
  PRD §7.3 subset of 10 classes is the MVP working set. Names must match across
  dataset, model, postprocess, rule engine, UI. (C-LABEL-SCHEMA + INGEST-CONFLICTS INFO #1)
- **Artifact directories**: models → `results/models/`; metrics → `results/metrics/`;
  predictions → `results/predictions/`; extracted blocks →
  `results/extracted_blocks/`; audit reports → `results/reports/`; formatted DOCX
  → `results/formatted_docs/`. Filenames timestamped. (C-ARTIFACT-DIRS)
- **Privacy**: documents processed locally; no external API submission; logs
  avoid full document text. (C-NFR-PRIVACY, D-007)
- **Reliability**: never abort on a single broken block; per-block errors land
  in `status=error`; original DOCX never overwritten. (C-NFR-RELIABILITY)
- **Explainability**: every violation tied to a specific rule; every fix tied to
  a specific rule; every block has an understandable status; low confidence is
  visually surfaced. (C-NFR-EXPLAINABILITY)
- **ML quality gates**: weighted_f1 ≥ 0.94 (baseline 0.9829); macro_f1 must not
  regress from current 0.9414; 100% of blocks explainable; 100% of detected
  unsafe fixes blocked. (C-METRICS-GATES, REQ-ml-quality-acceptance)
- **Reproducibility**: fixed train/val/test split, feature + model config saved
  with artifacts, error CSVs retained. (C-NFR-REPRODUCIBILITY)

## Key Decisions

<!--
  Status legend:
    Locked     — decision is sealed; revisiting requires explicit /gsd-amend-decision.
    Revisit    — under review.
    Pending    — too early to evaluate outcome.
    ✓ Good     — outcome confirmed.
    ⚠ Revisit  — outcome concerning.
-->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **D-PDF-SCOPE (LOCKED)**: PDF text-layer audit (read-only, no OCR, no autofix) is IN SCOPE for next slice; addendum wins over PRD §3.2 exclusion. | Resolves INGEST WARNING. Addendum is more recent and explicitly limits PDF to text-layer audit. Aligns with PDF-01/PDF-02/PDF-03 requirements and REQ-pdf-text-only. | **Locked** — do not silently re-exclude PDF; any reversal must be explicit. |
| **D-001**: Linear SVM + TF-IDF + format-features as primary classifier. | Block class depends on text and formatting; SVM on small corpus beats RuBERT; formatting features matter. | ✓ Good — `weighted_f1=0.9829`, `macro_f1=0.9414`. Not locked. |
| **D-002**: Hybrid ML + rule-based architecture; rule layer is mandatory. | ML decides block role; deterministic JSON rules drive normcontrol checks and safe autofixes. Cannot be replaced by ML alone. | ✓ Good. Not locked. |
| **D-003**: DOCX-only as MVP format; PDF text-layer addendum is the only PDF path. | Scope discipline. Superseded narrowly by D-PDF-SCOPE which scopes PDF text-layer audit IN. OCR/scanned PDF remain out. | ✓ Good. Not locked. |
| **D-004**: Safe autocorrection only; user remains final reviewer. | Autofix requires `autocorrect: true` + sufficient confidence + unambiguous structure; ambiguous blocks become `review`; inherited `None` is not a violation; body_text geometry + list_item scalars are review-only. | ✓ Good (FORMAT_FIX_PLAN Этап 6). Not locked. |
| **D-005**: Streamlit chosen as MVP UI; FastAPI/Next.js reserved for future. | MVP throughput priority. Local-only deployment fits. | Pending — to be re-confirmed after UI redesign design-review. Not locked. |
| **D-006**: SVM baseline is the default model in UI; transformer is opt-in. | When baseline artifact present, surface and select it first. | ✓ Good (`list_model_options()` returns baseline first). Not locked. |
| **D-007**: Local-only processing; no external Document AI services. | Privacy + thesis-grade reproducibility. Future web/server version requires its own retention policy. | ✓ Good. Not locked. |

---
*Last updated: 2026-05-14 after Phase 05 rule-profiles-methodical-profile-ingestion completion*
