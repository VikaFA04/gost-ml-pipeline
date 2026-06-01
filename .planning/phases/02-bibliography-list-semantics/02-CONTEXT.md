# Phase 2: Bibliography & list semantics - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Detect bibliography sections; enforce single `numId` per bibliography subsection (with hierarchical 2-level Word numbering rendering `<section>.<index>`); route ambiguous lists to `review` rather than auto-coercing; extend profile schema so Phase 5 can ingest different normcontrols.

In scope:
1. Postprocess override: `BIBLIOGRAPHY_TITLE_RE` match deterministically sets `label=bibliography_title`.
2. Bibliography subsection detection by position (after bibliography_title, before BIBLIOGRAPHY_STOP_RE) + Heading 1 style — drop legacy text-based `BIBLIOGRAPHY_SUBHEADING_RE`.
3. Single numId per subsection via 2-level Word numbering (Word renders `1.1`, `1.2`, `2.1` ...).
4. Idempotent allocator (scan existing numbering.xml on first call per document).
5. Ambiguous-list routing rules: marker + no numId → review; no marker + no numId + short body_text → stay body_text.
6. Profile schema extension: `numbering.bibliography.scope`, `list_detection.max_fallback_words`, `list_detection.max_fallback_chars` fields. Default GOST profile carries current values; Phase 5 owns selection UX + ingest.
7. Tests: hand-crafted `tests/fixtures/bibliography_minimal.docx` + real DOCX from `negative_examples/`.

Out of scope for Phase 2:
- Heading signature extension (Phase 3).
- `audit-regression` CLI gate (Phase 4).
- Multiple selectable profiles UX, `extract-methodical-profile` CLI, ingest from normcontrol PPTX/PDF (Phase 5).
- UI changes (Phase 6 — UI hint deferred).
- PDF (Phase 7).

</domain>

<decisions>
## Implementation Decisions

### Area 1 — Bibliography title override
- **D-01:** Deterministic override. When `BIBLIOGRAPHY_TITLE_RE.match(text)` is truthy and SVM returned `body_text` (or anything else other than `bibliography_title`), postprocess unconditionally sets `label = bibliography_title`. No SVM confidence threshold. No `manual_review_required` log — the override is a known, documented behavior of the rule engine.
- **D-02:** Keep current `BIBLIOGRAPHY_TITLE_RE` pattern: `^(список\s+(использованных|используемых)\s+источников|библиографический\s+список|литература)$` (case-insensitive). Do not add EN variants, do not add numbered-prefix tolerance, do not loosen the middle word. ROADMAP success criterion 1 wording (`СПИСОК ИСПОЛЬЗОВАННЫХ/ИСПОЛЬЗУЕМЫХ`) is already covered.

### Area 2 — Single-numId scope, subsection detection, hierarchical numbering
- **D-03:** Phase 2 keeps the **per-subsection numId** scope as the default (current `(id(numbering_root), section_index)` key in `_BIBLIOGRAPHY_NUM_IDS`). Add a profile schema field `numbering.bibliography.scope` with valid values `per_document | per_section | per_subsection_pattern` so Phase 5 can override from an ingested normcontrol profile. Phase 2 reads the field via `profile_loader`; if absent, defaults to `per_section`. No hard policy lock-in.
- **D-04:** Bibliography subsection detection inside bibliography context = **position + Heading 1 style**:
  - Position: paragraph appears AFTER a `bibliography_title` paragraph (set by D-01 override) AND BEFORE a `BIBLIOGRAPHY_STOP_RE` match (`заключение|приложение*`).
  - Style: `classify_style(paragraph) == "heading"` (reuses Phase 1 `src/rules/style_signatures.classify_style`).
  - Text pattern (`BIBLIOGRAPHY_SUBHEADING_RE`, `BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE`) is no longer the gate — actual section names vary by normcontrol (e.g. `ИССЛЕДОВАТЕЛЬСКИЙ РАЗДЕЛ` vs `ТЕОРЕТИЧЕСКАЯ ЧАСТЬ`). The regex moves to a fallback for documents where Heading 1 style is missing.
  - `bibliography_section_index` increments on each Heading 1 inside bibliography context.
- **D-05:** Source entries inside each bibliography subsection numbered via **2-level Word numbering abstract**. One `numId` per subsection (per D-03 default). The abstract has `level 0 = section_index` (decimal, no override) and `level 1 = entry_index` (decimal). Word renders the entry-displayed prefix as `<section>.<index>` automatically — no manual text injection. Allocator emits the abstract once per document, reuses across subsections.
- **D-06:** Mixed/heterogeneous existing numIds in a subsection — **coerce to first-valid**:
  - Scan all entries in the subsection on first encounter.
  - First entry carrying a valid `numId` (one that exists in `numbering.xml`) wins.
  - All other entries in the subsection get coerced to that `numId`.
  - If none of the entries carry a valid `numId` → allocate fresh `numId` from a new 2-level abstract.
  - `applied_fixes` includes `numbering:coerced_to_numId=<N>` so audit explains the change.
  - Idempotent: second run on the same document finds a single valid `numId` shared across the subsection → no change.
- **D-07:** Idempotency on re-run is enforced via **numbering.xml scan at first allocator call per document**. `_get_bibliography_num_id(paragraph, section_index)` opens `paragraph.part.numbering_part.element`, finds all paragraphs in document order labeled `bibliography_item`, collects their existing `numId`s grouped by `section_index`, and seeds `_BIBLIOGRAPHY_NUM_IDS[(id(numbering_root), section_index)] = first_valid_numId`. This also fixes the latent cross-document leak when `id()` collides between sequential Paragraph loads in the same Python process.

### Area 3 — Ambiguous-list routing
- **D-08:** Marker definitions stay current. `NUMBERED_MARKER_RE = ^\s*(?:\d+[\.\)]|[A-Za-zА-Яа-я][\.\)])\s+`. `BULLET_MARKER_RE = ^\s*[-—–•●■◦]\s+`. No hierarchical extension (`1.1`, `1.1.1` etc.) — D-05 has Word numbering render that automatically; manual text-prefix lists are out of scope.
- **D-09:** **Marker present + no numId → review.** When a paragraph SVM-predicted `body_text` (or any label) has a leading marker matching `NUMBERED_MARKER_RE` or `BULLET_MARKER_RE` but no Word `numId` reference, set `action=review` with `explanation: ambiguous_list_marker_no_numId`. Do NOT call `apply_list_numbering`. This satisfies ROADMAP success criterion 3 ("marker-only lists without numId become review").
- **D-10:** **No marker + no numId + short body_text → stay body_text.** No relabel, no review routing, no `classify_style` intervention. Phase 1 style guard already blocks body_text rules on styled paragraphs (Heading/TOC/Caption/List). This decision specifically covers the body-text-on-Normal-style case where length is below `MAX_FALLBACK_LIST_*` thresholds. Mirror of ROADMAP success criterion 3 ("long text paragraphs without numId are not coerced into lists").
- **D-11:** **Thresholds move to profile schema.** Phase 2 introduces profile fields `list_detection.max_fallback_words` (default 40) and `list_detection.max_fallback_chars` (default 300). Code-level constants `MAX_FALLBACK_LIST_WORDS` and `MAX_FALLBACK_LIST_CHARS` are deleted from `src/rules/rule_engine.py` and read from active profile via `profile_loader`. Default GOST profile (`src/rules/profiles/gost_7_32_2017.json`) carries 40/300.
- **D-12:** **Phase 2 owns schema only; Phase 5 owns UX.** No CLI flag for profile selection in Phase 2. No methodical-profile ingest. `profile_loader` already supports loading from disk; Phase 2 only extends what fields are valid in the JSON. Phase 5 will add `--profile <path>` flag, profile-picker UI, and `extract-methodical-profile` CLI.

### Area 4 — Bibliography autofix scope + tests
- **D-13:** `apply_bibliography_format` safe-fix scope split:
  - Always safe: `style_name` (default `List Number`), `numbering` (numId allocation per D-05/D-06/D-07).
  - Profile-driven (apply if profile config has the field, else skip): `alignment`, `first_line_indent_cm`, `left_indent_cm`, `line_spacing`, `space_before_pt`, `space_after_pt`.
  - When profile config is absent or omits a field, the field is NOT touched — paragraph keeps its inherited value (Phase 1 `style_guard_block:` philosophy: no silent rewrites of inherited values).
- **D-14:** Tests use BOTH hand-crafted and real fixtures:
  - **Hand-crafted unit fixture** `tests/fixtures/bibliography_minimal.docx` — 1 bibliography_title + 2 subsections (heading-styled, mixed naming) + 3 entries each, ONE subsection with mixed numIds to exercise D-06 coerce path. Built by a `_build_bibliography_minimal.py` script next to `_build_style_guard_minimal.py` (Phase 1 pattern).
  - **Integration fixture** — discover any `negative_examples/*.docx` containing `BIBLIOGRAPHY_TITLE_RE` match in extracted text; run `audit-docx --apply-safe` and assert all `bibliography_item` rows carry the same `numId` and `applied_fixes` includes `numbering` for at least one row.
- **D-15:** Regression gate keeps Phase 1 baseline + adds negative mean diff-rate:
  - `format-docx --apply-safe` on `positive_examples/{1,4,58,59}.docx` MUST keep `changed=0` (Phase 1 baseline — these 4 are the cleanest of 59).
  - Negative corpus mean `after_diff_rate` (column from `audits_to_frame` in `src/evaluation/format_regression_audit.py`) MUST stay `≤ 0.4781` (FORMAT_FIX_PLAN Этап 8 baseline carried by Phase 1).
  - Whole positive corpus (all 59 files) is NOT a gate in Phase 2 — files contain real defects. Phase 4 introduces an audit-regression CLI gate that handles the soft N_changed_post ≤ N_changed_pre target across all 59.

### Claude's Discretion
- Exact 2-level Word numbering abstract template (XML structure for `w:abstractNum` with 2 `w:lvl` children) — implement following existing `_create_section_abstract_num_id` pattern.
- Internal naming of new helpers (e.g. `_seed_bibliography_num_ids_from_doc()` for D-07, `_collect_bibliography_subsections()` for D-04).
- Exact profile schema layout under `numbering.bibliography.*` and `list_detection.*` — JSON shape emerges in plan-phase.
- Test naming convention (`test_bibliography_title_override`, `test_bibliography_subsection_per_section_numId`, `test_ambiguous_list_marker_no_numId_routes_to_review`, `test_bibliography_minimal_docx_single_numId_per_subsection`, `test_idempotent_on_rerun`).
- Whether D-04 fallback regex (legacy `BIBLIOGRAPHY_SUBHEADING_RE`) is kept as a Phase 5 hook or removed entirely — researcher decides based on negative corpus inspection.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & success criteria
- `.planning/ROADMAP.md` §"Phase 2: Bibliography & list semantics" — phase goal, depends-on (Phase 1), success criteria 1–4.
- `.planning/REQUIREMENTS.md` REQ-list-conservative-handling — PRD US-019 + HEADING_AND_NORMCONTROL Block A.

### Project-level
- `.planning/PROJECT.md` <decisions> D-002 (rule layer mandatory), D-004 (safe-only autocorrection: no silent rewrites of correct content).
- `.planning/intel/decisions.md` D-001…D-007 — informational decisions.
- `.planning/intel/constraints.md` C-NFR-EXPLAINABILITY, C-NFR-RELIABILITY.

### Phase 1 carry-forward
- `.planning/phases/01-engine-guardrails-cohesion-audit/01-CONTEXT.md` — Phase 1 decisions (style_signatures module, classify_style, style_guard_block: explanation pattern).
- `.planning/phases/01-engine-guardrails-cohesion-audit/01-VERIFICATION.md` — what Phase 1 actually shipped (53 tests, cohesion gate).
- `src/rules/style_signatures.py` — `classify_style`, `paragraph_has_list_style`, `paragraph_has_heading_style`, plus 4 regex constants. Phase 2 reuses `classify_style` for D-04.

### Defect catalog & remediation history
- `.planning/FORMAT_FIX_PLAN.md` §"HEADING_AND_NORMCONTROL Block A" — original bibliography failure catalog.
- `.planning/intel/context.md` §"Critical pipeline defects — DOCX formatter" — synthesized defect summary, FIX-05 entry.

### Source code (read before modifying)
- `src/postprocess/postprocess_rules.py` — `_is_bibliography_title`, `_is_bibliography_subheading`, `_stops_bibliography_context`, `_has_list_metadata`, `_looks_like_list_fragment`, `BIBLIOGRAPHY_TITLE_RE`/`BIBLIOGRAPHY_SUBHEADING_RE`/`BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE`/`BIBLIOGRAPHY_STOP_RE`/`BIBLIOGRAPHY_ENTRY_RE`. D-01 strengthens the override path here. D-04 changes detection to position + Heading 1 style.
- `src/rules/rule_engine.py` — `apply_bibliography_format` (line 230), `apply_bibliography_numbering` (line 409), `_get_bibliography_num_id` (line 367), `_BIBLIOGRAPHY_NUM_IDS` (line 43), `_apply_bibliography_rules` (line 609), `NUMBERED_MARKER_RE`/`BULLET_MARKER_RE` (line 27–28), `MAX_FALLBACK_LIST_WORDS`/`CHARS` (line 30–31). All Area 2/3/4 decisions land here.
- `src/rules/profile_loader.py` + `src/rules/profile_validator.py` — extend with D-03 and D-11 schema fields.
- `src/rules/profiles/gost_7_32_2017.json` (or equivalent path under `src/rules/profiles/`) — default profile carrying `numbering.bibliography.scope = per_section`, `list_detection.max_fallback_words = 40`, `list_detection.max_fallback_chars = 300`. Researcher should locate exact path; profile dir exists per `ls src/rules/profiles/`.
- `src/rules/formatting_rules_v1.json` — rule schema (do NOT modify — Phase 5 territory; Phase 2 only adds profile-level config fields).
- `src/evaluation/format_regression_audit.py` `audits_to_frame` — produces the `after_diff_rate` column gated by D-15.

### Test corpus
- `positive_examples/1.docx`, `4.docx`, `58.docx`, `59.docx` — Phase 1 baseline regression set (still `changed=0` after Phase 2). All 59 files in `positive_examples/` are mostly-correct documents with small defects (`помарки`); ALL 59 is NOT a Phase 2 gate.
- `negative_examples/` — discover bibliography-bearing docs at planning time for D-14 integration fixture.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_is_bibliography_title` / `BIBLIOGRAPHY_TITLE_RE` in `src/postprocess/postprocess_rules.py` — existing detection. D-01 builds on top.
- `apply_bibliography_format`, `apply_bibliography_numbering`, `_get_bibliography_num_id`, `_create_section_abstract_num_id` in `src/rules/rule_engine.py` — bibliography numbering infrastructure already exists. D-05/D-06/D-07 modify these.
- `classify_style` from `src/rules/style_signatures.py` (Phase 1) — reused in D-04 for heading detection in bibliography context.
- `style_guard_block:` explanation pattern (Phase 1) — D-09 mirrors it with `ambiguous_list_marker_no_numId`.
- `_BIBLIOGRAPHY_NUM_IDS` module-level dict — keyed by `(id(numbering_root), section_index)`. D-03 keeps the key shape; D-07 seeds it from numbering.xml scan.
- `profile_loader.py` + `profile_validator.py` — already load JSON profile from disk. D-03 and D-11 extend the schema.

### Established Patterns
- Postprocess label override happens BEFORE rule engine dispatch. Phase 2 follows: D-01 override lives in postprocess, not rule_engine.
- Two-level Word numbering abstract pattern exists in `_create_section_abstract_num_id` — but currently used to allocate per-section bullet/decimal abstracts. D-05 extends to a 2-level abstract that renders `<section>.<index>`.
- Audit explanation strings carry `<category>:<detail>` shape — D-09 follows the convention.
- Hand-crafted DOCX fixture pattern from Phase 1 (`tests/fixtures/_build_style_guard_minimal.py` + `tests/fixtures/style_guard_minimal.docx`) — D-14 reuses for bibliography_minimal.

### Integration Points
- `_apply_bibliography_rules` (line 609 of `rule_engine.py`) — dispatch hub for biblio rules. D-13 changes safe/review classification inside this function.
- `apply_rules_to_paragraph` (line ~635) — Phase 1 style_guard early-return lives here. D-10 needs no new code (existing guard covers Normal-styled body_text).
- `audit-docx --apply-safe` CLI entry — Phase 2 integration test target.
- Negative regression: direct `audit_negative_directory(...)` call (Plan 03 precedent — bypasses `src.main` sklearn import path).

</code_context>

<specifics>
## Specific Ideas

- Russian normcontrol bibliography subsections appear AFTER `СПИСОК ИСТОЧНИКОВ` and use the SAME Heading 1 style as body sections (`1 ИССЛЕДОВАТЕЛЬСКИЙ РАЗДЕЛ`, `1 ТЕОРЕТИЧЕСКАЯ ЧАСТЬ`). Section names vary by normcontrol — detection MUST be position-based not text-based. (User clarification, this session.)
- Source entries display as `<section>.<entry>` (e.g. `1.1`, `1.2`, `2.1`). Word numbering hierarchy renders this automatically when the 2-level abstract is configured correctly. (D-05.)
- All 59 files in `positive_examples/` contain small format defects (`помарки`); Phase 1's 4-file baseline is preserved because those 4 are the cleanest. (User clarification, this session — feeds D-15.)
- "Нумерация источников зависит от нормоконтроля" — each normcontrol document (each university's) carries its own bibliography numbering policy. Phase 2 does NOT lock policy; Phase 5 will ingest the policy from the normcontrol PPTX/PDF and populate the profile JSON `numbering.bibliography.scope` field. (D-03 hook for this.)

</specifics>

<deferred>
## Deferred Ideas

- **Profile selection UX (CLI flag `--profile <path>` + UI picker)** → Phase 5 / Phase 6.
- **`extract-methodical-profile` CLI ingesting normcontrol PPTX/PDF** → Phase 5.
- **Hierarchical text-marker support (manual `1.1`, `1.1.1` prefixes without Word numbering)** → out of scope; Word numbering renders hierarchy in D-05.
- **`audit-regression` CLI gate on all 59 positive_examples** → Phase 4.
- **Heading signature extension (font+paragraph-format combined, direct vs inherited separation)** → Phase 3 (FIX-06, REQ-heading-style-signature).
- **DOCX writer custom-styles fix for `58.docx`/`59.docx` template-specific edge cases** → Phase 3 (FIX-04, REQ-fix-docx-generator-custom-styles).
- **UI changes around profile selection display** → Phase 6 (UI-05, REQ-ui-main-flow). Phase 2 only adds backend schema; UI hint logged here.
- **EN-locale bibliography titles (`references`, `bibliography`)** → not on roadmap; defer indefinitely until use case appears.

</deferred>

---

*Phase: 02-bibliography-list-semantics*
*Context gathered: 2026-05-12*
