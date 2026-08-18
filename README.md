# Chat Agent Platform

Тонкий мост между **обычным ChatGPT Chat** и локальным Windows-компьютером через стандартный MCP. ChatGPT остаётся интеллектом/планировщиком; локальная часть выполняет только ограниченные детерминированные действия или специализированное восприятие.

Для продолжения разработки сначала читайте [`AGENTS.md`](AGENTS.md), [`project-context/START_HERE.md`](project-context/START_HERE.md), [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md) и контракт [`project-context/STAGE25_1_VISION_INTEGRATION.md`](project-context/STAGE25_1_VISION_INTEGRATION.md).

## Принятая основа

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> replaceable task-active MCP backends / focused adapters
  -> local programs/files/devices/models
```

1MCP остаётся внутренней diagnostic/adaptive/aggregation инфраструктурой. Публичная semantic surface содержит ровно пять действий:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

## Stage 25 — grounding safety baseline

PR #73 слит в `main` как `acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Accepted target baseline: llama.cpp `b10448/ad1de39e0`, LiquidAI LFM2.5-VL-450M F16 + F16 mmproj, CPU 8 threads, ctx 2048. С открытым Chrome: Search/Send/state HIT; Gamma/tiny safe ABSTAIN; отсутствующий Export CSV correct ABSTAIN; false clicks = 0; provider/context errors = 0; present-target baseline = 3/5.

## Stage 25.1 — same-session vision foundation

PR #74 squash-merged to `main` как `bbf490778a4d883bc54aa58a1d14e8779b7a5c94`.

Финальный reviewed target production-code HEAD: `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c`.

Приняты same-session capture/freshness/coordinate-action, fail-closed visual authorization, focused llama.cpp lifecycle owner, PID-bound listener verification, secure installed semantic runtime, lock-hash-controlled `npm ci`, junction containment, bounded browser literal-IP policy и CodeQL coverage.

Reviewed RAM policy:

```text
min_start_physical_gb = 1.35
min_start_virtual_gb = 3.0
min_run_physical_gb = 0.5
min_run_virtual_gb = 1.5
target emergency cutoff = 0.30 GB
```

## Stage 25.2 — semantic-first internal vision escalation

PR #77 завершает первый реальный public semantic→vision path внутри существующего `web_interact`, не добавляя шестого инструмента и второго ИИ-планировщика.

Финальный target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`

Поведение:

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
       -> real local F16 grounder
       -> deterministic authorization
       -> freshness proof
       -> single coordinate click OR ABSTAIN
```

Safety boundary:

- `targetText` — единственный semantic/visual anchor;
- planner не передаёт авторизующий `kind`;
- planner `target` и произвольная `instruction` не могут перенаправить vision на другой объект;
- router сам строит каноническую visual instruction из `targetText`;
- generic semantic click error никогда не вызывает vision;
- semantic ambiguity не вызывает vision;
- repeated-row/tiny/icon-only не получают автоматического promotion в Stage 25.2;
- safe ABSTAIN — это no-action result, а не ложная backend error.

Финальный real-F16 target result с обычным Chrome открытым:

```text
semantic_hits = 2
visual_hits = 1
correct_abstains = 2
false_clicks = 0
errors = 0
semantic_cases_started_vlm = 0
acceptance_pass = true
Doctor physical free RAM = 2.62 GB
Doctor virtual free RAM = 8.129 GB
minimum observed free physical RAM = 1.04 GB
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
VISION_RUNTIME_STATE_AFTER_TEST = stopped
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
STAGE25_2_FINAL_REVIEW_RESULT = PASSED
```

Result path:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage25\runtime\stage25-2-public-escalation-20260818-161812\result.json`

Все 9 workflow families, запущенные на финальном production-code HEAD, зелёные.

## Что это пока не означает

Платформа ещё не объявлена stable end-user product. Остаточные ограничения:

- repeated-row/tiny и automatic icon-only visual fallback не продвинуты;
- screenshot→click не атомарен;
- PID-bound loopback не криптографическая аутентификация;
- DNS/rebinding/redirect isolation неполон;
- Python/model distribution ещё не release-grade;
- реальные professional Windows applications ещё не product-accepted.

## Windows bootstrap/manager

Bootstrap:

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

## Текущий приоритет

1. Stage 26: реальные Windows/application workflows — Origin, REAPER, FFmpeg, Blender и broader Windows UI;
2. не продвигать repeated-row/tiny/icon-only без отдельного измеренного evidence;
3. решить более сильный DNS/redirect/private-network boundary;
4. dependency/Python/model reproducibility cleanup;
5. Stage 27: installer, update/repair/doctor/uninstall, key rotation, rollback, restart recovery и clean-user E2E;
6. только после этого объявлять первый stable release.

Точная текущая точка: [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md). План: [`project-context/ROADMAP.md`](project-context/ROADMAP.md).

## License / Support

MIT License. Поддержка проекта добровольна и не влияет на лицензионные права.
