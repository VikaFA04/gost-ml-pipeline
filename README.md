# GOST Formatter

Локальный Python-проект для первичного нормоконтроля DOCX-документов: извлечение блоков, классификация ролей через Linear SVM, консервативная постобработка, rule-based аудит ГОСТ и безопасное форматирование DOCX.

## Текущий MVP

- Основной источник данных: `dataset/`.
- Основная модель: TF-IDF + pattern features + форматные признаки + Linear SVM.
- Основной формат документа: DOCX.
- Основной пользовательский путь: CLI или Streamlit UI.
- Safe formatting применяет только проверяемые правки; спорные случаи остаются `review`.

## Данные

Файлы обучения:

- `dataset/annotations_train.csv`
- `dataset/annotations_val.csv`
- `dataset/annotations_test.csv`
- `dataset/document_splits.csv`

Справочные файлы:

- `dataset/annotations_train_ready.csv`
- `dataset/annotations_weak_labeled_all.csv`
- `dataset/annotations_review_queue.csv`
- `dataset/label_distribution.csv`
- `dataset/ml_baseline_comparison_weak_labels.csv`

`data/prepared/` не используется текущим MVP-обучением без отдельного явного решения.

## Быстрый запуск

В этом workspace используется Windows-venv:

```bash
.venv/Scripts/python.exe -m pytest -q
```

Ожидаемая текущая проверка:

```text
77 passed
```

Текущая проверка regression-аудита на локальных `positive_examples/` и `negative_examples/`:

```text
audits: 16
total_errors: 0
worse_count: 0
```

## Pre-PR проверка

Перед любым fix-track PR запусти:

```bash
make regression-gate
```

или (без GNU Make):

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

См. `CONTRIBUTING.md` для деталей (включая процедуру обновления baseline через `--update-baseline` + `--reason`).

## Обучение модели

```bash
.venv/Scripts/python.exe -m src.main train
```

Текущий проверенный артефакт:

```text
results/models/svm_block_classifier_20260506_082307.joblib
```

Текущие метрики на `dataset/annotations_test.csv` после консервативной постобработки:

```text
accuracy     0.9835
weighted_f1  0.9829
macro_f1     0.9414
```

## Оценка

```bash
.venv/Scripts/python.exe -m src.main evaluate \
  --model-path results/models/svm_block_classifier_20260506_082307.joblib \
  --input-csv dataset/annotations_test.csv
```

Оценка сохраняется в `results/metrics/evaluation_*.json` и содержит `before_rules` / `after_rules`.

## DOCX pipeline через CLI

Извлечь блоки:

```bash
.venv/Scripts/python.exe -m src.main extract-docx \
  --input-docx data/raw/docx/50.docx \
  --output-csv results/extracted_blocks/50_blocks.csv
```

Построить предсказания:

```bash
.venv/Scripts/python.exe -m src.main predict \
  --model-path results/models/svm_block_classifier_20260506_082307.joblib \
  --input-csv results/extracted_blocks/50_blocks.csv \
  --output-csv results/predictions/50_predictions.csv
```

Построить audit-only отчет:

```bash
.venv/Scripts/python.exe -m src.main audit-docx \
  --input-docx data/raw/docx/50.docx \
  --predictions-csv results/predictions/50_predictions.csv \
  --report-csv results/reports/50_audit.csv
```

Запустить regression-аудит по каталогам positive/negative DOCX:

```bash
.venv/Scripts/python.exe -m src.main audit-regression \
  --positive-dir positive_examples \
  --negative-dir negative_examples \
  --workspace-dir results/regression_audit \
  --limit 5 \
  --progress \
  --report-csv results/reports/regression_audit.csv \
  --summary-json results/reports/regression_audit_summary.json
```

Создать DOCX с безопасными исправлениями:

```bash
.venv/Scripts/python.exe -m src.main format-docx \
  --input-docx data/raw/docx/50.docx \
  --predictions-csv results/predictions/50_predictions.csv \
  --report-csv results/reports/50_format.csv \
  --output-docx results/generated_docx/50_formatted.docx \
  --apply-safe
```

Проверенный результат для `data/raw/docx/50.docx`:

```text
blocks_total: 260
format error: 0
second format changed: 0
```

## Локальные источники ГОСТ

Извлечь профиль оформления из локальной методички:

```bash
.venv/Scripts/python.exe -m src.main extract-methodical-profile \
  --input-path path/to/guideline.pdf \
  --output-dir src/rules/profiles \
  --profile-name "Локальный профиль нормоконтроля"
```

Команда поддерживает `PDF`, `DOCX`, `TXT` и `MD`. Из PDF текст извлекается через `pypdf`; если пакет не установлен, команда завершится с понятной ошибкой.

## Streamlit UI

```bash
.venv/Scripts/streamlit.exe run app.py
```

Baseline-модель выбирается первой, если в `results/models/` или `artifacts/baseline/` есть `.joblib`-артефакт. Transformer остается экспериментальной опцией.

## Ограничения MVP

- PDF не поддерживается в end-to-end pipeline.
- OCR и сканированные документы не входят в MVP.
- Автокоррекция не применяется к небезопасным или неоднозначным блокам.
- Финальная проверка спорных `review`-блоков остается за пользователем.
- Метрики считаются на weak-label датасете; спорные классы нужно дополнительно валидировать вручную.

## Limits

PDF input is supported in audit-only mode: the document must contain an extractable text layer (≥ 50% of pages must return non-empty text via `fitz.Page.get_text()`). Scanned PDFs and page-image PDFs are rejected at preflight — OCR is not supported. There is no corrected PDF produced; `applied_fixes` is always empty for PDF blocks. DOCX input remains the only path that produces a corrected document.

## Classical model comparison

The `compare-classical` CLI scores six classifier pipelines on the locked held-out
test set and writes structured artifacts for Phase 8 SC-2 acceptance.

### Invocation

```bash
# Full run (all six models, full training set):
python -m src.main compare-classical

# Subset of models:
python -m src.main compare-classical --models lr,svm,svm_production,nb,rf,hgb

# Specify output directory explicitly:
python -m src.main compare-classical --output-dir results/reports/classical_zoo_manual/

# Quick CI smoke (train subsampled to 1000 rows — NOT gated by Phase 8 SC-2):
python -m src.main compare-classical --quick --seed 42

# Run zoo AND Phase 8 SC-2 acceptance test in one step:
make compare-classical-acceptance
```

### Output

Each run writes four files under `results/reports/classical_zoo_<YYYYMMDD_HHMMSS>/`:

| File | Description |
|------|-------------|
| `results.csv` | Headline metrics table — six rows, 8 locked columns |
| `results.json` | Full structured record (models, environment, dataset hashes, timestamps, cli_args) |
| `summary.txt` | Human-readable summary with Phase 8 SC-2 verdict |
| `per_class_f1.md` | Per-class precision/recall/F1 for every model |

### results.csv shape

The `results.csv` file always has **six rows** (one per pipeline) and 8 columns in
locked order (`model`, `preprocessing_variant`, `accuracy`, `weighted_f1`, `macro_f1`,
`train_time_sec`, `inference_time_ms_per_block`, `model_size_mb`):

| model | preprocessing_variant | notes |
|-------|-----------------------|-------|
| `logistic_regression` | `tfidf_struct` | |
| `linear_svm` | `tfidf_struct` | Zoo apples-to-apples row (informational) |
| `linear_svm_production` | `tfidf_struct_textpatterns` | **Phase 8 SC-2 gate row** |
| `complement_nb` | `tfidf_only` | Structural features dropped (non-negativity constraint) |
| `random_forest` | `tfidf_struct` | |
| `histgbm_svd256` | `tfidf_struct_svd256` | TF-IDF block compressed via TruncatedSVD(256) |

The `linear_svm` row documents the cost of dropping `TextPatternFeatures` from the
pipeline in an apples-to-apples comparison. It is informational only — expected to
score below the SC-2 floor (~0.928 weighted F1 per research baseline).

The `linear_svm_production` row uses the full production preprocessing pipeline
(`src/train.py::build_pipeline()` with `TextPatternFeatures` included). This row is
the Phase 8 SC-2 gate: `weighted_f1 >= 0.94 AND macro_f1 >= 0.86`. Production
identity (`results/models/svm_block_classifier_*.joblib`) is preserved — Phase 9 is
strictly informational and does not swap the production model.

### Phase 8 SC-2 acceptance gate

```bash
python -m pytest tests/test_phase_8_sc2_acceptance.py -v
```

The test reads the most recent `results/reports/classical_zoo_*/results.csv`, locates
the `linear_svm_production` row, and asserts `weighted_f1 >= 0.94 AND macro_f1 >=
0.86`. If no zoo run exists, the test skips with an informative message.

Phase 9 planning and research are documented in
`.planning/phases/09-classical-model-zoo-lr-svm-complementnb-randomforest-histgbm/`.
