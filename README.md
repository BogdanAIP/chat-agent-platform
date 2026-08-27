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
main = 500bfc646a14892ea655369c20c8f8d725fccfeb
       PR #117 — CAP-M0 Verification Kernel mutation pilot
       ACCEPTED / MERGED

PR #115 — Windows/application real-task L3
       PHYSICALLY ACCEPTED / MERGED
       merge = e965e7b5466446c9f065f6b57f438f25168bed9a

active architecture/docs PR = #116
       Track M Agent Session / Delegation + ADR-037
       no runtime/public-tool authority
```

Всегда проверяйте live GitHub перед работой: `main` и PR heads могут измениться после этой записи.

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

Шесть — текущий проверенный контракт, а не вечный лимит. Любой будущий Windows/computer-use, Agent Session, project/environment или local-execution public surface требует отдельного schema/security/physical acceptance. Нельзя скрывать новые consequence classes за generic dispatch.

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
Windows DesktopState shared-kernel verification     PHYSICALLY ACCEPTED / MERGED #114
Windows/application real-task L3                    PHYSICALLY ACCEPTED / MERGED #115
CAP-M0 Verification mutation pilot                  ACCEPTED / MERGED #117
```

Browser L3 #113 доказал natural-language Case Desk задачу с independent Finish Gate и non-target invariants для своего исторического scope. Из-за более позднего усиления source-provenance методологии перед закрытием Stage 26.3B требуется один representative Browser L3 repeat с clean-tree/source-byte binding.

PR #114 принял общий Windows `DesktopState -> ObservationRef -> ExpectedEffect -> PASS|FAIL|UNKNOWN` путь для recorded scope.

PR #115 затем доказал representative Windows/application L3 через bounded registered procedure и независимый frozen Finish Gate. Финальный exact head `5ae5d5ac52f391b1a58662e94a976c6ab8d48c62` дал `STAGE26_3B_WINDOWS_APPLICATION_L3=PASS` и `EXTERNAL_FINISH_GATE=DONE`.

PR #117 добавил curated mutation assurance для Verification Kernel: 12/12 критических mutants должны быть `KILLED` только named detector assertion failure, с exact mutated-source binding; production verifier при этом не мутируется.

## Что делаем дальше

```text
finish/review PR #116 documentation replay
 -> representative Browser L3 repeat under stronger provenance
 -> close remaining Stage 26.3B evidence
 -> Stage 26.3C WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport
 -> broad real-app physical coverage
 -> bounded OpenAdapt integration spike
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
 -> typed recovery/reconciliation + LoopGuard
 -> structured WorkingState
 -> independent Finish Gate
```

Это не screenshot-only agent. DOM/accessibility/UIA/native/app state используются раньше pixels, когда структура надёжна.

Environmental content из UI/DOM/messages/files/screenshots/tool/worker output считается task data, а не authority над user intent или Control Plane policy.

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

Эти сущности не смешиваются: session — не task, доставка сообщения — не completion, project/worktree lifecycle — не session lifecycle.

Продуктовый центр Track M — authenticated web-AI conversations: существующие пользовательские чаты ChatGPT/Claude/Gemini/DeepSeek/Qwen и будущих web AI services.

Предпочтительный будущий route определяется для конкретного target surface:

```text
reviewed official/project-owned harness API / local host protocol when available
 -> validated provider/session native route
 -> Browser Companion + DOM/accessibility for web-chat surfaces
 -> reviewed GUI fallback
 -> ABSTAIN
```

Browser Companion остаётся основным cross-provider adapter family для web-chat. Native/harness interfaces — optional stronger routes там, где они действительно доступны и дают более надёжную identity/state/effect семантику.

Track M наследует существующие правила проекта: stable operation identity + reconciliation before unsafe retry, explicit ownership, minimum delegated worker authority, result correlation, bounded fan-out/LoopGuard и independent Finish Gate. Initial nested spawn depth = 1.

Подробно: [`project-context/CONVERSATION_BRIDGE_ARCHITECTURE.md`](project-context/CONVERSATION_BRIDGE_ARCHITECTURE.md) и ADR-035 в [`project-context/DECISIONS.md`](project-context/DECISIONS.md).

## Future ADR-037 — capability / event / policy substrate

```text
CapabilityRegistry
  = semantic discovery / availability / health / trust metadata
  != authorization / generic dispatch

TypedEventBus
  = typed lifecycle events / observation triggers
  != effect-success proof / WorkingState

PolicyHooks
  = registered bounded deterministic handlers
  != second planner / arbitrary shell-Python
```

Events могут инициировать свежую authoritative re-observation, но сами не доказывают внешний эффект. Hook output не может расширять grants или превращать `FAIL/UNKNOWN` в `PASS`, а `NOT_DONE/UNKNOWN` — в `DONE`.

Подробно: [`project-context/CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md`](project-context/CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md) и ADR-037 в [`project-context/DECISIONS.md`](project-context/DECISIONS.md).

## CAP-M0 mutation assurance

[`project-context/MUTATION_ASSURANCE.md`](project-context/MUTATION_ASSURANCE.md) фиксирует первый guarantee-oriented mutation layer.

Основной metric:

```text
Verification Guarantee Coverage
 = killed curated mutants / total curated mutants
```

`KILLED` означает конкретное падение named detector assertion на mutated target; harness/import/runtime/source-binding ошибки — это `ERROR`, а не ложный kill.

## С чего продолжать разработку

Сначала resolve live GitHub state, затем читать:

1. [`AGENTS.md`](AGENTS.md)
2. [`project-context/START_HERE.md`](project-context/START_HERE.md)
3. [`project-context/CONTINUATION_CONTEXT.md`](project-context/CONTINUATION_CONTEXT.md)
4. [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md)
5. [`project-context/PROJECT_RISKS.md`](project-context/PROJECT_RISKS.md)
6. [`project-context/STAGE26_3B_VERIFICATION_KERNEL.md`](project-context/STAGE26_3B_VERIFICATION_KERNEL.md) while 26.3B is active
7. [`project-context/SOURCE_PROVENANCE_ACCEPTANCE.md`](project-context/SOURCE_PROVENANCE_ACCEPTANCE.md)
8. [`project-context/REAL_TASK_ACCEPTANCE.md`](project-context/REAL_TASK_ACCEPTANCE.md)
9. [`project-context/ARCHITECTURE.md`](project-context/ARCHITECTURE.md)
10. [`project-context/CONTROL_PLANE.md`](project-context/CONTROL_PLANE.md)
11. [`project-context/COMPUTER_USE_ARCHITECTURE.md`](project-context/COMPUTER_USE_ARCHITECTURE.md)
12. [`project-context/SECURITY_POLICY.md`](project-context/SECURITY_POLICY.md)
13. [`project-context/ROADMAP.md`](project-context/ROADMAP.md)
14. [`project-context/CONVERSATION_BRIDGE_ARCHITECTURE.md`](project-context/CONVERSATION_BRIDGE_ARCHITECTURE.md) for ADR-035 / future Track M
15. [`project-context/CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md`](project-context/CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md) for ADR-037
16. [`project-context/BROWSER_HARNESS_ARCHITECTURE.md`](project-context/BROWSER_HARNESS_ARCHITECTURE.md) for ADR-036
17. [`project-context/MUTATION_ASSURANCE.md`](project-context/MUTATION_ASSURANCE.md)
18. [`project-context/DOCUMENT_STATUS.md`](project-context/DOCUMENT_STATUS.md)

Когда prose расходится с live code/tests/CI/physical evidence, live evidence важнее документации.
