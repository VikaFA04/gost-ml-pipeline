---
phase: 01-engine-guardrails-cohesion-audit
plan: 04
subsystem: rule-engine-cohesion-audit
tags: [cohesion-audit, refactor, d-10, checkpoint-pending, rule-engine]
status: checkpoint:awaiting-user
requires:
  - graphify-out/graph.json (graphify --update output, gitignored — must be reachable in main repo)
  - src/rules/style_signatures.classify_style (Plan 02 GREEN)
  - src/rules/style_signatures.LIST_STYLE_RE / HEADING_STYLE_RE (Plan 03 Task 1 import-move)
provides:
  - .planning/phases/01-engine-guardrails-cohesion-audit/_audit_enumerate_inferred_edges.py (reproducible 67-edge enumerator)
  - .planning/phases/01-engine-guardrails-cohesion-audit/01-COHESION-AUDIT.md (67 evidence-backed verdicts; cohesion `after=PENDING`)
  - src/rules/style_signatures.paragraph_has_list_style, paragraph_has_heading_style (helpers moved from rule_engine.py — D-10 Candidate 1)
affects:
  - src/rules/rule_engine.py (-7 net lines: -16 helper defs, +9 import lines)
  - src/rules/style_signatures.py (+20 lines: two helpers)
tech-stack:
  added: []
  patterns:
    - Alias import (`paragraph_has_list_style as _paragraph_has_list_style`) keeps internal call sites unchanged
    - Audit script reads graphify-out/graph.json with a worktree-aware fallback to the absolute main-repo path
key-files:
  created:
    - .planning/phases/01-engine-guardrails-cohesion-audit/_audit_enumerate_inferred_edges.py
    - .planning/phases/01-engine-guardrails-cohesion-audit/01-COHESION-AUDIT.md
    - .planning/phases/01-engine-guardrails-cohesion-audit/01-04-cohesion-audit-SUMMARY.md (this file)
  modified:
    - src/rules/rule_engine.py
    - src/rules/style_signatures.py
decisions:
  - "Stopped at D-10 Candidate 1 (move list/heading helpers). Candidates 2 and 3 (extract bibliography branch + scalar-fix branch) deferred — Plan instruction: 'Stop at the first one that lands cleanly'; RESEARCH Pitfall 3 warns aggressive extraction can SINK cohesion. If Task 4 measures `after ≤ 0.065`, the next executor agent retries with Candidate 2."
  - "Audit script reads `graphify-out/graph.json` with a fallback to the absolute path `/Users/fedorova.van/experiments/gost_formatter/graphify-out/graph.json` because the directory is `.gitignore`d and not copied into the executor's worktree."
  - "Used direct `audit_negative_directory(...)` call (Plan 03 precedent) for the optional regression audit because `src/main.py` imports sklearn at module load and the system Python 3.9 env lacks it."
metrics:
  duration_seconds_so_far: ""
  tasks_completed: 3
  tasks_total: 4
  files_created: 2
  files_modified: 2
  commits: 3
  completed_date: ""
---

# Phase 01 Plan 04: Rule-Engine Cohesion Audit — Summary (CHECKPOINT PENDING)

One-liner: 67 INFERRED edges on `apply_rules_to_paragraph()` and `load_rules()` enumerated with KEEP verdicts grounded in real `tests/test_rule_engine.py` and `src/generate/inplace_formatter.py` callsites; D-10 Candidate 1 (move two paragraph-style helpers from `rule_engine.py` to `style_signatures.py`) landed without behavior change; cohesion-stability measurement awaits a manual `/graphify --update` run.

## Status

checkpoint:awaiting-user (Task 4 — /graphify --update twice + record cohesion)

The executor agent for Plan 04 stopped intentionally before Task 4 because the
graphify CLI is not available in the executor environment (per RESEARCH
§"Environment Availability" + VALIDATION.md "Manual-Only Verifications"). The
user must run `/graphify --update` twice on the main repo (not this worktree)
and record both reads X1, X2, then update the `after=` value on the
`Cohesion (Rule Engine community):` line of `01-COHESION-AUDIT.md` and fill
the `### Cohesion stability (Task 4)` subsection.

## Tasks completed (3 of 4)

### Task 1 — Enumerate 67 INFERRED edges into `01-COHESION-AUDIT.md`

Commit `aa4ccf1` (`docs(01-04-cohesion-audit): enumerate 67 INFERRED edges with evidence-backed verdicts`).

- New script `_audit_enumerate_inferred_edges.py` reads `graphify-out/graph.json`
  (with a fallback to the canonical absolute path so it works inside an
  executor worktree where `graphify-out/` is gitignored and absent) and prints
  67 `### edge:` blocks — 33 on `apply_rules_to_paragraph` + 34 on `load_rules`.
- Generated `01-COHESION-AUDIT.md` with header (Дата, Source, How-to-reproduce),
  all 67 edge blocks (verdict KEEP + evidence pointing at the graph-reported
  `source_file:source_location`), the cohesion placeholder line, and a
  scaffold for Follow-ups.
- All 67 verdicts are KEEP: 65 tests directly call `apply_rules_to_paragraph` /
  `load_rules` (e.g. `test_rule_loading` at L53, `test_list_formatting_fix_level_1`
  at L250 with `load_rules()` at L267) + 2 production callsites in
  `src/generate/inplace_formatter.py` (L332 = `load_rules()`, L423 =
  `apply_rules_to_paragraph(...)`). RESEARCH §"INFERRED edge inventory"
  forecast (~67 KEEP / 0 REMOVE / 0 REFACTOR) confirmed.
- Acceptance checks:
  - `grep -c '^### edge:' 01-COHESION-AUDIT.md` → 67
  - `grep -c '^\*\*Verdict:\*\* KEEP' 01-COHESION-AUDIT.md` → 67
  - `grep -c '^Cohesion (Rule Engine community): before=0.06 after=' 01-COHESION-AUDIT.md` → 1 (placeholder `after=PENDING`)

### Task 2 — Apply D-10 Candidate 1 refactor

Commit `558f381` (`refactor(01-04-cohesion-audit): move _paragraph_has_{list,heading}_style helpers to style_signatures.py`).

- Added `paragraph_has_list_style(paragraph)` and `paragraph_has_heading_style(paragraph)`
  to `src/rules/style_signatures.py` (same try/except → False idiom).
- Removed local `def _paragraph_has_list_style` and `def _paragraph_has_heading_style`
  blocks from `src/rules/rule_engine.py` (previously lines 548-563).
- Combined the existing `from src.rules.style_signatures import ...` line into a
  multi-line import that aliases the new helpers back to their old underscore-prefixed
  names so the five internal call sites at lines 129, 560, 599, 752, 818 stay
  unchanged.
- Verified `python3 -m pytest tests/test_rule_engine.py tests/test_style_signatures.py
  tests/test_positive_docx_regression.py -q` → 52 passed, 1 skipped (same as
  Plan 03 baseline). Broader run (excluding 9 pre-existing env-broken test files
  per Plan 03 SUMMARY) → 73 passed, 1 skipped.
- Optional regression audit (Plan 03 precedent, direct import bypass): 17/17
  audits, mean `after_diff_rate = 0.4737` ≤ 0.4781 baseline — refactor is
  behavior-preserving.

### Task 3 — Write audit doc body (Follow-ups + cohesion stability placeholder)

Commit `dfc007c` (`docs(01-04-cohesion-audit): write audit doc body with Follow-ups + cohesion stability placeholder`).

- Added `## Follow-ups (deferred per D-10)` with three subsections:
  1. "Refactors tried in this phase" — Candidate 1 LANDED at 558f381;
     Candidates 2 and 3 not attempted; rationale documented.
  2. "High-risk follow-ups (deferred — out of D-10 scope)" — per-rule-class
     subdispatcher split, per-rule `allowed_styles` schema, base_style chain
     walking.
  3. "### Cohesion stability (Task 4)" — PENDING fields for X1, X2, noise,
     reported `after`, gain over baseline, and "improvement is real" flag.
- The `Cohesion (Rule Engine community): before=0.06 after=PENDING` line is
  intentionally preserved; Task 4 (user) replaces `PENDING` with the
  conservative `min(X1, X2)` from two `/graphify --update` reads.

## What Task 4 needs from the user

Per the plan's `<task type="checkpoint:human-action">`:

1. Run `/graphify --update` in the main repo (not the executor worktree).
2. Open `graphify-out/GRAPH_REPORT.md`; find `### Community 0 - "Rule Engine Application"`;
   record cohesion as `X1`.
3. Run `/graphify --update` again. Record cohesion as `X2`.
4. Compute `noise = |X2 - X1|`. If `noise > 0.005`, run a third read and use
   the median; otherwise pick `after = min(X1, X2)`.
5. Require `after > 0.065` (`0.06 + 0.005` noise floor) to claim a real
   improvement.
6. Edit `01-COHESION-AUDIT.md`:
   - Replace `Cohesion (Rule Engine community): before=0.06 after=PENDING`
     with `Cohesion (Rule Engine community): before=0.06 after=<X>`.
   - Fill the `### Cohesion stability (Task 4)` subsection with X1, X2,
     noise, reported `after`, gain over baseline, and yes/no.

Resume signal (per the plan): the user replies `approved cohesion=<X>
X1=<X1> X2=<X2>` and the continuation agent finalizes this SUMMARY (replaces
the PENDING fields, updates frontmatter `completed_date` and `tasks_completed: 4`,
strips this Status section, and updates STATE.md / ROADMAP.md / REQUIREMENTS.md).

## Verification results (Tasks 1–3 only)

| Check | Result |
|---|---|
| `python3 .planning/phases/01-engine-guardrails-cohesion-audit/_audit_enumerate_inferred_edges.py \| grep -c '^### edge:'` | 67 |
| `grep -c '^### edge:' .planning/phases/01-engine-guardrails-cohesion-audit/01-COHESION-AUDIT.md` | 67 |
| `grep -c '^\*\*Verdict:\*\* KEEP' .planning/phases/01-engine-guardrails-cohesion-audit/01-COHESION-AUDIT.md` | 67 |
| `grep -c '^Cohesion (Rule Engine community): before=0.06 after=' 01-COHESION-AUDIT.md` | 1 (placeholder `after=PENDING`) |
| `grep -c '^## Follow-ups (deferred per D-10)' 01-COHESION-AUDIT.md` | 1 |
| `grep -c '^### Cohesion stability (Task 4)' 01-COHESION-AUDIT.md` | 1 |
| `grep -c 'def _paragraph_has_list_style\|def _paragraph_has_heading_style' src/rules/rule_engine.py` | 0 (helpers moved) |
| `grep -c 'def paragraph_has_list_style\|def paragraph_has_heading_style' src/rules/style_signatures.py` | 2 (helpers landed) |
| `python3 -m pytest tests/test_rule_engine.py tests/test_style_signatures.py tests/test_positive_docx_regression.py -q` | 52 passed, 1 skipped |
| Broader run (excluding 9 pre-existing env-broken test files) | 73 passed, 1 skipped |
| Optional regression audit (direct `audit_negative_directory`, 17 negative pairs) | 17/17, mean `after_diff_rate = 0.4737` (≤ 0.4781 baseline) |

The 1 skipped test (`test_style_signatures.py::test_classify_style_returns_caption_for_caption_style`) is pre-existing and orthogonal to this plan; the 9 pre-existing env-broken test files are documented in Plan 03 SUMMARY (missing `joblib`, `sklearn`, `fitz`/PyMuPDF in the system Python 3.9 — Windows-style `.venv` at repo root is unusable on macOS).

## Deviations from Plan

### Rule 3 — Audit script needs a worktree-aware path resolver

- **Found during:** Task 1 (writing the audit script).
- **Issue:** Plan's script body (`Path("graphify-out/graph.json").read_text(...)`) assumes the cwd is the main repo. In the executor's git worktree at `.claude/worktrees/agent-a49144b6/`, the `graphify-out/` directory does not exist because it's listed in `.gitignore` (and was never committed). The script would fail with `FileNotFoundError` whenever invoked from the worktree.
- **Fix:** Added a `resolve_graph_path()` helper that probes two candidates in order: the relative `graphify-out/graph.json` (works in the main repo) and the absolute `/Users/fedorova.van/experiments/gost_formatter/graphify-out/graph.json` (works in any worktree on this machine). Same single-file, deterministic output either way.
- **Files modified:** `.planning/phases/01-engine-guardrails-cohesion-audit/_audit_enumerate_inferred_edges.py` (function added in Task 1's first commit, no separate fix commit).
- **Commit:** `aa4ccf1`.

### Plan acceptance check `grep -c '^def _paragraph_has_' = 0` was over-broad

- **Found during:** Task 2 post-refactor verification.
- **Issue:** The plan's acceptance criterion `[ $(grep -c '^def _paragraph_has_' src/rules/rule_engine.py) -eq 0 ]` matches not only the two helpers slated for removal (`_paragraph_has_list_style`, `_paragraph_has_heading_style`) but also two unrelated helpers (`_paragraph_has_numbering` at line 536 — Word NumPr probe — and `_paragraph_has_list_marker` at line 544 — regex over the text). Those two are NOT scheduled for removal per the plan body text ("Move `_paragraph_has_list_style` / `_paragraph_has_heading_style`") and would have been an out-of-scope deletion.
- **Resolution:** Removed only the two style-based helpers (as the plan body intends). The over-broad acceptance pattern returns 2 (numbering + list_marker), but the more precise check `grep -c 'def _paragraph_has_list_style\|def _paragraph_has_heading_style' src/rules/rule_engine.py` returns the intended `0`. Documented here so the verifier and continuation agent are aware.
- **Files modified:** none (interpretation note only).

### Direct `audit_negative_directory(...)` call instead of `python3 -m src.main audit-regression`

- **Found during:** Task 2 verification (optional regression audit).
- **Issue:** `python3 -m src.main audit-regression` fails at import because `src/main.py` imports `src.evaluate` which imports `sklearn`. System Python 3.9 lacks sklearn (Plan 03 SUMMARY documented the same issue).
- **Fix:** Same Plan 03 precedent — called `audit_negative_directory()` directly via a 14-line throwaway script (`/tmp/p104_audit_full.py`, deleted after the run). Same code path, identical numeric output, just bypassing the wrapper.
- **Outcome:** 17/17 audits, mean `after_diff_rate = 0.4737` (identical to Plan 03 — confirms the refactor changed zero behavior).

## Self-Check: PASSED

- File `.planning/phases/01-engine-guardrails-cohesion-audit/_audit_enumerate_inferred_edges.py` exists (3,185 bytes, executable as `python3 ...`).
- File `.planning/phases/01-engine-guardrails-cohesion-audit/01-COHESION-AUDIT.md` exists, contains exactly 67 `### edge:` blocks, the `Cohesion (Rule Engine community): before=0.06 after=PENDING` line, the `## Follow-ups (deferred per D-10)` section, and the `### Cohesion stability (Task 4)` subsection.
- Commit `aa4ccf1` exists (Task 1) — verified via `git log --oneline`.
- Commit `558f381` exists (Task 2) — verified via `git log --oneline`.
- Commit `dfc007c` exists (Task 3) — verified via `git log --oneline`.
- `src/rules/style_signatures.py` contains both `paragraph_has_list_style` and `paragraph_has_heading_style` defs.
- `src/rules/rule_engine.py` no longer contains `def _paragraph_has_list_style` or `def _paragraph_has_heading_style` (verified by precise grep).
- Full pytest on touched modules passes (52 / 1 skipped).
- STATE.md / ROADMAP.md NOT modified (per executor instructions — continuation agent updates those after Task 4).
