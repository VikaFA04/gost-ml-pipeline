# Phase 3: Heading signature & DOCX generator - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning (with prerequisite ROADMAP/REQUIREMENTS edits — see <decisions> D-08)

<domain>
## Phase Boundary

Extend the heading style signature (font + paragraph format + flow-control flags) so the rule engine can check both font and paragraph-format Word parameters with explicit direct-vs-inherited separation. Inherited mismatches go to `review`; direct overrides on Heading-styled paragraphs are autofixed. Per-field heading rules; positive corpus stays `changed=0`.

In scope:
1. Extend `src/io/block_extractor.py` row dict with one new nested key `heading_format_signature` carrying ~17 fields (font name/size/bold/italic/underline/color/CAPS + alignment / first_line_indent_cm / left_indent_cm / right_indent_cm / space_before_pt / space_after_pt / line_spacing + keep_with_next / keep_lines_together / page_break_before / widow_control). Existing 5 flat keys (alignment, style, bold_ratio, list_type, list_level) stay untouched — zero ML schema churn.
2. Each signature field carries `{value, source: "direct"|"inherited"|"unset"}` so rule selectors can branch on source.
3. Two-pass resolver: read `paragraph.paragraph_format` / `run.font` directly (None = inherited), then walk `paragraph.style.base_style` chain to resolve effective inherited value.
4. Per-field heading rules in `src/rules/formatting_rules_v1.json`: `heading_font_name`, `heading_font_size`, `heading_alignment`, etc. One rule per signature field. Profile-driven `expected_value`.
5. Inherited-mismatch policy: route to `review` with `explanation: heading_inherited_mismatch:field=<name>,actual=<a>,expected=<e>`. Never autofix inherited values (Phase 1 D-004 — no silent rewrites).
6. Direct-mismatch policy: autofix the direct override (set to expected, or clear to None to fall back to style). `applied_fixes` lists the field name.
7. Hand-crafted `tests/fixtures/heading_minimal.docx` with 4 paragraphs: positive heading, wrong-intervals heading, wrong-font-params heading, inherited-mismatch heading. Phase 1/2 fixture pattern.
8. Positive-corpus regression gate (Phase 2's `tests/test_positive_docx_regression.py`) extended with heading-direct-fix invariant: zero `heading_*` autofixes on the GOST-decorated positive subset.

Out of scope for Phase 3:
- 58/59 practice-doc support (REQ-fix-docx-generator-custom-styles dropped — see D-08).
- Multi-profile selection UX (Phase 5).
- Methodical-profile ingest of heading rules (Phase 5 — `extract-methodical-profile`).
- Style-cascade WRITE (mutating `document.styles[Heading N]`) — too risky, never in this phase.
- TOC field-code regeneration (preserved, never touched).

</domain>

<decisions>
## Implementation Decisions

### Area 1 — Signature shape & storage
- **D-01:** **Hybrid schema.** Existing 5 flat extractor keys (`alignment`, `style`, `bold_ratio`, `list_type`, `list_level`) stay flat — zero churn on training/predict rows and the SVM feature pipeline. New heading-only fields land in a nested `heading_format_signature: {...}` key. Audit CSV serializes the nest as a JSON string column. Decision rationale: option 1 (one nested object for all format) would force a dataset migration; option 2 (17 flat columns) explodes the audit CSV and breaks every downstream test that asserts column count.
- **D-02:** **All three field categories ship in Phase 3 — no defer.**
  - Font params: `font_name, font_size, bold, italic, underline, color, caps`. (`caps` derived from text + `style.font.all_caps`.)
  - Paragraph scalars: `alignment, first_line_indent_cm, left_indent_cm, right_indent_cm, space_before_pt, space_after_pt, line_spacing`.
  - Flow flags: `keep_with_next, keep_lines_together, page_break_before, widow_control`.
  Matches ROADMAP Phase 3 success criterion 1 verbatim.

### Area 2 — Direct vs inherited resolution
- **D-03:** **Two-pass resolver.**
  - Pass 1 — direct: read `paragraph.paragraph_format.X` and `run.font.X` directly. `None` ⇒ inherited (FORMAT_FIX_PLAN root cause A semantics).
  - Pass 2 — inherited: walk `paragraph.style.base_style → base_style → ...` until attribute is non-None or chain ends. Pure python-docx; no lxml. Reuses the inheritance pattern Phase 1 used to fix root cause A.
  - For multi-run paragraphs: font params come from the first run with a non-None value; if all runs inherit, walk the cascade.
- **D-04:** **Per-field source tagging.** Every entry in `heading_format_signature` is `{value: <T>, source: "direct"|"inherited"|"unset"}`. Rule selectors decide differently per source (D-05 / D-06). Audit CSV preserves both fields when serializing.

### Area 3 — Inherited-Heading autofix policy
- **D-05:** **Inherited mismatch → review only.** When `source=inherited` AND `value != profile.expected_value`, set `status=review`, `explanation=heading_inherited_mismatch:field=<name>,actual=<a>,expected=<e>`. NEVER autofix. Editing `document.styles[Heading N]` is rejected (mutates ALL siblings — silent rewrite anti-pattern). Writing direct override is rejected (introduces direct formatting on a styled paragraph — Phase 1 root cause A).
- **D-06:** **Direct mismatch → autofix the direct override.** When `source=direct` AND `value != profile.expected_value`, set `paragraph.paragraph_format.X` (or `run.font.X`) to expected, OR clear to `None` to fall back to the style. `applied_fixes` includes the field name. This is exactly what Phase 1 root cause A fix said is safe: removing wrong direct overrides on styled paragraphs.
- **D-07:** **Reuse Phase 2 positive-corpus gate, extend with heading-direct-fix invariant.** Keep `tests/test_positive_docx_regression.py` Phase 2 assertion (no scalar/format autofix on non-bibliography paragraphs). Add: zero `heading_*` autofixes fire on the GOST-decorated positive subset. If Phase 3 heading code touches a positive heading, gate FAILS.

### Area 4 — 58/59 scope reduction + rule shape + fixtures
- **D-08:** **Drop REQ-fix-docx-generator-custom-styles from this milestone.** 58.docx and 59.docx are practice reports (отчёт по практике), not GOST coursework — they have no GOST decoration to begin with. The "spurious LEFT/bold/spacing edits" are the symptom of applying the GOST profile to a document type the profile doesn't cover, not a writer defect. Practice-doc support, if needed at all, belongs in Phase 5 (multi-profile selection + methodical-profile ingest of a `practice_report` profile). Phase 3 covers REQ-heading-style-signature only.
  **Prerequisite edits before plan-phase runs (must land first OR Wave 0 of Phase 3 plan):**
  - `.planning/REQUIREMENTS.md` — mark `REQ-fix-docx-generator-custom-styles` as deferred/v2 with rationale.
  - `.planning/ROADMAP.md` — Phase 3 success criterion 3 deleted (or restated to drop the 58/59 reference). Phase 3 requirements list reduced to `REQ-heading-style-signature`. Phase 1 success criterion 1 restated: positive subset is GOST-decorated docs only (1.docx, 4.docx, plus any other GOST-decorated positives discoverable in the corpus — researcher to enumerate during plan-phase).
  - `tests/test_positive_docx_regression.py` — `checked_files` reduced to GOST-decorated subset; 58.docx and 59.docx dropped.
- **D-09:** **Per-field heading rules in `formatting_rules_v1.json`.** One rule per signature field: `heading_font_name`, `heading_font_size`, `heading_alignment`, `heading_first_line_indent_cm`, `heading_left_indent_cm`, `heading_right_indent_cm`, `heading_space_before_pt`, `heading_space_after_pt`, `heading_line_spacing`, `heading_keep_with_next`, `heading_keep_lines_together`, `heading_page_break_before`, `heading_widow_control`, `heading_underline`, `heading_color`, `heading_caps`, `heading_bold`, `heading_italic`. Each rule's `parameter` maps 1:1 to the signature field. `applied_fixes` lists each field separately. Audit explainability max — matches Phase 1/2 rule pattern.
- **D-10:** **Hand-crafted `tests/fixtures/heading_minimal.docx`.** 4 paragraphs minimum: (1) positive Heading 1 with target signature — should produce zero fixes; (2) wrong-intervals heading — `space_before_pt`/`space_after_pt` direct override mismatch → autofix per D-06; (3) wrong-font-params heading — `font_size`/`bold` direct override mismatch → autofix; (4) inherited-mismatch heading — Heading 1 with style-cascade values different from profile → review per D-05. Fixture builder script `tests/fixtures/_build_heading_minimal.py` (Phase 1/2 pattern). No 58/59 dependency.

### Claude's Discretion
- Exact JSON shape of `heading_format_signature` entries — `{value, source}` dict literal vs `{v, s}` short keys vs tuple. Plan-phase decides; researcher prefers verbose keys for audit-CSV readability.
- Internal helper naming (`_extract_heading_format_signature`, `_resolve_inherited_value`, `_compare_heading_signature_to_profile`).
- Exact `expected_value` JSON shape per heading rule — researcher reads `gost_7_32_2017.json` profile's heading section (if exists) and proposes; `apply_scalar_fix` already handles per-field expected.
- Whether the inherited-mismatch `explanation` includes the cascade chain (`heading_inherited_mismatch:field=font_size,actual=12,expected=14,cascade=Heading_1<-Normal`) or just `field=,actual=,expected=`. Plan-phase decides based on audit-CSV column width budget.
- Whether `heading_caps` rule uses `style.font.all_caps` flag OR derived `text == text.upper()` heuristic. Researcher decides after inspecting real positive heading samples.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & success criteria
- `.planning/ROADMAP.md` §"Phase 3: Heading signature & DOCX generator" — phase goal, depends-on (Phase 1), success criteria 1–4. **Note: criterion 3 + the `REQ-fix-docx-generator-custom-styles` row will be edited per D-08 before plan-phase runs.**
- `.planning/REQUIREMENTS.md` REQ-heading-style-signature (HEADING_AND_NORMCONTROL Block B). **REQ-fix-docx-generator-custom-styles to be marked deferred per D-08.**

### Project-level
- `.planning/PROJECT.md` <decisions> — D-002 (rule layer mandatory), D-004 (safe-only autocorrection: no silent rewrites of correct content). D-004 is the load-bearing decision behind D-05 (no autofix on inherited mismatch).
- `.planning/intel/decisions.md` D-001…D-007.
- `.planning/intel/constraints.md` C-NFR-EXPLAINABILITY (per-field rules in D-09).
- `.planning/intel/context.md` §"HEADING_AND_NORMCONTROL Block B" — original heading-rule defect catalog and 6 steps (extractor extension, regression fixtures, direct-vs-inherited separation, style-first fix, positive-corpus safety, UI explanation). All 6 are folded into D-01..D-07 above.

### Phase 1/2 carry-forward
- `.planning/phases/01-engine-guardrails-cohesion-audit/01-CONTEXT.md` — Phase 1 decisions (`classify_style`, `style_guard_block:` explanation pattern, root cause A semantics for None=inherited).
- `.planning/phases/01-engine-guardrails-cohesion-audit/01-VERIFICATION.md` — what Phase 1 actually shipped.
- `.planning/phases/02-bibliography-list-semantics/02-CONTEXT.md` D-13 — profile-driven scalars; rule layer respects field absence (no forced direct values). Same philosophy applied to heading rules in D-06.
- `.planning/phases/02-bibliography-list-semantics/02-VERIFICATION.md` — Phase 2 positive-baseline relaxation rationale (which D-07 extends).
- `src/rules/style_signatures.py` `classify_style`, `HEADING_STYLE_RE`, `paragraph_has_heading_style`. D-03 reuses the heading-name detection.

### Defect catalog
- `.planning/FORMAT_FIX_PLAN.md` "Root cause A" — `compare_scalar(None, expected)` returns False → direct rewrite of inherited value. D-03 / D-05 / D-06 are the fix shape for heading-specific application.
- `.planning/HEADING_AND_NORMCONTROL_PLAN.md` Block B — original 6-step heading plan.

### Source code (read before modifying)
- `src/io/block_extractor.py` `extract_paragraph_block` (line 126-147) — extends row dict with `heading_format_signature` per D-01.
- `src/rules/style_signatures.py` — `classify_style` reused; new helpers `_resolve_inherited_value` / `_extract_heading_format_signature` likely land here (researcher decides exact module).
- `src/rules/rule_engine.py` — `apply_rules_to_paragraph` selects `heading_*` rules; per-field rules dispatch via existing `apply_scalar_fix`. New autofix-vs-review branch points read `row_data["heading_format_signature"][field]["source"]`.
- `src/rules/formatting_rules_v1.json` — adds ~18 `heading_*` rules per D-09.
- `src/rules/profiles/gost_7_32_2017.json` — must carry the heading section (likely under `labels.title_section.style_profile` and `labels.title_subsection.style_profile`); researcher confirms exact path.
- `src/generate/docx_writer.py` + `src/generate/docx_styles.py` + `src/rules/docx_style_profile.py` — Phase 3 does NOT modify the writer for 58/59; per D-08 the writer change is descoped. Heading rule fixes happen in `src/generate/inplace_formatter.py` audit/format path, not docx_writer.
- `src/evaluation/format_regression_audit.py` `audits_to_frame` — `after_diff_rate` column the D-07 gate reads.

### Test corpus
- `positive_examples/{1,4}.docx` — confirmed GOST-decorated. Researcher must enumerate any other GOST-decorated docs in `positive_examples/` to widen the positive subset before plan-phase.
- `tests/test_positive_docx_regression.py` — Phase 2-relaxed; D-07 / D-08 require dropping 58/59 from `checked_files` and adding heading-direct-fix invariant.
- `tests/test_negative_corpus_diff_rate.py` — D-15 gate from Phase 2; must continue to pass.
- `tests/fixtures/heading_minimal.docx` (NEW) + `tests/fixtures/_build_heading_minimal.py` (NEW) — D-10.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/rules/style_signatures.py::classify_style` (Phase 1) — heading detection by style name. Phase 3 reads inside paragraphs only when `classify_style == "heading"`.
- `src/rules/rule_engine.py::apply_scalar_fix` — Phase 1/2 helper that handles per-parameter compare + autofix; per-field heading rules in D-09 dispatch through it.
- `style_guard_block:` explanation pattern (Phase 1) and `ambiguous_list_marker_no_numId` pattern (Phase 2) — D-05 mirrors them with `heading_inherited_mismatch:`.
- `src/rules/profile_loader.py` profile loading + Phase 2 D-03/D-11 helpers (`get_list_detection_thresholds`, `get_bibliography_numbering_scope`) — same pattern for new `get_heading_signature_target(profile, level)` helper.
- `tests/fixtures/_build_bibliography_minimal.py` (Phase 2) — pattern reference for D-10's `_build_heading_minimal.py`.

### Established Patterns
- `None` in `paragraph_format.X` and `run.font.X` means inherited — never autofix directly per Phase 1 root cause A.
- Postprocess attaches semantic indices (e.g. `bibliography_section_index`) to row dict; rule layer reads them — D-04 source tagging follows the same shape but lives nested.
- Each rule = one `parameter` + `expected_value`; `applied_fixes` lists per-field tags — keep for D-09.

### Integration Points
- `src/io/block_extractor.py::extract_paragraph_block` returns the row dict that flows into predictions CSV → postprocess → rule engine → audit CSV. Adding a new key affects every downstream reader; predictions CSV serialization should preserve the dict as JSON (researcher confirms `pandas.to_csv` handles via `default=str` or explicit `json.dumps`).
- `src/generate/inplace_formatter.py::audit_or_format_docx` is where heading rules fire; per-field heading rule selection happens through `apply_rules_to_paragraph`'s rule-loop.
- Audit CSV column for `heading_format_signature` is new; verify Phase 6 Streamlit UI doesn't break on extra column (probably fine — UI shows known columns).

</code_context>

<specifics>
## Specific Ideas

- D-08 conversation: user clarified that 58/59 are practice reports (отчёт по практике), not GOST-decorated coursework. The "spurious LEFT/bold/spacing edits" on 58/59 (FORMAT_FIX_PLAN Этап 8) was the symptom of applying GOST rules to non-GOST documents, not a docx_writer bug. Captured as project memory `scope_drop_58_59.md` so future phases don't re-open this.
- Heading regression fixture takes a builder script (Phase 1/2 pattern) — not committed binary if avoidable, generated from Python in `_build_heading_minimal.py`.

</specifics>

<deferred>
## Deferred Ideas

- **REQ-fix-docx-generator-custom-styles** — moves to v2 / Phase 5. If Phase 5 ingests a `practice_report` profile via methodical-profile, practice-doc support emerges naturally; otherwise the requirement stays deferred.
- **Heading TOC integration** — when heading text changes (none in Phase 3, but Phase 5 might), TOC field codes need refresh. Not in scope here.
- **Multi-level heading rules** (Heading 1 vs Heading 2 vs Heading 3 with different signatures) — Phase 3 ships per-field rules generic across heading levels using `paragraph_style_class == "heading"`. If profile carries level-specific targets (`heading_1.font_size = 14`, `heading_2.font_size = 13`), researcher decides whether to expose `level` in rule selector or keep one rule per parameter and let `expected_value` resolve from profile by level. Lean: keep generic, level-resolution lives in `profile_loader`.
- **Color check** in headings — D-02 includes `color` field. If positive headings vary widely in color (some templates use blue), the rule may be too aggressive — researcher confirms by sampling positive corpus before locking the rule's `expected_value`.

</deferred>

---

*Phase: 03-heading-signature-and-docx-generator*
*Context gathered: 2026-05-13*
