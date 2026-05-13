---
plan: 02-03-multilevel-numbering-green
phase: 02-bibliography-list-semantics
status: complete-with-deviations
completed_at: 2026-05-13
tasks_completed: 2
commits: 2
---

# Plan 02-03 — Multilevel Numbering GREEN — Summary

D-05/D-06/D-07 wired into `src/rules/rule_engine.py`. 6 of 8 Wave 0 RED tests
this plan was supposed to GREEN are now GREEN; 2 integration tests + the Phase
1 positive-corpus baseline reveal a routing/scope deviation that Plan 02-04
must resolve.

## Commits

- `666f888` feat(02-03): D-05 multilevel abstract + per-section lvlOverride helpers
- `c4d67ac` feat(02-03): D-06 coerce + D-07 idempotency + D-05 ilvl=1 in rule_engine

## Code Changes — `src/rules/rule_engine.py`

**Module-level state (3 declarations):**
- `_BIBLIOGRAPHY_NUM_IDS` cache — semantics shifted: key `(id(document.part), section_index)` (was `id(numbering_root)` — Pitfall 1 fix).
- `_SEEDED_DOCS: set[int]` — tracks which documents have had their numbering.xml scanned.
- `_BIBLIOGRAPHY_ABSTRACTS: dict[int, str]` — shared multilevel abstractNumId per doc.

**5 new functions:**

| Function | Purpose |
|---|---|
| `_create_bibliography_multilevel_abstract` | Emit 2-level multilevel `w:abstractNum` with lvl-1 lvlText `%1.%2.` (D-05). |
| `_create_bibliography_num_with_section_override` | Emit `w:num` carrying TWO `lvlOverride` (ilvl=0 startOverride=section_index, ilvl=1 startOverride=1) (D-05). |
| `_document_cache_key` | Stable `id(paragraph.part.document.part)` — fixes Pitfall 1 cross-doc id() collision (D-07). |
| `_bibliography_valid_numId` | Returns True iff numId exists AND its abstract is multilevel with lvl-1 lvlText `%1.%2.` (D-06 + Open Q3). |
| `_seed_bibliography_num_ids_from_doc` | One-time-per-document scan that walks body, identifies bib subsections via Heading style or fallback regex, seeds `_BIBLIOGRAPHY_NUM_IDS` with first valid numId per section (D-07). |

**2 functions rewritten:**

| Function | Change |
|---|---|
| `_get_bibliography_num_id` | First-call seed → cache lookup → if miss, allocate shared abstract (cached per doc) + fresh per-subsection w:num. |
| `bibliography_numbering_matches` | New idempotency oracle: True iff numId is valid (D-06) AND `lvlOverride[ilvl=0].startOverride == section_index` AND `<w:ilvl>` is "1". |

**1 function modified:**

- `apply_bibliography_numbering` — sets `<w:ilvl w:val="1"/>` (was "0"); appends `numbering:coerced_to_numId=N` when overwriting a different pre-existing numId.

## Test Changes

- `tests/test_rule_engine.py::test_bibliography_item_numbering_uses_section_prefix` — updated assertion from old `w:val="2.%1"` to new `w:val="%1.%2."` (legacy test pinned the singleLevel format that D-05 explicitly supersedes).
- `tests/test_rule_engine.py::test_bibliography_item_replaces_wrong_existing_section_numbering` — same update from `w:val="1.%1"` to `w:val="%1.%2."`.
- `tests/test_bibliography_phase2.py::_bibliography_item_rows` helper — Plan 02-01's RED tests pre-supposed CSV columns `postprocessed_label` / `predicted_label`, but the audit pipeline emits `label`. Helper now reads `label` first; old names kept as fallbacks for cross-version test runs.

## Wave 0 RED → GREEN

| Test | Decision | Status |
|---|---|---|
| `test_bibliography_multilevel_renders_section_dot_entry` | D-05 abstract | **GREEN** |
| `test_bibliography_num_with_section_override_carries_lvlOverride` | D-05 num | **GREEN** |
| `test_bibliography_subsection_coerces_to_first_valid_numId` | D-06 coercion tag | **GREEN** |
| `test_bibliography_idempotent_on_rerun` | D-07 idempotency | **GREEN** |
| `test_negative_4_bibliography_single_numId` | D-14 negative | **GREEN** |
| `test_negative_3_bibliography_coerces_mixed_numIds` | D-06 + D-14 negative | **GREEN** |
| `test_bibliography_apply_uses_ilvl_1` | D-05 ilvl=1 (integration) | **RED** — see deviation 1 below |
| `test_bibliography_minimal_docx_single_numId_per_subsection` | D-14 hand-crafted | **RED** — see deviation 1 below |

## Deviations / Open Items for Plan 02-04 + Verifier

1. **Postprocess routing of no-numPr bibliography_item entries.** On
   `bibliography_minimal.docx`, only the entry that originally carried
   `numId=1` reaches `apply_bibliography_numbering`. The two entries that
   start without `numPr` are routed to `review` instead of `changed`, so the
   final DOCX has numIds `[None, '11', None]` for subsection 1. D-05/D-14
   integration tests require all 3 entries to share one numId. Root cause is
   in `inplace_formatter` / `postprocess_rules` rule selection for the
   `bibliography_item` label when `numPr` is absent — Wave 2 only changed
   `rule_engine.py` numbering allocator/applier, not the routing that selects
   which paragraphs receive it. Plan 02-04 should either (a) extend the
   bibliography rule to fire on no-`numPr` entries that are postprocess-tagged
   `bibliography_item`, or (b) document this as a known D-14 gap.

2. **Phase 1 positive baseline regression — `positive_examples/1.docx`.**
   The plan acceptance criterion stated "files 1/4/58/59 have NO bibliography
   sections, so the bibliography path doesn't fire on them" — this is **false
   for `1.docx`**, which contains a Heading-1 bibliography with two
   subsections numbered with legacy singleLevel numId. After Wave 2:
   - 4 `bibliography_item` rows show `numbering:coerced_to_numId=12` (D-06 firing on legacy singleLevel),
   - 2 `bibliography_title` rows show `bibliography_section_prefix` writes,
   - `summary["changed"]` jumps from 0 → 6.

   This is the unavoidable consequence of D-06's contract that legacy
   singleLevel numIds are invalid. Plan 02-04 (or the verifier) needs to
   decide whether (a) the positive baseline asserts must relax for
   bibliography-bearing docs, or (b) D-06 should additionally honor "looks
   reasonable" singleLevel as valid (which would defeat the gate's purpose).
   Surfaced for user decision.

## Phase 1 Baseline (rule_engine + style_signatures)

- `tests/test_rule_engine.py` — **GREEN after legacy update** (47 of 47 in this file).
- `tests/test_style_signatures.py` — **GREEN** (untouched by Wave 2).
- `tests/test_postprocess_rules.py` — 1 D-04 test (`test_bibliography_subsection_detected_by_heading_style`) still RED; pre-existing Wave 1 gap, not introduced by Wave 2.
- `tests/test_positive_docx_regression.py::test_positive_docx_examples_are_not_autofixed` — fails on `1.docx` only; see deviation 2.

## Notes / Workflow Deviations

- Plan was executed inline by the orchestrator after two consecutive subagent
  attempts failed: (a) the worktree-isolated agent's runtime denied the Bash
  tool mid-task, and (b) a fresh in-place agent reached Task 1 then again hit
  the Bash permission denial. Task 1 commit (`666f888`) was made by the
  orchestrator using the staged-but-uncommitted edits the agent had produced;
  Task 2 was rewritten + committed inline.
- `python` is not on PATH; system `/usr/bin/python3` was used for all test
  runs. ML-stack tests (`test_application_service`, `test_baseline_inferencer`,
  …) were not exercised — system python lacks `sklearn`/`joblib`/`streamlit`.
