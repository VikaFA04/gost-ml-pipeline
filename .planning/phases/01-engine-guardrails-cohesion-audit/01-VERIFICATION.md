---
phase: 01-engine-guardrails-cohesion-audit
status: passed
verified_by: orchestrator-inline (gsd-verifier rate-limited; verification executed in main context against same evidence files)
verified_at: "2026-05-12"
requirements_verified:
  - REQ-fix-style-guards
  - REQ-fix-styled-paragraphs-no-direct-props
  - REQ-rule-engine-cohesion-audit
must_have_score: 4/4
---

# Phase 01 Verification Report

## Goal recap (from ROADMAP.md)

> The rule engine stops applying `body_text` rules to heading/toc/caption/list-styled paragraphs, the previously-flagged INFERRED edges around the rule engine are verified, and the cohesion problem from the graphify audit is documented.

## Must-have results

### MH1 — Positive corpus untouched by safe autofix
**Status:** PASSED
**Evidence:**
- `tests/test_positive_docx_regression.py::test_positive_docx_examples_are_not_autofixed` runs `audit-docx --apply-safe` (via direct `audit_negative_directory` import) on `positive_examples/{1,4,58,59}.docx` and asserts `changed == 0` for every block of every file.
- pytest output (this session, post-merge of all 4 plans): `1 passed in 10.32s` for that file in isolation; `53 passed in 10.80s` for the full phase test set.
- Style guard at `src/rules/rule_engine.py:apply_rules_to_paragraph` short-circuits before any direct-property write when `label == "body_text"` and `classify_style(paragraph) != "body"` — confirmed by `test_style_guard_does_not_write_direct_props` (asserts `paragraph_format.alignment is None` etc. after attempted body_text rule application on a Heading-styled paragraph).

### MH2 — Cohesion audit + cohesion strictly > 0.06
**Status:** PASSED (raw-value gate; see caveat)
**Evidence:**
- Audit doc `01-COHESION-AUDIT.md`: `grep -c '^### edge:'` → 67. Distribution: 33 on `apply_rules_to_paragraph` + 34 on `load_rules`. All 67 verdicts are KEEP, each backed by a grep-verified callsite (65 tests + 2 production callsites in `src/generate/inplace_formatter.py`).
- Cohesion line: `Cohesion (Rule Engine community): before=0.060192 after=0.061286`. Gain +0.001094 from 220 → 224 intra-community edges at constant n=86.
- Measured cluster noise = 0.000000 (5 deterministic runs in this session). The plan's a-priori `0.005` noise floor was an overestimate; with measured noise = 0, the effective gate falls back to the ROADMAP literal "strictly higher than 0.06", which the raw 0.061286 satisfies.
- **Caveat:** graphify's `cohesion_score()` does `round(actual/possible, 2)`, so `GRAPH_REPORT.md` still displays `0.06` (the gain is below the 0.005 rounding step). The audit doc and SUMMARY both record the underlying raw ratio, which is the load-bearing number for this gate. User signed off on this interpretation in this session.
- 3 D-10 low-risk refactors landed: helper move to `style_signatures.py` (commit `558f381`), `_apply_bibliography_rules` extraction (`27eca74`), `_apply_scalar_rule` extraction (`ff84ee7`).
- Follow-ups section in `01-COHESION-AUDIT.md` lists deferred high-risk work (dispatcher rewrites, per-rule `allowed_styles` schema, base_style chain walking) and the cohesion-stability subsection records both reads, noise, and gain.

### MH3 — Test baseline preserved + new guard tests added
**Status:** PASSED
**Evidence:**
- New tests added in this phase:
  - `tests/test_style_signatures.py` — 6 unit tests for `classify_style` (heading EN/RU, TOC EN/RU, caption EN/RU, list EN/RU, body negatives, None-style handling). All 6 pass.
  - `tests/test_rule_engine.py` — 8 new style_guard tests covering Heading/TOC/Caption/List blocking, heading-rule-on-heading passing, body-text-on-normal passing, no-direct-props writes, and `test_style_guard_minimal_docx_changed_zero` integration test against `tests/fixtures/style_guard_minimal.docx`.
  - `tests/test_positive_docx_regression.py` — extended to all 4 positive examples (1, 4, 58, 59).
- Pytest result on phase scope: `53 passed in 10.80s` (this session).
- The plan-stated baseline of "21+ tests" is honored: pre-existing rule_engine baseline (~38 tests) + 6 classify_style + 8 guard + 1 positive corpus = 53 in the targeted modules.

### MH4 — Negative corpus diff-rate not regressed
**Status:** PASSED
**Evidence:**
- Plan 03 SUMMARY records mean `after_diff_rate = 0.4737` across all 17 negative-corpus pairs after the style-guard insertion (gate threshold 0.4781).
- Plan 04 SUMMARY records the same `0.4737` after the helper-move refactor — confirming the refactor changed zero behavior.
- Numbers were obtained via direct `audit_negative_directory(...)` call (Plan 03 precedent — `src/main.py` import path is broken on system Python 3.9 because it pulls `sklearn` at module load; the direct call uses the same code path).

## Requirement traceability

| Req ID | Where met | Evidence |
|---|---|---|
| REQ-fix-style-guards | Plan 03 | Early-return guard at `src/rules/rule_engine.py:apply_rules_to_paragraph` (commit `9195efb`); 8 guard tests pass; integration test on style_guard_minimal.docx passes. |
| REQ-fix-styled-paragraphs-no-direct-props | Plan 03 | `test_style_guard_does_not_write_direct_props` (asserts no direct format properties after guarded run); positive corpus regression test confirms 0 changes. |
| REQ-rule-engine-cohesion-audit | Plan 04 | 67-edge audit doc + 3 D-10 refactors + cohesion-stability subsection; raw cohesion > 0.06. |

## Plan-level summary

| Plan | Status | Commits |
|---|---|---|
| 01-01 test-scaffolding-red | complete | 6 (5 RED tests/fixture + 1 SUMMARY) |
| 01-02 style-signatures-green | complete | 3 (2 impl + 1 SUMMARY) |
| 01-03 rule-engine-guard-green | complete | 3 (1 import-relocate + 1 guard insert + 1 SUMMARY) |
| 01-04 cohesion-audit | complete | 6 (1 audit doc + 3 D-10 refactors + 1 orphan-cleanup + 1 SUMMARY-finalize) |

## Deviations and caveats

1. **Wave 1 forced sequential.** Plans 01-01 and 01-02 both modify `src/rules/style_signatures.py`, so worktree parallel execution was unsafe. Wave 1 ran sequentially (`PARALLELIZATION` overridden for that wave). Documented as a planning defect for future replanning.
2. **TOC fixture style switched.** `test_style_guard_blocks_body_text_on_toc` uses `TOC Heading` style instead of `TOC 1` — python-docx default template has no `TOC 1` paragraph style. Documented in 01-01 SUMMARY.
3. **Pre-existing `blocked_unsafe_autofix` test updated.** `test_list_like_paragraph_predicted_as_body_text_is_not_autofixed` was changed from asserting `blocked_unsafe_autofix is True` (old late-path) to `explanation.startswith("style_guard_block:")` (new guard path) so the assertion stays meaningful after the early-return guard takes precedence. Documented in 01-03 SUMMARY.
4. **Audit script uses absolute-path fallback.** `_audit_enumerate_inferred_edges.py` reads `graphify-out/graph.json` with a fallback to the canonical absolute path because `graphify-out/` is gitignored and absent in executor worktrees. Documented in 01-04 SUMMARY.
5. **Regression audit via direct `audit_negative_directory` call.** `python3 -m src.main audit-regression` fails on system Python 3.9 because of an unconditional `sklearn` import at module load (Plan 03 precedent). The direct call hits the same code path with identical output.
6. **Cohesion metric is rounded by graphify.** `cohesion_score()` returns `round(actual/possible, 2)`. The reported gain (+0.001094) is below the 0.005 rounding step, so the graphify report keeps displaying `0.06`. Raw cohesion is what moves and is what the audit doc records.
7. **Dead-import cleanup.** After Plan 04 Candidate 1 moved the helpers, `LIST_STYLE_RE` and `HEADING_STYLE_RE` became orphan imports in `rule_engine.py`. Removed in commit `c19e25f` per CLAUDE.md rule on orphans.

## Result

**status: passed**

All 4 ROADMAP must-haves met. All 3 phase requirements traced. 53/53 phase-scope tests green. Negative corpus mean diff-rate 0.4737 ≤ 0.4781. Cohesion 0.060192 → 0.061286 (raw; ROADMAP > 0.06 satisfied; user-signed-off measured-noise-floor interpretation).
