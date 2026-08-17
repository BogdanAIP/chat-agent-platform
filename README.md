# Chat Agent Platform

Тонкий мост между **обычным ChatGPT Chat** и локальным Windows-компьютером через стандартный MCP. ChatGPT остаётся интеллектом/планировщиком; локальная часть выполняет только ограниченные детерминированные действия или специализированное восприятие.

Для продолжения разработки сначала читайте [`AGENTS.md`](AGENTS.md), [`project-context/START_HERE.md`](project-context/START_HERE.md), [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md) и Stage 25.1 контракт [`project-context/STAGE25_1_VISION_INTEGRATION.md`](project-context/STAGE25_1_VISION_INTEGRATION.md).

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

## Stage 25 grounding — safety baseline принят

PR #73 слит в `main` как `acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Accepted target baseline: llama.cpp `b10448/ad1de39e0`, LiquidAI LFM2.5-VL-450M F16 + F16 mmproj, CPU 8 threads, ctx 2048. С открытым Chrome: Search/Send/state HIT; Gamma/tiny safe ABSTAIN; отсутствующий Export CSV correct ABSTAIN; false clicks = 0; provider/context errors = 0; present-target baseline = 3/5.

## Stage 25.1 — merged and accepted

PR #74 `Stage 25.1: same-session vision fallback foundation` squash-merged to `main` как `bbf490778a4d883bc54aa58a1d14e8779b7a5c94`.

Финальный reviewed target production-code HEAD: `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c`.

Приняты:

- same-session Playwright capture/freshness/coordinate-action boundary;
- one-shot visual tokens с TTL purge и cap 256; expiry/capacity fail closed;
- ABSTAIN при stale/replay/layout/scroll/overlay/navigation uncertainty;
- отдельный lifecycle owner для llama.cpp с exact artifact/process ownership, RAM admission и TTL unload;
- PID-bound проверка listener `127.0.0.1:3068` перед screenshot inference;
- class-aware verifier: repeated-row и tiny принудительно не авторизуются;
- model-neutral production grounder и fixed-profile runtime-backed runner;
- Windows junction containment;
- secure semantic launcher, удаляющий `CONTROL_PLANE_API_KEY`/`OPENAI_API_KEY` до core import;
- bootstrap installed layout, совпадающий с source contract (`package.json`, `package-lock.json`, launcher, core);
- lockfile SHA256 marker: изменённый/missing lock marker вызывает новый `npm ci`;
- блокировка direct private/link-local/metadata literal IP при сохранённом loopback;
- CodeQL: Actions + JavaScript/TypeScript + Python.

Финальный real-F16 target result:

```text
labeled Send = HIT
Search icon = HIT
state-disambiguated Send = HIT
Gamma repeated-row = correct ABSTAIN
tiny indicator = correct ABSTAIN
absent target = correct ABSTAIN
hits = 3/3 expected
correct_abstains = 3/3 expected
safe_misses = 0
false_clicks = 0
errors = 0
safety_pass = true
acceptance_pass = true
Doctor physical free RAM = 1.919 GB
Doctor virtual free RAM = 8.335 GB
minimum observed free physical RAM = 0.60 GB
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
```

Это **не 6/6 visual accuracy**. Это шестикейсовый safety/behavior gate; Stage 25 present-target baseline остаётся 3/5.

Reviewed RAM policy:

```text
min_start_physical_gb = 1.35
min_start_virtual_gb = 3.0
min_run_physical_gb = 0.5
min_run_virtual_gb = 1.5
target emergency cutoff = 0.30 GB
```

Исходный 1.50 GB cold-start floor был измеренно слишком хрупким после Playwright load. Финальный target run прошёл при минимуме 0.60 GB, без safety stop и без закрытия пользовательского Chrome.

Остаточные ограничения записаны явно: screenshot->click не атомарен; PID-bound loopback не является криптографической аутентификацией; DNS/rebinding/redirect isolation неполон; repeated-row/tiny не продвинуты; Python packaging ещё не release-grade.

## Что намеренно ещё не подключено

Автоматическая цепочка внутри публичных `web_observe` / `web_interact` пока не включена:

```text
semantic miss/ambiguity
  -> real F16 runtime
  -> production grounder
  -> same-session freshness
  -> click/ABSTAIN
```

Это **следующий активный follow-up**. Public semantic contract должен остаться из пяти инструментов.

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
uncertain/stale/unpromoted grounding -> ABSTAIN -> zero page mutation
```

## Текущий приоритет

1. отдельный PR для semantic miss/ambiguity -> internal vision escalation;
2. не продвигать repeated-row/tiny без отдельного измеренного evidence;
3. решить, нужен ли более сильный DNS/redirect/private-network boundary;
4. dependency cleanup (`glob@10.5.0`), Python reproducibility, professional application capabilities и distribution hardening.

Точная текущая точка: [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md). План: [`project-context/ROADMAP.md`](project-context/ROADMAP.md).

## License / Support

MIT License. Поддержка проекта добровольна и не влияет на лицензионные права.
