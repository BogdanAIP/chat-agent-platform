# Chat Agent Platform

Тонкий мост между **обычным ChatGPT Chat** и локальным Windows-компьютером через стандартный MCP. ChatGPT остаётся интеллектом и выбирает инструменты; локальная часть не содержит второго planner/agent brain.

Для продолжения разработки из нового Chat/Codex сначала читайте [`AGENTS.md`](AGENTS.md) и [`project-context/START_HERE.md`](project-context/START_HERE.md).

## Принятая основа

Нормальный путь после завершения Stage 24.1:

```text
ordinary ChatGPT Chat
  -> ChatGPT custom MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> direct stdio semantic-projection
  -> replaceable task-active MCP backends / focused adapters
  -> local programs/files/devices/models
```

1MCP не удалён из проекта. Он остаётся заменяемой внутренней инфраструктурой для diagnostic/adaptive/catalog/aggregation задач, где его возможности действительно полезны, но обычный public `semantic` через 1MCP больше не проходит.

## Stage 24 / 24.1 — завершены

Stage 24 принял маленькую стабильную semantic typed surface:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Через один `Chat Local Bridge Test` пройден реальный ordinary-Chat workflow: scoped file read/write, browser navigation/observation/interaction и независимое чтение записанного результата.

Stage 24.1 сравнил старый 1MCP-hop и direct stdio. Оба варианта прошли 3/3 lifecycle-цикла на target Windows, но direct stdio оказался значительно быстрее в этой выборке и устранил локальный HTTP-hop/порт 3050 из normal semantic path.

Stage 24.1 squash-merged в `main` как:

```text
df1d5e232b739b62e72ad81e5d82fd01be53e884
Stage 24.1: direct semantic tunnel A/B acceptance (#70)
```

После merge постоянная копия `%LOCALAPPDATA%\ChatAgentPlatform\app` обновлена из `main`; SHA256 контрольных runtime-файлов совпал, а финальный target test завершился:

```text
STAGE24_1_PERSISTENT_INSTALL=PASS
active_profile=semantic
tunnel_binding=direct-stdio
active_count=1
conflict=false
PORT_3050_LISTENER_COUNT=0
```

## Windows bootstrap/manager

Bootstrap рассчитан на PowerShell 7+, Node/npm и обычный Windows user account:

```powershell
.\scripts\bootstrap-chat-platform.ps1
```

Он проверяет окружение и pinned dependencies, устанавливает проверенный официальный `openai/tunnel-client`, сохраняет runtime key через Windows DPAPI `CurrentUser`, устанавливает standalone manager под `%LOCALAPPDATA%\ChatAgentPlatform\app`, создаёт shortcut и поддерживает один authoritative runtime owner.

Manager/tray — только lifecycle/UI слой. Он не является агентом, MCP gateway или planner.

## Принцип безопасности

Рабочая модель:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Возможность может быть зарегистрирована, но не запущена; нужные процессы включаются по задаче; чувствительные операции получают соответствующий scope/authorization.

Безопасность не должна превращаться в бесконечные approval-карточки. Предпочтение: scoped roots/workspaces, backup/git/rollback, bounded tools и подтверждение действительно значимых/необратимых последствий.

## Stage 25 — local specialist inference / local vision

Stage 25 активен. Цель — добавить локальное мультимодальное восприятие без второго AI planner.

Предполагаемая граница:

```text
ChatGPT planner
  -> small typed local-vision capability
  -> deterministic focused adapter
  -> replaceable local inference runtime
  -> replaceable VLM
```

Первый runtime-manager кандидат: **LM Studio / `llmster`**. Текущая официальная документация LM Studio подтверждает headless `llmster`, `lms` lifecycle/model commands, memory estimate before load, GPU offload/context controls, TTL/JIT eviction, loopback HTTP server и OpenAI-compatible chat с изображениями.

### Исправление кандидата Liquid AI

Предыдущая документация ошибочно называла **`LiquidAI/LFM2.5-VL-3B`**. В текущей официальной LFM2.5-VL коллекции Liquid AI такого имени нет.

Текущие кандидаты:

1. **`LiquidAI/LFM2.5-VL-1.6B` / GGUF** — первый preferred current-generation кандидат;
2. `LiquidAI/LFM2.5-VL-450M` / GGUF — лёгкий вариант для сравнения;
3. `LiquidAI/LFM2-VL-3B` / GGUF — более крупный, но предыдущего поколения LFM2.

`LFM2.5-VL-1.6B` официально позиционируется для general vision-language, OCR и document comprehension; модель имеет 32k context и публикуется в native/GGUF/ONNX/MLX вариантах.

Ни LM Studio, ни конкретная VLM не считаются принятыми до реального target-Windows benchmark по качеству, скорости и памяти.

Подробный Stage 25 план: [`project-context/LOCAL_SPECIALIST_INFERENCE.md`](project-context/LOCAL_SPECIALIST_INFERENCE.md).

## Правило выбора модулей

1. официальный/vendor MCP или mature local runtime;
2. зрелый open-source MCP/runtime;
3. готовый local API/CLI + маленький typed adapter;
4. project-owned focused adapter только для измеримого отсутствующего boundary.

Никаких обязательных дополнительных SaaS для базовых локальных возможностей.

## Состояние разработки

Stage 21–24.1 завершены. **Stage 25 активен**: сначала runtime/model reconnaissance и benchmark на реальном Windows-компьютере, затем focused local-vision adapter и только после измерений — новый reviewed Chat-facing vision contract.

Точная текущая точка — [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md). План — [`project-context/ROADMAP.md`](project-context/ROADMAP.md).

Не считайте README более свежим источником, чем код/tests/CI и `CURRENT_STATE.md`.

## Security

Секреты, tunnel IDs и пользовательские абсолютные пути не являются repository content. См. `SECURITY.md` и `project-context/SECURITY_POLICY.md`.

## License / Support

MIT License без дополнительных обязательных условий. Поддержка проекта добровольна и не влияет на лицензионные права.
