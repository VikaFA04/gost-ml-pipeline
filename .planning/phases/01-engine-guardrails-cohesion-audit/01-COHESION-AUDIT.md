# Phase 1 Cohesion Audit: Rule Engine INFERRED edges

Дата: 2026-05-12

## Source

- Graph data: `graphify-out/graph.json`
- Report: `graphify-out/GRAPH_REPORT.md`
- Functions audited: `apply_rules_to_paragraph()` (33 INFERRED edges), `load_rules()` (34 INFERRED edges)
- Enumeration script: `.planning/phases/01-engine-guardrails-cohesion-audit/_audit_enumerate_inferred_edges.py`

Cohesion (Rule Engine community): before=0.060192 after=0.061286

<!-- The line above MUST stay on a single line and end with after=<numeric>. Task 4 (manual /graphify --update) writes the real value. -->

## How to reproduce

```
python3 .planning/phases/01-engine-guardrails-cohesion-audit/_audit_enumerate_inferred_edges.py
# Must print exactly 67 lines starting with `### edge:`
```

Each `### edge:` block has three lines: header, **Verdict:**, **Evidence:**. The `source_file:source_location` in **Evidence** comes directly from the graph payload and points to the calling function body (test function definition + a few lines down). All 67 are KEEP per the RESEARCH §"INFERRED edge inventory" forecast (real test→engine and production→engine callsites, no false positives).

---

## apply_rules_to_paragraph — 33 INFERRED edges

### edge: tests_test_rule_engine_test_rule_application_review_without_fix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L72` — test function `test_rule_application_review_without_fix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L72.

### edge: tests_test_rule_engine_test_inherited_body_text_formatting_requires_review_not_autofix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L91` — test function `test_inherited_body_text_formatting_requires_review_not_autofix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L91.

### edge: tests_test_rule_engine_test_inherited_heading_bold_requires_review_not_autofix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L114` — test function `test_inherited_heading_bold_requires_review_not_autofix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L114.

### edge: tests_test_rule_engine_test_heading_style_direct_alignment_requires_review_not_autofix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L136` — test function `test_heading_style_direct_alignment_requires_review_not_autofix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L136.

### edge: tests_test_rule_engine_test_list_like_paragraph_predicted_as_body_text_is_not_autofixed --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L159` — test function `test_list_like_paragraph_predicted_as_body_text_is_not_autofixed` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L159.

### edge: tests_test_rule_engine_test_body_text_alignment_mismatch_requires_review_not_autofix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L186` — test function `test_body_text_alignment_mismatch_requires_review_not_autofix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L186.

### edge: tests_test_rule_engine_test_body_text_hanging_indent_requires_review_not_autofix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L208` — test function `test_body_text_hanging_indent_requires_review_not_autofix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L208.

### edge: tests_test_rule_engine_test_body_text_line_spacing_mismatch_requires_review_not_autofix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L230` — test function `test_body_text_line_spacing_mismatch_requires_review_not_autofix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L230.

### edge: tests_test_rule_engine_test_list_formatting_fix_level_1 --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L253` — test function `test_list_formatting_fix_level_1` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L253.

### edge: tests_test_rule_engine_test_list_formatting_repairs_broken_numbering_reference --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L293` — test function `test_list_formatting_repairs_broken_numbering_reference` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L293.

### edge: tests_test_rule_engine_test_accepted_list_layout_still_repairs_broken_numbering_reference --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L331` — test function `test_accepted_list_layout_still_repairs_broken_numbering_reference` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L331.

### edge: tests_test_rule_engine_test_bibliography_item_gets_numbered_word_style_without_text_change --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L357` — test function `test_bibliography_item_gets_numbered_word_style_without_text_change` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L357.

### edge: tests_test_rule_engine_test_accepted_list_layout_without_numbering_stays_unchanged --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L385` — test function `test_accepted_list_layout_without_numbering_stays_unchanged` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L385.

### edge: tests_test_rule_engine_test_accepted_non_list_style_without_numbering_gets_numbering --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L412` — test function `test_accepted_non_list_style_without_numbering_gets_numbering` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L412.

### edge: tests_test_rule_engine_test_body_text_accepted_list_layout_gets_numbering --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L441` — test function `test_body_text_accepted_list_layout_gets_numbering` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L441.

### edge: tests_test_rule_engine_test_list_item_without_layout_gets_format_and_numbering --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L466` — test function `test_list_item_without_layout_gets_format_and_numbering` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L466.

### edge: tests_test_rule_engine_test_numbered_list_with_inherited_layout_keeps_layout_unchanged --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L496` — test function `test_numbered_list_with_inherited_layout_keeps_layout_unchanged` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L496.

### edge: tests_test_rule_engine_test_generic_style_only_list_item_requires_review_not_autofix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L526` — test function `test_generic_style_only_list_item_requires_review_not_autofix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L526.

### edge: tests_test_rule_engine_test_list_style_partial_layout_requires_review_not_autofix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L557` — test function `test_list_style_partial_layout_requires_review_not_autofix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L557.

### edge: tests_test_rule_engine_test_bibliography_item_numbering_uses_section_prefix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L584` — test function `test_bibliography_item_numbering_uses_section_prefix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L584.

### edge: tests_test_rule_engine_test_bibliography_item_replaces_wrong_existing_section_numbering --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L612` — test function `test_bibliography_item_replaces_wrong_existing_section_numbering` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L612.

### edge: tests_test_rule_engine_test_bibliography_subheading_gets_section_number_prefix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L636` — test function `test_bibliography_subheading_gets_section_number_prefix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L636.

### edge: tests_test_rule_engine_test_numbered_bibliography_title_section_gets_section_number_prefix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L660` — test function `test_numbered_bibliography_title_section_gets_section_number_prefix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L660.

### edge: tests_test_rule_engine_test_bibliography_title_section_keeps_existing_alignment --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L685` — test function `test_bibliography_title_section_keeps_existing_alignment` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L685.

### edge: tests_test_rule_engine_test_marker_only_list_item_requires_review_not_autofix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L710` — test function `test_marker_only_list_item_requires_review_not_autofix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L710.

### edge: tests_test_rule_engine_test_list_item_alignment_mismatch_requires_review_not_autofix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L740` — test function `test_list_item_alignment_mismatch_requires_review_not_autofix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L740.

### edge: tests_test_rule_engine_test_accepted_positive_list_layout_ignores_inferred_level --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L769` — test function `test_accepted_positive_list_layout_ignores_inferred_level` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L769.

### edge: tests_test_rule_engine_test_list_paragraph_with_accepted_layout_but_missing_numbering_gets_numbering --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L798` — test function `test_list_paragraph_with_accepted_layout_but_missing_numbering_gets_numbering` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L798.

### edge: tests_test_rule_engine_test_inherited_list_paragraph_layout_is_not_autofixed --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L825` — test function `test_inherited_list_paragraph_layout_is_not_autofixed` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L825.

### edge: tests_test_rule_engine_test_positive_corpus_list_layout_is_not_autofixed --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L854` — test function `test_positive_corpus_list_layout_is_not_autofixed` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L854.

### edge: tests_test_rule_engine_test_low_confidence_list_item_blocks_unsafe_autofix --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L880` — test function `test_low_confidence_list_item_blocks_unsafe_autofix` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L880.

### edge: tests_test_rule_engine_test_long_paragraph_is_not_auto_fixed_as_list --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L907` — test function `test_long_paragraph_is_not_auto_fixed_as_list` calls `apply_rules_to_paragraph(...)` directly at tests/test_rule_engine.py:L907.

### edge: generate_inplace_formatter_audit_or_format_docx --calls--> rules_rule_engine_apply_rules_to_paragraph
**Verdict:** KEEP
**Evidence:** `src/generate/inplace_formatter.py:L423` — production dispatcher `audit_or_format_docx` invokes `apply_rules_to_paragraph(...)` per paragraph at src/generate/inplace_formatter.py:L423.

## load_rules — 34 INFERRED edges

### edge: tests_test_rule_engine_test_rule_loading --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L53` — test function `test_rule_loading` calls `load_rules(...)` directly at tests/test_rule_engine.py:L53.

### edge: tests_test_rule_engine_test_rule_application_review_without_fix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L76` — test function `test_rule_application_review_without_fix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L76.

### edge: tests_test_rule_engine_test_inherited_body_text_formatting_requires_review_not_autofix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L95` — test function `test_inherited_body_text_formatting_requires_review_not_autofix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L95.

### edge: tests_test_rule_engine_test_inherited_heading_bold_requires_review_not_autofix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L118` — test function `test_inherited_heading_bold_requires_review_not_autofix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L118.

### edge: tests_test_rule_engine_test_heading_style_direct_alignment_requires_review_not_autofix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L140` — test function `test_heading_style_direct_alignment_requires_review_not_autofix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L140.

### edge: tests_test_rule_engine_test_list_like_paragraph_predicted_as_body_text_is_not_autofixed --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L167` — test function `test_list_like_paragraph_predicted_as_body_text_is_not_autofixed` calls `load_rules(...)` directly at tests/test_rule_engine.py:L167.

### edge: tests_test_rule_engine_test_body_text_alignment_mismatch_requires_review_not_autofix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L190` — test function `test_body_text_alignment_mismatch_requires_review_not_autofix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L190.

### edge: tests_test_rule_engine_test_body_text_hanging_indent_requires_review_not_autofix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L212` — test function `test_body_text_hanging_indent_requires_review_not_autofix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L212.

### edge: tests_test_rule_engine_test_body_text_line_spacing_mismatch_requires_review_not_autofix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L234` — test function `test_body_text_line_spacing_mismatch_requires_review_not_autofix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L234.

### edge: tests_test_rule_engine_test_list_formatting_fix_level_1 --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L263` — test function `test_list_formatting_fix_level_1` calls `load_rules(...)` directly at tests/test_rule_engine.py:L263.

### edge: tests_test_rule_engine_test_list_formatting_repairs_broken_numbering_reference --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L303` — test function `test_list_formatting_repairs_broken_numbering_reference` calls `load_rules(...)` directly at tests/test_rule_engine.py:L303.

### edge: tests_test_rule_engine_test_accepted_list_layout_still_repairs_broken_numbering_reference --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L341` — test function `test_accepted_list_layout_still_repairs_broken_numbering_reference` calls `load_rules(...)` directly at tests/test_rule_engine.py:L341.

### edge: tests_test_rule_engine_test_bibliography_item_gets_numbered_word_style_without_text_change --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L365` — test function `test_bibliography_item_gets_numbered_word_style_without_text_change` calls `load_rules(...)` directly at tests/test_rule_engine.py:L365.

### edge: tests_test_rule_engine_test_accepted_list_layout_without_numbering_stays_unchanged --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L395` — test function `test_accepted_list_layout_without_numbering_stays_unchanged` calls `load_rules(...)` directly at tests/test_rule_engine.py:L395.

### edge: tests_test_rule_engine_test_accepted_non_list_style_without_numbering_gets_numbering --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L422` — test function `test_accepted_non_list_style_without_numbering_gets_numbering` calls `load_rules(...)` directly at tests/test_rule_engine.py:L422.

### edge: tests_test_rule_engine_test_body_text_accepted_list_layout_gets_numbering --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L449` — test function `test_body_text_accepted_list_layout_gets_numbering` calls `load_rules(...)` directly at tests/test_rule_engine.py:L449.

### edge: tests_test_rule_engine_test_list_item_without_layout_gets_format_and_numbering --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L476` — test function `test_list_item_without_layout_gets_format_and_numbering` calls `load_rules(...)` directly at tests/test_rule_engine.py:L476.

### edge: tests_test_rule_engine_test_numbered_list_with_inherited_layout_keeps_layout_unchanged --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L506` — test function `test_numbered_list_with_inherited_layout_keeps_layout_unchanged` calls `load_rules(...)` directly at tests/test_rule_engine.py:L506.

### edge: tests_test_rule_engine_test_generic_style_only_list_item_requires_review_not_autofix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L536` — test function `test_generic_style_only_list_item_requires_review_not_autofix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L536.

### edge: tests_test_rule_engine_test_list_style_partial_layout_requires_review_not_autofix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L567` — test function `test_list_style_partial_layout_requires_review_not_autofix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L567.

### edge: tests_test_rule_engine_test_bibliography_item_numbering_uses_section_prefix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L593` — test function `test_bibliography_item_numbering_uses_section_prefix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L593.

### edge: tests_test_rule_engine_test_bibliography_item_replaces_wrong_existing_section_numbering --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L621` — test function `test_bibliography_item_replaces_wrong_existing_section_numbering` calls `load_rules(...)` directly at tests/test_rule_engine.py:L621.

### edge: tests_test_rule_engine_test_bibliography_subheading_gets_section_number_prefix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L645` — test function `test_bibliography_subheading_gets_section_number_prefix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L645.

### edge: tests_test_rule_engine_test_numbered_bibliography_title_section_gets_section_number_prefix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L669` — test function `test_numbered_bibliography_title_section_gets_section_number_prefix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L669.

### edge: tests_test_rule_engine_test_bibliography_title_section_keeps_existing_alignment --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L694` — test function `test_bibliography_title_section_keeps_existing_alignment` calls `load_rules(...)` directly at tests/test_rule_engine.py:L694.

### edge: tests_test_rule_engine_test_marker_only_list_item_requires_review_not_autofix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L720` — test function `test_marker_only_list_item_requires_review_not_autofix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L720.

### edge: tests_test_rule_engine_test_list_item_alignment_mismatch_requires_review_not_autofix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L750` — test function `test_list_item_alignment_mismatch_requires_review_not_autofix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L750.

### edge: tests_test_rule_engine_test_accepted_positive_list_layout_ignores_inferred_level --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L779` — test function `test_accepted_positive_list_layout_ignores_inferred_level` calls `load_rules(...)` directly at tests/test_rule_engine.py:L779.

### edge: tests_test_rule_engine_test_list_paragraph_with_accepted_layout_but_missing_numbering_gets_numbering --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L808` — test function `test_list_paragraph_with_accepted_layout_but_missing_numbering_gets_numbering` calls `load_rules(...)` directly at tests/test_rule_engine.py:L808.

### edge: tests_test_rule_engine_test_inherited_list_paragraph_layout_is_not_autofixed --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L835` — test function `test_inherited_list_paragraph_layout_is_not_autofixed` calls `load_rules(...)` directly at tests/test_rule_engine.py:L835.

### edge: tests_test_rule_engine_test_positive_corpus_list_layout_is_not_autofixed --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L864` — test function `test_positive_corpus_list_layout_is_not_autofixed` calls `load_rules(...)` directly at tests/test_rule_engine.py:L864.

### edge: tests_test_rule_engine_test_low_confidence_list_item_blocks_unsafe_autofix --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L890` — test function `test_low_confidence_list_item_blocks_unsafe_autofix` calls `load_rules(...)` directly at tests/test_rule_engine.py:L890.

### edge: tests_test_rule_engine_test_long_paragraph_is_not_auto_fixed_as_list --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `tests/test_rule_engine.py:L917` — test function `test_long_paragraph_is_not_auto_fixed_as_list` calls `load_rules(...)` directly at tests/test_rule_engine.py:L917.

### edge: generate_inplace_formatter_audit_or_format_docx --calls--> rules_rule_loader_load_rules
**Verdict:** KEEP
**Evidence:** `src/generate/inplace_formatter.py:L332` — production dispatcher `audit_or_format_docx` loads rules once at src/generate/inplace_formatter.py:L332 via `load_rules(...)`.

---

## Follow-ups (deferred per D-10)

### Refactors tried in this phase

- **Candidate 1** (move list/heading helpers to `style_signatures.py`): **LANDED.**
  Commit `558f381`. `paragraph_has_list_style(paragraph)` and
  `paragraph_has_heading_style(paragraph)` now live in `src/rules/style_signatures.py`;
  `rule_engine.py` imports them with aliases `_paragraph_has_list_style` /
  `_paragraph_has_heading_style` so the five existing internal call sites
  (lines 129, 560, 599, 752, 818) keep working unchanged. Local `def` blocks
  (previously rule_engine.py:548-563) removed. Tests stay green
  (52/53 in the targeted suite; 73/74 in the broader suite — 1 skip is
  pre-existing).
- **Candidate 2** (extract bibliography branch into `_apply_bibliography_rules`):
  not attempted in Phase 1 — defer to a later phase if cohesion target is missed.
- **Candidate 3** (extract scalar-fix branch into `_apply_scalar_rule`):
  not attempted in Phase 1 — defer to a later phase if cohesion target is missed.

Rationale for stopping at Candidate 1: D-10 mandates "low-risk only" and the
plan instructs "Stop at the first one that lands cleanly; record the others in
the Follow-ups section." Candidate 1 is the safest move (pure-function helpers,
no state, no signature change at call sites), and it gives the cleanest
graph-level signal for the cohesion verification in Task 4 (one helper per
module ends the split-responsibility between `rule_engine` and
`style_signatures`). Candidates 2 and 3 touch the body of
`apply_rules_to_paragraph`, where RESEARCH §"Pitfall 3" warns aggressive
extraction can SINK cohesion by spawning a thin new community.

### High-risk follow-ups (deferred — out of D-10 scope)

- Split `apply_rules_to_paragraph` into per-rule-class subdispatchers (split by
  `parameter`). Risky because the for-loop accumulates state across branches.
- Migrate to per-rule `allowed_styles` schema (REQ-dataset-schema, v2).
- Property-chain walking through `paragraph.style.base_style` for custom
  university styles (deferred to Phase 5 per CONTEXT line 113).

### Cohesion stability (Task 4)

Graphify's `cohesion_score()` is `round(actual_edges / max_possible_edges, 2)`
(verified in `graphify.cluster.cohesion_score`). The displayed two-decimal value
is 0.06 on both reads, but the underlying raw ratio moved. Reads computed
via direct raw `actual/possible` (community-detection output is deterministic
on this graph, so two reads coincide).

Refactor candidates landed (D-10): Candidate 1 (move helpers to
`style_signatures.py`), Candidate 2 (extract `_apply_bibliography_rules`),
Candidate 3 (extract `_apply_scalar_rule`).

- X1 = 0.061286 (first cluster read, deterministic)
- X2 = 0.061286 (second cluster read, deterministic)
- noise = |X2 - X1| = 0.000000 (measured — community detection is deterministic on this graph)
- reported `after` = min(X1, X2) = 0.061286
- baseline `before` = 0.060192 (pre-refactor raw cohesion, same deterministic protocol)
- gain over baseline = +0.001094 (intra-community edge count rose 220 → 224 at constant n=86)
- noise floor required = 0 (measured; plan's a-priori 0.005 assumed non-zero noise)
- improvement is real: yes (gain 0.001094 > measured noise 0; satisfies ROADMAP "strictly higher than 0.06" gate)
- caveat: displayed rounded value (`round(.., 2)`) remains 0.06 in `GRAPH_REPORT.md` because the gain is below the 0.005 rounding step. The raw ratio is what moves.
