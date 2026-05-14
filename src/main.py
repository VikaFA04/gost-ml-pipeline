from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import (
    EXTRACTED_DIR,
    GENERATED_DOCX_DIR,
    METRICS_DIR,
    MODELS_DIR,
    PREDICTIONS_DIR,
    REPORTS_DIR,
)
from src.evaluate import evaluate_predictions, save_evaluation
from src.evaluation.format_regression_audit import (
    audit_negative_directory,
    audits_to_frame,
    write_per_pair_baseline,
)
from src.generate.inplace_formatter import audit_or_format_docx
from src.io.block_extractor import extract_blocks_from_docx
from src.rules.methodical_extractor import extract_methodical_profile
from src.predict_blocks import load_blocks_csv, predict_blocks
from src.train import run_training


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def get_latest_model_path() -> Path:
    candidates = sorted(MODELS_DIR.glob("svm_block_classifier_*.joblib"))
    if not candidates:
        raise FileNotFoundError(
            f"В папке {MODELS_DIR} не найдена обученная модель. "
            f"Сначала запусти команду train."
        )
    return candidates[-1]


def resolve_model_path(model_path: Optional[str]) -> Path:
    if model_path is None:
        return get_latest_model_path()
    return Path(model_path)


def default_extracted_csv_path(input_docx: str | Path) -> Path:
    input_docx = Path(input_docx)
    return EXTRACTED_DIR / f"{input_docx.stem}_blocks_{now_ts()}.csv"


def default_predictions_csv_path() -> Path:
    return PREDICTIONS_DIR / f"predictions_{now_ts()}.csv"


def default_evaluation_json_path() -> Path:
    return METRICS_DIR / f"evaluation_{now_ts()}.json"


def default_audit_report_path(input_docx: str | Path) -> Path:
    input_docx = Path(input_docx)
    return REPORTS_DIR / f"{input_docx.stem}_audit_{now_ts()}.csv"


def default_format_report_path(input_docx: str | Path) -> Path:
    input_docx = Path(input_docx)
    return REPORTS_DIR / f"{input_docx.stem}_format_report_{now_ts()}.csv"


def default_regression_audit_report_path(positive_dir: str | Path, negative_dir: str | Path) -> Path:
    positive_dir = Path(positive_dir)
    negative_dir = Path(negative_dir)
    return REPORTS_DIR / f"regression_audit_{positive_dir.stem}_{negative_dir.stem}_{now_ts()}.csv"


def default_output_docx_path(input_docx: str | Path) -> Path:
    input_docx = Path(input_docx)
    return GENERATED_DOCX_DIR / f"{input_docx.stem}_formatted_{now_ts()}.docx"


def cmd_train() -> None:
    result = run_training()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_extract_docx(input_docx: str, output_csv: Optional[str]) -> None:
    input_docx_path = Path(input_docx)
    if not input_docx_path.exists():
        raise FileNotFoundError(f"Не найден DOCX-файл: {input_docx_path}")

    df = extract_blocks_from_docx(input_docx_path)

    output_path = Path(output_csv) if output_csv else default_extracted_csv_path(input_docx_path)
    ensure_parent_dir(output_path)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Извлеченные блоки сохранены в: {output_path}")
    print(f"Количество блоков: {len(df)}")


def cmd_predict(model_path: Optional[str], input_csv: str, output_csv: Optional[str]) -> None:
    input_csv_path = Path(input_csv)
    if not input_csv_path.exists():
        raise FileNotFoundError(f"Не найден CSV-файл: {input_csv_path}")

    model = resolve_model_path(model_path)
    if not model.exists():
        raise FileNotFoundError(f"Не найдена модель: {model}")

    df = load_blocks_csv(input_csv_path)
    pred_df = predict_blocks(model_path=model, blocks_df=df, apply_rules=True)

    output_path = Path(output_csv) if output_csv else default_predictions_csv_path()
    ensure_parent_dir(output_path)
    pred_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Использована модель: {model}")
    print(f"Предсказания сохранены в: {output_path}")
    print(f"Количество строк: {len(pred_df)}")


def cmd_evaluate(model_path: Optional[str], input_csv: str) -> None:
    input_csv_path = Path(input_csv)
    if not input_csv_path.exists():
        raise FileNotFoundError(f"Не найден CSV-файл: {input_csv_path}")

    model = resolve_model_path(model_path)
    if not model.exists():
        raise FileNotFoundError(f"Не найдена модель: {model}")

    df = load_blocks_csv(input_csv_path)
    pred_df = predict_blocks(model_path=model, blocks_df=df, apply_rules=True)

    result = evaluate_predictions(pred_df)
    output_path = default_evaluation_json_path()
    save_evaluation(result, output_path)

    print(f"Использована модель: {model}")
    print(f"Оценка сохранена в: {output_path}")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_audit_docx(input_docx: str, predictions_csv: str, report_csv: Optional[str]) -> None:
    input_docx_path = Path(input_docx)
    predictions_csv_path = Path(predictions_csv)

    if not input_docx_path.exists():
        raise FileNotFoundError(f"Не найден DOCX-файл: {input_docx_path}")
    if not predictions_csv_path.exists():
        raise FileNotFoundError(f"Не найден CSV с предсказаниями: {predictions_csv_path}")

    report_path = Path(report_csv) if report_csv else default_audit_report_path(input_docx_path)
    ensure_parent_dir(report_path)

    result = audit_or_format_docx(
        input_docx=input_docx_path,
        predictions_csv=predictions_csv_path,
        report_csv=report_path,
        output_docx=None,
        apply_safe=False,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_format_docx(
    input_docx: str,
    predictions_csv: str,
    report_csv: Optional[str],
    output_docx: Optional[str],
    apply_safe: bool,
) -> None:
    input_docx_path = Path(input_docx)
    predictions_csv_path = Path(predictions_csv)

    if not input_docx_path.exists():
        raise FileNotFoundError(f"Не найден DOCX-файл: {input_docx_path}")
    if not predictions_csv_path.exists():
        raise FileNotFoundError(f"Не найден CSV с предсказаниями: {predictions_csv_path}")

    report_path = Path(report_csv) if report_csv else default_format_report_path(input_docx_path)
    ensure_parent_dir(report_path)

    resolved_output_docx: Path | None = None
    if apply_safe:
        resolved_output_docx = Path(output_docx) if output_docx else default_output_docx_path(input_docx_path)
        ensure_parent_dir(resolved_output_docx)

    result = audit_or_format_docx(
        input_docx=input_docx_path,
        predictions_csv=predictions_csv_path,
        report_csv=report_path,
        output_docx=resolved_output_docx,
        apply_safe=apply_safe,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_audit_regression(
    positive_dir: str,
    negative_dir: str,
    workspace_dir: str,
    report_csv: Optional[str],
    summary_json: Optional[str],
    profile_id: str,
    limit: Optional[int] = None,
    progress: bool = False,
    update_baseline: Optional[str] = None,
    reason: Optional[str] = None,
) -> None:
    positive_dir_path = Path(positive_dir)
    negative_dir_path = Path(negative_dir)
    workspace_dir_path = Path(workspace_dir)

    if not positive_dir_path.exists():
        raise FileNotFoundError(f"Не найдена папка положительных примеров: {positive_dir_path}")
    if not negative_dir_path.exists():
        raise FileNotFoundError(f"Не найдена папка отрицательных примеров: {negative_dir_path}")

    report_path = Path(report_csv) if report_csv else default_regression_audit_report_path(
        positive_dir_path,
        negative_dir_path,
    )
    ensure_parent_dir(report_path)
    summary_path = Path(summary_json) if summary_json else report_path.with_suffix(".json")
    ensure_parent_dir(summary_path)

    def report_progress(index: int, total: int, negative_path: Path) -> None:
        print(f"[{index}/{total}] {negative_path.name}")

    audits = audit_negative_directory(
        positive_dir=positive_dir_path,
        negative_dir=negative_dir_path,
        workspace_dir=workspace_dir_path,
        profile_id=profile_id,
        limit=limit,
        progress_callback=report_progress if progress else None,
    )
    frame = audits_to_frame(audits)

    if update_baseline:
        # Probe 6 minimum: --reason must be >= 8 chars after strip (free text,
        # no forced ticket-ID format). Empty / whitespace / 7-char reasons
        # are refused.
        if not reason or len(reason.strip()) < 8:
            raise SystemExit(
                "--update-baseline требует --reason '<text>' (минимум 8 символов после strip; "
                "D-004: no silent rewrites; RESEARCH.md Probe 6)."
            )
        write_per_pair_baseline(
            path=Path(update_baseline),
            frame=frame,
            reason=reason.strip(),
            profile_id=profile_id,
        )

    frame.to_csv(report_path, index=False, encoding="utf-8-sig")

    summary = {
        "audits": len(audits),
        "report_csv": str(report_path),
        "summary_json": str(summary_path),
        "workspace_dir": str(workspace_dir_path),
        "total_changed": int(frame["formatter_changed"].sum()) if not frame.empty else 0,
        "total_errors": int(frame["formatter_error"].sum()) if not frame.empty else 0,
        "worse_count": int((frame["diff_delta"] > 0).sum()) if not frame.empty else 0,
        "improved_count": int((frame["diff_delta"] < 0).sum()) if not frame.empty else 0,
        "field_mismatch_delta": int(frame["field_mismatch_delta"].sum()) if not frame.empty else 0,
        "profile_id": profile_id,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def cmd_extract_methodical_profile(
    input_path: str,
    output_dir: Optional[str],
    profile_name: Optional[str],
    base_profile_ids: list[str],
) -> None:
    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        raise FileNotFoundError(f"Не найден файл методички: {input_path_obj}")

    profile, output_path = extract_methodical_profile(
        input_path=input_path_obj,
        output_dir=output_dir,
        base_profile_ids=base_profile_ids or None,
        profile_name=profile_name,
    )
    print(f"Профиль сохранен в: {output_path}")
    print(
        json.dumps(
            {
                "profile_id": profile.get("profile_id"),
                "profile_name": profile.get("profile_name"),
                "profile_type": profile.get("profile_type"),
                "source_type": profile.get("source_type"),
                "base_profiles": profile.get("base_profiles", []),
            },
            ensure_ascii=True,
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CLI для системы автоматизированного оформления документов по ГОСТ"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("train", help="Обучить модель на prepared dataset")

    extract_parser = subparsers.add_parser(
        "extract-docx",
        help="Извлечь блоки из DOCX в CSV",
    )
    extract_parser.add_argument("--input-docx", required=True, help="Путь к исходному DOCX")
    extract_parser.add_argument("--output-csv", required=False, help="Путь для сохранения CSV")

    predict_parser = subparsers.add_parser(
        "predict",
        help="Построить предсказания по CSV блоков",
    )
    predict_parser.add_argument(
        "--model-path",
        required=False,
        help="Путь к .joblib модели. Если не указан, берется последняя обученная модель.",
    )
    predict_parser.add_argument("--input-csv", required=True, help="CSV с блоками документа")
    predict_parser.add_argument("--output-csv", required=False, help="Куда сохранить предсказания")

    eval_parser = subparsers.add_parser(
        "evaluate",
        help="Оценить качество модели на размеченном CSV",
    )
    eval_parser.add_argument(
        "--model-path",
        required=False,
        help="Путь к .joblib модели. Если не указан, берется последняя обученная модель.",
    )
    eval_parser.add_argument("--input-csv", required=True, help="CSV с true labels")

    audit_parser = subparsers.add_parser(
        "audit-docx",
        help="Построить отчет нормоконтроля без изменения DOCX",
    )
    audit_parser.add_argument("--input-docx", required=True, help="Путь к исходному DOCX")
    audit_parser.add_argument("--predictions-csv", required=True, help="CSV с предсказаниями")
    audit_parser.add_argument("--report-csv", required=False, help="Куда сохранить отчет")

    format_parser = subparsers.add_parser(
        "format-docx",
        help="Выполнить безопасное форматирование DOCX",
    )
    format_parser.add_argument("--input-docx", required=True, help="Путь к исходному DOCX")
    format_parser.add_argument("--predictions-csv", required=True, help="CSV с предсказаниями")
    format_parser.add_argument("--report-csv", required=False, help="Куда сохранить отчет")
    format_parser.add_argument("--output-docx", required=False, help="Куда сохранить исправленный DOCX")
    format_parser.add_argument(
        "--apply-safe",
        action="store_true",
        help="Применить только безопасные изменения. Без этого флага будет только отчет.",
    )

    regression_parser = subparsers.add_parser(
        "audit-regression",
        help="Запустить regression-аудит по каталогам positive/negative DOCX",
    )
    regression_parser.add_argument("--positive-dir", required=True, help="Каталог положительных DOCX")
    regression_parser.add_argument("--negative-dir", required=True, help="Каталог отрицательных DOCX")
    regression_parser.add_argument(
        "--workspace-dir",
        required=False,
        help="Папка для промежуточных predictions/report/docx артефактов",
    )
    regression_parser.add_argument("--report-csv", required=False, help="Куда сохранить итоговый CSV отчет")
    regression_parser.add_argument("--summary-json", required=False, help="Куда сохранить итоговый JSON summary")
    regression_parser.add_argument(
        "--profile-id",
        required=False,
        default="gost_7_32_2017",
        help="profile_id для safe-formatting",
    )
    regression_parser.add_argument(
        "--limit",
        required=False,
        type=int,
        help="Ограничить число отрицательных DOCX для быстрого прогона",
    )
    regression_parser.add_argument(
        "--progress",
        action="store_true",
        help="Печатать текущий номер документа при регресс-аудите",
    )
    regression_parser.add_argument(
        "--update-baseline",
        required=False,
        type=str,
        metavar="PATH",
        help="Если задано, перезаписать per-pair ceilings из текущего прогона в JSON по этому пути. Требует --reason.",
    )
    regression_parser.add_argument(
        "--reason",
        required=False,
        type=str,
        help="Обязательное обоснование (свободный текст, минимум 8 символов после strip) при --update-baseline.",
    )

    methodical_parser = subparsers.add_parser(
        "extract-methodical-profile",
        help="Извлечь профиль оформления из локальной методички PDF/DOCX/TXT",
    )
    methodical_parser.add_argument("--input-path", required=True, help="Путь к PDF/DOCX/TXT/MD файлу")
    methodical_parser.add_argument(
        "--output-dir",
        required=False,
        help="Папка для сохранения профиля JSON",
    )
    methodical_parser.add_argument(
        "--profile-name",
        required=False,
        help="Человекочитаемое имя профиля",
    )
    methodical_parser.add_argument(
        "--base-profile-ids",
        nargs="+",
        default=["gost_7_32_2017", "gost_r_7_0_100_2018_bibliography"],
        help="Базовые profile_id, которые нужно слить перед извлечением",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "train":
        cmd_train()
        return

    if args.command == "extract-docx":
        cmd_extract_docx(
            input_docx=args.input_docx,
            output_csv=args.output_csv,
        )
        return

    if args.command == "predict":
        cmd_predict(
            model_path=args.model_path,
            input_csv=args.input_csv,
            output_csv=args.output_csv,
        )
        return

    if args.command == "evaluate":
        cmd_evaluate(
            model_path=args.model_path,
            input_csv=args.input_csv,
        )
        return

    if args.command == "audit-docx":
        cmd_audit_docx(
            input_docx=args.input_docx,
            predictions_csv=args.predictions_csv,
            report_csv=args.report_csv,
        )
        return

    if args.command == "format-docx":
        cmd_format_docx(
            input_docx=args.input_docx,
            predictions_csv=args.predictions_csv,
            report_csv=args.report_csv,
            output_docx=args.output_docx,
            apply_safe=args.apply_safe,
        )
        return

    if args.command == "audit-regression":
        cmd_audit_regression(
            positive_dir=args.positive_dir,
            negative_dir=args.negative_dir,
            workspace_dir=args.workspace_dir or str(REPORTS_DIR / "regression_audit" / now_ts()),
            report_csv=args.report_csv,
            summary_json=args.summary_json,
            profile_id=args.profile_id,
            limit=args.limit,
            progress=args.progress,
            update_baseline=args.update_baseline,
            reason=args.reason,
        )
        return

    if args.command == "extract-methodical-profile":
        cmd_extract_methodical_profile(
            input_path=args.input_path,
            output_dir=args.output_dir,
            profile_name=args.profile_name,
            base_profile_ids=args.base_profile_ids,
        )
        return

    raise ValueError(f"Неизвестная команда: {args.command}")


if __name__ == "__main__":
    main()
