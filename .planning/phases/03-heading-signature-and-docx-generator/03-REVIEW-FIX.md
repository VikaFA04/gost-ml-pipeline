---
phase: 03-heading-signature-and-docx-generator
fixed_at: 2026-05-13T00:00:00Z
review_path: .planning/phases/03-heading-signature-and-docx-generator/03-REVIEW.md
iteration: 1
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase 3: Code Review Fix Report

**Fixed at:** 2026-05-13
**Source review:** .planning/phases/03-heading-signature-and-docx-generator/03-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 2 (2 warnings; info findings out of scope per `--auto`)
- Fixed: 2 (1 already_fixed in HEAD, 1 applied this pass)
- Skipped: 0

## Fixed Issues

### WR-01: `apply_scalar_fix` writes `run.font.name = default_font_name` as a side effect of `bold` / `font_size_pt` fixes — risks overwriting inherited heading font

**Status:** already_fixed (pre-existing in HEAD, no action this iteration)

**Files modified:** `src/rules/rule_engine.py` (history)
**Commits:**
- TDD RED: `c0de4be` — test(03): RED — WR-01 invariant on D-06 heading autofix preserving inherited font_name
- GREEN: `d7b15d7` — fix(03): WR-01 — D-06 bold/font_size must not overwrite inherited font_name

**Applied fix (in HEAD):** Replaced the delegation from `apply_heading_scalar_fix` to `apply_scalar_fix` for the `bold` / `font_size` parameters with inline writes that mutate only `run.bold` / `run.font.size` and never touch `run.font.name`. The 6 `paragraph_format` params still delegate (where `apply_scalar_fix` never writes `run.font.name`). The returned `applied_fixes` for the font-size branch is `["font_size"]` (matching the `HEADING_SIG_FIELDS` key) instead of `["font_size_pt"]`, closing a latent gap in the D-07 invariant. Two regression tests pin the invariant: `test_heading_direct_bold_fix_preserves_inherited_font_name` and `test_heading_direct_font_size_fix_preserves_inherited_font_name`.

**Verification:** Both commits present in `git log` (verified via `git show --stat d7b15d7`). No re-application performed.

### WR-02: Empty-document fallback DataFrame schema omits `heading_format_signature` column

**Files modified:** `src/io/block_extractor.py`
**Commit:** `469be87`
**Applied fix:** Added `"heading_format_signature"` to the explicit column list in the `if df.empty:` fallback at `src/io/block_extractor.py:248-263`, so the empty-fallback DataFrame schema matches the populated-path schema. Downstream consumers (`apply_rules_to_paragraph`, the D-05/D-06 dispatcher at `rule_engine.py:1294`) already treat the column as optional via `row_data.get("heading_format_signature")`, so the change is schema-only with no behavior change on non-empty docs; it closes the latent inconsistency that would have silently failed the Plan 03-04 signature-presence assertion in `tests/test_positive_docx_regression.py:124` if the empty-fallback path were ever hit.

**Verification:**
- Tier 1: re-read lines 246-265 of `src/io/block_extractor.py`, confirmed `"heading_format_signature"` present as the last column entry and surrounding code intact.
- Tier 2: `python3 -c "import ast; ast.parse(...)"` → SYNTAX_OK.
- Regression: `python3 -m pytest tests/test_rule_engine.py tests/test_style_signatures.py tests/test_positive_docx_regression.py -q` → **66 passed in 7.79s**.

---

_Fixed: 2026-05-13_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
