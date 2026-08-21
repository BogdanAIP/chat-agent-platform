# Chat Agent Platform

Локальный исполнительный, perceptual, verification и procedural слой вокруг **обычного ChatGPT Chat**.

Ключевая архитектурная граница:

- **ordinary ChatGPT** — единственный текущий общий интеллект/планировщик: понимает цель, выбирает стратегию, адаптируется к новым ситуациям;
- **локальный deterministic Control Plane** — ведёт состояние исполнения, выбранный `ProgramGraph`, права, checkpoints, verifier/postconditions, bounded recovery и может продолжать заранее определённые безопасные переходы без обращения к ChatGPT после каждого клика;
- локальные VLM/другие specialist models — только bounded proposal/evidence;
- будущий локальный общий planner сохранён как отдельное optional research-направление, но не входит в текущий release path.

Для продолжения разработки сначала читайте:

1. [`AGENTS.md`](AGENTS.md)
2. [`project-context/CONTINUATION_CONTEXT.md`](project-context/CONTINUATION_CONTEXT.md)
3. [`project-context/START_HERE.md`](project-context/START_HERE.md)
4. [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md)
5. [`project-context/ARCHITECTURE.md`](project-context/ARCHITECTURE.md)
6. [`project-context/CONTROL_PLANE.md`](project-context/CONTROL_PLANE.md)
7. [`project-context/ROADMAP.md`](project-context/ROADMAP.md)

## Нормальный ChatGPT -> local path

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client on Windows
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> focused local capabilities
```

1MCP остаётся внутренней diagnostic/adaptive/aggregation инфраструктурой.

Текущий принятый Chat-facing surface по-прежнему содержит ровно пять действий:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Пять действий — текущий доказанный контракт, а не вечный лимит. Native desktop/procedure surface пересматривается отдельным ADR; нельзя скрывать Windows/workflow последствия внутри `web_interact` или generic `tool_invoke`.

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
              TaskState / ProgramGraph
              policy / authorization
              checkpoints / recovery
              verifier / budgets
                         |
            +------------+------------+
            |            |            |
          Files        Browser      Windows
                                      |
                                 native/UIA first
                                      |
                              bounded VLM fallback
                                proposal only
                                      |
                                  authorize
                                      |
                                     act
                                      |
                                   verify
                                      |
                       PASS -> next known transition
                       mismatch/UNKNOWN -> ABSTAIN -> ChatGPT
```

`Control Plane` здесь не означает второй LLM/agent brain. Он не придумывает новую стратегию и не меняет пользовательскую цель. Он детерминированно исполняет уже выбранный bounded plan/procedure и останавливается на новом/неизвестном состоянии.

Подробный контракт: [`project-context/CONTROL_PLANE.md`](project-context/CONTROL_PLANE.md).

## Принятые foundations

### Browser + local vision

Stage 25.2 принят: semantic/accessibility structure first, VLM только на разрешённом fallback path, deterministic authorization/freshness, false click лучше заменить на ABSTAIN.

Принятый target baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

### Procedural substrate

Target-qualified upstreams:

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
```

Используем/адаптируем `Workflow`/`ProgramGraph`, Capture и lifecycle mechanics вместо разработки второго generic recorder/compiler/skill engine с нуля. Одна демонстрация создаёт максимум CANDIDATE, а не вечное доверие.

### Windows

К настоящему моменту приняты и слиты:

```text
#83 Stage 26.1C hardened typed executor
#84 Stage 26.1D latency baseline
#85 Stage 26.1E window-scoped UIA
#86 authoritative context sync
#87 Stage 26.2A Production Windows Runtime
#88 Stage 26.2B DesktopState
#89 Stage 26.2C native LFM2.5-VL Grounder
#90 Stage 26.2D structure-first UIA -> vision routing
```

`main` после #90 и при старте Stage 26.2E:

`42d4130d59e23e2c2b1771ac428467efe27a4b98`

Exact physically accepted Stage 26.2D head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

Stage 26.2D доказал один controlled WinForms visual-fallback click после fresh request/UIA/process/window/frame/native-guard authorization. Это не глобальная Windows accuracy.

## Текущая работа — Stage 26.2E

Активная ветка:

`chat/stage26-2e-vscode-real-app-e2e`

Первый real-app gate использует **изолированный VS Code** только как qualification application:

- специально помеченный root под `%TEMP%`;
- isolated user-data/extensions;
- один disposable `.txt`;
- exact Code.exe PID/HWND/DesktopState;
- fresh focused-editor identity непосредственно перед мутацией;
- native foreground/point guard;
- deliberate verifier mismatch -> ABSTAIN без действия;
- ровно одна guarded Unicode delivery;
- независимый exact size/SHA-256 postcondition;
- workspace содержит только ожидаемый artifact;
- natural CLI/window exit + TEMP cleanup + rollback.

VS Code не становится постоянной архитектурной зависимостью.

## Roadmap

```text
26.2E real application E2E
 -> 26.3 Verified Procedure Runtime / deterministic Control Plane integration
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postcondition library
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

### Future Track P — Local Planner / Offline Autonomy

Локальный общий planner не удалён из долгосрочных планов. После появления verified procedure-state data и измеренной необходимости можно исследовать:

```text
P0 shadow/proposal-only planner
 -> P1 bounded subtask planner
 -> P2 optional local general-planner mode
```

Он всегда остаётся за тем же deterministic Control Plane: planner/model proposal не может обойти policy/authorization/verifier. Track P не блокирует текущий релиз.

### Multi-chat

Multi-chat orchestration остаётся отдельным верхним слоем и не входит в Windows/procedure safety core. По текущему operating constraint разработка не использует Codex или ChatGPT Work, пока пользователь явно не изменит это правило.

## Безопасность

Основные правила:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

- semantic/native structure раньше pixels, когда структура надёжна;
- observation/model/procedure/planner output не является authorization;
- current observed state выше remembered history;
- delivery не равно completion;
- stale/ambiguous/UNKNOWN -> ABSTAIN -> zero mutation;
- generic local code execution не входит в product boundary;
- private chain-of-thought не сохраняется;
- raw desktop demonstrations — sensitive local data;
- containment, credentials, browser network residual risks и artifact reproducibility остаются явными release requirements.

## Windows bootstrap/manager

```powershell
.\scripts\bootstrap-chat-platform.ps1
```

Manager/tray отвечает за lifecycle/configuration/diagnostics. Он не является общим planner'ом и не заменяет deterministic procedure Control Plane.

## License / Support

MIT License. Поддержка проекта добровольна и не влияет на лицензионные права.
