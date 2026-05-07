from __future__ import annotations

from pathlib import Path

# БАЗОВЫЕ ПУТИ ПРОЕКТА
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
PREPARED_DIR = DATA_DIR / "prepared"
DATASET_DIR = PROJECT_ROOT / "dataset"

RESULTS_DIR = PROJECT_ROOT / "results"
MODELS_DIR = RESULTS_DIR / "models"
METRICS_DIR = RESULTS_DIR / "metrics"
PREDICTIONS_DIR = RESULTS_DIR / "predictions"
REPORTS_DIR = RESULTS_DIR / "reports"
GENERATED_DOCX_DIR = RESULTS_DIR / "generated_docx"
EXTRACTED_DIR = RESULTS_DIR / "extracted_blocks"

# ОСНОВНЫЕ DATASET ФАЙЛЫ
TRAIN_CSV = DATASET_DIR / "annotations_train.csv"
VAL_CSV = DATASET_DIR / "annotations_val.csv"
TEST_CSV = DATASET_DIR / "annotations_test.csv"
DOCUMENT_SPLITS_CSV = DATASET_DIR / "document_splits.csv"

# КОЛОНКИ ДАННЫХ
TEXT_COL = "text"
TARGET_COL = "label_core"

FEATURE_COLUMNS = [
    "text",
    "kind",
    "alignment",
    "style",
    "bold_ratio",
]

CAT_COLS = [
    "kind",
    "alignment",
    "style",
]

NUM_COLS = [
    "bold_ratio",
]

OPTIONAL_META_COLUMNS = [
    "doc_id",
    "block_id",
    "file_name",
    "confidence",
    "notes",
    "split",
    "label_core",
    "label_detailed",
]

# ПАРАМЕТРЫ TF-IDF
TFIDF_MAX_FEATURES = 15000
TFIDF_NGRAM_RANGE = (1, 2)
TFIDF_MIN_DF = 2
TFIDF_SUBLINEAR_TF = True

# ПАРАМЕТРЫ МОДЕЛИ
SVM_C = 1.0
SVM_CLASS_WEIGHT = "balanced"
RANDOM_STATE = 42
SVM_MAX_ITER = 10000

# ПРЕФИКСЫ ИМЕН АРТЕФАКТОВ
MODEL_FILENAME_PREFIX = "svm_block_classifier"
EVAL_FILENAME_PREFIX = "evaluation"
PRED_FILENAME_PREFIX = "predictions"
AUDIT_FILENAME_PREFIX = "audit_report"
FORMAT_FILENAME_PREFIX = "format_report"
EXTRACT_FILENAME_PREFIX = "extracted_blocks"

# СЛУЖЕБНЫЕ ФУНКЦИИ
def ensure_directories() -> None:
    for path in [
        RESULTS_DIR,
        MODELS_DIR,
        METRICS_DIR,
        PREDICTIONS_DIR,
        REPORTS_DIR,
        GENERATED_DOCX_DIR,
        EXTRACTED_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def validate_core_paths() -> None:
    required_files = [TRAIN_CSV, VAL_CSV, TEST_CSV]
    missing = [str(p) for p in required_files if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Не найдены обязательные prepared dataset файлы:\n"
            + "\n".join(missing)
        )


ensure_directories()