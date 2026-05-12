---
phase: 02-bibliography-list-semantics
plan: 03
type: execute
wave: 2
depends_on: [01, 02]
files_modified:
  - src/rules/rule_engine.py
  - tests/test_rule_engine.py
autonomous: true
requirements:
  - REQ-list-conservative-handling
requirements_addressed:
  - REQ-list-conservative-handling
tags:
  - bibliography
  - numbering
  - ooxml
  - phase-2

must_haves:
  truths:
    - "A new function `_create_bibliography_multilevel_abstract(numbering_root) -> str` emits ONE w:abstractNum per document with multiLevelType='multilevel' and TWO w:lvl children whose lvlText values are '%1.' (ilvl=0) and '%1.%2.' (ilvl=1)."
    - "A new function `_create_bibliography_num_with_section_override(numbering_root, abstract_num_id, section_index) -> int` emits ONE w:num per subsection with TWO w:lvlOverride children (ilvl=0 startOverride=section_index; ilvl=1 startOverride=1)."
    - "`_get_bibliography_num_id` is rewritten to (a) seed `_BIBLIOGRAPHY_NUM_IDS` from numbering.xml on first call per document via `_seed_bibliography_num_ids_from_doc`, (b) key the cache by `(id(paragraph.part.document.part), section_index)` not `(id(numbering_root), section_index)`, (c) coerce first-valid-numId-in-subsection wins (D-06), (d) allocate via the new 2-level abstract + per-subsection w:num pair on cache miss."
    - "`apply_bibliography_numbering` sets `<w:ilvl w:val=\"1\"/>` (changed from \"0\") and returns `['numbering']` on fresh-allocate / first-valid-match, OR `['numbering', 'numbering:coerced_to_numId=<N>']` when coercing away from a pre-existing different numId (D-06)."
    - "Module-level state additions: `_SEEDED_DOCS: set[int] = set()` (Plan 04 may clear at audit-boundary if needed; this plan only adds it)."
    - "Phase 1 baseline (53 tests) still GREEN; Wave 0 D-05/D-06/D-07 + D-14 hand-crafted tests turn GREEN."
    - "The legacy `_create_section_abstract_num_id` stays in place (researcher Don't Hand-Roll anti-pattern: do NOT edit in place). It is no longer called from the bibliography path; cleanup deferred to a follow-up commit if/when verified safe."
  artifacts:
    - path: "src/rules/rule_engine.py"
      provides: "2-level abstract emission + per-subsection w:num + idempotent seeded allocator + first-valid-numId coercion"
      contains: "def _create_bibliography_multilevel_abstract"
  key_links:
    - from: "src/rules/rule_engine._get_bibliography_num_id"
      to: "src/rules/rule_engine._seed_bibliography_num_ids_from_doc"
      via: "first-call seed before allocation"
      pattern: "_seed_bibliography_num_ids_from_doc"
    - from: "src/rules/rule_engine.apply_bibliography_numbering"
      to: "src/rules/rule_engine._create_bibliography_multilevel_abstract + _create_bibliography_num_with_section_override"
      via: "indirect through _get_bibliography_num_id"
      pattern: "_create_bibliography_multilevel_abstract\\|_create_bibliography_num_with_section_override"
    - from: "_BIBLIOGRAPHY_NUM_IDS cache key"
      to: "id(paragraph.part.document.part)"
      via: "_document_cache_key(paragraph)"
      pattern: "id\\(paragraph\\.part\\.document\\.part\\)"
---

<objective>
Wave 2 GREEN — D-05 (2-level multilevel abstract), D-06 (first-valid-numId-in-subsection coercion), D-07 (idempotency via numbering.xml seed + stable document key). All three land in `src/rules/rule_engine.py` because they share the same allocator + the same cache.

Why one plan, one file: D-05 (new abstract shape), D-06 (coercion logic), D-07 (cache key + seed) are tightly coupled — they all flow through `_get_bibliography_num_id`. Splitting them across plans would produce a broken intermediate state where the cache key changed but the allocator still emitted singleLevel abstracts, or vice versa. The user's CLAUDE.md rule "восстанавливай отсутствующий или сломанный `numPr` у списка, не меняя уже принятую раскладку абзаца" demands the numbering change be atomic.

Risk surface: HIGHEST in Phase 2. The 2-level abstract emission, lvlOverride placement, and cache-key migration are all OOXML-spec-driven and tested per Pitfall 1/2/3 in RESEARCH.md. The full XML template lives below verbatim — executor copies it without paraphrase.

Output: 1 source file modified; 4-6 Wave 0 RED tests turn GREEN; D-14 integration tests on bibliography_minimal.docx + negative DOCX move to GREEN.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@.planning/phases/02-bibliography-list-semantics/02-CONTEXT.md
@.planning/phases/02-bibliography-list-semantics/02-RESEARCH.md
@.planning/phases/02-bibliography-list-semantics/02-PATTERNS.md
@.planning/phases/02-bibliography-list-semantics/02-02-postprocess-and-profile-green-PLAN.md
@src/rules/rule_engine.py
@tests/test_bibliography_phase2.py

<interfaces>
<!-- Existing in rule_engine.py (preserve) -->
```python
# Imports (lines 1-14):
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from src.rules.style_signatures import classify_style, ...

# Module-level state to MODIFY:
_BIBLIOGRAPHY_NUM_IDS: dict[tuple[int, int | None], int] = {}  # KEY CHANGES IN THIS PLAN

# Module-level state to ADD:
_SEEDED_DOCS: set[int] = set()

# Existing oracle functions (DO NOT MODIFY — D-07 reads them):
def _num_id_exists(paragraph: Paragraph, num_id: str | int | None) -> bool: ...   # line 148
def paragraph_numbering_reference_is_valid(paragraph: Paragraph) -> bool: ...    # line 156

# Existing allocator-adjacent helpers (PRESERVE):
def _next_abstract_num_id(numbering_root) -> int: ...   # line 285
def _next_num_id(numbering_root) -> int: ...            # line 294
def _find_decimal_abstract_num_id(numbering_root) -> str: ...  # line 268

# Existing allocator (REWRITE inside this plan):
def _get_bibliography_num_id(paragraph, section_index=None) -> int: ...  # line 367

# Existing num-write helper (MODIFY: ilvl 0 → 1, return-value extension):
def apply_bibliography_numbering(paragraph, section_index=None) -> list[str]: ...  # line 409

# Existing match-check helper (REVIEW: may need new "valid" criterion — see Open Question 3):
def bibliography_numbering_matches(paragraph, section_index) -> bool: ...  # line 338

# Existing legacy emitter (LEAVE IN PLACE per researcher anti-pattern):
def _create_section_abstract_num_id(numbering_root, section_index: int) -> str: ...  # line 303
```

<!-- D-05 verbatim XML template — copy without paraphrase -->
The new `_create_bibliography_multilevel_abstract` function emits this exact XML structure (from ECMA-376 §17.9.16 / c-rex.net sample):

```xml
<w:abstractNum w:abstractNumId="N">
  <w:multiLevelType w:val="multilevel"/>
  <w:lvl w:ilvl="0">
    <w:start w:val="1"/>
    <w:numFmt w:val="decimal"/>
    <w:lvlText w:val="%1."/>
    <w:lvlJc w:val="left"/>
  </w:lvl>
  <w:lvl w:ilvl="1">
    <w:start w:val="1"/>
    <w:numFmt w:val="decimal"/>
    <w:lvlText w:val="%1.%2."/>
    <w:lvlJc w:val="left"/>
  </w:lvl>
</w:abstractNum>
```

Each `w:num` referencing this abstract carries TWO `w:lvlOverride` children (Pitfall 2 — without these, Word does not reset the level-1 counter across subsections):

```xml
<w:num w:numId="M">
  <w:abstractNumId w:val="N"/>
  <w:lvlOverride w:ilvl="0">
    <w:startOverride w:val="<section_index>"/>
  </w:lvlOverride>
  <w:lvlOverride w:ilvl="1">
    <w:startOverride w:val="1"/>
  </w:lvlOverride>
</w:num>
```

<!-- D-07 stable cache key — verbatim -->
The new cache key for `_BIBLIOGRAPHY_NUM_IDS` is the tuple:
```python
(id(paragraph.part.document.part), section_index)
```
not the legacy `(id(numbering_root), section_index)`. Rationale: `paragraph.part.document.part` is held by `paragraph._parent._part` for the entire Document lifetime, so `id()` does not collide with freed numbering_root elements across documents in the same Python process (Pitfall 1).

<!-- D-06 valid-numId definition (researcher Open Question 3 resolution) -->
A numId is "valid for D-06 coercion" when:
1. `_num_id_exists(paragraph, num_id)` returns True (numId resolves to a w:num in numbering.xml), AND
2. The referenced w:num's abstractNum has `<w:multiLevelType w:val="multilevel"/>`, AND
3. The abstractNum's `<w:lvl w:ilvl="1">` has `<w:lvlText w:val="%1.%2."/>`.

Legacy singleLevel numIds (entry 2 of bibliography_minimal.docx) FAIL condition 2 → treated as invalid → coerced away from. This makes D-07 idempotency work: a second run finds a Phase-2-emitted multilevel numId → matches → no further work.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Emit 2-level multilevel abstract + per-subsection w:num with lvlOverride (D-05)</name>
  <files>src/rules/rule_engine.py</files>
  <read_first>
    - src/rules/rule_engine.py lines 1-50 (imports + existing module-level state — confirm OxmlElement + qn are imported)
    - src/rules/rule_engine.py lines 283-335 (existing _next_abstract_num_id, _next_num_id, _create_section_abstract_num_id — copy the OxmlElement-build pattern verbatim)
    - .planning/phases/02-bibliography-list-semantics/02-PATTERNS.md §"src/rules/rule_engine.py — D-05 2-level abstract emission (NEW)" lines 87-135
    - .planning/phases/02-bibliography-list-semantics/02-RESEARCH.md §"Example C" lines 285-339 (exact function bodies — copy verbatim)
    - .planning/phases/02-bibliography-list-semantics/02-RESEARCH.md §"Pitfall 2" lines 214-218 (two lvlOverride children mandatory)
    - tests/test_bibliography_phase2.py::test_bibliography_multilevel_renders_section_dot_entry + test_bibliography_num_with_section_override_carries_lvlOverride (RED tests this task makes GREEN)
  </read_first>
  <behavior>
    - 2 new module-level functions in `src/rules/rule_engine.py`:
      1. `_create_bibliography_multilevel_abstract(numbering_root) -> str` — returns the new abstract's `abstractNumId` as a string. Emits ONE multilevel abstract per call; CALLERS must ensure they only call once per document (the allocator's seeded cache handles this).
      2. `_create_bibliography_num_with_section_override(numbering_root, abstract_num_id: str, section_index: int) -> int` — returns the new `numId` as an int. Emits ONE w:num pointing at the shared abstract, with two `w:lvlOverride` children.
    - Both functions use only `OxmlElement` + `qn` (no python-docx high-level API — none exists for multilevel numbering per researcher).
    - Both functions follow the existing OxmlElement build idiom (set abstractNumId / numId attribute; create children; append; return).
    - The legacy `_create_section_abstract_num_id` (lines 303-335) is NOT modified, NOT deleted — per researcher anti-pattern guidance, the bibliography path simply stops calling it.
  </behavior>
  <action>
    Insert the two new functions immediately AFTER `_create_section_abstract_num_id` (currently ending around line 335) and BEFORE `bibliography_numbering_matches` (line 338). The location keeps the OOXML emitters clustered.

    Verbatim code to insert (copy without paraphrase — XML structure is load-bearing):

    ```python
    def _create_bibliography_multilevel_abstract(numbering_root) -> str:
        """D-05: Emit a 2-level Word numbering abstract for bibliography entries.

        Structure:
          <w:abstractNum w:abstractNumId="N">
            <w:multiLevelType w:val="multilevel"/>
            <w:lvl w:ilvl="0">  ← section counter (rendered as "1.", "2.", ...)
              <w:start w:val="1"/>
              <w:numFmt w:val="decimal"/>
              <w:lvlText w:val="%1."/>
              <w:lvlJc w:val="left"/>
            </w:lvl>
            <w:lvl w:ilvl="1">  ← entry counter (rendered as "1.1.", "1.2.", ...)
              <w:start w:val="1"/>
              <w:numFmt w:val="decimal"/>
              <w:lvlText w:val="%1.%2."/>
              <w:lvlJc w:val="left"/>
            </w:lvl>
          </w:abstractNum>

        Returns the abstractNumId as a string (matches _create_section_abstract_num_id idiom).
        Word renders the entry prefix from level-1 lvlText '%1.%2.' against per-w:num
        lvlOverride values — see _create_bibliography_num_with_section_override.
        """
        abstract_num_id = _next_abstract_num_id(numbering_root)
        abstract_num = OxmlElement("w:abstractNum")
        abstract_num.set(qn("w:abstractNumId"), str(abstract_num_id))

        multi_level_type = OxmlElement("w:multiLevelType")
        multi_level_type.set(qn("w:val"), "multilevel")
        abstract_num.append(multi_level_type)

        # Level 0 — section counter (decimal, lvlText="%1.").
        lvl0 = OxmlElement("w:lvl"); lvl0.set(qn("w:ilvl"), "0")
        s0 = OxmlElement("w:start"); s0.set(qn("w:val"), "1"); lvl0.append(s0)
        f0 = OxmlElement("w:numFmt"); f0.set(qn("w:val"), "decimal"); lvl0.append(f0)
        t0 = OxmlElement("w:lvlText"); t0.set(qn("w:val"), "%1."); lvl0.append(t0)
        j0 = OxmlElement("w:lvlJc"); j0.set(qn("w:val"), "left"); lvl0.append(j0)
        abstract_num.append(lvl0)

        # Level 1 — entry counter (decimal, lvlText="%1.%2.").
        lvl1 = OxmlElement("w:lvl"); lvl1.set(qn("w:ilvl"), "1")
        s1 = OxmlElement("w:start"); s1.set(qn("w:val"), "1"); lvl1.append(s1)
        f1 = OxmlElement("w:numFmt"); f1.set(qn("w:val"), "decimal"); lvl1.append(f1)
        t1 = OxmlElement("w:lvlText"); t1.set(qn("w:val"), "%1.%2."); lvl1.append(t1)
        j1 = OxmlElement("w:lvlJc"); j1.set(qn("w:val"), "left"); lvl1.append(j1)
        abstract_num.append(lvl1)

        numbering_root.append(abstract_num)
        return str(abstract_num_id)


    def _create_bibliography_num_with_section_override(
        numbering_root,
        abstract_num_id: str,
        section_index: int,
    ) -> int:
        """D-05 + Pitfall 2: Emit a w:num pointing at the shared multilevel abstract,
        carrying two w:lvlOverride children:
          - ilvl=0 startOverride=<section_index>  → section counter starts at this subsection
          - ilvl=1 startOverride=1                → entry counter resets to 1

        WITHOUT both lvlOverride elements, Word does NOT reset the level-1 counter
        across subsections (bibliography subsection headings are Heading 1 paragraphs,
        not part of the numbering scheme). All entries would render 1.1, 1.2, ...,
        1.N continuously across subsections — wrong.
        """
        num_id = _next_num_id(numbering_root)
        num = OxmlElement("w:num")
        num.set(qn("w:numId"), str(num_id))

        abstract_ref = OxmlElement("w:abstractNumId")
        abstract_ref.set(qn("w:val"), abstract_num_id)
        num.append(abstract_ref)

        # Force level-0 counter to start at section_index.
        ov0 = OxmlElement("w:lvlOverride"); ov0.set(qn("w:ilvl"), "0")
        so0 = OxmlElement("w:startOverride"); so0.set(qn("w:val"), str(section_index))
        ov0.append(so0); num.append(ov0)

        # Reset level-1 counter at subsection boundary.
        ov1 = OxmlElement("w:lvlOverride"); ov1.set(qn("w:ilvl"), "1")
        so1 = OxmlElement("w:startOverride"); so1.set(qn("w:val"), "1")
        ov1.append(so1); num.append(ov1)

        numbering_root.append(num)
        return num_id
    ```

    Do NOT call these new functions yet from `apply_bibliography_numbering` or `_get_bibliography_num_id` — Task 2 wires them in. Insertion-only this task; the existing bibliography numbering path still uses `_create_section_abstract_num_id` until Task 2 swaps the call sites.
  </action>
  <verify>
    <automated>grep -c "^def _create_bibliography_multilevel_abstract" src/rules/rule_engine.py && grep -c "^def _create_bibliography_num_with_section_override" src/rules/rule_engine.py && python -m pytest tests/test_bibliography_phase2.py::test_bibliography_multilevel_renders_section_dot_entry tests/test_bibliography_phase2.py::test_bibliography_num_with_section_override_carries_lvlOverride -x -q 2>&1 | tail -15</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c "^def _create_bibliography_multilevel_abstract" src/rules/rule_engine.py` returns `1`.
    - `grep -c "^def _create_bibliography_num_with_section_override" src/rules/rule_engine.py` returns `1`.
    - `grep -c "^def _create_section_abstract_num_id" src/rules/rule_engine.py` returns `1` (legacy still present — anti-pattern guard).
    - `grep -F 'lvlText"), "%1.%2."' src/rules/rule_engine.py` returns the line containing the multilevel lvlText (verbatim sanity check).
    - `grep -F 'multiLevelType"); multi_level_type.set(qn("w:val"), "multilevel"' src/rules/rule_engine.py` returns the line containing the multilevel attribute (verbatim sanity check).
    - `python -m pytest tests/test_bibliography_phase2.py::test_bibliography_multilevel_renders_section_dot_entry -x -q` exits 0 — D-05 abstract GREEN.
    - `python -m pytest tests/test_bibliography_phase2.py::test_bibliography_num_with_section_override_carries_lvlOverride -x -q` exits 0 — D-05 num GREEN.
    - Phase 1 baseline `python -m pytest tests/test_style_signatures.py tests/test_positive_docx_regression.py -x -q` still 100% GREEN (no behavior change to non-bibliography paths yet).
    - `python -m pytest tests/test_rule_engine.py -x -q` still GREEN — adding new functions doesn't change existing callers.
  </acceptance_criteria>
  <done>Two new OOXML emitters added; verbatim multilevel XML in source; two Wave 0 RED tests GREEN; no callers wired yet (Task 2 wires them).</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Rewrite _get_bibliography_num_id (D-07 idempotency + stable key + D-06 coercion) and update apply_bibliography_numbering (ilvl=1, coercion tag)</name>
  <files>src/rules/rule_engine.py</files>
  <read_first>
    - src/rules/rule_engine.py lines 26-43 (module-level state — _BIBLIOGRAPHY_NUM_IDS dict)
    - src/rules/rule_engine.py lines 148-163 (_num_id_exists, paragraph_numbering_reference_is_valid — D-07 valid-numId oracle)
    - src/rules/rule_engine.py lines 338-388 (bibliography_numbering_matches, _get_bibliography_num_id, _safe_int — TO BE REPLACED in this task)
    - src/rules/rule_engine.py lines 409-429 (apply_bibliography_numbering — MODIFY: ilvl 0→1, return value extension)
    - .planning/phases/02-bibliography-list-semantics/02-RESEARCH.md §"Example D" lines 343-382 (seeded allocator skeleton)
    - .planning/phases/02-bibliography-list-semantics/02-RESEARCH.md §"Pitfall 1" lines 208-212 (cross-document leak — fix via stable key + first-call seed)
    - .planning/phases/02-bibliography-list-semantics/02-PATTERNS.md §"src/rules/rule_engine.py — D-07 idempotent seed + stable cache key" lines 173-210
    - .planning/phases/02-bibliography-list-semantics/02-PATTERNS.md §"src/rules/rule_engine.py — D-06 first-valid-numId coercion + applied_fixes tag" lines 138-170
    - tests/test_bibliography_phase2.py::test_bibliography_subsection_coerces_to_first_valid_numId, test_bibliography_idempotent_on_rerun, test_bibliography_apply_uses_ilvl_1, test_bibliography_minimal_docx_single_numId_per_subsection (RED tests this task makes GREEN)
  </read_first>
  <behavior>
    - Module-level state additions:
      - `_SEEDED_DOCS: set[int] = set()` (new).
      - `_BIBLIOGRAPHY_NUM_IDS` key tuple changes from `(id(numbering_root), section_index)` to `(id(paragraph.part.document.part), section_index)`. The dict annotation stays `dict[tuple[int, int | None], int]`.
    - New helpers:
      - `_document_cache_key(paragraph) -> int` returns `id(paragraph.part.document.part)`.
      - `_bibliography_valid_numId(paragraph, num_id) -> bool` returns True iff `_num_id_exists(paragraph, num_id)` AND the referenced abstract is multilevel with lvl-1 lvlText=`"%1.%2."`.
      - `_seed_bibliography_num_ids_from_doc(paragraph) -> None` scans `paragraph.part.document.element.body`, walks paragraphs in document order, tracks bibliography section_index from order (NOT from row_data — this seed runs without access to the predictions DataFrame), collects the FIRST valid numId per section_index, seeds `_BIBLIOGRAPHY_NUM_IDS[(doc_key, section_index)] = first_valid_num_id`.
    - `_get_bibliography_num_id(paragraph, section_index)` rewritten:
      1. Compute `doc_key = _document_cache_key(paragraph)`.
      2. If `doc_key not in _SEEDED_DOCS`: call `_seed_bibliography_num_ids_from_doc(paragraph)`; add `doc_key` to `_SEEDED_DOCS`.
      3. Compute `root_key = (doc_key, section_index)`.
      4. If `root_key in _BIBLIOGRAPHY_NUM_IDS`: return the cached numId.
      5. Else: allocate a shared multilevel abstract once per doc (cache it on `doc_key` in a NEW dict `_BIBLIOGRAPHY_ABSTRACTS: dict[int, str] = {}`); allocate a fresh per-subsection w:num via `_create_bibliography_num_with_section_override`; populate `_BIBLIOGRAPHY_NUM_IDS[root_key]`; return the new numId.
    - `apply_bibliography_numbering(paragraph, section_index)` modifications:
      - The `<w:ilvl>` element's `w:val` becomes `"1"` (was `"0"`).
      - Detect coercion: if the paragraph ALREADY had a `<w:numId>` with a value DIFFERENT from the target allocated numId, append `f"numbering:coerced_to_numId={target}"` to the returned list IN ADDITION to `"numbering"`.
    - `bibliography_numbering_matches(paragraph, section_index)` REWRITE to compare against the new lvlText:
      - Returns True iff the paragraph's current numId resolves to a multilevel abstract whose lvl-1 lvlText is `"%1.%2."` AND whose corresponding w:num has lvlOverride ilvl=0 startOverride=`section_index`.
      - Returns False on legacy singleLevel numIds (so D-07 idempotency correctly RE-allocates rather than declaring them "matched").
  </behavior>
  <action>
    **CRITICAL: This task does a coordinated rewrite. Read it through TWICE before editing. Test after EACH sub-step.**

    **Sub-step 2a — Add module-level state additions.** Find the existing `_BIBLIOGRAPHY_NUM_IDS: dict[...] = {}` declaration around line 43. Replace its annotation comment and add `_SEEDED_DOCS` + `_BIBLIOGRAPHY_ABSTRACTS` immediately after. The key shape annotation stays the same — semantically the first int is now `id(document.part)` rather than `id(numbering_root)`:

    ```python
    # Cache for bibliography numIds. Key: (id(paragraph.part.document.part), section_index).
    # Switched from id(numbering_root) in Phase 2 — see Pitfall 1 in 02-RESEARCH.md.
    _BIBLIOGRAPHY_NUM_IDS: dict[tuple[int, int | None], int] = {}

    # Tracks which documents have already had their numbering.xml scanned for
    # existing bibliography numIds. Key: id(paragraph.part.document.part).
    # D-07: first-call seed prevents re-discovery on every paragraph.
    _SEEDED_DOCS: set[int] = set()

    # Cache for the shared multilevel abstractNumId per document. One abstract
    # per doc — every per-subsection w:num references it.
    # Key: id(paragraph.part.document.part); Value: str(abstractNumId).
    _BIBLIOGRAPHY_ABSTRACTS: dict[int, str] = {}
    ```

    **Sub-step 2b — Add new helpers immediately before `_get_bibliography_num_id`** (line 367). Place in this exact order:

    ```python
    def _document_cache_key(paragraph: Paragraph) -> int:
        """D-07: Stable cache key for the document containing this paragraph.

        Returns id(paragraph.part.document.part) which lives as long as the
        Document object (held via paragraph._parent._part). Prevents the
        cross-document id() collision that legacy id(numbering_root) suffered
        (Pitfall 1).
        """
        return id(paragraph.part.document.part)


    def _bibliography_valid_numId(paragraph: Paragraph, num_id: str | int | None) -> bool:
        """D-06 + Open Question 3: A numId is 'valid' for bibliography coercion when:
          1. It exists in numbering.xml (_num_id_exists), AND
          2. Its abstractNum has multiLevelType=multilevel, AND
          3. Its level-1 lvlText is exactly '%1.%2.'.

        Legacy singleLevel numIds (Phase-1-era) FAIL conditions 2-3 → treated as
        invalid → D-06 coerces away from them. Phase-2-emitted multilevel numIds
        PASS all three → idempotent re-runs find them and reuse.
        """
        if num_id is None or not _num_id_exists(paragraph, num_id):
            return False
        try:
            numbering_root = paragraph.part.numbering_part.element
            # Find w:num with matching w:numId.
            target_num = None
            for n in numbering_root.findall(qn("w:num")):
                if n.get(qn("w:numId")) == str(num_id):
                    target_num = n
                    break
            if target_num is None:
                return False
            abs_ref = target_num.find(qn("w:abstractNumId"))
            if abs_ref is None:
                return False
            abs_num_id_val = abs_ref.get(qn("w:val"))
            # Find the abstractNum.
            target_abstract = None
            for a in numbering_root.findall(qn("w:abstractNum")):
                if a.get(qn("w:abstractNumId")) == abs_num_id_val:
                    target_abstract = a
                    break
            if target_abstract is None:
                return False
            mlt = target_abstract.find(qn("w:multiLevelType"))
            if mlt is None or mlt.get(qn("w:val")) != "multilevel":
                return False
            # Check level-1 lvlText.
            for lvl in target_abstract.findall(qn("w:lvl")):
                if lvl.get(qn("w:ilvl")) == "1":
                    lvl_text = lvl.find(qn("w:lvlText"))
                    return lvl_text is not None and lvl_text.get(qn("w:val")) == "%1.%2."
            return False
        except Exception:
            return False


    def _seed_bibliography_num_ids_from_doc(paragraph: Paragraph) -> None:
        """D-07: One-time-per-document scan. Walks the document body in order,
        identifies bibliography sections by Heading 1 inside bibliography context
        (mirrors postprocess D-04 logic), collects the FIRST valid numId per
        section_index, and seeds _BIBLIOGRAPHY_NUM_IDS[(doc_key, section_index)].

        Re-runs on already-corrected documents find a single valid multilevel
        numId per section → cache hits → no allocation → idempotent.
        """
        from src.postprocess.postprocess_rules import (
            _is_bibliography_title as _is_bib_title,
            _stops_bibliography_context as _stops_bib,
            BIBLIOGRAPHY_SUBHEADING_RE as _bib_subhead_re,
        )

        doc_key = _document_cache_key(paragraph)
        body = paragraph.part.document.element.body

        in_bib = False
        section_index = 0
        for p_elem in body.iter(qn("w:p")):
            # Extract text from runs.
            text = "".join(t.text or "" for t in p_elem.iter(qn("w:t"))).strip()
            if not text:
                continue
            if _is_bib_title(text):
                in_bib = True
                continue
            if in_bib and _stops_bib(text, ""):
                in_bib = False
                continue
            if not in_bib:
                continue

            # Subsection detection: Heading style OR fallback regex.
            p_pr_local = p_elem.find(qn("w:pPr"))
            style_name = None
            if p_pr_local is not None:
                p_style = p_pr_local.find(qn("w:pStyle"))
                if p_style is not None:
                    style_name = p_style.get(qn("w:val")) or ""
            # Word stores 'Heading 1' as style id 'Heading1'/'Heading2' or RU 'Заголовок1' etc.
            # Use a simple "Heading"/"Заголовок" startswith — full classify_style is overkill
            # for the seed path. Plan 04 may tighten if needed.
            is_subsection = (
                (style_name is not None and (style_name.startswith("Heading") or style_name.startswith("Заголовок")))
                or _bib_subhead_re.search(text) is not None
            )
            if is_subsection:
                section_index += 1
                continue

            # Bibliography entry — read numId.
            num_id_val: str | None = None
            if p_pr_local is not None:
                num_pr = p_pr_local.find(qn("w:numPr"))
                if num_pr is not None:
                    n_id = num_pr.find(qn("w:numId"))
                    if n_id is not None:
                        num_id_val = n_id.get(qn("w:val"))

            if num_id_val is None or section_index < 1:
                continue
            # Validate this numId against D-06 criterion.
            if not _bibliography_valid_numId(paragraph, num_id_val):
                continue
            key = (doc_key, section_index)
            if key not in _BIBLIOGRAPHY_NUM_IDS:
                _BIBLIOGRAPHY_NUM_IDS[key] = int(num_id_val)
    ```

    **Sub-step 2c — Replace `_get_bibliography_num_id` (lines 367-388)** with the new seeded + coerce-aware allocator:

    ```python
    def _get_bibliography_num_id(paragraph: Paragraph, section_index: int | None = None) -> int:
        """D-05/D-06/D-07 allocator.

        - First call per document: scan numbering.xml for existing valid (multilevel
          + %1.%2.) bibliography numIds and seed _BIBLIOGRAPHY_NUM_IDS.
        - Cache hit (root_key seeded OR previously allocated): return cached numId
          (idempotency).
        - Cache miss: allocate a shared multilevel abstract once per doc, allocate
          a fresh per-subsection w:num with lvlOverride, cache and return.
        """
        doc_key = _document_cache_key(paragraph)
        if doc_key not in _SEEDED_DOCS:
            _seed_bibliography_num_ids_from_doc(paragraph)
            _SEEDED_DOCS.add(doc_key)

        root_key = (doc_key, section_index)
        cached = _BIBLIOGRAPHY_NUM_IDS.get(root_key)
        if cached is not None:
            return int(cached)

        # Allocate fresh: shared abstract (once per doc) + per-subsection w:num.
        numbering_root = paragraph.part.numbering_part.element
        abstract_num_id = _BIBLIOGRAPHY_ABSTRACTS.get(doc_key)
        if abstract_num_id is None:
            abstract_num_id = _create_bibliography_multilevel_abstract(numbering_root)
            _BIBLIOGRAPHY_ABSTRACTS[doc_key] = abstract_num_id

        # section_index may be None when the caller didn't pass it — treat as 1.
        effective_section = section_index if section_index is not None else 1
        new_num_id = _create_bibliography_num_with_section_override(
            numbering_root, abstract_num_id, int(effective_section)
        )
        _BIBLIOGRAPHY_NUM_IDS[root_key] = new_num_id
        return new_num_id
    ```

    **Sub-step 2d — Rewrite `bibliography_numbering_matches` (lines 338-364).** The new "matches" condition is: paragraph's current numId is valid per D-06 criterion AND its w:num's lvlOverride[ilvl=0] startOverride == section_index. Replace the entire function:

    ```python
    def bibliography_numbering_matches(paragraph: Paragraph, section_index: int | None) -> bool:
        """D-07 idempotency oracle. A paragraph is "already correctly numbered" iff:
          1. Its numId is valid per D-06 criterion (multilevel abstract, lvl-1 lvlText '%1.%2.'), AND
          2. Its w:num carries a lvlOverride[ilvl=0] whose startOverride == section_index, AND
          3. Its <w:ilvl> is "1".

        When all true → no change needed → audit reports no fix → re-run shows changed=0.
        """
        try:
            p_pr = paragraph._p.find(qn("w:pPr"))
            if p_pr is None:
                return False
            num_pr = p_pr.find(qn("w:numPr"))
            if num_pr is None:
                return False
            ilvl_el = num_pr.find(qn("w:ilvl"))
            if ilvl_el is None or ilvl_el.get(qn("w:val")) != "1":
                return False
            num_id_el = num_pr.find(qn("w:numId"))
            if num_id_el is None:
                return False
            num_id_val = num_id_el.get(qn("w:val"))
            if not _bibliography_valid_numId(paragraph, num_id_val):
                return False
            # Verify lvlOverride[ilvl=0] startOverride matches section_index.
            numbering_root = paragraph.part.numbering_part.element
            for n in numbering_root.findall(qn("w:num")):
                if n.get(qn("w:numId")) != num_id_val:
                    continue
                for ov in n.findall(qn("w:lvlOverride")):
                    if ov.get(qn("w:ilvl")) == "0":
                        so = ov.find(qn("w:startOverride"))
                        if so is not None and section_index is not None and so.get(qn("w:val")) == str(section_index):
                            return True
                return False
            return False
        except Exception:
            return False
    ```

    **Sub-step 2e — Modify `apply_bibliography_numbering` (lines 409-429)** to (a) set `<w:ilvl w:val="1"/>` and (b) emit `numbering:coerced_to_numId=<N>` when coercing from a different pre-existing numId. Replace the function body:

    ```python
    def apply_bibliography_numbering(paragraph: Paragraph, section_index: int | None = None) -> list[str]:
        """D-05 + D-06: Set numPr.numId to the allocator's choice for this subsection,
        and set numPr.ilvl=1 (entries live at level 1 in the multilevel abstract).

        Returns:
          ['numbering']                                  — fresh allocation or seeded match.
          ['numbering', 'numbering:coerced_to_numId=N']  — paragraph had a different numId,
                                                           D-06 coerced it to N.
        """
        p_pr = paragraph._p.get_or_add_pPr()
        num_pr = p_pr.find(qn("w:numPr"))
        is_fresh_numPr = num_pr is None
        previous_num_id_val: str | None = None
        if is_fresh_numPr:
            num_pr = OxmlElement("w:numPr")
            p_pr.append(num_pr)
        else:
            prev = num_pr.find(qn("w:numId"))
            if prev is not None:
                previous_num_id_val = prev.get(qn("w:val"))

        # Force ilvl=1 (entries are at level 1; section counter is level 0 via lvlOverride).
        ilvl = num_pr.find(qn("w:ilvl"))
        if ilvl is None:
            ilvl = OxmlElement("w:ilvl")
            num_pr.append(ilvl)
        ilvl.set(qn("w:val"), "1")

        target_num_id = _get_bibliography_num_id(paragraph, section_index)
        num_id_el = num_pr.find(qn("w:numId"))
        if num_id_el is None:
            num_id_el = OxmlElement("w:numId")
            num_pr.append(num_id_el)
        num_id_el.set(qn("w:val"), str(target_num_id))

        applied = ["numbering"]
        # D-06 — emit coercion tag when we changed an existing numId to a different one.
        if (
            previous_num_id_val is not None
            and previous_num_id_val != str(target_num_id)
        ):
            applied.append(f"numbering:coerced_to_numId={target_num_id}")
        return applied
    ```
  </action>
  <verify>
    <automated>python -c "from src.rules.rule_engine import _get_bibliography_num_id, apply_bibliography_numbering, _seed_bibliography_num_ids_from_doc, _bibliography_valid_numId, _document_cache_key, _SEEDED_DOCS, _BIBLIOGRAPHY_ABSTRACTS, bibliography_numbering_matches; print('symbols OK')" && python -m pytest tests/test_bibliography_phase2.py::test_bibliography_apply_uses_ilvl_1 tests/test_bibliography_phase2.py::test_bibliography_subsection_coerces_to_first_valid_numId tests/test_bibliography_phase2.py::test_bibliography_idempotent_on_rerun tests/test_bibliography_phase2.py::test_bibliography_minimal_docx_single_numId_per_subsection tests/test_bibliography_phase2.py::test_negative_4_bibliography_single_numId -x -q 2>&1 | tail -30</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c "^def _document_cache_key" src/rules/rule_engine.py` returns `1`.
    - `grep -c "^def _bibliography_valid_numId" src/rules/rule_engine.py` returns `1`.
    - `grep -c "^def _seed_bibliography_num_ids_from_doc" src/rules/rule_engine.py` returns `1`.
    - `grep -c "_SEEDED_DOCS: set\[int\] = set()" src/rules/rule_engine.py` returns `1`.
    - `grep -c "_BIBLIOGRAPHY_ABSTRACTS: dict" src/rules/rule_engine.py` returns `1`.
    - `grep -F 'ilvl.set(qn("w:val"), "1")' src/rules/rule_engine.py` returns at least 1 line (in apply_bibliography_numbering — the new ilvl=1).
    - `grep -F 'numbering:coerced_to_numId=' src/rules/rule_engine.py` returns ≥1 line (D-06 tag).
    - `python -m pytest tests/test_bibliography_phase2.py::test_bibliography_apply_uses_ilvl_1 -x -q` exits 0.
    - `python -m pytest tests/test_bibliography_phase2.py::test_bibliography_subsection_coerces_to_first_valid_numId -x -q` exits 0 — D-06 tag emitted on bibliography_minimal.docx subsection 1.
    - `python -m pytest tests/test_bibliography_phase2.py::test_bibliography_idempotent_on_rerun -x -q` exits 0 — D-07 idempotency, second run changed=0.
    - `python -m pytest tests/test_bibliography_phase2.py::test_bibliography_minimal_docx_single_numId_per_subsection -x -q` exits 0 — D-14 hand-crafted integration GREEN.
    - `python -m pytest tests/test_bibliography_phase2.py::test_negative_4_bibliography_single_numId -x -q` exits 0 OR skips with "fixture not present".
    - Phase 1 baseline `python -m pytest tests/test_positive_docx_regression.py tests/test_style_signatures.py -x -q` still GREEN (the cache-key change does not break positive_examples — files 1/4/58/59 have NO bibliography sections, so the bibliography path doesn't fire on them).
    - `python -m pytest tests/test_rule_engine.py -x -q` GREEN — existing bibliography tests in this file (lines 355-700) may rely on the old singleLevel format; if any FAIL, copy the assertion shape and verify whether the test pinned `ilvl="0"` or the legacy `lvlText` — those tests must be UPDATED to the new contract OR the test names documented in the SUMMARY as "Phase 2 changed behavior" with rationale.
  </acceptance_criteria>
  <done>D-05/D-06/D-07 wired end-to-end; 5+ Wave 0 RED tests GREEN; Phase 1 baseline preserved.</done>
</task>

</tasks>

<verification>
After both tasks complete:

```bash
python -m pytest tests/ -x -q 2>&1 | tail -40
```

Expected outcome:
- Phase 1 baseline preserved: positive_examples + style_signatures + non-bibliography test_rule_engine still green.
- Wave 0 tests gated by this plan turn GREEN:
  - test_bibliography_multilevel_renders_section_dot_entry (D-05 abstract)
  - test_bibliography_num_with_section_override_carries_lvlOverride (D-05 num)
  - test_bibliography_apply_uses_ilvl_1 (D-05 ilvl)
  - test_bibliography_subsection_coerces_to_first_valid_numId (D-06)
  - test_bibliography_idempotent_on_rerun (D-07)
  - test_bibliography_minimal_docx_single_numId_per_subsection (D-14 hand-crafted)
  - test_negative_4_bibliography_single_numId (D-14 negative — if fixture present)
  - test_negative_3_bibliography_coerces_mixed_numIds (D-06 + D-14 negative — if fixture present)
- Wave 0 tests still gated by Plan 04:
  - test_ambiguous_list_marker_no_numId_routes_to_review (D-09 — branch not added yet)
  - test_bibliography_format_skips_alignment_when_profile_omits (D-13 — formatting_rules_v1.json strip not done yet)
  - test_negative_corpus_diff_rate_phase2_baseline (D-15 — Plan 04 may need to relax / widen)
- Bibliography integration on D-14 negative DOCX produces applied_fixes containing "numbering" for at least one row.

If existing tests in `tests/test_rule_engine.py` lines 355-700 (legacy bibliography family) FAIL because they pinned old singleLevel behavior (ilvl="0", lvlText pattern), document each failure in the SUMMARY with one of two resolutions:
1. The legacy test pinned the OLD wrong behavior — UPDATE the test assertion to match the new D-05 contract.
2. The legacy test exercises a non-bibliography path — INVESTIGATE; this would indicate the cache-key migration broke something unrelated, which is a bug.
</verification>

<success_criteria>
- src/rules/rule_engine.py has 3 new module-level state declarations (_SEEDED_DOCS, _BIBLIOGRAPHY_ABSTRACTS, plus the documented key-meaning shift of _BIBLIOGRAPHY_NUM_IDS).
- src/rules/rule_engine.py has 5 new functions (_create_bibliography_multilevel_abstract, _create_bibliography_num_with_section_override, _document_cache_key, _bibliography_valid_numId, _seed_bibliography_num_ids_from_doc).
- 2 functions rewritten (_get_bibliography_num_id, bibliography_numbering_matches).
- 1 function modified (apply_bibliography_numbering — ilvl=1, coercion tag).
- D-05 + D-06 + D-07 Wave 0 RED tests turn GREEN.
- D-14 hand-crafted integration test on bibliography_minimal.docx GREEN.
- Phase 1 positive-corpus baseline preserved (changed=0 on 1/4/58/59).
- Legacy `_create_section_abstract_num_id` left in place per researcher anti-pattern.
</success_criteria>

<output>
After completion, create `.planning/phases/02-bibliography-list-semantics/02-03-multilevel-numbering-green-SUMMARY.md` documenting:
- New functions added (5) with one-line descriptions.
- Functions rewritten (2: _get_bibliography_num_id, bibliography_numbering_matches).
- Module-level state additions (_SEEDED_DOCS, _BIBLIOGRAPHY_ABSTRACTS, key-meaning shift documented).
- Wave 0 tests turned GREEN.
- Any legacy tests in test_rule_engine.py that were UPDATED to the new contract (with justification per test).
- Phase 1 baseline test count + result.
- D-14 negative DOCX integration result (numId-per-subsection on real `4_formatted_*.docx`).
- Confirmation that legacy `_create_section_abstract_num_id` is still in place but no longer called from bibliography path (`grep` callsites).
</output>
</content>
