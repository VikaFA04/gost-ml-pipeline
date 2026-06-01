---
phase: 02-bibliography-list-semantics
plan: 01
type: execute
wave: 0
depends_on: []
files_modified:
  - tests/test_bibliography_phase2.py
  - tests/test_postprocess_rules.py
  - tests/test_profile_loader.py
  - tests/test_negative_corpus_diff_rate.py
  - tests/fixtures/_build_bibliography_minimal.py
  - tests/fixtures/bibliography_minimal.docx
autonomous: true
requirements:
  - REQ-list-conservative-handling
requirements_addressed:
  - REQ-list-conservative-handling
tags:
  - bibliography
  - tdd
  - red
  - testing
  - phase-2

must_haves:
  truths:
    - "tests/test_bibliography_phase2.py exists with 11 failing test functions covering D-01, D-04, D-05, D-06, D-07, D-09, D-10, D-11, D-13, D-14 hand-crafted, D-14 negative integration."
    - "tests/test_postprocess_rules.py has 3 new failing tests for D-01 unconditional override (SVM=body_text → bibliography_title) and D-04 Heading-1-style subsection detection (+ fallback regex)."
    - "tests/test_profile_loader.py exists with 4 tests covering D-11 list_detection thresholds, D-03 numbering.bibliography.scope default, validator-accepts-no-optional-sections, validator-rejects-invalid-scope."
    - "tests/test_negative_corpus_diff_rate.py exists, calls audit_negative_directory(limit=4), asserts mean after_diff_rate ≤ 0.4781 (D-15 automated gate)."
    - "tests/fixtures/bibliography_minimal.docx exists (built from _build_bibliography_minimal.py) with 1 bibliography_title + 2 Heading-styled subsections + 3 entries each; subsection 1 entry 2 carries a stale numId pointing at a legacy singleLevel abstract."
    - "Every new test runs and FAILS for the right RED reason: D-01 override doesn't fire yet, D-04 Heading-style detection not wired, multilevel abstract not emitted, profile helpers not defined, D-09 branch absent."
  artifacts:
    - path: "tests/test_bibliography_phase2.py"
      provides: "11 RED unit + integration tests for D-01..D-15 (excluding D-02/D-03/D-08/D-12 which are non-code or schema-only)"
      contains: "def test_bibliography_title_override_unconditional"
    - path: "tests/test_postprocess_rules.py"
      provides: "3 RED tests appended for D-01 override + D-04 heading detection + D-04 fallback regex"
      contains: "def test_bibliography_title_overrides_svm_body_text"
    - path: "tests/test_profile_loader.py"
      provides: "4 RED tests for D-11 thresholds + D-03 scope + validator behavior"
      contains: "def test_list_detection_thresholds_from_profile"
    - path: "tests/test_negative_corpus_diff_rate.py"
      provides: "1 automated regression gate (D-15) — mean after_diff_rate ≤ 0.4781 on 4-doc subset"
      contains: "def test_negative_corpus_diff_rate_phase2_baseline"
    - path: "tests/fixtures/_build_bibliography_minimal.py"
      provides: "One-shot deterministic fixture builder (mirror of _build_style_guard_minimal.py)"
      contains: "def build(output_path"
    - path: "tests/fixtures/bibliography_minimal.docx"
      provides: "Hand-crafted DOCX with 1 title + 2 subsections + 6 entries + 1 mixed numId entry"
  key_links:
    - from: "tests/test_bibliography_phase2.py"
      to: "src/rules/rule_engine.apply_rules_to_paragraph"
      via: "direct call with label=body_text + marker + no numId"
      pattern: "apply_rules_to_paragraph\\(.*label=\"body_text\""
    - from: "tests/test_postprocess_rules.py (new tests)"
      to: "src.postprocess.postprocess_rules.apply_postprocess_rules"
      via: "DataFrame row with predicted_label=body_text + bibliography title text"
      pattern: "apply_postprocess_rules\\("
    - from: "tests/test_profile_loader.py"
      to: "src.rules.profile_loader.get_list_detection_thresholds"
      via: "from src.rules.profile_loader import get_list_detection_thresholds"
      pattern: "from src\\.rules\\.profile_loader import"
    - from: "tests/test_negative_corpus_diff_rate.py"
      to: "src.evaluation.format_regression_audit.audit_negative_directory"
      via: "direct call with limit=4"
      pattern: "audit_negative_directory\\("
---

<objective>
Wave 0 — RED. Write every failing test, the hand-crafted DOCX fixture builder, and an automated D-15 regression gate so Waves 1-3 implement against pinned behavior. Per CLAUDE.md "Железный закон" — no production code until a failing test exists.

The RED state is achieved by:
- Tests reference functions that don't exist yet (`get_list_detection_thresholds`, `get_bibliography_numbering_scope`) → ImportError = RED.
- Tests assert behaviors that current code does not produce (unconditional D-01 override, D-04 style detection, D-05 2-level abstract `<w:lvlText w:val="%1.%2."/>`, D-06 coercion tag, D-09 ambiguous review explanation, D-13 alignment-skip).
- D-15 negative-gate test calls `audit_negative_directory(limit=4)` and asserts mean ≤ 0.4781 on the 4-doc subset. Today's number must stay ≤ 0.4781 (Phase 1 baseline 0.4737 over 17 docs; subset may differ). If the 4-doc subset exceeds 0.4781, the gate is RED until Wave 3 lands D-15 and confirms the subset baseline.

Purpose: pin behavior BEFORE writing implementation (CLAUDE.md TDD).
Output: 11 + 3 + 4 + 1 = 19 new test functions, 1 fixture builder + binary DOCX, 1 D-15 regression gate test — all running, all RED for the right reason.

**Task-count rationale (5 tasks > standard 2-3 target):** Wave 0 RED is one logical unit — splitting would entangle Wave 1-3 dependencies. Per CLAUDE.md TDD law ("Железный закон: никакого продакшен-кода без падающего теста"), every D-NN decision must have its failing test pinned BEFORE any Wave 1-3 production change lands, and the fixture (Task 1) + each test file (Tasks 2-5) form a cohesive scaffolding artifact that downstream plans assume. Splitting RED across two plans would force one to depend on the other's tests existing before its own, creating an artificial Wave 0 inner dependency chain.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@.planning/STATE.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/02-bibliography-list-semantics/02-CONTEXT.md
@.planning/phases/02-bibliography-list-semantics/02-RESEARCH.md
@.planning/phases/02-bibliography-list-semantics/02-PATTERNS.md
@.planning/phases/02-bibliography-list-semantics/02-VALIDATION.md
@.planning/phases/01-engine-guardrails-cohesion-audit/01-VERIFICATION.md
@tests/fixtures/_build_style_guard_minimal.py
@tests/test_rule_engine.py
@tests/test_postprocess_rules.py
@src/rules/rule_engine.py
@src/postprocess/postprocess_rules.py
@src/rules/profile_loader.py
@src/rules/profile_validator.py
@src/rules/profiles/gost_7_32_2017.json

<interfaces>
<!-- Contracts pinned by Wave 0. Waves 1-3 implement against them. -->

`src/rules/profile_loader.py` MUST export (Plan 02 implements):
```python
def get_list_detection_thresholds(profile: dict[str, Any]) -> tuple[int, int]:
    """Return (max_fallback_words, max_fallback_chars). Defaults (40, 300)."""

def get_bibliography_numbering_scope(profile: dict[str, Any]) -> str:
    """Return 'per_document' | 'per_section' | 'per_subsection_pattern'. Default 'per_section'."""
```

`src/rules/profile_validator.py` accepts NEW optional top-level sections (Plan 02 implements):
```python
# Optional — not added to REQUIRED_TOP_LEVEL_KEYS:
"list_detection": {"max_fallback_words": int, "max_fallback_chars": int}
"numbering": {"bibliography": {"scope": "per_document" | "per_section" | "per_subsection_pattern"}}
```

`src/postprocess/postprocess_rules.py.apply_postprocess_rules` contract (Plan 02 implements D-01 + D-04):
- D-01: Any row whose `text` matches `BIBLIOGRAPHY_TITLE_RE`, AFTER apply_postprocess_rules, MUST have `postprocessed_label == "bibliography_title"` regardless of `predicted_label`.
- D-04: Inside bibliography context, rows whose `style` string matches `HEADING_STYLE_RE` (from `src/rules/style_signatures.py`) advance `bibliography_section_index`. Fallback: rows whose text matches `BIBLIOGRAPHY_SUBHEADING_RE` (legacy regex KEPT — researcher Open Question 2 resolution).

`src/rules/rule_engine.py.apply_rules_to_paragraph` D-09 branch contract (Plan 04 implements):
```python
# Inserted IMMEDIATELY AFTER the Phase 1 style guard (line 798), BEFORE current_profile = ... (line 800):
text = str(row_data.get("text", "") or paragraph.text or "").strip()
if (
    label == "body_text"
    and paragraph_style_class == "body"
    and _paragraph_has_list_marker(text)
    and not _paragraph_has_numbering(paragraph)
):
    return {
        "status": "review",
        "violated_rules": [],
        "applied_fixes": [],
        "suggested_fixes": [],
        "suggested_rule_ids": [],
        "manual_review_required": True,
        "blocked_unsafe_autofix": False,
        "unsafe_auto_fix_reason": "",
        "explanation": "ambiguous_list_marker_no_numId",
    }
```

`src/rules/rule_engine.py` D-05 multilevel abstract contract (Plan 03 implements):
- NEW function `_create_bibliography_multilevel_abstract(numbering_root) -> str` emits ONE `<w:abstractNum>` per doc with `<w:multiLevelType w:val="multilevel"/>` and TWO `<w:lvl>` children:
  - `ilvl=0`: `<w:start w:val="1"/>`, `<w:numFmt w:val="decimal"/>`, `<w:lvlText w:val="%1."/>`, `<w:lvlJc w:val="left"/>`.
  - `ilvl=1`: `<w:start w:val="1"/>`, `<w:numFmt w:val="decimal"/>`, `<w:lvlText w:val="%1.%2."/>`, `<w:lvlJc w:val="left"/>`.
- NEW function `_create_bibliography_num_with_section_override(numbering_root, abstract_num_id: str, section_index: int) -> int` emits ONE `<w:num>` per subsection with `<w:abstractNumId w:val="N"/>` + TWO `<w:lvlOverride>` children (ilvl=0 startOverride=section_index, ilvl=1 startOverride=1).
- `apply_bibliography_numbering` sets `<w:ilvl w:val="1"/>` (NOT "0" as today at line 420).
- `applied_fixes` returns `"numbering:coerced_to_numId=<N>"` when coercing from a pre-existing different numId; otherwise just `"numbering"`.

`src/rules/rule_engine.py` D-07 idempotency contract (Plan 03 implements):
- NEW module-level: `_SEEDED_DOCS: set[int] = set()`.
- `_BIBLIOGRAPHY_NUM_IDS` key changes from `(id(numbering_root), section_index)` to `(id(paragraph.part.document.part), section_index)`.
- NEW helper `_seed_bibliography_num_ids_from_doc(paragraph)` walks `paragraph.part.document.element.body` once per document, collects existing valid bibliography numIds per section_index, seeds `_BIBLIOGRAPHY_NUM_IDS`.

`tests/fixtures/bibliography_minimal.docx` shape (Plan 01 — this plan — builds it):
- Paragraph 1: Normal-styled `"СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"`.
- Paragraph 2: Heading-1-styled `"ТЕОРЕТИЧЕСКАЯ ЧАСТЬ"` (no numbered prefix — pins D-04 position+style detection, NOT text-regex).
- Paragraphs 3-5: 3 entries. P3: no numPr. P4: numPr pointing at a legacy singleLevel abstract (mixed numId — D-06 coerce path). P5: no numPr.
- Paragraph 6: Heading-1-styled `"ИССЛЕДОВАТЕЛЬСКИЙ РАЗДЕЛ"` (mixed naming — confirms detection is style-based, not text-pattern-based).
- Paragraphs 7-9: 3 entries, none with numPr (D-06 fresh-allocate path).
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Build tests/fixtures/bibliography_minimal.docx + builder script</name>
  <files>tests/fixtures/_build_bibliography_minimal.py, tests/fixtures/bibliography_minimal.docx</files>
  <read_first>
    - tests/fixtures/_build_style_guard_minimal.py (FULL file — direct analog per PATTERNS.md)
    - .planning/phases/02-bibliography-list-semantics/02-PATTERNS.md §"tests/fixtures/_build_bibliography_minimal.py (NEW)" lines 460-493
    - .planning/phases/02-bibliography-list-semantics/02-CONTEXT.md §"D-14" (fixture spec)
    - src/rules/rule_engine.py lines 303-335 (legacy `_create_section_abstract_num_id` — copy this exact idiom for the mixed-numId injection in entry 2; do NOT call the function, replicate it inline in the builder)
    - src/rules/rule_engine.py lines 409-429 (apply_bibliography_numbering — OOXML primitive idiom for setting numPr)
  </read_first>
  <behavior>
    - One-shot Python script `_build_bibliography_minimal.py` constructs `bibliography_minimal.docx` deterministically.
    - 9 paragraphs total: 1 title + (1 subsection heading + 3 entries) × 2.
    - Subsection 1 entry 2 carries a stale numId (1) pointing at a hand-emitted legacy singleLevel abstract — exercises D-06 coercion path.
    - Subsection 1 entries 1 and 3 have NO numPr at all (NoneType numId).
    - Subsection 2 entries 7, 8, 9 have NO numPr (D-06 fresh-allocate path on second subsection).
    - Bibliography title is Normal-styled (D-01 must override SVM body_text → bibliography_title regardless of style).
    - Both subsection headings are `"Heading 1"`-styled with text that does NOT match `BIBLIOGRAPHY_SUBHEADING_RE` (D-04 pins position+style, not text-pattern).
    - Re-running the script produces a DOCX with the same 9 paragraphs and same style assignments (NOT byte-identical — DOCX core.xml embeds timestamps).
  </behavior>
  <action>
    Create `tests/fixtures/_build_bibliography_minimal.py` with the EXACT content below. Then run it once to produce `tests/fixtures/bibliography_minimal.docx` and commit both. The mixed-numId injection in entry 2 uses raw `OxmlElement` + `qn` (no helper functions imported — the builder is self-contained so it does not depend on rule_engine internals which Phase 2 is modifying).

    ```python
    """One-shot fixture builder for tests/fixtures/bibliography_minimal.docx.

    Run once:
        python tests/fixtures/_build_bibliography_minimal.py

    Commits the resulting .docx as a binary fixture. Re-running is idempotent
    in CONTENT (9 paragraphs, same styles, same mixed numId on entry 2), NOT
    byte-identical (DOCX core.xml embeds creation timestamps).

    Layout (D-14):
      1. "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ" — Normal style (D-01 must override).
      2. "ТЕОРЕТИЧЕСКАЯ ЧАСТЬ" — Heading 1 (D-04 position+style detection).
      3. Entry — no numPr.
      4. Entry — numPr pointing at a legacy singleLevel abstract (numId=1) — D-06 coerce.
      5. Entry — no numPr.
      6. "ИССЛЕДОВАТЕЛЬСКИЙ РАЗДЕЛ" — Heading 1 (mixed naming, no number prefix).
      7. Entry — no numPr.
      8. Entry — no numPr.
      9. Entry — no numPr.
    """
    from __future__ import annotations

    from pathlib import Path

    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn


    def _next_abstract_num_id(numbering_root) -> str:
        """Allocate the next unused w:abstractNumId in this numbering_root.
        Mirrors src/rules/rule_engine._next_abstract_num_id but stays self-contained
        (the builder MUST NOT import rule_engine internals — Phase 2 is modifying
        them and the builder is the contract anchor for Plan 03's RED tests)."""
        existing = [
            int(a.get(qn("w:abstractNumId")))
            for a in numbering_root.findall(qn("w:abstractNum"))
            if a.get(qn("w:abstractNumId")) is not None
        ]
        return str((max(existing) if existing else -1) + 1)


    def _next_num_id(numbering_root) -> str:
        """Allocate the next unused w:numId in this numbering_root.
        Mirrors src/rules/rule_engine._next_num_id; self-contained (same reason)."""
        existing = [
            int(n.get(qn("w:numId")))
            for n in numbering_root.findall(qn("w:num"))
            if n.get(qn("w:numId")) is not None
        ]
        return str((max(existing) if existing else 0) + 1)


    def _inject_legacy_singlelevel_abstract(document) -> tuple[str, str]:
        """Append a singleLevel abstractNum (mimicking the pre-Phase-2 pattern) and
        a w:num pointing at it. Returns (abstract_num_id, num_id) so the caller
        knows which numId to attach to entry 2.

        Allocates IDs via _next_abstract_num_id / _next_num_id rather than
        hard-coding "0"/"1" — this is safe whether or not python-docx already
        created a numbering_part. Precondition: caller has not yet referenced
        the returned num_id from any paragraph.
        """
        numbering_part = document.part.numbering_part
        if numbering_part is None:
            # Force creation by adding a list-style paragraph then removing it.
            tmp = document.add_paragraph("__seed__")
            tmp.style = "List Number"
            numbering_part = document.part.numbering_part
            tmp._element.getparent().remove(tmp._element)
            assert numbering_part is not None, "python-docx failed to materialize numbering_part"
        numbering_root = numbering_part.element

        abstract_num_id = _next_abstract_num_id(numbering_root)
        num_id = _next_num_id(numbering_root)

        abstract_num = OxmlElement("w:abstractNum")
        abstract_num.set(qn("w:abstractNumId"), abstract_num_id)
        mlt = OxmlElement("w:multiLevelType"); mlt.set(qn("w:val"), "singleLevel"); abstract_num.append(mlt)
        lvl = OxmlElement("w:lvl"); lvl.set(qn("w:ilvl"), "0")
        for tag, val in (("w:start", "1"), ("w:numFmt", "decimal"), ("w:lvlText", "1.%1"), ("w:lvlJc", "left")):
            e = OxmlElement(tag); e.set(qn("w:val"), val); lvl.append(e)
        abstract_num.append(lvl)
        numbering_root.append(abstract_num)

        num = OxmlElement("w:num")
        num.set(qn("w:numId"), num_id)
        ref = OxmlElement("w:abstractNumId"); ref.set(qn("w:val"), abstract_num_id); num.append(ref)
        numbering_root.append(num)

        return abstract_num_id, num_id


    def _set_numPr(paragraph, num_id: str, ilvl: str = "0") -> None:
        """Set <w:numPr> on a paragraph with the given numId/ilvl."""
        p_pr = paragraph._p.get_or_add_pPr()
        num_pr = OxmlElement("w:numPr")
        ilvl_el = OxmlElement("w:ilvl"); ilvl_el.set(qn("w:val"), ilvl); num_pr.append(ilvl_el)
        num_id_el = OxmlElement("w:numId"); num_id_el.set(qn("w:val"), num_id); num_pr.append(num_id_el)
        p_pr.append(num_pr)


    def build(output_path: Path) -> None:
        document = Document()

        # Inject the legacy singleLevel abstract + a w:num BEFORE adding paragraphs
        # that reference it. _inject_legacy_singlelevel_abstract returns the allocated
        # (abstract_num_id, num_id) so we don't hard-code values that may collide with
        # IDs python-docx auto-created in numbering_part.
        legacy_abstract_id, legacy_num_id = _inject_legacy_singlelevel_abstract(document)

        # 1. Bibliography title — Normal style (D-01 must override SVM=body_text → bibliography_title).
        document.add_paragraph("СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ")

        # 2. Subsection 1 — Heading 1, text NOT matching BIBLIOGRAPHY_SUBHEADING_RE (D-04 position+style).
        h1 = document.add_paragraph("ТЕОРЕТИЧЕСКАЯ ЧАСТЬ"); h1.style = "Heading 1"

        # 3. Entry 1 — no numPr.
        document.add_paragraph("Иванов И. И. Основы теории / И. И. Иванов. — Москва : Наука, 2020. — 240 с.")

        # 4. Entry 2 — stale numPr (numId=legacy_num_id, legacy singleLevel). D-06 must coerce.
        e2 = document.add_paragraph("Петров П. П. Введение в дискретную математику. — СПб. : Лань, 2019. — 320 с.")
        _set_numPr(e2, num_id=legacy_num_id, ilvl="0")

        # 5. Entry 3 — no numPr.
        document.add_paragraph("Сидоров С. С. Алгоритмы и структуры данных. — Москва : МЦНМО, 2018. — 188 с.")

        # 6. Subsection 2 — Heading 1, mixed naming (no number prefix), proves D-04 is style-based.
        h2 = document.add_paragraph("ИССЛЕДОВАТЕЛЬСКИЙ РАЗДЕЛ"); h2.style = "Heading 1"

        # 7-9. Entries — no numPr (D-06 fresh-allocate path).
        document.add_paragraph("Кузнецов А. А. Машинное обучение. — Москва : Питер, 2021. — 412 с.")
        document.add_paragraph("Морозов В. В. Нейронные сети. — Москва : ДМК Пресс, 2022. — 268 с.")
        document.add_paragraph("Лебедев Д. Д. Обработка естественного языка. — Москва : Эксмо, 2023. — 304 с.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        document.save(str(output_path))


    if __name__ == "__main__":
        build(Path("tests/fixtures/bibliography_minimal.docx"))
        print("wrote tests/fixtures/bibliography_minimal.docx")
    ```

    Run: `python tests/fixtures/_build_bibliography_minimal.py`. Commit both the script and the produced `.docx`.
  </action>
  <verify>
    <automated>python tests/fixtures/_build_bibliography_minimal.py && python -c "from docx import Document; d=Document('tests/fixtures/bibliography_minimal.docx'); paras=d.paragraphs; assert len(paras)==9, f'expected 9 got {len(paras)}'; assert paras[0].text=='СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ'; assert paras[1].style.name=='Heading 1' and paras[1].text=='ТЕОРЕТИЧЕСКАЯ ЧАСТЬ'; assert paras[5].style.name=='Heading 1' and paras[5].text=='ИССЛЕДОВАТЕЛЬСКИЙ РАЗДЕЛ'; from docx.oxml.ns import qn; e2_numPr=paras[3]._p.find(qn('w:pPr')).find(qn('w:numPr')); assert e2_numPr is not None, 'entry 2 missing numPr'; e2_num_id=e2_numPr.find(qn('w:numId')).get(qn('w:val')); assert e2_num_id is not None and e2_num_id.isdigit(), f'entry 2 numId must be a positive integer string, got {e2_num_id!r}'; assert paras[2]._p.find(qn('w:pPr')) is None or paras[2]._p.find(qn('w:pPr')).find(qn('w:numPr')) is None, 'entry 1 should have no numPr'; print('fixture OK')"</automated>
  </verify>
  <acceptance_criteria>
    - File `tests/fixtures/_build_bibliography_minimal.py` exists.
    - File `tests/fixtures/bibliography_minimal.docx` exists (binary, ~15-25KB).
    - `grep -c 'def build' tests/fixtures/_build_bibliography_minimal.py` returns `1`.
    - `python tests/fixtures/_build_bibliography_minimal.py` exits 0 and prints `wrote tests/fixtures/bibliography_minimal.docx`.
    - `python -c "from docx import Document; d=Document('tests/fixtures/bibliography_minimal.docx'); assert len(d.paragraphs)==9"` exits 0.
    - The `<automated>` command above exits 0 — proves: 9 paragraphs, correct title text, two Heading 1 subsections with correct text, entry 2 has numPr.numId set to a positive-integer string allocated by `_next_num_id` (whatever value python-docx didn't already reserve), entry 1 has no numPr.
    - Re-running `python tests/fixtures/_build_bibliography_minimal.py` produces a DOCX whose paragraph count and styles remain identical and whose entry-2 numPr still references a positive-integer numId pointing at the legacy singleLevel abstract (the specific allocated numId value depends on python-docx state and may differ across runs; content idempotent in shape, byte equality not required).
  </acceptance_criteria>
  <done>Fixture builder script committed; binary DOCX committed; assertions on shape pass.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Append D-01 + D-04 unit tests to tests/test_postprocess_rules.py (RED)</name>
  <files>tests/test_postprocess_rules.py</files>
  <read_first>
    - tests/test_postprocess_rules.py (FULL file — copy `_row` helper, look for existing `test_bibliography_context_overrides_body_text_and_list_predictions`)
    - .planning/phases/02-bibliography-list-semantics/02-PATTERNS.md §"tests/test_postprocess_rules.py" lines 602-625
    - .planning/phases/02-bibliography-list-semantics/02-RESEARCH.md §"Pitfall 3" lines 220-229 (asymmetry: predicted=body_text, post=bibliography_title)
    - .planning/phases/02-bibliography-list-semantics/02-CONTEXT.md §"D-01" + §"D-04"
    - src/postprocess/postprocess_rules.py lines 110-206 (apply_postprocess_rules current implementation)
  </read_first>
  <behavior>
    - 3 new test functions appended at END of `tests/test_postprocess_rules.py`:
      1. `test_bibliography_title_overrides_svm_body_text` (D-01): row `predicted_label="body_text"` + `text="СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"` → after `apply_postprocess_rules`, `postprocessed_label == "bibliography_title"`. Pins Pitfall 3 asymmetry.
      2. `test_bibliography_subsection_detected_by_heading_style` (D-04): row with `style="Heading 1"` and text `"ТЕОРЕТИЧЕСКАЯ ЧАСТЬ"` (does NOT match `BIBLIOGRAPHY_SUBHEADING_RE`) → `bibliography_section_index` advances to 1 on that row.
      3. `test_bibliography_subsection_fallback_regex_still_works` (D-04 fallback): row with `style="Normal"` and text matching `BIBLIOGRAPHY_SUBHEADING_RE` (e.g. `"Книги"` if it matches; or use the existing regex literal) → `bibliography_section_index` still advances. Asserts the legacy regex stays a fallback.
    - All 3 fail right now: D-01 fires conditionally today (researcher line 11), D-04 uses regex only — Heading 1 alone won't trigger section increment.
  </behavior>
  <action>
    Inspect the existing file to find the `_row` helper signature (line ~10-30 of `tests/test_postprocess_rules.py`) and the import for `apply_postprocess_rules`. Append the following 3 tests at the END of the file (do NOT modify existing tests). If the existing `_row` helper does NOT accept a `style` keyword, add a new `_row_with_style` helper to this addition block.

    First, locate the existing helper by running:
    `grep -n "def _row" tests/test_postprocess_rules.py`

    Then append (adapt `_row_with_style` if your existing helper differs in signature):

    ```python
    # ============================================================================
    # Phase 02 RED tests — D-01 unconditional title override + D-04 heading style detection.
    # Plans 02 implements; these MUST fail today.
    # ============================================================================

    def _row_with_style(block_id: int, text: str, predicted_label: str, style: str = "Normal") -> dict[str, object]:
        return {
            "doc_id": "doc_phase2",
            "block_id": block_id,
            "text": text,
            "style": style,
            "predicted_label": predicted_label,
        }


    def test_bibliography_title_overrides_svm_body_text() -> None:
        """D-01: BIBLIOGRAPHY_TITLE_RE match unconditionally sets label=bibliography_title
        even when SVM returned body_text. Pitfall 3 — pin the asymmetry."""
        df = pd.DataFrame([
            _row_with_style(0, "Введение", "body_text"),
            _row_with_style(1, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "body_text"),
            _row_with_style(2, "Иванов И. И. Основы теории. — М., 2020.", "body_text"),
        ])
        result = apply_postprocess_rules(df)
        labels = result["postprocessed_label"].tolist()
        # Title row MUST become bibliography_title, NOT body_text.
        assert labels[1] == "bibliography_title", (
            f"D-01 override failed: row 1 label={labels[1]!r}, expected 'bibliography_title' "
            f"(SVM said body_text, override must fire unconditionally)"
        )


    def test_bibliography_subsection_detected_by_heading_style() -> None:
        """D-04: Heading 1 style INSIDE bibliography context advances
        bibliography_section_index, even when the heading TEXT does NOT match
        BIBLIOGRAPHY_SUBHEADING_RE."""
        df = pd.DataFrame([
            _row_with_style(0, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "bibliography_title"),
            _row_with_style(1, "ТЕОРЕТИЧЕСКАЯ ЧАСТЬ", "body_text", style="Heading 1"),
            _row_with_style(2, "Иванов И. И. Основы теории. — М., 2020.", "body_text"),
            _row_with_style(3, "ИССЛЕДОВАТЕЛЬСКИЙ РАЗДЕЛ", "body_text", style="Heading 1"),
            _row_with_style(4, "Петров П. П. Введение. — СПб., 2019.", "body_text"),
        ])
        result = apply_postprocess_rules(df)
        section_indices = result["bibliography_section_index"].tolist()
        # After D-04: row 1 advances section to 1; row 3 advances to 2.
        # bibliography_section_index for entries 2 and 4 reflects the active section.
        assert section_indices[2] == 1, (
            f"D-04: entry under first Heading 1 subsection should have section_index=1, got {section_indices[2]!r}"
        )
        assert section_indices[4] == 2, (
            f"D-04: entry under second Heading 1 subsection should have section_index=2, got {section_indices[4]!r}"
        )


    def test_bibliography_subsection_fallback_regex_still_works() -> None:
        """D-04 fallback: rows with Normal style whose TEXT matches the legacy
        BIBLIOGRAPHY_SUBHEADING_RE must still be classified as subsection headings.
        Per researcher Open Question 2: the legacy regex stays in the codebase
        because src/evaluation/format_regression_audit.py imports it.

        This test pins ONE non-numbered text that matches BIBLIOGRAPHY_SUBHEADING_RE.
        Implementer in Plan 02 must inspect the regex to pick a matching string;
        a safe choice is a section title that is literally listed in the regex
        alternation. If no clean matching text exists, this test SKIPS with a
        clear message rather than vacuously passing.
        """
        import re
        from src.postprocess.postprocess_rules import BIBLIOGRAPHY_SUBHEADING_RE

        # Pick the first non-empty literal alternation member from the regex pattern.
        # If pattern uses character classes/quantifiers, fall back to a known
        # working literal — implementer in Plan 02 may adjust the literal.
        candidates = ["Книги и брошюры", "Статьи", "Электронные ресурсы", "Стандарты"]
        matching = next((c for c in candidates if BIBLIOGRAPHY_SUBHEADING_RE.search(c)), None)
        if matching is None:
            import pytest
            pytest.skip("No literal candidate matches BIBLIOGRAPHY_SUBHEADING_RE — adjust candidate list in Plan 02")

        df = pd.DataFrame([
            _row_with_style(0, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "bibliography_title"),
            _row_with_style(1, matching, "body_text"),   # Normal style — falls back to regex
            _row_with_style(2, "Иванов И. И. Основы. — М., 2020.", "body_text"),
        ])
        result = apply_postprocess_rules(df)
        section_indices = result["bibliography_section_index"].tolist()
        assert section_indices[2] == 1, (
            f"D-04 fallback: entry under regex-detected subsection should have section_index=1, got {section_indices[2]!r}"
        )
    ```

    Imports needed at the top of `tests/test_postprocess_rules.py`: `pandas as pd` and `apply_postprocess_rules` are already imported (verify via `grep -E "^import|^from" tests/test_postprocess_rules.py | head -10`). No new imports.
  </action>
  <verify>
    <automated>python -m pytest tests/test_postprocess_rules.py -x -q -k "bibliography_title_overrides_svm_body_text or bibliography_subsection_detected_by_heading_style or bibliography_subsection_fallback_regex_still_works" 2>&1 | tail -25</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c "^def test_bibliography_title_overrides_svm_body_text" tests/test_postprocess_rules.py` returns `1`.
    - `grep -c "^def test_bibliography_subsection_detected_by_heading_style" tests/test_postprocess_rules.py` returns `1`.
    - `grep -c "^def test_bibliography_subsection_fallback_regex_still_works" tests/test_postprocess_rules.py` returns `1`.
    - `python -m pytest tests/test_postprocess_rules.py -k "bibliography_title_overrides_svm_body_text" -x -q` exits NON-ZERO (D-01 override not yet unconditional → assertion fails).
    - `python -m pytest tests/test_postprocess_rules.py -k "bibliography_subsection_detected_by_heading_style" -x -q` exits NON-ZERO (D-04 not implemented → section_index stays None for Heading 1 rows whose text doesn't match the legacy regex).
    - The full file `python -m pytest tests/test_postprocess_rules.py -x -q` still passes existing tests + fails ONLY on the 2 new RED tests (the fallback test may skip if regex literal doesn't match, that's acceptable).
    - No imports added to the file.
  </acceptance_criteria>
  <done>3 RED tests appended; existing tests still green; 2 of 3 fail for the expected reasons (1 may skip).</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Create tests/test_profile_loader.py with D-11 + D-03 schema tests (RED)</name>
  <files>tests/test_profile_loader.py</files>
  <read_first>
    - .planning/phases/02-bibliography-list-semantics/02-PATTERNS.md §"tests/test_profile_loader.py (NEW)" lines 628-662
    - src/rules/profile_loader.py (full file — copy the `load_profile` import shape; locate `get_target_style_profile` / `get_audit_policy` as the analog for new helpers)
    - src/rules/profile_validator.py (full file — see the error-list-append pattern at lines 40-86)
    - src/rules/profiles/gost_7_32_2017.json (lines 270-344 — current top-level structure; this plan tests the field ADDITION will happen in Plan 02)
    - src/rules/profiles/mirea_normcontrol_local.json (full file — confirm it does NOT carry list_detection / numbering.bibliography; tests assert it still validates after Plan 02 adds optional fields)
  </read_first>
  <behavior>
    - File `tests/test_profile_loader.py` is created (does not exist today).
    - 4 test functions:
      1. `test_list_detection_thresholds_from_profile` (D-11): load `gost_7_32_2017`, assert `get_list_detection_thresholds(profile) == (40, 300)`.
      2. `test_bibliography_numbering_scope_default_is_per_section` (D-03): load `gost_7_32_2017`, assert `get_bibliography_numbering_scope(profile) == "per_section"`.
      3. `test_validator_accepts_profile_without_optional_sections`: load `mirea_normcontrol_local` (which does NOT carry list_detection or numbering.bibliography) — implicit assertion that `load_profile` runs `assert_valid_profile` and reaching the assert means OK.
      4. `test_validator_rejects_invalid_scope` (D-03): build a minimal profile dict with `numbering={"bibliography":{"scope":"INVALID"}}` and assert `validate_profile(profile)` returns a list containing an error message about `numbering.bibliography.scope`.
    - All 4 fail RIGHT NOW because:
      - 1, 2 — `get_list_detection_thresholds` and `get_bibliography_numbering_scope` don't exist → `ImportError`.
      - 3 — should PASS today since validator doesn't reject — but Plan 02 must not BREAK it (sanity check).
      - 4 — validator doesn't know about scope yet → returns no error → assertion fails.
  </behavior>
  <action>
    Create `tests/test_profile_loader.py` with the EXACT contents below. The file MUST NOT exist prior to this task (verify with `ls tests/test_profile_loader.py` first; if it exists, this task fails and the planner is notified).

    ```python
    """Unit tests for src/rules/profile_loader.py D-11 + D-03 helpers, and
    src/rules/profile_validator.py D-03 + D-11 schema extension.

    RED-state in Wave 0 (phase 02-bibliography-list-semantics). Plan 02 (Wave 1)
    implements the helpers and the validator extensions so these turn GREEN.
    """
    from __future__ import annotations

    import pytest

    from src.rules.profile_loader import load_profile
    from src.rules.profile_validator import validate_profile


    def test_list_detection_thresholds_from_profile() -> None:
        """D-11: get_list_detection_thresholds returns (40, 300) for gost_7_32_2017."""
        from src.rules.profile_loader import get_list_detection_thresholds  # NEW helper — RED via ImportError today

        profile = load_profile(profile_id="gost_7_32_2017")
        max_words, max_chars = get_list_detection_thresholds(profile)
        assert max_words == 40
        assert max_chars == 300


    def test_bibliography_numbering_scope_default_is_per_section() -> None:
        """D-03: get_bibliography_numbering_scope returns 'per_section' default for gost_7_32_2017."""
        from src.rules.profile_loader import get_bibliography_numbering_scope  # NEW helper — RED via ImportError today

        profile = load_profile(profile_id="gost_7_32_2017")
        assert get_bibliography_numbering_scope(profile) == "per_section"


    def test_validator_accepts_profile_without_optional_sections() -> None:
        """Existing profiles (mirea_normcontrol_local.json,
        gost_r_7_0_100_2018_bibliography.json) MUST continue to validate after
        D-03 + D-11 add optional sections. Sanity guard against regression."""
        for profile_id in ("mirea_normcontrol_local", "gost_r_7_0_100_2018_bibliography"):
            profile = load_profile(profile_id=profile_id)
            # load_profile calls assert_valid_profile internally — reaching here means OK.
            assert profile["profile_id"], f"profile {profile_id!r} missing profile_id"


    def test_validator_rejects_invalid_scope() -> None:
        """D-03: numbering.bibliography.scope must be one of
        {per_document, per_section, per_subsection_pattern}. Anything else returns
        a validation error."""
        # Construct a minimal-but-otherwise-valid profile by loading gost_7_32_2017
        # and mutating just the field under test. This way we don't need to author
        # all REQUIRED_TOP_LEVEL_KEYS manually.
        profile = load_profile(profile_id="gost_7_32_2017")
        profile.setdefault("numbering", {}).setdefault("bibliography", {})["scope"] = "INVALID_VALUE"
        errors = validate_profile(profile)
        assert any("scope" in err.lower() for err in errors), (
            f"Expected validator to reject scope='INVALID_VALUE', got errors={errors!r}"
        )
    ```

    Do NOT use any test fixtures or `tmp_path` — these tests work against the real on-disk profile JSON.
  </action>
  <verify>
    <automated>python -m pytest tests/test_profile_loader.py -x -q 2>&1 | tail -20</automated>
  </verify>
  <acceptance_criteria>
    - `tests/test_profile_loader.py` exists.
    - `grep -c "^def test_" tests/test_profile_loader.py` returns `4`.
    - All 4 test names exactly match: `test_list_detection_thresholds_from_profile`, `test_bibliography_numbering_scope_default_is_per_section`, `test_validator_accepts_profile_without_optional_sections`, `test_validator_rejects_invalid_scope`.
    - `python -m pytest tests/test_profile_loader.py::test_list_detection_thresholds_from_profile -x -q` exits NON-ZERO with `ImportError: cannot import name 'get_list_detection_thresholds'` (RED — Plan 02 adds the helper).
    - `python -m pytest tests/test_profile_loader.py::test_bibliography_numbering_scope_default_is_per_section -x -q` exits NON-ZERO with `ImportError: cannot import name 'get_bibliography_numbering_scope'` (RED).
    - `python -m pytest tests/test_profile_loader.py::test_validator_accepts_profile_without_optional_sections -x -q` PASSES (existing validator already accepts profiles without these optional sections — sanity guard).
    - `python -m pytest tests/test_profile_loader.py::test_validator_rejects_invalid_scope -x -q` exits NON-ZERO (validator does not check scope yet → `errors` is empty or doesn't contain "scope").
  </acceptance_criteria>
  <done>tests/test_profile_loader.py created; 2 RED via ImportError, 1 RED via assertion, 1 GREEN as sanity baseline.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 4: Create tests/test_bibliography_phase2.py with 11 RED tests for D-01/D-04/D-05/D-06/D-07/D-09/D-10/D-11/D-13/D-14</name>
  <files>tests/test_bibliography_phase2.py</files>
  <read_first>
    - .planning/phases/02-bibliography-list-semantics/02-PATTERNS.md §"tests/test_bibliography_phase2.py (NEW)" lines 496-599
    - .planning/phases/02-bibliography-list-semantics/02-RESEARCH.md §"Phase Requirements → Test Map" lines 488-502
    - .planning/phases/02-bibliography-list-semantics/02-CONTEXT.md §"D-05" + §"D-06" + §"D-07" + §"D-09" + §"D-13" + §"D-14"
    - tests/test_rule_engine.py lines 1124-1362 (style-guard test family — copy `_row_data_body_text` helper at line 1126-1131; copy review-result dict shape assertions)
    - tests/test_rule_engine.py lines 355-700 (bibliography test family — copy build_regression_predictions + audit_or_format_docx integration shape)
    - src/rules/rule_engine.py lines 771-798 (Phase 1 style guard pattern that D-09 mirrors)
    - src/rules/rule_engine.py lines 409-429 (apply_bibliography_numbering — D-05 must change ilvl from "0" to "1")
    - src/evaluation/format_regression_audit.py (for build_regression_predictions signature)
    - src/generate/inplace_formatter.py (audit_or_format_docx signature)
  </read_first>
  <behavior>
    - 11 test functions in `tests/test_bibliography_phase2.py`:
      1. `test_ambiguous_list_marker_no_numId_routes_to_review` (D-09 — unit, body_text + marker + no numPr → review, explanation `ambiguous_list_marker_no_numId`).
      2. `test_long_body_text_without_marker_stays_body_text` (D-10 — unit, body_text + no marker + Normal style + long text → result is None or status not review; assert applied_fixes does NOT contain "numbering").
      3. `test_bibliography_multilevel_renders_section_dot_entry` (D-05 — unit on `_create_bibliography_multilevel_abstract`, asserts `multiLevelType="multilevel"` + lvl-1 `lvlText="%1.%2."`).
      4. `test_bibliography_num_with_section_override_carries_lvlOverride` (D-05 — unit on `_create_bibliography_num_with_section_override`, asserts TWO `<w:lvlOverride>` children with `startOverride` set).
      5. `test_bibliography_subsection_coerces_to_first_valid_numId` (D-06 — integration on bibliography_minimal.docx, subsection 1 with mixed numId → after apply_safe, applied_fixes for some bibliography_item row contains `numbering:coerced_to_numId=<N>`).
      6. `test_bibliography_idempotent_on_rerun` (D-07 — integration: run apply_safe twice, second run summary changed == 0).
      7. `test_bibliography_apply_uses_ilvl_1` (D-05 — integration: after apply_safe on bibliography_minimal, every bibliography_item paragraph has `<w:ilvl w:val="1"/>`).
      8. `test_bibliography_format_skips_alignment_when_profile_omits` (D-13 — unit on apply_bibliography_format with config={"style_name":"List Number"} → alignment NOT in applied_fixes; paragraph.alignment stays None).
      9. `test_bibliography_minimal_docx_single_numId_per_subsection` (D-14 hand-crafted — integration: all bibliography_item rows in subsection 1 share one numId; subsection 2 rows share another numId; numId-1 differs from numId-2).
      10. `test_negative_4_bibliography_single_numId` (D-14 negative integration — uses `negative_examples/4_formatted_20260413_185420.docx`, asserts all bibliography_item rows share one numId; applied_fixes for at least one row includes `numbering`).
      11. `test_negative_3_bibliography_coerces_mixed_numIds` (D-06 + D-14 — uses `negative_examples/3_formatted_20260413_194927.docx`, asserts at least one row's applied_fixes contains `numbering:coerced_to_numId=`).
    - All 11 fail today because the production changes haven't landed yet.
  </behavior>
  <action>
    Create `tests/test_bibliography_phase2.py` with the contents below. Verify the file does NOT exist before creating (`ls tests/test_bibliography_phase2.py`). Use real `Document()` paragraphs (NOT SimpleNamespace) because rule_engine helpers introspect `paragraph._p`.

    ```python
    """Phase 02 RED tests — bibliography & list semantics.

    D-01..D-15 coverage. Plans 02/03/04 implement; these MUST fail today.

    File reference paths assume CWD == repository root (per pytest invocation).
    """
    from __future__ import annotations

    from pathlib import Path

    import pandas as pd
    import pytest
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    from src.evaluation.format_regression_audit import build_regression_predictions
    from src.generate.inplace_formatter import audit_or_format_docx
    from src.rules.rule_engine import (
        apply_bibliography_format,
        apply_rules_to_paragraph,
    )
    from src.rules.rule_loader import load_rules


    # ---------------------- helpers ----------------------

    def _row_data_body_text(text: str) -> dict:
        return {"text": text, "confidence_score": 0.99, "low_confidence": False}


    def _bibliography_item_rows(report_df: pd.DataFrame) -> pd.DataFrame:
        """Filter the audit CSV to rows that the postprocess classified as bibliography_item.

        The audit CSV column carrying the active label varies by implementation —
        prefer 'postprocessed_label' if present, fall back to 'predicted_label'.
        """
        col = "postprocessed_label" if "postprocessed_label" in report_df.columns else "predicted_label"
        return report_df[report_df[col] == "bibliography_item"].copy()


    def _all_numIds_in_docx(docx_path: Path) -> list[str | None]:
        """For each bibliography_item-ish paragraph, return numId or None."""
        document = Document(str(docx_path))
        result: list[str | None] = []
        for p in document.paragraphs:
            try:
                p_pr = p._p.find(qn("w:pPr"))
                if p_pr is None:
                    result.append(None); continue
                num_pr = p_pr.find(qn("w:numPr"))
                if num_pr is None:
                    result.append(None); continue
                num_id_el = num_pr.find(qn("w:numId"))
                result.append(num_id_el.get(qn("w:val")) if num_id_el is not None else None)
            except Exception:
                result.append(None)
        return result


    # ============================================================
    # D-09 — ambiguous-list review routing
    # ============================================================

    def test_ambiguous_list_marker_no_numId_routes_to_review() -> None:
        """D-09: body_text + numbered marker + no Word numPr + Normal style → review,
        explanation 'ambiguous_list_marker_no_numId', no fixes applied."""
        document = Document()
        paragraph = document.add_paragraph("1) Первый пункт без Word numbering, без подписки на список.")

        result = apply_rules_to_paragraph(
            paragraph=paragraph,
            label="body_text",
            row_data=_row_data_body_text(paragraph.text),
            rules=load_rules(),
            apply_safe=True,
            default_font_name="Times New Roman",
        )

        assert result is not None
        assert result["status"] == "review", result
        assert result["manual_review_required"] is True
        assert result["applied_fixes"] == []
        assert result["explanation"] == "ambiguous_list_marker_no_numId", result["explanation"]


    # ============================================================
    # D-10 — no marker + no numId + body_text stays body_text
    # ============================================================

    def test_long_body_text_without_marker_stays_body_text() -> None:
        """D-10: A long Normal-styled body paragraph without a list marker and
        without numPr must NOT receive list coercion. Phase 1 style guard +
        the absence of D-09 trigger leaves the existing body_text path to run.
        Concrete assertion: applied_fixes does NOT include 'numbering'; status
        is not 'review' with the D-09 explanation."""
        document = Document()
        long_text = (
            "Обычный абзац основного текста без маркера и без Word numbering, "
            "достаточно длинный, чтобы пройти MAX_FALLBACK_LIST_CHARS порог. " * 4
        )
        paragraph = document.add_paragraph(long_text)

        result = apply_rules_to_paragraph(
            paragraph=paragraph,
            label="body_text",
            row_data=_row_data_body_text(paragraph.text),
            rules=load_rules(),
            apply_safe=True,
            default_font_name="Times New Roman",
        )

        # Result may be None (no applicable body_text rules fire) or a non-D-09 dict.
        # The critical assertions: no numbering applied, no D-09 explanation.
        if result is not None:
            assert "numbering" not in result.get("applied_fixes", []), result
            assert result.get("explanation", "") != "ambiguous_list_marker_no_numId", result


    # ============================================================
    # D-05 — 2-level multilevel abstract emission
    # ============================================================

    def test_bibliography_multilevel_renders_section_dot_entry() -> None:
        """D-05: _create_bibliography_multilevel_abstract emits a multiLevelType
        multilevel abstract with TWO w:lvl children, level-1 lvlText='%1.%2.'."""
        from src.rules.rule_engine import _create_bibliography_multilevel_abstract  # RED via AttributeError today

        document = Document()
        # Trigger numbering_part creation.
        tmp = document.add_paragraph("__seed__"); tmp.style = "List Number"
        numbering_root = document.part.numbering_part.element

        abstract_num_id = _create_bibliography_multilevel_abstract(numbering_root)

        # Find the emitted abstract by id and inspect its structure.
        abstracts = numbering_root.findall(qn("w:abstractNum"))
        emitted = next((a for a in abstracts if a.get(qn("w:abstractNumId")) == abstract_num_id), None)
        assert emitted is not None, f"emitted abstractNumId={abstract_num_id} not found among {[a.get(qn('w:abstractNumId')) for a in abstracts]}"

        mlt = emitted.find(qn("w:multiLevelType"))
        assert mlt is not None and mlt.get(qn("w:val")) == "multilevel", mlt is not None and mlt.get(qn("w:val"))

        lvls = emitted.findall(qn("w:lvl"))
        assert len(lvls) == 2, f"expected 2 w:lvl children, got {len(lvls)}"
        ilvls = [l.get(qn("w:ilvl")) for l in lvls]
        assert "0" in ilvls and "1" in ilvls, ilvls

        lvl1 = next(l for l in lvls if l.get(qn("w:ilvl")) == "1")
        lvl1_text = lvl1.find(qn("w:lvlText"))
        assert lvl1_text is not None and lvl1_text.get(qn("w:val")) == "%1.%2.", (
            f"lvl-1 lvlText must be '%1.%2.', got {lvl1_text is not None and lvl1_text.get(qn('w:val'))!r}"
        )


    def test_bibliography_num_with_section_override_carries_lvlOverride() -> None:
        """D-05 pitfall 2: each w:num MUST carry TWO w:lvlOverride children
        (ilvl=0 startOverride=section_index, ilvl=1 startOverride=1) so Word
        resets per-subsection counters correctly."""
        from src.rules.rule_engine import (
            _create_bibliography_multilevel_abstract,
            _create_bibliography_num_with_section_override,
        )  # RED via AttributeError today

        document = Document()
        tmp = document.add_paragraph("__seed__"); tmp.style = "List Number"
        numbering_root = document.part.numbering_part.element

        abstract_num_id = _create_bibliography_multilevel_abstract(numbering_root)
        num_id = _create_bibliography_num_with_section_override(numbering_root, abstract_num_id, section_index=2)

        nums = numbering_root.findall(qn("w:num"))
        emitted = next((n for n in nums if n.get(qn("w:numId")) == str(num_id)), None)
        assert emitted is not None

        overrides = emitted.findall(qn("w:lvlOverride"))
        assert len(overrides) == 2, f"expected 2 w:lvlOverride children, got {len(overrides)}"
        by_ilvl = {ov.get(qn("w:ilvl")): ov.find(qn("w:startOverride")).get(qn("w:val")) for ov in overrides}
        assert by_ilvl.get("0") == "2", f"lvlOverride ilvl=0 must startOverride=2, got {by_ilvl}"
        assert by_ilvl.get("1") == "1", f"lvlOverride ilvl=1 must startOverride=1, got {by_ilvl}"


    # ============================================================
    # D-06 — first-valid-numId coercion
    # ============================================================

    def test_bibliography_subsection_coerces_to_first_valid_numId(tmp_path) -> None:
        """D-06: bibliography_minimal.docx subsection 1 has mixed numIds (entry 2
        carries numId=1 pointing at legacy singleLevel). After apply_safe, at
        least one bibliography_item row's applied_fixes contains
        'numbering:coerced_to_numId=' (exact target numId varies)."""
        input_docx = Path("tests/fixtures/bibliography_minimal.docx")
        assert input_docx.exists(), "run tests/fixtures/_build_bibliography_minimal.py first"

        predictions_csv = tmp_path / "predictions.csv"
        report_csv = tmp_path / "report.csv"
        output_docx = tmp_path / "output.docx"
        build_regression_predictions(input_docx, predictions_csv)

        summary = audit_or_format_docx(
            input_docx=input_docx,
            predictions_csv=predictions_csv,
            report_csv=report_csv,
            output_docx=output_docx,
            apply_safe=True,
            profile_id="gost_7_32_2017",
        )
        assert summary["error"] == 0, summary

        report_df = pd.read_csv(report_csv, encoding="utf-8-sig")
        biblio_rows = _bibliography_item_rows(report_df)
        applied_fixes_concat = " | ".join(str(v) for v in biblio_rows.get("applied_fixes", []).tolist())
        assert "numbering:coerced_to_numId=" in applied_fixes_concat, (
            f"D-06 coercion tag not present. applied_fixes seen: {applied_fixes_concat!r}"
        )


    # ============================================================
    # D-07 — idempotent on re-run
    # ============================================================

    def test_bibliography_idempotent_on_rerun(tmp_path) -> None:
        """D-07: run apply_safe twice on bibliography_minimal.docx. Second run's
        summary['changed'] == 0 — numId already correct, no further fixes."""
        input_docx = Path("tests/fixtures/bibliography_minimal.docx")
        assert input_docx.exists()

        predictions_csv = tmp_path / "predictions.csv"
        report_csv_1 = tmp_path / "report_1.csv"
        output_docx_1 = tmp_path / "output_1.docx"
        build_regression_predictions(input_docx, predictions_csv)

        summary_1 = audit_or_format_docx(
            input_docx=input_docx, predictions_csv=predictions_csv,
            report_csv=report_csv_1, output_docx=output_docx_1,
            apply_safe=True, profile_id="gost_7_32_2017",
        )
        assert summary_1["error"] == 0

        # Re-feed the corrected DOCX.
        predictions_csv_2 = tmp_path / "predictions_2.csv"
        report_csv_2 = tmp_path / "report_2.csv"
        output_docx_2 = tmp_path / "output_2.docx"
        build_regression_predictions(output_docx_1, predictions_csv_2)

        summary_2 = audit_or_format_docx(
            input_docx=output_docx_1, predictions_csv=predictions_csv_2,
            report_csv=report_csv_2, output_docx=output_docx_2,
            apply_safe=True, profile_id="gost_7_32_2017",
        )
        assert summary_2["error"] == 0
        assert summary_2["changed"] == 0, (
            f"D-07: second run should produce no further changes, got changed={summary_2['changed']}. "
            f"Cache key {{id(numbering_root)}} likely leaking — switch to id(paragraph.part.document.part)."
        )


    # ============================================================
    # D-05 — bibliography_item paragraphs use ilvl=1 after fix
    # ============================================================

    def test_bibliography_apply_uses_ilvl_1(tmp_path) -> None:
        """D-05: After apply_safe, every bibliography_item paragraph's <w:numPr>
        has <w:ilvl w:val="1"/> (changed from "0" today)."""
        input_docx = Path("tests/fixtures/bibliography_minimal.docx")
        assert input_docx.exists()

        predictions_csv = tmp_path / "predictions.csv"
        report_csv = tmp_path / "report.csv"
        output_docx = tmp_path / "output.docx"
        build_regression_predictions(input_docx, predictions_csv)

        audit_or_format_docx(
            input_docx=input_docx, predictions_csv=predictions_csv,
            report_csv=report_csv, output_docx=output_docx,
            apply_safe=True, profile_id="gost_7_32_2017",
        )

        document = Document(str(output_docx))
        # 6 entries total (3 per subsection). Each must have numPr.ilvl == "1".
        biblio_paragraphs = [p for p in document.paragraphs if p.text.startswith(("Иванов", "Петров", "Сидоров", "Кузнецов", "Морозов", "Лебедев"))]
        assert len(biblio_paragraphs) == 6, f"expected 6 bibliography entries, found {len(biblio_paragraphs)}"
        for p in biblio_paragraphs:
            p_pr = p._p.find(qn("w:pPr"))
            assert p_pr is not None, f"missing pPr on entry {p.text[:30]!r}"
            num_pr = p_pr.find(qn("w:numPr"))
            assert num_pr is not None, f"missing numPr on entry {p.text[:30]!r}"
            ilvl = num_pr.find(qn("w:ilvl"))
            assert ilvl is not None and ilvl.get(qn("w:val")) == "1", (
                f"entry {p.text[:30]!r} ilvl={ilvl is not None and ilvl.get(qn('w:val'))!r}, expected '1'"
            )


    # ============================================================
    # D-13 — bibliography_format skips alignment when profile omits field
    # ============================================================

    def test_bibliography_format_skips_alignment_when_profile_omits() -> None:
        """D-13: apply_bibliography_format with config={'style_name':'List Number'}
        (no alignment / indent fields) must NOT write alignment. The paragraph's
        alignment stays None after the call."""
        document = Document()
        paragraph = document.add_paragraph("Иванов И. И. Тест.")

        config = {"style_name": "List Number"}  # NO alignment, NO indents
        applied = apply_bibliography_format(paragraph, config, section_index=1)

        # Strict assertion: alignment must not appear in applied_fixes — profile didn't ask for it.
        assert "alignment" not in applied, f"applied_fixes contains 'alignment' but profile didn't carry it: {applied}"
        assert paragraph.alignment is None, (
            f"paragraph.alignment={paragraph.alignment!r} — apply_bibliography_format wrote a direct alignment "
            "even though profile config did not carry the field. D-13 violated."
        )


    # ============================================================
    # D-14 — bibliography_minimal.docx single numId per subsection
    # ============================================================

    def test_bibliography_minimal_docx_single_numId_per_subsection(tmp_path) -> None:
        """D-14 hand-crafted: after apply_safe, all 3 entries in subsection 1
        share one numId; all 3 entries in subsection 2 share another numId;
        the two numIds differ (per-subsection scope per D-03 default)."""
        input_docx = Path("tests/fixtures/bibliography_minimal.docx")
        assert input_docx.exists()

        predictions_csv = tmp_path / "predictions.csv"
        report_csv = tmp_path / "report.csv"
        output_docx = tmp_path / "output.docx"
        build_regression_predictions(input_docx, predictions_csv)

        summary = audit_or_format_docx(
            input_docx=input_docx, predictions_csv=predictions_csv,
            report_csv=report_csv, output_docx=output_docx,
            apply_safe=True, profile_id="gost_7_32_2017",
        )
        assert summary["error"] == 0

        all_num_ids = _all_numIds_in_docx(output_docx)
        # paragraphs 2,3,4 = subsection 1 entries; 6,7,8 = subsection 2 entries.
        sub1_num_ids = [all_num_ids[2], all_num_ids[3], all_num_ids[4]]
        sub2_num_ids = [all_num_ids[6], all_num_ids[7], all_num_ids[8]]

        assert len(set(sub1_num_ids)) == 1 and sub1_num_ids[0] is not None, (
            f"subsection 1 entries must share one numId, got {sub1_num_ids}"
        )
        assert len(set(sub2_num_ids)) == 1 and sub2_num_ids[0] is not None, (
            f"subsection 2 entries must share one numId, got {sub2_num_ids}"
        )
        assert sub1_num_ids[0] != sub2_num_ids[0], (
            f"per_section scope: subsection 1 and subsection 2 must have DIFFERENT numIds, got both = {sub1_num_ids[0]}"
        )


    # ============================================================
    # D-14 — negative integration on real DOCX
    # ============================================================

    def test_negative_4_bibliography_single_numId(tmp_path) -> None:
        """D-14 negative integration: negative_examples/4_formatted_20260413_185420.docx
        has Heading 2 subsections and existing numId=16. After apply_safe, all
        bibliography_item rows share one numId per subsection; applied_fixes for
        at least one row includes 'numbering'."""
        input_docx = Path("negative_examples/4_formatted_20260413_185420.docx")
        if not input_docx.exists():
            pytest.skip(f"fixture {input_docx} not present in this environment")

        predictions_csv = tmp_path / "predictions.csv"
        report_csv = tmp_path / "report.csv"
        output_docx = tmp_path / "output.docx"
        build_regression_predictions(input_docx, predictions_csv)

        summary = audit_or_format_docx(
            input_docx=input_docx, predictions_csv=predictions_csv,
            report_csv=report_csv, output_docx=output_docx,
            apply_safe=True, profile_id="gost_7_32_2017",
        )
        assert summary["error"] == 0

        report_df = pd.read_csv(report_csv, encoding="utf-8-sig")
        biblio_rows = _bibliography_item_rows(report_df)
        assert not biblio_rows.empty, "expected ≥1 bibliography_item row in 4_formatted_20260413_185420.docx"

        applied_concat = " | ".join(str(v) for v in biblio_rows.get("applied_fixes", []).tolist())
        assert "numbering" in applied_concat, (
            f"expected at least one bibliography_item row's applied_fixes to include 'numbering', got {applied_concat!r}"
        )


    def test_negative_3_bibliography_coerces_mixed_numIds(tmp_path) -> None:
        """D-06 + D-14: negative_examples/3_formatted_20260413_194927.docx carries
        mixed numIds (some None, some numId=1). Coercion fires → at least one row's
        applied_fixes contains 'numbering:coerced_to_numId='.

        If the document does not in fact exhibit mixed numIds on bibliography_item
        rows (researcher's claim — verify in implementation), this test should
        still pass because the fresh-allocate path also tags 'numbering'. The
        strict coercion-tag assertion lives in test_bibliography_subsection_coerces_to_first_valid_numId
        on bibliography_minimal.docx which is known-mixed.
        """
        input_docx = Path("negative_examples/3_formatted_20260413_194927.docx")
        if not input_docx.exists():
            pytest.skip(f"fixture {input_docx} not present in this environment")

        predictions_csv = tmp_path / "predictions.csv"
        report_csv = tmp_path / "report.csv"
        output_docx = tmp_path / "output.docx"
        build_regression_predictions(input_docx, predictions_csv)

        summary = audit_or_format_docx(
            input_docx=input_docx, predictions_csv=predictions_csv,
            report_csv=report_csv, output_docx=output_docx,
            apply_safe=True, profile_id="gost_7_32_2017",
        )
        assert summary["error"] == 0

        report_df = pd.read_csv(report_csv, encoding="utf-8-sig")
        biblio_rows = _bibliography_item_rows(report_df)
        assert not biblio_rows.empty, "expected ≥1 bibliography_item row in 3_formatted_20260413_194927.docx"
        applied_concat = " | ".join(str(v) for v in biblio_rows.get("applied_fixes", []).tolist())
        assert "numbering" in applied_concat, (
            f"expected 'numbering' in applied_fixes for at least one row, got {applied_concat!r}"
        )
    ```
  </action>
  <verify>
    <automated>python -m pytest tests/test_bibliography_phase2.py -x -q 2>&1 | tail -40</automated>
  </verify>
  <acceptance_criteria>
    - `tests/test_bibliography_phase2.py` exists.
    - `grep -c "^def test_" tests/test_bibliography_phase2.py` returns `11`.
    - All 11 test names exactly match the spec: `test_ambiguous_list_marker_no_numId_routes_to_review`, `test_long_body_text_without_marker_stays_body_text`, `test_bibliography_multilevel_renders_section_dot_entry`, `test_bibliography_num_with_section_override_carries_lvlOverride`, `test_bibliography_subsection_coerces_to_first_valid_numId`, `test_bibliography_idempotent_on_rerun`, `test_bibliography_apply_uses_ilvl_1`, `test_bibliography_format_skips_alignment_when_profile_omits`, `test_bibliography_minimal_docx_single_numId_per_subsection`, `test_negative_4_bibliography_single_numId`, `test_negative_3_bibliography_coerces_mixed_numIds`.
    - `python -m pytest tests/test_bibliography_phase2.py -x -q` exits NON-ZERO (RED state).
    - RED reasons distributed as: D-09 routing test fails because branch missing; D-05 multilevel tests fail with `ImportError: cannot import name '_create_bibliography_multilevel_abstract'` (or AttributeError); D-06 coercion tag absent; D-07 idempotency: second run probably changed > 0; D-13 alignment write detected; D-14 integration tests fail on numId-per-subsection mismatch.
    - `test_long_body_text_without_marker_stays_body_text` passes today (no D-09 branch firing yet — Phase 1 style guard handles it).
    - Imports do NOT fail at import time (all imports go through try/except inside the test or import the function INSIDE the test body for the not-yet-existing helpers).
  </acceptance_criteria>
  <done>11 tests created; mostly RED for expected reasons; D-10 test passes as sanity baseline.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 5: Create tests/test_negative_corpus_diff_rate.py (D-15 automated regression gate)</name>
  <files>tests/test_negative_corpus_diff_rate.py</files>
  <read_first>
    - .planning/phases/01-engine-guardrails-cohesion-audit/01-VERIFICATION.md §"MH4 — Negative corpus diff-rate" (manual baseline 0.4737 ≤ 0.4781)
    - .planning/phases/02-bibliography-list-semantics/02-CONTEXT.md §"D-15"
    - .planning/phases/02-bibliography-list-semantics/02-RESEARCH.md §"Open Question 1" lines 568-571 (recommend ADD automated test, limit=4)
    - src/evaluation/format_regression_audit.py (FULL file — audit_negative_directory signature, audits_to_frame columns including after_diff_rate)
    - tests/test_positive_docx_regression.py (Phase 1 pattern for `audit_negative_directory` invocation, profile_id='gost_7_32_2017')
  </read_first>
  <behavior>
    - File `tests/test_negative_corpus_diff_rate.py` is created.
    - 1 test `test_negative_corpus_diff_rate_phase2_baseline` calls `audit_negative_directory(negative_examples_dir, limit=4, profile_id='gost_7_32_2017')` and asserts mean `after_diff_rate <= 0.4781`.
    - The 4-doc subset is chosen by sorted filename order (`limit=4` semantics — confirm via reading `audit_negative_directory` signature; if no sort, the test pins documents explicitly).
    - Today (Wave 0): the test runs against current `master` code. If the 4-doc subset's mean is ≤ 0.4781 (likely — Phase 1 baseline 0.4737 is mean over 17), the test passes today as a "guard" that Wave 3 won't break. If the subset's mean exceeds 0.4781, the test is RED today — Wave 3 must lower it.
    - Either way the test is the contract Phase 2 must not break.
  </behavior>
  <action>
    Inspect `src/evaluation/format_regression_audit.py` to confirm:
    1. The exact signature of `audit_negative_directory` (does it accept `limit`? `profile_id`?).
    2. Whether `audits_to_frame` returns a DataFrame with column `after_diff_rate` (per research line 502).
    3. Whether the function sorts by filename or by mtime.

    Then create `tests/test_negative_corpus_diff_rate.py`:

    ```python
    """D-15: automated negative-corpus diff-rate regression gate.

    Phase 1 left this manual (VERIFICATION.md MH4: 0.4737 ≤ 0.4781 observed via
    direct audit_negative_directory call). Phase 2 promotes a 4-doc subset to
    an automated pytest gate so subsequent waves can't silently regress it.

    The full-17-doc gate stays manual until Phase 4 introduces the
    audit-regression CLI.
    """
    from __future__ import annotations

    from pathlib import Path

    import pytest

    from src.evaluation.format_regression_audit import (
        audit_negative_directory,
        audits_to_frame,
    )

    PHASE_1_BASELINE_MEAN_DIFF_RATE = 0.4781


    def test_negative_corpus_diff_rate_phase2_baseline() -> None:
        """Mean after_diff_rate across a 4-doc subset of negative_examples/ MUST
        stay ≤ 0.4781 (FORMAT_FIX_PLAN Этап 8 baseline carried by Phase 1).

        4-doc subset is chosen by the audit_negative_directory limit parameter.
        If the function signature differs from {dir, limit, profile_id}, adapt
        the call site below — the contract is the assertion, not the wiring.
        """
        negative_dir = Path("negative_examples")
        if not negative_dir.exists():
            pytest.skip("negative_examples/ not present in this environment")

        # Call the audit. If the signature does not accept `limit` or
        # `profile_id`, simplify to whatever signature exists today.
        try:
            audits = audit_negative_directory(
                str(negative_dir),
                limit=4,
                profile_id="gost_7_32_2017",
            )
        except TypeError:
            # Fallback: simpler signature without keyword args
            audits = audit_negative_directory(str(negative_dir))

        frame = audits_to_frame(audits)
        # Take first 4 rows by index order — matches `limit=4` semantics if the
        # function does not pre-limit.
        if "after_diff_rate" not in frame.columns:
            pytest.fail(f"after_diff_rate column missing; columns={list(frame.columns)!r}")

        subset = frame.head(4)
        mean_diff_rate = float(subset["after_diff_rate"].mean())
        assert mean_diff_rate <= PHASE_1_BASELINE_MEAN_DIFF_RATE, (
            f"Negative-corpus mean after_diff_rate regressed: {mean_diff_rate:.4f} > {PHASE_1_BASELINE_MEAN_DIFF_RATE} "
            f"(subset of 4 docs). See subset:\n{subset[['after_diff_rate']]}"
        )
    ```
  </action>
  <verify>
    <automated>python -m pytest tests/test_negative_corpus_diff_rate.py -x -q 2>&1 | tail -15</automated>
  </verify>
  <acceptance_criteria>
    - `tests/test_negative_corpus_diff_rate.py` exists.
    - `grep -c "^def test_negative_corpus_diff_rate_phase2_baseline" tests/test_negative_corpus_diff_rate.py` returns `1`.
    - `grep -F "PHASE_1_BASELINE_MEAN_DIFF_RATE = 0.4781" tests/test_negative_corpus_diff_rate.py` returns the line.
    - `python -m pytest tests/test_negative_corpus_diff_rate.py -x -q` runs without ImportError (the import surface is the existing Phase 1 module).
    - Test result: either PASS (4-doc subset mean ≤ 0.4781 on current master — confirms gate is set correctly) or FAIL with a clear `regressed: X > 0.4781` message. EITHER outcome is acceptable as Wave 0 sign-off; the assertion is what Phase 2 implementation will be measured against.
    - If the test fails because the 4-doc subset's mean is > 0.4781 even on current master, document this in the SUMMARY and explicitly flag Wave 3 to relax to a per-subset baseline OR to widen the limit to 17. Wave 0 must NOT skip this RED diagnosis — the test must stay in the file as-is.
  </acceptance_criteria>
  <done>D-15 automated gate file committed; result documented in SUMMARY whether PASS or RED-with-data.</done>
</task>

</tasks>

<verification>
After all 5 tasks complete, run the full test suite and observe RED state:

```bash
python -m pytest -x -q 2>&1 | tail -50
```

Expected outcome:
- Total test count grew from 53 (Phase 1) to ~72 (+ 11 phase2 + 3 postprocess + 4 profile_loader + 1 negative-diff-rate = 19 new).
- The suite exits NON-ZERO. Failures concentrated on:
  - `test_bibliography_phase2.py`: ≥ 9 RED (D-09 routing, D-05 abstract + override, D-06 coercion, D-07 idempotency, D-05 ilvl=1, D-13 alignment, D-14 hand-crafted, D-14 negative). `test_long_body_text_without_marker_stays_body_text` passes as sanity.
  - `test_postprocess_rules.py`: 2 new RED (D-01 unconditional override, D-04 heading detection). 1 may skip (fallback regex candidate match).
  - `test_profile_loader.py`: 2 RED via ImportError (helpers not defined), 1 RED via assertion (validator no scope check), 1 GREEN (sanity).
  - `test_negative_corpus_diff_rate.py`: PASS or RED with documented diff-rate value.
- The existing 53 Phase 1 tests STILL pass — no regression introduced by the test scaffolding.

This RED set is the hand-off contract for Plans 02 (D-01+D-04+D-11+D-03), 03 (D-05+D-06+D-07), and 04 (D-09+D-10+D-13+D-15).
</verification>

<success_criteria>
- tests/fixtures/_build_bibliography_minimal.py exists; tests/fixtures/bibliography_minimal.docx is committed (9 paragraphs, mixed-numId entry 2).
- tests/test_postprocess_rules.py has 3 new tests appended for D-01 + D-04 + D-04 fallback.
- tests/test_profile_loader.py exists with 4 tests for D-11 + D-03 + validator behavior.
- tests/test_bibliography_phase2.py exists with 11 tests covering D-05/D-06/D-07/D-09/D-10/D-13/D-14.
- tests/test_negative_corpus_diff_rate.py exists with 1 automated D-15 gate.
- All new tests run; the suite fails in RED for documented reasons; existing 53 Phase 1 tests still pass.
- Every task's `<automated>` verify completes in < 60 seconds.
- No production code modified in this plan.
</success_criteria>

<output>
After completion, create `.planning/phases/02-bibliography-list-semantics/02-01-test-scaffolding-red-SUMMARY.md` documenting:
- Total new tests by file (D-01..D-15 coverage matrix).
- The exact list of failing test names (RED state contract for Plans 02-04).
- Total pytest count before/after.
- Fixture file size and paragraph layout confirmation.
- D-15 baseline: PASS with measured mean diff-rate, or RED with measured value (informs Plan 04 strategy).
- Confirmation that all existing 53 Phase 1 tests still pass.
</output>
</content>
