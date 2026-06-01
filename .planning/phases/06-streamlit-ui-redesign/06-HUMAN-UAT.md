---
status: partial
phase: 06-streamlit-ui-redesign
source: [06-VERIFICATION.md]
started: 2026-05-15T07:42:00Z
updated: 2026-05-15T07:42:00Z
checkpoint_override: approved-with-followups (06-05 sign-off; no follow-ups recorded; live walk deferred)
---

## Current Test

[awaiting human testing in Streamlit-enabled venv]

## Tests

### 1. Live linear flow walk-through (SC-1 / REQ-ui-main-flow)
expected: On `streamlit run app.py` (Streamlit-enabled venv) — sidebar
shows «Панель управления», profile picker, modal trigger «+ Создать
профиль из методички», DOCX uploader, primary «Запустить аудит»
disabled until DOCX uploaded; uploading a real positive-corpus DOCX,
picking a profile, clicking run leads to main pane with report header
«Отчёт по документу: {filename}», 6-cell metric strip, 3 grouped
sections («Требуют внимания» expanded first, «Изменены» / «Без
изменений» collapsed), «Скачать результаты» section + run-log download —
reachable in ≤ 3 sidebar interactions.
result: [pending]

### 2. Visual distinction between status chips (SC-2 / REQ-ui-problem-block-view)
expected: Status chips for `error` (✗ «Ошибка», #fde7ef bg / #9f1239
text) and `no_change` (● «Без изменений», #dff7ea bg / #166534 text)
are distinguishable at a glance; per-block expander body shows
confidence, original block text via st.code, manual-review reason from
explanation.
result: [pending]

### 3. Preflight error surface — no traceback (SC-3 / REQ-input-preflight)
expected: Uploading a renamed-text-file as `.docx` or an empty `.docx`
shows the Russian preflight string under the file uploader. No
`Traceback (most recent call last):` substring appears anywhere in the
UI.
result: [pending]

### 4. Run-log JSON PII walk (SC-3 / REQ-pipeline-logging)
expected: After a real audit, click «Скачать журнал запуска (JSON)»;
open the downloaded file; inspect at least 2 `error_message` fields;
confirm no paragraph text from the uploaded document appears, no
forbidden keys (`text` / `paragraph` / `block_content` / `traceback`),
no consecutive Russian-letter substring matching document content.
result: [pending]

### 5. Modal D-004 reason gate (SC-1 modal subflow)
expected: Click «+ Создать профиль из методички»; in the modal upload a
small PDF + select a base profile; click «Сгенерировать предпросмотр»;
on profile-id collision the «Применить и сохранить» button must be
disabled when reason is empty; entering `abc` (3 chars) keeps it
disabled; entering `abcdefgh` (8 chars) enables it; entering 8 spaces
(whitespace-only) keeps it disabled; entering 8 zero-width joiners
(‍ × 8) keeps it disabled (CR-01 fix verification).
result: [pending]

### 6. Profile auto-select after modal apply (SC-1 modal subflow / Pitfall 4)
expected: Complete the methodical modal apply flow on a non-colliding
profile_id; on close, the sidebar profile picker shows the new profile
pre-selected; the selected option is the FORMATTED label from
`format_profile_option`, not the raw `profile_id`.
result: [pending]

### 7. Design-review sign-off (SC-4 / REQ-ui-design-review)
expected: 06-DESIGN-REVIEW.md is filled in: 5 pre-flight checks ticked,
6 falsifiable PASS criteria each marked PASS (or any FAIL recorded with
a fix commit in the defect log), 8 spot-check items ticked,
Reviewer/Date filled, Final status `APPROVED` or
`APPROVED-WITH-FOLLOWUPS`.
result: [override-accepted] — User signed off via orchestrator
checkpoint as approved-with-followups (no follow-ups recorded). Live
walk deferred to a Streamlit-enabled venv. Tracked here so it surfaces
in /gsd-progress until formally walked.

## Summary

total: 7
passed: 0
issues: 0
pending: 6
override-accepted: 1
skipped: 0
blocked: 0

## Gaps

(none recorded — items 1-6 awaiting live walk; item 7 has explicit
checkpoint override per Wave 5 sign-off)
