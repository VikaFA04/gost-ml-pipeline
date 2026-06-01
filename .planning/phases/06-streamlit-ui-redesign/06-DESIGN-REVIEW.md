---
phase: 06-streamlit-ui-redesign
review_type: design-review
reviewer: project-owner
created: 2026-05-14
status: pending
---

# Phase 6 Design Review

This checklist is the executable form of `06-CONTEXT.md` SC-4 («UI passes a design-review pass by the project owner») and `06-VALIDATION.md` §"Manual-Only Verifications". The project owner runs `streamlit run app.py`, walks the linear flow + methodical modal + preflight error path + run-log download, marks each criterion below PASS / FAIL, records defects in §"Defect log", and signs off in §"Design-Review Sign-Off". Sign-off must be `APPROVED` or `APPROVED-WITH-FOLLOWUPS`; `REJECTED` requires returning to the relevant plan (06-02 / 06-03 / 06-04) for repair before re-running this checkpoint.

## Pre-flight check

- [ ] `python -m pytest tests/ -x -q --ignore=tests/test_methodical_profile_editor.py` exits 0.
- [ ] `streamlit run app.py` launches without exception.
- [ ] Sidebar visible with «Панель управления» header.
- [ ] Profile dropdown populated.
- [ ] Run button («Запустить аудит») disabled until DOCX uploaded.

## Falsifiable PASS criteria

1. **Flow completeness.** Tester uploads a real DOCX (e.g., from `positive_examples/`), selects a profile, clicks «Запустить аудит», and reaches the «Скачать результаты» section in ≤ 3 sidebar interactions. No dead-ends (empty tab, broken button). — `[ ] PASS  [ ] FAIL`  Notes: ____

2. **Visual distinction.** «Требуют внимания» section is visually first and expanded by default; «Без изменений» section is collapsed. Status chips for `error` and `no_change` are visually distinguishable at a glance (different icon: ✗ vs ●; different Russian label: «Ошибка» vs «Без изменений»). — `[ ] PASS  [ ] FAIL`  Notes: ____

3. **No traceback exposure.** Running audit on an intentionally malformed DOCX (e.g., empty file or `.docx`-renamed `.txt`) shows a Russian error message under the uploader. No Python stack trace visible anywhere in the UI. The only Python identifier permitted in the UI is the bare error class name (e.g., `KeyError`) inside the run-log; no `Traceback (most recent call last)` substring appears. — `[ ] PASS  [ ] FAIL`  Notes: ____

4. **Run-log PII check.** Click «Скачать журнал запуска (JSON)» — produces a JSON file. Open it. No paragraph text from the uploaded document appears in any field. Tester must inspect at least the `error_message` fields. Forbidden keys: `text`, `paragraph`, `block_content`, `traceback`. Forbidden values: any substring matching ≥ 6 consecutive Russian letters from the input document. — `[ ] PASS  [ ] FAIL`  Notes: ____

5. **Modal D-004 gate.** In the methodical modal, after generating a preview that hits a profile_id collision, the «Применить и сохранить» button must be disabled when the reason textarea is empty. Enter `"abc"` (3 chars) — still blocked. Enter `"abcdefgh"` (8 chars, all non-whitespace) — button becomes enabled. Whitespace-only reason of length ≥ 8 (e.g., `"        "`) must remain blocked. — `[ ] PASS  [ ] FAIL`  Notes: ____

6. **Profile auto-select.** After completing the methodical modal apply flow on a non-colliding profile_id, close modal, verify the sidebar profile picker shows the new profile pre-selected on the next rerun. The selected option must be the FORMATTED label from `format_profile_option`, not the raw `profile_id`. — `[ ] PASS  [ ] FAIL`  Notes: ____

## Visual / Russian copy spot check

- [ ] Sidebar run button reads «Запустить аудит» (not «Запустить анализ документа» or similar).
- [ ] Modal trigger button reads «+ Создать профиль из методички».
- [ ] Report header reads «Отчёт по документу: {filename}» (with the literal `«` `»` quote glyphs and the colon-space pattern).
- [ ] Section header «Требуют внимания» visible at the top of the main pane after a run (above «Изменены» and «Без изменений»).
- [ ] Download button «Скачать журнал запуска (JSON)» visible at the bottom of the «Скачать результаты» section.
- [ ] Empty-state heading «Загрузите DOCX-документ, чтобы начать аудит» visible before any run.
- [ ] No tab strip («Обзор / Предсказания / Аудит / Форматирование / Артефакты») present anywhere in the main pane.
- [ ] No `st.exception` traceback visible on any error path (preflight, modal PDF-no-text, modal collision, or pipeline failure).

## Defect log

Per `06-CONTEXT.md` SC-4: «defects fixed before close». CRITICAL and HIGH defects are blocking; MEDIUM and LOW may close as known-issue v2 entries (with explicit user sign-off recorded in §"Design-Review Sign-Off" Final status as `APPROVED-WITH-FOLLOWUPS`).

| Severity (CRITICAL/HIGH/MEDIUM/LOW) | Criterion ref (1-6 or spot-check item) | Description | Status (open / fixed) | Fix commit (sha) |
| ------------------------------------ | -------------------------------------- | ----------- | --------------------- | ---------------- |
| _example: HIGH_                      | _criterion 3_                          | _Traceback leaks under uploader on empty .docx_ | _open_ | _-_ |

## Design-Review Sign-Off

- **Reviewer:** ____
- **Date:** ____
- **Final status:** `[ ] APPROVED  [ ] APPROVED-WITH-FOLLOWUPS  [ ] REJECTED`
- **Approval signature:** ____________________
