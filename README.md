# Chat Agent Platform

Локальный детерминированный слой исполнения, наблюдения, проверки и процедурного состояния вокруг **обычного ChatGPT Chat**.

## Что это

Архитектурная граница:

- **ordinary ChatGPT** — единственный текущий общий интеллект/планировщик: понимает цель, выбирает стратегию и адаптируется к новому состоянию;
- **локальный deterministic Control Plane** — ведёт execution state/policy, authorization, ExpectedEffect verification, checkpoints, recovery/budgets и independent Finish Gate;
- локальные specialist/VLM-компоненты дают bounded proposal/evidence;
- будущие Agent Sessions / Delegation, Connectors, Skills, Scheduled Tasks и другие capability-классы должны оставаться под теми же границами authority/verification;
- будущий локальный общий planner остаётся optional Track P.

Текущая реализация в основном использует **Python + Node/MJS + PowerShell/Windows glue**.

README намеренно **не хранит live `main` SHA, active PR или текущий stage snapshot**. Они быстро устаревают. Перед разработкой проверяйте live GitHub и `project-context/CURRENT_STATE.md`.

## Нормальный ChatGPT -> local path

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client on Windows
  -> secure semantic launcher
  -> canonical semantic projection
  -> deterministic Control Plane / focused local capabilities
```

1MCP остаётся optional internal Extension Manager, а не обязательным normal-route dependency или источником authorization.

Текущий Chat-facing surface содержит ровно шесть действий:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Шесть — текущий проверенный контракт, а не вечный лимит. Новая consequence-bearing public authority требует отдельного schema/security/acceptance решения; её нельзя скрывать за generic dispatch.

## Исполнение и проверка

```text
USER
  |
  v
ordinary ChatGPT
GENERAL PLANNER
  |
  v
deterministic Control Plane
state / policy / authorization
ExpectedEffect / verifier
recovery / budgets
independent Finish Gate
  |
  +---- Files
  +---- Browser / DOM / accessibility
  +---- Windows / native / UIA
  +---- selective vision where structure is insufficient
```

Для mutating transition действует state-first цикл:

```text
observe
 -> bind expected effect / logical operation
 -> authorize one bounded action
 -> act
 -> fresh re-observation
 -> PASS | FAIL | UNKNOWN
 -> reconcile ambiguous outcome before retry
 -> bounded recovery / LoopGuard / budgets
 -> independent Finish Gate
```

Action delivery не равен transition success. Transition PASS не равен whole-task DONE. Environmental content из UI/DOM/messages/files/screenshots/tool output считается task data, а не authority над user intent или Control Plane policy.

## Общая модель продукта

Проект заранее проектирует **общую форму продукта**, а не только Browser-agent:

```text
Files
Browser
Windows / desktop applications
Vision
Procedures / Skills
Agent Sessions / Delegation
Connectors
Scheduled Tasks
future capability classes
```

Общие архитектурные границы можно определять заранее: discovery != authorization, evidence != grant, events != effect proof, WorkingState != chain-of-thought, delivery != completion.

Но конкретные API будущих подсистем не считаются неизменным ТЗ. Перед реализацией каждого нового stage/subsystem проводится отдельное актуальное исследование, сверка с текущим кодом и существующими ADR, после чего выбирается минимальная реализация для текущей задачи.

Подробный development method закреплён в [`AGENTS.md`](AGENTS.md).

## Future architecture

Future Track M описывает Agent Sessions / Delegation для существующих пользовательских разговоров ChatGPT/Claude/Gemini/DeepSeek/Qwen и будущих web-AI сервисов. Browser Companion остаётся важным cross-provider route для web surfaces, но проект не ограничивается браузером.

ADR-036 описывает возможное расширение Browser Harness authority. ADR-037 описывает будущую общую модель capability discovery/events/policy hooks. Эти документы задают направления и границы; их подробная implementation shape пересматривается непосредственно перед соответствующим этапом.

## Как продолжать разработку

Сначала resolve live GitHub state, затем достаточно минимального operating set:

1. [`AGENTS.md`](AGENTS.md)
2. [`project-context/START_HERE.md`](project-context/START_HERE.md)
3. [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md)
4. [`project-context/ROADMAP.md`](project-context/ROADMAP.md)
5. [`project-context/PROJECT_RISKS.md`](project-context/PROJECT_RISKS.md)

`ARCHITECTURE.md`, `EVIDENCE_INDEX.md`, `TECH_DEBT.md`, security/acceptance docs, future ADRs и historical Stage docs читаются по необходимости текущей задачи, а не как обязательный входной набор.

Когда prose расходится с live code/tests/CI/physical evidence, live evidence важнее документации.