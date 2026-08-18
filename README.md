# Chat Agent Platform

Тонкий мост между **обычным ChatGPT Chat** и локальным Windows-компьютером через стандартный MCP. ChatGPT остаётся единственным интеллектом/планировщиком; локальная часть даёт ограниченные детерминированные действия, специализированное восприятие и процедурную память без второго агентного мозга.

Для продолжения разработки сначала читайте [`AGENTS.md`](AGENTS.md), [`project-context/START_HERE.md`](project-context/START_HERE.md), [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md), [`project-context/STAGE26_1A_OPENADAPT_QUALIFICATION.md`](project-context/STAGE26_1A_OPENADAPT_QUALIFICATION.md) и [`project-context/STAGE26_PROCEDURAL_MEMORY.md`](project-context/STAGE26_PROCEDURAL_MEMORY.md).

## Принятая основа

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> replaceable task-active backends / focused adapters
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

Stage 25.1 добавил same-session screenshot/freshness/coordinate-action foundation, fail-closed authorization, focused vision runtime lifecycle и security/runtime hardening.

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

`targetText` — semantic/visual authorization anchor. Planner `target`, произвольная `instruction` и planner-supplied `kind` не могут переопределить visual authorization.

Финальный real-F16 target result с обычным Chrome открытым: 2 semantic HIT, 1 visual HIT, 2 correct ABSTAIN, 0 false clicks, 0 errors; runtime остановлен после теста, Chrome остался запущен.

## Stage 26 — Procedural Memory

Цель — научить платформу безопасно переиспользовать **проверенные способы работы**, не превращая локальную часть во второго агента и не делая слепой replay макросов.

### UI-Mate — архитектурный референс

Официальный `Tencent/UI-Mate` показал полезный паттерн:

```text
rich demonstration trajectory
        ↓
compact current-subtask guidance
        ↓
current live state remains authoritative
```

Мы не переносим UI-Mate как второго GUI-агента и не делаем его 9B/27B модели обязательными.

### OpenAdapt — квалифицированный procedural-engine кандидат

После более широкого исследования выяснилось, что значительную часть ранее запланированной собственной разработки уже реализует OpenAdapt.

На реальном Windows target проверены exact pins:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

Target-tested qualification-code HEAD:

`f8e8f606db845821b8fa24c09f9032015fb0e79e`

Результат:

```text
Python 3.12.10
exact source commit verification = PASS
PHASE_B_PASS=True
PHASE_C_TUTORIAL_PASS=True
PROBE_ERROR=<null>
ERROR=<null>
TEST_EXIT_CODE=0
Chrome processes before/after = 15/15
```

То есть OpenAdapt Flow/Capture реально устанавливаются из закреплённых исходников, а модельно-независимый tutorial проходит `record/compile/replay/VERIFIED` path на целевой машине.

Текущие решения:

- Flow `Workflow`/`ProgramGraph` compiler/IR — **использовать как upstream substrate**, а не писать аналог с нуля;
- `SkillLibrary`/learn/teach — **адаптировать**, потому что у нас остаётся более строгая candidate-first trust policy;
- Capture — следующим шагом проверить на реальной bounded Windows recording fixture, а не писать свой recorder заранее;
- Windows backend/agent — отдельно пройти security A/B;
- локальный LFM2.5-VL F16 — позже подключить через узкий proposal-only OpenAdapt `Grounder` seam;
- OpenAdapt Desktop — использовать как референс для будущего installer/sidecar/cockpit, но не как текущий runtime baseline.

OpenAdapt пока **не встроен** в production `semantic-projection` и не меняет публичные Chat tools.

## Следующий шаг — Stage 26.1B Windows Capture qualification

На безвредном тестовом окне нужно доказать:

```text
record start/stop
  -> window scope
  -> click/type/key/scroll capture
  -> UIA evidence where available
  -> convert to Flow recording
  -> compile/replay or bounded refusal
  -> zero false/unrelated-window actions
  -> local artifact containment
  -> cleanup
```

Конкретные локальные программы заранее в roadmap не фиксируются — выбираются позже по реальным задачам.

## Windows desktop surface — отдельный обязательный Stage 26.3

После qualification A/B должен появиться product-level **Windows desktop surface**:

```text
native/deterministic UI observation first
  -> screen capture where needed
  -> bounded local vision where needed
  -> reviewed keyboard/mouse action
  -> verification / ABSTAIN
```

Этот этап явно записан в roadmap и не должен потеряться.

**Только после появления Windows desktop surface** отдельно решаем, нужно ли расширять public contract или можно сохранить ту же философию несколькими крупными семантическими действиями.

До этого публичные tool names остаются текущими пятью.

## Что это пока не означает

Платформа ещё не объявлена stable end-user product. Остаточные ограничения:

- repeated-row/tiny и automatic icon-only visual fallback не продвинуты;
- screenshot→click не атомарен;
- PID-bound loopback не является криптографической аутентификацией;
- DNS/rebinding/redirect isolation неполон;
- Python/model/OpenAdapt distribution ещё не release-grade;
- raw human demonstration retention/redaction/encryption policy не принят;
- OpenAdapt Capture ещё не прошёл real Windows capture gate;
- Windows executor security boundary и F16 Grounder adapter ещё не приняты;
- Windows desktop surface и human demonstration transfer ещё не product-accepted;
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
model/grounder proposal = not authorization
completion = verifier/effect evidence required
```

Точная текущая точка: [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md). План: [`project-context/ROADMAP.md`](project-context/ROADMAP.md).

## License / Support

MIT License. Поддержка проекта добровольна и не влияет на лицензионные права.
