# Phase 2: Bibliography & list semantics - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-12
**Phase:** 02-bibliography-list-semantics
**Areas discussed:** Bib title override strictness, Single-numId scope key, Ambiguous-list routing, Bib autofix scope + tests

---

## Bibliography title override strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Force `bibliography_title` always | Deterministic override on regex match, no confidence threshold | ✓ |
| Override only when SVM confidence < threshold | Override iff `confidence < 0.7` | |
| Override + log as `manual_review_required` | Apply override but emit explanation about SVM disagreement | |

**User's choice (Q1):** Force `bibliography_title` always (Recommended)
**Notes:** Matches ROADMAP success criterion 1 wording exactly.

| Option | Description | Selected |
|--------|-------------|----------|
| Keep current 3 phrases | `список использованных/используемых источников`, `библиографический список`, `литература` | ✓ |
| Add EN + numbered prefix tolerance | `references`, `bibliography`, optional `\d+` prefix | |
| Add fuzzy SPISOK + (источники\|литература) | Loosen middle word | |

**User's choice (Q2):** Keep current 3 phrases (Recommended)

---

## Single-numId scope key

| Option | Description | Selected |
|--------|-------------|----------|
| Default per-section + hook для Phase 5 | Preserve current `(id(num_root), section_index)` key; add `numbering.bibliography.scope` profile field | ✓ |
| Только один numId на весь bibliography (literal ROADMAP) | One numId across all subsections | |
| Defer numbering policy entirely в Phase 5 | Phase 2 skips numbering, only detection | |

**User's choice (Q1):** Default per-section + hook для Phase 5 (Recommended)
**Notes:** "Нумерация источников зависит от нормоконтроля. В идеале необходимо извлекать необходимое требование из загруженного документа-нормоконтроля и формализовывать в правило" — Phase 5 ingestion will own real policy; Phase 2 ships the hook.

| Option | Description | Selected |
|--------|-------------|----------|
| Position + Heading 1 style | Inside bibliography context, any Heading 1 = subheading | ✓ |
| Position + numbered-prefix regex | `^\d+\s+\S+` regex within context | |
| Position + Heading 1 + любой число-префикс | Combination | |

**User's choice (Q2 — subsection detection):** Position + Heading 1 style (Recommended)
**Notes:** "изначально оба являются Heading 1 / после появления СПИСОК ИСТОЧНИКОВ как Heading 1 далее появятся разделы и под каждым из них пронумерованные источники в соответствии с номером раздела"

| Option | Description | Selected |
|--------|-------------|----------|
| Per-subsection numId, рендер 1.1/1.2 через Word hierarchy | 2-level Word numbering abstract | ✓ |
| Single numId + manual numbering text | Manual `1.`/`2.` in source text | |
| Defer hierarchical numbering до Phase 5 | Flat per-subsection now | |

**User's choice (Q3 — source numbering):** Per-subsection numId, рендер 1.1/1.2 через Word numbering hierarchy (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Coerce to first-valid в subsection | Scan, first valid wins, others coerced | ✓ |
| Route subsection в review | Mixed numIds → action=review | |
| Allocate свежий numId, coerce все | Always fresh numId | |

**User's choice (Q4 — mixed numIds):** Coerce to first-valid в subsection (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Скан numbering.xml на входе | Seed `_BIBLIOGRAPHY_NUM_IDS` at first allocator call per doc | ✓ |
| Persist cache в sidecar JSON | External JSON next to docx | |
| Не решаем, живем с клуттером | Status quo | |

**User's choice (Q5 — re-run state):** Скан numbering.xml на входе (Recommended)

---

## Ambiguous-list routing

| Option | Description | Selected |
|--------|-------------|----------|
| Текущие регексы, не меняем | `NUMBERED_MARKER_RE` + `BULLET_MARKER_RE` as-is | ✓ |
| Расширить hierarchical `1.1`, `1.1.1` | Match nested numbering in text | |

**User's choice (Q1 — marker definition):** Текущие регексы, не меняем (Recommended)
**Notes:** D-05 Word numbering hierarchy makes manual prefixes irrelevant.

| Option | Description | Selected |
|--------|-------------|----------|
| Route в review | `action=review`, `explanation: ambiguous_list_marker_no_numId` | ✓ |
| Auto-allocate numId (current) | Existing `apply_list_numbering` | |

**User's choice (Q2 — marker no numId):** Route в review (Recommended)
**Notes:** Matches ROADMAP success criterion 3 ("marker-only lists without numId become review").

| Option | Description | Selected |
|--------|-------------|----------|
| Оставляем body_text | No intervention | ✓ |
| Route в review | All short ambiguous → review | |
| Coerce в list_item если List Paragraph style | classify_style intervention | |

**User's choice (Q3 — short ambiguous):** Оставляем body_text (Recommended)
**Notes:** Mirror of ROADMAP success criterion 3 ("long text paragraphs without numId are not coerced").

| Option | Description | Selected |
|--------|-------------|----------|
| Schema в profile + default GOST профиль несёт 40/300 | Just thresholds in profile | ✓ |
| Schema в profile + ВСЕ Phase 2 пороги/regex туда же | Full profile-driven | |
| Только thresholds сейчас, regex отдельным phase | Numeric only | |

**User's choice (Q4 — thresholds):** Schema в profile + default GOST профиль несёт 40/300 (Recommended)
**Notes:** User clarified: "я хочу иметь возможность оформлять свою работу не только по встроенному госту, но и по загруженному нормоконтролю (локально из моего университета) / У каждого госта разные требования."

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 5 владеет UX, Phase 2 только schema | Just schema extension | ✓ |
| Phase 2 включает выбор локального profile | Add `--profile <path>` flag now | |

**User's choice (Q5 — profile UX):** Phase 5 владеет UX, Phase 2 только schema (Recommended)

---

## Bib autofix scope + tests

| Option | Description | Selected |
|--------|-------------|----------|
| style_name + numbering safe; остальные — profile-driven | Conservative, profile-conditional | ✓ |
| Только numbering safe, всё остальное — review | Strictest | |
| Все 8 филдов safe | Status quo | |

**User's choice (Q1 — safe fields):** style_name + numbering safe; остальные — profile-driven (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Оба: hand-crafted minimal + real corpus integration | Phase 1 fixture pattern + real DOCX | ✓ |
| Только hand-crafted | Unit only | |
| Только real corpus | Integration only | |

**User's choice (Q2 — fixtures):** Оба: hand-crafted minimal для юнитов + real corpus для integration (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 1 baseline (1/4/58/59) changed=0 + negative ≤ 0.4781 | Carried-forward Phase 1 gate | ✓ |
| Snapshot diff на все 59: количество changed не растёт | Track N_changed across full corpus | |
| Phase 1 baseline + 5 ручно выбранных файлов с bibliography | Hand-pick expansion | |

**User's choice (Q3 — regression gate):** Phase 1 baseline (1/4/58/59) changed=0 + negative ≤ 0.4781 (Recommended)
**Notes:** User clarified: "в каждом файле есть небольшие помарки / но в большинстве случаев они хорошо оформлены" — full-corpus changed=0 unrealistic; Phase 4 audit-regression CLI handles soft N_changed metric across all 59.

---

## Claude's Discretion

- Exact 2-level Word numbering abstract XML template (D-05 implementation).
- Internal naming of helpers (`_seed_bibliography_num_ids_from_doc`, `_collect_bibliography_subsections`).
- Exact profile schema layout under `numbering.bibliography.*` and `list_detection.*`.
- Test naming convention.
- Whether D-04 fallback regex stays as a Phase 5 hook or removed entirely (researcher decides).

## Deferred Ideas

- Profile selection UX (CLI + UI) → Phase 5/6
- `extract-methodical-profile` CLI → Phase 5
- Hierarchical text-marker support → out of scope
- `audit-regression` CLI on all 59 → Phase 4
- Heading signature extension → Phase 3
- DOCX writer custom styles → Phase 3
- UI changes → Phase 6
- EN-locale bibliography titles → indefinite
