# Phase 5: Rule profiles & methodical-profile ingestion — Pattern Map

**Mapped:** 2026-05-14
**Files analyzed:** 11 (5 NEW, 6 MODIFY)
**Analogs found:** 11 / 11

Phase 5 is gap closure, not greenfield. Every NEW/MODIFY file has a strong in-repo analog. Phase 4 (regression-gate) shipped the canonical `--apply / --force / --reason "<text ≥8>"` dispatcher, the bogus-required-field schema-lint RED carrier, the 4-file pytest gate (Makefile + GHA workflow), and the per-row CSV `profile_id` column — Phase 5 ports these patterns verbatim with surface-level adaptation.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/rules/methodical_extractor.py` (MODIFY 5-01) | service | file-I/O + transform | itself (current shape) + `src/rules/profile_loader.py` traversal | exact (self) |
| `tests/test_methodical_extractor.py` (EXTEND 5-01) | test (unit) | request-response | itself (2 existing tests) | exact (self) |
| `src/rules/profile_diff.py` (NEW 5-02) | utility (pure function) | transform | `src/evaluation/format_regression_audit.py::write_per_pair_baseline` (lines 247-261, hand-rolled flatten-and-diff loop) + `src/rules/profile_loader.py::deep_merge` (recursive dict walker) | role-match (analog walks dict recursively) |
| `tests/test_profile_diff.py` (NEW 5-02) | test (unit, pure fn) | request-response | `tests/test_profile_loader.py` (pure-function unit test shape) | exact |
| `src/main.py::cmd_extract_methodical_profile` (MODIFY 5-03) | dispatcher (CLI) | request-response | `src/main.py::cmd_audit_regression` lines 247-261 (8-char `--update-baseline / --reason` guard) | exact |
| `src/main.py::build_parser` methodical block (MODIFY 5-03) | CLI parser | request-response | `src/main.py::build_parser` lines 403-415 (`--update-baseline / --reason` argparse stanza, all `required=False`) | exact |
| `tests/test_cli_parser.py` (EXTEND 5-03 & 5-04) | test (integration) | request-response | `tests/test_cli_parser.py::test_cli_parser_accepts_update_baseline_and_reason` + `::test_cmd_audit_regression_refuses_update_baseline_without_reason` | exact (self) |
| `tests/test_profile_quality_acceptance.py` (NEW 5-04) | test (lint) | static read | `tests/test_rules_quality_acceptance.py` (Phase 4 Wave C — REQUIRED_FIELDS set + per-file iteration + failure aggregation) | exact |
| `src/main.py::build_parser` audit/format blocks (MODIFY 5-04, SC-1) | CLI parser | request-response | `src/main.py::build_parser` lines 386-391 (`regression_parser.add_argument("--profile-id", ...)`) | exact |
| `tests/fixtures/methodical/normocontrol_berger.pdf` (NEW 5-05, 1.4MB binary) | fixture (committed asset) | static read | `tests/fixtures/heading_minimal.docx`, `tests/fixtures/bibliography_minimal.docx` (committed binary fixtures already in repo) | role-match (binary fixture under tests/fixtures/) |
| `.github/workflows/regression-gate.yml` (MODIFY 5-05) | CI workflow | event-driven | itself (Phase 4 Wave E shape — 4-file pytest invocation, existing fixture stage step) | exact (self) |
| `Makefile` regression-gate target (MODIFY 5-05) | build script | request-response | itself (4-file pytest block lines 17-21) | exact (self) |

---

## Pattern Assignments

### Plan 5-01 — `src/rules/methodical_extractor.py` (MODIFY) + `tests/test_methodical_extractor.py` (EXTEND)

**Analog:** `src/rules/methodical_extractor.py` itself (current shape) — the file is being mutated, not rewritten. Per-page traversal pattern is NEW (no in-repo precedent; closest reference is the current `_read_pdf_text` collapsed shape).

**Imports pattern** (lines 1-9, keep as-is):

```python
# Source: src/rules/methodical_extractor.py:1-9 (KEEP unchanged)
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.rules.profile_loader import PROFILES_DIR, deep_merge, load_profile
```

**Current PDF reader to REPLACE** (lines 12-28, becomes per-page iterator):

```python
# Source: src/rules/methodical_extractor.py:12-28 (CURRENT — flat collapse)
def _read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception as e:
        try:
            import fitz  # PyMuPDF
        except Exception as fitz_exc:
            raise ImportError(
                "Для извлечения текста из PDF нужен пакет pypdf или PyMuPDF. "
                "Установи: pip install pypdf pymupdf"
            ) from fitz_exc

        document = fitz.open(str(path))
        return "\n".join((page.get_text("text") or "") for page in document)

    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)
```

**Phase 5 GREEN shape** (per RESEARCH §Code Examples + §Architecture Pattern 2):

```python
# Source: hand-rolled per Phase 5 D-05. RESEARCH §Pattern 2 lines 290-318.
# Remove dead pypdf try-branch (RESEARCH §State of the Art: pypdf NOT in requirements.txt).
from typing import Iterator

def iterate_text_chunks(path: Path) -> Iterator[tuple[str, str]]:
    """Yield (loc_label, text) per page/paragraph/line.
       PDF -> ("page_N", text), DOCX -> ("paragraph_N", text), TXT/MD -> ("line_N", text)."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        import fitz
        doc = fitz.open(str(path))
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            # RESEARCH §Pitfall 2: strip Arabic-block noise that fitz injects
            text = re.sub(r"[؀-ۿ]", "", text)
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

**Per-field `_source` annotation** (replaces flat scalar assignment in `_extract_document_rules` lines 75-96):

```python
# Source: hand-rolled per D-05; RESEARCH §Pattern 2 lines 324-343
def _extract_margin_left_cm(
    chunks: list[tuple[str, str]],
    file_name: str,
) -> tuple[float, dict[str, Any]]:
    """Return (value, _source). _source has file, loc, confidence, needs_review.
       Threshold per D-05: confidence < 0.7 → needs_review=True."""
    pattern = r"левое\s*[—\-:]\s*(\d+[.,]?\d*)\s*мм"
    for loc, text in chunks:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            value_mm = float(m.group(1).replace(",", "."))
            return (round(value_mm / 10.0, 2), {
                "file": file_name,
                "loc": loc,
                "confidence": 0.85,  # regex match on documented pattern
                "needs_review": False,
            })
    return (3.0, {  # default fallback
        "file": file_name, "loc": "default",
        "confidence": 0.0, "needs_review": True,
    })
```

**Derived `needs_manual_review` REPLACING line 357** (`extraction_confidence < 0.9` heuristic):

```python
# Source: per D-05 / RESEARCH §Pitfall 8 — delete the hand-set heuristic and derive
def _any_leaf_needs_review(node: Any) -> bool:
    """Walk profile dict; return True if any leaf's _source.needs_review is True."""
    if isinstance(node, dict):
        if "_source" in node and isinstance(node["_source"], dict):
            if node["_source"].get("needs_review"):
                return True
        return any(_any_leaf_needs_review(v) for k, v in node.items() if k != "_source")
    if isinstance(node, list):
        return any(_any_leaf_needs_review(item) for item in node)
    return False

# Then at line 357 (CURRENT: "needs_manual_review": extraction_confidence < 0.9):
profile["extraction_meta"]["needs_manual_review"] = _any_leaf_needs_review(profile)
```

**Test pattern** (`tests/test_methodical_extractor.py` — extend existing file, follow `test_extract_methodical_profile_from_text_file` shape lines 9-71):

```python
# Source: tests/test_methodical_extractor.py:9-71 (existing shape, extend)
# Phase 5 RED tests per RESEARCH §Validation Architecture lines 805-810:
def test_extract_methodical_profile_from_berger_pdf_emits_source_per_leaf() -> None:
    fixture = Path("tests/fixtures/methodical/normocontrol_berger.pdf")
    # NOTE: until 5-05 commits the fixture, this test skips. In 5-01 the test
    # is RED via AssertionError on _source missing (the fixture exists by then
    # OR the test is run on the local 9.4MB Нормоконтроль 2026.pdf instead —
    # planner choice in 5-01 task ordering vs 5-05 fixture commit).
    profile, _ = extract_methodical_profile(input_path=fixture, output_dir=...)
    margin = profile["document_rules"]["page"]["margin_left_cm"]
    # AFTER Phase 5: leaves are dicts {value: ..., _source: {...}} OR there's
    # a parallel _source dict tree. Planner picks the exact schema shape per D-05.
    assert "_source" in profile["document_rules"]["page"]["margin_left_cm"], (
        "expected _source sidecar at margin_left_cm leaf"
    )
```

---

### Plan 5-02 — `src/rules/profile_diff.py` (NEW) + `tests/test_profile_diff.py` (NEW)

**Analog:** No direct precedent in repo. Closest analog for the recursive dict walk is `src/rules/profile_loader.py::deep_merge` (lines 11-20, recursive dict traversal). Closest analog for the "flatten + emit `<path>: <old> → <new>` lines" pattern is `src/evaluation/format_regression_audit.py::write_per_pair_baseline` line 259 (`print(f"{name}: {old} -> {new_ceiling}")`). Test analog is `tests/test_profile_loader.py` (pure-function unit test shape).

**Recursive walker analog — `deep_merge`** (lines 11-20):

```python
# Source: src/rules/profile_loader.py:11-20 — RECURSIVE DICT WALKER pattern
def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result
```

**`<old> -> <new>` line-emit analog** (`write_per_pair_baseline` line 259):

```python
# Source: src/evaluation/format_regression_audit.py:259 — line-emit shape
print(f"{name}: {old} -> {new_ceiling}")
```

**Phase 5 GREEN shape — full hand-rolled flatten + diff** (per RESEARCH §Pattern 3 lines 360-417, ~50 LoC total):

```python
# Source: hand-rolled per D-02; stdlib only. RESEARCH §Pattern 3.
from typing import Any

def _flatten(d: Any, prefix: str = "") -> dict[str, Any]:
    """Walk nested dict/list/scalar; return {dotted_path: leaf_value}.
       _source sidecar dicts are NOT recursed into — RESEARCH §Pitfall 4."""
    out: dict[str, Any] = {}
    if isinstance(d, dict):
        for k, v in d.items():
            new_prefix = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)) and k != "_source":
                out.update(_flatten(v, new_prefix))
            else:
                out[new_prefix] = v
    elif isinstance(d, list):
        out[prefix] = d  # lists diffed whole-value (avoid index churn)
    else:
        out[prefix] = d
    return out


def compute_profile_diff(base: dict, candidate: dict) -> list[str]:
    """Return diff lines grouped under top-level section headers.
       Output: '## <section>' header lines + '<dotted.path>: <old> → <new>' lines.
       _source paths are skipped to avoid provenance-metadata noise."""
    base_flat = _flatten(base)
    cand_flat = _flatten(candidate)
    all_paths = sorted(set(base_flat) | set(cand_flat))
    lines_by_section: dict[str, list[str]] = {}
    for path in all_paths:
        old = base_flat.get(path, "<missing>")
        new = cand_flat.get(path, "<missing>")
        if old == new:
            continue
        if path.endswith("._source") or "._source." in path:
            continue  # RESEARCH §Pitfall 4
        section = path.split(".", 1)[0]
        lines_by_section.setdefault(section, []).append(f"{path}: {old} → {new}")
    out_lines: list[str] = []
    for section in sorted(lines_by_section):
        out_lines.append(f"## {section}")
        out_lines.extend(lines_by_section[section])
        out_lines.append("")
    return out_lines
```

**Test pattern** (mirror `tests/test_profile_loader.py:33-41` "validator accepts ..." shape — pure-function assertions):

```python
# Source: tests/test_profile_loader.py:33-41 — pure-fn unit test shape
def test_validator_accepts_profile_without_optional_sections() -> None:
    for profile_id in ("mirea_normcontrol_local", "gost_r_7_0_100_2018_bibliography"):
        profile = load_profile(profile_id=profile_id)
        assert profile["profile_id"], f"profile {profile_id!r} missing profile_id"
```

```python
# Phase 5 plan 5-02 RED: tests fail with ModuleNotFoundError
# RESEARCH §Validation Architecture lines 815-819
from src.rules.profile_diff import compute_profile_diff  # ImportError on RED

def test_compute_profile_diff_groups_by_top_level_key() -> None:
    base = {"document_rules": {"page": {"margin_left_cm": 3.0}}}
    cand = {"document_rules": {"page": {"margin_left_cm": 2.5}}}
    lines = compute_profile_diff(base, cand)
    assert "## document_rules" in lines
    assert "document_rules.page.margin_left_cm: 3.0 → 2.5" in lines

def test_compute_profile_diff_skips_source_metadata() -> None:
    base = {"x": {"_source": {"confidence": 0.85}, "v": 1}}
    cand = {"x": {"_source": {"confidence": 0.87}, "v": 1}}
    lines = compute_profile_diff(base, cand)
    assert lines == []  # all changes filtered (only _source moved)
```

---

### Plan 5-03 — `src/main.py::cmd_extract_methodical_profile` (MODIFY) + parser (MODIFY) + `tests/test_cli_parser.py` (EXTEND)

**Analog:** `cmd_audit_regression` lines 205-278 (Phase 4 Wave D, commit 2bdaf71) — verbatim port of `--update-baseline / --reason` 8-char dispatcher guard pattern.

**Dispatcher guard pattern — verbatim source** (`src/main.py:247-261`):

```python
# Source: src/main.py:247-261 (Phase 4 Wave D — analog for plan 5-03)
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

**Argparse stanza — verbatim source** (`src/main.py:403-415`, `regression_parser`):

```python
# Source: src/main.py:403-415 (Phase 4 Wave D — analog for plan 5-03 methodical parser)
regression_parser.add_argument(
    "--update-baseline",
    required=False,
    type=str,
    metavar="PATH",
    help="Если задано, перезаписать per-pair ceilings из текущего прогона в JSON по этому пути. Требует --reason.",
)
regression_parser.add_argument(
    "--reason",
    required=False,
    type=str,
    help="Обязательное обоснование (свободный текст, минимум 8 символов после strip) при --update-baseline.",
)
```

**Current methodical parser block to EXTEND** (`src/main.py:417-437`):

```python
# Source: src/main.py:417-437 — CURRENT methodical_parser, missing --apply/--force/--reason
methodical_parser = subparsers.add_parser(
    "extract-methodical-profile",
    help="Извлечь профиль оформления из локальной методички PDF/DOCX/TXT",
)
methodical_parser.add_argument("--input-path", required=True, help="Путь к PDF/DOCX/TXT/MD файлу")
methodical_parser.add_argument("--output-dir", required=False, help="Папка для сохранения профиля JSON")
methodical_parser.add_argument("--profile-name", required=False, help="Человекочитаемое имя профиля")
methodical_parser.add_argument(
    "--base-profile-ids", nargs="+",
    default=["gost_7_32_2017", "gost_r_7_0_100_2018_bibliography"],
    help="Базовые profile_id, которые нужно слить перед извлечением",
)
```

**Phase 5 ADDITIONS** (D-03/D-04 — append three flags, all `required=False`):

```python
# Source: hand-rolled per D-03/D-04, mirrors regression_parser shape (src/main.py:403-415)
methodical_parser.add_argument(
    "--apply", action="store_true",
    help="Записать профиль в PROFILES_DIR/<id>.json. Без флага — dry-run в tempfile.gettempdir().",
)
methodical_parser.add_argument(
    "--force", action="store_true",
    help="Перезаписать существующий профиль (требует --reason ≥8 символов). D-004: no silent rewrites.",
)
methodical_parser.add_argument(
    "--reason", required=False, type=str,
    help="Обязательное обоснование (минимум 8 символов после strip) при --apply --force над существующим профилем.",
)
```

**Current dispatcher to REPLACE** (`src/main.py:281-310`):

```python
# Source: src/main.py:281-310 — CURRENT cmd_extract_methodical_profile (silent overwrite)
def cmd_extract_methodical_profile(
    input_path: str,
    output_dir: Optional[str],
    profile_name: Optional[str],
    base_profile_ids: list[str],
) -> None:
    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        raise FileNotFoundError(f"Не найден файл методички: {input_path_obj}")
    profile, output_path = extract_methodical_profile(
        input_path=input_path_obj,
        output_dir=output_dir,
        base_profile_ids=base_profile_ids or None,
        profile_name=profile_name,
    )
    print(f"Профиль сохранен в: {output_path}")
    # ... summary print
```

**Phase 5 GREEN shape** (per RESEARCH §Pattern 1 lines 247-273 — two-layer guard):

```python
# Source: hand-rolled per D-03/D-04; analog cmd_audit_regression lines 247-261
def cmd_extract_methodical_profile(
    input_path: str, output_dir: Optional[str], profile_name: Optional[str],
    base_profile_ids: list[str],
    apply: bool = False, force: bool = False, reason: Optional[str] = None,
) -> None:
    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        raise FileNotFoundError(f"Не найден файл методички: {input_path_obj}")

    # Build candidate profile (in-memory; no disk write yet)
    profile = build_methodical_profile(input_path=input_path_obj, ...)
    target_path = PROFILES_DIR / f"{profile['profile_id']}.json"

    # Compute & print diff against base
    base_profile = load_profile(profile_id=base_profile_ids[0])
    diff_lines = compute_profile_diff(base_profile, profile)
    for line in diff_lines:
        print(line)

    if not apply:
        # Dry-run (default per D-03 + D-12). Write to tempfile preview + sidecar.
        import tempfile
        preview_path = Path(tempfile.gettempdir()) / f"{profile['profile_id']}.preview.json"
        preview_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
        sidecar = preview_path.with_suffix(".diff.txt")
        sidecar.write_text("\n".join(diff_lines), encoding="utf-8")
        print(f"Dry-run: профиль записан в {preview_path}. Используй --apply для PROFILES_DIR.")
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

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Профиль сохранен в: {target_path}")
```

**Dispatcher wiring — current `main()` block** (`src/main.py:505-512`):

```python
# Source: src/main.py:505-512 — CURRENT
if args.command == "extract-methodical-profile":
    cmd_extract_methodical_profile(
        input_path=args.input_path,
        output_dir=args.output_dir,
        profile_name=args.profile_name,
        base_profile_ids=args.base_profile_ids,
    )
    return
```

**Phase 5 ADDITION** (three new kwargs threaded through):

```python
# Source: per plan 5-03 — mirror audit-regression dispatch lines 490-502
if args.command == "extract-methodical-profile":
    cmd_extract_methodical_profile(
        input_path=args.input_path,
        output_dir=args.output_dir,
        profile_name=args.profile_name,
        base_profile_ids=args.base_profile_ids,
        apply=args.apply,
        force=args.force,
        reason=args.reason,
    )
    return
```

**Test pattern — `tests/test_cli_parser.py` extension** (analog: existing Phase 4 tests lines 239-281):

```python
# Source: tests/test_cli_parser.py:239-253 — argparse parse_args test analog
def test_cli_parser_accepts_update_baseline_and_reason(tmp_path) -> None:
    parser = build_parser()
    baseline_path = tmp_path / "baseline.json"
    args = parser.parse_args([
        "audit-regression",
        "--positive-dir", "positive_examples",
        "--negative-dir", "negative_examples",
        "--update-baseline", str(baseline_path),
        "--reason", "FIX-XX: root cause locked",
    ])
    assert args.command == "audit-regression"
    assert args.update_baseline == str(baseline_path)
    assert args.reason == "FIX-XX: root cause locked"
```

```python
# Source: tests/test_cli_parser.py:256-281 — dispatcher SystemExit test analog
def test_cmd_audit_regression_refuses_update_baseline_without_reason(tmp_path) -> None:
    positive_dir = tmp_path / "positive"; positive_dir.mkdir()
    negative_dir = tmp_path / "negative"; negative_dir.mkdir()
    baseline_path = tmp_path / "baseline.json"
    for bad_reason in ("", "   ", "abcdefg"):  # 7 chars triggers Probe 6 min-length
        with pytest.raises(SystemExit) as excinfo:
            cmd_audit_regression(
                positive_dir=str(positive_dir), negative_dir=str(negative_dir),
                workspace_dir=str(tmp_path / "ws"), report_csv=None, summary_json=None,
                profile_id="gost_7_32_2017", limit=None, progress=False,
                update_baseline=str(baseline_path), reason=bad_reason,
            )
        assert "--update-baseline" in str(excinfo.value)
        assert "--reason" in str(excinfo.value)
```

**Phase 5 ADDITIONS** (mirror both shapes):

```python
# Plan 5-03 RED tests per RESEARCH §Validation Architecture lines 826-830:
def test_extract_methodical_profile_dry_run_is_default(tmp_path) -> None:
    """No --apply → preview path written, PROFILES_DIR untouched."""
    # ... call cmd_extract_methodical_profile(apply=False); assert target_path not touched

def test_extract_methodical_profile_apply_refuses_overwrite_without_force_reason(tmp_path) -> None:
    """--apply on existing profile path raises SystemExit citing D-004."""
    # ... pre-write target file; call with apply=True, force=False
    with pytest.raises(SystemExit) as excinfo:
        cmd_extract_methodical_profile(..., apply=True, force=False, reason=None)
    assert "D-004" in str(excinfo.value)

def test_extract_methodical_profile_force_refuses_short_reason(tmp_path) -> None:
    """--apply --force on existing target with reason < 8 chars after strip → SystemExit."""
    for bad_reason in ("", "   ", "abcdefg"):
        with pytest.raises(SystemExit):
            cmd_extract_methodical_profile(..., apply=True, force=True, reason=bad_reason)
```

---

### Plan 5-04 — `tests/test_profile_quality_acceptance.py` (NEW) + `src/main.py` SC-1 verify (MODIFY 2 parsers)

**Analog — schema lint:** `tests/test_rules_quality_acceptance.py` (Phase 4 Wave C, commit b8ee13a). RED-carrier via bogus required field; GREEN removes it.

**REQUIRED_FIELDS analog** (`tests/test_rules_quality_acceptance.py:15-26`):

```python
# Source: tests/test_rules_quality_acceptance.py:15-26 (Phase 4 Wave C — RED carrier)
RULES_PATH = Path("src/rules/formatting_rules_v1.json")

REQUIRED_FIELDS = {
    "id", "applicable_labels", "parameter", "expected_value",
    "action", "severity", "autocorrect", "priority",
}
ALLOWED_ACTION_VALUES = {"fix", "review", "check_or_fix"}
ALLOWED_SEVERITY_VALUES = {"low", "medium", "high"}


def _load_rules() -> list[dict]:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))["rules"]
```

**Per-rule iteration + failure aggregation pattern** (lines 33-41):

```python
# Source: tests/test_rules_quality_acceptance.py:33-41 — failure-aggregation shape
def test_every_rule_carries_full_rulerecord_shape() -> None:
    rules = _load_rules()
    assert rules, "formatting_rules_v1.json is empty"
    failures = []
    for rule in rules:
        missing = REQUIRED_FIELDS - set(rule.keys())
        if missing:
            failures.append(f"{rule.get('id', '<no-id>')}: missing fields {sorted(missing)}")
    assert not failures, "\n".join(failures)
```

**Phase 5 GREEN shape** (per RESEARCH §Pattern 4 lines 451-464 + §Pitfall 1 two-tier structure):

```python
# Source: hand-rolled per D-08; analog tests/test_rules_quality_acceptance.py:33-41
from pathlib import Path
import json
from src.rules.profile_validator import validate_profile

PROFILES_DIR = Path("src/rules/profiles")

# RED carrier per RESEARCH §Pattern 4 + §Validation Architecture line 837.
# Remove "__red_placeholder__" in GREEN commit.
REQUIRED_TOP_LEVEL_KEYS_FOR_METHODICAL = {
    "profile_id", "profile_name", "profile_type", "is_default",
    "extraction_meta",
    "__red_placeholder__",  # ← RED carrier; remove in GREEN per Pattern 4
}

def _load_all_profiles() -> list[tuple[Path, dict]]:
    return [(p, json.loads(p.read_text(encoding="utf-8")))
            for p in sorted(PROFILES_DIR.glob("*.json"))]


def test_every_profile_passes_validator() -> None:
    """Tier A — applies to ALL profiles (GOST + methodical). RESEARCH §Pitfall 1."""
    failures = []
    for path, profile in _load_all_profiles():
        errors = validate_profile(profile)
        if errors:
            failures.append(f"{path.name}: {errors}")
    assert not failures, "\n".join(failures)


def test_every_methodical_profile_has_required_top_level_keys() -> None:
    """Tier B — methodical only. RED via bogus key; GREEN removes it."""
    for path, profile in _load_all_profiles():
        if profile.get("profile_type") != "methodical_guidelines":
            continue  # Tier B filter — does NOT apply to hand-authored GOST profiles
        missing = REQUIRED_TOP_LEVEL_KEYS_FOR_METHODICAL - set(profile)
        assert not missing, f"{path.name}: missing {sorted(missing)}"


def test_every_methodical_profile_has_source_per_leaf() -> None:
    """Tier B — vacuous at HEAD (no methodical profile committed yet)."""
    # Walk profile dict; every leaf in document_rules.*, labels.*.style_profile.*,
    # bibliography_rules.* MUST have _source sidecar per D-05.


def test_methodical_needs_manual_review_consistent_with_per_leaf_sources() -> None:
    """Tier B — derived field consistency per D-05."""
    # assert profile["extraction_meta"]["needs_manual_review"] == _any_leaf_needs_review(profile)
```

**Analog — SC-1 verify (add `--profile-id` to `audit-docx` + `format-docx`):** `src/main.py::build_parser` lines 386-391 (`regression_parser.add_argument("--profile-id", ...)`).

**Verbatim source** (lines 386-391):

```python
# Source: src/main.py:386-391 — analog for SC-1 plan 5-04 verify (Pitfall 5)
regression_parser.add_argument(
    "--profile-id",
    required=False,
    default="gost_7_32_2017",
    help="profile_id для safe-formatting",
)
```

**Current `audit_parser` block lacking flag** (`src/main.py:351-357`):

```python
# Source: src/main.py:351-357 — CURRENT audit_parser (missing --profile-id; RESEARCH §Pitfall 5)
audit_parser = subparsers.add_parser(
    "audit-docx",
    help="Построить отчет нормоконтроля без изменения DOCX",
)
audit_parser.add_argument("--input-docx", required=True, help="Путь к исходному DOCX")
audit_parser.add_argument("--predictions-csv", required=True, help="CSV с предсказаниями")
audit_parser.add_argument("--report-csv", required=False, help="Куда сохранить отчет")
```

**Phase 5 ADDITION** (one-line argparse + thread to `cmd_audit_docx` + thread kwarg into `audit_or_format_docx` — already accepts `profile_id` per `src/generate/inplace_formatter.py:325`):

```python
# Plan 5-04 SC-1 verify per Pitfall 5. Copy the same 6-line stanza into format_parser block.
audit_parser.add_argument(
    "--profile-id", required=False, default="gost_7_32_2017",
    help="profile_id для аудита (по умолчанию gost_7_32_2017)",
)
# Then cmd_audit_docx signature gains `profile_id: str` parameter,
# threaded to audit_or_format_docx(profile_id=profile_id).
# main() dispatch (line 472-477) gains `profile_id=args.profile_id`.
```

**Backing API already accepts kwarg** (`src/generate/inplace_formatter.py:318-331`):

```python
# Source: src/generate/inplace_formatter.py:318-331 — audit_or_format_docx ALREADY accepts profile_id
def audit_or_format_docx(
    input_docx: str | Path,
    predictions_csv: str | Path,
    report_csv: str | Path,
    output_docx: str | Path | None = None,
    apply_safe: bool = False,
    profile_path: str | Path | None = None,
    profile_id: str | None = None,  # ← already wired
) -> dict[str, Any]:
    ...
    profile = load_profile(profile_path=profile_path, profile_id=profile_id)
```

**SC-1 verify in CSV/JSON** (already wired per `inplace_formatter.py:504` and `:550` — verify-only, no addition needed):

```python
# Source: src/generate/inplace_formatter.py:504 — per-row CSV column
"profile_id": profile.get("profile_id"),

# Source: src/generate/inplace_formatter.py:550 — summary JSON key
"profile_id": profile.get("profile_id"),
```

---

### Plan 5-05 — `tests/fixtures/methodical/normocontrol_berger.pdf` (NEW binary) + `.github/workflows/regression-gate.yml` (MODIFY) + `Makefile` (MODIFY)

**Analog — committed binary fixture:** `tests/fixtures/heading_minimal.docx` (36773 bytes), `tests/fixtures/bibliography_minimal.docx` (37173 bytes), `tests/fixtures/style_guard_minimal.docx` (36927 bytes). All three are committed binary assets under `tests/fixtures/` — exact precedent for placing the 1.4MB Бергер PDF at `tests/fixtures/methodical/normocontrol_berger.pdf`.

**Layout precedent:**

```
tests/fixtures/
├── bibliography_minimal.docx     # committed binary, 37173 bytes
├── heading_minimal.docx          # committed binary, 36773 bytes
├── style_guard_minimal.docx      # committed binary, 36927 bytes
├── corpus/                       # Phase 4 staging-target subdir
│   ├── positive/
│   └── negative/
└── methodical/                   # NEW per D-06
    └── normocontrol_berger.pdf   # NEW 1.4MB, committed
```

**Analog — CI workflow extension:** `.github/workflows/regression-gate.yml` itself (Phase 4 Wave E).

**Verbatim source — current 4-file pytest invocation** (lines 24-35):

```yaml
# Source: .github/workflows/regression-gate.yml:24-35 (Phase 4 Wave E — analog for plan 5-05)
- name: Stage corpus subset from fixtures
  run: |
    mkdir -p positive_examples negative_examples
    cp tests/fixtures/corpus/positive/* positive_examples/
    cp tests/fixtures/corpus/negative/* negative_examples/
- name: Run regression gate
  run: |
    python -m pytest -q \
      tests/test_negative_corpus_diff_rate.py \
      tests/test_positive_docx_regression.py \
      tests/test_rules_quality_acceptance.py \
      tests/test_format_regression_audit.py
```

**Phase 5 ADDITION** (per RESEARCH §Pattern 5 lines 484-494 + §Pattern 6 lines 511-519 — extend from 4-file to 6-file; methodical fixture lives at its final path so NO additional staging step is needed):

```yaml
# Plan 5-05 GREEN shape — extend existing "Run regression gate" step:
- name: Run regression gate
  run: |
    python -m pytest -q \
      tests/test_negative_corpus_diff_rate.py \
      tests/test_positive_docx_regression.py \
      tests/test_rules_quality_acceptance.py \
      tests/test_format_regression_audit.py \
      tests/test_profile_quality_acceptance.py \
      tests/test_methodical_extractor.py
```

Note: Per RESEARCH §Pattern 5 line 494, **no separate "Stage methodical fixtures" step needed** — the Бергер fixture is committed at its final path (`tests/fixtures/methodical/normocontrol_berger.pdf`) and tests read it directly. The existing Phase 4 corpus-staging step exists only because positive/negative examples were originally outside `tests/`.

**Analog — Makefile extension:** `Makefile` itself, lines 17-21.

**Verbatim source** (`Makefile:17-21`):

```makefile
# Source: Makefile:17-21 (Phase 4 Wave D — analog for plan 5-05)
$(PYTHON) -m pytest -q \
    tests/test_negative_corpus_diff_rate.py \
    tests/test_positive_docx_regression.py \
    tests/test_rules_quality_acceptance.py \
    tests/test_format_regression_audit.py
```

**Phase 5 ADDITION** (symmetric — same two test files):

```makefile
$(PYTHON) -m pytest -q \
    tests/test_negative_corpus_diff_rate.py \
    tests/test_positive_docx_regression.py \
    tests/test_rules_quality_acceptance.py \
    tests/test_format_regression_audit.py \
    tests/test_profile_quality_acceptance.py \
    tests/test_methodical_extractor.py
```

---

## Shared Patterns

### Russian-language UX (D-11)

**Source:** `src/main.py:252-255` (Phase 4 Wave D), throughout `cmd_extract_methodical_profile` print/raise statements at line 297, throughout `_read_pdf_text` error at line 19-22.

**Apply to:** All new CLI error messages in plan 5-03 (`SystemExit` strings) AND all new argparse `help=...` text in plans 5-03 and 5-04.

```python
# Source: src/main.py:252-255 — Russian SystemExit citing D-004
raise SystemExit(
    "--update-baseline требует --reason '<text>' (минимум 8 символов после strip; "
    "D-004: no silent rewrites; RESEARCH.md Probe 6)."
)
```

### `--reason ≥8 chars after strip` guard

**Source:** `src/main.py:251` (Phase 4 Wave D), `tests/test_cli_parser.py:265-280` (test analog).

**Apply to:** Plan 5-03 dispatcher guard + plan 5-03 test trio. The constant `8` is code-not-config per Phase 4 Probe 6 precedent.

```python
# Source: src/main.py:251 — verbatim 8-char strip-minimum predicate
if not reason or len(reason.strip()) < 8:
    raise SystemExit(...)
```

### Russian print success message

**Source:** `src/main.py:297` — `print(f"Профиль сохранен в: {output_path}")`. Phase 5 plan 5-03 reuses verbatim for `--apply` success path; dry-run uses analog `print(f"Dry-run: профиль записан в {preview_path}. Используй --apply для PROFILES_DIR.")`.

### Profile validation entrypoint

**Source:** `src/rules/profile_validator.py:42-116` — `validate_profile(profile: dict[str, Any]) -> list[str]` returns error list; `assert_valid_profile` raises `ValueError`.

**Apply to:** Tier A check in plan 5-04 `test_every_profile_passes_validator`. Do NOT extend `profile_validator.py` for `_source`-shape lint — the Phase 5 plan 5-04 test does the leaf-walk inline (Pitfall 1 + RESEARCH §Don't Hand-Roll line 538).

### Atomic JSON write idiom

**Source:** `src/rules/methodical_extractor.py:371-372` (current `save_methodical_profile`) + `src/evaluation/format_regression_audit.py:260-261` (`write_per_pair_baseline`).

```python
# Source: src/evaluation/format_regression_audit.py:260-261
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
```

**Apply to:** Plan 5-03 target_path write + preview_path write + sidecar.diff.txt write.

### Failure-aggregation test idiom

**Source:** `tests/test_rules_quality_acceptance.py:33-41` — collect all failures into a list, single final `assert not failures, "\n".join(failures)`. Used so the test reports EVERY failing profile/rule, not just the first.

**Apply to:** Plan 5-04 Tier A `test_every_profile_passes_validator` and Tier B `test_every_methodical_profile_has_source_per_leaf` — both should aggregate failures, not short-circuit on first failure.

### Pure-function unit test shape

**Source:** `tests/test_profile_loader.py:15-30` — direct import, call function, assert on returned value. No fixtures, no I/O beyond what the function needs.

**Apply to:** Plan 5-02 `tests/test_profile_diff.py` — `compute_profile_diff` is a pure function over two dicts; tests build dicts inline and assert on returned `list[str]`.

---

## No Analog Found

All Phase 5 NEW/MODIFY targets have in-repo analogs. No files in this phase require fallback to RESEARCH.md generic patterns. The "per-page PDF iteration with location attribution" capability is the only NEW pattern with no direct in-repo precedent, but the underlying primitive (`fitz.open` + `enumerate(doc.pages)`) is already used at `src/rules/methodical_extractor.py:24-25` — the gap is just refactoring the collapse-with-`\n.join` into a yield.

---

## Metadata

**Analog search scope:**
- `src/main.py` (518 LOC, full read)
- `src/rules/methodical_extractor.py` (374 LOC, full read)
- `src/rules/profile_loader.py` (200 LOC, full read)
- `src/rules/profile_validator.py` (123 LOC, full read)
- `src/evaluation/format_regression_audit.py` (262 LOC, full read)
- `src/generate/inplace_formatter.py` (lines 315-560 targeted; grep for `profile_id`)
- `src/rules/profiles/mirea_normcontrol_local.json` (40 lines partial — profile shape sample)
- `tests/test_methodical_extractor.py` (93 LOC, full read)
- `tests/test_cli_parser.py` (281 LOC, full read — Phase 4 Wave D analog at end)
- `tests/test_rules_quality_acceptance.py` (117 LOC, full read — Phase 4 Wave C analog)
- `tests/test_format_regression_audit.py` (108 LOC, full read)
- `tests/test_profile_loader.py` (56 LOC, full read)
- `.github/workflows/regression-gate.yml` (35 LOC, full read)
- `Makefile` (22 LOC, full read)
- `tests/fixtures/` directory listing (committed binary fixture precedent)

**Files scanned:** 15
**Pattern extraction date:** 2026-05-14
