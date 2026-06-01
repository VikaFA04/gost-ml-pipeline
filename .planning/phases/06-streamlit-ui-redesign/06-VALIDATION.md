---
phase: 6
slug: streamlit-ui-redesign
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-14
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Detailed PASS criteria and tooling are defined in `06-RESEARCH.md` §8 «Validation Architecture». This file is the executable contract derived from that section.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + `streamlit.testing.v1.AppTest` (Streamlit ≥1.32) |
| **Config file** | `pyproject.toml` / `pytest.ini` (existing repo config) |
| **Quick run command** | `pytest tests/test_app_ui.py tests/test_run_log.py -x` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~30s quick / ~3min full |

**Venv constraint (from RESEARCH §8 OQ-3):** `pytest` MUST be invoked inside a venv where `streamlit` is importable. System Python invocation breaks. Wave 0 task standardizes this.

---

## Sampling Rate

- **After every task commit:** Run quick command.
- **After every plan wave:** Run full suite command.
- **Before `/gsd-verify-work`:** Full suite must be green.
- **Max feedback latency:** 60 seconds for quick run.

---

## Per-Surface Validation Map (P0)

| Surface | Requirement | Validation Method | Tooling | PASS Criterion |
|---------|-------------|-------------------|---------|----------------|
| Audit flow (upload → profile → run → summary → table → download) | REQ-ui-main-flow | AppTest end-to-end | `streamlit.testing.v1.AppTest` | Linear flow completes; sidebar drives visibility of main-pane sections per D-01 |
| Per-block view (5 statuses, status chips, inline expanders, original text + confidence + explanation) | REQ-ui-problem-block-view | AppTest + golden HTML | `AppTest`, snapshot of rendered chip HTML | All 5 status values render distinct chip; expander payload contains confidence + explanation + original block text |
| Preflight failures (unreadable DOCX, malformed paragraphs, MIME mismatch) | REQ-input-preflight | Unit + AppTest | pytest on `validate_document_input` translator + AppTest on error surface | No `Traceback` substring in rendered output; user message in Russian; technical class name available in run-log only |
| Run-log JSON (PII boundary) | REQ-pipeline-logging | Unit golden-file + property test | pytest on `src/inference/run_log.py` | JSON contains `{stage, ts, status, error_class, error_message}`; basename-only filename; no document text; no traceback; assertion: no key in {`text`, `paragraph`, `block_content`, `traceback`} present in any record |
| Methodical modal mirrors CLI D-004 | REQ-ui-main-flow (modal subflow) | AppTest + contract test | `AppTest` driving `st.dialog` interactions; cross-check vs `cmd_extract_methodical_profile` | Apply button disabled until `reason.strip() ≥ 8`; whitespace-only reason rejected; no writes under `src/rules/profiles/` until apply; preview path under `tempfile.gettempdir()` |
| Design-review pass | REQ-ui-design-review | Manual against falsifiable rubric | Owner reviews against UI-SPEC §criteria (RESEARCH §8 lists falsifiable items) | Rubric items pass: status chip palette matches UI-SPEC; sidebar/main-pane split present; no 5-tab structure; Russian copy present; defect list closed before sign-off |

---

## Per-Task Verification Map

To be filled by planner. Each task MUST link to one row above OR mark `<automated>` Wave 0 dependency. See deep_work_rules in plan-phase: every task gets `<read_first>` + grep-verifiable `<acceptance_criteria>`.

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — shared `AppTest` fixture pointing to `app.py`; venv resolution helper.
- [ ] `tests/test_app_ui.py` — RED stubs for each P0 surface above (AppTest-driven).
- [ ] `tests/test_run_log.py` — RED stubs for run-log PII boundary + golden JSON.
- [ ] Test runner venv convention documented in plan or `Makefile` (resolves OQ-3 from RESEARCH §8).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Design-review sign-off | REQ-ui-design-review | Visual/UX judgment | Owner runs `streamlit run app.py`, walks linear flow with one real `.docx`, opens methodical modal, triggers a preflight error, downloads run-log; rubric in RESEARCH §8 design-review criteria; defects logged in `06-DESIGN-REVIEW.md`; resolution before phase verification. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s for quick run
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
