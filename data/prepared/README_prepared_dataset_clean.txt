Подготовленный чистый датасет на 59 документах.

Файлы:
- annotations_prepared_all_59_clean.csv — общий датасет со столбцом split
- annotations_train_59_clean.csv — обучающая выборка
- annotations_val_59_clean.csv — валидационная выборка
- annotations_test_59_clean.csv — тестовая выборка
- document_splits_59_clean.csv — разбиение по документам
- class_distribution_59_clean.csv — распределение классов
- doc_distribution_59_clean.csv — распределение документов
- baseline_train_clean59.py — baseline-скрипт для чистого датасета

Параметры разбиения:
- train docs: 41
- val docs: 9
- test docs: 9

Число блоков:
- train: 14734
- val: 2571
- test: 2707

Важно:
Разбиение выполнено по doc_id, чтобы исключить утечку информации между выборками.