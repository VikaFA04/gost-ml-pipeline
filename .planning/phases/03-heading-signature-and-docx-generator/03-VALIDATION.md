---
phase: 3
slug: heading-signature-and-docx-generator
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-13
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (system python) |
| **Config file** | none — `/usr/bin/python3 -m pytest` direct invocation |
| **Quick run command** | `/usr/bin/python3 -m pytest tests/test_style_signatures.py tests/test_rule_engine.py -x -q` |
| **Full suite command** | `/usr/bin/python3 -m pytest tests/test_style_signatures.py tests/test_rule_engine.py tests/test_positive_docx_regression.py tests/test_negative_corpus_diff_rate.py tests/test_postprocess_rules.py tests/test_profile_loader.py tests/test_bibliography_phase2.py tests/test_format_regression_audit.py -q` |
| **Estimated runtime** | ~150s (full); ~10s (quick) |

`python` is not on PATH — use `/usr/bin/python3`. ML-stack tests
(`test_application_service`, `test_baseline_inferencer`,
`test_methodical_profile_editor`, `test_pattern_features`,
`test_predict_blocks`, `test_app_upload_contract`, `test_cli_parser`,
`test_dataset_contract`) are NOT in the suite — system python lacks
`sklearn`/`joblib`/`streamlit`.

---

## Sampling Rate

- **After every task commit:** Run quick command (≈10s feedback).
- **After every plan wave:** Run full command (≈150s).
- **Before `/gsd-verify-work`:** Full suite must be GREEN.
- **Max feedback latency:** 30 seconds for quick command.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 0 | D-01 | unit | `pytest tests/test_style_signatures.py::test_heading_signature_key_present -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 0 | D-03/D-04 | unit | `pytest tests/test_style_signatures.py::test_heading_signature_direct_none_is_inherited -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 0 | D-03/D-04 | unit | `pytest tests/test_style_signatures.py::test_heading_signature_direct_override_detected -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | 0 | D-03 | unit | `pytest tests/test_style_signatures.py::test_heading_signature_cascade_walk -x` | ❌ W0 | ⬜ pending |
| 03-01-05 | 01 | 0 | D-05 | unit | `pytest tests/test_rule_engine.py::test_heading_inherited_mismatch_routes_to_review -x` | ❌ W0 | ⬜ pending |
| 03-01-06 | 01 | 0 | D-06 | unit | `pytest tests/test_rule_engine.py::test_heading_direct_mismatch_routes_to_autofix -x` | ❌ W0 | ⬜ pending |
| 03-01-07 | 01 | 0 | D-06 | unit | `pytest tests/test_rule_engine.py::test_heading_direct_match_no_change -x` | ❌ W0 | ⬜ pending |
| 03-01-08 | 01 | 0 | D-09 | schema | `pytest tests/test_rule_engine.py::test_heading_rules_present_in_schema -x` | ❌ W0 | ⬜ pending |
| 03-01-09 | 01 | 0 | D-10 | unit | `pytest tests/test_rule_engine.py::test_heading_minimal_positive_zero_fixes -x` | ❌ W0 | ⬜ pending |
| 03-01-10 | 01 | 0 | D-10 | unit | `pytest tests/test_rule_engine.py::test_heading_minimal_direct_fix -x` | ❌ W0 | ⬜ pending |
| 03-01-11 | 01 | 0 | D-10 | unit | `pytest tests/test_rule_engine.py::test_heading_minimal_inherited_review -x` | ❌ W0 | ⬜ pending |
| 03-02-* | 02 | 1 | D-01..D-04 | unit | quick command | ✅ (W0 RED) | ⬜ pending |
| 03-03-* | 03 | 2 | D-05/D-06/D-09 | unit | quick command | ✅ (W0 RED) | ⬜ pending |
| 03-04-* | 04 | 3 | D-07/D-10 + regression | integration | full command | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_style_signatures.py` — add 4+ heading signature extraction tests (`test_heading_signature_key_present`, `test_heading_signature_direct_none_is_inherited`, `test_heading_signature_direct_override_detected`, `test_heading_signature_cascade_walk`).
- [ ] `tests/test_rule_engine.py` — add 6+ D-05/D-06 routing tests + 1 schema-presence test + 3 fixture-driven tests; UPDATE `test_heading_style_direct_alignment_requires_review_not_autofix` to assert `status="changed"` (D-06 behavior post blanket-guard removal).
- [ ] `tests/fixtures/_build_heading_minimal.py` — builder script (Phase 1/2 pattern).
- [ ] `tests/fixtures/heading_minimal.docx` — generated binary (4 paragraphs per D-10).
- [ ] `tests/test_positive_docx_regression.py` — extend assertion to forbid `heading_*` autofixes on the GOST-decorated subset (heading-direct-fix invariant per D-07).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Open output DOCX in Word | D-06 visible behavior | Word rendering | After `format-docx --apply-safe` on a heading_minimal-derived doc, open in Word and confirm the autofixed paragraph displays the corrected font/spacing while the inherited-mismatch paragraph is unchanged |
| Inspect XML diff for direct-property writes | D-06 invariant | XML-level inspection | `unzip -p out.docx word/document.xml | grep -A2 'pPr' | head -40` — confirm no spurious direct properties on inherited paragraphs |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (5 entries above)
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s for quick command
- [ ] `nyquist_compliant: true` set in frontmatter once Wave 0 lands

**Approval:** pending
