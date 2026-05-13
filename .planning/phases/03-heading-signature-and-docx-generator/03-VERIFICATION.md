---
phase: 03-heading-signature-and-docx-generator
verified: 2026-05-13T16:44:53Z
status: passed
score: 3/3 ROADMAP Success Criteria verified; REQ-heading-style-signature SATISFIED
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 3: Heading Signature & DOCX Generator — Verification Report

**Phase Goal:** Heading rules check both font and paragraph-format Word parameters with explicit direct-vs-inherited separation. Inherited mismatches go to `review`; direct overrides on Heading-styled paragraphs are autofixed. Per-field heading rules.
**Verified:** 2026-05-13T16:44:53Z
**Status:** passed
**Re-verification:** No — initial verification.

---

## Goal Achievement

### Observable Truths (from ROADMAP §Phase 3 Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Extractor's heading signature includes font name/size/bold/italic/underline/color/CAPS + alignment / first-line indent / left+right indent / space_before+after / line_spacing / keep_with_next / keep_lines_together / page_break_before / widow control (18 fields). | VERIFIED | `HEADING_SIG_FIELDS` frozenset at `src/rules/rule_engine.py:29-34` has 18 elements. `_extract_heading_format_signature` at `src/rules/style_signatures.py:191-210` returns dict with exactly those 18 keys. `test_heading_signature_key_present` PASSED — asserts all 18 keys present with `{value, source}` shape. |
| 2 | For paragraphs whose Heading style is inherited from `Heading 1/2/3`, autofix is blocked — mismatch routes to `review`. Direct overrides on Heading-styled paragraphs are autofixed. | VERIFIED | Blanket guard at old `rule_engine.py:998-1004` REMOVED (`grep _paragraph_has_heading_style(paragraph):` returns 0). Per-field dispatcher at `rule_engine.py:1307-1357` routes by `source`: `inherited` → `manual_review_required=True` with `heading_inherited_mismatch:` explanation (line 1339-1344); `direct` → `apply_heading_scalar_fix(...)` (line 1352-1356). Tests `test_heading_inherited_mismatch_routes_to_review`, `test_heading_direct_mismatch_routes_to_autofix`, `test_inherited_heading_bold_requires_review_not_autofix` all PASS. |
| 3 | GOST positive subset stays `changed=0` for any heading rule (D-07 invariant); negative heading fixtures move toward target signatures with no text changes; TOC/list structure stable. | VERIFIED | `tests/test_positive_docx_regression.py` PASSES with D-07 `heading_changed.empty` + signature-presence assertions (lines 88-130). `tests/test_negative_corpus_diff_rate.py` PASSES (mean ≤ 0.4781). `tests/fixtures/heading_minimal.docx` end-to-end: p2/p3 → changed with direct-override autofixes, p4 → review with `heading_inherited_mismatch:` (recorded in 03-04-SUMMARY.md lines 142-147). |

**Score:** 3/3 Success Criteria verified.

---

### Required Artifacts (must_haves from 4 plans)

#### Plan 03-01 (Wave 0 RED — tests + fixture)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/fixtures/_build_heading_minimal.py` | Builder, no src/ imports | VERIFIED | File exists. `grep '^from src\.'` returns 0. Idempotent per builder docstring. |
| `tests/fixtures/heading_minimal.docx` | 4 paragraphs, all Heading 1, D-10 layout | VERIFIED | 36773 bytes, 4 paragraphs, exact texts confirmed in 03-01-SUMMARY.md line 91. |
| `tests/test_style_signatures.py` | 4 heading signature tests | VERIFIED | `test_heading_signature_key_present`, `_direct_none_is_inherited`, `_direct_override_detected`, `_cascade_walk` — all 4 present at lines 98-158, all PASS. |
| `tests/test_rule_engine.py` | 8 routing tests + WR-01 invariants | VERIFIED | All 8 D-05/D-06/D-09/D-10 tests present (lines 1363-1545). `test_inherited_heading_bold_requires_review_not_autofix` preserved at line 111. 2 new WR-01 invariant tests at lines 1547, 1579. Old `test_heading_style_direct_alignment_requires_review_not_autofix` removed. All PASS. |
| `tests/test_positive_docx_regression.py` | D-07 invariant + appendix narrowing + signature-presence | VERIFIED | `_has_heading_fix` (line 102), `_is_appendix_heading` (line 57), `heading_changed.empty` (line 113), `predictions_df.columns` (line 124), `heading_rows.empty` (line 130). All PASS. |

#### Plan 03-02 (Wave 1 GREEN — extractor)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/rules/style_signatures.py` | `_resolve_inherited_value` + `_extract_heading_format_signature` (18 fields) | VERIFIED | Both functions exist (lines 68, 88). 18-key return dict verified at lines 191-210. Length conversion (.pt/.cm) at lines 125, 146-152, 165-189. Lazy ALIGNMENT_MAP import at line 93. |
| `src/io/block_extractor.py` | `heading_format_signature` column, lazy via classify_style=='heading' | VERIFIED — minor info | Import line 16, lazy guard line 157, try/except line 161-163. **Info:** empty-DataFrame columns list at line 249 does NOT include `heading_format_signature` (Plan 03-02 acceptance criterion 6 minor deviation); does not affect runtime — only triggers on docs with zero paragraphs. |

#### Plan 03-03 (Wave 2 GREEN — routing + rules)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/rules/rule_engine.py` | Per-field dispatcher + apply_heading_scalar_fix; blanket guard removed | VERIFIED | `HEADING_SIG_FIELDS` at line 29 (18 elements). `apply_heading_scalar_fix` at line 793. Per-field dispatcher at line 1307-1357. Blanket guard `_paragraph_has_heading_style(paragraph):` REMOVED (grep returns 0). `heading_inherited_mismatch:field=` explanation pattern at line 1342. Bibliography guard at line 1349-1350 preserved. WR-01 fix: bold/font_size now inline writes (lines 831-840), no longer delegate to apply_scalar_fix (which would overwrite font_name). |
| `src/rules/formatting_rules_v1.json` | 20 heading_* rules (3 existing + 17 new); level-split; null+autocorrect=false for 10 rules | VERIFIED | 20 heading_* IDs total. 10 rules with `expected_value=null` + `autocorrect=false` (load+skip): `heading_caps`, `heading_color`, `heading_font_name`, `heading_italic`, `heading_keep_lines_together`, `heading_keep_with_next`, `heading_page_break_before`, `heading_right_indent_cm`, `heading_underline`, `heading_widow_control`. Level-split confirmed: `heading_section_font_size` (18.0), `heading_subsection_font_size` (16.0), `heading_section_space_before_pt` (0.0), `heading_subsection_space_before_pt` (15.0). |

#### Plan 03-04 (Wave 3 — regression gate close-out)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/test_positive_docx_regression.py` | Signature-presence assertion + appendix-narrowed D-07 | VERIFIED | Lines 53-60: `_is_appendix_heading` with rationale comment citing "Phase 3 user decision 2026-05-13". Line 81 + 111: applied in both non_bib_changed and heading_changed filters. Lines 118-130: signature-presence assertion. |
| `tests/test_negative_corpus_diff_rate.py` | No change required; still passes | VERIFIED | No file modifications. Test PASSES (mean ≤ 0.4781 preserved). |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `block_extractor.extract_paragraph_block` | `style_signatures._extract_heading_format_signature` | `from src.rules.style_signatures import classify_style, _extract_heading_format_signature` (line 16) + call at line 158 inside `if classify_style(paragraph) == "heading"` (line 157) | WIRED | Top-level import + lazy call inside classify_style guard. Smoke check: `python -c "from src.io.block_extractor import extract_paragraph_block; ..."` succeeds. |
| `style_signatures._extract_heading_format_signature` | `ALIGNMENT_MAP` from block_extractor | Lazy import inside function body (line 93) to break circular dep | WIRED | No top-level import; verified by `grep -c "^from src\.io\.block_extractor" src/rules/style_signatures.py` returns 0. |
| `rule_engine.apply_rules_to_paragraph` | `row_data["heading_format_signature"]` (JSON string from extractor) | `json.loads` with NaN-guard at lines 1310-1318 | WIRED | Handles str (line 1310), NaN-float (line 1315), and dict-passthrough for tests (line 1317). |
| `rule_engine` D-06 direct dispatcher | `apply_heading_scalar_fix` | Direct call at line 1355 | WIRED | Function at line 793. Tests confirm bold and font_size autofix succeeds without clobbering inherited font.name (WR-01 invariants). |
| `formatting_rules_v1.json` `parameter` field | `_extract_heading_format_signature` key names | Dispatcher `sig.get(parameter, ...)` at line 1321 | WIRED | Rule names match signature keys (`font_size`, not `font_size_pt`; `keep_lines_together`, not `keep_together`). |
| Bibliography guard in D-06 | Phase 2 carry-forward | `if bibliography_section_index is not None: manual_review_required = True` at line 1349-1350 | WIRED | CLAUDE.md invariant: "Не применяй обычные heading scalar autofix к библиографическим section headings." |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|----|
| `_extract_heading_format_signature` | `paragraph` (`docx.text.paragraph.Paragraph`) | python-docx live document object — actual Word XML | Yes — 18 fields each pulled from `paragraph.paragraph_format.X`, `run.font.X`, or `_resolve_inherited_value(style.base_style)` cascade walk. End-to-end empirically confirmed by heading_minimal.docx output in 03-04-SUMMARY.md: actual values like `actual=14.0,expected=18.0` for font_size on Heading 1. | FLOWING |
| `extract_paragraph_block` `row['heading_format_signature']` | JSON string from extractor | Live extraction at line 158, fallback None at line 151 + 163 | Yes — positive corpus test asserts at least one row has non-NaN signature column starting with `{` (lines 128-130 of test). | FLOWING |
| `apply_rules_to_paragraph` `sig` | row_data dict from CSV round-trip | json.loads of column value at line 1312 | Yes — tests confirm direct vs inherited routing produces different outcomes (test_heading_direct_mismatch_routes_to_autofix vs test_heading_inherited_mismatch_routes_to_review). | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All Phase 3 symbols importable | `python -c "from src.rules.rule_engine import HEADING_SIG_FIELDS, apply_heading_scalar_fix, apply_rules_to_paragraph; from src.rules.style_signatures import _extract_heading_format_signature, _resolve_inherited_value; from src.io.block_extractor import extract_paragraph_block"` | exit 0; `HEADING_SIG_FIELDS: 18; All symbols importable: True` | PASS |
| Blanket guard removed | `grep -c "_paragraph_has_heading_style(paragraph):" src/rules/rule_engine.py` | 0 | PASS |
| 18 HEADING_SIG_FIELDS | `python -c "from src.rules.rule_engine import HEADING_SIG_FIELDS; print(len(HEADING_SIG_FIELDS))"` | 18 | PASS |
| 20 heading_* rules in JSON | `python -c "import json; rules=json.load(open('src/rules/formatting_rules_v1.json'))['rules']; print(len([r for r in rules if r['id'].startswith('heading_')]))"` | 20 | PASS |
| 10 load+skip rules (expected=null, autocorrect=false) | Same JSON inspection | 10: `heading_caps, heading_color, heading_font_name, heading_italic, heading_keep_lines_together, heading_keep_with_next, heading_page_break_before, heading_right_indent_cm, heading_underline, heading_widow_control` | PASS |
| WR-01 invariant tests pass | `pytest tests/test_rule_engine.py::test_heading_direct_bold_fix_preserves_inherited_font_name tests/test_rule_engine.py::test_heading_direct_font_size_fix_preserves_inherited_font_name -v` | 2 passed in 0.64s | PASS |
| Full Phase 3 test sweep | `pytest tests/test_rule_engine.py tests/test_style_signatures.py tests/test_positive_docx_regression.py tests/test_negative_corpus_diff_rate.py tests/test_postprocess_rules.py tests/test_profile_loader.py -q` | **84 passed, 1 skipped in 86.64s** | PASS |
| WR-01 fix commit present | `git log --oneline | grep d7b15d7` | `d7b15d7 fix(03): WR-01 — D-06 bold/font_size must not overwrite inherited font_name` | PASS |
| D-07 narrowing rationale | `grep -B1 -A4 '_is_appendix_heading' tests/test_positive_docx_regression.py` | Comment block at lines 53-56 cites "Phase 3 user decision 2026-05-13" | PASS |

---

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|---------------|-------------|--------|----------|
| REQ-heading-style-signature | 03-01, 03-02, 03-03, 03-04 | Heading style signature extended with 18 fields (font + paragraph format + flow flags), direct-vs-inherited separation. Positive corpus stays changed=0; negative heading fixtures move toward target with no text changes. | SATISFIED | `_extract_heading_format_signature` returns 18 fields with `{value, source}` shape; per-field D-05/D-06 routing in rule_engine; 20 heading_* rules in JSON; positive corpus test passes with appendix-narrowed D-07 invariant; negative corpus diff-rate gate preserved. REQUIREMENTS.md line 106 marked `[x]`. |
| REQ-fix-docx-generator-custom-styles | (none — deferred) | 58/59 practice-doc support. | N/A — DEFERRED to v2 per Phase 3 D-08 (2026-05-13). Confirmed in REQUIREMENTS.md line 88, ROADMAP.md scope-reduction note. | N/A |

**Orphaned requirements:** None. The only REQ ID mapped to Phase 3 in REQUIREMENTS.md is `REQ-heading-style-signature` — every plan's `requirements:` frontmatter lists it. `REQ-fix-docx-generator-custom-styles` is explicitly deferred and correctly absent from all 4 plans' requirements lists.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/io/block_extractor.py` | 248-260 | Empty-DataFrame columns list does not include `heading_format_signature` (Plan 03-02 acceptance criterion 6 minor miss) | Info | Pure maintenance — runtime only hits this branch when DOCX has zero paragraphs. Schema consumers downstream of empty DOCX would see NaN if they request the column; pandas concat handles non-empty case correctly. Cosmetic, not blocking. |
| `tests/test_positive_docx_regression.py` | 53-60 | `_is_appendix_heading` helper text-pattern matching | Info | Documented as narrowed D-07 invariant per user decision 2026-05-13. Rationale comment explicit and cites root cause (RESEARCH.md corpus sampling miss). Not a stub — intentional regression-gate narrowing. |
| `src/rules/rule_engine.py` | 869-872 | `color` parameter in `apply_heading_scalar_fix` returns `[]` (no-op) | Info | Defensive — `heading_color` rule has `autocorrect=false` so dispatcher should never call this branch. Comment explains intent. Not a stub, intentional defense in depth. |
| `src/rules/formatting_rules_v1.json` | 10 rules | `expected_value=null` + `autocorrect=false` (load+skip) | Info | Open Question 2 resolution: rules without GOST-defined targets are loaded for schema-completeness (the dispatcher skips them via `if expected is None: continue` at rule_engine.py line 1330-1331). Carry-forward to Phase 5. Documented in 03-03-SUMMARY.md, 03-04-SUMMARY.md, and Plan 03-03 frontmatter. Not a stub — intentional contract per resolved Open Question. |

No Blocker or Warning anti-patterns. All 4 Info findings are documented intentional decisions.

---

### Human Verification Required

None. Phase 3 deliverables are entirely programmatically verifiable:

- **No UI changes:** Phase 3 modifies rule engine + extractor + rule JSON + tests. No Streamlit / visual surface area.
- **No real-time behavior:** All paths are synchronous read/transform/write on DOCX bytes.
- **No external services:** Purely local processing.
- **No edge cases requiring eye-on-output:** All behavior pinned by 12 RED→GREEN tests + 2 WR-01 invariant tests + positive-corpus regression gate + negative-corpus diff-rate gate.
- **End-to-end behavior verified empirically:** `heading_minimal.docx` end-to-end output recorded in 03-04-SUMMARY.md lines 142-147 matches D-10 spec exactly (p1 review, p2/p3 changed, p4 review with `heading_inherited_mismatch`).

---

### Gaps Summary

**No gaps.** All 3 ROADMAP Success Criteria are empirically verified. REQ-heading-style-signature is delivered. The WR-01 follow-up (uncovered in 03-REVIEW.md after Plan 03-04 close-out) was fixed at commit `d7b15d7` with two new invariant tests at `c0de4be` (RED) — both invariants pass.

The single Info-level deviation (empty-DataFrame columns list in `block_extractor.py` missing the new column) is a cosmetic maintenance miss with no behavioral consequence — every test in the Phase 3 acceptance suite passes.

---

## Phase 3 Verification Summary

- **All 3 ROADMAP Success Criteria:** VERIFIED (SC-1, SC-2, SC-3)
- **REQ-heading-style-signature:** SATISFIED (every plan declares it; implementation complete; checkbox `[x]` in REQUIREMENTS.md)
- **REQ-fix-docx-generator-custom-styles:** correctly DEFERRED to v2 (Phase 5) per Phase 3 D-08 user decision 2026-05-13
- **Test sweep:** 84 passed, 1 skipped in 86.64s
- **Production code:** `_extract_heading_format_signature` + `_resolve_inherited_value` (style_signatures.py), `heading_format_signature` column wiring (block_extractor.py), per-field D-05/D-06 dispatcher + `apply_heading_scalar_fix` + `HEADING_SIG_FIELDS` (rule_engine.py), 20 heading_* rules incl. level-split + 10 null-target load+skip (formatting_rules_v1.json) — all present and wired
- **WR-01 fix:** landed at commit d7b15d7 with TDD RED at c0de4be; two invariant tests pass
- **D-07 narrowing:** appendix-headings excluded with rationale comment at lines 53-56 of test_positive_docx_regression.py, citing Phase 3 user decision 2026-05-13
- **Open Question 2:** 10 heading_* rules carry `expected_value=null` + `autocorrect=false` (load+skip); documented for Phase 5 fill via per-profile heading_signature dict
- **Blanket heading guard:** REMOVED (grep returns 0)
- **Bibliography guard:** PRESERVED in D-06 direct-mismatch branch (CLAUDE.md invariant)
- **No regressions:** Phase 1 and Phase 2 test suites stay green; negative-corpus diff-rate ≤ 0.4781 preserved

---

_Verified: 2026-05-13T16:44:53Z_
_Verifier: Claude (gsd-verifier)_
