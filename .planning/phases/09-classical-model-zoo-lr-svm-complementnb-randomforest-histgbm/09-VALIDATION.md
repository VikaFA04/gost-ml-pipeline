---
phase: 09
slug: classical-model-zoo-lr-svm-complementnb-randomforest-histgbm
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-16
---

# Phase 9 — Validation Strategy

> Per-phase validation contract. Reconstructed from PLAN + SUMMARY artifacts (State B — no prior VALIDATION.md existed).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (installed in `/tmp/gost-test-venv`) |
| **Config file** | none — no `pytest.ini`; `@pytest.mark.slow` is an unregistered custom mark (PytestUnknownMarkWarning is informational only) |
| **Quick run command** | `/tmp/gost-test-venv/bin/python -m pytest tests/test_compare_classical_acceptance.py -k "not slow" -q` |
| **Full Phase 9 surface** | `/tmp/gost-test-venv/bin/python -m pytest tests/test_compare_classical_acceptance.py tests/test_phase_8_sc2_acceptance.py -v` |
| **Full suite (incl. slow)** | `make compare-classical-acceptance` (runs full zoo + SC-2 acceptance test end-to-end) |
| **Estimated runtime** | ~30 s (3 fast tests + skip 1 slow + 1 artifact-level test); ~277 s for full 4-test pass including `@pytest.mark.slow` test |

---

## Sampling Rate

- **After every task commit:** Run quick command (3 fast non-slow tests)
- **After every plan wave:** Run full Phase 9 surface command
- **Before `/gsd-verify-work`:** Full suite (`make compare-classical-acceptance`) must be green
- **Max feedback latency:** 30 s (fast path); 277 s (full including slow)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | REQ-classical-model-zoo | T-09-W1-01 | Additive-only edit to REQUIREMENTS.md; no executable surface | unit (grep) | `grep -n "REQ-classical-model-zoo" .planning/REQUIREMENTS.md` | ✅ | ✅ |
| 09-01-02 | 01 | 1 | REQ-classical-model-zoo (D-D-04 TDD gates: CLI smoke + CSV schema + metric floors + per-class coverage) | T-09-W1-02 | Tests run locally; no PII in label names | integration | `/tmp/gost-test-venv/bin/python -m pytest tests/test_compare_classical_acceptance.py -k "not slow" -q` | ✅ | ✅ |
| 09-02-01 | 02 | 2 | REQ-classical-model-zoo (D-B-01 + D-E-01 six pipelines; D-C-02 CSV schema; D-E-02 per-model exception handling; D-C-03 inference timing; D-C-05 model_size_mb) | T-09-W2-01 T-09-W2-02 | output-dir path normalised; error["message"] truncated to 200 chars; no full traceback leaked | integration | `/tmp/gost-test-venv/bin/python -m pytest tests/test_compare_classical_acceptance.py -k "not slow" -q` | ✅ | ✅ |
| 09-02-02 | 02 | 2 | REQ-classical-model-zoo (D-C-04 CLI subcommand; D-C-04 --models/--output-dir/--seed/--quick flags) | T-09-W2-04 | Timestamped output dir prevents silent overwrites | smoke | `/tmp/gost-test-venv/bin/python -m src.main compare-classical --help` | ✅ | ✅ |
| 09-02-03 | 02 | 2 | REQ-classical-model-zoo (D-D-04 all 4 gates GREEN: CLI smoke + CSV schema + metric floors + per-class F1 coverage) | T-09-W2-03 | Per-model exception handler catches MemoryError; CLI exits 1; SC-2 still verifiable | integration | `/tmp/gost-test-venv/bin/python -m pytest tests/test_compare_classical_acceptance.py -v -k "not slow"` (fast) + `/tmp/gost-test-venv/bin/python -m pytest tests/test_compare_classical_acceptance.py -v -m slow` (slow, full dataset SC-2 gate) | ✅ | ✅ |
| 09-03-01 | 03 | 3 | REQ-classical-model-zoo (D-D-02 + D-E-01 + D-E-05: standalone Phase 8 SC-2 floor gate on latest zoo CSV; Makefile target) | T-09-W3-01 T-09-W3-02 | Glob reads from local results/ (gitignored); test is read-only; date-expansion in Makefile uses $$(date) | integration + smoke | `/tmp/gost-test-venv/bin/python -m pytest tests/test_phase_8_sc2_acceptance.py -v` | ✅ | ✅ |
| 09-03-02 | 03 | 3 | REQ-classical-model-zoo (documentation: CLI invocation, 6-row output shape, linear_svm_production identity, Phase 8 SC-2 gate row) | T-09-W3-05 | README content locked to D-C-04 + D-E-01 decisions | smoke (grep) | `grep -c "linear_svm_production" README.md` | ✅ | ✅ |
| 09-03-03 | 03 | 3 | REQ-classical-model-zoo (SC-1..SC-5 live verification on full annotations_test.csv corpus; UAT 8/8 approved) | — | Manual inspection; no automated coverage possible | manual | See Manual-Only Verifications below | N/A | ✅ |

*Status: ⬜ pending · ⏵ in progress · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 1 Requirements

Wave 1 in this phase corresponds to Plan 09-01 (RED scaffolding). All items were delivered by the close of Plan 09-01 execution.

- [x] `tests/test_compare_classical_acceptance.py` — 4 RED TDD acceptance tests (D-D-04 gates 1–4); RED trigger was `from src.compare_classical import run_compare_classical` at module level raising `ModuleNotFoundError`; confirmed GREEN after Plan 09-02.
- [x] `.planning/REQUIREMENTS.md` — REQ-classical-model-zoo entry inserted before REQ-mvp-acceptance (line 152 post-insert); locked acceptance language from D-C-01, D-C-02, D-D-04, D-E-01.

*Amendment applied mid-Wave-2 (OQ-5 / D-E-05 2026-05-16): `SC2_MACRO_F1_FLOOR` in `test_compare_classical_acceptance.py` relaxed from `0.9414` (after-rules system metric) to `0.86` (raw-ML production baseline). This amendment is recorded in CONTEXT.md D-E-05 and both test files. The 0.9414 after-rules gate remains in REQUIREMENTS.md REQ-ml-quality-acceptance and ROADMAP Phase 8 SC-2 as a separate measurement source.*

**Existing infrastructure covered all other requirements.** No new pytest framework installation was needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions | Status |
|----------|-------------|------------|-------------------|--------|
| End-to-end live zoo run + 8-point artifact inspection (09-03 Task 3 UAT) | REQ-classical-model-zoo SC-1..SC-5 | Full-dataset 277 s run + visual inspection of `results.csv` shape, `summary.txt` SC-2 verdict line, `per_class_f1.md` heading and body_text row count, `make compare-classical-acceptance` exit 0 — requires project-owner judgment on content correctness beyond schema assertions | UAT points: (1) activate `/tmp/gost-test-venv`; (2) `python -m src.main compare-classical`; (3) inspect CSV 6 rows × 8 cols + 6 model names; (4) confirm `linear_svm_production` weighted_f1 ≥ 0.94 AND macro_f1 ≥ 0.86; (5) confirm `linear_svm` is informational below SC-2; (6) read `summary.txt` for SC-2 verdict line; (7) `head -60 per_class_f1.md` + `grep -c body_text`; (8) `make compare-classical-acceptance` exits 0 | Approved 2026-05-16 — 8/8 points PASS |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or are covered by the Wave 1 test file
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (each of the 8 tasks has either a grep, pytest, or help-flag command)
- [x] Wave 1 covers all MISSING references (4 RED tests landed in 09-01; no gaps remained at 09-02 start)
- [x] No watch-mode flags in any automated command
- [x] Feedback latency < 30 s for fast path (3 non-slow tests collected in 4.75 s; estimated fast-path run ≈ 30 s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-16

---

## Audit Trail

| Date | Event | Gaps Found | Gaps Resolved | Gaps Escalated | Notes |
|------|-------|------------|---------------|----------------|-------|
| 2026-05-16 | state_b_initial — reconstructed from PLAN + SUMMARY artifacts; no prior VALIDATION.md existed | 0 | 0 | 0 | All 5 test functions collected cleanly (`--collect-only` confirmed); all 8 per-task rows classified COVERED; 3 fast tests GREEN per 09-02-SUMMARY; 1 slow test GREEN per 09-03 UAT + make exit 0; 1 standalone SC-2 test PASSED per 09-03-SUMMARY |
