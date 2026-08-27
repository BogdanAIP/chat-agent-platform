# Chat Agent Platform

Локальный детерминированный слой исполнения, наблюдения, проверки и процедурной памяти вокруг **обычного ChatGPT Chat**.

## Что это сейчас

Архитектурная граница:

- **ordinary ChatGPT** — единственный текущий общий интеллект/планировщик: понимает цель, выбирает стратегию и адаптацию к новому состоянию;
- **локальный deterministic Control Plane** — ведёт execution state/policy, authorization, ExpectedEffect verification, checkpoints, recovery/budgets и independent Finish Gate;
- локальные specialist/VLM-компоненты дают только bounded proposal/evidence;
- будущий локальный общий planner остаётся optional Track P;
- будущий Agent Session / Delegation слой остаётся parallel Track M и не является текущим вторым planner/runtime authority.

Текущая реализация — в основном **Python + Node/MJS + PowerShell/Windows glue**. Rust не является текущей runtime-зависимостью и не должен использоваться как описание фактической реализации, пока это не подтверждается кодом.

## Текущий статус

На контрольной точке 2026-08-27:

```text
main = cc0fa3d1b7afe9d833334ae68482d2d3dca4b818
       PR #114 — Windows DesktopState shared-kernel verification
       ACCEPTED / MERGED

active release-critical PR = #115
       Windows/application real-task L3
       DRAFT / physical acceptance pending
```

Всегда проверяйте live GitHub перед работой: head #115 может измениться после этой записи.

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

Шесть — текущий проверенный контракт, а не вечный лимит. Любой будущий Windows/computer-use или Agent Session public surface требует отдельного schema/security/physical acceptance. Нельзя скрывать новые consequence classes за generic dispatch.

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
                recovery / budgets
                independent Finish Gate
                           |
         +-----------------+------------------+
         |                 |                  |
       Files             Browser            Windows
                          DOM/AX             native/UIA
                             \                /
                              selective vision
                                    |
                                bounded action
                                    |
                                re-observe
                                    |
                            PASS | FAIL | UNKNOWN

future parallel Track M:
  Agent Sessions / Delegation
  -> same Control Plane / verifier / Finish Gate authority boundary
```

`Control Plane` — не второй LLM-мозг. Он исполняет уже выбранные bounded transitions и останавливается/эскалирует, когда нужна новая стратегия.

## Что уже принято

```text
Stage 26.3A canonical six-tool runtime               ACCEPTED / MERGED #92
Verification Kernel foundation                      MERGED #99
file/artifact kernel integration                    PHYSICALLY ACCEPTED / MERGED #102
Browser observation foundation                      MERGED #106
production web_open verification                    PHYSICALLY ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                      MERGED #110
production web_interact verification                PHYSICALLY ACCEPTED / MERGED #111
Browser L3 real-task acceptance                     PHYSICALLY ACCEPTED / MERGED #113
Windows DesktopState shared-kernel verification     ACCEPTED / MERGED #114
```

Browser L3 #113 доказал natural-language Case Desk задачу с independent Finish Gate и non-target invariants для своего исторического scope. Из-за более позднего усиления source-provenance методологии перед закрытием Stage 26.3B требуется один representative Browser L3 repeat с clean-tree/source-byte binding.

PR #114 принял общий Windows `DesktopState -> ObservationRef -> ExpectedEffect -> PASS|FAIL|UNKNOWN` путь для recorded scope.

Текущий PR #115 строит поверх этого representative Windows/application L3 через bounded registered procedure и независимый внешний Finish Gate.

## Что делаем дальше

```text
finish PR #115 hosted + source/install/runtime-provenance-bound physical L3
 -> representative Browser L3 repeat under stronger provenance
 -> close remaining Stage 26.3B evidence
 -> Stage 26.3C WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport
 -> broad real-app physical coverage
 -> Stage 26.4 candidate skills
 -> Stage 26.5 hybrid integration
 -> distribution / clean-user stable release
```

Broad real-app coverage — evidence gate, а не отдельный архитектурный stage.

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

## Future Track M — Agent Sessions / Delegation

Track M остаётся future/parallel и не расширяет текущий runtime или шеституловый Chat-facing surface.

Ключевая модель:

```text
HarnessSession
Conversation / Chat
DelegationTask
MessageDelivery
ExecutionEnvironment
```

Эти сущности не смешиваются: session — не task, доставка сообщения — не completion, а project/worktree lifecycle — не session lifecycle.

Предпочтительный будущий route:

```text
official/project-owned harness API / local host protocol
 -> validated provider/session native route
 -> Browser Companion + DOM/accessibility
 -> reviewed GUI fallback
 -> ABSTAIN
```

Track M наследует существующие правила проекта: stable operation identity + reconciliation before unsafe retry, explicit ownership, minimum delegated worker authority, result correlation, bounded fan-out/LoopGuard и independent Finish Gate.

Подробно: [`project-context/CONVERSATION_BRIDGE_ARCHITECTURE.md`](project-context/CONVERSATION_BRIDGE_ARCHITECTURE.md) и ADR-035 в [`project-context/DECISIONS.md`](project-context/DECISIONS.md).

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
10. [`project-context/SECURITY_POLICY.md`](project-context/SECURITY_POLICY.md)
11. [`project-context/ROADMAP.md`](project-context/ROADMAP.md)
12. [`project-context/CONVERSATION_BRIDGE_ARCHITECTURE.md`](project-context/CONVERSATION_BRIDGE_ARCHITECTURE.md) for ADR-035 / future Track M
13. [`project-context/BROWSER_HARNESS_ARCHITECTURE.md`](project-context/BROWSER_HARNESS_ARCHITECTURE.md) for ADR-036
14. [`project-context/DOCUMENT_STATUS.md`](project-context/DOCUMENT_STATUS.md)

Когда prose расходится с live code/tests/CI/physical evidence, live evidence важнее документации.
