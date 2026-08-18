# Chat Agent Platform

Тонкий мост между **обычным ChatGPT Chat** и локальным Windows-компьютером через стандартный MCP. ChatGPT остаётся единственным интеллектом/планировщиком; локальная часть даёт ограниченные детерминированные действия, специализированное восприятие и, начиная со Stage 26, проектируемую процедурную память без второго агентного мозга.

Для продолжения разработки сначала читайте [`AGENTS.md`](AGENTS.md), [`project-context/START_HERE.md`](project-context/START_HERE.md), [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md) и активный Stage 26 контракт [`project-context/STAGE26_PROCEDURAL_MEMORY.md`](project-context/STAGE26_PROCEDURAL_MEMORY.md).

## Принятая основа

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> replaceable task-active MCP backends / focused adapters
  -> local capabilities
```

1MCP остаётся внутренней diagnostic/adaptive/aggregation инфраструктурой. Текущий публичный semantic surface содержит ровно пять действий:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

## Stage 25 / 25.1 / 25.2 — browser semantic + local vision foundation accepted

Stage 25 выбрал безопасный target-laptop baseline: llama.cpp `b10448/ad1de39e0`, LFM2.5-VL-450M F16 + F16 mmproj, CPU 8 threads, ctx 2048. Present-target baseline остаётся 3/5, потому что repeated-row/tiny специально не продвинуты.

Stage 25.1 добавил same-session screenshot/freshness/coordinate-action foundation, fail-closed authorization, focused vision runtime lifecycle, PID-bound listener verification, installed-layout parity, junction containment и dependency/security regressions.

Stage 25.2 слит в `main` через PR #77:

`2a410476ef849fd6d9c172703a004b1befcbcfb1`

Финальный target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`

Поведение `web_interact(click)`:

```text
fresh accessibility snapshot
  -> exact enabled button
       -> semantic click; VLM не запускается
  -> same-name buttons, ровно один enabled + disabled alternatives
       -> semantic click; VLM не запускается
  -> disabled / non-button / unresolved ambiguity
       -> ABSTAIN; VLM не запускается
  -> 0 exact candidates
       -> screenshot той же Playwright session
       -> reviewed local F16 text-labeled grounder
       -> deterministic authorization
       -> freshness proof
       -> single coordinate click OR ABSTAIN
```

`targetText` — semantic/visual anchor. Planner `target`, произвольная `instruction` и planner-supplied `kind` не могут переопределить visual authorization.

Финальный real-F16 target result с обычным Chrome открытым:

```text
semantic_hits = 2
visual_hits = 1
correct_abstains = 2
false_clicks = 0
errors = 0
semantic_cases_started_vlm = 0
acceptance_pass = true
minimum observed free physical RAM = 1.04 GB
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
```

## Stage 26 — Procedural Memory / Demo2Workflow

Следующий этап теперь не привязан к заранее выбранному списку программ. Цель — научить платформу сохранять и повторно использовать **проверенные способы работы**, а конкретные локальные возможности и программы выбирать по фактическим задачам.

Технический референс: официальный `Tencent/UI-Mate`, разобранный на pinned commit `d2b2e0aede83eeacfb1bc86f66503acbc4a6738a`. Мы не переносим UI-Mate как второго GUI-агента и не делаем 27B-модель обязательной. Берём принцип:

```text
successful trajectory
  -> raw structured evidence
  -> Demo Compiler
  -> coordinate-free versioned skill
  -> compact current-subtask guidance
  -> current state has priority
  -> verified completion
```

Процедурная память не является планировщиком и не авторизует действия сама по себе. Один успешный проход создаёт максимум candidate skill; promotion требует повторной проверяемой успешности.

Полный контракт: [`project-context/STAGE26_PROCEDURAL_MEMORY.md`](project-context/STAGE26_PROCEDURAL_MEMORY.md).

## Windows desktop surface — отдельный обязательный следующий слой

После procedural-memory foundation в roadmap явно сохранён **Windows desktop surface**: native/semantic observation first, screen/vision only where needed, reviewed keyboard/mouse execution and fail-closed behavior.

До его появления публичные tool names остаются текущими пятью. **Только после появления Windows desktop surface** отдельно решаем, нужно ли расширять public contract или можно сохранить ту же философию несколькими крупными семантическими действиями. Это должно быть отдельное архитектурное решение и ordinary-Chat acceptance, а не постепенное скрытое разрастание `semantic-projection`.

## Что это пока не означает

Платформа ещё не объявлена stable end-user product. Остаточные ограничения:

- repeated-row/tiny и automatic icon-only visual fallback не продвинуты;
- screenshot→click не атомарен;
- PID-bound loopback не является криптографической аутентификацией;
- DNS/rebinding/redirect isolation неполон;
- Python/model distribution ещё не release-grade;
- procedural-memory substrate, Windows desktop surface и human demonstration capture ещё не product-accepted;
- installer/update/repair/rollback/restart-recovery и clean-user release gate ещё впереди.

## Windows bootstrap/manager

```powershell
.\scripts\bootstrap-chat-platform.ps1
```

Менеджер/tray отвечает за lifecycle/configuration/diagnostics, а не за ИИ-планирование. Секрет tunnel-client хранится через Windows DPAPI.

## Безопасность

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Для browser vision:

```text
semantic structure first
  -> reviewed semantic miss only
  -> local perception
  -> deterministic authorization
  -> stale/uncertain/unpromoted -> ABSTAIN -> zero page mutation
```

Для procedural memory:

```text
remembered procedure = guidance/evidence
current observed state = authoritative
completion report = not sufficient without verifier evidence
```

Точная текущая точка: [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md). План: [`project-context/ROADMAP.md`](project-context/ROADMAP.md).

## License / Support

MIT License. Поддержка проекта добровольна и не влияет на лицензионные права.
