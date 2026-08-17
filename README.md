# Chat Agent Platform

Тонкий мост между **обычным ChatGPT Chat** и локальным Windows-компьютером через стандартный MCP. ChatGPT остаётся единственным интеллектом/планировщиком; локальная часть выполняет ограниченные детерминированные действия или специализированное восприятие.

Для продолжения разработки сначала читайте [`AGENTS.md`](AGENTS.md), [`project-context/START_HERE.md`](project-context/START_HERE.md), [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md) и текущий Stage 25.1 контракт [`project-context/STAGE25_1_VISION_INTEGRATION.md`](project-context/STAGE25_1_VISION_INTEGRATION.md).

## Принятая основа

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio semantic-projection
  -> replaceable task-active MCP backends / focused adapters
```

1MCP остаётся внутренней diagnostic/adaptive/aggregation инфраструктурой. Публичная semantic surface по-прежнему содержит ровно пять действий:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

## Stage 25 grounding — принят

PR #73 слит как `acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Текущий target baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

С открытым Chrome: Search/Send/state — HIT; Gamma/tiny — безопасный ABSTAIN; отсутствующий Export CSV — корректный ABSTAIN; `false_clicks=0`, `provider/context_errors=0`, точность по присутствующим целям `3/5`.

Vision поэтому остаётся безопасным fallback-кандидатом, а не основным browser controller.

## Stage 25.1 — что уже доказано

Активна draft PR #74: `chat/stage25-1-vision-integration-foundation`.

На полностью зелёном implementation head `c7eecc4ec1c4796e943816c9e51256d6b181b452` доказаны:

- **same-session visual bridge:** один Playwright MCP session, CSS screenshot, one-shot visual token, повторный screenshot, exact freshness check, coordinate action или ABSTAIN;
- replay, layout shift, scroll, overlay, navigation/page replacement, missing/ambiguous target — без непредусмотренного coordinate action;
- публичных semantic tools всё ещё ровно пять;
- отдельный local-vision runtime owner проходит synthetic Windows lifecycle: Doctor, idempotent Start, Touch, TTL unload, Stop, tamper rejection, foreign-listener и ownership fail-closed;
- Windows junction из workspace наружу не позволяет `workspace_read`/`workspace_write` выйти за root на текущем pinned Filesystem stack;
- production grounding policy не разрешает repeated-row и tiny target превращать в клик без отдельного evidence;
- CodeQL покрывает Actions + JavaScript/TypeScript + Python; Dependabot следит за Actions/npm/pip.

Важно: **реальный F16 ещё не подключён к same-session bridge в production path**. Synthetic runtime proof также не заменяет target-laptop lifecycle acceptance.

## Архитектурное правило vision

```text
semantic DOM/accessibility first
  -> если target надёжен: semantic action
  -> иначе SAME Playwright page/session
       -> capture
       -> bounded local vision
       -> production authorization policy
       -> freshness proof
       -> action ИЛИ ABSTAIN
```

`semantic-projection` не превращается в model manager, workflow brain или универсальный gateway. Heavyweight model lifecycle живёт отдельно.

## Следующие приоритеты

1. проверить наследование `CONTROL_PLANE_API_KEY` и при необходимости явно вычистить его из downstream child env;
2. зафиксировать localhost/private-network navigation scope без поломки намеренных local-web workflows;
3. добавить настоящий npm lockfile и перейти на `npm ci`;
4. подключить model-neutral real VLM grounder через runtime owner + production policy;
5. включить controlled semantic->vision escalation;
6. провести real target-Windows F16 lifecycle + same-session acceptance с Chrome;
7. только затем расширять target-class promotion или публичную capability surface.

## Безопасность

Базовая модель:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Для visual browser action дополнительно:

```text
uncertain/stale/unpromoted target -> ABSTAIN -> zero page mutation
```

## Windows bootstrap

```powershell
.\scripts\bootstrap-chat-platform.ps1
```

Менеджер отвечает за lifecycle/configuration/diagnostics; tunnel key хранится через Windows DPAPI; shared runtime использует authoritative ownership/fail-closed handling.

## License / Support

MIT License. Поддержка проекта добровольна и не влияет на лицензионные права.
