# Chat Agent Platform

Локальный исполнительный, perceptual, verification и procedural слой вокруг **обычного ChatGPT Chat**.

Ключевая архитектурная граница:

- **ordinary ChatGPT** — единственный текущий общий интеллект/планировщик: понимает цель, выбирает стратегию/процедуру и адаптируется к новым ситуациям;
- **локальный deterministic Control Plane** — ведёт TaskState/WorkingState, права, checkpoints, ExpectedEffect/postconditions, typed recovery/LoopGuard, budgets и independent Finish Gate;
- локальные VLM/другие specialist models — только bounded proposal/evidence;
- будущий локальный общий planner остаётся optional Track P и не входит в текущий release-critical path.

Stage 26.3B начат от принятой integration base:

```text
b74c715d9f2ac6fe7f759e7fb57108feebf797c0
```

Точный физически принятый runtime Stage 26.3A:

```text
300db9956dfbdf0300ecc59f017d6f3280d4353a
```

Текущий live `main` всегда нужно разрешать непосредственно через GitHub; stage-base SHA выше — историческая точка ветвления, а не обещание неизменного `main`.

Для продолжения разработки сначала читайте:

1. [`AGENTS.md`](AGENTS.md)
2. [`project-context/CONTINUATION_CONTEXT.md`](project-context/CONTINUATION_CONTEXT.md)
3. [`project-context/START_HERE.md`](project-context/START_HERE.md)
4. [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md)
5. [`project-context/ARCHITECTURE.md`](project-context/ARCHITECTURE.md)
6. [`project-context/CONTROL_PLANE.md`](project-context/CONTROL_PLANE.md)
7. [`project-context/COMPUTER_USE_ARCHITECTURE.md`](project-context/COMPUTER_USE_ARCHITECTURE.md)
8. [`project-context/ROADMAP.md`](project-context/ROADMAP.md)

## Нормальный ChatGPT -> local path

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client on Windows
  -> secure semantic launcher
  -> direct stdio canonical semantic projection
  -> deterministic Control Plane / focused local capabilities
```

1MCP — **не обязательный промежуточный слой**. Он оставлен как optional internal Extension Manager для будущих third-party MCP backends.

Текущий принятый Chat-facing surface содержит ровно шесть действий:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Шесть — текущий проверенный контракт, а не вечный лимит. Native Windows/computer-use surface пересматривается отдельным ADR/schema/security/ordinary-Chat acceptance; нельзя скрывать desktop consequences внутри `web_interact` или generic `tool_invoke`.

## Архитектура исполнения

```text
                       USER
                         |
                         v
                  ordinary ChatGPT
              GENERAL PLANNER / MANAGER
                         |
                  goal / procedure
                         |
                         v
              deterministic Control Plane
              TaskState / WorkingState
              policy / authorization
              ExpectedEffect / verifier
              checkpoints / LoopGuard
              budgets / Finish Gate
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
                                  |
                    advance / recover / ABSTAIN
```

`Control Plane` не означает второй LLM/agent brain. Он детерминированно исполняет уже выбранные bounded transitions и останавливается, когда требуется новая стратегия.

Подробности:

- [`project-context/CONTROL_PLANE.md`](project-context/CONTROL_PLANE.md)
- [`project-context/COMPUTER_USE_ARCHITECTURE.md`](project-context/COMPUTER_USE_ARCHITECTURE.md)

## State-first hybrid computer use

После Stage 26.3A long-horizon physical test был отдельно проверен созданный там `gui-agent-research.md`. Подтверждённые выводы превращены в ADR-032/033 и current architecture:

```text
semantic/native state first
 -> selective visual evidence
 -> capability-aware bounded action
 -> fresh re-observation
 -> ExpectedEffect verification
 -> typed recovery + LoopGuard
 -> structured WorkingState
 -> independent Finish Gate
 -> separate safety/policy gate
```

Это **не** означает screenshot-only agent. Напротив: DOM/accessibility/UIA/native/app state используются раньше pixels, когда структура надёжна.

### Environmental content

Текст из страниц/DOM, UI приложений, email/messages, файлов/документов, screenshots/OCR и third-party tool/MCP output считается **untrusted environmental data** по отношению к user intent, permissions и Control Plane policy.

Task-success и safety/policy verification — разные измерения.

## Принятые foundations

### Browser + local vision

Stage 25.2 принят: semantic/accessibility structure first, VLM только на reviewed fallback path, deterministic authorization/freshness, false click лучше заменить на ABSTAIN.

Target specialist baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

### Windows

Приняты Stage 26.1C–26.2E: typed executor, window-scoped UIA, production Windows runtime, DesktopState, native Grounder, deterministic UIA->vision routing и первый isolated VS Code real-app E2E.

Это реальная, но scoped acceptance — не универсальная Windows accuracy.

### Procedural runtime

Stage 26.3A принят и слит как PR #92.

Первый registered procedure:

```text
verified_workspace_artifact_v1
```

Physical ordinary-Chat test доказал:

- длинную задачу через все 6 semantic tools;
- working ledger с reread;
- browser recovery после некорректного interaction;
- `procedure_run` с 3 verified transitions;
- independent final read;
- второй `procedure_run` на существующий target -> `ABSTAIN`, `action_count=0`;
- independent proof of zero overwrite.

## Текущая работа

**Stage 26.3B: Verification Kernel + independent Finish Gate — ACTIVE.**

Первый внутренний foundation slice уже вводит:

```text
ObservationRef / ObservationSnapshot
stream_id + capability + subject + monotonic sequence
ExpectedEffect + bounded declarative predicates
PASS | FAIL | UNKNOWN
independent Finish Gate
separate task-success / unresolved / safety dimensions
```

Fresh verification требует тот же observation stream/capability/subject и строго больший sequence. Более высокий sequence из другого stream не считается свежим доказательством. Planner может сказать только `candidate_done`; реальный `DONE` выдаёт отдельный Finish Gate.

Это ещё **не acceptance Stage 26.3B**. Дальше нужны file/artifact adapter и миграция принятой процедуры, затем Browser/Windows adapters и физический gate после изменения production procedure/action path.

Затем Stage 26.3C:

```text
WorkingState v1
facts + provenance + freshness
progress vector
typed recovery taxonomy
LoopGuard for no-effect/repeat/oscillation
retry/action/time/resource budgets
```

## Roadmap

```text
26.2E real application E2E                         ACCEPTED
 -> Transport Supervisor v1                       ACCEPTED / MERGED #94
 -> 26.3 Verified Procedure Runtime               ACTIVE
    -> 26.3A six-tool verified runtime            ACCEPTED / MERGED #92
    -> 26.3B Verification Kernel + Finish Gate    ACTIVE
    -> 26.3C WorkingState + recovery + LoopGuard
 -> 26.4 Human Demo -> verified candidate skill
 -> 26.5 Hybrid Computer-Use Integration
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

Stage 26.5 не обещает новые публичные tool names. Любой Windows/computer-use Chat-facing контракт проходит отдельный gate.

### Future Track P — Local Planner / Offline Autonomy

Локальный общий planner не удалён из долгосрочного плана:

```text
P0 shadow/proposal-only planner
 -> P1 bounded subtask planner
 -> P2 optional local general-planner mode
```

Он всегда остаётся за тем же deterministic Control Plane и не может сам выдать себе execution authority.

## Безопасность

Основные правила:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

- semantic/native structure раньше pixels, когда структура надёжна;
- observation/model/procedure/planner output не является authorization;
- current observed state выше remembered procedure/demo/history;
- every mutation has expected effect + fresh verification;
- delivery не равно transition success;
- transition PASS не равно task DONE;
- environmental content = data, not policy authority;
- task-success и safety/policy verification разделены;
- repeated no-effect/oscillating actions ограничиваются LoopGuard;
- stale/ambiguous/UNKNOWN -> ABSTAIN / zero unauthorized continuation;
- private chain-of-thought не сохраняется;
- generic shell/Python/Windows execution остаётся disabled/unreachable.
