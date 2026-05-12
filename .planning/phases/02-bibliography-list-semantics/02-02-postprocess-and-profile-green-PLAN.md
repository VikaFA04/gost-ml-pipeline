---
phase: 02-bibliography-list-semantics
plan: 02
type: execute
wave: 1
depends_on: [01]
files_modified:
  - src/postprocess/postprocess_rules.py
  - src/rules/profile_loader.py
  - src/rules/profile_validator.py
  - src/rules/profiles/gost_7_32_2017.json
autonomous: true
requirements:
  - REQ-list-conservative-handling
requirements_addressed:
  - REQ-list-conservative-handling
tags:
  - bibliography
  - postprocess
  - profile
  - phase-2

must_haves:
  truths:
    - "BIBLIOGRAPHY_TITLE_RE match unconditionally sets postprocessed_label='bibliography_title' regardless of predicted_label (D-01)."
    - "Inside bibliography context, rows whose `style` string matches HEADING_STYLE_RE advance bibliography_section_index (D-04)."
    - "The legacy BIBLIOGRAPHY_SUBHEADING_RE / BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE constants remain importable and act as a fallback when style-based detection misses (D-04 fallback per Pitfall 4)."
    - "src.rules.profile_loader exports get_list_detection_thresholds(profile) → (40, 300) and get_bibliography_numbering_scope(profile) → 'per_section' for gost_7_32_2017 (D-11, D-03)."
    - "src/rules/profile_validator.validate_profile accepts profiles with new optional sections list_detection.* and numbering.bibliography.scope, AND rejects scope values outside {per_document, per_section, per_subsection_pattern} (D-03)."
    - "src/rules/profiles/gost_7_32_2017.json carries list_detection={max_fallback_words:40, max_fallback_chars:300} and numbering.bibliography.scope='per_section' at top level."
    - "Phase 1 baseline (53 tests) still green; no regression."
    - "All Wave 0 RED tests gated by this plan (D-01 + D-04 + D-04 fallback + D-11 + D-03 + validator-rejects-invalid-scope + validator-accepts-no-optional-sections) turn GREEN."
  artifacts:
    - path: "src/postprocess/postprocess_rules.py"
      provides: "D-01 first-pass unconditional title override + D-04 heading-style subsection detection with regex fallback"
      contains: "for position in range(len(labels))"
    - path: "src/rules/profile_loader.py"
      provides: "get_list_detection_thresholds(), get_bibliography_numbering_scope() helpers"
      contains: "def get_list_detection_thresholds"
    - path: "src/rules/profile_validator.py"
      provides: "Optional schema validation for list_detection + numbering.bibliography.scope"
      contains: "ALLOWED_BIBLIOGRAPHY_SCOPES"
    - path: "src/rules/profiles/gost_7_32_2017.json"
      provides: "Default values for list_detection (40/300) + numbering.bibliography.scope ('per_section')"
      contains: "\"max_fallback_words\": 40"
  key_links:
    - from: "src/postprocess/postprocess_rules.py"
      to: "src/rules/style_signatures.HEADING_STYLE_RE"
      via: "from src.rules.style_signatures import HEADING_STYLE_RE, TOC_STYLE_RE, CAPTION_STYLE_RE, LIST_STYLE_RE"
      pattern: "from src\\.rules\\.style_signatures import"
    - from: "src/rules/profile_loader.py (new helpers)"
      to: "src/rules/profiles/gost_7_32_2017.json"
      via: "profile['list_detection']['max_fallback_words'], profile['numbering']['bibliography']['scope']"
      pattern: "profile\\.get\\(\"list_detection\""
    - from: "src/rules/profile_validator.py"
      to: "ALLOWED_BIBLIOGRAPHY_SCOPES set"
      via: "scope not in ALLOWED_BIBLIOGRAPHY_SCOPES → error"
      pattern: "ALLOWED_BIBLIOGRAPHY_SCOPES"
---

<objective>
Wave 1 GREEN — postprocess + profile. Land D-01 (unconditional bibliography_title override), D-04 (Heading-style subsection detection with regex fallback), D-03 (profile schema scope), and D-11 (profile-driven list thresholds — adding the helpers and JSON fields ONLY; the deletion of `MAX_FALLBACK_LIST_*` constants from rule_engine.py lives in Plan 04 to keep this plan focused on postprocess + profile surface).

Why this plan is one chunk: D-01 + D-04 share `apply_postprocess_rules`; the profile helpers + validator + JSON are mutually dependent (helpers read fields, validator validates fields, JSON carries them). Splitting either would create broken intermediate states. Both surfaces are small and well-scoped.

Purpose: turn the Wave 0 RED tests in this surface GREEN without touching numbering or routing — those land in Plans 03/04.
Output: 4 source files modified; ~9 Wave 0 RED tests turn GREEN; Phase 1 baseline preserved.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@.planning/STATE.md
@.planning/ROADMAP.md
@.planning/phases/02-bibliography-list-semantics/02-CONTEXT.md
@.planning/phases/02-bibliography-list-semantics/02-RESEARCH.md
@.planning/phases/02-bibliography-list-semantics/02-PATTERNS.md
@.planning/phases/01-engine-guardrails-cohesion-audit/01-VERIFICATION.md
@src/postprocess/postprocess_rules.py
@src/rules/profile_loader.py
@src/rules/profile_validator.py
@src/rules/profiles/gost_7_32_2017.json
@src/rules/style_signatures.py
@src/evaluation/format_regression_audit.py
@tests/test_postprocess_rules.py
@tests/test_profile_loader.py
@tests/test_bibliography_phase2.py

<interfaces>
<!-- Existing interfaces this plan consumes -->

From `src/rules/style_signatures.py` (Phase 1):
```python
HEADING_STYLE_RE: re.Pattern[str]
TOC_STYLE_RE: re.Pattern[str]
CAPTION_STYLE_RE: re.Pattern[str]
LIST_STYLE_RE: re.Pattern[str]

def classify_style(paragraph) -> Literal["heading", "toc", "caption", "list", "body"]: ...
```

From `src/postprocess/postprocess_rules.py` (kept intact, used by callers):
```python
BIBLIOGRAPHY_TITLE_RE: re.Pattern  # KEEP (D-02 — regex unchanged)
BIBLIOGRAPHY_SUBHEADING_RE: re.Pattern  # KEEP (fallback per Pitfall 4)
BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE: re.Pattern  # KEEP — src/evaluation/format_regression_audit.py imports it
BIBLIOGRAPHY_STOP_RE: re.Pattern
BIBLIOGRAPHY_ENTRY_RE: re.Pattern

def _is_bibliography_title(text: str) -> bool: ...
def _is_bibliography_subheading(text: str) -> bool: ...
def apply_postprocess_rules(df: pd.DataFrame, pred_col="predicted_label", out_col="postprocessed_label") -> pd.DataFrame: ...
```

From `src/rules/profile_loader.py` (Phase 1):
```python
def load_profile(profile_id: str | None = None) -> dict[str, Any]: ...
def get_target_style_profile(profile, label) -> dict | None: ...
def get_audit_policy(profile, label) -> dict: ...
def get_label_config(profile, label) -> dict | None: ...
```

From `src/rules/profile_validator.py` (Phase 1):
```python
REQUIRED_TOP_LEVEL_KEYS: set[str]  # do NOT modify
REQUIRED_STYLE_KEYS: set[str]
def validate_profile(profile: dict) -> list[str]: ...
def assert_valid_profile(profile: dict) -> None: ...
```

<!-- New interfaces this plan creates (Plans 03/04 will consume) -->

`src/rules/profile_loader.py` NEW exports:
```python
def get_list_detection_thresholds(profile: dict[str, Any]) -> tuple[int, int]:
    """Return (max_fallback_words, max_fallback_chars). Defaults (40, 300)."""

def get_bibliography_numbering_scope(profile: dict[str, Any]) -> str:
    """Return scope. Default 'per_section'."""
```

`src/rules/profile_validator.py` NEW module-level set:
```python
ALLOWED_BIBLIOGRAPHY_SCOPES: set[str] = {"per_document", "per_section", "per_subsection_pattern"}
```

`src/postprocess/postprocess_rules.py` NEW behavior contract:
- D-01: First-pass `for position in range(len(labels))` that unconditionally sets `labels[position] = "bibliography_title"` when `_is_bibliography_title(texts[position])`. Runs BEFORE the existing body_text/list_item rewrite pass at line 130.
- D-04: In the existing in-bibliography loop (lines 160-181), replace the `_is_bibliography_subheading(text)` gate with:
  ```python
  style_class = _row_style_class(row)  # NEW helper
  is_subsection_heading = style_class == "heading" or _is_bibliography_subheading(text)  # fallback
  if is_subsection_heading:
      bibliography_section_index += 1
      ...
  ```
  Drop the `_is_numbered_bibliography_subheading(text)` precondition — every heading-styled (or fallback-regex-matched) row increments the section index.

NEW helper in `src/postprocess/postprocess_rules.py`:
```python
def _row_style_class(row) -> Literal["heading", "toc", "caption", "list", "body"]:
    """Classify by row['style'] string. Order matches classify_style: toc → heading → caption → list → body.
    Try/except → 'body' on any error."""
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Extend src/rules/profile_loader.py + profile_validator.py + gost_7_32_2017.json (D-03 + D-11)</name>
  <files>src/rules/profile_loader.py, src/rules/profile_validator.py, src/rules/profiles/gost_7_32_2017.json</files>
  <read_first>
    - src/rules/profile_loader.py (FULL file — locate lines 165-175 for `get_target_style_profile` analog)
    - src/rules/profile_validator.py (FULL file — lines 40-86 validator loop)
    - src/rules/profiles/gost_7_32_2017.json (lines 270-344 — extraction_meta is last top-level key; insert new keys before the final `}`)
    - src/rules/profiles/mirea_normcontrol_local.json (CONFIRM it does NOT carry list_detection or numbering.bibliography — validator must continue to accept it)
    - src/rules/profiles/gost_r_7_0_100_2018_bibliography.json (same confirmation)
    - .planning/phases/02-bibliography-list-semantics/02-PATTERNS.md §"src/rules/profile_loader.py — D-11 helper getter" + §"src/rules/profile_validator.py — D-03 + D-11 schema extension" + §"src/rules/profiles/gost_7_32_2017.json"
    - tests/test_profile_loader.py (the 4 Wave 0 RED tests — this task makes them all GREEN)
  </read_first>
  <behavior>
    - `profile_loader` exports two new helpers; existing exports unchanged.
    - `profile_validator` adds `ALLOWED_BIBLIOGRAPHY_SCOPES` constant and validates the two new optional sections.
    - `gost_7_32_2017.json` carries `list_detection.{max_fallback_words:40, max_fallback_chars:300}` and `numbering.bibliography.scope = "per_section"` at the top level.
    - `mirea_normcontrol_local.json` and `gost_r_7_0_100_2018_bibliography.json` MUST NOT be modified; they continue to validate via the optional-fields contract.
    - All 4 Wave 0 `test_profile_loader.py` tests turn GREEN.
  </behavior>
  <action>
    **Sub-step 1a — Add two helpers to `src/rules/profile_loader.py`.** Append after `get_audit_policy` (or wherever the existing one-liner helpers cluster — search for `def get_audit_policy` and add immediately after):

    ```python
    def get_list_detection_thresholds(profile: dict[str, Any]) -> tuple[int, int]:
        """D-11: return (max_fallback_words, max_fallback_chars). Defaults 40/300.

        Profile JSON shape:
            {"list_detection": {"max_fallback_words": 40, "max_fallback_chars": 300}}
        """
        cfg = profile.get("list_detection", {}) or {}
        return int(cfg.get("max_fallback_words", 40)), int(cfg.get("max_fallback_chars", 300))


    def get_bibliography_numbering_scope(profile: dict[str, Any]) -> str:
        """D-03: return numbering.bibliography.scope. Default 'per_section'.

        Profile JSON shape:
            {"numbering": {"bibliography": {"scope": "per_section"}}}
        """
        return str(
            profile.get("numbering", {}).get("bibliography", {}).get("scope", "per_section")
        )
    ```

    **Sub-step 1b — Extend `src/rules/profile_validator.py`.** At the TOP of the module (after existing module-level constants `REQUIRED_TOP_LEVEL_KEYS`, `REQUIRED_STYLE_KEYS`), add:

    ```python
    ALLOWED_BIBLIOGRAPHY_SCOPES: set[str] = {"per_document", "per_section", "per_subsection_pattern"}
    ```

    Then in `validate_profile`, AFTER the existing labels loop ends (search for the end of the `for label_name, ... in labels.items()` loop and the closing `return errors` — insert the optional-sections block immediately before `return errors`):

    ```python
        # D-11 — list_detection (optional). If present, must be dict with int fields.
        list_detection = profile.get("list_detection")
        if list_detection is not None:
            if not isinstance(list_detection, dict):
                errors.append("Поле list_detection должно быть словарем")
            else:
                for key in ("max_fallback_words", "max_fallback_chars"):
                    if key in list_detection and not isinstance(list_detection[key], int):
                        errors.append(f"В list_detection поле '{key}' должно быть целым числом")

        # D-03 — numbering.bibliography.scope (optional).
        numbering = profile.get("numbering")
        if numbering is not None:
            if not isinstance(numbering, dict):
                errors.append("Поле numbering должно быть словарем")
            else:
                bibliography_cfg = numbering.get("bibliography")
                if bibliography_cfg is not None:
                    if not isinstance(bibliography_cfg, dict):
                        errors.append("Поле numbering.bibliography должно быть словарем")
                    else:
                        scope = bibliography_cfg.get("scope")
                        if scope is not None and scope not in ALLOWED_BIBLIOGRAPHY_SCOPES:
                            errors.append(
                                f"Недопустимое numbering.bibliography.scope='{scope}'; "
                                f"допустимые: {sorted(ALLOWED_BIBLIOGRAPHY_SCOPES)}"
                            )
    ```

    CRITICAL: do NOT add `list_detection` or `numbering` to `REQUIRED_TOP_LEVEL_KEYS`. Both sections are optional. The validator only checks them WHEN PRESENT.

    **Sub-step 1c — Extend `src/rules/profiles/gost_7_32_2017.json`.** The file currently ends at line 344 with `}` after `extraction_meta`. Insert two new top-level keys before the final `}`. After this edit, the file structure must be:

    ```json
    {
      ...existing keys...,
      "extraction_meta": { ... },
      "list_detection": {
        "max_fallback_words": 40,
        "max_fallback_chars": 300
      },
      "numbering": {
        "bibliography": {
          "scope": "per_section"
        }
      }
    }
    ```

    Do NOT touch `mirea_normcontrol_local.json` or `gost_r_7_0_100_2018_bibliography.json` — they remain unmodified (optional fields contract).
  </action>
  <verify>
    <automated>python -c "from src.rules.profile_loader import load_profile, get_list_detection_thresholds, get_bibliography_numbering_scope; p=load_profile(profile_id='gost_7_32_2017'); assert get_list_detection_thresholds(p)==(40,300), get_list_detection_thresholds(p); assert get_bibliography_numbering_scope(p)=='per_section', get_bibliography_numbering_scope(p); print('helpers OK')" && python -c "from src.rules.profile_loader import load_profile; load_profile(profile_id='mirea_normcontrol_local'); load_profile(profile_id='gost_r_7_0_100_2018_bibliography'); print('optional sections OK — other profiles validate')" && python -m pytest tests/test_profile_loader.py -x -q 2>&1 | tail -10</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c "def get_list_detection_thresholds" src/rules/profile_loader.py` returns `1`.
    - `grep -c "def get_bibliography_numbering_scope" src/rules/profile_loader.py` returns `1`.
    - `grep -c "ALLOWED_BIBLIOGRAPHY_SCOPES" src/rules/profile_validator.py` returns `≥2` (definition + reference).
    - `python -c "import json; data=json.load(open('src/rules/profiles/gost_7_32_2017.json')); assert data['list_detection']['max_fallback_words']==40; assert data['list_detection']['max_fallback_chars']==300; assert data['numbering']['bibliography']['scope']=='per_section'; print('JSON OK')"` exits 0.
    - `python -c "import json; data=json.load(open('src/rules/profiles/mirea_normcontrol_local.json')); assert 'list_detection' not in data; assert 'numbering' not in data; print('mirea unchanged')"` exits 0.
    - `python -m pytest tests/test_profile_loader.py -x -q` exits 0 — all 4 tests GREEN (test_list_detection_thresholds_from_profile, test_bibliography_numbering_scope_default_is_per_section, test_validator_accepts_profile_without_optional_sections, test_validator_rejects_invalid_scope).
    - Phase 1 baseline `python -m pytest tests/ -x -q -k "not bibliography_phase2 and not test_bibliography_title_overrides_svm_body_text and not test_bibliography_subsection_detected_by_heading_style and not test_bibliography_subsection_fallback_regex_still_works"` exits 0 (no Phase 1 regression — exclude Wave 0 RED tests that this plan does not gate).
  </acceptance_criteria>
  <done>2 helpers added; validator extended with optional schema validation; gost_7_32_2017.json carries new fields; other profiles untouched; 4 Wave 0 profile_loader tests GREEN.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: D-01 unconditional title override + D-04 heading-style subsection detection in postprocess_rules.py</name>
  <files>src/postprocess/postprocess_rules.py</files>
  <read_first>
    - src/postprocess/postprocess_rules.py (FULL file — lines 1-30 imports, lines 110-206 apply_postprocess_rules)
    - src/rules/style_signatures.py (FULL file — HEADING_STYLE_RE, TOC_STYLE_RE, CAPTION_STYLE_RE, LIST_STYLE_RE patterns + classify_style order)
    - .planning/phases/02-bibliography-list-semantics/02-RESEARCH.md §"Example A" (D-01 pre-pass) + §"Example B" (D-04 detection — lines 246-282)
    - .planning/phases/02-bibliography-list-semantics/02-PATTERNS.md §"src/postprocess/postprocess_rules.py — D-01 unconditional override + D-04 position+heading detection" lines 31-84
    - .planning/phases/02-bibliography-list-semantics/02-RESEARCH.md §"Pitfall 4" lines 224-228 (BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE MUST stay importable)
    - src/evaluation/format_regression_audit.py (CONFIRM lines 19-22, 50-51 still import BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE — this plan must NOT remove that constant)
    - tests/test_postprocess_rules.py (3 RED tests this plan must turn GREEN)
    - tests/test_bibliography_phase2.py (D-14 integration tests — they exercise the same code path)
  </read_first>
  <behavior>
    - D-01: A new pre-pass at the start of each group's iteration unconditionally sets `labels[position] = "bibliography_title"` whenever `_is_bibliography_title(texts[position])`. Runs BEFORE the existing body_text/list_item rewrite pass at line 130 and BEFORE the in_bibliography loop at line 160.
    - D-04: A new helper `_row_style_class(row)` classifies the row's `style` string into one of the 5 StyleClass values using the regexes from `style_signatures`. The existing in_bibliography loop's subsection-detection gate becomes `style_class == "heading" or _is_bibliography_subheading(text)`. Every detected subsection increments `bibliography_section_index` (drop the `_is_numbered_bibliography_subheading` precondition).
    - Existing `BIBLIOGRAPHY_TITLE_RE`, `BIBLIOGRAPHY_SUBHEADING_RE`, `BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE` regex constants STAY intact (Pitfall 4).
    - 3 Wave 0 RED tests in test_postprocess_rules.py turn GREEN.
    - The D-14 integration tests in test_bibliography_phase2.py move closer to GREEN (D-14 needs Plan 03 for numbering — this plan only fixes label/section_index).
  </behavior>
  <action>
    **Sub-step 2a — Add imports** at the top of `src/postprocess/postprocess_rules.py`. Find the existing import block (lines 1-10 area) and add ONE new import statement:

    ```python
    from src.rules.style_signatures import HEADING_STYLE_RE, TOC_STYLE_RE, CAPTION_STYLE_RE, LIST_STYLE_RE
    ```

    Do NOT import `classify_style` itself — it takes a `Paragraph`, not a row.

    **Sub-step 2b — Add a private helper** `_row_style_class` near the other module-level helpers (search for `def _is_bibliography_title` — place the new helper just above or below it, in the helpers cluster). Implementation mirrors the regex priority of `classify_style` (toc → heading → caption → list → body):

    ```python
    def _row_style_class(row) -> str:
        """Classify a DataFrame row's `style` string into one of the 5 StyleClass values.

        Priority matches src.rules.style_signatures.classify_style:
            toc → heading → caption → list → body.

        Returns 'body' on any error or empty/missing style.
        """
        try:
            style_value = row.get("style", "") if hasattr(row, "get") else ""
            if not isinstance(style_value, str) or not style_value:
                return "body"
            if TOC_STYLE_RE.search(style_value):
                return "toc"
            if HEADING_STYLE_RE.search(style_value):
                return "heading"
            if CAPTION_STYLE_RE.search(style_value):
                return "caption"
            if LIST_STYLE_RE.search(style_value):
                return "list"
            return "body"
        except Exception:
            return "body"
    ```

    **Sub-step 2c — Add the D-01 pre-pass** inside `apply_postprocess_rules`. The function iterates groups via `for _, group in df.groupby("doc_id", sort=False):` (line 123). Inside that loop, AFTER `texts = [...]` (line 126) and `section_indices: list[int | None] = [None] * len(labels)` (line 127), BEFORE the existing `for position, (_, row) in enumerate(group.iterrows()):` at line 129, insert:

    ```python
            # D-01 — unconditional bibliography_title override. Runs BEFORE all other
            # label-rewriting passes. BIBLIOGRAPHY_TITLE_RE matches → label becomes
            # bibliography_title regardless of SVM's predicted_label.
            for position in range(len(labels)):
                if _is_bibliography_title(texts[position]):
                    labels[position] = "bibliography_title"
    ```

    **Sub-step 2d — Rewrite the in_bibliography loop body** (current lines 160-181) to use D-04 style-class detection while preserving the fallback regex. Replace the existing block:

    ```python
            in_bibliography = False
            bibliography_section_index = 0
            for position, (_, row) in enumerate(group.iterrows()):
                text = texts[position]
                label = labels[position]
                if _is_bibliography_title(text):
                    labels[position] = "bibliography_title"
                    in_bibliography = True
                    continue
                if in_bibliography and _stops_bibliography_context(text, label):
                    in_bibliography = False
                if not in_bibliography:
                    continue
                if _is_bibliography_subheading(text):
                    if _is_numbered_bibliography_subheading(text):
                        bibliography_section_index += 1
                    if label not in {"title_section", "title_subsection"}:
                        labels[position] = "bibliography_title"
                    section_indices[position] = bibliography_section_index or None
                elif label in {"body_text", "list_item"} and _looks_like_bibliography_entry(row, text):
                    labels[position] = "bibliography_item"
                    section_indices[position] = bibliography_section_index or None
    ```

    With:

    ```python
            in_bibliography = False
            bibliography_section_index = 0
            for position, (_, row) in enumerate(group.iterrows()):
                text = texts[position]
                label = labels[position]
                if _is_bibliography_title(text):
                    labels[position] = "bibliography_title"
                    in_bibliography = True
                    continue
                if in_bibliography and _stops_bibliography_context(text, label):
                    in_bibliography = False
                if not in_bibliography:
                    continue

                # D-04 — subsection detection: primary signal is Heading 1/2/3 style;
                # fallback is the legacy BIBLIOGRAPHY_SUBHEADING_RE so that
                # src.evaluation.format_regression_audit.infer_regression_label (which
                # uses synthetic predictions WITHOUT a real style string) keeps working.
                style_class = _row_style_class(row)
                is_subsection_heading = (
                    style_class == "heading"
                    or _is_bibliography_subheading(text)
                )
                if is_subsection_heading:
                    bibliography_section_index += 1
                    if label not in {"title_section", "title_subsection"}:
                        labels[position] = "bibliography_title"
                    section_indices[position] = bibliography_section_index or None
                elif label in {"body_text", "list_item"} and _looks_like_bibliography_entry(row, text):
                    labels[position] = "bibliography_item"
                    section_indices[position] = bibliography_section_index or None
    ```

    Critical difference from current behavior: `_is_numbered_bibliography_subheading(text)` was gating section_index increment — now EVERY subsection heading (style-detected OR regex fallback) increments. This matches D-04 ("bibliography_section_index increments on each Heading 1 inside bibliography context").

    Do NOT delete `_is_numbered_bibliography_subheading` from the module — keep it for callers (grep `grep -n "_is_numbered_bibliography_subheading" src/ tests/` before removal; only Plan 04 may decide to retire it).

    **Sub-step 2e — Smoke-test imports** to confirm no circular import is introduced by importing from `style_signatures`:

    ```bash
    python -c "from src.postprocess.postprocess_rules import apply_postprocess_rules, _row_style_class; print('imports OK')"
    ```
  </action>
  <verify>
    <automated>python -m pytest tests/test_postprocess_rules.py -x -q 2>&1 | tail -25 && python -m pytest tests/test_postprocess_rules.py::test_bibliography_title_overrides_svm_body_text tests/test_postprocess_rules.py::test_bibliography_subsection_detected_by_heading_style -x -q 2>&1 | tail -10</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c "from src.rules.style_signatures import HEADING_STYLE_RE" src/postprocess/postprocess_rules.py` returns `1`.
    - `grep -c "def _row_style_class" src/postprocess/postprocess_rules.py` returns `1`.
    - `grep -c "D-01" src/postprocess/postprocess_rules.py` returns `≥1` (anchor comment for the new pre-pass).
    - `grep -c "D-04" src/postprocess/postprocess_rules.py` returns `≥1` (anchor comment for the new detection block).
    - `grep -c "BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE\s*=" src/postprocess/postprocess_rules.py` returns `1` (constant preserved).
    - `python -c "from src.evaluation.format_regression_audit import build_regression_predictions; print('format_regression_audit import OK')"` exits 0 (no Pitfall 4 regression).
    - `python -m pytest tests/test_postprocess_rules.py::test_bibliography_title_overrides_svm_body_text -x -q` exits 0 — D-01 turns GREEN.
    - `python -m pytest tests/test_postprocess_rules.py::test_bibliography_subsection_detected_by_heading_style -x -q` exits 0 — D-04 turns GREEN.
    - `python -m pytest tests/test_postprocess_rules.py -x -q` exits 0 — entire file green (D-04 fallback test may skip if no candidate matches the regex, that's acceptable).
    - Phase 1 baseline (`python -m pytest tests/test_style_signatures.py tests/test_rule_engine.py tests/test_positive_docx_regression.py -x -q`) still 53/53 GREEN.
  </acceptance_criteria>
  <done>D-01 + D-04 land in postprocess; 2-3 Wave 0 RED tests in test_postprocess_rules.py GREEN; Phase 1 baseline preserved; format_regression_audit still imports cleanly.</done>
</task>

</tasks>

<verification>
After all 2 tasks complete:

```bash
python -m pytest tests/ -x -q 2>&1 | tail -30
```

Expected outcome:
- Phase 1 baseline preserved: 53/53 tests still pass.
- Wave 0 tests this plan gates turn GREEN:
  - tests/test_profile_loader.py — 4 tests GREEN.
  - tests/test_postprocess_rules.py — 2 new RED tests GREEN (the fallback regex test may skip).
- Wave 0 tests gated by Plans 03/04 still RED:
  - tests/test_bibliography_phase2.py — D-05/06/07 tests still RED (numbering not changed); D-09 still RED (routing not added); D-13 still RED; D-14 integration still RED.
- D-14 integration tests on bibliography_minimal.docx now likely produce CSV reports where bibliography_title rows are correctly labeled (D-01) and bibliography_section_index is stamped (D-04) — but numbering is still legacy-singleLevel → applied_fixes still uses old shape.
</verification>

<success_criteria>
- src/rules/profile_loader.py exports get_list_detection_thresholds + get_bibliography_numbering_scope returning the documented defaults.
- src/rules/profile_validator.py defines ALLOWED_BIBLIOGRAPHY_SCOPES and rejects scope outside the set; accepts profiles without optional sections.
- src/rules/profiles/gost_7_32_2017.json carries list_detection.{max_fallback_words:40, max_fallback_chars:300} and numbering.bibliography.scope='per_section'.
- src/postprocess/postprocess_rules.py D-01 pre-pass + D-04 heading-style detection (with regex fallback) wired without removing existing exports.
- All 4 Wave 0 test_profile_loader.py tests GREEN.
- 2 of 3 Wave 0 test_postprocess_rules.py tests GREEN (fallback regex test may skip).
- Phase 1 baseline 53/53 still GREEN.
- No production constants deleted yet — Plan 04 handles MAX_FALLBACK_LIST_* removal as a coordinated change with the numbering switch.
</success_criteria>

<output>
After completion, create `.planning/phases/02-bibliography-list-semantics/02-02-postprocess-and-profile-green-SUMMARY.md` documenting:
- Files modified: 4 with line-counts (added/removed).
- Wave 0 tests turned GREEN (exact names).
- Wave 0 tests still RED (handoff to Plans 03/04).
- Confirmation that other profile JSONs (mirea, gost_r_7_0_100_2018) remain unmodified and validate.
- Confirmation that BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE is still importable from postprocess_rules.py (Pitfall 4 guard).
- Phase 1 baseline test count + result.
</output>
</content>
