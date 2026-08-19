# Chat Agent Platform

Локальный исполнительный, perceptual и процедурный слой вокруг **обычного ChatGPT Chat**. ChatGPT остаётся единственным общим интеллектом/планировщиком; локальная часть даёт ограниченное наблюдение, безопасные действия, проверку результата, специализированное локальное восприятие и проверяемую процедурную память без второго автономного агентного мозга.

Для продолжения разработки сначала читайте [`AGENTS.md`](AGENTS.md), [`project-context/START_HERE.md`](project-context/START_HERE.md), [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md), [`project-context/ROADMAP.md`](project-context/ROADMAP.md) и [`project-context/ARCHITECTURE.md`](project-context/ARCHITECTURE.md).

## Принятая основа

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client on Windows
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> replaceable focused local capabilities
```

1MCP остаётся внутренней diagnostic/adaptive/aggregation инфраструктурой.

Текущий публичный semantic surface содержит ровно пять действий:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Это текущий принятый контракт, а не вечное ограничение. Решение по честным desktop/procedure tools принимается отдельным ADR только после появления production Windows desktop surface.

---

## Browser semantic + local vision — принято

Для браузера принят порядок:

```text
semantic/accessibility structure first
  -> точный безопасный semantic target
       -> semantic action; VLM выключен
  -> disabled / unpromoted / unresolved ambiguity
       -> ABSTAIN; VLM выключен
  -> разрешённый zero-exact-candidate path
       -> screenshot той же session
       -> local LFM2.5-VL F16 proposal
       -> deterministic authorization + freshness
       -> one coordinate action OR ABSTAIN
```

Принятый локальный visual baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16
F16 mmproj
CPU 8 threads
ctx 2048
```

Stage 25.2 real target: 2 semantic HIT, 1 visual HIT, 2 correct ABSTAIN, 0 false clicks, 0 errors.

---

## Stage 26 — Windows capability + procedural memory

После OpenAdapt/UI-Mate исследования проект не строит собственный generic recorder/compiler/skill engine с нуля.

Target-qualified upstreams:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

Используем/адаптируем:

- Flow `Workflow` / `ProgramGraph` как процедурный substrate;
- Capture как источник демонстрационных траекторий;
- `SkillLibrary`/learn/teach internals под более строгой project candidate-first trust policy;
- typed OpenAdapt Windows backend/agent как исполнительный substrate после hardening qualification.

Одна демонстрация никогда не означает автоматическое вечное доверие.

---

## Stage 26.1B — Windows Capture принят

Bounded Windows Capture квалифицирован на реальном target.

Accepted qualification head:

`7a9daa9329d81994833c22b4ca2e321927527dcc`

Доказаны bounded capture/structural evidence, Flow compile path, отсутствие foreign structural-window actions и clean local artifact containment/refusal behavior.

---

## Stage 26.1C — typed Windows executor принят на target

PR #83 exact accepted head:

`4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`

Доказаны:

```text
loopback-only + auth
legacy arbitrary exec disabled/unreachable in qualification configuration
typed bounded actions
stale frame/context refusal
focus checks
UIA uniqueness
fingerprint-bound structural actions
guarded keyboard/pointer/scroll
layout-independent Unicode typing
FALSE_ACTION_COUNT=0
UNRELATED_WINDOW_ACTION_COUNT=0
```

Писать новый собственный actuator без измеренного blocker сейчас не нужно.

---

## Stage 26.1D / 26.1E — главный Windows UIA bottleneck найден и устранён

Stage 26.1D измерил warm action sequence:

```text
p50 ~183.6 s
p95 ~185.6 s
```

Причина — desktop-wide UIA traversal от `GetRootControl()` с повторным полным разрешением перед структурным действием.

Stage 26.1E заменил qualification path на:

```text
expected PID
 -> bounded Win32 HWND enumeration
 -> same-process HWND filter
 -> exact UIA window
 -> native FindAll only inside that window
 -> existing candidate/fingerprint semantics
```

PR #85 exact physically accepted head:

`66390aca1dadf57c4f11568ec311ad6fcdbd7596`

Physical result:

```text
WINDOW_SCOPED_FIND_CALLS=97
WINDOW_NAME_MATCH_COUNT=97
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
FALSE_ACTION_COUNT=0
UNRELATED_WINDOW_ACTION_COUNT=0

p50=3323.570 ms
p95=3720.061 ms
p50 speedup=55.244x
p95 speedup=49.883x
```

Важно: 97/97 — это точность **контролируемого WinForms fixture и exercised role+name path**, а не заявление о 100% точности произвольного Windows GUI.

---

## Текущее состояние веток

На момент этой документационной синхронизации `main` ещё не содержит C/D/E. Они находятся в stacked PR chain:

```text
#83 -> #84 -> #85
```

Эта docs-ветка создана от exact accepted #85 head. Сначала нужно безопасно land #83, retarget/verify #84, затем retarget/verify #85. Только после этого docs PR retarget на `main` и повторная проверка diff/CI.

Нельзя просто слить downstream stacked PR вслепую.

---

## Следующий основной инженерный этап — Production Windows Runtime

После landing qualification stack нужно перенести доказанные механизмы из `scripts/stage26-*` в нормальный maintained runtime:

```text
runtime/windows/
  session identity
  process/application identity
  PID/HWND exact-window binding
  window-scoped UIA
  typed actuation
  stale/focus/fingerprint safety
  verifier foundation
  lifecycle / health / logging
```

Базовый runtime обязан проверять эффект:

```text
observe before
 -> authorize
 -> act
 -> observe after
 -> PASS | FAIL | UNKNOWN
```

`action delivered != task completed`.

---

## Затем

```text
DesktopState / observation
 -> native desktop LFM2.5-VL Grounder
 -> semantic/UIA -> vision routing + adversarial accuracy suite
 -> one real medium-complexity application E2E
 -> Verified Procedure Runtime
 -> Human Demo -> transferable candidate skill
 -> distribution/release
```

Первое реальное приложение выбирается по задаче и измеримому тесту, а не навсегда фиксируется в roadmap. VS Code, OriginPro и Reaper — только возможные кандидаты.

---

## Что не является release blocker

### Tiny local reasoner

TRM/STARM/FPRM/small-model experiments возможны позже, когда появится verified procedure-state dataset и измеренная необходимость уменьшить ChatGPT escalation/decision latency. Это optional research track, не prerequisite для Stage 27/28.

### Multi-Chat / Codex orchestration

Отдельный верхний слой может координировать ChatGPT/Codex chats для research/code/review, но он не входит в Windows executor safety core и не блокирует релиз основной платформы.

---

## Безопасность

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Основные правила:

- semantic/native structure раньше pixels, когда структура надёжна;
- VLM только предлагает target evidence;
- procedure memory только даёт bounded guidance/evidence;
- current observed state выше remembered history;
- stale/ambiguous/unknown -> ABSTAIN -> zero mutation;
- generic local exec отсутствует из product boundary;
- private chain-of-thought никогда не сохраняется в procedural memory;
- raw desktop demonstrations считаются sensitive local data;
- Windows link/junction containment, credential isolation и browser DNS/redirect residual risks остаются явными;
- release-grade Python/model/OpenAdapt artifact reproducibility обязательна до stable distribution.

Точная текущая точка: [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md). План: [`project-context/ROADMAP.md`](project-context/ROADMAP.md).

## Windows bootstrap/manager

```powershell
.\scripts\bootstrap-chat-platform.ps1
```

Manager/tray отвечает за lifecycle/configuration/diagnostics, а не за ИИ-планирование.

## License / Support

MIT License. Поддержка проекта добровольна и не влияет на лицензионные права.
