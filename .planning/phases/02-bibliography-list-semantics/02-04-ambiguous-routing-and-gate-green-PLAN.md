---
phase: 02-bibliography-list-semantics
plan: 04
type: execute
wave: 3
depends_on: [01, 02, 03]
files_modified:
  - src/rules/rule_engine.py
  - src/rules/formatting_rules_v1.json
autonomous: true
requirements:
  - REQ-list-conservative-handling
requirements_addressed:
  - REQ-list-conservative-handling
tags:
  - bibliography
  - routing
  - profile
  - regression-gate
  - phase-2

must_haves:
  truths:
    - "D-09: When `apply_rules_to_paragraph` sees label='body_text' on a Normal-styled paragraph whose text matches a list marker and which has NO Word numPr, it returns status='review' with explanation='ambiguous_list_marker_no_numId' and no fixes applied."
    - "D-10: When the same body_text paragraph has NO list marker AND no numPr, the D-09 branch does NOT fire and the existing body_text path runs unchanged."
    - "D-13: `formatting_rules_v1.json` bibliography_item_format.expected_value is stripped to {'style_name': 'List Number'} — first_line_indent_cm and left_indent_cm scalars REMOVED. `apply_bibliography_format` therefore no longer writes alignment / indents via the rule path; profile JSON `labels.bibliography_item.style_profile.*` becomes the authoritative source for those scalars."
    - "D-11: `MAX_FALLBACK_LIST_WORDS` and `MAX_FALLBACK_LIST_CHARS` module-level constants are DELETED from `src/rules/rule_engine.py`. `_is_long_plain_paragraph` accepts `max_words` and `max_chars` keyword arguments with default values 40/300 — callers may override via the profile-loader helper or pass the defaults (Pitfall 5: backwards-compatible threading)."
    - "D-15: `tests/test_negative_corpus_diff_rate.py` is GREEN — the 4-doc subset's mean after_diff_rate ≤ 0.4781. If the subset's mean post-Phase-2 exceeds 0.4781, Plan 04 must either tighten the implementation (most likely D-09 too greedy) OR widen the test to the full 17-doc corpus (matching Phase 1's manual baseline 0.4737 ≤ 0.4781)."
    - "Phase 1 positive-corpus baseline preserved: `audit-docx --apply-safe` on `positive_examples/{1,4,58,59}.docx` keeps changed=0."
    - "ALL Wave 0 RED tests for Phase 2 are GREEN: ROADMAP success criteria 1-4 met."
  artifacts:
    - path: "src/rules/rule_engine.py"
      provides: "D-09 ambiguous-list review branch + D-11 constant deletion + _is_long_plain_paragraph threading"
      contains: "ambiguous_list_marker_no_numId"
    - path: "src/rules/formatting_rules_v1.json"
      provides: "Stripped bibliography_item_format.expected_value (D-13)"
      contains: "\"style_name\": \"List Number\""
  key_links:
    - from: "src/rules/rule_engine.apply_rules_to_paragraph"
      to: "src/rules/rule_engine._paragraph_has_list_marker + _paragraph_has_numbering"
      via: "D-09 branch immediately after Phase 1 style guard"
      pattern: "ambiguous_list_marker_no_numId"
    - from: "src/rules/rule_engine._is_long_plain_paragraph"
      to: "callers (assess_list_auto_fix_safety, is_list_like_paragraph)"
      via: "max_words, max_chars keyword arguments"
      pattern: "max_words=|max_chars="
    - from: "src/rules/formatting_rules_v1.json bibliography_item_format"
      to: "src/rules/rule_engine.apply_bibliography_format"
      via: "stripped expected_value → scalar fields absent → apply_bibliography_format skips them"
      pattern: "\\\"first_line_indent_cm\\\"|\\\"left_indent_cm\\\""
---

<objective>
Wave 3 GREEN — close the remaining decisions and verify the regression gate.

This plan covers:
- D-09 (ambiguous-list review routing) in `apply_rules_to_paragraph`.
- D-10 (no-marker no-numId body_text stays body_text) — sanity-only; no production code needed (Phase 1 style guard already handles this; this plan verifies the D-09 branch does NOT over-fire on the negative case).
- D-13 (safe-fix scope split) — strip `first_line_indent_cm` and `left_indent_cm` from `formatting_rules_v1.json:bibliography_item_format.expected_value`. Per researcher Open Question 4: the profile JSON is the authoritative source of scalar truth.
- D-11 (delete module-level constants `MAX_FALLBACK_LIST_WORDS` / `MAX_FALLBACK_LIST_CHARS`) — thread thresholds through `_is_long_plain_paragraph` with kwarg defaults so non-profile callers keep working. **CRITICAL: do this AS ONE TASK with the JSON change to avoid a broken intermediate state per phase_specific_constraints.**
- D-15 (regression gate) — verify `tests/test_negative_corpus_diff_rate.py` passes on the post-Phase-2 codebase. If the subset's mean diff-rate exceeds 0.4781, diagnose and remediate.

Why this set is one plan: D-09 and D-10 share the routing branch; D-11 deletion is a one-task coordinated change with `_is_long_plain_paragraph`; D-13 JSON strip is one-line; D-15 is a verification gate, not a code change. Total ~3 tasks. The deletion of `MAX_FALLBACK_LIST_*` MUST land in this plan because Plan 02 added the helpers + JSON; deleting the code constants in the same plan as that wiring would have created a broken state if Plan 02's profile read path wasn't wired through `_is_long_plain_paragraph`. Plan 02 explicitly deferred the deletion here.

Output: 2 source files modified; final ~3 Wave 0 RED tests turn GREEN; ROADMAP success criteria 1-4 all met.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@.planning/phases/02-bibliography-list-semantics/02-CONTEXT.md
@.planning/phases/02-bibliography-list-semantics/02-RESEARCH.md
@.planning/phases/02-bibliography-list-semantics/02-PATTERNS.md
@.planning/phases/02-bibliography-list-semantics/02-02-postprocess-and-profile-green-PLAN.md
@.planning/phases/02-bibliography-list-semantics/02-03-multilevel-numbering-green-PLAN.md
@src/rules/rule_engine.py
@src/rules/formatting_rules_v1.json
@tests/test_bibliography_phase2.py
@tests/test_negative_corpus_diff_rate.py

<interfaces>
<!-- D-09 branch contract (verbatim from RESEARCH.md Example E) -->

`src/rules/rule_engine.apply_rules_to_paragraph` MUST gain a new branch IMMEDIATELY AFTER the Phase 1 style guard at line 798, BEFORE `current_profile = get_current_paragraph_profile(paragraph)` at line 800. The branch reuses existing helpers `_paragraph_has_list_marker` (line 542) and `_paragraph_has_numbering` (line 534) — NO new helpers needed:

```python
text = str(row_data.get("text", "") or paragraph.text or "").strip()
if (
    label == "body_text"
    and paragraph_style_class == "body"
    and _paragraph_has_list_marker(text)
    and not _paragraph_has_numbering(paragraph)
):
    return {
        "status": "review",
        "violated_rules": [],
        "applied_fixes": [],
        "suggested_fixes": [],
        "suggested_rule_ids": [],
        "manual_review_required": True,
        "blocked_unsafe_autofix": False,
        "unsafe_auto_fix_reason": "",
        "explanation": "ambiguous_list_marker_no_numId",
    }
```

The explanation string is the BARE token `ambiguous_list_marker_no_numId` (no `<category>:<detail>` colon-suffix — no sub-detail today; Phase 5 may add one).

<!-- D-11 constant deletion + _is_long_plain_paragraph signature change -->

Current state (line 30-31 + 546-547):
```python
MAX_FALLBACK_LIST_WORDS = 40
MAX_FALLBACK_LIST_CHARS = 300

def _is_long_plain_paragraph(text: str) -> bool:
    return len(text) >= MAX_FALLBACK_LIST_CHARS or len(text.split()) >= MAX_FALLBACK_LIST_WORDS
```

Target state:
```python
# (MAX_FALLBACK_LIST_WORDS and MAX_FALLBACK_LIST_CHARS DELETED)

def _is_long_plain_paragraph(text: str, *, max_words: int = 40, max_chars: int = 300) -> bool:
    return len(text) >= max_chars or len(text.split()) >= max_words
```

Callers `assess_list_auto_fix_safety` (line 559) and `is_list_like_paragraph` (line 599) currently call `_is_long_plain_paragraph(text)` — they continue working unchanged because of kwarg defaults. **Phase 2 explicitly does NOT thread `profile` through every list-like caller** — that's `is_list_like_paragraph` + `assess_list_auto_fix_safety`, which would require updating every single callsite of those functions (most of `apply_rules_to_paragraph`). Per researcher Pitfall 5: defer profile-driven override until a real consumer needs it. Phase 2 ships kwarg-with-default so existing tests pass; future phases can plumb the profile through if/when needed.

<!-- D-13 JSON strip (verbatim, from researcher Open Question 4) -->

Current `src/rules/formatting_rules_v1.json` lines 118-130:
```json
{
  "id": "bibliography_item_format",
  "applicable_labels": ["bibliography_item"],
  "parameter": "bibliography_format",
  "expected_value": {
    "style_name": "List Number",
    "first_line_indent_cm": -1.0,
    "left_indent_cm": 2.25
  },
  ...
}
```

Target state — REMOVE the two scalar fields, leave style_name:
```json
{
  "id": "bibliography_item_format",
  "applicable_labels": ["bibliography_item"],
  "parameter": "bibliography_format",
  "expected_value": {
    "style_name": "List Number"
  },
  ...
}
```

Rationale (Open Question 4): D-13 says "if profile has field → apply, else skip". The current rule expected_value carries scalars unconditionally, defeating the profile-driven design. Stripping them at the rule level + leaving the profile JSON to carry overrides realizes D-13 cleanly.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add D-09 ambiguous-list review branch + delete MAX_FALLBACK_LIST_* constants + thread thresholds through _is_long_plain_paragraph</name>
  <files>src/rules/rule_engine.py</files>
  <read_first>
    - src/rules/rule_engine.py lines 26-43 (existing module-level constants — MAX_FALLBACK_LIST_WORDS at 30, MAX_FALLBACK_LIST_CHARS at 31)
    - src/rules/rule_engine.py lines 525-600 (the long-plain-paragraph helper, marker helper, has-numbering helper, list-safety assessor)
    - src/rules/rule_engine.py lines 771-800 (apply_rules_to_paragraph head + Phase 1 style guard at 786-798)
    - .planning/phases/02-bibliography-list-semantics/02-RESEARCH.md §"Example E" lines 384-405 (D-09 branch verbatim)
    - .planning/phases/02-bibliography-list-semantics/02-PATTERNS.md §"src/rules/rule_engine.py — D-09 ambiguous-list review branch (NEW)" lines 213-271
    - .planning/phases/02-bibliography-list-semantics/02-PATTERNS.md §"src/rules/rule_engine.py — D-11 profile threading + remove MAX_FALLBACK_LIST_*" lines 273-312
    - tests/test_bibliography_phase2.py::test_ambiguous_list_marker_no_numId_routes_to_review (RED — D-09)
    - tests/test_bibliography_phase2.py::test_long_body_text_without_marker_stays_body_text (sanity — D-10 must not over-fire)
  </read_first>
  <behavior>
    - D-09 branch inserted at the right position; uses ONLY existing helpers `_paragraph_has_list_marker` and `_paragraph_has_numbering`.
    - D-10 verified by the existing `test_long_body_text_without_marker_stays_body_text` (no production change needed — the existing branch's guards prevent firing without a marker).
    - `MAX_FALLBACK_LIST_WORDS` and `MAX_FALLBACK_LIST_CHARS` deleted from module level.
    - `_is_long_plain_paragraph` accepts `max_words=40, max_chars=300` keyword arguments; behavior unchanged for callers that don't override.
    - Existing callers continue to work because they pass no kwargs (kwarg defaults preserve the 40/300 thresholds).
    - Phase 1 baseline preserved.
  </behavior>
  <action>
    **Sub-step 1a — Delete `MAX_FALLBACK_LIST_*` constants.** Find lines 30-31 in `src/rules/rule_engine.py`:

    ```python
    MAX_FALLBACK_LIST_WORDS = 40
    MAX_FALLBACK_LIST_CHARS = 300
    ```

    Remove both lines. Before deleting, verify no other file references these constants:

    ```bash
    grep -rn "MAX_FALLBACK_LIST_WORDS\|MAX_FALLBACK_LIST_CHARS" src/ tests/ scripts/
    ```

    If the grep returns ANY hit outside `src/rules/rule_engine.py` itself, STOP and add the same kwarg-threading pattern to that consumer before deleting. The expected result is hits ONLY in `src/rules/rule_engine.py` (the definition + the consumer in `_is_long_plain_paragraph`).

    **Sub-step 1b — Update `_is_long_plain_paragraph` signature.** Find the function at line 546:

    ```python
    def _is_long_plain_paragraph(text: str) -> bool:
        return len(text) >= MAX_FALLBACK_LIST_CHARS or len(text.split()) >= MAX_FALLBACK_LIST_WORDS
    ```

    Replace with:

    ```python
    def _is_long_plain_paragraph(text: str, *, max_words: int = 40, max_chars: int = 300) -> bool:
        """Default thresholds 40/300 match the historical MAX_FALLBACK_LIST_* constants
        (deleted in Phase 2). Profile-driven callers may pass `max_words` and `max_chars`
        from `src.rules.profile_loader.get_list_detection_thresholds(profile)`.

        Pitfall 5: keep keyword arguments with defaults — existing callers are NOT
        re-threaded in Phase 2 because the existing call surface in `apply_rules_to_paragraph`
        doesn't carry a profile dict yet.
        """
        return len(text) >= max_chars or len(text.split()) >= max_words
    ```

    Do NOT update `assess_list_auto_fix_safety` or `is_list_like_paragraph` callers — they pass no kwargs, so the defaults handle them.

    **Sub-step 1c — Add D-09 branch in `apply_rules_to_paragraph`.** Find the Phase 1 style guard at lines 786-798 (the block returning `style_guard_block:`). IMMEDIATELY AFTER that block's closing `}` (line 798) and BEFORE `current_profile = get_current_paragraph_profile(paragraph)` (line 800), insert:

    ```python
        # D-09 — ambiguous-list review routing.
        # body_text label + Normal style + visible list marker (1) /  – etc.) + NO Word
        # numPr → review with explanation 'ambiguous_list_marker_no_numId'. Mirrors the
        # Phase 1 style_guard_block: pattern (review-result dict shape; routing decision
        # before rule loop).
        if label == "body_text" and paragraph_style_class == "body":
            text_for_marker = str(row_data.get("text", "") or paragraph.text or "").strip()
            if _paragraph_has_list_marker(text_for_marker) and not _paragraph_has_numbering(paragraph):
                return {
                    "status": "review",
                    "violated_rules": [],
                    "applied_fixes": [],
                    "suggested_fixes": [],
                    "suggested_rule_ids": [],
                    "manual_review_required": True,
                    "blocked_unsafe_autofix": False,
                    "unsafe_auto_fix_reason": "",
                    "explanation": "ambiguous_list_marker_no_numId",
                }
    ```

    Critical: the branch is INSIDE the same function, AFTER the style guard's `}`. Indentation must match (the Phase 1 guard is one level inside `def apply_rules_to_paragraph`). Confirm with `python -m py_compile src/rules/rule_engine.py` after the insert.
  </action>
  <verify>
    <automated>grep -c "^MAX_FALLBACK_LIST_WORDS" src/rules/rule_engine.py && grep -c "^MAX_FALLBACK_LIST_CHARS" src/rules/rule_engine.py; echo "expect both 0" && grep -c "ambiguous_list_marker_no_numId" src/rules/rule_engine.py && grep -rn "MAX_FALLBACK_LIST_WORDS\|MAX_FALLBACK_LIST_CHARS" src/ tests/ scripts/ 2>/dev/null; echo "expect no hits anywhere" && python -m pytest tests/test_bibliography_phase2.py::test_ambiguous_list_marker_no_numId_routes_to_review tests/test_bibliography_phase2.py::test_long_body_text_without_marker_stays_body_text -x -q 2>&1 | tail -15</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c "^MAX_FALLBACK_LIST_WORDS" src/rules/rule_engine.py` returns `0` (constant deleted).
    - `grep -c "^MAX_FALLBACK_LIST_CHARS" src/rules/rule_engine.py` returns `0` (constant deleted).
    - `grep -rn "MAX_FALLBACK_LIST" src/ tests/ scripts/ 2>/dev/null | wc -l` returns `0` (no hits remain anywhere).
    - `grep -c "ambiguous_list_marker_no_numId" src/rules/rule_engine.py` returns `≥1` (the explanation string).
    - `grep -F "def _is_long_plain_paragraph(text: str, *, max_words: int = 40, max_chars: int = 300)" src/rules/rule_engine.py` returns `1` line.
    - `python -m py_compile src/rules/rule_engine.py` exits 0 (no syntax error from the branch insertion).
    - `python -m pytest tests/test_bibliography_phase2.py::test_ambiguous_list_marker_no_numId_routes_to_review -x -q` exits 0 — D-09 GREEN.
    - `python -m pytest tests/test_bibliography_phase2.py::test_long_body_text_without_marker_stays_body_text -x -q` exits 0 — D-10 sanity preserved.
    - `python -m pytest tests/ -x -q -k "not test_negative_corpus_diff_rate_phase2_baseline and not bibliography_format_skips_alignment"` exits 0 — Phase 1 + everything except the two tasks-2/3 gates passes.
    - Phase 1 positive corpus test `python -m pytest tests/test_positive_docx_regression.py -x -q` GREEN — D-09 branch does NOT over-fire on existing positive_examples.
  </acceptance_criteria>
  <done>D-09 routing live; MAX_FALLBACK_LIST_* constants removed; _is_long_plain_paragraph signature backwards-compatible via kwarg defaults; D-09 + D-10 tests GREEN; Phase 1 baseline preserved.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: D-13 strip first_line_indent_cm and left_indent_cm from bibliography_item_format rule</name>
  <files>src/rules/formatting_rules_v1.json</files>
  <read_first>
    - src/rules/formatting_rules_v1.json lines 115-132 (bibliography_item_format rule)
    - .planning/phases/02-bibliography-list-semantics/02-RESEARCH.md §"Open Question 4" lines 583-586 (researcher recommendation to STRIP)
    - .planning/phases/02-bibliography-list-semantics/02-PATTERNS.md §"src/rules/rule_engine.py — D-13 conditional bibliography format scalars" lines 314-339
    - src/rules/rule_engine.py apply_bibliography_format (lines 230-265 — VERIFY the scalar_fields loop already skips fields not in config; no code change needed, just JSON)
    - src/rules/profiles/gost_7_32_2017.json (CONFIRM the profile JSON carries `labels.bibliography_item.style_profile.{first_line_indent_cm, left_indent_cm}` so the profile path remains a fallback if Phase 5 wants to wire it; if not, the SUMMARY notes Phase 5 owns the profile-level scalars)
    - tests/test_bibliography_phase2.py::test_bibliography_format_skips_alignment_when_profile_omits (RED — D-13)
  </read_first>
  <behavior>
    - `src/rules/formatting_rules_v1.json` `bibliography_item_format.expected_value` is reduced to `{"style_name": "List Number"}`.
    - No production code change needed: `apply_bibliography_format` already skips fields not present in `config` (existing `if field not in config: continue` loop at line 254-256).
    - The Wave 0 D-13 test `test_bibliography_format_skips_alignment_when_profile_omits` is a UNIT test that passes config directly (not from the JSON), so this JSON change does NOT make it pass — verify by running it before and after the JSON edit. If still RED after the JSON change, the test fails because `apply_bibliography_format`'s scalar_fields loop is including alignment in the iteration even when the config dict doesn't carry it (i.e., there's a bug at lines 254-265 that the existing code never exposed because the rule ALWAYS carried the scalars). Diagnose and fix in this task.
    - Phase 1 + Phase 2 integration tests on bibliography_minimal.docx and negative DOCX must still pass — the entries lose their automatic indent fix, but the regression gate measures `after_diff_rate` and the negative corpus shouldn't regress because the entries' inherited indents were not being respected anyway (the rule was forcing -1.0 / 2.25 over the document's actual indent).
    - If the negative-corpus mean diff-rate REGRESSES because of this strip, document in the SUMMARY and propose either (a) restoring the scalars in this rule (per-rule), or (b) moving the scalars to `gost_7_32_2017.json` profile `labels.bibliography_item.style_profile.*` and threading the profile through to apply_bibliography_format. Per researcher Open Question 4 recommendation, option (b) is the cleaner path; if needed, the executor adds the profile fields in this task as a follow-up sub-step.
  </behavior>
  <action>
    **Sub-step 2a — Verify current state.** Read `src/rules/formatting_rules_v1.json` lines 115-132. Confirm the rule shape matches the "Current state" in <interfaces>.

    **Sub-step 2b — Edit the JSON.** Replace:

    ```json
        {
          "id": "bibliography_item_format",
          "applicable_labels": ["bibliography_item"],
          "parameter": "bibliography_format",
          "expected_value": {
            "style_name": "List Number",
            "first_line_indent_cm": -1.0,
            "left_indent_cm": 2.25
          },
    ```

    with:

    ```json
        {
          "id": "bibliography_item_format",
          "applicable_labels": ["bibliography_item"],
          "parameter": "bibliography_format",
          "expected_value": {
            "style_name": "List Number"
          },
    ```

    Keep `action`, `severity`, `autocorrect`, `priority` fields intact.

    **Sub-step 2c — Validate JSON.**

    ```bash
    python -c "import json; data=json.load(open('src/rules/formatting_rules_v1.json')); rule=[r for r in data['rules'] if r['id']=='bibliography_item_format'][0]; assert rule['expected_value']=={'style_name':'List Number'}, rule['expected_value']; print('JSON OK')"
    ```

    **Sub-step 2d — Run the D-13 unit test.**

    ```bash
    python -m pytest tests/test_bibliography_phase2.py::test_bibliography_format_skips_alignment_when_profile_omits -x -q
    ```

    If RED — open `src/rules/rule_engine.py` `apply_bibliography_format` (line 230) and inspect the scalar_fields loop. The test passes `config={"style_name": "List Number"}` (no alignment / indents). If `applied` contains `"alignment"`, the loop is iterating over `scalar_fields` but not actually short-circuiting on `if field not in config: continue`. Diagnose: maybe `config[field]` is being called with a missing key, raising KeyError that's swallowed elsewhere, OR the loop is using `for field, value in config.items()` instead. Fix to the documented PATTERNS.md shape:

    ```python
    scalar_fields = [
        "alignment", "first_line_indent_cm", "left_indent_cm",
        "line_spacing", "space_before_pt", "space_after_pt",
    ]
    for field in scalar_fields:
        if field not in config:
            continue
        applied.extend(
            apply_scalar_fix(
                paragraph=paragraph, parameter=field, expected_value=config[field],
                default_font_name="Times New Roman",
            )
        )
    ```

    Place this loop INSIDE `apply_bibliography_format` after the `style_name` block and after `applied.extend(apply_bibliography_numbering(...))`.

    **Sub-step 2e — Regression check.** Run the full suite to verify no regression from the JSON strip:

    ```bash
    python -m pytest tests/ -x -q -k "not test_negative_corpus_diff_rate_phase2_baseline" 2>&1 | tail -30
    ```

    Expected: ONLY `test_negative_corpus_diff_rate_phase2_baseline` is excluded (Task 3 verifies it). All other tests should be GREEN. If the bibliography integration tests on bibliography_minimal.docx or negative DOCX REGRESS — diagnose: the strip removed scalars that `audit_or_format_docx` was using to bring entries into compliance. Two remediation paths:
    1. **Add profile-level scalars**: open `src/rules/profiles/gost_7_32_2017.json`. Inside `labels.bibliography_item.style_profile`, add `"first_line_indent_cm": -1.0` and `"left_indent_cm": 2.25`. The rule consumes via profile flow.
    2. **Restore rule-level scalars**: revert the JSON strip. This abandons D-13 cleanliness but preserves regression.

    Choose path 1 (researcher recommendation). Document the choice in the SUMMARY.
  </action>
  <verify>
    <automated>python -c "import json; data=json.load(open('src/rules/formatting_rules_v1.json')); rule=[r for r in data['rules'] if r['id']=='bibliography_item_format'][0]; assert rule['expected_value']=={'style_name':'List Number'}, rule['expected_value']; print('JSON OK')" && python -m pytest tests/test_bibliography_phase2.py::test_bibliography_format_skips_alignment_when_profile_omits -x -q 2>&1 | tail -10 && python -m pytest tests/ -x -q -k "not test_negative_corpus_diff_rate_phase2_baseline" 2>&1 | tail -5</automated>
  </verify>
  <acceptance_criteria>
    - `python -c "import json; data=json.load(open('src/rules/formatting_rules_v1.json')); rule=[r for r in data['rules'] if r['id']=='bibliography_item_format'][0]; assert 'first_line_indent_cm' not in rule['expected_value']; assert 'left_indent_cm' not in rule['expected_value']; assert rule['expected_value']['style_name']=='List Number'; print('OK')"` exits 0.
    - `python -m pytest tests/test_bibliography_phase2.py::test_bibliography_format_skips_alignment_when_profile_omits -x -q` exits 0 — D-13 GREEN.
    - `python -m pytest tests/ -x -q -k "not test_negative_corpus_diff_rate_phase2_baseline"` exits 0 — no other regressions.
    - Phase 1 positive corpus regression (`python -m pytest tests/test_positive_docx_regression.py -x -q`) GREEN — D-13 strip does not break positive corpus because positive_examples don't have bibliography_item paragraphs that need this rule's fix path.
    - If profile-level scalars were added (sub-step 2e path 1), `src/rules/profiles/gost_7_32_2017.json` contains both `labels.bibliography_item.style_profile.first_line_indent_cm` and `labels.bibliography_item.style_profile.left_indent_cm`; SUMMARY documents the addition and rationale (regression remediation under D-13).
  </acceptance_criteria>
  <done>D-13 JSON strip applied; test_bibliography_format_skips_alignment_when_profile_omits GREEN; regression handled (either via profile-level scalars or via documented test/rule update).</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Verify D-15 negative-corpus regression gate; remediate if mean diff-rate exceeds 0.4781</name>
  <files>tests/test_negative_corpus_diff_rate.py</files>
  <read_first>
    - tests/test_negative_corpus_diff_rate.py (Wave 0 created the test; check whether it PASSED or FAILED in the Wave 0 SUMMARY)
    - .planning/phases/02-bibliography-list-semantics/02-01-test-scaffolding-red-SUMMARY.md (records the Wave 0 D-15 status)
    - .planning/phases/01-engine-guardrails-cohesion-audit/01-VERIFICATION.md §"MH4" (Phase 1 mean over 17 docs = 0.4737)
    - .planning/phases/02-bibliography-list-semantics/02-CONTEXT.md §"D-15"
    - .planning/phases/02-bibliography-list-semantics/02-RESEARCH.md §"Open Question 1" lines 568-571
    - src/evaluation/format_regression_audit.py audit_negative_directory (CONFIRM signature: does it accept `limit`? `profile_id`?)
  </read_first>
  <behavior>
    - Run `tests/test_negative_corpus_diff_rate.py`. Expected outcome: PASS (mean ≤ 0.4781).
    - If FAIL — investigate which subset documents drove the mean up. Likely candidates: D-09 over-firing on body_text rows that previously got auto-fixed (now route to review, increasing diff distance), or D-05 ilvl=1 change rendering entries at a different position causing apparent diff.
    - Three remediation paths, in order of preference:
      1. **Tighten D-09**: If D-09 over-fires on rows that should stay body_text (i.e., the marker regex is too greedy on legitimate prose like `"и т. д."`), narrow `_paragraph_has_list_marker` heuristic OR add a length lower bound (e.g., only fire D-09 when text is short — say ≤ MAX_FALLBACK_LIST_CHARS).
      2. **Widen the test corpus**: Switch `limit=4` to the full directory (no limit) to match Phase 1's mean baseline (0.4737 ≤ 0.4781). The 4-doc subset may be unrepresentative.
      3. **Update the baseline number**: ONLY if the 4-doc subset's pre-Phase-1 baseline was already > 0.4781 (i.e., the subset is harder than the full corpus). Document the new baseline as a 4-doc-subset-specific number and re-pin.
    - If a remediation requires production code change, that change goes in this task (not deferred). The plan ships the gate GREEN.
  </behavior>
  <action>
    **Sub-step 3a — Run the test.**

    ```bash
    python -m pytest tests/test_negative_corpus_diff_rate.py -x -q 2>&1 | tail -10
    ```

    If GREEN — done. Confirm acceptance criteria below.

    **Sub-step 3b — If RED, capture the diagnostic.**

    Re-run with detailed output to see the measured mean and which docs failed:

    ```bash
    python -m pytest tests/test_negative_corpus_diff_rate.py -x -v 2>&1 | tail -40
    ```

    Read the `subset[['after_diff_rate']]` table from the assertion message.

    **Sub-step 3c — Diagnose.**

    Compare each 4-doc subset entry's `after_diff_rate` against the Phase 1 baseline (which was over 17 docs, mean 0.4737). If a SINGLE doc's `after_diff_rate` is > 0.5 and dominates the mean, it's likely a Phase 2 regression on that file specifically. Open the file and audit by hand:

    ```bash
    python -c "
    from pathlib import Path
    from src.evaluation.format_regression_audit import audit_negative_directory, audits_to_frame
    audits = audit_negative_directory('negative_examples', profile_id='gost_7_32_2017')
    frame = audits_to_frame(audits)
    print(frame[['source_file', 'before_diff_rate', 'after_diff_rate']].sort_values('after_diff_rate', ascending=False).head(10))
    "
    ```

    Identify the worst-regressing file. If its `before_diff_rate` is much LOWER than `after_diff_rate`, Phase 2 changes hurt it. If `before == after`, the file was always bad and the subset is just unlucky.

    **Sub-step 3d — Choose remediation path.**

    - **Path 1 (tighten D-09)**: if the regressing file's audit CSV contains many rows whose `applied_fixes` are now `review` (because D-09 over-fires), add a length floor:

      Modify the D-09 branch in `src/rules/rule_engine.py` (the one Task 1 inserted) to add:

      ```python
      if label == "body_text" and paragraph_style_class == "body":
          text_for_marker = str(row_data.get("text", "") or paragraph.text or "").strip()
          if (
              _paragraph_has_list_marker(text_for_marker)
              and not _paragraph_has_numbering(paragraph)
              and not _is_long_plain_paragraph(text_for_marker)  # NEW guard: don't review long prose with a leading bullet-like character
          ):
              return { ... }
      ```

      Re-run the gate. Re-run the D-09 unit test (`test_ambiguous_list_marker_no_numId_routes_to_review`) — it should STILL pass because its test text is short.

    - **Path 2 (widen corpus)**: change the test to drop the `limit=4` (or pass `limit=None` if signature supports it). Update `PHASE_1_BASELINE_MEAN_DIFF_RATE` if needed (likely no — 0.4737 ≤ 0.4781).

    - **Path 3 (update baseline)**: re-pin `PHASE_1_BASELINE_MEAN_DIFF_RATE` to the post-Phase-2 measured mean of the 4-doc subset. Document the rationale in the test docstring.

    Choose path 1 first (tightens the implementation), then path 2 (corpus widens), then path 3 only as last resort.

    **Sub-step 3e — Final verification.**

    ```bash
    python -m pytest tests/test_negative_corpus_diff_rate.py -x -q
    python -m pytest tests/ -x -q 2>&1 | tail -20
    ```

    Both must exit 0. Phase 1 baseline test (`test_positive_docx_examples_are_not_autofixed`) MUST still be GREEN — never sacrifice the positive corpus to satisfy the negative gate.
  </action>
  <verify>
    <automated>python -m pytest tests/test_negative_corpus_diff_rate.py -x -q 2>&1 | tail -10 && python -m pytest tests/ -x -q 2>&1 | tail -10</automated>
  </verify>
  <acceptance_criteria>
    - `python -m pytest tests/test_negative_corpus_diff_rate.py -x -q` exits 0 — D-15 GREEN.
    - `python -m pytest tests/ -x -q` exits 0 — FULL test suite GREEN.
    - `python -m pytest tests/test_positive_docx_regression.py -x -q` exits 0 — Phase 1 positive baseline preserved (NEVER regressed).
    - SUMMARY records:
      - Pre-fix measured mean diff-rate (the value from Sub-step 3a if RED).
      - Remediation path chosen (1, 2, or 3).
      - Post-fix measured mean diff-rate.
      - Confirmation Phase 1 positive corpus stayed `changed=0` on `1.docx, 4.docx, 58.docx, 59.docx`.
    - All Wave 0 RED tests across `tests/test_bibliography_phase2.py`, `tests/test_postprocess_rules.py`, `tests/test_profile_loader.py`, `tests/test_negative_corpus_diff_rate.py` are GREEN.
  </acceptance_criteria>
  <done>D-15 gate GREEN; Phase 2 ships with full test suite GREEN; Phase 1 baseline preserved.</done>
</task>

</tasks>

<verification>
After all 3 tasks complete:

```bash
python -m pytest tests/ -v 2>&1 | tail -40
```

Expected outcome:
- 100% GREEN across the entire test suite.
- 53 Phase 1 tests preserved.
- ~19 Phase 2 new tests all GREEN.
- D-09 routing works on body_text + marker + no numPr.
- D-10 verified — no over-firing on plain body_text.
- D-13 unit test GREEN — apply_bibliography_format respects profile/config absence.
- D-15 automated regression gate GREEN.
- MAX_FALLBACK_LIST_* constants deleted; `_is_long_plain_paragraph` threaded via kwargs.
- `formatting_rules_v1.json:bibliography_item_format.expected_value` carries only `style_name`.

ROADMAP success criteria verification:
1. ✓ `СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ` overridden to bibliography_title (Plan 02 + this plan's regression check).
2. ✓ After `audit-docx --apply-safe` on a real negative DOCX, all bibliography entries share one numId AND `applied_fixes` includes `numbering` (test_negative_4_bibliography_single_numId — Plan 03 + this plan).
3. ✓ Long body_text without numId stays body_text (test_long_body_text_without_marker_stays_body_text); marker-only lists without numId become review (test_ambiguous_list_marker_no_numId_routes_to_review — this plan).
4. ✓ Targeted pytest fixtures cover all three behaviors (Wave 0 tests, all GREEN).
</verification>

<success_criteria>
- src/rules/rule_engine.py: MAX_FALLBACK_LIST_WORDS / MAX_FALLBACK_LIST_CHARS deleted; D-09 review branch added; _is_long_plain_paragraph kwarg-threaded.
- src/rules/formatting_rules_v1.json: bibliography_item_format.expected_value stripped to {"style_name": "List Number"}.
- ALL Wave 0 Phase 2 RED tests GREEN.
- ROADMAP Phase 2 success criteria 1-4 all verifiable via the test suite.
- Phase 1 baseline preserved on positive_examples + style_signatures + cohesion-audit invariants.
- No production code regressions on integration tests for bibliography_minimal.docx or negative_examples DOCX.
</success_criteria>

<output>
After completion, create `.planning/phases/02-bibliography-list-semantics/02-04-ambiguous-routing-and-gate-green-SUMMARY.md` documenting:
- Files modified (2) with line counts (added/removed).
- Constants deleted (MAX_FALLBACK_LIST_WORDS, MAX_FALLBACK_LIST_CHARS).
- D-09 branch position and explanation string.
- D-13 JSON strip applied to bibliography_item_format.expected_value.
- D-15 regression gate outcome:
  - Pre-fix measured mean (if RED initially).
  - Remediation path (Task 3 sub-step 3d choice with rationale).
  - Post-fix mean (must be ≤ 0.4781).
- All Wave 0 RED tests turn GREEN — exact names.
- Phase 1 positive corpus confirmation (changed=0 on 1/4/58/59).
- Full test count: 53 (Phase 1) + ~19 (Phase 2) = ~72 GREEN.
- ROADMAP Phase 2 success criteria 1-4 traceability — which test proves each.
- Any deferred follow-ups (e.g. legacy `_create_section_abstract_num_id` cleanup, profile-level scalar additions if Task 2 took path 1).
</output>
</content>
