---
phase: 04-regression-gate
plan: 01
subsystem: testing
tags: [regression-gate, audit-regression, git-bisect, baseline, D-05]

# Dependency graph
requires:
  - phase: 02-bibliography-and-list-semantics
    provides: Phase 2 D-05/D-06 numId coercion + multilevel numbering (one of the bisect probe points)
  - phase: 03-heading-signature-and-docx-generator
    provides: Phase 3 D-05/D-06 per-field heading source routing (commit 7207cbe — the root cause Wave A identified)
provides:
  - 04-WAVE-A-3docx-rootcause.md (D-05 Branch B declaration + locked ceilings + 4-doc subset)
  - results/reports/regression_audit_phase4_worst_offenders.csv (full-corpus audit, 18 pairs)
  - results/reports/regression_audit_phase4_worst_offenders.json (audit summary)
  - results/reports/3docx_style_diff_HEAD.txt (bisect trace + per-commit 3.docx after_diff_rate values)
affects: [04-02-PLAN (Wave B baseline JSON + conditional ROADMAP/REQUIREMENTS amendment), 04-03-PLAN, 04-04-PLAN, 04-05-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Suspicion-ranked git bisect (not blind) per RESEARCH.md Probe 3 — start at median high-suspect commit, fan out by ranking until one-commit-wide interval"
    - "Single-doc audit dir pattern: copy target pair into /tmp/.../<negative>.docx + use audit-regression with that as --negative-dir to avoid lexicographic --limit truncation"
    - "Negative-column subset_filenames pattern: audit_negative_directory returns 'negative' = formatted-DOCX filename, NOT the originating positive; Wave B baseline JSON dict keys must follow this convention"

key-files:
  created:
    - .planning/phases/04-regression-gate/04-WAVE-A-3docx-rootcause.md
    - results/reports/regression_audit_phase4_worst_offenders.csv
    - results/reports/regression_audit_phase4_worst_offenders.json
    - results/reports/3docx_style_diff_HEAD.txt
  modified: []

key-decisions:
  - "D-05 locked to Branch B (legit Phase 3 behaviour change, NOT bug fix) — root cause is sealed Phase 3 D-05/D-06 dispatcher, reverting would re-introduce field-level mismatches the dispatcher exists to fix"
  - "Locked Wave B baseline ceilings: after_diff_rate_ceiling=0.359712, field_mismatch_ceiling=630 (3.docx pair, negative=3_formatted_20260413_194927.docx)"
  - "4-doc subset for Wave B: 3_formatted_20260413_194927.docx + tmp5x0alx_2_baseline_formatted_20260506_091235.docx + tmp9dp7t40y_transformer_formatted_20260417_181218.docx + 4_formatted_20260413_185420.docx (excludes 58/59 per Phase 3 D-08)"
  - "Empirical sanity-stable floor is 0.163743 — RESEARCH.md target of ≤0.1 is not achievable in the current corpus net of 58/59"
  - "REQUIREMENTS.md REQ-fix-negative-corpus-no-regression line '3.docx pair returns to ≤ 0.318' is held UNTOUCHED at Wave A close — amendment is Wave B's atomic responsibility per Branch B"

patterns-established:
  - "Wave A → Wave B handoff via written artefact (not chat history); Wave B reads concrete ceiling values + subset filenames verbatim from 04-WAVE-A-3docx-rootcause.md"
  - "Bisect trace persistence: each probed SHA + 3.docx after_diff_rate appended to a single .txt audit file (results/reports/3docx_style_diff_HEAD.txt) — auditable per Wave A automated verify"

requirements-completed: []  # REQ-fix-negative-corpus-no-regression is NOT closed by Wave A — Wave A only investigates; Wave B closes it via baseline JSON + ROADMAP/REQUIREMENTS amendment per Branch B.

# Metrics
duration: ~80min
completed: 2026-05-13
---

# Phase 04 Plan 01: Wave A — 3.docx Root-Cause Investigation Summary

**Bisect-identified `7207cbe` (Phase 3 D-05/D-06 per-field heading source dispatcher) as the sole source of the +0.025307 drift since FORMAT_FIX_PLAN Этап 8; D-05 locked to Branch B with after_diff_rate_ceiling=0.359712 and field_mismatch_ceiling=630 for Wave B baseline JSON.**

## Performance

- **Duration:** ~80 min (Wave A investigation, including suspicion-ranked bisect over 4 commits + artefact writing)
- **Started:** 2026-05-13T19:35Z (per STATE.md `Planned Phase: 04 ... 19:33:26Z`)
- **Completed:** 2026-05-13 (Task 3 artefact committed `dd2db78`)
- **Tasks:** 3 (Task 1 audit, Task 2 bisect, Task 3 artefact + human-verify checkpoint approved)
- **Files modified:** 4 created, 0 modified

## Accomplishments
- Empirical 3.docx pair after_diff_rate at HEAD nailed down to **0.359712** (vs FORMAT_FIX_PLAN folklore of 0.334) — the +0.025 additional drift since Этап 8 is now data, not rumor.
- Suspicion-ranked bisect narrowed the drift to a **one-commit-wide interval**: `ac41aaa` (good) → `7207cbe` (drift). Single responsible commit identified.
- Root cause classified as **LEGITIMATE Phase 3 D-05/D-06 behaviour change**, not a bug — backed by code analysis showing the +0.003597 paragraph-level cost = 1/278 paragraphs flipping from "blanket-guard skip" to "D-06 direct-mismatch autofix" (field_mismatch_delta net-improved).
- **D-05 Branch B locked**: Wave B amends ROADMAP success criterion 2 + REQUIREMENTS REQ-fix-negative-corpus-no-regression atomically with baseline JSON write; ceiling values `after_diff_rate_ceiling=0.359712`, `field_mismatch_ceiling=630` recorded for verbatim consumption.
- 4-doc subset pinned for Wave B (negative-column filenames, 58/59 excluded per Phase 3 D-08) with the `negative` vs `positive` naming-convention gotcha documented so Wave B's `.isin(...)` filter matches correctly.

## Task Commits

Each task was committed atomically:

1. **Task 1: Full-corpus regression audit** — `c0904b4` (feat: full-corpus audit CSV + summary JSON, 18-pair enumeration, 58/59-excluded worst-offender ranking, 3.docx after_diff_rate=0.359712 nailed down)
2. **Task 2: Bisect 3.docx drift** — `5e9df74` (feat: suspicion-ranked bisect over 7207cbe → c4d67ac → 92fcfee → ac41aaa, drift PRESENT at 7207cbe only, working tree restored to HEAD)
3. **Task 3: Wave A artefact + D-05 Branch B declaration** — `dd2db78` (docs: 04-WAVE-A-3docx-rootcause.md with empirical datapoints, bisect trace table, root-cause analysis citing Phase 3 D-05/D-06, Branch B decision, locked ceilings, 4-doc subset)

**Plan metadata commit:** (this SUMMARY + STATE.md + ROADMAP.md) — appended below.

## Files Created/Modified
- `.planning/phases/04-regression-gate/04-WAVE-A-3docx-rootcause.md` — Wave A root-cause artefact (D-05 Branch B, locked ceilings, 4-doc subset, naming-convention gotcha) consumed verbatim by Wave B
- `results/reports/regression_audit_phase4_worst_offenders.csv` — full-corpus 18-pair regression audit at HEAD (force-added; `results/` is .gitignore-d per project convention)
- `results/reports/regression_audit_phase4_worst_offenders.json` — companion summary JSON (force-added)
- `results/reports/3docx_style_diff_HEAD.txt` — bisect raw trace (4 probed SHAs + per-commit 3.docx after_diff_rate values; HEAD-restored proof)

## Decisions Made
See `key-decisions` frontmatter. Most load-bearing:
- **D-05 Branch B**: rationale tied directly to the bisect — 7207cbe implements sealed Phase 3 D-05/D-06; the +0.003597 cost is the documented price of correctly autofixing a heading direct override on 3.docx that the Phase 2 blanket guard incorrectly left alone. CLAUDE.md rule «При выборе gate-варианта по success criterion из ROADMAP/REQUIREMENTS отдавай предпочтение опции, обусловленной выявлением корневой причины» applied.
- **Empirical-floor concession**: sanity-stable doc target of ≤0.1 (planning-time heuristic) is not met in the current corpus net of 58/59; lowest is 0.163743. Wave B locks at the empirical floor.

## Deviations from Plan

The 3-task plan executed in the order written. Four findings emerged that the plan did not anticipate; all are flagged for Wave B (per Plan 04-01 §"Actions for Wave B") rather than fixed in Wave A — Wave A's scope is investigation, Wave B is locking.

### Flagged for Wave B (NOT auto-fixed in Wave A — out of scope)

**1. [Flagged — Wave B input] Negative-column naming convention vs Plan 04-02 verify clauses**
- **Found during:** Task 3 (artefact authoring)
- **Issue:** `audit_negative_directory` returns `frame["negative"]` = formatted-DOCX filename (e.g. `3_formatted_20260413_194927.docx`), NOT the originating positive (`3.docx`). Wave B Plan 04-02 line 203 says `frame["negative"].isin(subset_filenames)`, which means `_metadata.subset_filenames` MUST contain negative-column filenames; the string `"3.docx"` would never match.
- **Action:** Documented at length in 04-WAVE-A-3docx-rootcause.md §"Naming convention gotcha" with the 4 verbatim subset filenames Wave B must copy. Wave B planner asked to audit 04-02 verify clauses for consistency.
- **Why not auto-fixed in Wave A:** Modifying Plan 04-02 is Wave B planner's responsibility; Wave A only flags.

**2. [Flagged — Wave B input] +0.025 additional drift since Этап 8 was undocumented**
- **Found during:** Task 1 (full-corpus audit)
- **Issue:** FORMAT_FIX_PLAN Этап 8 reported `0.334` for 3.docx; HEAD shows `0.359712`. The +0.025 was not in any prior planning document. Bisect (Task 2) confirmed it landed at `7207cbe` (Phase 3 D-05/D-06), AFTER Этап 8 was written — i.e. Этап 8 is stale, not wrong.
- **Action:** Empirical datapoint + drift breakdown recorded in artefact §"Empirical datapoints". Branch B ceiling reflects the post-7207cbe value, not the stale Этап 8 number.
- **Why not auto-fixed in Wave A:** Этап 8 is historical; updating FORMAT_FIX_PLAN is out of plan scope.

**3. [Flagged — Wave B input] No sanity-stable doc with after_diff_rate ≤ 0.1 in the corpus**
- **Found during:** Task 1 (worst-offender enumeration)
- **Issue:** RESEARCH.md Probe 1 recommends sanity-stable selection at `≤ 0.1`. Empirical floor net of 58/59 is `0.163743` (`4_formatted_20260413_185420.docx`).
- **Action:** Artefact §"4-doc subset" picks the empirical floor and explicitly notes the heuristic was unmet. Wave B uses the empirical value.
- **Why not auto-fixed in Wave A:** No "fix" available — corpus is what it is; documenting the deviation is the appropriate response.

**4. [Flagged — Wave B input] Aggregate-mean of Branch B subset (0.5857) exceeds existing D-15 ceiling 0.4781**
- **Found during:** Task 3 (artefact authoring — subset aggregate computed)
- **Issue:** Subset mean at HEAD = `(0.359712 + 0.963899 + 0.855596 + 0.163743) / 4 = 0.585738`. Phase 2 D-15 / ROADMAP Phase 1 success criterion 4 ceiling is `0.4781`. Branch B (legit Phase 3 behaviour change) raises the per-pair ceiling for 3.docx but the aggregate-mean collision is a fresh question.
- **Action:** Artefact §"Actions for Wave B" item 4 lists the two options Wave B must choose between: (a) raise aggregate-mean ceiling commensurate with the Phase 3 behaviour change in the same ROADMAP amendment, or (b) shrink the subset until the mean fits.
- **Why not auto-fixed in Wave A:** Aggregate-ceiling lifting is a ROADMAP edit; Wave A is forbidden from touching ROADMAP per `<rules>` of the continuation prompt.

### Auto-fixed Issues

None — Wave A scope is investigation only; no production code or test changes.

---

**Total deviations:** 0 auto-fixed; 4 findings flagged for Wave B (none of them violate Wave A scope).
**Impact on plan:** All four findings reach Wave B via the written artefact, not chat history. Wave B planner has explicit decisions to make on items 1 and 4 before the first test commit.

## Issues Encountered

- During Task 3 commit, `gsd-sdk query commit ... .planning/phases/.../04-WAVE-A-3docx-rootcause.md` returned `{"committed": false, "reason": "nothing staged"}` because the `.planning/` path is in `.gitignore` (line 40). Resolved via `git add -f` (the same force-add pattern Task 1 used for `results/reports/*` per its commit message). Working tree was inspected before commit to ensure only the artefact was staged; no incidental files swept in. This was a tooling pattern observation, not a deviation from the plan.

## User Setup Required

None.

## Next Phase Readiness

- **Wave B (04-02-PLAN) can start immediately.** All four prerequisite inputs are on disk:
  1. Empirical 3.docx ceilings: `after_diff_rate_ceiling=0.359712`, `field_mismatch_ceiling=630`.
  2. 4-doc subset (negative-column filenames, copy-paste-ready in artefact §"4-doc subset").
  3. D-05 Branch B locked → Wave B Task 1 includes the atomic ROADMAP + REQUIREMENTS amendment in the same commit as the baseline JSON write (NOT before, NOT after — same PR per Pitfall 3).
  4. Aggregate-mean (0.5857) vs D-15 ceiling (0.4781) collision flagged — Wave B planner must decide raise-or-shrink before writing the baseline JSON.
- **Naming-convention gotcha:** Wave B's `_metadata.subset_filenames` and per-pair dict keys MUST use negative-column filenames; the artefact lists them verbatim.
- **No blockers** — working tree clean against HEAD on `src/` `tests/`; no source code changed in Wave A.

## Self-Check

Verified all claims before completion.

- File `.planning/phases/04-regression-gate/04-WAVE-A-3docx-rootcause.md` — FOUND (committed `dd2db78`).
- File `results/reports/regression_audit_phase4_worst_offenders.csv` — FOUND (committed `c0904b4`).
- File `results/reports/regression_audit_phase4_worst_offenders.json` — FOUND (committed `c0904b4`).
- File `results/reports/3docx_style_diff_HEAD.txt` — FOUND (committed `5e9df74`).
- Commit `c0904b4` — FOUND in `git log`.
- Commit `5e9df74` — FOUND in `git log`.
- Commit `dd2db78` — FOUND in `git log` (Task 3 commit just made in this session).
- Task 3 automated verify clauses: file exists, no `<placeholder>`/`<X>`/`TBD`, `Branch chosen.*[AB]` matches, `after_diff_rate_ceiling = [0-9]` matches, `field_mismatch_ceiling = [0-9]` matches — all PASS (re-run inline above before the commit).
- Working tree clean against HEAD on src/tests: `git diff --quiet HEAD -- src/ tests/` → exit 0 (verified inline).

## Self-Check: PASSED

---
*Phase: 04-regression-gate*
*Completed: 2026-05-13*
