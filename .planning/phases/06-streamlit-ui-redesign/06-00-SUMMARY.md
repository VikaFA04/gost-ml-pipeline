---
phase: 06-streamlit-ui-redesign
plan: 00
status: complete
commits:
  - a01b6eb test(06-00): wave 0 RED scaffold for app.py UI surface (Task 1)
  - b1b69b8 test(06-00): wave 0 RED stubs — RunLog PII contract + STATUS_CHIP + preflight translator (Task 2)
key-files:
  created:
    - tests/conftest.py
    - tests/test_app_ui.py
    - tests/test_run_log.py
    - tests/test_render_block_section.py
    - tests/test_preflight.py
tests:
  red: 25
  green: 0
---

# 06-00 SUMMARY — Wave 0 RED test scaffolding

## What was built

Five test files establishing the RED contract for Phase 6 Waves 1-5.

| File | `def test_` count | RED reason (expected) |
|------|------------------:|-----------------------|
| `tests/conftest.py` | 0 (fixtures only) | n/a — provides `app_test` AppTest fixture + `pytest.importorskip("streamlit")` venv guard |
| `tests/test_app_ui.py` | 4 | Empty-state copy not yet present in `render_hero` (Wave 2/3); no-traceback assertion guards `app.py:773` `st.exception(exc)` removal in Wave 2 |
| `tests/test_run_log.py` | 7 | `ModuleNotFoundError: src.inference.run_log` until Wave 1 lands |
| `tests/test_render_block_section.py` | 9 | `AttributeError: app.STATUS_CHIP` / `app.modal_reason_is_valid` until Waves 2/4 |
| `tests/test_preflight.py` | 5 | `AttributeError: app.preflight_translate_error` until Wave 2 |

Total: 25 RED-stub tests. No production code touched.

## Confirmed RED signals

`pytest --collect-only -q tests/test_run_log.py tests/test_render_block_section.py tests/test_preflight.py tests/test_app_ui.py` (system Python, no venv):

```
ImportError while importing test module 'tests/test_run_log.py'.
tests/test_run_log.py:24: in <module>
    from src.inference.run_log import RunLog
E   ModuleNotFoundError: No module named 'src.inference.run_log'
```

`tests/test_render_block_section.py` and `tests/test_preflight.py` skip cleanly via the
module-level `pytest.importorskip("streamlit")` gate (acceptable per 06-RESEARCH.md
§10 OQ-3 — Streamlit-dependent tests skip on system Python and only run inside the
venv where `streamlit==1.56.0` is importable).

`tests/test_app_ui.py` collects 4 tests; the empty-state and no-traceback tests are
the RED signals for Wave 2/3.

## conftest.py AppTest fixture pattern (for downstream waves)

```python
@pytest.fixture
def app_test():
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(REPO_ROOT / "app.py"))
```

Downstream waves invoke as `at = app_test.run(timeout=30)`; iterate
`at.markdown / at.error / at.title / at.header / at.subheader / at.warning / at.info`
elements and assert via membership over their `.value` strings.

## Deviations from plan

None. All 5 files match the planned test names and RED signals.

## Note on test_run_log.py overlap with 06-01

Both this plan (Wave 0, owner) and 06-01 (Wave 1, RunLog impl) added
`tests/test_run_log.py` in their respective worktrees. **06-00 is the canonical
owner per the plan's `files_modified` list**; the 06-01 agent created a parallel
copy because its dependency (`src.inference.run_log`) did not yet exist when its
worktree branched. Orchestrator must resolve the merge favouring 06-00's version
(149 lines vs 06-01's 143-line near-duplicate). Both versions assert the same 7
contract truths against the same `RunLog` API; the 06-00 canonical version wins.
