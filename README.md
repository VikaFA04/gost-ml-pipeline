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
