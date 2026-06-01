# Phase 2: Bibliography & list semantics - Research

**Researched:** 2026-05-12
**Domain:** DOCX bibliography detection + Word numbering hierarchy + profile schema extension
**Confidence:** HIGH (all 10 research areas resolved against live code + OOXML spec; one open question on D-04 fallback regex)

## Summary

Phase 2 lands on a mature engine: Phase 1 shipped `classify_style()` + style guard in `apply_rules_to_paragraph` (line 786-798), and Phase 2 inherits a working `bibliography_section_index` plumbing through postprocess → CSV → `row_data`. The work splits cleanly into four areas:

1. **Detection** (D-01, D-04) — postprocess is THE place. `BIBLIOGRAPHY_TITLE_RE` already exists at `src/postprocess/postprocess_rules.py:12`; today's detection inside `apply_postprocess_rules` (line 165) already sets `label = bibliography_title` when the regex matches, BUT only when the SVM didn't preempt it on the position-walk pass. The D-01 strengthening is to make this override unconditional (move the regex check to a first-pass label rewrite before any other label logic). For D-04, replace `BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE`-only gating at line 173-175 with `classify_style(paragraph) == "heading"` AND position-in-bibliography-context.

2. **Numbering** (D-05, D-06, D-07) — `_create_section_abstract_num_id` (line 303) currently emits a `singleLevel` abstract with the section index BAKED INTO `lvlText` as `f"{section_index}.%1"` (literal string). D-05 wants a TRUE 2-level abstract: `multiLevelType="multilevel"`, `ilvl=0` decimal w/ `lvlText="%1."`, `ilvl=1` decimal w/ `lvlText="%1.%2."`. Word renders entry display automatically from the two counters. D-06 adds "first-valid-numId-in-subsection wins" coercion; D-07 seeds `_BIBLIOGRAPHY_NUM_IDS` from `numbering_part.element` scan on first call per document AND fixes the latent cross-document `id()` collision.

3. **Ambiguous routing** (D-09, D-10) — Phase 1's style guard at line 786-798 already covers D-10 (no-marker + Normal style + body_text label flows through the guard's "body" branch and proceeds normally; long plain paragraph then hits the existing `_is_long_plain_paragraph` check). D-09 needs a NEW branch in `apply_rules_to_paragraph` between the style guard and the rule loop: if `label == "body_text"`, paragraph_style != list, marker present, no `numId` → return `review` with `ambiguous_list_marker_no_numId`.

4. **Profile schema** (D-03, D-11, D-13) — `profile_loader.py` + `profile_validator.py` use a strict required-keys validator. Add new optional sections `numbering.bibliography.scope` and `list_detection.{max_fallback_words,max_fallback_chars}`. Default profile `src/rules/profiles/gost_7_32_2017.json` carries current values (per_section / 40 / 300). Delete hard-coded `MAX_FALLBACK_LIST_*` constants from `rule_engine.py` and thread profile through `apply_rules_to_paragraph`. D-13 reshapes `apply_bibliography_format` to apply ONLY `style_name + numbering` always; scalars only if profile carries the field.

**Primary recommendation:** Build the new 2-level abstract template alongside the existing `_create_section_abstract_num_id` (don't refactor in place — Phase 1 mid-air migrations are a known footgun). Seed the dict at first-call via numbering.xml scan, keyed by a stable `id(paragraph.part.document.part)` to kill the `id(numbering_root)` collision. Implement profile threading by passing the loaded `profile` dict through `apply_rules_to_paragraph` (it already gets `default_font_name` — same wiring point). Tests: extend `_build_style_guard_minimal.py` pattern with `_build_bibliography_minimal.py`; integration fixture is any of the 17 negative_examples (all carry a bibliography title).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `BIBLIOGRAPHY_TITLE_RE` deterministic label override (D-01) | Postprocess (`src/postprocess/postprocess_rules.py`) | — | Postprocess already owns `apply_postprocess_rules`; SVM output is its input. Per Phase 1 D-001-style separation, "label override before rule engine dispatch". |
| Bibliography subsection position+style detection (D-04) | Postprocess | Rule engine reads `bibliography_section_index` from row_data | `bibliography_section_index` is already stamped onto the dataframe at `postprocess_rules.py:203` and read by `_bibliography_section_index` in `rule_engine.py:432`. Detection logic moves to postprocess (has access to paragraph order); rule engine consumes the stamped int. |
| 2-level Word numbering abstract emission (D-05) | Rule engine (`src/rules/rule_engine.py`) | python-docx OOXML primitives | Existing `_create_section_abstract_num_id` lives here; numbering manipulation requires Paragraph.part.numbering_part access. |
| Idempotent allocator seeding (D-07) | Rule engine | python-docx | `_BIBLIOGRAPHY_NUM_IDS` cache lives in rule_engine module; numbering.xml scan needs access to the Document part. |
| First-valid-numId-in-subsection coercion (D-06) | Rule engine | — | Same module as allocator + section-index lookup. |
| Ambiguous-list `review` routing (D-09) | Rule engine `apply_rules_to_paragraph` | — | Style guard precedent (Phase 1) lives there; routing must happen BEFORE rule loop. |
| Profile schema extension (D-03, D-11) | Profile loader / validator (`src/rules/profile_loader.py`, `profile_validator.py`) | Default profile JSON | Schema validation is centralized; adding new fields requires validator changes. |
| Profile-driven thresholds + autofix scope (D-11, D-13) | Rule engine reads profile, applies conditionally | Profile loader supplies dict | Profile flows from CLI/inplace_formatter into rule engine — needs a new wiring parameter. |
| Hand-crafted DOCX fixture (D-14) | Tests (`tests/fixtures/`) | python-docx | Mirrors Phase 1 pattern `_build_style_guard_minimal.py`. |
| Negative-corpus diff-rate gate (D-15) | Tests + `src/evaluation/format_regression_audit.py` | — | Gate is enforced via direct `audit_negative_directory` call (Plan 03 precedent). |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-docx | already in project | DOCX read/write, OOXML primitives | Already the only DOCX dep; project ships against `docx.oxml.OxmlElement`, `qn`, `Paragraph.part.numbering_part.element` (verified at `rule_engine.py:151, 168, 191`). |
| pandas | already in project | Postprocess dataframe ops | Already used in `apply_postprocess_rules`. |
| pytest | already in project | Test runner | Phase 1 baseline 53 tests. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none added by Phase 2) | — | — | Phase 2 is a behavioral change, not a stack addition. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-rolled 2-level abstract XML | python-docx high-level numbering API | python-docx has NO high-level multi-level numbering API (verified: docs at python-docx_readthedocs_io_en list `_NumberingStyle` as "Not yet implemented"). Direct OOXML manipulation via `OxmlElement` is the only path — same pattern Phase 2's existing `_create_section_abstract_num_id` uses. |
| Stable cache key via `id(numbering_root)` | UUID stored on the part, or `id(paragraph.part.document.part)` | `id()` collisions across documents in the same Python process are real (CPython reuses freed object IDs). The cache MUST be keyed by something that lives as long as the document. Recommended: `id(paragraph.part.document.part)` because `document.part` is held by `paragraph._parent._part` for the document lifetime. |

**Installation:** No new packages.

**Version verification:**
```bash
python -c "import docx; print(docx.__version__)"
```
Verify python-docx is at a version that exposes `OxmlElement`, `qn`, `Paragraph.part.numbering_part.element` — already in use, so no upgrade needed.

## Architecture Patterns

### System Architecture Diagram

```
DOCX input                                    profile JSON
   │                                               │
   ▼                                               ▼
extract-docx → blocks CSV       profile_loader.load_profile()
   │                                               │
   ▼                                               │
predict-blocks → predictions                       │
   │                                               │
   ▼                                               │
apply_postprocess_rules ◄─── D-01: unconditional override BIBLIOGRAPHY_TITLE_RE → label=bibliography_title
   │                    │── D-04: position+Heading 1 style → bibliography_section_index
   │                    └── stamps row_data: postprocessed_label, bibliography_section_index
   ▼
audit_or_format_docx (inplace_formatter)            │
   │                                                │
   ▼                                                ▼
apply_rules_to_paragraph(paragraph, label, row_data, rules, profile)
   ├── Phase 1 style guard (line 786-798): body_text → review on non-body styles
   ├── NEW D-09: body_text + marker + no numId → review (ambiguous_list_marker_no_numId)
   ├── bibliography rules → _apply_bibliography_rules → apply_bibliography_format
   │       └── D-05: 2-level abstract via _create_section_abstract_num_id (REWRITTEN)
   │       └── D-06: scan subsection for first-valid numId, coerce others
   │       └── D-07: _get_bibliography_num_id seeds dict from numbering.xml on first call
   │       └── D-13: apply only style_name + numbering always; scalars iff profile carries field
   ├── scalar rules → _apply_scalar_rule (Phase 1)
   └── list rules → list_format (uses MAX_FALLBACK_LIST_* — replaced by profile lookup, D-11)
   │
   ▼
audit report CSV + corrected DOCX
```

### Recommended Project Structure
```
src/
├── postprocess/postprocess_rules.py       # D-01 override + D-04 position-based subsection detection
├── rules/
│   ├── rule_engine.py                     # D-05/06/07/09/13/11 — all numbering + routing changes
│   ├── profile_loader.py                  # D-11 helper getters: get_list_detection_thresholds, get_bibliography_scope
│   ├── profile_validator.py               # D-03/D-11 — new optional schema fields
│   └── profiles/gost_7_32_2017.json       # carry current values explicitly
├── evaluation/format_regression_audit.py  # Phase 2 reuses Phase 1's gate (no changes)
tests/
├── fixtures/
│   ├── _build_bibliography_minimal.py     # NEW (mirror _build_style_guard_minimal.py)
│   └── bibliography_minimal.docx          # NEW binary fixture
├── test_postprocess_rules.py              # extend with D-01 override + D-04 position+heading tests
├── test_rule_engine.py                    # extend with D-05/06/07/09/13 tests
├── test_profile_loader.py                 # NEW or extend — D-11 threshold reads from profile
└── test_bibliography_negative_integration.py  # NEW — D-14 integration on one negative_examples doc
```

### Pattern 1: Postprocess label override (D-01)

**What:** Replace conditional override at `postprocess_rules.py:165-167` with a first-pass rewrite that runs BEFORE the body_text→list_item pass at line 130 and the list-intro pass at line 135.

**When to use:** For every paragraph whose `text` matches `BIBLIOGRAPHY_TITLE_RE` — unconditional, regardless of SVM predicted_label.

**Example:**
```python
# Source: src/postprocess/postprocess_rules.py (line 124-135 area — add new pre-pass)
# Before any of the body_text/list_item label-rewriting passes:
for position in range(len(labels)):
    if _is_bibliography_title(texts[position]):
        labels[position] = "bibliography_title"
# Then run the existing body_text→list_item, list-intro, bibliography-context passes as today.
```

### Pattern 2: 2-level abstract emission (D-05)

**What:** Emit `w:abstractNum` with `multiLevelType="multilevel"` and two `w:lvl` children rendering `1.1`, `1.2`, `2.1`.

**When to use:** Per document, ONCE — reuse the same abstract across all bibliography subsections; only allocate fresh `w:num` (numId pointer) per subsection.

**Example:**
```xml
<!-- Source: ecma-376 §17.9.16 (sample at c-rex.net/.../w_abstractNum_topic) -->
<w:abstractNum w:abstractNumId="N">
  <w:multiLevelType w:val="multilevel"/>
  <w:lvl w:ilvl="0">
    <w:start w:val="1"/>
    <w:numFmt w:val="decimal"/>
    <w:lvlText w:val="%1."/>
    <w:lvlJc w:val="left"/>
    <w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>
  </w:lvl>
  <w:lvl w:ilvl="1">
    <w:start w:val="1"/>
    <w:numFmt w:val="decimal"/>
    <w:lvlText w:val="%1.%2."/>
    <w:lvlJc w:val="left"/>
    <w:pPr><w:ind w:left="1440" w:hanging="360"/></w:pPr>
  </w:lvl>
</w:abstractNum>
<!-- One <w:num> per subsection, all pointing at the same abstractNumId.
     Paragraphs in each subsection set their numPr to (numId, ilvl=1), so Word
     renders "1.1", "1.2" automatically. Subsection counter advancement happens
     via lvl-0 paragraphs in document order. -->
```

**Critical detail:** Bibliography entry paragraphs use `ilvl=1` (not `ilvl=0` as today). Word increments the level-0 counter only when a level-0 paragraph appears OR by an explicit `<w:lvlOverride><w:startOverride w:val="N"/></w:lvlOverride>` on the `w:num` element setting the section_index. Researcher recommends: use `lvlOverride` because entries don't carry a level-0 paragraph between sections (the section header is a Heading style, not part of the numbering scheme). One `w:num` per subsection, each with a `lvlOverride w:ilvl="0"` setting `startOverride` to the section_index. This makes level-1 lvlText "%1.%2." render `<section_index>.<entry_index>`.

### Pattern 3: Idempotent allocator seeding (D-07)

**What:** First call to `_get_bibliography_num_id` for a document scans `numbering_part.element` for existing `w:num` elements referenced by `bibliography_item` paragraphs, groups them by `section_index` (read from the corresponding row_data), and seeds the cache so re-runs find the same numId.

**When to use:** Inside `_get_bibliography_num_id` at `rule_engine.py:367` — early return if seeded.

**Example:**
```python
# Source: derived from existing pattern at rule_engine.py:367-388
def _get_bibliography_num_id(paragraph, section_index, document_cache_key):
    if document_cache_key not in _SEEDED_DOCS:
        _seed_bibliography_num_ids_from_doc(paragraph.part)
        _SEEDED_DOCS.add(document_cache_key)
    # ... rest of allocator unchanged ...
```

**Stable key recommendation:** `document_cache_key = id(paragraph.part.document.part)`. The `document.part` reference is held by every paragraph for the lifetime of the document — `id()` is stable while the document is in memory and goes away when the document is garbage-collected, preventing leaks across documents in the same process.

### Anti-Patterns to Avoid

- **Editing `_create_section_abstract_num_id` in place:** It bakes section_index as LITERAL text into `lvlText`. The 2-level rewrite changes the emission model fundamentally (`multiLevelType` "singleLevel" → "multilevel"; level count 1 → 2; per-subsection abstract → shared abstract w/ per-subsection num+lvlOverride). Rename the legacy as `_create_section_abstract_num_id__legacy_singleLevel` and write a new `_create_bibliography_multilevel_abstract` to avoid mid-air breakage of `bibliography_numbering_matches` (line 338).
- **Stamping `bibliography_section_index` lazily from rule_engine:** All callers of `apply_rules_to_paragraph` go through `inplace_formatter.py:423` which already passes `row_data = row._asdict()`. Postprocess already stamps the int into the CSV. Keep this contract; do not re-derive in rule_engine.
- **Resetting `_BIBLIOGRAPHY_NUM_IDS` between docs from tests:** The leak is architectural — fix it at the allocator (D-07's stable key), not by clearing module state from test fixtures.
- **Adding the D-09 review branch inside `_apply_scalar_rule` or `_apply_bibliography_rules`:** The check is about LABEL ROUTING, not about a specific rule. Place it next to the Phase 1 style guard at `apply_rules_to_paragraph:786`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 2-level multi-level numbering rendering | A loop that prefixes `f"{section}.{entry} "` into paragraph text | Word `<w:abstractNum>` with `multiLevelType="multilevel"` + level-1 `lvlText="%1.%2."` + `lvlOverride` per num | Word renders the prefix from counters; injecting text into paragraph runs would (a) break audit re-runs, (b) double-prefix on second run, (c) violate D-004 "no silent rewrites of text". |
| Tracking section index lazily in rule_engine from paragraph order | Re-walk document.paragraphs inside `apply_rules_to_paragraph` | `bibliography_section_index` field on row_data, stamped by postprocess (already exists, line 178/181 of postprocess_rules.py) | Postprocess sees ALL paragraphs of a doc in one pass; rule engine sees one at a time. Don't re-implement order tracking. |
| numId allocation idempotency | Clear module dict between documents | Seed dict from `numbering_part.element` scan on first call + stable key per document | Module-level state with `id()` keys is leaky. Scan-on-first-call is the only correct way. |
| Profile threshold lookup | `if config.get("max_fallback_list_words", 40)` scattered in rule_engine | Single helper `get_list_detection_thresholds(profile) -> (max_words, max_chars)` in `profile_loader.py` | One place to read, validators+tests cover one function, profile updates land in one schema location. |

**Key insight:** Phase 2's biggest hand-roll temptation is the section.entry text prefix. RESIST IT. Word's `lvlText="%1.%2."` is exactly the right primitive — and the existing `bibliography_numbering_matches` (line 338) already checks `lvlText` for idempotency.

## Common Pitfalls

### Pitfall 1: `_BIBLIOGRAPHY_NUM_IDS` cross-document leak
**What goes wrong:** Run `audit-docx` on doc A then doc B in the same process. Doc B's `_get_bibliography_num_id` finds a stale key in `_BIBLIOGRAPHY_NUM_IDS` because `id(numbering_root)` happens to collide (CPython reuses freed IDs). Allocator returns a numId that doesn't exist in doc B's numbering.xml → broken numbering reference → audit reports "numbering" was applied but Word renders nothing.
**Why it happens:** Module-level dict keyed by `id()` of a numbering_part element. The element lives only as long as the python-docx Document holds a reference; once GCed, its `id()` is free for reuse.
**How to avoid:** D-07 seed-from-numbering.xml-on-first-call also acts as the cure: each new doc re-discovers existing num_ids, so even a stale dict entry is overwritten with the correct value. Plus switch key to `id(paragraph.part.document.part)` (lives the entire document lifetime in `paragraph._parent._part`).
**Warning signs:** Test that audits two different DOCXs in the same `pytest` run reports correct numId for one and a garbage numId for the other.

### Pitfall 2: Word counter reset across subsections (D-05 implementation)
**What goes wrong:** Implementer creates one `w:num` per document (not per subsection), expects Word to reset `ilvl=1` counter when `ilvl=0` advances. Reality: in a `multilevel` abstract, lvl-1 resets when lvl-0 advances ONLY if a lvl-0 paragraph appears. Bibliography subsection headings are Heading 1/2 paragraphs — NOT part of the numbering. So lvl-1 counter never resets → all entries get sequential `1.1, 1.2, 1.3, ..., 1.20` across all subsections.
**Why it happens:** No level-0 paragraph between subsections means no counter advance.
**How to avoid:** ONE `w:num` per subsection (each with a `<w:lvlOverride w:ilvl="0"><w:startOverride w:val="N"/></w:lvlOverride>` setting the section_index AND `<w:lvlOverride w:ilvl="1"><w:startOverride w:val="1"/></w:lvlOverride>` resetting the entry counter). All `w:num`s point at the same `abstractNumId`.
**Warning signs:** Bibliography_minimal.docx integration test asserts entries from subsection 2 render as `2.1, 2.2, 2.3` not `1.4, 1.5, 1.6`.

### Pitfall 3: SVM gets the title right; D-01 override is a no-op for those cases
**What goes wrong:** The override path runs but doesn't change anything for documents where SVM already returned `bibliography_title`. The test author writes an assertion that "override fires" but the SVM-correct path is indistinguishable.
**Why it happens:** D-01 is a defense, not a transformation, when SVM is correct.
**How to avoid:** Test specifically with predicted_label=`body_text` for a title-matching text — assert postprocessed_label flips to `bibliography_title`. Phase 1 `test_fix_mode_preserves_tabbed_bibliography_entries_from_predictions_csv` (line 1045) is the existing precedent — its CSV has `predicted_label="body_text", postprocessed_label="bibliography_title"` for the title row. Mirror this asymmetry in the new unit test.

### Pitfall 4: `BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE` removal breaks `infer_regression_label`
**What goes wrong:** D-04 says "drop legacy `BIBLIOGRAPHY_SUBHEADING_RE`" — but `src/evaluation/format_regression_audit.py:50` also imports `BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE` to seed `predicted_label = title_section` for the regression baseline. Delete the regex and the regression label inference breaks → positive corpus regression `changed=0` might still pass (bibliography sections are absent in 1/4/58/59 positive examples), but the negative corpus `after_diff_rate` flips because heading detection in bibliography subsections returns to body_text.
**Why it happens:** Cross-module reuse of regex.
**How to avoid:** Keep the regex constant; just move the gating logic in postprocess from "regex match" to "position + style". The regex stays as a fallback (per CONTEXT.md Claude's Discretion: "whether D-04 fallback regex is kept as a Phase 5 hook or removed entirely — researcher decides based on negative corpus inspection"). **Researcher decision: KEEP the regex** because `format_regression_audit.infer_regression_label` is a synthetic-prediction harness that bypasses postprocess and needs SOME way to label bibliography subsections without the trained SVM. The regex is the cheapest synthetic signal.

### Pitfall 5: Profile-driven thresholds + Phase 1 contract incompatibility
**What goes wrong:** `assess_list_auto_fix_safety` (line 550) consumes `MAX_FALLBACK_LIST_*` directly. Convert to profile lookup → every caller (especially `is_list_like_paragraph` at line 595) needs the profile too. `apply_rules_to_paragraph` signature changes → every existing test breaks.
**Why it happens:** Module-level constants don't have call sites; profile-driven values do.
**How to avoid:** Thread the profile as a NEW keyword argument with a default (`profile: dict | None = None`). When `None`, use the hard-coded defaults (40/300). When provided, read from `profile["list_detection"]["max_fallback_words"]`. Existing tests that don't pass profile keep their current behavior. New tests pass a profile to verify override. **This pattern matches Phase 1's `default_font_name` parameter** at line 777.

## Code Examples

### Example A: Postprocess D-01 unconditional override (NEW first pass)
```python
# Source: NEW pre-pass to add at src/postprocess/postprocess_rules.py around line 128
# (BEFORE the body_text/list_item rewrite pass at line 130)
for position in range(len(labels)):
    if _is_bibliography_title(texts[position]):
        labels[position] = "bibliography_title"
```

### Example B: D-04 position-based subsection detection (REWRITE of lines 160-181)
```python
# Source: REPLACE the existing "in_bibliography" pass at postprocess_rules.py:160-181
from src.rules.style_signatures import classify_style  # NEW import

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

    # D-04: detect subsection by position + Heading 1 style first.
    # Fallback: legacy text regex for synthetic-prediction harness compatibility.
    style_class = _row_style_class(row)  # NEW helper: classify from row.style string
    is_subsection_heading = (
        style_class == "heading"
        or _is_bibliography_subheading(text)  # legacy fallback
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

Note: `_row_style_class(row)` is a row-style-string classifier (not a paragraph classifier) because postprocess works on the predictions DataFrame, not on Paragraph objects. Implementation: apply `HEADING_STYLE_RE / TOC_STYLE_RE / CAPTION_STYLE_RE / LIST_STYLE_RE` (from `src/rules/style_signatures.py`) to `row.get("style")` string. Order same as `classify_style`.

### Example C: D-05 2-level abstract emission
```python
# Source: NEW function in src/rules/rule_engine.py replacing _create_section_abstract_num_id
def _create_bibliography_multilevel_abstract(numbering_root) -> str:
    abstract_num_id = _next_abstract_num_id(numbering_root)
    abstract_num = OxmlElement("w:abstractNum")
    abstract_num.set(qn("w:abstractNumId"), str(abstract_num_id))

    multi_level_type = OxmlElement("w:multiLevelType")
    multi_level_type.set(qn("w:val"), "multilevel")
    abstract_num.append(multi_level_type)

    # Level 0 — section counter (decimal, lvlText = "%1.")
    lvl0 = OxmlElement("w:lvl"); lvl0.set(qn("w:ilvl"), "0")
    s0 = OxmlElement("w:start"); s0.set(qn("w:val"), "1"); lvl0.append(s0)
    f0 = OxmlElement("w:numFmt"); f0.set(qn("w:val"), "decimal"); lvl0.append(f0)
    t0 = OxmlElement("w:lvlText"); t0.set(qn("w:val"), "%1."); lvl0.append(t0)
    j0 = OxmlElement("w:lvlJc"); j0.set(qn("w:val"), "left"); lvl0.append(j0)
    abstract_num.append(lvl0)

    # Level 1 — entry counter (decimal, lvlText = "%1.%2.")
    lvl1 = OxmlElement("w:lvl"); lvl1.set(qn("w:ilvl"), "1")
    s1 = OxmlElement("w:start"); s1.set(qn("w:val"), "1"); lvl1.append(s1)
    f1 = OxmlElement("w:numFmt"); f1.set(qn("w:val"), "decimal"); lvl1.append(f1)
    t1 = OxmlElement("w:lvlText"); t1.set(qn("w:val"), "%1.%2."); lvl1.append(t1)
    j1 = OxmlElement("w:lvlJc"); j1.set(qn("w:val"), "left"); lvl1.append(j1)
    abstract_num.append(lvl1)

    numbering_root.append(abstract_num)
    return str(abstract_num_id)


def _create_bibliography_num_with_section_override(
    numbering_root, abstract_num_id: str, section_index: int
) -> int:
    """One w:num per subsection — lvlOverride sets the section counter start."""
    num_id = _next_num_id(numbering_root)
    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))
    abstract_ref = OxmlElement("w:abstractNumId")
    abstract_ref.set(qn("w:val"), abstract_num_id)
    num.append(abstract_ref)

    # Force level-0 counter to start at section_index
    ov0 = OxmlElement("w:lvlOverride"); ov0.set(qn("w:ilvl"), "0")
    so0 = OxmlElement("w:startOverride"); so0.set(qn("w:val"), str(section_index))
    ov0.append(so0); num.append(ov0)

    # Force level-1 counter to start at 1 (reset on subsection boundary)
    ov1 = OxmlElement("w:lvlOverride"); ov1.set(qn("w:ilvl"), "1")
    so1 = OxmlElement("w:startOverride"); so1.set(qn("w:val"), "1")
    ov1.append(so1); num.append(ov1)

    numbering_root.append(num)
    return num_id
```

When applying to a bibliography_item paragraph, set `<w:ilvl w:val="1"/>` (not "0" as today at `apply_bibliography_numbering:420`). Word resolves the level-1 lvlText against the per-num lvlOverride and renders `<section>.<entry>`.

### Example D: D-07 seeding from numbering.xml + stable key
```python
# Source: NEW in src/rules/rule_engine.py
_SEEDED_DOCS: set[int] = set()  # tracks document_cache_key per process

def _document_cache_key(paragraph) -> int:
    return id(paragraph.part.document.part)

def _seed_bibliography_num_ids_from_doc(paragraph) -> None:
    """First-call scan: walk all paragraphs in document order, group by
    bibliography_section_index (inferred from order — first heading=1, second=2, ...)
    so existing numIds populate _BIBLIOGRAPHY_NUM_IDS before allocator runs.

    Note: postprocess already supplies bibliography_section_index per row;
    this seeding only handles the case where Phase 2 audit runs on a document
    that was previously corrected by Phase 2 (idempotency).
    """
    numbering_root = paragraph.part.numbering_part.element
    doc_key = _document_cache_key(paragraph)
    body = paragraph.part.document.element.body

    section_index = 0
    in_bibliography = False
    for p_elem in body.iter(qn("w:p")):
        # ... walk paragraphs; detect title; track section_index; collect numId per section ...
        # First valid numId per section seeds _BIBLIOGRAPHY_NUM_IDS[(doc_key, section_index)]
        pass  # implementation deferred to plan-phase

def _get_bibliography_num_id(paragraph, section_index=None):
    doc_key = _document_cache_key(paragraph)
    if doc_key not in _SEEDED_DOCS:
        _seed_bibliography_num_ids_from_doc(paragraph)
        _SEEDED_DOCS.add(doc_key)

    root_key = (doc_key, section_index)
    if root_key in _BIBLIOGRAPHY_NUM_IDS:
        return _BIBLIOGRAPHY_NUM_IDS[root_key]

    # ... rest of allocator: create 2-level abstract once per doc, num per subsection ...
```

### Example E: D-09 ambiguous-list review routing
```python
# Source: ADD to src/rules/rule_engine.py:apply_rules_to_paragraph, RIGHT AFTER Phase 1 style guard at line 798
text = str(row_data.get("text", "") or paragraph.text or "").strip()
if (
    label == "body_text"
    and paragraph_style_class == "body"        # Phase 1 guard already passed
    and _paragraph_has_list_marker(text)        # NUMBERED_MARKER_RE or BULLET_MARKER_RE matches
    and not _paragraph_has_numbering(paragraph) # no Word numPr
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

### Example F: D-13 conditional bibliography format scalar application
```python
# Source: REWRITE src/rules/rule_engine.py:apply_bibliography_format (line 230)
def apply_bibliography_format(paragraph, config, section_index=None):
    applied = []

    # ALWAYS safe: style_name + numbering (per D-13)
    style_name = str(config.get("style_name", "List Number"))
    try:
        if paragraph.style is None or paragraph.style.name != style_name:
            paragraph.style = style_name
            applied.append("style_name")
    except Exception:
        pass

    applied.extend(apply_bibliography_numbering(paragraph, section_index))

    # PROFILE-DRIVEN: only apply if the profile carries the field
    profile_driven_fields = [
        "alignment",
        "first_line_indent_cm",
        "left_indent_cm",
        "line_spacing",
        "space_before_pt",
        "space_after_pt",
    ]
    for field in profile_driven_fields:
        if field not in config:
            continue  # D-13: profile didn't specify → don't rewrite inherited value
        applied.extend(apply_scalar_fix(
            paragraph=paragraph,
            parameter=field,
            expected_value=config[field],
            default_font_name="Times New Roman",
        ))
    return sorted(set(applied))
```

Note: current code (line 254-265) ALREADY iterates scalar_fields and ALREADY does `if field not in config: continue`. **No behavior change needed** for the conditional path — the change is only that `expected_value` in `formatting_rules_v1.json` for `bibliography_item_format` (line 119) is `{"style_name": "List Number", "first_line_indent_cm": -1.0, "left_indent_cm": 2.25}` — i.e., it carries `first_line_indent_cm` and `left_indent_cm`. Plan-phase decision: either (a) strip these from the rule's expected_value so paragraphs keep inherited values, or (b) keep them as the default but allow profile to override. CONTEXT.md D-13 says "if profile config has field → apply, else skip" — that maps to option (a) at the rule level + (b) at the profile level if profile contributes more.

## Runtime State Inventory

> This is a rename/refactor/migration phase only in the sense that `_BIBLIOGRAPHY_NUM_IDS` cache semantics change. Otherwise greenfield additions.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `_BIBLIOGRAPHY_NUM_IDS` module-level dict at `rule_engine.py:43` keyed by `(id(numbering_root), section_index)`. Cache state survives across documents in the same Python process. | Code edit: change key to `id(paragraph.part.document.part)`. Add `_SEEDED_DOCS` set for first-call seeding. No data migration — cache is process-local. |
| Live service config | None — no live services. | None — verified by inspecting `src/` (no DB/queue/cache config). |
| OS-registered state | None. | None. |
| Secrets/env vars | None added by Phase 2. | None. |
| Build artifacts | None — pure Python. | None. |

**Key takeaway:** the only "runtime state" is the in-process numId cache. D-07 fixes both the idempotency and the cross-document-leak symptoms with one change.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python-docx | All numbering ops | ✓ | already pinned in project | — |
| pandas | postprocess + regression audit | ✓ | already pinned | — |
| pytest | Tests | ✓ | already pinned | — |
| `positive_examples/{1,4,58,59}.docx` | Phase 1 baseline regression gate | ✓ | filesystem | gate `pytest.skip` (line 17 of test_positive_docx_regression.py) |
| `negative_examples/*.docx` | D-14 integration fixture + D-15 mean-diff-rate gate | ✓ (17 files all carry biblio title) | filesystem | none — D-14 requires real DOCX |
| `tests/fixtures/style_guard_minimal.docx` | Phase 1 pattern reference | ✓ | committed binary | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (Phase 1 baseline 53 tests) |
| Config file | none — pytest discovery from `tests/` directory |
| Quick run command | `pytest tests/test_postprocess_rules.py tests/test_rule_engine.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-list-conservative-handling (D-01) | `BIBLIOGRAPHY_TITLE_RE` match → label=bibliography_title regardless of SVM | unit | `pytest tests/test_postprocess_rules.py::test_bibliography_title_overrides_svm_body_text -x` | ❌ Wave 0 |
| REQ-list-conservative-handling (D-04) | Heading 1 style inside bibliography context → bibliography_section_index advances | unit | `pytest tests/test_postprocess_rules.py::test_subsection_detected_by_heading_style_not_regex -x` | ❌ Wave 0 |
| REQ-list-conservative-handling (D-05) | 2 bibliography subsections → entries render `1.1, 1.2, 2.1` (lvlText `%1.%2.` + lvlOverride) | unit | `pytest tests/test_rule_engine.py::test_bibliography_multilevel_renders_section_dot_entry -x` | ❌ Wave 0 |
| REQ-list-conservative-handling (D-06) | Mixed numIds in one subsection → first-valid wins; others coerced; `applied_fixes` includes `numbering:coerced_to_numId=<N>` | unit | `pytest tests/test_rule_engine.py::test_bibliography_subsection_coerces_to_first_valid_numId -x` | ❌ Wave 0 |
| REQ-list-conservative-handling (D-07) | Second `apply-safe` run on already-corrected doc → no further changes (idempotent) | unit | `pytest tests/test_rule_engine.py::test_bibliography_idempotent_on_rerun -x` | ❌ Wave 0 |
| REQ-list-conservative-handling (D-09) | Marker + no numId → review, explanation `ambiguous_list_marker_no_numId`, no fixes applied | unit | `pytest tests/test_rule_engine.py::test_ambiguous_list_marker_no_numId_routes_to_review -x` | ❌ Wave 0 |
| REQ-list-conservative-handling (D-10) | Long body_text without marker without numId → stays body_text (Phase 1 style guard suffices) | unit | `pytest tests/test_rule_engine.py::test_long_body_text_without_marker_stays_body_text -x` | ❌ Wave 0 |
| REQ-list-conservative-handling (D-11) | Profile thresholds 40/300 read via `profile_loader`; code constants gone | unit | `pytest tests/test_profile_loader.py::test_list_detection_thresholds_from_profile -x` | ❌ Wave 0 |
| REQ-list-conservative-handling (D-13) | `apply_bibliography_format` doesn't touch alignment when profile omits field | unit | `pytest tests/test_rule_engine.py::test_bibliography_format_skips_alignment_when_profile_omits -x` | ❌ Wave 0 |
| REQ-list-conservative-handling (D-14 hand-crafted) | `bibliography_minimal.docx` → after `--apply-safe`, all entries in subsection share one numId | integration | `pytest tests/test_rule_engine.py::test_bibliography_minimal_docx_single_numId_per_subsection -x` | ❌ Wave 0 |
| REQ-list-conservative-handling (D-14 negative integration) | Real `negative_examples/4_formatted_*.docx` → bibliography entries share numId, `applied_fixes` includes `numbering` | integration | `pytest tests/test_bibliography_negative_integration.py::test_negative_4_bibliography_single_numId -x` | ❌ Wave 0 |
| ROADMAP Success #4 (positive corpus) | `audit-docx --apply-safe` on `positive_examples/{1,4,58,59}.docx` keeps `changed=0` | integration | `pytest tests/test_positive_docx_regression.py -x` | ✅ exists |
| ROADMAP Success #4 (negative regression) | `audit_negative_directory` mean `after_diff_rate ≤ 0.4781` | script-driven | `python -c "from src.evaluation.format_regression_audit import audit_negative_directory, audits_to_frame; ..."` | ❌ Wave 0 (script ad-hoc per Phase 1; recommend committed test_negative_corpus_diff_rate.py) |

### Sampling Rate
- **Per task commit:** `pytest tests/test_postprocess_rules.py tests/test_rule_engine.py -x` (~ 5-10s)
- **Per wave merge:** `pytest tests/ -x` (full suite, ~ 30s with current 53 tests + ~10 new Phase 2 tests)
- **Phase gate:** Full suite green + manual `audit_negative_directory` invocation confirms mean `after_diff_rate ≤ 0.4781`

### Wave 0 Gaps

- [ ] `tests/fixtures/_build_bibliography_minimal.py` + `tests/fixtures/bibliography_minimal.docx` — hand-crafted: 1 title + 2 Heading 2 subsections + 3 entries each, one subsection with mixed numIds
- [ ] `tests/test_bibliography_negative_integration.py` — integration with one real negative_examples DOCX (recommend `4_formatted_20260413_185420.docx` — has explicit Heading 2 subsections "ТЕОРЕТИЧЕСКАЯ ЧАСТЬ" / "ПРАКТИЧЕСКАЯ ЧАСТЬ" and existing numId=16 → straightforward coercion test)
- [ ] `tests/test_postprocess_rules.py` extensions — D-01 unconditional override + D-04 position+heading detection
- [ ] `tests/test_rule_engine.py` extensions — D-05/06/07/09/13 unit tests
- [ ] `tests/test_profile_loader.py` (or extend existing) — D-11 schema fields readable + validator accepts new optional fields
- [ ] Test framework install: none — pytest already in use
- [ ] (Optional) `tests/test_negative_corpus_diff_rate.py` — wraps the Phase 1 manual baseline as an automated regression test, gated to `≤ 0.4781`. Recommend INCLUDE in Phase 2 (Phase 4 hardens it anyway, but having it automated now prevents Phase 2 from silently regressing.)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (local CLI tool, no auth) |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | DOCX is user-supplied; python-docx handles XXE protection internally. Profile JSON validated via `profile_validator.assert_valid_profile`. |
| V6 Cryptography | no | — |

### Known Threat Patterns for {python-docx + pandas + pytest stack}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed DOCX → python-docx raises | DoS | Wrap `audit_or_format_docx` calls in try/except — already done in `inplace_formatter.py` |
| Profile JSON with arbitrary regex (numbering_pattern) → ReDoS | DoS | Profile JSON is trusted (ships in repo); user-supplied profiles are Phase 5 territory. Phase 2 scope: schema-validate but don't execute user regexes at this phase. |
| User-supplied `--profile <path>` path traversal | Tampering | Phase 5 territory; not in Phase 2 scope (D-12 explicit). |
| Bibliography content leaking PII in audit logs | Information disclosure | Already enforced via Phase 1 REQ-pipeline-logging — log filenames + technical context only, not paragraph text content. |

Phase 2 introduces no new security surface beyond Phase 1.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-level numbering with section index baked into `lvlText` as `f"{section_index}.%1"` | 2-level `multilevel` abstract with `lvlText="%1.%2."` + per-subsection `w:num` with `lvlOverride` | Phase 2 (this work) | Word renders `<section>.<entry>` from counters; supports proper hierarchy; idempotent reruns work correctly because the lvlText pattern is a fixed string, not a per-section template. |
| `_BIBLIOGRAPHY_NUM_IDS` keyed by `id(numbering_root)` | Keyed by `id(paragraph.part.document.part)` + seed-from-numbering.xml | Phase 2 | Eliminates cross-document leak when CPython reuses `id()` values. |
| `BIBLIOGRAPHY_SUBHEADING_RE` text regex as primary subsection detector | `classify_style(paragraph) == "heading"` + position-in-bibliography-context as primary; regex as fallback | Phase 2 | Detection works for ALL Heading-styled subsections regardless of text content (`ИССЛЕДОВАТЕЛЬСКИЙ РАЗДЕЛ` etc.); text regex stays only as a synthetic-prediction-harness fallback. |
| Hard-coded `MAX_FALLBACK_LIST_WORDS = 40` etc. | Profile-driven `list_detection.max_fallback_words` | Phase 2 | Different normcontrols can carry different thresholds (Phase 5 prerequisite). |

**Deprecated/outdated:**
- `_create_section_abstract_num_id` (singleLevel, literal-section-in-lvlText): supplanted by `_create_bibliography_multilevel_abstract` + `_create_bibliography_num_with_section_override`. **Leave the old function in place during Phase 2** for safety — only the bibliography path stops calling it. (Other callers may exist for non-bibliography numbering — researcher checked: no callers other than `_get_bibliography_num_id` at line 374. Function CAN be removed in Phase 2 final cleanup task.)

## Assumptions Log

> All claims tagged `[ASSUMED]` in this research.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `lvlOverride/startOverride` on each `w:num` is the correct OOXML primitive to reset/initialize per-subsection counters | Example C, Pitfall 2 | If Word ignores `startOverride` when no level-0 paragraph exists, level-1 counter won't reset. Mitigation: integration test on bibliography_minimal.docx with 2 subsections asserts `2.1, 2.2` (not `1.4, 1.5`). [CITED: ecma-376 §17.9.16 — c-rex.net example shows abstractNum without lvlOverride; lvlOverride lives in w:num and IS the canonical reset mechanism per ECMA-376 §17.9.5] |
| A2 | `id(paragraph.part.document.part)` is stable for the document lifetime | Example D, Pitfall 1 | If python-docx ever swaps the `document.part` object during a session, the key changes mid-session and seeding re-runs unnecessarily. Mitigation: low risk — `Document.part` is set in `__init__` and never reassigned (verified by reading python-docx source). [ASSUMED — python-docx source not re-verified this session; cite Phase 1 cohesion-audit Plan 04 which already reasons about `paragraph._parent._part`] |
| A3 | All 17 negative_examples carry a `BIBLIOGRAPHY_TITLE_RE` match | Environment Availability, Pitfall 3 | If only some do, D-14 integration fixture must select carefully. Mitigation: VERIFIED via `python3 -c "from pathlib import Path; from docx import Document; ..."` (ran this session — see Step 2.6 output, all 17 match). [VERIFIED: this session, see Bash output above] |
| A4 | Phase 1's 0.4781 baseline is NOT enforced via an automated test | Pitfall 5, Validation Architecture | If there's a hidden enforcement, Phase 2 plan duplicates work. Mitigation: VERIFIED via `grep -rn "0.4781" tests/ src/` — no matches in src or tests (only `after_diff_rate` rounded to 6 decimals in format_regression_audit.py). The 0.4737 result was a manual `audit_negative_directory` invocation in Plan 03 SUMMARY. Recommend Phase 2 add this as an automated test (Wave 0 optional). [VERIFIED: this session] |
| A5 | python-docx `Paragraph.part.numbering_part.element` returns the `<w:numbering>` root unchanged across reads | All numbering examples | If python-docx mutates it lazily, our scan-on-first-call could see different children than the allocator writes. Mitigation: existing code (line 151, 168, 191) treats this as stable across reads. [ASSUMED based on existing rule_engine.py patterns; not re-verified against python-docx source this session] |
| A6 | `bibliography_section_index` in row_data from CSV survives pandas `Series.itertuples` round-trip as int (not float NaN) | Profile passthrough, Example C | If pandas converts to NaN-bearing float column, `_safe_int` at line 391 returns None — section_index is lost. Mitigation: VERIFIED — existing `test_bibliography_item_numbering_uses_section_prefix` (line 584) passes section_index=2 via dict-style row_data and works. CSV round-trip uses pandas which preserves int-or-None. [VERIFIED: existing test confirms] |

## Open Questions for Planner (RESOLVED)

1. **Should D-15 negative-corpus mean diff-rate gate become an automated pytest in Phase 2 or stay manual until Phase 4?**
   - What we know: Phase 1 left it manual (Plan 03 SUMMARY: "Numbers were obtained via direct `audit_negative_directory(...)` call"). No `tests/test_negative_corpus_diff_rate.py` exists.
   - What's unclear: Phase 4 explicitly owns `audit-regression` CLI gate (REQ-audit-regression-cli). Inserting it earlier (Phase 2) duplicates work, but skipping it leaves Phase 2 with no automated regression detection for negative corpus.
   - Recommendation → RESOLVED: ADD a Phase 2 pytest test that calls `audit_negative_directory` directly with `limit=4` (1, 4, 58, 59 negative variants — same files as positive baseline) and asserts mean `after_diff_rate ≤ 0.4781`. Full 17-file gate stays manual until Phase 4. This is faster (4 docs vs 17) and prevents Phase 2 from silently breaking the gate. *Adopted by Plan 01 (Wave 0 builds `tests/test_negative_corpus_diff_rate.py`) and Plan 04 Task 3 (verifies gate stays GREEN).*

2. **For D-04, should `BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE` and `BIBLIOGRAPHY_SUBHEADING_RE` be kept as a fallback or removed?**
   - What we know: `src/evaluation/format_regression_audit.py:50` imports `BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE` to seed synthetic `title_section` labels. Removing the regex would break the regression baseline.
   - What's unclear: CONTEXT.md Claude's Discretion line punts to researcher.
   - Recommendation (RESOLVED): **KEEP both regexes.** Primary subsection detection is `classify_style == "heading"`. Fallback is the regex, used when the row's style string doesn't match HEADING_STYLE_RE (e.g., synthetic predictions in `format_regression_audit.infer_regression_label`). This preserves Phase 1 dependencies without compromising D-04's intent (position+style primary). *Adopted by Plan 02 (postprocess D-04 implementation keeps both regexes as fallback).*

3. **D-06 "valid numId" definition — does it have to map to an abstractNum with the new 2-level structure, or any abstractNum?**
   - What we know: Phase 1 already has `_num_id_exists` (line 148) and `paragraph_numbering_reference_is_valid` (line 156) checking that numId resolves to an existing `w:num` in numbering.xml. Today's `bibliography_numbering_matches` (line 338) checks the EXPECTED lvlText `f"{section_index}.%1"`.
   - What's unclear: After D-05, "valid" for coercion purposes — does it mean "any numId pointing at a real abstractNum" OR "a numId pointing at the new 2-level abstract with the right lvlOverride"?
   - Recommendation → RESOLVED: **"Valid"** = exists in numbering.xml AND its abstractNum has multiLevelType=multilevel AND level-1 lvlText=="%1.%2.". Lower bar fails idempotency (would coerce to a legacy singleLevel numId which then renders wrong). *Adopted by Plan 03 — `_bibliography_valid_numId` enforces all three conditions; legacy singleLevel numIds in `bibliography_minimal.docx` entry 2 deliberately fail criterion (2) so D-06 coerces away from them.*

4. **D-13 — do existing rule expected_values in `formatting_rules_v1.json:118-130` (carrying `first_line_indent_cm: -1.0, left_indent_cm: 2.25`) stay, or get stripped?**
   - What we know: D-13 says "if profile has field → apply, else skip". Current rule definition carries `first_line_indent_cm` and `left_indent_cm` in its expected_value — these effectively force application regardless of profile.
   - What's unclear: Should rule expected_value get pruned to `{"style_name": "List Number"}` so the profile becomes the sole source of scalar truth?
   - Recommendation → RESOLVED: **Strip the scalars from `formatting_rules_v1.json:118-130` expected_value**, leaving only `style_name`. Profile JSON `labels.bibliography_item.style_profile.*` becomes the authoritative source. This realizes D-13's "Phase 1 style_guard_block: philosophy of no silent rewrites of inherited values" at the rule schema level. *Adopted by Plan 04 Task 2 — JSON stripped; profile-level scalar addition is sub-step 2e remediation path 1 if regression appears.*

5. **Does the new 2-level abstract need a `<w:nsid>` element to be Word-compatible?**
   - What we know: ECMA-376 sample at c-rex.net shows `<w:nsid w:val="FFFFFF7F"/>` as the first child. Existing `_create_section_abstract_num_id` (line 303-335) DOES NOT emit nsid; Word still opens documents created by Phase 1 rule engine without complaint.
   - Recommendation → RESOLVED: **Skip nsid for parity with existing code.** Plan-phase smoke-test on a real DOCX confirms. *Adopted by Plan 03 — `_create_bibliography_multilevel_abstract` emits no `<w:nsid>`; matches the legacy emitter idiom.*
## Project Constraints (from CLAUDE.md)

The following CLAUDE.md directives are load-bearing for Phase 2 planning. Treat with same authority as locked CONTEXT.md decisions.

- **"Для автонумерации DOCX применяй Word numbering (`numPr`), а не только стиль абзаца"** — D-05 implementation MUST set `numPr` on each bibliography_item paragraph; setting only `paragraph.style = "List Number"` is insufficient.
- **"Для многораздельной библиографии передавай номер раздела через postprocess metadata до rule engine"** — `bibliography_section_index` MUST be stamped in postprocess (already does this at line 178/181); rule_engine reads from `row_data`, never re-derives.
- **"Не применяй обычные heading scalar autofix к библиографическим section headings"** — already enforced at `rule_engine.py:722` (when `label in {"title_section", "title_subsection"}` AND `bibliography_section_index is not None`, scalar autofix returns review). Phase 2 must preserve this guard.
- **"Не автоисправляй generic `list_type=list` без маркера и Word numbering"** — `assess_list_auto_fix_safety` (line 566-567) already enforces. Phase 2 D-09 strengthens for `body_text` label specifically.
- **"Восстанавливай отсутствующий или сломанный `numPr` у списка, не меняя уже принятую раскладку абзаца"** — D-06 first-valid-wins coercion must preserve paragraph format (left_indent_cm, first_line_indent_cm) — only touch numPr.
- **"Перед фиксацией нумерационных/length/regex constants в коде проверь, не должны ли они быть profile-driven"** — D-11 directly maps. `MAX_FALLBACK_LIST_WORDS = 40` and `MAX_FALLBACK_LIST_CHARS = 300` MUST move to profile.
- **"Если есть более простой подход — скажи; отказывайся от него только при обосновании."** — A simpler approach for D-05 would be to keep singleLevel and bake section.entry directly into lvlText (current pattern). REJECTED because: (a) section number must be a Word counter for proper continuation across resets, (b) the existing `bibliography_numbering_matches` already special-cases `f"{section_index}.%1"` so the legacy approach has its own technical-debt cost.
- **"Не «улучшай» соседний код, форматирование и комментарии; следуй существующему стилю."** — Phase 2 leaves `_create_section_abstract_num_id` in place even though the new function supplants it. Cleanup is a separate task or deferred.
- **"Каждая изменённая строка должна напрямую отслеживаться до запроса пользователя."** — Every change in Phase 2 traces to a D-NN decision in CONTEXT.md.

## Sources

### Primary (HIGH confidence)
- **Source code (verified this session):**
  - `src/postprocess/postprocess_rules.py:12-29` — `BIBLIOGRAPHY_TITLE_RE` etc.
  - `src/postprocess/postprocess_rules.py:110-206` — `apply_postprocess_rules` (label rewriting, bibliography_section_index stamping)
  - `src/rules/rule_engine.py:26-43` — constants `BIBLIOGRAPHY_SUBHEADING_RE`, `NUMBERED_MARKER_RE`, `BULLET_MARKER_RE`, `MAX_FALLBACK_LIST_WORDS`, `MAX_FALLBACK_LIST_CHARS`, `_BIBLIOGRAPHY_NUM_IDS`
  - `src/rules/rule_engine.py:230-265` — `apply_bibliography_format` (D-13 scope)
  - `src/rules/rule_engine.py:303-335` — `_create_section_abstract_num_id` (legacy singleLevel)
  - `src/rules/rule_engine.py:338-364` — `bibliography_numbering_matches` (checks `lvlText`)
  - `src/rules/rule_engine.py:367-388` — `_get_bibliography_num_id` (allocator + cache)
  - `src/rules/rule_engine.py:409-429` — `apply_bibliography_numbering` (sets `numPr` on paragraph; currently hardcoded `ilvl=0`)
  - `src/rules/rule_engine.py:609-663` — `_apply_bibliography_rules` (dispatch)
  - `src/rules/rule_engine.py:771-798` — Phase 1 style guard inside `apply_rules_to_paragraph`
  - `src/rules/style_signatures.py` — `classify_style` + 4 regexes
  - `src/rules/profile_loader.py` — `load_profile`, `_resolve_base_profiles`, `get_label_config`
  - `src/rules/profile_validator.py` — `REQUIRED_TOP_LEVEL_KEYS`, `REQUIRED_STYLE_KEYS`, `validate_profile`
  - `src/rules/profiles/gost_7_32_2017.json` — default profile structure
  - `src/rules/formatting_rules_v1.json` — `bibliography_item_format` rule structure (line 118-130)
  - `src/evaluation/format_regression_audit.py` — `audit_negative_directory`, `audits_to_frame`, `after_diff_rate` column
  - `src/generate/inplace_formatter.py:340-470` — `audit_or_format_docx` row_data construction + `apply_rules_to_paragraph` call site
  - `src/io/block_extractor.py` — confirms `list_type`/`list_level` populated but NOT `bibliography_section_index` (that's postprocess-only)
  - `tests/fixtures/_build_style_guard_minimal.py` — Phase 1 fixture builder pattern
  - `tests/test_positive_docx_regression.py` — positive corpus gate
  - `tests/test_rule_engine.py:355-700` — existing bibliography tests
- **`.planning/phases/01-engine-guardrails-cohesion-audit/01-VERIFICATION.md`** — Phase 1 shipped 53 tests; negative diff-rate 0.4737 ≤ 0.4781 (manual)
- **`.planning/phases/02-bibliography-list-semantics/02-CONTEXT.md`** — locked decisions D-01..D-15

### Secondary (MEDIUM confidence)
- **ECMA-376 OOXML reference** (via [c-rex.net abstractNum sample](https://c-rex.net/samples/ooxml/e1/Part4/OOXML_P4_DOCX_abstractNum_topic_ID0EJGJU.html)) — canonical XML for `w:abstractNum` + `multiLevelType="multilevel"` + 2-level lvlText. Sample example shows exactly the pattern Phase 2 needs.
- **[multiLevelType reference](https://c-rex.net/samples/ooxml/e1/Part4/OOXML_P4_DOCX_ST_MultiLevelType_topic_ID0E2FB3.html)** — enum values singleLevel / multilevel / hybridMultilevel.
- **[python-docx Numbering Part docs](https://python-docx.readthedocs.io/en/latest/dev/analysis/features/numbering.html)** — confirms no high-level API for multi-level numbering; direct OOXML manipulation is the way.
- **Negative_examples scan** (this session) — 17/17 DOCX files match `BIBLIOGRAPHY_TITLE_RE`; document 4_formatted shows Heading 2 subsection + numId=16 → ideal D-14 fixture.

### Tertiary (LOW confidence)
- ECMA-376 §17.9.5 `lvlOverride` semantics (Pitfall 2 / Example C / Assumption A1) — believed correct via WebSearch + c-rex sample, but not re-verified against an authoritative spec snippet this session. Plan-phase verification: write a 1-paragraph integration test that round-trips a 2-section bibliography and asserts level-0 counter resets correctly.

## Files to Read Before Planning

Consolidated reading list for `gsd-planner`:

1. **CONTEXT (decisions):**
   - `.planning/phases/02-bibliography-list-semantics/02-CONTEXT.md` — D-01..D-15
2. **Project-level:**
   - `.planning/REQUIREMENTS.md` — REQ-list-conservative-handling
   - `.planning/ROADMAP.md` Phase 2 section (success criteria 1-4)
   - `./CLAUDE.md` — project rules cited in "Project Constraints"
3. **Phase 1 carry-forward:**
   - `.planning/phases/01-engine-guardrails-cohesion-audit/01-CONTEXT.md`
   - `.planning/phases/01-engine-guardrails-cohesion-audit/01-VERIFICATION.md`
   - `src/rules/style_signatures.py` (reused for `classify_style`)
4. **Code-to-modify:**
   - `src/postprocess/postprocess_rules.py` (D-01, D-04)
   - `src/rules/rule_engine.py` (D-05, D-06, D-07, D-09, D-11, D-13)
   - `src/rules/profile_loader.py` (D-11)
   - `src/rules/profile_validator.py` (D-03, D-11)
   - `src/rules/profiles/gost_7_32_2017.json` (D-03, D-11)
   - `src/rules/formatting_rules_v1.json` (D-13 — consider scalar strip from `bibliography_item_format`)
5. **Code-to-read-but-not-modify (consumers of changed contracts):**
   - `src/generate/inplace_formatter.py:340-470` (rule_engine caller; row_data construction)
   - `src/evaluation/format_regression_audit.py` (regression gate consumer; `infer_regression_label` uses `BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE`)
6. **Test patterns:**
   - `tests/fixtures/_build_style_guard_minimal.py` (mirror pattern)
   - `tests/test_positive_docx_regression.py` (gate pattern)
   - `tests/test_rule_engine.py:355-700, 1045-1122, 1124-1370` (bibliography + style-guard test patterns)
   - `tests/test_postprocess_rules.py` (existing bibliography postprocess tests)
7. **Test corpus:**
   - `negative_examples/4_formatted_20260413_185420.docx` — recommended D-14 integration fixture (has Heading 2 subsections + numId=16)
   - Alternative: `negative_examples/3_formatted_20260413_194927.docx` — has mixed numIds (some `None`, some `numId=1`) → exercises D-06 coercion path
   - `positive_examples/{1,4,58,59}.docx` — Phase 1 baseline (no biblio entries)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; verified python-docx is sufficient.
- Architecture / 2-level numbering: HIGH for XML structure (ECMA-376 sample matches need exactly); MEDIUM-HIGH for `lvlOverride` semantics (cited from spec, but plan should validate with integration test).
- Pitfalls: HIGH — `_BIBLIOGRAPHY_NUM_IDS` leak verified by code inspection (no `.clear()` calls); cross-module `BIBLIOGRAPHY_NUMBERED_SUBHEADING_RE` dependency verified by grep.
- Profile schema: HIGH — `profile_validator.py` is short, well-structured; D-11 fields slot in cleanly as optional.
- Test fixtures: HIGH — Phase 1 pattern (`_build_style_guard_minimal.py`) directly applicable.

**Research date:** 2026-05-12
**Valid until:** 2026-06-12 (30 days) — Phase 2 is bounded by current python-docx version + repository state; no fast-moving external dependencies.

## RESEARCH COMPLETE
