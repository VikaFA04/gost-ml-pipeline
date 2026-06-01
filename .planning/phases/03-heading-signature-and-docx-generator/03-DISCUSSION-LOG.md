# Phase 3: Heading signature & DOCX generator - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 03-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-13
**Mode:** interactive (no flags)

## Areas selected
All 4: Signature shape & storage, Direct vs inherited resolution, Inherited-Heading autofix policy, 58/59 custom-style strategy.

---

## Area 1 — Signature shape & storage

### Q: Where should the extended heading signature live in the extractor row dict?
**Options presented:**
1. Nested object `format_signature: {...}` (initially recommended)
2. Flat columns (~17 new top-level keys)
3. Hybrid — flat for current SVM features + nested `heading_format_signature`

**User clarification:** asked why option 3 wasn't recommended. Orchestrator agreed option 3 is better (zero ML schema churn, isolated heading-only nest). Recommendation switched.

**Selected:** Hybrid (option 3). → D-01.

### Q: Which `heading_format_signature` fields ship in Phase 3?
**Options presented (multiSelect):**
1. Font params (name, size, bold, italic, underline, color, caps)
2. Paragraph scalars (alignment, indents, spacing, line_spacing)
3. Flow flags (keep_with_next, keep_lines_together, page_break_before, widow_control)
4. Defer color, caps, widow to Phase 5

**Selected:** 1, 2, 3 (no defer). → D-02.

---

## Area 2 — Direct vs inherited resolution

### Q: How to resolve effective heading format?
**Options presented:**
1. Two-pass: read paragraph_format directly + walk style.base_style chain (recommended)
2. Raw lxml on w:pPr/w:rPr only
3. Compare paragraph_format vs paragraph.style.paragraph_format only (one-level, no cascade)

**Selected:** Option 1. → D-03.

### Q: Direct-vs-inherited surfacing in audit/rule layer?
**Options presented:**
1. Each field tagged `{value, source: "direct"|"inherited"|"unset"}` (recommended)
2. Two parallel signatures: direct_signature + effective_signature
3. Single value, no source tagging

**Selected:** Option 1. → D-04.

---

## Area 3 — Inherited-Heading autofix policy

### Q: Inherited mismatch — what autofix policy?
**Options presented:**
1. Route to review only — never autofix inherited (recommended)
2. Edit `document.styles[Heading N]` in-place
3. Write direct override on this paragraph only

**Selected:** Option 1. → D-05.

### Q: Direct mismatch — what autofix policy?
**Options presented:**
1. Autofix the direct override (recommended)
2. Route to review

**Selected:** Option 1. → D-06.

### Q: Positive-corpus regression gate — same as Phase 2 or new?
**Options presented:**
1. Reuse Phase 2 gate, extend with heading-direct-fix invariant (recommended)
2. Separate gate per phase (heading-only test file)

**Selected:** Option 1. → D-07.

---

## Area 4 — 58/59 strategy + rule shape + fixtures

### Q (initial draft): How does docx_writer handle 58/59 template-specific custom heading styles?
**Options presented:**
1. Extend writer config with per-template style-name map (recommended)
2. Alias custom → canonical at write time
3. Skip custom-styled headings entirely (route to review)

**User clarification:** "files 58 & 59 are not documents with gost decoration. These documents are practices, not coursework or graduate work."

Orchestrator reframed — original framing assumed 58/59 were GOST docs needing custom-style writer support, but they are practice reports outside the GOST profile's scope. Saved as project memories `positive_corpus_doc_types.md` and `scope_drop_58_59.md`. Re-asked Q1 with reframed options.

### Q (reformed): If 58/59 are practice docs, what should Phase 3 do about them?
**Options presented:**
1. Doc-type detect + skip GOST autofix (recommended)
2. Move REQ-fix-docx-generator-custom-styles to Phase 5
3. Drop the requirement — 58/59 are out of scope

**Selected:** Option 3. → D-08 (REQ-fix-docx-generator-custom-styles dropped from milestone; ROADMAP / REQUIREMENTS / `tests/test_positive_docx_regression.py` need edits as Phase 3 prereqs).

### Q: Heading rule schema granularity?
**Options presented:**
1. Per-field rules — one per signature field (recommended)
2. Single signature-match rule with structured expected_value

**Selected:** Option 1. → D-09.

### Q: Negative heading regression fixtures?
**Options presented:**
1. Hand-crafted minimal `heading_minimal.docx` (recommended)
2. Hand-crafted minimal + new GOST-decorated negative fixture

**Selected:** Option 1. → D-10.

---

## Deferred ideas captured during discussion
- **REQ-fix-docx-generator-custom-styles** → v2 / Phase 5 candidate.
- **Heading TOC integration** — out of scope.
- **Multi-level heading rules** (Heading 1 vs 2 vs 3 with different signatures) — researcher decides whether to expose `level` in rule selector or resolve via profile.
- **Color check** — researcher samples positive corpus first to avoid over-aggression.

## Memories created during discussion
- `positive_corpus_doc_types.md` (project) — 58/59 are practice docs, NOT GOST-decorated.
- `scope_drop_58_59.md` (project) — REQ-fix-docx-generator-custom-styles dropped from milestone with ROADMAP/REQUIREMENTS/test edit prereqs.
