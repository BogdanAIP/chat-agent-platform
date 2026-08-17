# Chat Agent Platform

Тонкий мост между **обычным ChatGPT Chat** и локальным Windows-компьютером через стандартный MCP. ChatGPT остаётся интеллектом/планировщиком; локальная часть выполняет только ограниченные детерминированные действия или специализированное восприятие.

Для продолжения разработки сначала читайте [`AGENTS.md`](AGENTS.md), [`project-context/START_HERE.md`](project-context/START_HERE.md), [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md) и Stage 25.1 контракт [`project-context/STAGE25_1_VISION_INTEGRATION.md`](project-context/STAGE25_1_VISION_INTEGRATION.md).

## Принятая основа

Нормальный путь после Stage 24.1:

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> replaceable task-active MCP backends / focused adapters
  -> local programs/files/devices/models
```

1MCP остаётся внутренней diagnostic/adaptive/aggregation инфраструктурой, но обычный public `semantic` проходит напрямую через stdio.

Публичная semantic surface содержит ровно пять действий:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

## Stage 25 grounding — safety baseline принят

PR #73 слит в `main` как `acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Реальный baseline на целевом ноутбуке:

```text
runtime = llama.cpp b10448 / ad1de39e0
model = LiquidAI LFM2.5-VL-450M F16
mmproj = F16
CPU = 8 threads
ctx = 2048
```

С открытым Chrome:

- Search — HIT;
- Send — HIT;
- enabled Send/state disambiguation — HIT;
- Gamma repeated-row — безопасный ABSTAIN;
- tiny indicator — безопасный ABSTAIN;
- отсутствующий Export CSV — корректный ABSTAIN;
- false clicks = 0;
- provider/context errors = 0;
- точность по присутствующим целям = 3/5.

Vision поэтому остаётся безопасным fallback-кандидатом, а не основным browser controller.

## Stage 25.1 — foundation прошёл реальный target gate

PR #74 реализует безопасную same-session интеграцию без шестого Chat tool и без второго planner.

Доказаны/реализованы:

- same-session Playwright capture/freshness/coordinate-action boundary;
- one-shot visual tokens и ABSTAIN при layout/scroll/overlay/navigation/replay;
- отдельный lifecycle owner для llama.cpp с RAM admission, exact artifact/process ownership и TTL unload;
- class-aware verifier: repeated-row и tiny принудительно не авторизуются;
- model-neutral production grounder и fixed-profile runtime-backed runner;
- Windows junction containment;
- secure semantic launcher, который удаляет унаследованные `CONTROL_PLANE_API_KEY`/`OPENAI_API_KEY` до загрузки core;
- semantic npm lockfile и product/acceptance `npm ci`;
- прямые private/link-local/metadata literal IP блокируются в `web_open`, а loopback остаётся доступен;
- CodeQL: Actions + JavaScript/TypeScript + Python;
- отдельный Windows regression для descendant-stdio cold-Start;
- target harness без долгой stdout/stderr буферизации.

Финальный real-F16 прогон на целевом Windows-ноутбуке с открытым пользовательским Chrome прошёл полностью:

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
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
```

Это **не 6/6 visual accuracy**. Это шестикейсовый safety/behavior gate. Stage 25 baseline по присутствующим целям остаётся 3/5, потому что repeated-row и tiny классы намеренно не продвинуты к клику.

Важно: Playwright origin filters используются только как дополнительная защита. Они не считаются полноценной DNS/redirect network sandbox.

## Что намеренно ещё не подключено

Автоматическая цепочка внутри публичных `web_observe` / `web_interact` пока не включена:

```text
semantic miss/ambiguity
  -> real F16 runtime
  -> production grounder
  -> same-session freshness
  -> click/ABSTAIN
```

Эту политику следует делать отдельным follow-up после merge Stage 25.1 foundation. Public semantic contract при этом должен остаться из пяти инструментов.

## Windows bootstrap/manager

Bootstrap:

```powershell
.\scripts\bootstrap-chat-platform.ps1
```

Менеджер/tray отвечает за lifecycle/configuration/diagnostics, а не за ИИ-планирование. Секрет tunnel-client хранится через Windows DPAPI. Для shared runtime действует один authoritative owner и fail-closed обработка конфликтов.

## Безопасность

Основная модель:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Для browser vision дополнительно:

```text
uncertain/stale/unpromoted grounding -> ABSTAIN -> zero page mutation
```

Тяжёлый vision runtime запускается только после resource admission и выгружается по TTL/pressure policy.

## Текущий приоритет

1. финальная документационная/CI проверка и merge Stage 25.1 foundation;
2. отдельный follow-up для semantic miss/ambiguity -> internal vision escalation;
3. не продвигать repeated-row/tiny без отдельного измеренного evidence;
4. отдельно решить, нужен ли более сильный DNS/redirect/private-network boundary;
5. после Stage 25.1 — dependency cleanup (`glob@10.5.0`), professional application capabilities и distribution hardening.

Точная текущая точка: [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md). План: [`project-context/ROADMAP.md`](project-context/ROADMAP.md).

## License / Support

MIT License. Поддержка проекта добровольна и не влияет на лицензионные права.
