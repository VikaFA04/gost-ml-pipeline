# План большого блока: заголовки, списки источников и материалы нормоконтроля

Дата: 2026-05-10

## Контекст

Текущий safe-formatting уже умеет исправлять часть list layout и теперь распознает список используемых/использованных источников по DOCX-структуре и текстовому контексту. Следующий крупный риск — заголовки: визуально они могут выглядеть правильно, но Word-параметры стиля, абзаца и положения на странице остаются непроверенными или наследуемыми.

## Блок A. Списки и список источников — текущий срочный фикс

Цель: исправлять маркированные/нумерованные списки и список источников без изменения текста.

Шаги:

1. Распознавать `СПИСОК ИСПОЛЬЗОВАННЫХ/ИСПОЛЬЗУЕМЫХ ИСТОЧНИКОВ` как `bibliography_title`, даже если модель дала `body_text`.
2. Внутри библиографического контекста распознавать `Теоретическая часть` и `Практическая часть` как подзаголовки списка источников.
3. Распознавать источники по URL, году, ISBN, ГОСТ-маркерам, `//` и DOCX list metadata.
4. Применять к источникам единый Word numbering (`numPr`) без добавления цифр в текст.
5. Проверить, что все источники одного списка получают один `numId`, а не несколько разрозненных нумераций.

Verify:

- targeted pytest для postprocess/rule engine;
- real negative DOCX через `process_document(..., mode="fix")`;
- отчет содержит `bibliography_item` и `applied_fixes` включает `numbering`;
- все источники в выходном DOCX имеют один общий `numId`.

## Блок B. Заголовки — отдельная большая фаза

Цель: полноценно проверять и исправлять заголовки не только визуально, но и по Word-параметрам.

Параметры шрифта:

- font name;
- font size;
- bold/italic;
- underline;
- text color;
- all-caps/uppercase policy, если требуется методичкой.

Параметры абзаца:

- alignment;
- first line indent;
- left indent;
- right indent;
- space before;
- space after;
- line spacing;
- keep with next;
- keep lines together;
- page break before;
- widow/orphan control.

Шаги:

1. Расширить extractor style signature: добавить underline, color, right indent, keep flags и page break flags.
2. Сделать heading-specific regression fixtures: positive heading, negative heading with wrong intervals, negative heading with wrong font params.
3. Разделить heading checks на direct formatting и style inheritance.
4. Для наследуемых Heading styles сначала править стиль документа, а не перезаписывать каждый абзац прямыми значениями.
5. Добавить отдельный safe policy: direct heading fix разрешен только при regression-тесте, подтверждающем сохранение positive examples.
6. Добавить UI/report пояснение: `review` означает "визуально похоже, но Word-параметры не подтверждены".

Verify:

- positive DOCX examples remain `changed=0`;
- negative heading fixtures become closer to target signatures;
- no text changes;
- output DOCX keeps table of contents/list structure stable.

## Блок C. Методичка по нормоконтролю — future input source

> Note (2026-05-14, Phase 5 D-01): PPTX dropped from Phase 5 scope; PDF + DOCX cover the user's reality.

Цель: использовать методический документ по нормоконтролю как источник требований для профиля форматирования диплома.

Шаги:

1. Добавить загрузку PDF/DOCX методички как методического источника, не как проверяемого диплома.
2. Извлекать текст страниц/параграфов и таблиц требований.
3. Синтезировать черновик профиля поверх `gost_7_32_2017` и `gost_r_7_0_100_2018_bibliography`.
4. Показывать пользователю diff профиля перед сохранением.
5. Привязать профиль к Streamlit-сценарию форматирования диплома.

Verify:

- методичка не подменяет ГОСТ молча;
- все извлеченные правила имеют источник/страницу;
- спорные требования идут в `needs_manual_review`.
