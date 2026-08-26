# Chat Agent Platform

Локальный детерминированный слой исполнения, наблюдения, проверки и процедурной памяти вокруг **обычного ChatGPT Chat**.

## Что это сейчас

Архитектурная граница:

- **ordinary ChatGPT** — единственный текущий общий интеллект/планировщик: понимает цель, выбирает стратегию и новую адаптацию;
- **локальный deterministic Control Plane** — ведёт execution state/policy, authorization, ExpectedEffect verification, checkpoints, budgets и independent Finish Gate;
- локальные specialist/VLM-компоненты дают только bounded proposal/evidence;
- будущий локальный общий planner остаётся optional Track P.

Текущая реализация — в основном **Python + Node/MJS + PowerShell/Windows glue**. Rust не является текущей runtime-зависимостью и не должен использоваться как описание фактической реализации, пока это не подтверждается кодом.

## Текущий статус

На контрольной точке 2026-08-26:

```text
main = 20d06e8311ef65ee04b9a8a940c4f0d5725de0e0
       PR #106 — Browser observation foundation

active release-critical PR = #107
       production web_open final-state verification
```

Предыдущий code head PR #107 `08671b5a8763d589bcd16da69e8ed70bcb5f9509` прошёл 11/11 hosted workflows. После синхронизации документации ветка получает новый exact head, поэтому перед merge снова требуется зелёный hosted CI на финальном head и затем обязательный ordinary-Chat target-Windows physical Browser gate на том же head.

Следующий функциональный slice после принятия #107 — проверка postconditions для `web_interact` click/type.

Подробный live status: [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md).

Ранжированные проблемы и условия их закрытия: [`project-context/PROJECT_RISKS.md`](project-context/PROJECT_RISKS.md).

## Нормальный ChatGPT -> local path

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client on Windows
  -> secure semantic launcher
  -> direct stdio canonical semantic projection
  -> deterministic Control Plane / focused local capabilities
```

1MCP — **не обязательный промежуточный слой**. Он остаётся optional internal Extension Manager для будущих third-party MCP backends.

Текущий Chat-facing surface содержит ровно шесть действий:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Шесть — текущий проверенный контракт, а не вечный лимит. Любой будущий Windows/computer-use public surface требует отдельного schema/security/physical acceptance.

## Исполнение

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
              checkpoints / budgets
              independent Finish Gate
                         |
            +------------+------------+
            |            |            |
          Files        Browser      Windows
                        DOM/AX       native/UIA
                           \           /
                            selective vision
                                  |
                              bounded action
                                  |
                              re-observe
                                  |
                          PASS | FAIL | UNKNOWN
```

`Control Plane` — не второй LLM-мозг. Он исполняет уже выбранные bounded transitions и останавливается/эскалирует, когда нужна новая стратегия.

## Что уже принято

```text
Stage 26.3A canonical six-tool runtime          ACCEPTED / MERGED #92
Verification Kernel foundation                 MERGED #99
file/artifact kernel integration               PHYSICALLY ACCEPTED / MERGED #102
Browser observation foundation                 MERGED #106
```

В файловом production path уже доказаны kernel-gated transitions, independent Finish Gate и zero-overwrite behavior.

PR #107 переносит тот же принцип на `web_open`:

```text
fresh browser state BEFORE
 -> navigate
 -> fresh browser state AFTER
 -> ExpectedEffect
 -> PASS | FAIL | UNKNOWN
```

В первом slice redirects fail closed: доставленная навигация на другой final URL не считается verified success.

## Что делаем дальше

```text
finish PR #107 exact-head hosted + physical gate
 -> web_interact verification
 -> remaining Stage 26.3B Browser/Windows verification
 -> Stage 26.3C WorkingState + typed recovery + LoopGuard
 -> broad real-app physical coverage matrix
 -> Stage 26.4 candidate skills
 -> Stage 26.5 hybrid integration
 -> distribution / clean-user stable release
```

Broad real-app coverage специально поставлен как evidence gate, а не как новый архитектурный stage: задача — доказать работу на разных реальных приложениях до очередного расширения архитектуры.

## State-first computer use

```text
semantic/native state first
 -> selective visual evidence when structure is insufficient
 -> capability-aware bounded action
 -> fresh re-observation
 -> ExpectedEffect verification
 -> typed recovery + LoopGuard
 -> structured WorkingState
 -> independent Finish Gate
```

Это не screenshot-only agent. DOM/accessibility/UIA/native/app state используются раньше pixels, когда структура надёжна.

Environmental content из UI/DOM/messages/files/screenshots/tool output считается task data, а не authority над user intent или Control Plane policy.

## С чего продолжать разработку

Сначала resolve live GitHub state, затем читать:

1. [`AGENTS.md`](AGENTS.md)
2. [`project-context/START_HERE.md`](project-context/START_HERE.md)
3. [`project-context/CONTINUATION_CONTEXT.md`](project-context/CONTINUATION_CONTEXT.md)
4. [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md)
5. [`project-context/PROJECT_RISKS.md`](project-context/PROJECT_RISKS.md)
6. [`project-context/STAGE26_3B_VERIFICATION_KERNEL.md`](project-context/STAGE26_3B_VERIFICATION_KERNEL.md) while 26.3B is active
7. [`project-context/ARCHITECTURE.md`](project-context/ARCHITECTURE.md)
8. [`project-context/CONTROL_PLANE.md`](project-context/CONTROL_PLANE.md)
9. [`project-context/COMPUTER_USE_ARCHITECTURE.md`](project-context/COMPUTER_USE_ARCHITECTURE.md)
10. [`project-context/ROADMAP.md`](project-context/ROADMAP.md)

Когда prose расходится с live code/tests/CI/physical evidence, live evidence важнее документации.
