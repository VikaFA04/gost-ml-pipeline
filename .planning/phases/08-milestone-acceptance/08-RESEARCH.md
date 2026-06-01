# Phase 8: Milestone Acceptance — Research

**Researched:** 2026-05-15
**Domain:** Verification / acceptance gate — no new feature code in src/
**Confidence:** HIGH (all findings grounded in actual repo files)

---

## 1. Domain Overview

Phase 8 is a pure verification phase. The boundary is:

- **Consumes** only what Phases 1-7 and 9 already shipped.
- **Produces** five artifacts: `08-VERDICT.md`, `CHANGELOG.md`, `git tag -a v1.0`,
  `tests/test_milestone_acceptance_sc*.py` (3 new test files), and
  `08-DESIGN-REVIEW-ROLLUP.md`.
- **Executes** via `make milestone-acceptance` (slow, local) and
  `make milestone-smoke` (fast CI subset).

Five success criteria to close:

| SC | Gate | Source |
|----|------|--------|
| SC-1 | End-to-end corpus run | new test using `process_document()` |
| SC-2 | ML quality dual-source | Phase 9 zoo CSV + `results/metrics/<svm>.json["after_rules"]` |
| SC-3 | Negative-corpus regression | existing `make regression-gate` (Phase 4) |
| SC-4 | Design-review consolidation + 0 open critical/high | new test + `08-DESIGN-REVIEW-ROLLUP.md` |
| SC-5 | Milestone-close artifacts | VERDICT.md + CHANGELOG.md + git tag |

Reuse principle: SC-2 raw-ML half and SC-3 are satisfied by invoking existing Make
targets verbatim. No src/ changes.

---

## 2. Makefile Pattern Reference

### 2.1 Existing Targets (exact content from `Makefile`)

File: `/Users/fedorova.van/experiments/gost_formatter/Makefile` [VERIFIED: file read]

```makefile
# Pre-PR gate. Default interpreter is python3 (this repo's macOS host has
# no plain `python`); override with `make PYTHON=python regression-gate`
# if your environment provides `python -m src.main audit-regression`.
PYTHON ?= python3
POSITIVE_DIR ?= positive_examples
NEGATIVE_DIR ?= negative_examples
PROFILE_ID ?= gost_7_32_2017
SUBSET_LIMIT ?= 4

.PHONY: regression-gate
regression-gate:
	$(PYTHON) -m src.main audit-regression \
		--positive-dir $(POSITIVE_DIR) \
		--negative-dir $(NEGATIVE_DIR) \
		--profile-id $(PROFILE_ID) \
		--limit $(SUBSET_LIMIT)
	$(PYTHON) -m pytest -q \
		tests/test_negative_corpus_diff_rate.py \
		tests/test_positive_docx_regression.py \
		tests/test_rules_quality_acceptance.py \
		tests/test_format_regression_audit.py \
		tests/test_profile_quality_acceptance.py \
		tests/test_methodical_extractor.py

.PHONY: compare-classical-acceptance
compare-classical-acceptance:
	$(PYTHON) -m src.main compare-classical \
		--output-dir results/reports/classical_zoo_$$(date +%Y%m%d_%H%M%S)/
	$(PYTHON) -m pytest tests/test_phase_8_sc2_acceptance.py -v
```

### 2.2 New Targets to Add — Recipe Shape

Adopt these conventions from the two existing targets:

| Convention | Value |
|------------|-------|
| Python variable | `$(PYTHON)` (from `PYTHON ?= python3` at top of file) |
| Recipe indent | **hard tab** (Makefile syntax requirement; space-indent silently breaks make) |
| Shell variable escape | `$$` inside recipe for shell-evaluated expressions (e.g., `$$(date ...)`) |
| `.PHONY` declaration | one line before each target |
| Sub-target chaining | sequential lines inside the recipe; if any step fails, make halts |
| Independent leaf targets | same name with `-sc1`, `-sc2`, `-sc3`, `-sc4` suffix |
| pytest invocation | `$(PYTHON) -m pytest <test-file> -v` (use `-v` for acceptance gates; `-q` for suites) |

### 2.3 Proposed New Target Skeleton

```makefile
.PHONY: milestone-acceptance-sc1
milestone-acceptance-sc1:
	$(PYTHON) -m pytest tests/test_milestone_acceptance_sc1.py -v

.PHONY: milestone-acceptance-sc2
milestone-acceptance-sc2:
	$(MAKE) compare-classical-acceptance
	$(PYTHON) -m pytest tests/test_milestone_acceptance_sc2_after_rules.py -v

.PHONY: milestone-acceptance-sc3
milestone-acceptance-sc3:
	$(MAKE) regression-gate

.PHONY: milestone-acceptance-sc4
milestone-acceptance-sc4:
	$(PYTHON) -m pytest tests/test_milestone_acceptance_sc4.py -v

.PHONY: milestone-acceptance
milestone-acceptance: milestone-acceptance-sc3 milestone-acceptance-sc1 milestone-acceptance-sc2 milestone-acceptance-sc4

.PHONY: milestone-smoke
milestone-smoke:
	$(PYTHON) -m pytest tests/test_milestone_acceptance_sc1.py -v -k "fast_tier"
	$(MAKE) compare-classical-acceptance
	$(MAKE) regression-gate
	$(PYTHON) -m pytest tests/test_streamlit_smoke.py -v
```

**Sub-target order rationale (Claude's Discretion area):** SC-3 (`regression-gate`)
is the cheapest existing gate (~1-2 min). Running it first short-circuits the full
corpus run (SC-1, 20-60 min) if the regression baseline is broken. Recommended order
in the chain: SC-3 → SC-1 → SC-2 → SC-4.

---

## 3. CLI Invocation Reference

### 3.1 The SC-1 Pipeline

The CLI does NOT have a single end-to-end command. The application service
`src/inference/application_service.py::process_document()` is the correct
abstraction that wires the full chain in one call.

[VERIFIED: `src/inference/application_service.py` lines 233-284]

```python
from src.inference.application_service import process_document

artifacts = process_document(
    input_path="tests/fixtures/corpus/positive/1.docx",
    model_choice="baseline",          # resolves latest svm_block_classifier_*.joblib
    mode="fix",                       # "fix" → apply_safe=True; "audit" → apply_safe=False
    profile_path="rules/gost_7_32_2017.json",
)
# artifacts.report_csv   — Path to CSV report
# artifacts.output_docx  — Path to corrected DOCX (None if mode="audit")
```

**What gets emitted per fixture (mode="fix"):**

| Artifact | Location |
|----------|----------|
| Extracted blocks | `results/extracted_blocks/<stem>_blocks_<ts>.csv` |
| Predictions | `results/predictions/<stem>_baseline_predictions_<ts>.csv` |
| Audit report CSV | `results/reports/<stem>_fix_audit_<ts>.csv` |
| Corrected DOCX | `results/formatted_docs/<stem>_baseline_formatted_<ts>.docx` |
| Report JSON | `results/reports/<stem>_fix_audit_<ts>.json` |
| Summary JSON | `results/reports/<stem>_fix_audit_<ts>_summary.json` |
| Summary TXT | `results/reports/<stem>_fix_audit_<ts>_summary.txt` |

### 3.2 Critical CLI Flags Note

The raw `audit-docx` subcommand (src/main.py lines 424-436) does NOT have
`--apply-safe` or `--audit-only` flags. The flag `--apply-safe` is on
`format-docx` only. [VERIFIED: src/main.py]

The SC-1 test should call `process_document()` directly (Python API), not the CLI,
for simplicity and to avoid subprocess overhead. Alternatively, invoke
`format-docx --apply-safe` via subprocess for true CLI-surface validation.

**`audit-docx` subparser flags (actual):**

```
--input-docx        required  Path to DOCX
--predictions-csv   required  Path to predictions CSV
--report-csv        optional  Output path (default: results/reports/<stem>_audit_<ts>.csv)
--profile-id        optional  default="gost_7_32_2017"
```

**`format-docx` subparser flags (actual, for SC-1 slow-tier if using raw CLI):**

```
--input-docx        required
--predictions-csv   required
--report-csv        optional
--output-docx       optional
--apply-safe        flag      If set → write corrected DOCX; else → audit report only
--profile-id        optional  default="gost_7_32_2017"
```

---

## 4. Production `after_rules` JSON Schema

**Source file:** `results/metrics/evaluation_20260506_083350.json`
[VERIFIED: file read, actual production file]

The SC-2 after-rules half asserts against the literal key path:

```
results/metrics/<svm_run>.json
  └── "after_rules"
        └── "weighted avg"
              └── "f1-score"        ← SC-2 gate: >= 0.94
        └── "macro avg"
              └── "f1-score"        ← SC-2 gate: >= 0.9414
```

**Actual values from production file `evaluation_20260506_083350.json`:**

```json
{
  "after_rules": {
    "weighted avg": {
      "precision": 0.9835660666194219,
      "recall":    0.9835225192237276,
      "f1-score":  0.9828743683772444,   ← weighted_f1 = 0.9829
      "support":   5462.0
    },
    "macro avg": {
      "precision": 0.9494554430637053,
      "recall":    0.9451480703952170,
      "f1-score":  0.9414208675319512,   ← macro_f1 = 0.9414
      "support":   5462.0
    }
  }
}
```

**Discovery logic in the test** (per 08-CONTEXT.md `specifics`):

```python
from pathlib import Path
METRICS_DIR = Path("results/metrics")
latest = sorted(METRICS_DIR.glob("evaluation_*.json"), reverse=True)[0]
```

**Skip condition:** If no `evaluation_*.json` exists, the test should
`pytest.skip("No evaluation metrics found — run 'python -m src.main train' first")`
(conservative approach, per 08-CONTEXT.md Claude's Discretion).

---

## 5. `/gsd-audit-uat` Aggregate Surface

### 5.1 Command That Exists

```bash
node ~/.claude/get-shit-done/bin/gsd-tools.cjs audit-uat --json
```

[VERIFIED: `gsd-tools.cjs` line 778 + `lib/uat.cjs` full read]

There is NO `audit.uat-aggregate` query key. The GSD SDK exposes:
- `gsd-sdk query audit-uat` (or equivalently the cjs invocation above)

### 5.2 Actual JSON Output Shape

The tool scans `*-UAT.md` and `*-VERIFICATION.md` files across all milestone
phase directories. It returns non-passing items only (pending / skipped / blocked
from UAT files; human_needed / gaps_found from VERIFICATION files).

```json
{
  "results": [
    {
      "phase": "05",
      "phase_dir": "05-rule-profiles-...",
      "file": "05-VERIFICATION.md",
      "file_path": ".planning/phases/05-.../05-VERIFICATION.md",
      "type": "verification",
      "status": "human_needed",
      "items": [
        {
          "test": 1,
          "name": "...",
          "result": "human_needed",
          "category": "human_uat"
        }
      ]
    }
  ],
  "summary": {
    "total_files": 2,
    "total_items": 6,
    "by_category": {"human_uat": 6},
    "by_phase": {"05": 2, "06": 4}
  }
}
```

**Critical gap:** The tool does NOT produce `open_critical_count` or
`open_high_count` fields. The output is category-based, not severity-based.

### 5.3 SC-4 Assertion Gap Analysis

08-CONTEXT D-C-02 specifies:
> "asserts the returned `open_critical_count == 0` and `open_high_count == 0`"

The audit-uat tool does not track severity. The current actual output maps UAT
item status to `category` values: `pending`, `blocked`, `human_uat`,
`skipped_unresolved`, etc.

**Live state from actual run:** The current `audit-uat --json` returns 6
non-passing items from Phases 5 and 6 VERIFICATION files (human_uat category).
These represent unwalked manual verification steps, not critical bugs.

### 5.4 Recommended Approach for SC-4 Test

**Option A (direct file-read, simpler):** `test_milestone_acceptance_sc4.py`
reads `08-DESIGN-REVIEW-ROLLUP.md` and asserts it contains the signed-off
verdict strings from all three phase records; then reads `07-UAT.md` frontmatter
and asserts `status: complete`; then reads `09-03-SUMMARY.md` and asserts UAT
8/8 pass. No SDK invocation.

**Option B (SDK-based, as locked in D-C-02):** Invoke `audit-uat --json`, parse
the result, and assert `summary.total_items == 0` (no non-passing items) at
close-of-phase — meaning all VERIFICATION files must be updated to `complete` or
removed. This is the mechanized assertion approach but requires that all open
VERIFICATION items (currently 6 in phases 05/06) are either resolved or the
VERIFICATION files updated before Phase 8 runs.

**Proposed CJS handler (if planner chooses Option B with a richer severity model):**

```javascript
// .planning/tools/uat_aggregate.cjs
// Usage: node .planning/tools/uat_aggregate.cjs --json
// Wraps audit-uat and adds severity-based counts derived from item.category.
// critical = items with category "blocked" where blocked_by implies data loss
// high     = items with category "pending" or "gaps_found"
// Returns: { open_critical_count, open_high_count, total_items, raw }
```

**Planner decision required (OQ-1 below).** For now, Option A (direct file-read
assertions) is the lowest-risk approach given the tool's actual output schema.

---

## 6. `pytest.mark.slow` Registration

### 6.1 Current State

`pytest.mark.slow` is used in `tests/test_compare_classical_acceptance.py` line
100 (decorates `test_per_model_metric_floor`). [VERIFIED: file read + actual
PytestUnknownMarkWarning confirmed by running pytest --collect-only]

No `pyproject.toml`, `pytest.ini`, or `setup.cfg` exists in the repo root.
[VERIFIED: all three paths return NONE_FOUND]

The warning is:
```
PytestUnknownMarkWarning: Unknown pytest.mark.slow - is this a typo?
```

### 6.2 Registration Options

**Option A — `pyproject.toml` (recommended):**
Adds project metadata capability at the same time. Since D-D-04 explicitly
states "NO `pyproject.toml` version bump — repository has no `pyproject.toml`",
and the intent is to stay tag-only, this is a boundary call. However,
`pyproject.toml` is not solely a packaging file — it can exist just for tool
configuration. Minimal `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
```

**Option B — `pytest.ini` (zero risk to D-D-04):**
`pytest.ini` cannot be confused with a version file. Simplest possible form:

```ini
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
```

**Option C — `conftest.py` (no new file):**
Add to `tests/conftest.py` (already exists, already imports pytest):

```python
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
```

**Recommendation:** Option B (`pytest.ini`) because:
- Zero risk of conflicting with D-D-04 pyproject.toml concerns
- No change to existing `tests/conftest.py` (CLAUDE.md: don't modify working code
  without explicit request)
- `pytest.ini` is the conventional pytest-first config choice
- Suppresses the warning with a 2-line file

**Location:** `pytest.ini` at repo root alongside `Makefile`.

**`-m` usage in Makefile smoke target:**

```makefile
milestone-smoke:
	$(PYTHON) -m pytest tests/test_milestone_acceptance_sc1.py -v -k "fast_tier" -m "not slow"
```

---

## 7. CHANGELOG.md Per-Phase Source Map

### 7.1 Format Decision (from 08-CONTEXT D-D-02)

Keep-a-Changelog 1.1.0 structure, but replacing per-section Added/Changed/Removed
buckets with per-phase subsections. Top-level:

```
## [v1.0] — YYYY-MM-DD
### Phase N: <name> (<completion date>)
- bullet 1
- bullet 2
```

### 7.2 Source Map per Phase

[VERIFIED: ROADMAP.md full read; CONTEXT files for all phases; SUMMARY files confirmed present]

| Phase | Completion Date | Primary Source | What to Extract |
|-------|----------------|----------------|-----------------|
| Phase 1 | 2026-05-12 | `01-CONTEXT.md` SC+decisions + ROADMAP Phase 1 summary | Style guard (body_text on Heading/TOC blocked); 67 INFERRED edges audited; cohesion 0.06 → improved |
| Phase 2 | 2026-05-12 | `02-CONTEXT.md` decisions + ROADMAP Phase 2 summary | Bibliography title override; single numId enforcement; ambiguous lists → review |
| Phase 3 | 2026-05-13 | `03-CONTEXT.md` decisions + ROADMAP Phase 3 summary | 18-key heading signature; per-field source dispatcher (inherited → review, direct → fix); D-08 scope reduction noted |
| Phase 4 | 2026-05-14 | `04-CONTEXT.md` + ROADMAP Phase 4 summary line | Per-pair diff-rate baseline JSON; `make regression-gate`; GHA gate validated; rules quality acceptance test |
| Phase 5 | 2026-05-14 | `05-CONTEXT.md` + ROADMAP Phase 5 summary | Per-leaf `_source` annotation; profile_diff; extract-methodical-profile rewrite (dry-run + --apply + audit trail); two-tier schema lint; 6-file CI gate |
| Phase 6 | 2026-05-15 | `06-CONTEXT.md` + `06-05-SUMMARY.md` | UI rebuilt (sidebar → audit flow); RunLog PII boundary; STATUS_CHIP; render_report sections; methodical modal @st.dialog; design-review approved |
| Phase 7 | 2026-05-15 | `07-UAT.md` + `07-CONTEXT.md` + `07-05-SUMMARY.md` | PDF text-layer accepted (no OCR); read-only audit; PDF path bypasses SVM; 5 gap-closure commits; UAT 7/7 pass |
| Phase 9 | 2026-05-16 | `09-03-SUMMARY.md` + `09-CONTEXT.md` D-E-05 | 6-model classical zoo (LR/SVM/SVM-prod/NB/RF/HistGBM+SVD256); `compare-classical` CLI; dual-source SC-2 gate; UAT 8/8 approved |

**Bullet density guidance (Claude's Discretion):** 2-3 bullets per phase. Each
bullet = one locked truth tied to a success criterion or ROADMAP decision. Do
not list plan-level implementation details. Use present tense ("Stops X",
"Enforces Y").

**Date format:** Match ROADMAP format: `2026-05-12`.

### 7.3 CHANGELOG Structure Sketch

```markdown
# Changelog

## [v1.0] — 2026-05-16

### Phase 9: Classical model zoo (2026-05-16)
- Adds `compare-classical` CLI scoring six classifier pipelines
  (LR, LinearSVC, LinearSVC-production, ComplementNB, RandomForest, HistGBM+SVD256)
  on the locked `annotations_test.csv` held-out set.
- `linear_svm_production` row clears dual-source Phase 8 SC-2 floor:
  raw-ML `weighted_f1 ≥ 0.94 / macro_f1 ≥ 0.86`; after-rules `weighted_f1 ≥ 0.94 / macro_f1 ≥ 0.9414`.

### Phase 7: PDF text-layer audit slice (2026-05-15)
...

### Phase 1: Engine guardrails & cohesion audit (2026-05-12)
...
```

Note: Phases listed newest-first matches Keep-a-Changelog convention (newest
release at top), but within the v1.0 block, the sub-sections may go oldest-first
(Phase 1 → Phase 9) for narrative clarity. Planner to decide.

---

## 8. Streamlit Headless Smoke Pattern

### 8.1 Requirements

Per 08-CONTEXT D-C-04:
- Boots `streamlit run app.py --server.headless=true --server.port 8501`
- Confirms HTTP 200 within 30s
- Clean shutdown after test
- Catches import-level syntax errors that pytest.importorskip misses

### 8.2 Reliable Pattern (subprocess.Popen + wait loop)

```python
import subprocess
import sys
import time
import socket
import os
import signal

import pytest
import requests

STREAMLIT_PORT = 8502  # Use 8502 not 8501 to avoid conflict with running dev instance


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


@pytest.fixture(scope="module")
def streamlit_process():
    requests_mod = pytest.importorskip("requests")
    _ = requests_mod  # used below

    if not _port_free(STREAMLIT_PORT):
        pytest.skip(f"Port {STREAMLIT_PORT} already in use — cannot launch headless Streamlit")

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "true",
            "--server.port", str(STREAMLIT_PORT),
            "--server.runOnSave", "false",
            "--logger.level", "error",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    deadline = time.monotonic() + 30
    started = False
    while time.monotonic() < deadline:
        try:
            r = requests.get(f"http://127.0.0.1:{STREAMLIT_PORT}", timeout=2)
            if r.status_code == 200:
                started = True
                break
        except Exception:
            time.sleep(0.5)

    if not started:
        proc.terminate()
        proc.wait(timeout=5)
        pytest.fail("Streamlit did not start within 30s")

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def test_streamlit_boots_to_200(streamlit_process):
    import requests
    r = requests.get(f"http://127.0.0.1:{STREAMLIT_PORT}", timeout=5)
    assert r.status_code == 200
```

### 8.3 Port Handling

**Recommended:** Use port `8502` (not 8501) to avoid conflicts with any
developer-running Streamlit instance. Check port freedom before launch.
Dynamic free-port discovery is more robust but adds complexity; given the 30s
budget and the CI-environment assumption, a fixed secondary port (`8502`) is
sufficient.

If 8502 is also taken, `pytest.skip()` is the right action (not `pytest.fail()`),
since CI port availability is an environment concern, not a code defect.

### 8.4 Teardown

`proc.terminate()` sends SIGTERM to the Streamlit process. On Windows,
`proc.terminate()` sends `CTRL_BREAK_EVENT` or terminates the process handle.
`proc.wait(timeout=5)` prevents zombie processes. If wait times out, fall back
to `proc.kill()`.

**Windows note:** The process group may spawn a child watcher thread. On CI
(Linux), this is handled. On Windows CI, use `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`
if CTRL+C propagation issues appear — but this is a CI-edge concern, not
Day-1 blocker.

### 8.5 Upload-Type Contract Assertion (from D-C-04)

```python
def test_streamlit_app_upload_contract():
    """D-C-04: app.SUPPORTED_UPLOAD_TYPES mirrors Phase 7 D-04 §3 contract."""
    import importlib, sys
    # Use importorskip so the test is skipped cleanly on no-streamlit CI
    pytest.importorskip("streamlit")
    # Remove cached module if already imported
    if "app" in sys.modules:
        del sys.modules["app"]
    import app
    assert app.SUPPORTED_UPLOAD_TYPES == ["docx", "pdf"]
```

This assertion does NOT need the headless server. It can run independently in
the fast tier without the 30s boot wait.

---

## 9. Pitfalls

**P1 — `audit-docx` CLI vs `format-docx --apply-safe`:**
The `audit-docx` subcommand has no `--apply-safe` flag (it is always audit-only).
`--apply-safe` belongs to `format-docx`. SC-1's per-fixture run must use
`format-docx --apply-safe` if testing corrected DOCX emission, or
`process_document(mode="fix")` from the Python API. Using `audit-docx` produces
a report CSV but never an `output_docx`.

**P2 — SC-2 after-rules metric source is NOT the zoo CSV:**
The `0.9414` macro_f1 floor in SC-2(b) reads from `results/metrics/evaluation_*.json`
(produced by `python -m src.main train` → `python -m src.main evaluate`).
It is NOT derived from the zoo's `classical_zoo_<ts>/results.csv`. Confusing
these two sources is the primary SC-2 design risk. The zoo CSV contains raw-ML
metrics with floor 0.86; the metrics JSON contains after-rules metrics with floor
0.9414. Both must pass.

**P3 — `audit-uat --json` does not emit `open_critical_count`:**
The tool (lib/uat.cjs) returns items keyed by `category` (pending, blocked,
human_uat, etc.), not by severity (critical, high). The SC-4 test assertion
`open_critical_count == 0` from 08-CONTEXT D-C-02 cannot be implemented by
passing the tool's raw output through a `json.loads()` and checking a key.
The test must either (a) assert `summary.total_items == 0` or (b) assert the
ROLLUP document content directly. See Section 5.4.

**P4 — Open VERIFICATION items in Phases 05/06 will cause SC-4 to fail if using
total_items == 0:**
The current `audit-uat --json` returns 6 non-passing items from phase 05 and 06
VERIFICATION files (human_uat category). These are unwalked manual verification
steps, not blocked UAT tests. Before SC-4 can pass with `total_items == 0`,
these VERIFICATION files must be updated to reflect that their manual steps
are now superseded by the ROLLUP or marked complete. This is a Wave 0 setup task.

**P5 — `06-DESIGN-REVIEW.md` is not signed off:**
Reading the file confirms the design-review sign-off section has blank fields
(Reviewer / Date / Final status are all empty). The Phase 6 UAT (VERIFICATION
file) reflects this. The rollup `08-DESIGN-REVIEW-ROLLUP.md` must synthesise
what is actually known (06-05-SUMMARY shows "approved-with-followups" informally)
and get a formal sign-off if required. If the planner treats this as already
approved-with-followups (per SUMMARY), the ROLLUP records that and SC-4 passes
on the ROLLUP alone.

**P6 — `make milestone-smoke` must use `-m "not slow"` or `-k "fast_tier"`, not
run the full SC-1 corpus:**
The slow-tier corpus (20-60 min) must never land in the fast CI tier. The smoke
test and fast-tier SC-1 must use the 5MB subset
(`tests/fixtures/corpus/positive/{1,4}.docx` + `tests/fixtures/corpus/negative/{45.docx,...}`).

**P7 — `git tag -a v1.0` must be on the closing commit of Phase 8 (the commit
that lands `08-VERDICT.md` + `CHANGELOG.md`), not on the final plan-merge commit:**
If Phase 8 produces multiple commits (ROLLUP commit, then VERDICT+CHANGELOG commit),
the tag goes on the last commit. The planner's task that creates the tag must
run after the VERDICT+CHANGELOG commit, not before.

**P8 — `pytest.mark.slow` warning is currently live:** Until `pytest.ini` (or
equivalent) is added, every `pytest` invocation emits a PytestUnknownMarkWarning.
This does not fail tests but is noise. Adding `pytest.ini` in Wave 0 cleans this
before SC-2 test file is added.

**P9 — No `compare-classical` zoo artifact exists until `make compare-classical-acceptance`
runs:**
`test_phase_8_sc2_acceptance.py` (Phase 9) and the proposed SC-2 after-rules test
both `pytest.skip` gracefully when their source files are absent. The milestone-
acceptance operator must run `make compare-classical-acceptance` first (or ensure
the zoo artifact is present from Phase 9 close). The VERDICT template should include
a pre-flight checklist item for this.

---

## 10. Open Questions

**OQ-1 — SC-4 assertion mechanism (planner must decide):**
- Option A: `test_milestone_acceptance_sc4.py` reads ROLLUP + UAT/VERIFICATION
  files directly (no SDK call). Simpler. More resilient to tool output changes.
- Option B: Invokes `audit-uat --json` and asserts `summary.total_items == 0`
  (requires all VERIFICATION files updated to complete before Phase 8 close).
- Recommendation: Option A for the direct assertions; Option B as an additional
  check if the planner wants SDK coverage. Severity-based counts (`open_critical_count`)
  require a custom CJS handler (proposed in Section 5.4) or can be dropped in
  favour of direct file-read checks.

**OQ-2 — `make milestone-acceptance` sub-target order:**
08-CONTEXT leaves this to the planner. Recommendation (Section 2.3): SC-3 first
(cheapest, fast fail), then SC-1 (slow corpus), then SC-2, then SC-4. Planner
must confirm.

**OQ-3 — `08-VERDICT.md` template:**
No existing template in `$HOME/.claude/get-shit-done/templates/`. The planner
should produce the template inline in Wave 0. Suggested structure (mirrors
06-DESIGN-REVIEW.md verdict-checklist style):

```markdown
---
phase: 08-milestone-acceptance
verdict_date: YYYY-MM-DD
status: PASS | FAIL
milestone: v1.0
---

# Milestone v1.0 Acceptance Verdict

## SC-1: End-to-end corpus run
Status: PASS | FAIL
Metric: <fixtures processed> / <total>, 0 crashes
Artifact: results/reports/<stem>_*_audit_<ts>.csv

## SC-2: ML quality dual-source
...

## SC-3: Negative-corpus regression
...

## SC-4: Design-review consolidation
...

## Open follow-ups (Deferred to v1.1)
- [999.1] ui-tabbed-layout-restoration
- [999.2] docx-formatting-bugs-list-indent-formula-vars

## Sign-off
Date: YYYY-MM-DD
```

**OQ-4 — Whether to re-run `python -m src.main train` inside SC-2:**
08-CONTEXT recommends conservative approach: read the latest existing
`results/metrics/evaluation_*.json`. If none exists, `pytest.skip`. This avoids
including a training run (~several minutes) inside the acceptance test. Planner
should confirm the conservative approach.

**OQ-5 — CHANGELOG phase ordering (newest-first vs oldest-first within v1.0 block):**
Keep-a-Changelog convention is newest-at-top (Phase 9 before Phase 1).
But narrative reads more naturally oldest-first. Planner picks; both are valid.

---

## Sources

- `Makefile` — regression-gate and compare-classical-acceptance targets [VERIFIED]
- `src/main.py` — CLI subparser definitions for audit-docx, format-docx, compare-classical [VERIFIED]
- `src/inference/application_service.py` — `process_document()` API [VERIFIED]
- `results/metrics/evaluation_20260506_083350.json` — after_rules block key structure [VERIFIED]
- `.planning/phases/08-milestone-acceptance/08-CONTEXT.md` — locked decisions D-A-01..D-D-04, SC traceback [VERIFIED]
- `.planning/phases/09-classical-model-zoo-.../09-CONTEXT.md` — D-E-05 dual-source design [VERIFIED]
- `.planning/phases/09-classical-model-zoo-.../09-03-SUMMARY.md` — UAT 8/8 approved record [VERIFIED]
- `.planning/phases/06-streamlit-ui-redesign/06-DESIGN-REVIEW.md` — unsigned sign-off state [VERIFIED]
- `.planning/phases/07-pdf-text-layer-audit-slice/07-UAT.md` — status=complete, 7/7 pass, 3 gaps resolved [VERIFIED]
- `~/.claude/get-shit-done/bin/lib/uat.cjs` — audit-uat JSON output schema [VERIFIED: code read + live run]
- `tests/test_compare_classical_acceptance.py` — pytest.mark.slow usage + PytestUnknownMarkWarning confirmed [VERIFIED]
- `tests/conftest.py` — existing fixtures (no pytest_configure mark registration) [VERIFIED]
- `tests/test_phase_8_sc2_acceptance.py` — Phase 9 standalone SC-2 gate pattern [VERIFIED]
- `.planning/ROADMAP.md` — per-phase completion dates and deliverable descriptions [VERIFIED]
- `.planning/config.json` — nyquist_validation key absent (treat as enabled) [VERIFIED]
