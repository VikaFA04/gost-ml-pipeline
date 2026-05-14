# CONTRIBUTING

## Pre-PR проверка

Перед любым fix-track PR обязательно:

```bash
make regression-gate
```

Без GNU Make:

```bash
python3 -m src.main audit-regression \
  --positive-dir positive_examples \
  --negative-dir negative_examples \
  --limit 4
python3 -m pytest -q \
  tests/test_negative_corpus_diff_rate.py \
  tests/test_positive_docx_regression.py \
  tests/test_rules_quality_acceptance.py \
  tests/test_format_regression_audit.py
```

Гейт читает `tests/baselines/negative_corpus.json` — per-pair ceilings + aggregate mean. Любая регрессия на pinned subset (`3.docx` + worst-offenders) проваливает PR.

## Обновление baseline

Если изменение **намеренно** улучшает регрессионную метрику (например, fix-track PR закрывает гэп) или ослабляет ceiling по обоснованным причинам, baseline нужно перезаписать. Только через CLI с обязательным `--reason` — **без `--limit`, чтобы захватить весь pinned subset**:

```bash
python3 -m src.main audit-regression \
  --positive-dir positive_examples \
  --negative-dir negative_examples \
  --update-baseline tests/baselines/negative_corpus.json \
  --reason "FIX-XX: <human-readable rationale, >= 8 символов после strip>"
```

Правила (см. `.planning/PROJECT.md` D-004 — no silent rewrites; RESEARCH.md Probe 6 — минимальная длина `--reason`):

- `--reason` обязательно. CLI откажется работать, если `len(reason.strip()) < 8` (минимум 8 символов после strip; пустая, пробельная или 7-символьная строка отвергается).
- Commit message обязан повторять текст `--reason`.
- **`--update-baseline` НЕ должен использоваться вместе с `--limit`.** `--limit N` берёт первые N документов по лексикографическому порядку (`1.docx, 10.docx, 11.docx, ...`) — pinned subset (`3.docx` + worst-offenders) при этом частично выпадает (Pitfall 1). `write_per_pair_baseline` фильтрует frame по `_metadata.subset_filenames` ПЕРЕД записью, и если какая-то из subset-фамилий отсутствует в frame, помощник напечатает `WARNING: subset filenames [...] missing from frame ...`. Это сигнал перезапустить команду без `--limit`.
- Если baseline ослабляется (ceiling растёт), commit message должен ссылаться на ROADMAP success criterion и (если применимо) на Phase 4 D-05 branch decision artefact `.planning/phases/04-regression-gate/04-WAVE-A-3docx-rootcause.md`.
- Если ослабление ceiling требует пересмотра ROADMAP/REQUIREMENTS success criterion — амендмент успехового критерия идёт в ТОМ ЖЕ commit, что и baseline JSON (атомарно, без молчаливого обхода — Phase 4 D-05 + Pitfall 3).

## Безопасность

`--update-baseline <path>` принимает любой путь, который указал разработчик: CLI — dev-only утилита, не предназначенная для запуска с недоверенным входом (T-04-01, low severity). `--reason "<text>"` хранится как opaque строка через `json.dumps(..., ensure_ascii=False)` и не уходит в shell-out — никаких injection-векторов (T-04-02, low severity).

## Что покрывает гейт

- `tests/test_negative_corpus_diff_rate.py` — per-pair `after_diff_rate ≤ ceiling`, per-pair `field_mismatch_delta ≤ 0`, subset aggregate `mean ≤ 0.4781`.
- `tests/test_positive_docx_regression.py` — heading-style invariant на positive corpus (Phase 3 D-07).
- `tests/test_rules_quality_acceptance.py` — RuleRecord schema lint + runtime CSV-invariants smoke (REQ-rules-quality-acceptance).
- `tests/test_format_regression_audit.py` — `audits_to_frame` column contract + `audit_negative_directory` smoke (REQ-audit-regression-cli — ROADMAP Phase 4 SC-1).

Full corpus прогон (без `--limit`) — ручной, перед merge большого fix-track PR, и обязательный для `--update-baseline`.

## CI corpus fixture (Option D)

`tests/fixtures/corpus/` holds a minimal DOCX subset (3.docx, 4.docx, 45.docx positives + their formatted negatives + 1.docx positive) so the GHA `regression-gate` workflow can run the gate against real DOCX inputs without committing the full `positive_examples/` / `negative_examples/` directories (gitignored, ~107MB combined).

The workflow copies the fixture into the hardcoded test paths before running pytest. Local devs continue to use the full real `positive_examples/` / `negative_examples/`.

If you change the Wave B `_metadata.subset_filenames` in `tests/baselines/negative_corpus.json`, update `tests/fixtures/corpus/negative/` to match.
