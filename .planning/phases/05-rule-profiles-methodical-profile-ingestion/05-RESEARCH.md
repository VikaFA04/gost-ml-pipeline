# Phase 5: Rule profiles & methodical-profile ingestion — Research

**Researched:** 2026-05-14
**Domain:** Methodical-profile extraction (PDF/DOCX → JSON profile), unified text diff over flattened JSON paths, dry-run/apply CLI dispatcher, profile schema lint, GHA CI gate extension.
**Confidence:** HIGH (all 6 in-scope gaps probed against existing source; Phase 4 patterns extracted verbatim from already-shipped code).

## Summary

Phase 5 closes six concrete gaps in a partially-built tool, not greenfield work. The extractor (`src/rules/methodical_extractor.py`, 374 LOC), CLI command (`src/main.py:cmd_extract_methodical_profile`), profile loader/validator, three profile JSONs, and two extractor tests already exist. The Бергер test PDF (1.4 MB, 28 pages) and the local 9.4 MB Нормоконтроль 2026 PDF both parse cleanly via the already-installed `pymupdf` (fitz) — `requirements.txt` line 10. No new top-level dependencies are needed; `difflib.unified_diff` from stdlib is sufficient for D-02. Phase 4 shipped the canonical `--apply/--force/--reason` dispatcher pattern (Wave D, `cmd_audit_regression`), the bogus-required-field RED-carrier for schema lints (Wave C, `tests/test_rules_quality_acceptance.py`), and the GHA + Makefile gate (Wave E, `regression-gate.yml`); Phase 5 extends these exact patterns rather than inventing new ones.

The most invasive change is per-field `_source` annotation (D-05): the extractor today writes flat scalars (`profile["document_rules"]["page"]["margin_left_cm"] = 3.0`); it must learn to attach a `_source` sidecar at every leaf, AND the existing flat-string `extract_text_from_file` must be replaced with a per-page (PDF) / per-paragraph (DOCX) traversal so regex matches carry their origin. The schema-lint test (D-08) must verify both directions: methodical profiles MUST carry `_source` per leaf, hand-authored GOST profiles MUST NOT (backwards-compat for the three existing profiles). SC-1 (D-07) is a no-op verify: `profile_id` already lives in both the per-row audit CSV column AND the summary JSON returned by `audit_or_format_docx`, but `audit-docx` / `format-docx` CLI subcommands DO NOT accept `--profile-id` (only `audit-regression` does); the one-line gap-closure is to add `--profile-id` to those two parsers and thread it through.

**Primary recommendation:** Five plans in strict-sequential execution, following CONTEXT.md `<plans_shape>` exactly. Each plan with code changes follows Phase 4 Wave D's RED→GREEN structure. The Бергер PDF moves to `tests/fixtures/methodical/normocontrol_berger.pdf` and is the single CI fixture. Verify (don't reimplement) SC-1 in plan 5-04 — the report header already carries `profile_id`.

## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01** — Phase 5 input scope: PDF + DOCX (+ existing TXT/MD). PPTX DROPPED. Methодичка at `normocontrol/Нормоконтроль 2026.pdf` is the local reference; `Нормоконтроль Бергер.pdf` (1.4MB Феврал) is the CI fixture. PRD US-028 SC-3 amendment lands atomically with plan 5-01 commit per D-004.

**D-02** — Diff format: unified text diff over flattened JSON paths. One line per change: `<dotted.path>: <old> → <new>`. Grouped under top-level section headers (`## document_rules`, `## labels`, `## bibliography_rules`, etc.). Both stdout and sidecar `.diff.txt` next to candidate JSON. NOT JSONpatch RFC 6902.

**D-03** — Dispatcher pattern: dry-run by default. `--apply` writes to `PROFILES_DIR/<profile_id>.json`. If target file already exists: refuse unless `--force --reason "<text>"` with `len(reason.strip()) >= 8`. Mirrors Phase 4 D-13 audit-trail pattern.

**D-04** — Overwrite policy: refuse silent overwrite of any existing profile JSON. `--force --reason` required. Russian-language error citing D-004. Reason recorded in profile's `extraction_meta.override_reason` field.

**D-05** — Per-field source attribution schema: `{"_source": {"file", "loc", "confidence", "needs_review"}}`. `loc` = `"page_N"` for PDF, `"paragraph_N"` for DOCX, `"line_N"` for TXT/MD. `confidence` ∈ [0.0, 1.0]; threshold `confidence < 0.7 → needs_review: true` (single sentinel). Annotation at LEAF level. Whole-profile `extraction_meta.needs_manual_review` becomes derived: `any(leaf._source.needs_review)`.

**D-06** — Test fixture: `tests/fixtures/methodical/normocontrol_berger.pdf` (1.4MB Феврал 2026 Бергер version). CI uses it. Current `Нормоконтроль 2026.pdf` (9.4MB) stays gitignored; local devs verify against it via Makefile target.

**D-07** — SC-1 verification: read `cmd_audit_regression` + `cmd_audit_docx` report writers; confirm `profile_id` is present in either CSV header column or summary JSON. If missing, add a single-line write. Treat as verify task, not implementation task.

**D-08** — Profile schema lint test (`tests/test_profile_quality_acceptance.py`): every `src/rules/profiles/*.json` validates through `profile_validator.validate()`; every profile carries top-level `profile_id`, `profile_name`, `profile_type`, `is_default`; every methodical-extracted profile (`profile_type == "methodical_guidelines"`) carries `_source` annotation on every leaf field in `document_rules.*`, `labels.*.style_profile`, `bibliography_rules.*`; computed `extraction_meta.needs_manual_review` matches `any(leaf._source.needs_review)`. Mirrors Phase 4 Wave C structure.

**D-09** — TDD discipline mandatory per CLAUDE.md «Железный закон». Each plan with code changes has explicit RED commit (`test(05-NN): RED — ...`) before GREEN (`feat(05-NN): GREEN — ...`).

**D-10** — CI gate extension reuses Phase 4 Option D pattern: workflow step copies `tests/fixtures/methodical/*.pdf` into a known path before pytest. Existing 4-file pytest invocation → 6-file invocation (existing 4 + `test_profile_quality_acceptance.py` + `test_methodical_extractor.py`). Makefile updated symmetrically. Timeout 10 min likely sufficient.

**D-11** — Russian-language UX preserved. Extends to new CLI flags' help text and error messages.

**D-12** — Backwards compatibility: existing `extract-methodical-profile` CLI without `--apply` becomes dry-run by default. No silent breakage — argparse help text + first-run banner cite D-004. Plan 5-03 RED commit captures the breaking-change test.

### Claude's Discretion

None marked explicitly in CONTEXT.md `<open_questions>` — "None — all decisions locked". Implementation choices below are bounded by D-01..D-12; specific code shape (function names, exact regex tolerance for Arabic-ligature noise, exact section-header set in the diff grouping) is researcher / planner judgement.

### Deferred Ideas (OUT OF SCOPE)

- **PPTX input** — DROPPED 2026-05-14.
- **OCR / image-only PDF** — methодичка must have an extractable text layer.
- **Rule engine changes** — Phase 5 only produces profile JSONs; no `apply_rules_to_paragraph` / scalar / list dispatcher changes.
- **UI integration** — Streamlit profile selection belongs to Phase 6.
- **Multi-profile per audit** — single `--profile-id` per run.
- **GHA full-corpus nightly + matrix** — Phase 4 out-of-scope items carry forward.
- **58.docx / 59.docx practice reports** — Phase 3 D-08 carries forward (practice reports excluded from GOST gate).

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-rule-profiles | Multiple rule profiles (GOST + university-local), stored outside code, selectable per audit, profile recorded in report | Already 90% shipped: 3 profile JSONs at `src/rules/profiles/*.json`, `--profile-id` flag exists on `audit-regression`, per-row CSV column + summary JSON both carry `profile_id` (verified: `src/generate/inplace_formatter.py` lines 504, 550). **Gap:** `audit-docx` + `format-docx` parsers lack `--profile-id` flag. Plan 5-04 closes by adding the flag + dispatcher kwarg (D-07). |
| REQ-methodical-profile-extract | `extract-methodical-profile` CLI ingests PDF/DOCX (PPTX dropped per D-01), produces draft profile, shows diff against base profile, requires explicit `--apply` before save; ambiguous requirements land as `needs_manual_review` with `page_N` / `paragraph_N` attribution | Partially shipped: extractor + CLI + two TXT/PDF tests in `tests/test_methodical_extractor.py`. **Six gaps:** (1) flat-text → per-page/per-paragraph traversal so each match carries origin; (2) `_source` annotation at every leaf (D-05); (3) diff generator over flattened JSON paths (D-02); (4) dry-run-by-default + `--apply/--force/--reason` (D-03/D-04); (5) `needs_manual_review` becomes derived (D-05); (6) PRD US-028 SC-3 + REQUIREMENTS REQ-methodical-profile-extract amended to drop PPTX (D-01 atomic with plan 5-01). |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| PDF/DOCX text extraction with location attribution | Library (pymupdf, python-docx) | — | fitz already in requirements.txt; existing extractor uses fitz for PDF and python-docx for DOCX. Per-page / per-paragraph iteration is already supported by the libraries; current code just collapses them with `\n`.join`. |
| Methodical profile build (regex over text → JSON dict) | Domain logic (`src/rules/methodical_extractor.py`) | — | Pure-Python rule engine; no I/O concerns at this layer. |
| `_source` annotation construction | Domain logic (extractor) | — | Annotation is data, not behaviour; lives next to the extracted value. Schema lint enforces shape; no runtime consumer in Phase 5. |
| Profile JSON diff (flattened path → unified diff) | Domain logic (NEW `src/rules/profile_diff.py`) | stdlib `difflib` | Stateless function; deterministic; testable in isolation. |
| Dry-run / apply / force / reason CLI guard | CLI dispatcher (`src/main.py:cmd_extract_methodical_profile`) | — | Mirror of Phase 4 `cmd_audit_regression` 8-char guard — pattern is local to dispatcher per Pitfall 6 (argparse cannot conditionally require). |
| Schema lint of profile JSONs | Test fixture / Test harness (`tests/test_profile_quality_acceptance.py`) | `src/rules/profile_validator.py` | Static lint reads JSON files via `Path.glob` + `json.loads`; runtime is irrelevant. |
| CI gate orchestration | GHA workflow + Makefile | — | Existing Phase 4 surface; Phase 5 only adds two pytest file references and one fixture-stage step. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pymupdf` (fitz) | ≥ 1.24 (per `requirements.txt` line 10) [VERIFIED: requirements.txt] | PDF text extraction with per-page iteration | Already installed and used by the extractor's `_read_pdf_text` fallback branch; Бергер PDF (28 pages, real text layer) parses cleanly — verified by probe (this research session, `/usr/bin/python3 -m pip install pymupdf` + `fitz.open` + 28 pages confirmed). pypdf is mentioned in code as a primary try but is NOT in requirements.txt — actual runtime uses fitz. |
| `python-docx` | ≥ 1.1 [VERIFIED: requirements.txt] | DOCX paragraph iteration | Already used everywhere in the codebase including `_read_docx_text`. |
| `difflib` (stdlib) | Python 3.11 [VERIFIED: stdlib import probe] | Unified text diff for profile diff generator | stdlib, zero new deps, deterministic output. `difflib.unified_diff(a, b, fromfile, tofile, n=3)` produces standard `@@ -... +... @@` headers. Phase 5 D-02 does NOT need patch-format (RFC 6902 explicitly rejected); plain readable line-by-line diff is the user value. |
| `pytest` | ≥ 8.0 [VERIFIED: requirements.txt] | Test harness — schema lint + extractor smoke | Established Phase 4 idiom. |
| `argparse` (stdlib) | Python 3.11 | CLI parsing | Established repo pattern in `src/main.py:build_parser`. |
| `json` (stdlib) | Python 3.11 | Profile JSON read/write | Established repo pattern; the existing extractor writes via `json.dump(... ensure_ascii=False, indent=2)`. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pathlib.Path` (stdlib) | Python 3.11 | File path manipulation | Throughout repo; do not regress. |
| `re` (stdlib) | Python 3.11 | Regex-based field extraction | Existing extractor uses `re.search` with `re.IGNORECASE \| re.MULTILINE`. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `difflib.unified_diff` | `jsondiff` (PyPI) | New dep; emits JSON-patch shape not aligned with D-02 ("readable error list"); rejected per D-02. |
| `difflib.unified_diff` | Hand-rolled `for path in flatten(profile): if old != new: print(...)` | Even simpler; loses the `@@` context headers which aid PR review of large profiles. **Recommended.** D-02 specifies "one line per change" + "section headers by top-level key", which is closer to hand-rolled than to `unified_diff` actually. The "unified text diff" phrase in CONTEXT.md is naming the SHAPE not requiring stdlib `unified_diff`. Researcher recommends **hand-rolled flatten + group-by-top-level-key + simple `<path>: <old> → <new>` lines** — simpler, fewer LoC, matches CLAUDE.md «50 строк вместо 200». |
| `pymupdf` (fitz) | `pypdf` | pypdf was the original primary try in the extractor but is NOT in requirements.txt → never executes in current runtime. Remove the `try: pypdf` branch in plan 5-01 to simplify; document that fitz is the canonical PDF reader. |
| Bogus-required-field RED carrier (Phase 4 Wave C deviation) | Probe-derived narrow allowed set | Phase 4 Wave C plan originally narrowed `ALLOWED_ACTION_VALUES = {"fix"}` to force RED, but discovered HEAD already satisfied the wider set so the lint had to be re-engineered with a bogus required field. Phase 5 plan 5-04 should use bogus-required-field directly to force RED in the schema lint, exactly as Phase 4 Wave C ended up doing — see SUMMARY 04-03. |

**Installation:** Zero new top-level dependencies. `pip install -r requirements.txt` already covers the stack.

**Version verification:** Performed via `cat requirements.txt` (read above) — pinned ranges shown. `npm view`-style verification N/A for Python; `pip show pymupdf` returns the installed minor version on the dev machine.

## Architecture Patterns

### System Architecture Diagram

```
                             ┌─────────────────────────┐
                             │ CLI invocation          │
                             │ extract-methodical-     │
                             │ profile --input-path X  │
                             │ [--apply --force        │
                             │  --reason "..."]        │
                             └────────────┬────────────┘
                                          │
                            ┌─────────────▼─────────────┐
                            │ cmd_extract_methodical_   │
                            │ profile (src/main.py)     │
                            │ — parses argv             │
                            │ — Pitfall-6 guard:        │
                            │   --force needs --reason  │
                            │   ≥8 chars                │
                            └─────────────┬─────────────┘
                                          │
                            ┌─────────────▼─────────────┐
                            │ extract_methodical_       │
                            │ profile() (extractor)     │
                            │ — file → per-page/        │
                            │   per-paragraph traversal │
                            │ — for each section:       │
                            │   regex match → value     │
                            │     + _source{file,loc,   │
                            │     confidence,           │
                            │     needs_review}         │
                            │ — derive needs_manual_    │
                            │   review = any(leaf       │
                            │   _source.needs_review)   │
                            └─┬───────────────────────┬─┘
                              │                       │
            ┌─────────────────▼──┐          ┌─────────▼────────────┐
            │ candidate_profile  │          │ base_profile (loaded │
            │ (dict)             │          │  via load_profile +  │
            └─────────┬──────────┘          │  deep_merge for      │
                      │                     │  base_profile_ids)   │
                      │                     └──────────┬───────────┘
                      │                                │
                      └────────┬───────────────────────┘
                               │
                ┌──────────────▼───────────────┐
                │ profile_diff.compute_diff()  │
                │ — flatten both dicts to      │
                │   sorted dotted paths        │
                │ — emit "<path>: <old> → <new>" │
                │   per changed leaf           │
                │ — group by top-level key     │
                └─────────┬─────────────┬──────┘
                          │             │
        ┌─────────────────▼─┐    ┌──────▼─────────────┐
        │ stdout (diff)     │    │ sidecar .diff.txt  │
        │ — always printed  │    │ — written next to  │
        └─────────┬─────────┘    │   candidate JSON   │
                  │              └────────────────────┘
                  │
        ┌─────────▼──────────────────────────┐
        │ Decision branch:                   │
        │ if --apply:                        │
        │   target = PROFILES_DIR/<id>.json  │
        │   if target.exists():              │
        │     require --force --reason ≥8    │
        │     extraction_meta.override_reason│
        │     = reason                       │
        │   write(target)                    │
        │ else (dry-run, default):           │
        │   write to TEMP/PREVIEW path       │
        │   exit 0 without touching          │
        │   PROFILES_DIR                     │
        └────────────────────────────────────┘
```

### Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| CLI parser | `src/main.py:build_parser` (lines 417-437, methodical_parser block) | Adds `--apply`, `--force`, `--reason` per D-03/D-04. Per Pitfall 6 all three are `required=False`; dispatcher enforces conditional rules. |
| Dispatcher | `src/main.py:main()` (lines 505-512) | Thread new args into `cmd_extract_methodical_profile`. |
| CLI body | `src/main.py:cmd_extract_methodical_profile` (lines 281-310) | Apply 8-char reason guard, manage dry-run vs --apply, write sidecar diff, write profile JSON. |
| Extractor | `src/rules/methodical_extractor.py` (374 LOC) | Replace flat `extract_text_from_file` with per-page/per-paragraph iterator; emit `_source` per leaf; compute derived `needs_manual_review`. |
| Diff generator | `src/rules/profile_diff.py` (NEW) | `compute_profile_diff(old: dict, new: dict) -> list[str]` — flatten + emit `<path>: <old> → <new>` lines, grouped by top-level key. |
| Schema lint | `tests/test_profile_quality_acceptance.py` (NEW) | Static test reading all `src/rules/profiles/*.json`; validates each through `profile_validator.validate()`; checks `_source` per leaf for methodical profiles only. |
| Extractor smoke | `tests/test_methodical_extractor.py` (EXISTING — extend) | Add tests for `_source` annotation on Бергер fixture + derived `needs_manual_review` consistency. |
| CI gate | `.github/workflows/regression-gate.yml` (MODIFY) | Add fixture-stage step for `tests/fixtures/methodical/`; extend pytest invocation from 4 files to 6. |
| Local gate | `Makefile` (MODIFY) | Mirror CI: add the same 2 pytest files to the `regression-gate` target. |

### Recommended Project Structure
```
src/rules/
├── methodical_extractor.py    # MODIFIED — per-page traversal + _source per leaf
├── profile_diff.py            # NEW — flatten + emit diff lines
├── profile_loader.py          # UNCHANGED — already handles deep_merge for base_profiles
├── profile_validator.py       # UNCHANGED (or +1 fn for _source structural lint, see Pitfall 5)
├── profiles/
│   ├── gost_7_32_2017.json                 # UNCHANGED — hand-authored, no _source
│   ├── gost_r_7_0_100_2018_bibliography.json  # UNCHANGED
│   └── mirea_normcontrol_local.json        # UNCHANGED
tests/
├── fixtures/methodical/
│   └── normocontrol_berger.pdf  # NEW — 1.4MB Бергер fixture for CI
├── test_methodical_extractor.py  # EXTEND — add Бергер fixture tests
├── test_profile_diff.py          # NEW — diff generator unit tests
├── test_profile_quality_acceptance.py  # NEW — schema lint, mirrors test_rules_quality_acceptance.py
└── test_cli_parser.py            # EXTEND — add --apply/--force/--reason tests
.github/workflows/
└── regression-gate.yml           # MODIFY — stage fixtures + pytest 4→6 files
Makefile                          # MODIFY — pytest 4→6 files
```

### Pattern 1: `--apply / --force / --reason "<text ≥8 chars>"` dispatcher (Phase 4 D-13 verbatim port)

**What:** argparse all `required=False`; dispatcher checks the conditional rule.

**When to use:** Whenever a CLI writes to a tracked/source-controlled artifact and the policy is "no silent rewrites" (PROJECT D-004).

**Source — verbatim from `src/main.py:cmd_audit_regression` lines 247-261:**

```python
# Source: src/main.py:247-261 (Phase 4 Wave D, commit 2bdaf71)
if update_baseline:
    # Probe 6 minimum: --reason must be >= 8 chars after strip (free text,
    # no forced ticket-ID format). Empty / whitespace / 7-char reasons
    # are refused.
    if not reason or len(reason.strip()) < 8:
        raise SystemExit(
            "--update-baseline требует --reason '<text>' (минимум 8 символов после strip; "
            "D-004: no silent rewrites; RESEARCH.md Probe 6)."
        )
    write_per_pair_baseline(
        path=Path(update_baseline),
        frame=frame,
        reason=reason.strip(),
        profile_id=profile_id,
    )
```

**Phase 5 adaptation (`cmd_extract_methodical_profile`):**

```python
# Two-layer guard:
# Layer 1 — --apply alone: switches from dry-run to write
# Layer 2 — --apply + target file exists: requires --force --reason ≥8
target_path = PROFILES_DIR / f"{profile['profile_id']}.json"
if not apply:
    # Dry-run (default per D-03 + D-12). Write to a temp/preview path.
    preview_path = Path(tempfile.gettempdir()) / f"{profile['profile_id']}.preview.json"
    # ... write preview + diff to stdout + sidecar
    return
# --apply requested
if target_path.exists():
    if not force:
        raise SystemExit(
            f"Профиль {target_path} уже существует. Используй --apply --force "
            f"--reason '<text>' (минимум 8 символов; D-004: no silent rewrites)."
        )
    if not reason or len(reason.strip()) < 8:
        raise SystemExit(
            "--force требует --reason '<text>' (минимум 8 символов после strip; "
            "D-004: no silent rewrites)."
        )
    profile["extraction_meta"]["override_reason"] = reason.strip()
# Write to target_path
```

**Anti-pattern:** Marking `--reason` as `required=True` in argparse — argparse cannot conditionally require, so an `extract-methodical-profile --input-path X` (no `--apply`, no `--reason`) would refuse to parse. Pitfall 6 in Phase 4 RESEARCH explicitly forbids this; the conditional guard MUST live in the dispatcher.

### Pattern 2: Per-page / per-paragraph PDF/DOCX traversal (NEW for Phase 5)

**What:** Replace `extract_text_from_file(path) -> str` with `iterate_text_chunks(path) -> Iterator[tuple[str, str]]` returning `(loc_label, text)` pairs.

**When to use:** Any regex-based extraction where the match location matters for downstream attribution.

**Source — NEW (no precedent in repo):**

```python
# Source: hand-rolled per Phase 5 D-05; relies on fitz.open + python-docx
# both already available.
from typing import Iterator

def iterate_text_chunks(path: Path) -> Iterator[tuple[str, str]]:
    """Yield (loc_label, text) pairs.

    PDF -> ("page_1", "..."), ("page_2", "...")
    DOCX -> ("paragraph_1", "..."), ("paragraph_2", "...")
    TXT/MD -> ("line_1", "..."), ("line_2", "...") (or one whole chunk)
    """
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        import fitz
        doc = fitz.open(str(path))
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            if text.strip():
                yield (f"page_{i}", text)
    elif suffix == ".docx":
        from docx import Document
        document = Document(str(path))
        for i, p in enumerate(document.paragraphs, start=1):
            t = (p.text or "").strip()
            if t:
                yield (f"paragraph_{i}", t)
    elif suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), start=1):
            if line.strip():
                yield (f"line_{i}", line)
    else:
        raise ValueError(f"Неподдерживаемый формат методички: {path.suffix}")
```

**Then each extractor field becomes:**

```python
def _extract_margin_left_cm(chunks: list[tuple[str, str]], file_name: str) -> tuple[float, dict]:
    """Return (value, _source_dict). _source_dict has file, loc, confidence, needs_review."""
    pattern = r"левое\s*[—\-:]\s*(\d+[.,]?\d*)\s*мм"
    for loc, text in chunks:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            value_mm = float(m.group(1).replace(",", "."))
            return (round(value_mm / 10.0, 2), {
                "file": file_name,
                "loc": loc,
                "confidence": 0.85,  # regex match on documented pattern
                "needs_review": False,  # 0.85 >= 0.7 threshold
            })
    # Default fallback — confidence drops, needs_review fires
    return (3.0, {
        "file": file_name,
        "loc": "default",
        "confidence": 0.0,
        "needs_review": True,
    })
```

**Phase 5 D-05 threshold:** `confidence < 0.7 → needs_review: True`. Single sentinel hard-coded in extractor; CONTEXT.md D-05 says "adjustable in code, not config".

### Pattern 3: Profile diff over flattened JSON paths (NEW for Phase 5)

**What:** Walk two dicts, flatten to sorted dotted-path scalars, emit one `<path>: <old> → <new>` line per changed leaf, group by top-level key.

**When to use:** Comparing two structured JSONs where the user value is "readable error list" (D-02).

**Source — NEW (per D-02):**

```python
# Source: hand-rolled per Phase 5 D-02; stdlib only.
from typing import Any

def _flatten(d: Any, prefix: str = "") -> dict[str, Any]:
    """Walk a nested dict/list/scalar; return {dotted_path: leaf_value}.

    Leaves that are themselves _source sidecar dicts are kept whole at their
    parent path with a "._source" suffix — they're not flattened past one level,
    so the diff stays readable.
    """
    out: dict[str, Any] = {}
    if isinstance(d, dict):
        for k, v in d.items():
            new_prefix = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)) and k != "_source":
                out.update(_flatten(v, new_prefix))
            else:
                out[new_prefix] = v
    elif isinstance(d, list):
        # Lists are diffed as whole-value (no per-index path) to avoid
        # spurious diff noise on list reordering. Diff is "lists differ" or
        # "lists equal".
        out[prefix] = d
    else:
        out[prefix] = d
    return out


def compute_profile_diff(base: dict, candidate: dict) -> list[str]:
    """Return list of diff lines, grouped by top-level key.

    Output example:
      ## document_rules
      document_rules.page.margin_left_cm: 3.0 → 2.5
      document_rules.default_font.font_size_pt: 14 → 12

      ## labels
      labels.body_text.style_profile.first_line_indent_cm: 1.25 → 1.5
    """
    base_flat = _flatten(base)
    cand_flat = _flatten(candidate)
    all_paths = sorted(set(base_flat) | set(cand_flat))

    lines_by_section: dict[str, list[str]] = {}
    for path in all_paths:
        old = base_flat.get(path, "<missing>")
        new = cand_flat.get(path, "<missing>")
        if old == new:
            continue
        # Skip _source-only changes — they're metadata, not policy
        if path.endswith("._source") or "._source." in path:
            continue
        section = path.split(".", 1)[0]
        lines_by_section.setdefault(section, []).append(f"{path}: {old} → {new}")

    out_lines: list[str] = []
    for section in sorted(lines_by_section):
        out_lines.append(f"## {section}")
        out_lines.extend(lines_by_section[section])
        out_lines.append("")
    return out_lines
```

**Anti-pattern:** Using `json.dumps(a) == json.dumps(b)` for equality — key ordering becomes a false-positive change source. Use `_flatten` then dict equality per path.

**Anti-pattern:** Recursing into the `_source` sidecar dict during flattening. The sidecar IS metadata about the leaf; diffing it produces noise of the form `document_rules.page.margin_left_cm._source.confidence: 0.85 → 0.87` on every re-extraction. Skip `_source` keys explicitly (see `k != "_source"` guard above).

### Pattern 4: Schema lint with bogus-required-field RED carrier (Phase 4 Wave C precedent)

**What:** When HEAD already satisfies the proposed lint, the RED commit cannot fail organically. Force RED by adding a deliberately-bogus required field; remove it in GREEN.

**When to use:** Forward-only regression gates (Phase 5 D-08 mirrors Phase 4 D-12 verbatim).

**Source — verbatim from `tests/test_rules_quality_acceptance.py` (Phase 4 Wave C, commit b8ee13a):**

```python
# Source: tests/test_rules_quality_acceptance.py:137-146 (Phase 4 Wave C)
REQUIRED_FIELDS = {
    "id",
    "applicable_labels",
    "parameter",
    "expected_value",
    "action",
    "severity",
    "autocorrect",
    "priority",
}
# For Phase 5 plan 5-04 RED commit, add: "__red_placeholder__" — every rule
# is missing it → RED. Remove in GREEN commit.
```

**Phase 5 D-08 adaptation (`tests/test_profile_quality_acceptance.py`):**

```python
# RED carrier per Phase 5 plan 5-04: include a bogus required key.
# Remove in GREEN.
REQUIRED_TOP_LEVEL_KEYS_FOR_METHODICAL = {
    "profile_id", "profile_name", "profile_type", "is_default",
    "extraction_meta", "__red_placeholder__",  # ← RED carrier; remove in GREEN
}

def test_every_methodical_profile_has_required_top_level_keys():
    """RED via bogus key; GREEN via removing it. Pattern from Wave C."""
    for path in METHODICAL_PROFILE_PATHS:
        profile = json.loads(path.read_text(encoding="utf-8"))
        missing = REQUIRED_TOP_LEVEL_KEYS_FOR_METHODICAL - set(profile)
        assert not missing, f"{path.name}: missing {sorted(missing)}"
```

### Pattern 5: CI fixture stage step (Phase 4 D-10 / Wave E Option D)

**What:** Workflow step copies in-repo fixtures into runtime paths before pytest runs.

**Source — verbatim from `.github/workflows/regression-gate.yml` lines 24-28 (Phase 4 Wave E, commit 5c6327d):**

```yaml
# Source: .github/workflows/regression-gate.yml:24-28
- name: Stage corpus subset from fixtures
  run: |
    mkdir -p positive_examples negative_examples
    cp tests/fixtures/corpus/positive/* positive_examples/
    cp tests/fixtures/corpus/negative/* negative_examples/
```

**Phase 5 D-10 adaptation (add to same workflow):**

```yaml
- name: Stage methodical fixtures
  run: |
    mkdir -p tests/fixtures/methodical
    # Already in repo via plan 5-05; this step is just a no-op verify that
    # the fixture exists. If the methodical_extractor test reads the fixture
    # via its committed path tests/fixtures/methodical/normocontrol_berger.pdf,
    # no staging is needed and this step can be omitted.
    test -f tests/fixtures/methodical/normocontrol_berger.pdf
```

**Recommended (simpler):** Since the Бергер fixture is committed in-repo at its final path (D-06), no staging step is needed — `pytest` reads it directly. The corpus staging step exists in Phase 4 only because Phase 4's positive/negative examples were originally outside `tests/`. Phase 5's methodical fixture lives inside `tests/fixtures/` from the start.

### Pattern 6: Pytest 4-file → 6-file invocation extension

**Source — verbatim from `Makefile` lines 17-21 (Phase 4 Wave D, commit 2bdaf71):**

```makefile
# Source: Makefile:17-21 (Phase 4 Wave D)
	$(PYTHON) -m pytest -q \
		tests/test_negative_corpus_diff_rate.py \
		tests/test_positive_docx_regression.py \
		tests/test_rules_quality_acceptance.py \
		tests/test_format_regression_audit.py
```

**Phase 5 D-10 adaptation:**

```makefile
	$(PYTHON) -m pytest -q \
		tests/test_negative_corpus_diff_rate.py \
		tests/test_positive_docx_regression.py \
		tests/test_rules_quality_acceptance.py \
		tests/test_format_regression_audit.py \
		tests/test_profile_quality_acceptance.py \
		tests/test_methodical_extractor.py
```

Same delta in `.github/workflows/regression-gate.yml` lines 31-35.

### Anti-Patterns to Avoid

- **Flat-text extractor with after-the-fact loc inference:** Trying to compute `page_N` by counting form-feeds or character offsets after `\n`.join`-ing pages will break on PDFs with mid-page line breaks. Iterate per-page from fitz; never collapse first.
- **Storing `_source` at the parent dict level:** CONTEXT.md D-05 is explicit — annotation at the LEAF. Storing at parent breaks the diff generator's per-path equality check and makes "which field changed" un-derivable.
- **Diffing the `_source` sidecar:** Even small confidence drifts (0.85 → 0.87) will spam the diff. Skip via path filter (see Pattern 3).
- **Hand-rolling JSON validation when `profile_validator.validate()` exists:** Phase 1/2 shipped `profile_validator`; Phase 5 D-08 explicitly mandates running existing JSONs through it. Do not duplicate; extend if needed.
- **Allowing `_source` on hand-authored GOST profiles:** D-08 says the per-leaf-`_source` requirement applies ONLY to `profile_type == "methodical_guidelines"`. Hand-authored profiles must validate via the existing `assert_valid_profile` path unchanged.
- **Auto-creating `tests/fixtures/methodical/` via runtime mkdir:** The fixture is a 1.4 MB committed asset. Commit it; do not synthesize. Plan 5-05 `git add tests/fixtures/methodical/normocontrol_berger.pdf` via `git add -f` since `.planning` is gitignored but `tests/` is not.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF text extraction | Custom PyMuPDF wrapper with manual page numbering | `for i, page in enumerate(fitz.open(p), start=1)` | Stdlib-style iteration over fitz pages is already idiomatic in repo (`_read_pdf_text` line 24-25); just don't collapse with `\n`.join`. |
| DOCX paragraph iteration | XML walking via lxml | `for i, p in enumerate(Document(str(p)).paragraphs, start=1)` | `python-docx` is in requirements.txt and `_read_docx_text` already does this; just don't collapse with `\n`.join`. |
| Profile JSON validation | Custom AST/key check | `src/rules/profile_validator.py:assert_valid_profile` | Shipped Phase 2; the existing 22-line validator covers required keys + label style shape + alignment + bibliography scope. Extend (don't rewrite) if `_source`-shape lint is needed. |
| Profile deep merge for base profile chain | Recursive dict update | `src/rules/profile_loader.py:deep_merge` | Already handles nested dict merging; tested in `tests/test_profile_loader.py`. |
| Unified diff format | Custom token diff | `difflib.unified_diff` OR hand-rolled flat-path diff | Per D-02 the user value is "readable" not "patchable" — hand-rolled flat-path diff is simpler and matches CLAUDE.md «50 строк». 30-50 LoC suffices. |
| CLI argument parsing | Custom argv loop | `argparse` already-established repo pattern | `build_parser` in `src/main.py` already handles 7 subcommands; extending the `methodical_parser` block is 4-6 new `.add_argument` calls. |
| Russian-language CLI errors | English error then translate | Direct `raise SystemExit("Русский текст...")` | Phase 4 `cmd_audit_regression` line 252-255 establishes the idiom verbatim. |
| 8-char strip-minimum reason validation | Regex on ticket-id format | `not reason or len(reason.strip()) < 8` | Free-text mode per Phase 4 Probe 6; ticket-ID format was explicitly rejected. |
| Test fixture for methodical extractor | Synthetic fitz-generated minimal PDF | Бергер's real `normocontrol_berger.pdf` (1.4 MB, 28 pages) | Per D-06; synthetic fixtures miss real edge cases (e.g., Arabic-ligature noise `прﮦавое` in Бергер PDF page 11 — observed during research probe). |

**Key insight:** Phase 5's surface is small (≈ 6 new functions across 3 files, ≈ 2 new test files, 1 fixture, 2 modified workflow/makefile files). Phase 4 already shipped every needed pattern; Phase 5 ports them verbatim. The biggest risk is over-engineering the diff generator — `difflib.unified_diff` would work but is heavier than necessary; a 30-line hand-rolled `_flatten + group + emit` matches D-02 exactly.

## Runtime State Inventory

Phase 5 is **not a rename/refactor/migration** — it adds new code and extends Phase 4 patterns. No string-replacement audit needed. Section omitted per RESEARCH.md template guidance.

## Common Pitfalls

### Pitfall 1: Backwards-compat break on existing profile JSONs (D-12)

**What goes wrong:** `tests/test_profile_quality_acceptance.py` enforces `_source` per leaf for every `profile_type == "methodical_guidelines"` profile. If the test is written too broadly (e.g., enforces `_source` for every profile regardless of type), the three existing hand-authored GOST profiles fail the lint immediately and Phase 1/2/3 baselines RED.

**Why it happens:** Test author copies the methodical-profile requirement and forgets the type filter.

**How to avoid:** Two-tier test structure in `test_profile_quality_acceptance.py`:
- **Tier A (all profiles):** `profile_validator.validate()` returns no errors; top-level keys `profile_id`, `profile_name`, `profile_type`, `is_default` present. Applies to ALL `src/rules/profiles/*.json`.
- **Tier B (methodical only):** Filter `[p for p in PROFILES if p.get("profile_type") == "methodical_guidelines"]`, then assert every leaf in `document_rules.*`, `labels.*.style_profile`, `bibliography_rules.*` carries `_source`. At HEAD this set is empty (no methodical profile committed) so Tier B passes vacuously — that's correct. Only when plan 5-01 runs the extractor against Бергер and saves to `src/rules/profiles/methodical_normocontrol_berger.json` (test fixture path) does Tier B fire substantively.

**Warning signs:** RED test at GREEN HEAD; failing test mentions `gost_7_32_2017.json`.

### Pitfall 2: Page-number drift on Cyrillic-ligature noise in Бергер PDF

**What goes wrong:** Probe (this session) showed Бергер PDF page 11 contains `прﮦавое` (`п-р-U+06EE-а-в-о-е`) — the Arabic Tail Ligature `ﮦ` (U+06EE) is interleaved with Cyrillic. Existing regex `r"правое\s*[—\-:]\s*(\d+[.,]?\d*)\s*мм"` (`flags=re.IGNORECASE`) will NOT match because `пра` ≠ `прﮦа`.

**Why it happens:** PDF text extraction tools sometimes inject Arabic combining marks during glyph reassembly (font-specific artifact).

**How to avoid:** Normalize page text before regex: `text = re.sub(r"[؀-ۿ]", "", text)` (strip all Arabic-block characters) OR use `unicodedata.normalize("NFKD", text)` followed by ASCII-fallback strip. The simpler `re.sub` is sufficient — Arabic characters should never appear legitimately in Russian methодички.

**Warning signs:** Extractor returns the default margin (3.0 cm) for Бергер PDF even though page 11 clearly states "левое — 30 мм". Schema test fails on `confidence < 0.7 → needs_review: True` invariant.

**Confidence: HIGH** — observed during research probe.

### Pitfall 3: Argparse cannot conditionally require `--reason` when `--apply --force` is set

**What goes wrong:** Author writes `parser.add_argument("--reason", required=True)` then realizes `extract-methodical-profile --input-path X` (no --apply) is now refused.

**Why it happens:** argparse only supports required-always / required-never; conditional requirement must be in the dispatcher.

**How to avoid:** All three new flags (`--apply`, `--force`, `--reason`) are `required=False`. Dispatcher checks `if apply and target_exists and not force: raise SystemExit(...)`, `if apply and target_exists and force and (not reason or len(reason.strip()) < 8): raise SystemExit(...)`. This is Phase 4 Pitfall 6 verbatim.

**Warning signs:** RED on `tests/test_cli_parser.py::test_extract_methodical_profile_dry_run_works_without_apply` (the dry-run-by-default test).

### Pitfall 4: Diff output explodes when extractor changes `_source.confidence` on every run

**What goes wrong:** Regex match against PDF text may have non-deterministic confidence (e.g., re-running extraction on the same PDF emits 0.85 vs 0.87 due to a subtle scoring change). Every `_source` field then shows up as a diff line, drowning out the actual policy changes (margin values, etc.).

**Why it happens:** Diff generator doesn't filter `_source` paths.

**How to avoid:** In `compute_profile_diff`, skip any path containing `._source.` (see Pattern 3 above). The diff is about policy values, not provenance metadata.

**Warning signs:** First call to `compute_profile_diff(base, candidate)` returns hundreds of lines, ~80% of them ending in `._source.confidence`.

### Pitfall 5: SC-1 verify gap — `audit-docx` / `format-docx` lack `--profile-id`

**What goes wrong:** D-07 says "treat as verify task". But verification shows: `cmd_audit_regression` (line 205) accepts `profile_id`; `cmd_audit_docx` (line 150) does NOT; `cmd_format_docx` (line 172) does NOT. Their underlying call to `audit_or_format_docx` defaults `profile_id=None`, which inside `load_profile` defaults to `"gost_7_32_2017"`. Per-row CSV column `profile_id` is populated correctly (line 504 of `inplace_formatter.py`), so SC-1 ("the chosen profile id is recorded in the report header") is satisfied for DEFAULT profile only — not for user-selected profile.

**Why it happens:** Phase 2 D-11 added `--profile-id` to the regression command only.

**How to avoid:** Plan 5-04 verify task adds three lines to `audit_parser` and `format_parser` (mirror the existing `regression_parser.add_argument("--profile-id", required=False, default="gost_7_32_2017", ...)` block at line 386-391), threads `profile_id=args.profile_id` through `main()` dispatch, and passes it as kwarg to `audit_or_format_docx`. That's 6-8 lines total; per D-07 this is still a verify task, not a new implementation.

**Warning signs:** `python -m src.main audit-docx --input-docx X --predictions-csv Y --profile-id mirea_normcontrol_local` exits with `error: unrecognized arguments: --profile-id`.

**Confidence: HIGH** — verified by `grep -n "--profile-id" src/main.py` (only `regression_parser` block has it; `audit_parser` and `format_parser` blocks do not).

### Pitfall 6: `.planning/` is gitignored — Bergер fixture must use `tests/` path

**What goes wrong:** Author places Бергер PDF in `.planning/phases/05-.../fixtures/` and notices it's silently gitignored (PROJECT-wide `.gitignore` line 39: `.planning/`).

**Why it happens:** Phase 4 worked around this with `git add -f` for plan/summary files — but a 1.4 MB binary asset shouldn't depend on `--force` to commit.

**How to avoid:** Commit Бергер at `tests/fixtures/methodical/normocontrol_berger.pdf` (per D-06). `tests/` is NOT gitignored. Verify with `git check-ignore tests/fixtures/methodical/normocontrol_berger.pdf` (expect empty output → not ignored).

**Warning signs:** `git status` after `git add tests/fixtures/methodical/normocontrol_berger.pdf` shows the file as untracked still, or `git ls-files tests/fixtures/methodical/` returns empty after commit.

### Pitfall 7: CI runtime exceeds 10-minute budget when Бергер extraction is slow

**What goes wrong:** PDF text extraction over 28 pages plus the full regex sweep takes > 60s on GHA runners; combined with the 4 existing gate test files, total exceeds 10 min.

**Why it happens:** GHA runners are slower than dev machines; cold pymupdf cache; cold pytest.

**How to avoid:** Time the Бергер extraction locally before plan 5-05. If > 30s (per CONTEXT.md D-10 estimate "PDF parse ~1s"), the warning is unfounded. If > 60s, plan 5-05 bumps `timeout-minutes: 10` → `15`. Per D-10 "Workflow `timeout-minutes: 10` likely sufficient (PDF parse ~1s); bump to 15 only if Бергер extraction exceeds 60s."

**Warning signs:** GHA workflow times out at exactly 10:00; pytest output shows `tests/test_methodical_extractor.py` still running.

**Mitigation if observed:** Run extraction once in `conftest.py` via session-scoped fixture, share the result across tests. Reduces re-extraction overhead.

### Pitfall 8: `extraction_meta.needs_manual_review` inconsistency after derivation

**What goes wrong:** D-05 says the field becomes derived: `any(leaf._source.needs_review)`. Author writes the derivation in one place (extractor) but leaves the old hand-set heuristic (`extraction_confidence < 0.9`, line 357 of `methodical_extractor.py`) somewhere else. Tests then disagree which value is canonical.

**Why it happens:** Two definitions of the same field; D-05 didn't explicitly say "delete the old heuristic".

**How to avoid:** Plan 5-01 GREEN commit removes the line `"needs_manual_review": extraction_confidence < 0.9,` (line 357) entirely and replaces with `"needs_manual_review": _any_leaf_needs_review(profile),` where `_any_leaf_needs_review` walks the profile dict and returns `True` if any `_source.needs_review` is True. Schema lint in plan 5-04 verifies consistency.

**Warning signs:** Test `assert profile["extraction_meta"]["needs_manual_review"] == any(leaf._source.needs_review for leaf in profile)` fails on a profile where extraction_confidence ≥ 0.9 but at least one regex defaulted.

## Code Examples

Verified patterns from official sources / shipped repo.

### Reading a PDF page-by-page (verified)

```python
# Source: /Users/fedorova.van/experiments/gost_formatter/src/rules/methodical_extractor.py:23-25
# (current shape — collapsed; Phase 5 changes to per-page yield)
import fitz
document = fitz.open(str(path))
# CURRENT (collapsed):
return "\n".join((page.get_text("text") or "") for page in document)
# PHASE 5 (per-page):
for i, page in enumerate(document, start=1):
    yield (f"page_{i}", page.get_text("text") or "")
```

### Reading a DOCX paragraph-by-paragraph (verified)

```python
# Source: /Users/fedorova.van/experiments/gost_formatter/src/rules/methodical_extractor.py:31-34
from docx import Document
document = Document(str(path))
# CURRENT (collapsed):
return "\n".join(p.text.strip() for p in document.paragraphs if p.text and p.text.strip())
# PHASE 5 (per-paragraph):
for i, p in enumerate(document.paragraphs, start=1):
    if p.text and p.text.strip():
        yield (f"paragraph_{i}", p.text.strip())
```

### Schema lint loading all profile JSONs (pattern from Phase 4 Wave C, adapted)

```python
# Source: tests/test_rules_quality_acceptance.py:135-153 (Phase 4 Wave C)
# Adapted for Phase 5 profile lint
from pathlib import Path
import json
from src.rules.profile_validator import validate_profile

PROFILES_DIR = Path("src/rules/profiles")

def _load_all_profiles() -> list[tuple[Path, dict]]:
    return [(p, json.loads(p.read_text(encoding="utf-8"))) for p in sorted(PROFILES_DIR.glob("*.json"))]


def test_every_profile_passes_validator() -> None:
    failures = []
    for path, profile in _load_all_profiles():
        # NOTE: validate_profile uses _resolve_base_profiles only when called
        # via load_profile(). For schema-only lint, read raw JSON and validate
        # the union shape via validate_profile (which checks REQUIRED_TOP_LEVEL_KEYS).
        errors = validate_profile(profile)
        if errors:
            failures.append(f"{path.name}: {errors}")
    assert not failures, "\n".join(failures)
```

### Sidecar file write next to candidate JSON (NEW pattern)

```python
# Source: hand-rolled per D-02
candidate_path = Path(tempfile.gettempdir()) / f"{profile['profile_id']}.preview.json"
candidate_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
sidecar_path = candidate_path.with_suffix(".diff.txt")
diff_lines = compute_profile_diff(base_profile, profile)
sidecar_path.write_text("\n".join(diff_lines), encoding="utf-8")
for line in diff_lines:
    print(line)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Extractor saves directly to `PROFILES_DIR/<id>.json` (silent overwrite) | Dry-run by default; explicit `--apply --force --reason ≥8` required | Phase 5 plan 5-03 (D-03/D-04) | **Breaking change** for callers; D-12 + first-run banner mitigate. |
| Whole-profile `extraction_meta.needs_manual_review` = `extraction_confidence < 0.9` (hand-set boolean) | Derived: `any(leaf._source.needs_review)` per D-05 | Phase 5 plan 5-01 | More precise; localizes "this specific field is uncertain" rather than global flag. |
| Flat string `extract_text_from_file(path) -> str` collapsing all pages/paragraphs | `iterate_text_chunks(path) -> Iterator[(loc, text)]` | Phase 5 plan 5-01 | Enables `loc: page_N` / `paragraph_N` attribution per D-05. |
| 3-file pytest gate (Phase 2/3 era) | 4-file pytest gate (`+ tests/test_format_regression_audit.py`) | Phase 4 Wave D commit 19b6592 | Closed Phase 4 SC-1; Phase 5 extends to 6-file. |
| `audit-regression` without `--update-baseline` | + `--update-baseline PATH --reason "<text ≥8>"` | Phase 4 Wave D | Audit-trail for baseline rewrites per D-004. Phase 5 mirrors the pattern for profile-write. |

**Deprecated/outdated:**
- `pypdf` try-branch in `_read_pdf_text` (lines 13-22): not in requirements.txt → never executes → dead code path. Remove in plan 5-01.
- `extraction_confidence < 0.9` heuristic (line 357): replaced by derived field per D-05. Remove in plan 5-01 GREEN.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pymupdf >= 1.24` is sufficient for the Бергер PDF; no upgrade needed. | Standard Stack | Low — verified by probe (28 pages parsed cleanly with system pip-installed pymupdf). If a newer pymupdf changes `get_text("text")` semantics, the regex baseline shifts. |
| A2 | Arabic Tail Ligature noise in PDF text (`прﮦавое`) can be safely stripped via `re.sub(r"[؀-ۿ]", "", text)` without breaking any legitimate methодичка content. | Pitfall 2 | Low — Russian/English-only domain; Arabic-block characters cannot appear in a Russian технический документ. Confidence: HIGH (single observed occurrence in Бергер). |
| A3 | The Бергер PDF (1.4 MB) parses in < 30s on GHA `ubuntu-latest`, keeping the 10-min workflow budget intact. | Pitfall 7 | Medium — not measured on GHA hardware. If wrong, bump `timeout-minutes` to 15 per D-10. |
| A4 | Hand-rolled flat-path diff (~50 LoC) beats `difflib.unified_diff` for D-02's "readable error list" goal. | Architecture Pattern 3 | Low — D-02 explicitly says "one line per change" + "section headers", which matches hand-rolled exactly. Decision is researcher recommendation; planner may use `difflib.unified_diff` if preferred. |
| A5 | `cmd_audit_docx` and `cmd_format_docx` gap (missing `--profile-id`) is in-scope for plan 5-04 as part of D-07 verify task. | Pitfall 5 | Low — CONTEXT.md D-07 says "If missing, add a single-line write." The CLI argparse gap IS the missing piece. Plan 5-04 should close it. |
| A6 | Phase 5 keeps the existing 2 extractor tests in `tests/test_methodical_extractor.py` and only EXTENDS the file (no rewrite). | Recommended Project Structure | Low — the two existing tests don't assert `_source` per leaf, so they remain valid after D-05 lands. Extension adds Бергер-fixture tests. |
| A7 | Methodical profile output filename (`methodical_normocontrol_berger.json`) lands in `src/rules/profiles/` (with `--apply`) or `tempfile.gettempdir()` (dry-run, default). The CONTEXT.md doesn't pin the dry-run path; planner choice. | Architecture Pattern 1 | Low — temp path is a Claude's-discretion area. `.planning/phases/05-.../05-04-PLAN.md` may also pick a workspace-local path like `results/methodical/`. |

**If this table is empty:** N/A — 7 assumptions logged. The planner / discuss-phase should confirm A3 (CI timeout) and A4 (diff library choice) before locking plan 5-02 and plan 5-05.

## Open Questions

None remain that block planning. All CONTEXT.md `<open_questions>` were closed by the discuss-phase. The researcher-level assumptions in §Assumptions Log are low-risk and can be confirmed during execution rather than re-discussed.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `pymupdf` (fitz) | PDF extractor — per-page traversal | ✓ | ≥ 1.24 per requirements.txt (verified by probe: `import fitz` + `fitz.open` works) | None needed — already in stack |
| `python-docx` | DOCX extractor — paragraph iteration | ✓ | ≥ 1.1 per requirements.txt | None needed |
| `pytest` | Test harness | ✓ | ≥ 8.0 per requirements.txt | None needed |
| `difflib` (stdlib) | Diff generator | ✓ | Python 3.11 | N/A — stdlib |
| `argparse` (stdlib) | CLI parsing | ✓ | Python 3.11 | N/A — stdlib |
| Бергер PDF file at `normocontrol/Нормоконтроль Бергер.pdf` | Source for `tests/fixtures/methodical/normocontrol_berger.pdf` | ✓ | 1.4 MB, 28 pages, verified text layer (this research probe) | None — must commit |
| `make` (GNU Make) | Local pre-PR gate | Likely ✓ on user's macOS dev box; not on GHA ubuntu-latest by default but Phase 4 already bypassed via direct pytest invocation in workflow | — | Workflow uses direct `python -m pytest` invocation (Phase 4 Wave E precedent — pattern already in place) |
| `pypdf` | Currently a `try:` branch in `_read_pdf_text` | ✗ (NOT in requirements.txt — falls through to fitz) | — | Already falling back to fitz; remove dead `try: pypdf` branch in plan 5-01 |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** `pypdf` — dead code, remove.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest >= 8.0` (pinned in `requirements.txt`) |
| Config file | none — pytest default discovery in `tests/` |
| Quick run command | `python -m pytest -q tests/test_methodical_extractor.py tests/test_profile_diff.py tests/test_profile_quality_acceptance.py tests/test_cli_parser.py` |
| Full suite command | `python -m pytest -q tests/` (or `make regression-gate` after plan 5-05) |
| Estimated runtime | ~30–60 sec local; ~60–90 sec CI (Бергер PDF parse ~1–5s × 2 tests + existing 4 gate files) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-methodical-profile-extract | Extractor emits `_source` per leaf on PDF input; loc = `page_N` | unit | `pytest -q tests/test_methodical_extractor.py::test_extract_methodical_profile_from_berger_pdf_emits_source_per_leaf` | ❌ Plan 5-01 creates |
| REQ-methodical-profile-extract | `extraction_meta.needs_manual_review` derives from `any(leaf._source.needs_review)` | unit | `pytest -q tests/test_methodical_extractor.py::test_needs_manual_review_is_derived_from_per_leaf_sources` | ❌ Plan 5-01 creates |
| REQ-methodical-profile-extract | Extractor handles DOCX input with `loc = paragraph_N` | unit | `pytest -q tests/test_methodical_extractor.py::test_extract_methodical_profile_from_docx_emits_paragraph_loc` | ❌ Plan 5-01 creates |
| REQ-methodical-profile-extract | `compute_profile_diff` emits `<path>: <old> → <new>` lines grouped by top-level key | unit | `pytest -q tests/test_profile_diff.py::test_compute_profile_diff_groups_by_top_level_key` | ❌ Plan 5-02 creates |
| REQ-methodical-profile-extract | `compute_profile_diff` skips `_source` paths (Pitfall 4) | unit | `pytest -q tests/test_profile_diff.py::test_compute_profile_diff_skips_source_metadata` | ❌ Plan 5-02 creates |
| REQ-methodical-profile-extract | CLI `extract-methodical-profile --input-path X` (no --apply) does dry-run, prints diff, exits 0 without touching PROFILES_DIR | integration | `pytest -q tests/test_cli_parser.py::test_extract_methodical_profile_dry_run_is_default` | ❌ Plan 5-03 creates |
| REQ-methodical-profile-extract | CLI `--apply` to an existing profile path refuses unless `--force --reason "<text ≥8>"` | integration | `pytest -q tests/test_cli_parser.py::test_extract_methodical_profile_apply_refuses_overwrite_without_force_reason` | ❌ Plan 5-03 creates |
| REQ-methodical-profile-extract | `--reason` < 8 chars (after strip) refused with Russian SystemExit citing D-004 | integration | `pytest -q tests/test_cli_parser.py::test_extract_methodical_profile_force_refuses_short_reason` | ❌ Plan 5-03 creates |
| REQ-rule-profiles + REQ-methodical-profile-extract | Every `src/rules/profiles/*.json` passes `validate_profile` (Tier A) | unit | `pytest -q tests/test_profile_quality_acceptance.py::test_every_profile_passes_validator` | ❌ Plan 5-04 creates |
| REQ-methodical-profile-extract | Every `profile_type == "methodical_guidelines"` profile carries `_source` per leaf (Tier B; vacuous at HEAD) | unit | `pytest -q tests/test_profile_quality_acceptance.py::test_every_methodical_profile_has_source_per_leaf` | ❌ Plan 5-04 creates |
| REQ-methodical-profile-extract | `extraction_meta.needs_manual_review` matches `any(leaf._source.needs_review)` (Tier B; vacuous at HEAD) | unit | `pytest -q tests/test_profile_quality_acceptance.py::test_methodical_needs_manual_review_consistent_with_per_leaf_sources` | ❌ Plan 5-04 creates |
| REQ-rule-profiles | `audit-docx --profile-id <id>` records the chosen profile in the per-row CSV header column (SC-1 verify) | integration | `pytest -q tests/test_cli_parser.py::test_audit_docx_accepts_profile_id_and_records_it_in_report` | ❌ Plan 5-04 creates |
| REQ-rule-profiles | `format-docx --profile-id <id>` records the chosen profile in the per-row CSV header column (SC-1 verify) | integration | `pytest -q tests/test_cli_parser.py::test_format_docx_accepts_profile_id_and_records_it_in_report` | ❌ Plan 5-04 creates |
| (CI) | GHA gate runs all 6 pytest files on every PR; fails red on regression | manual end-to-end | Two PRs per Phase 4 Wave E precedent: clean (GREEN) + designed-failure (RED) | Workflow exists; plan 5-05 extends |

### Sampling Rate

- **Per task commit:** `python -m pytest -q tests/<file>::<node>` for the test the task targets (< 5s).
- **Per wave merge:** `python -m pytest -q tests/test_methodical_extractor.py tests/test_profile_diff.py tests/test_profile_quality_acceptance.py tests/test_cli_parser.py` (< 60s).
- **Phase gate:** `make regression-gate` (6 test files, including the existing 4 Phase 4 files) green before `/gsd-verify-phase 5`.

### RED Test Names + Observable Failure Signatures

These are the **planned failing tests per plan** with exact expected failure signatures, to be captured in each plan's SUMMARY.md.

#### Plan 5-01 RED commit (extractor `_source` annotation)

| Test name (file: nodeid) | Expected stderr/stdout signature on RED |
|--------------------------|----------------------------------------|
| `tests/test_methodical_extractor.py::test_extract_methodical_profile_from_berger_pdf_emits_source_per_leaf` | `AssertionError: profile["document_rules"]["page"]["margin_left_cm"]._source missing` (the field is a bare float `3.0`, not a sidecar dict) |
| `tests/test_methodical_extractor.py::test_needs_manual_review_is_derived_from_per_leaf_sources` | `AssertionError: profile["extraction_meta"]["needs_manual_review"] == True (hand-set heuristic), expected False (derived from per-leaf sources, all confidence >= 0.7)` |
| `tests/test_methodical_extractor.py::test_extract_methodical_profile_from_docx_emits_paragraph_loc` | `KeyError: '_source'` OR `AssertionError: expected loc='paragraph_3', got 'page_3'` (current code emits `page_N` for everything since flat-string lost origin) |

GREEN commit removes the bogus assertion (if any) and lands the per-page traversal + `_source` annotation + derived `needs_manual_review`.

#### Plan 5-02 RED commit (diff generator)

| Test name (file: nodeid) | Expected stderr/stdout signature on RED |
|--------------------------|----------------------------------------|
| `tests/test_profile_diff.py::test_compute_profile_diff_groups_by_top_level_key` | `ModuleNotFoundError: No module named 'src.rules.profile_diff'` (module doesn't exist yet) |
| `tests/test_profile_diff.py::test_compute_profile_diff_emits_path_old_to_new` | Same `ModuleNotFoundError` |
| `tests/test_profile_diff.py::test_compute_profile_diff_skips_source_metadata` | Same `ModuleNotFoundError` |

GREEN creates `src/rules/profile_diff.py` with `compute_profile_diff` + `_flatten`.

#### Plan 5-03 RED commit (CLI dispatcher)

| Test name (file: nodeid) | Expected stderr/stdout signature on RED |
|--------------------------|----------------------------------------|
| `tests/test_cli_parser.py::test_extract_methodical_profile_dry_run_is_default` | `AssertionError: PROFILES_DIR/<id>.json was touched without --apply` (current code writes immediately on every invocation) |
| `tests/test_cli_parser.py::test_extract_methodical_profile_apply_refuses_overwrite_without_force_reason` | `argparse error: unrecognized arguments: --apply --force` (argparse doesn't know the flags yet) OR `TypeError: cmd_extract_methodical_profile() got an unexpected keyword argument 'apply'` |
| `tests/test_cli_parser.py::test_extract_methodical_profile_force_refuses_short_reason` | Same `argparse error` / `TypeError` |

GREEN adds `--apply`, `--force`, `--reason` flags + dispatcher guards. Russian SystemExit message text: `"Профиль {path} уже существует. Используй --apply --force --reason '<text>' (минимум 8 символов; D-004: no silent rewrites)."`

#### Plan 5-04 RED commit (schema lint, bogus-required-field carrier per Pattern 4)

| Test name (file: nodeid) | Expected stderr/stdout signature on RED |
|--------------------------|----------------------------------------|
| `tests/test_profile_quality_acceptance.py::test_every_profile_has_required_top_level_keys` (with `REQUIRED_TOP_LEVEL_KEYS_FOR_METHODICAL` including bogus `"__red_placeholder__"`) | `AssertionError: gost_7_32_2017.json: missing ['__red_placeholder__']` (per Phase 4 Wave C pattern) |
| `tests/test_cli_parser.py::test_audit_docx_accepts_profile_id_and_records_it_in_report` | `argparse error: unrecognized arguments: --profile-id` (audit-docx parser lacks the flag, per Pitfall 5) |

GREEN removes the bogus key AND adds `--profile-id` to `audit_parser` + `format_parser`.

#### Plan 5-05 RED commit (CI gate extension, optional — pattern from Phase 4 Wave E)

Per Phase 4 D-09 the CI gate wave is "execute (checkpoint)", not TDD. The manual checkpoint substitutes for a RED commit: deliberately-failing PR validates the gate fires correctly. See `<manual_only>` row in this table.

### Wave 0 Gaps

- ❌ `tests/test_profile_diff.py` — covers REQ-methodical-profile-extract diff generator
- ❌ `tests/test_profile_quality_acceptance.py` — covers REQ-rule-profiles + REQ-methodical-profile-extract schema lint
- ❌ `tests/fixtures/methodical/normocontrol_berger.pdf` — committed fixture for CI

(`tests/test_methodical_extractor.py`, `tests/test_cli_parser.py` already exist and are extended.)

No new framework installs needed; pytest already on the gate.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | dev-only CLI, no auth surface |
| V3 Session Management | no | no sessions |
| V4 Access Control | no | no multi-user |
| V5 Input Validation | yes | argparse type=`str`; `--reason` strip + length check; PDF/DOCX file extension check via `Path.suffix.lower()`; methodical extractor's regex patterns operate on the extracted text only — never on argv |
| V6 Cryptography | no | no crypto; profile JSONs are plaintext |
| V7 Error Handling | yes | All raised errors use Russian-language `SystemExit` or `ValueError` with explicit user-facing text; no stack traces leak in production CLI |
| V8 Data Protection | partial | Profile JSON files written to user-controlled paths; `--apply` writes to `PROFILES_DIR` which is in-repo (developer-controlled); dry-run writes to `tempfile.gettempdir()` (per-user tempdir on Unix, `%TEMP%` on Windows) |

### Known Threat Patterns for {extractor + CLI stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path-traversal via `--input-path "../../../etc/passwd"` | Tampering | Dev-only CLI per Phase 4 T-04-01 precedent. Path is accepted opaquely; document in CONTRIBUTING.md as developer-invoked. No mitigation needed beyond the existing FileNotFoundError on missing path. |
| Path-traversal via `--output-dir "../../../"` | Tampering | Same as above. Output dir is dev-controlled; mkdir + write happen in dev shell context. |
| Log-injection via `--reason "<text>"` | Tampering | Treat as opaque string. `reason.strip()` is the only transform. Persisted into JSON via `json.dumps(..., ensure_ascii=False)` — JSON encoder handles all escaping. Printed to stdout unmodified (terminal renders Cyrillic safely). No log files. Mirror of Phase 4 T-04-02. |
| Malicious PDF causing fitz.open to crash | DoS | Acceptable — dev-only context; a malicious PDF is a dev-supplied input. fitz crashes propagate as `ValueError` / `RuntimeError` to user; no fallthrough to silent state corruption. |
| Malicious DOCX with crafted XML | DoS | Same — dev-only context; python-docx exceptions propagate. |
| Profile JSON corruption (partial write) | Data integrity | Atomic write idiom (Phase 4 Wave D pattern): `path.parent.mkdir(parents=True, exist_ok=True)` → `path.write_text(json.dumps(...), encoding="utf-8")`. `write_text` is atomic on POSIX (single `open(O_TRUNC)` + `write` + `close`) — partial writes leave the file empty, not partial. Recovery: re-run extractor. |
| Silent overwrite of existing profile | Integrity / regression | **Mitigated by D-03/D-04** — `--apply` refuses to overwrite unless `--force --reason "<text ≥8>"`; D-004 (no silent rewrites) is the project-level rule. |
| Russian-language injection via filename in error msg | Information disclosure | All error messages use `f"Профиль {path} уже существует. ..."` — the path is a `Path` object, repr-safe. No shell expansion. |

**Phase 5 threat register inherits Phase 4 T-04-01 + T-04-02 verbatim.** Severity: low. No new attack surface.

## Project Constraints (from CLAUDE.md)

The following directives must be honored by the planner. Phase 5 plans MUST NOT contradict any of these.

### TDD Discipline (Железный закон)
- No production code without a failing test. Each plan with code changes commits RED before GREEN.
- Test must be observed failing for the expected reason — not because of a `NameError` or import error unrelated to the intended assertion.
- Bug fix starts with a failing test reproducing the bug.

### Минимум кода
- Solve in 50 lines vs 200 — researcher recommends hand-rolled flat-path diff (~50 LoC) over `difflib.unified_diff` wrapper.
- No improving neighbor code, formatting, comments. Follow existing style.
- Do not refactor working code without explicit request.

### Russian-language UX (D-11 amplification of CLAUDE.md project convention)
- All new CLI flag help text in Russian.
- All `SystemExit` / `ValueError` user-facing strings in Russian.
- Cite D-004 in overwrite-refusal messages.

### Profile-driven constants
- Per CLAUDE.md: "Перед фиксацией нумерационных/length/regex constants в коде проверь, не должны ли они быть profile-driven". The `confidence < 0.7` threshold (D-05) is explicitly *code-not-config* per CONTEXT.md. The 8-char `--reason` minimum is *code-not-config* per Phase 4 Probe 6 precedent. Document inline.

### No AI/Co-Authored-By trailers
- Per CLAUDE.md project rule: "Не добавляй в commit messages трейлеры Co-Authored-By, signed-off-by, Generated-by или любые маркеры авторства AI/инструмента". Phase 5 commits follow this — applies to all 5 plans.

### File-path traceability
- "Каждая изменённая строка должна напрямую отслеживаться до запроса пользователя." Plans must name exact files + exact lines (or `(NEW file)`) per change.

### Audit-trail for baselines / profiles
- "Сохраняй regression-audit summary в JSON для автоматизации." Phase 5 D-04 stores `extraction_meta.override_reason` inside the profile JSON itself, satisfying this rule.
- "При выборе gate-варианта по success criterion из ROADMAP/REQUIREMENTS отдавай предпочтение опции, обусловленной выявлением корневой причины." Phase 5 SC-1 verify (D-07) is structured as "verify task" — adding `--profile-id` to two CLI parsers IS the root-cause fix, not a number tweak.

### Avoid known anti-patterns
- "Не перезаписывай наследуемое DOCX-форматирование прямыми значениями без regression-теста на сохранение Word-стилей." Phase 5 does not touch the rule engine; this constraint is informational.
- "Не делай поспешных выводов; формулируй допущения вслух и спрашивай, если не уверен." Researcher logged 7 assumptions in §Assumptions Log.

## Sources

### Primary (HIGH confidence)
- `/Users/fedorova.van/experiments/gost_formatter/src/rules/methodical_extractor.py` (374 LOC, read in full) — current extractor shape
- `/Users/fedorova.van/experiments/gost_formatter/src/rules/profile_loader.py` (200 LOC, read in full) — `deep_merge`, `load_profile`, `_resolve_base_profiles`, `list_available_profiles`, `get_*` accessors
- `/Users/fedorova.van/experiments/gost_formatter/src/rules/profile_validator.py` (123 LOC, read in full) — `REQUIRED_TOP_LEVEL_KEYS`, `REQUIRED_STYLE_KEYS`, `ALLOWED_ALIGNMENTS`, `ALLOWED_BIBLIOGRAPHY_SCOPES`, `validate_profile`, `assert_valid_profile`
- `/Users/fedorova.van/experiments/gost_formatter/src/main.py` (518 LOC, key sections read) — `cmd_audit_regression` lines 205-278 (verbatim --apply pattern source), `cmd_extract_methodical_profile` lines 281-310, `build_parser` lines 313-439 (methodical_parser at 417-437; audit_parser at 351-357 missing --profile-id; format_parser at 359-371 missing --profile-id; regression_parser at 373-415 has --profile-id at 386-391)
- `/Users/fedorova.van/experiments/gost_formatter/src/generate/inplace_formatter.py` lines 320-555 — `audit_or_format_docx` signature + per-row CSV columns (`profile_id` at line 504, summary-dict `profile_id` at line 550) — confirms SC-1 is already 90% wired
- `/Users/fedorova.van/experiments/gost_formatter/src/rules/profiles/gost_7_32_2017.json` (355 lines, partial read) — hand-authored GOST profile shape; no `_source` keys
- `/Users/fedorova.van/experiments/gost_formatter/src/rules/profiles/mirea_normcontrol_local.json` (225 lines, partial read) — university-local profile
- `/Users/fedorova.van/experiments/gost_formatter/tests/test_methodical_extractor.py` (read in full) — 2 existing tests (TXT + PDF)
- `/Users/fedorova.van/experiments/gost_formatter/.planning/phases/04-regression-gate/04-04-PLAN.md` — Phase 4 Wave D --update-baseline / --reason CLI pattern verbatim
- `/Users/fedorova.van/experiments/gost_formatter/.planning/phases/04-regression-gate/04-03-PLAN.md` — Phase 4 Wave C schema lint pattern verbatim
- `/Users/fedorova.van/experiments/gost_formatter/.planning/phases/04-regression-gate/04-05-PLAN.md` — Phase 4 Wave E GHA workflow shape
- `/Users/fedorova.van/experiments/gost_formatter/.planning/phases/04-regression-gate/04-03-SUMMARY.md` — bogus-required-field RED-carrier deviation (Rule 4) lessons
- `/Users/fedorova.van/experiments/gost_formatter/.planning/phases/04-regression-gate/04-04-SUMMARY.md` — Pitfall 6 dispatcher-level conditional-require pattern
- `/Users/fedorova.van/experiments/gost_formatter/.planning/phases/04-regression-gate/04-VALIDATION.md` — phase-level validation contract template
- `/Users/fedorova.van/experiments/gost_formatter/.planning/phases/04-regression-gate/04-CONTEXT.md` — D-13, D-07, D-08 baseline-update / Makefile / GHA patterns
- `/Users/fedorova.van/experiments/gost_formatter/.github/workflows/regression-gate.yml` (read in full) — verbatim 4-file pytest invocation
- `/Users/fedorova.van/experiments/gost_formatter/Makefile` (read in full) — `regression-gate` target shape
- `/Users/fedorova.van/experiments/gost_formatter/requirements.txt` (read in full) — dep verification: `pymupdf>=1.24` confirmed; `pypdf` NOT present
- `/Users/fedorova.van/experiments/gost_formatter/CLAUDE.md` — project rules (read in full)
- `/Users/fedorova.van/experiments/gost_formatter/.planning/REQUIREMENTS.md` (read in full) — REQ-rule-profiles, REQ-methodical-profile-extract phrasing
- `/Users/fedorova.van/experiments/gost_formatter/.planning/ROADMAP.md` (read in full) — Phase 5 SC-1..SC-4
- `/Users/fedorova.van/experiments/gost_formatter/normocontrol/Нормоконтроль Бергер.pdf` — direct probe via fitz.open: 28 pages, real text layer, margin specs on pages 8/11/12/15/16/17/22

### Secondary (MEDIUM confidence)
- Probe-derived Arabic-ligature finding (`прﮦавое` on page 11) — single observation in one PDF; confidence in mitigation strategy is HIGH but the assumption that this is the only Unicode anomaly is MEDIUM.
- Python stdlib `difflib.unified_diff` docstring (verified via `python3 -c "import difflib; print(difflib.unified_diff.__doc__)"`)

### Tertiary (LOW confidence)
- A3 (CI parse-time budget): not measured on GHA hardware, only on local macOS. Risk MEDIUM if Бергер extraction is unexpectedly slow.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all deps verified in `requirements.txt`; PDF probe confirms Бергер parses cleanly.
- Architecture: HIGH — patterns extracted verbatim from already-shipped Phase 4 code; no novel design.
- Pitfalls: HIGH for Pitfalls 1, 3, 5, 6, 8 (all verified by source-code grep); HIGH for Pitfall 2 (Arabic ligature observed empirically); MEDIUM for Pitfalls 4, 7 (extrapolation from typical behaviour).
- Validation Architecture: HIGH — RED test signatures derived from current code shape (functions don't exist, kwargs don't exist, regex defaults fire).
- Security: HIGH — inherits Phase 4 T-04-01 / T-04-02 threat register verbatim; no new surface.

**Research date:** 2026-05-14
**Valid until:** 2026-06-13 (30 days; stable codebase, Phase 4 patterns recently locked, no upcoming dependency changes flagged in `requirements.txt`)
