---
phase: 09
slug: classical-model-zoo-lr-svm-complementnb-randomforest-histgbm
status: verified
threats_open: 0
asvs_level: 2
created: 2026-05-16
---

# Phase 09 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| test file → filesystem | Tests write/read under tmp_path (pytest-managed); no production data touched | Ephemeral test artifacts |
| REQUIREMENTS.md edit | Plain text additive edit; no executable surface | Structured text (requirements language) |
| CLI args → run_compare_classical | User-controlled --output-dir, --models, --seed values | Developer-supplied path strings and integers |
| dataset files → pipeline.fit | CSV files read from filesystem; no external network | Annotation labels (document structure labels, no PII) |
| fitted pipeline → pickle.dumps | In-memory serialisation for size measurement only; never written to disk | Scikit-learn model object bytes |
| Makefile recipe → shell | compare-classical-acceptance recipe runs python and pytest as shell commands; date substitution via $$(date ...) | Shell timestamp string |
| acceptance test → filesystem | Test reads glob-matched results.csv from results/ directory; no user-controlled input path | ML metric floats |
| README.md edit | Plain text append; no executable surface | Developer documentation |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status | Evidence |
|-----------|----------|-----------|-------------|------------|--------|----------|
| T-09-W1-01 | Tampering | REQUIREMENTS.md edit | accept | Read-only source artifact; edit is additive only; git diff reviewable | closed | AR-09-01 |
| T-09-W1-02 | Information Disclosure | test subprocess output | accept | Tests run locally only; no PII in dataset labels (document structure labels) | closed | AR-09-02 |
| T-09-W2-01 | Tampering | --output-dir path traversal | mitigate | `Path(output_dir).resolve()` normalises path; symlink/traversal sequences collapsed to absolute; results/ gitignored | closed | src/compare_classical.py:248-254, commit e93b7fe |
| T-09-W2-02 | Information Disclosure | error["message"] in results.json | mitigate | `str(exc)[:200]` truncation; `type(exc).__name__` only; no full traceback | closed | src/compare_classical.py:389-392 |
| T-09-W2-03 | Denial of Service | HistGBM OOM on large dataset | accept | Non-production informational run; per-model exception handler; CLI exits 1 | closed | AR-09-03 |
| T-09-W2-04 | Repudiation | results.csv overwritten silently | accept | Timestamped output dir per D-C-01 (`classical_zoo_<ts>/`); each run gets fresh directory | closed | AR-09-04 |
| T-09-W2-05 | Information Disclosure | dataset_hashes in results.json | accept | SHA-256 of annotation CSV, no PII; reproducibility aid for dev team | closed | AR-09-05 |
| T-09-W3-01 | Tampering | Makefile --output-dir date substitution | mitigate | `$$(date +%Y%m%d_%H%M%S)` fixed-format timestamp; no user-supplied string injected | closed | Makefile compare-classical-acceptance target |
| T-09-W3-02 | Tampering | acceptance test glob reads latest CSV | accept | Test reads from results/reports/ (local developer filesystem only); no network I/O; read-only | closed | AR-09-06 |
| T-09-W3-03 | Information Disclosure | README metric thresholds | accept | Thresholds (0.94, 0.86) are internal quality-gate values, not PII or credentials | closed | AR-09-07 |
| T-09-W3-04 | Denial of Service | make compare-classical-acceptance full re-run | accept | Manual invocation, not CI hot path; developer-initiated by design | closed | AR-09-08 |
| T-09-W3-05 | Repudiation | README drift from actual CLI flags | mitigate | CLAUDE.md trace rule: every changed line must trace to user request; README documents locked D-C-04+D-E-01 decisions | closed | README.md Classical Model Comparison section |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-09-01 | T-09-W1-01 | REQUIREMENTS.md edit is additive-only plain text change; reviewable via git diff; no executable attack surface | gsd-security-auditor | 2026-05-15 |
| AR-09-02 | T-09-W1-02 | Dataset labels are document structure labels (body_text, heading, etc.), not personal data; tests run in local dev environment only; no subprocess output egress | gsd-security-auditor | 2026-05-15 |
| AR-09-03 | T-09-W2-03 | HistGBM OOM is caught by per-model exception handler (src/compare_classical.py); error stored under results_json.models[i].error; remaining models continue; CLI exits 1; Phase 8 SC-2 verifiable via linear_svm_production row regardless | gsd-security-auditor | 2026-05-15 |
| AR-09-04 | T-09-W2-04 | Output directory is timestamped per D-C-01 (classical_zoo_<YYYYMMDD_HHMMSS>/); overwrite scenario does not occur in normal use; silent overwrite risk is structurally eliminated by timestamp collision probability | gsd-security-auditor | 2026-05-15 |
| AR-09-05 | T-09-W2-05 | SHA-256 hashes of annotation CSVs contain no PII; they are reproducibility fingerprints for the dev team; dataset is local-only and gitignored | gsd-security-auditor | 2026-05-15 |
| AR-09-06 | T-09-W3-02 | Acceptance test reads results/ via sorted glob; results/ is gitignored and local-only; test is strictly read-only (no write operations on the CSV); no network I/O | gsd-security-auditor | 2026-05-15 |
| AR-09-07 | T-09-W3-03 | Metric thresholds 0.94 (weighted_f1) and 0.86 (macro_f1) are internal ML quality-gate values documented in CONTEXT.md; they are not credentials, PII, or system-topology information | gsd-security-auditor | 2026-05-15 |
| AR-09-08 | T-09-W3-04 | make compare-classical-acceptance is a developer-only manual target; full zoo re-run is its stated purpose; not wired into any CI hot path | gsd-security-auditor | 2026-05-15 |

---

## Unregistered Threat Flags

From 09-02-SUMMARY.md: No new network endpoints, auth paths, or file access patterns beyond gitignored `results/` output directory. No unregistered flags surfaced during Wave 2 implementation.

From 09-03-SUMMARY.md: No `## Threat Flags` section present; no new flags surfaced during Wave 3 implementation.

From 09-01-SUMMARY.md: No `## Threat Flags` section present.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By | Notes |
|------------|---------------|--------|------|--------|-------|
| 2026-05-15 | 12 | 11 | 1 | gsd-security-auditor (claude-sonnet-4-6) | Initial audit; T-09-W2-01 open — `.resolve()` absent from src/compare_classical.py |
| 2026-05-16 | 12 | 12 | 0 | gsd-security-auditor (claude-sonnet-4-6) | Recheck after commit e93b7fe; `Path(cli_args.output_dir).resolve()` confirmed at lines 248-254 of src/compare_classical.py for both user-supplied and default output_dir branches; inline comment cites T-09-W2-01; smoke test test_cli_smoke_runs_end_to_end_quick GREEN |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-05-16
