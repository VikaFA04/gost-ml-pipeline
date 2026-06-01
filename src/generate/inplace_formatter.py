from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from docx.table import Table
from docx.text.paragraph import Paragraph

from src.io.docx_reader import iter_block_items
from src.rules.profile_loader import (
    get_audit_policy,
    get_global_audit_policy,
    get_label_config,
    get_target_style_profile,
    load_profile,
)
from src.rules.rule_engine import apply_rules_to_paragraph
from src.rules.rule_loader import load_rules

LABEL_COL_CANDIDATES = ["postprocessed_label", "predicted_label"]


def resolve_label_column(df: pd.DataFrame) -> str:
    for col in LABEL_COL_CANDIDATES:
        if col in df.columns:
            return col
    raise ValueError("Predictions CSV must contain either 'postprocessed_label' or 'predicted_label'.")


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def extract_table_text(table: Table) -> str:
    rows: list[str] = []
    for row in table.rows:
        cells: list[str] = []
        for cell in row.cells:
            cell_text = "\n".join(
                p.text.strip() for p in cell.paragraphs if p.text and p.text.strip()
            ).strip()
            cells.append(cell_text)
        row_text = " | ".join(cells).strip()
        if row_text:
            rows.append(row_text)
    return "\n".join(rows).strip()


def normalize_compare_text(text: str) -> str:
    return " ".join(str(text).split()).strip()


def build_filtered_docx_blocks(document: Document) -> list[tuple[object, str, str]]:
    filtered_blocks: list[tuple[object, str, str]] = []
    for block in iter_block_items(document):
        if isinstance(block, Paragraph):
            text = "" if block.text is None else str(block.text)
            kind = "paragraph"
        elif isinstance(block, Table):
            text = extract_table_text(block)
            kind = "table"
        else:
            continue

        if text:
            filtered_blocks.append((block, kind, text))
    return filtered_blocks


def length_to_cm(value) -> float | None:
    if value is None:
        return None
    try:
        return round(value.cm, 3)
    except Exception:
        return None


def length_to_pt(value) -> float | None:
    if value is None:
        return None
    try:
        return round(value.pt, 3)
    except Exception:
        return None


def normalize_alignment(value) -> str | None:
    if value is None:
        return None

    mapping = {
        WD_ALIGN_PARAGRAPH.LEFT: "LEFT",
        WD_ALIGN_PARAGRAPH.CENTER: "CENTER",
        WD_ALIGN_PARAGRAPH.RIGHT: "RIGHT",
        WD_ALIGN_PARAGRAPH.JUSTIFY: "JUSTIFY",
        WD_ALIGN_PARAGRAPH.DISTRIBUTE: "DISTRIBUTE",
        WD_ALIGN_PARAGRAPH.JUSTIFY_MED: "JUSTIFY",
        WD_ALIGN_PARAGRAPH.JUSTIFY_HI: "JUSTIFY",
        WD_ALIGN_PARAGRAPH.JUSTIFY_LOW: "JUSTIFY",
        WD_ALIGN_PARAGRAPH.THAI_JUSTIFY: "JUSTIFY",
    }
    return mapping.get(value, str(value))


def get_first_text_run_style(paragraph: Paragraph) -> dict[str, Any]:
    for run in paragraph.runs:
        if run.text and run.text.strip():
            font_size_pt = None
            try:
                if run.font.size is not None:
                    font_size_pt = round(run.font.size.pt, 3)
            except Exception:
                font_size_pt = None

            return {
                "font_size_pt": font_size_pt,
                "bold": bool(run.bold) if run.bold is not None else False,
            }

    return {
        "font_size_pt": None,
        "bold": False,
    }


def get_current_paragraph_profile(paragraph: Paragraph) -> dict[str, Any]:
    fmt = paragraph.paragraph_format

    line_spacing = fmt.line_spacing
    line_spacing_value = None
    if isinstance(line_spacing, (int, float)):
        line_spacing_value = round(float(line_spacing), 3)

    run_style = get_first_text_run_style(paragraph)

    return {
        "alignment": normalize_alignment(paragraph.alignment),
        "first_line_indent_cm": length_to_cm(fmt.first_line_indent),
        "left_indent_cm": length_to_cm(fmt.left_indent),
        "line_spacing": line_spacing_value,
        "space_before_pt": length_to_pt(fmt.space_before),
        "space_after_pt": length_to_pt(fmt.space_after),
        "font_size_pt": run_style["font_size_pt"],
        "bold": run_style["bold"],
    }


def compare_profiles(
    current: dict[str, Any],
    target: dict[str, Any],
    tol: float = 0.05,
) -> tuple[list[str], list[str]]:
    changed_fields: list[str] = []
    uncertain_fields: list[str] = []

    for key, target_value in target.items():
        current_value = current.get(key)

        if current_value is None:
            continue

        if isinstance(target_value, float):
            try:
                if abs(float(current_value) - target_value) > tol:
                    changed_fields.append(key)
            except Exception:
                uncertain_fields.append(key)
        elif isinstance(target_value, int):
            try:
                if int(round(float(current_value))) != int(target_value):
                    changed_fields.append(key)
            except Exception:
                uncertain_fields.append(key)
        else:
            if current_value != target_value:
                changed_fields.append(key)

    return changed_fields, uncertain_fields


def apply_font_to_runs(
    paragraph: Paragraph,
    font_name: str = "Times New Roman",
    font_size_pt: int = 14,
    bold: bool | None = None,
) -> None:
    for run in paragraph.runs:
        if not run.text:
            continue
        run.font.name = font_name
        run.font.size = Pt(font_size_pt)
        if bold is not None:
            run.bold = bold


def apply_profile_to_paragraph(
    paragraph: Paragraph,
    style_profile: dict[str, Any],
    default_font_name: str = "Times New Roman",
) -> None:
    fmt = paragraph.paragraph_format

    fmt.first_line_indent = Cm(float(style_profile.get("first_line_indent_cm", 0.0)))
    fmt.left_indent = Cm(float(style_profile.get("left_indent_cm", 0.0)))
    fmt.right_indent = Cm(0)
    fmt.line_spacing = float(style_profile.get("line_spacing", 1.5))
    fmt.space_before = Pt(float(style_profile.get("space_before_pt", 0.0)))
    fmt.space_after = Pt(float(style_profile.get("space_after_pt", 0.0)))

    alignment_map = {
        "LEFT": WD_ALIGN_PARAGRAPH.LEFT,
        "CENTER": WD_ALIGN_PARAGRAPH.CENTER,
        "RIGHT": WD_ALIGN_PARAGRAPH.RIGHT,
        "JUSTIFY": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "DISTRIBUTE": WD_ALIGN_PARAGRAPH.DISTRIBUTE,
    }
    paragraph.alignment = alignment_map.get(
        style_profile.get("alignment", "LEFT"),
        WD_ALIGN_PARAGRAPH.LEFT,
    )

    apply_font_to_runs(
        paragraph=paragraph,
        font_name=default_font_name,
        font_size_pt=int(style_profile.get("font_size_pt", 14)),
        bold=bool(style_profile.get("bold", False)),
    )


def build_reason(
    action: str,
    label: str,
    changed_fields: list[str],
    uncertain_fields: list[str],
    low_confidence: bool,
) -> str:
    if low_confidence:
        return "Model confidence is too low for automatic formatting."

    if action in {"changed", "review"} and changed_fields:
        return f"Formatting differences detected: {', '.join(changed_fields)}"

    if action == "review" and uncertain_fields:
        return "Manual review is required because some formatting parameters could not be verified."

    if action == "no_change":
        return f"Block '{label}' already matches the expected formatting profile."

    if action == "error":
        return "An error occurred while applying formatting rules."

    return "No additional action required."


def build_recommendation(
    action: str,
    changed_fields: list[str],
    low_confidence: bool,
    manual_review_required: bool = False,
    suggested_fixes: list[str] | None = None,
    unsafe_auto_fix_reason: str = "",
) -> str:
    if low_confidence:
        return "Verify the predicted block type manually."

    if action == "changed" and changed_fields:
        return f"Applied fixes: {', '.join(changed_fields)}"

    if manual_review_required and suggested_fixes:
        return f"Manual decision required for: {', '.join(suggested_fixes)}"

    if unsafe_auto_fix_reason:
        return f"Unsafe auto-fix blocked: {unsafe_auto_fix_reason}"

    if action == "review" and changed_fields:
        return f"Review and optionally correct: {', '.join(changed_fields)}"

    if action == "no_change":
        return "No changes required."

    if action == "review":
        return "Manual review required."

    if action == "error":
        return "Inspect the block and rule configuration manually."

    return "No action."


def decide_action(
    changed_fields: list[str],
    uncertain_fields: list[str],
    low_confidence: bool,
    apply_safe: bool,
    audit_policy: dict[str, Any],
) -> str:
    if low_confidence and audit_policy.get("review_on_low_confidence", True):
        return "review"

    if changed_fields:
        if apply_safe and audit_policy.get("allow_auto_fix", False):
            return "changed"
        return "review"

    if uncertain_fields and audit_policy.get("review_on_uncertain_fields", True):
        return "review"

    return "no_change"


def audit_or_format_docx(
    input_docx: str | Path,
    predictions_csv: str | Path,
    report_csv: str | Path,
    output_docx: str | Path | None = None,
    apply_safe: bool = False,
    profile_path: str | Path | None = None,
    profile_id: str | None = None,
) -> dict[str, Any]:
    input_docx = Path(input_docx)
    predictions_csv = Path(predictions_csv)
    report_csv = Path(report_csv)

    profile = load_profile(profile_path=profile_path, profile_id=profile_id)
    rules = load_rules()
    global_policy = get_global_audit_policy(profile)
    labels_cfg = profile.get("labels", {})
    default_font_name = (
        profile.get("document_rules", {})
        .get("default_font", {})
        .get("font_name", "Times New Roman")
    )

    df = pd.read_csv(predictions_csv)
    if "block_id" in df.columns:
        df = df.sort_values("block_id").reset_index(drop=True)

    label_col = resolve_label_column(df)
    document = Document(str(input_docx))
    filtered_docx_blocks = build_filtered_docx_blocks(document)

    if len(filtered_docx_blocks) != len(df):
        raise ValueError(
            f"Filtered block count mismatch: DOCX={len(filtered_docx_blocks)}, CSV={len(df)}"
        )

    report_rows: list[dict[str, Any]] = []
    changed_count = 0
    review_count = 0
    no_change_count = 0
    error_count = 0
    blocked_unsafe_autofix_count = 0

    for i, ((block, actual_kind, docx_text), row) in enumerate(
        zip(filtered_docx_blocks, df.itertuples(index=False)),
        start=1,
    ):
        row_data = row._asdict()
        csv_kind = str(getattr(row, "kind", "paragraph"))
        csv_text = "" if pd.isna(getattr(row, "text", "")) else str(getattr(row, "text", ""))
        label = str(getattr(row, label_col, ""))
        low_confidence = bool(getattr(row, "low_confidence", False))
        confidence_score = getattr(row, "confidence_score", None)

        if actual_kind != csv_kind:
            raise ValueError(f"Kind mismatch at block {i}: DOCX={actual_kind}, CSV={csv_kind}")

        if normalize_compare_text(docx_text) != normalize_compare_text(csv_text):
            raise ValueError(
                f"Text mismatch at block {i}.\nDOCX: {docx_text[:120]}\nCSV : {csv_text[:120]}"
            )
        row_data["text"] = csv_text

        action = "skip"
        changed_fields: list[str] = []
        uncertain_fields: list[str] = []
        violated_rules: list[str] = []
        applied_fixes: list[str] = []
        suggested_fixes: list[str] = []
        suggested_rule_ids: list[str] = []
        manual_review_required = False
        blocked_unsafe_autofix = False
        unsafe_auto_fix_reason = ""
        explanation = ""

        if isinstance(block, Table):
            action = "review" if global_policy.get("review_tables_by_default", False) else "skip_table"
            if action == "review":
                review_count += 1

        elif label not in labels_cfg:
            action = "review" if global_policy.get("review_unknown_labels", True) else "skip_label"
            if action == "review":
                review_count += 1

        else:
            target_profile = get_target_style_profile(profile, label)
            label_cfg = get_label_config(profile, label) or {}
            allowed_kinds = label_cfg.get("kind", ["paragraph"])
            audit_policy = get_audit_policy(profile, label)

            if actual_kind not in allowed_kinds:
                action = "review"
                review_count += 1
                explanation = "Block kind is not allowed for the predicted label."
            elif target_profile is None:
                action = "review"
                review_count += 1
                explanation = "No formatting profile is configured for this label."
            elif not isinstance(block, Paragraph):
                action = "review"
                review_count += 1
                explanation = "Paragraph-level rules cannot be applied to this block."
            else:
                try:
                    rule_result = apply_rules_to_paragraph(
                        paragraph=block,
                        label=label,
                        row_data=row_data,
                        rules=rules,
                        apply_safe=apply_safe,
                        default_font_name=default_font_name,
                    )

                    if rule_result is not None:
                        action = str(rule_result["status"])
                        violated_rules = list(rule_result["violated_rules"])
                        applied_fixes = list(rule_result["applied_fixes"])
                        suggested_fixes = list(rule_result.get("suggested_fixes", []))
                        suggested_rule_ids = list(rule_result.get("suggested_rule_ids", []))
                        manual_review_required = bool(rule_result.get("manual_review_required", False))
                        blocked_unsafe_autofix = bool(rule_result.get("blocked_unsafe_autofix", False))
                        unsafe_auto_fix_reason = str(rule_result.get("unsafe_auto_fix_reason", ""))
                        changed_fields = applied_fixes.copy()
                        explanation = str(rule_result["explanation"])
                    else:
                        current_profile = get_current_paragraph_profile(block)
                        changed_fields, uncertain_fields = compare_profiles(
                            current=current_profile,
                            target=target_profile,
                        )
                        action = decide_action(
                            changed_fields=changed_fields,
                            uncertain_fields=uncertain_fields,
                            low_confidence=low_confidence,
                            apply_safe=apply_safe,
                            audit_policy=audit_policy,
                        )
                        if action == "changed":
                            before_text = block.text
                            apply_profile_to_paragraph(
                                paragraph=block,
                                style_profile=target_profile,
                                default_font_name=default_font_name,
                            )
                            after_text = block.text
                            if before_text != after_text:
                                raise ValueError(f"Formatting changed the text content of block {i}, which is not allowed.")
                            applied_fixes = changed_fields.copy()
                        explanation = build_reason(
                            action=action,
                            label=label,
                            changed_fields=changed_fields,
                            uncertain_fields=uncertain_fields,
                            low_confidence=low_confidence,
                        )
                except Exception as exc:
                    action = "error"
                    explanation = f"Rule/formatting error: {exc}"
                    error_count += 1

                if blocked_unsafe_autofix:
                    blocked_unsafe_autofix_count += 1

                if action == "changed":
                    changed_count += 1
                elif action == "review":
                    review_count += 1
                elif action == "no_change":
                    no_change_count += 1

        reason = explanation or build_reason(
            action=action,
            label=label,
            changed_fields=changed_fields,
            uncertain_fields=uncertain_fields,
            low_confidence=low_confidence,
        )

        report_rows.append(
            {
                "block_id": getattr(row, "block_id", i),
                "kind": csv_kind,
                "label": label,
                "status": action,
                "action": action,
                "profile_id": profile.get("profile_id"),
                "profile_name": profile.get("profile_name"),
                "confidence_score": confidence_score,
                "low_confidence": low_confidence,
                "manual_review_required": manual_review_required,
                "blocked_unsafe_autofix": blocked_unsafe_autofix,
                "unsafe_auto_fix_reason": unsafe_auto_fix_reason,
                "violated_rules": ", ".join(violated_rules),
                "suggested_rule_ids": ", ".join(suggested_rule_ids),
                "applied_fixes": ", ".join(applied_fixes),
                "suggested_fix": ", ".join(suggested_fixes),
                "changed_fields": ", ".join(changed_fields),
                "uncertain_fields": ", ".join(uncertain_fields),
                "reason": reason,
                "explanation": reason,
                "recommendation": build_recommendation(
                    action=action,
                    changed_fields=changed_fields,
                    low_confidence=low_confidence,
                    manual_review_required=manual_review_required,
                    suggested_fixes=suggested_fixes,
                    unsafe_auto_fix_reason=unsafe_auto_fix_reason,
                ),
                "text": csv_text[:500],
            }
        )

    report_df = pd.DataFrame(report_rows)
    report_csv.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(report_csv, index=False, encoding="utf-8-sig")

    saved_output_docx = None
    if apply_safe:
        if output_docx is None:
            raise ValueError("output_docx is required when apply_safe=True.")

        output_docx = Path(output_docx)
        output_docx.parent.mkdir(parents=True, exist_ok=True)
        document.save(str(output_docx))
        saved_output_docx = str(output_docx)

    return {
        "input_docx": str(input_docx),
        "predictions_csv": str(predictions_csv),
        "report_csv": str(report_csv),
        "output_docx": saved_output_docx,
        "profile_id": profile.get("profile_id"),
        "profile_name": profile.get("profile_name"),
        "blocks_total": len(df),
        "no_change": no_change_count,
        "review": review_count,
        "changed": changed_count,
        "error": error_count,
        "blocked_unsafe_autofix": blocked_unsafe_autofix_count,
        "mode": "apply_safe" if apply_safe else "audit_only",
    }
