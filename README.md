# Chat Agent Platform

Тонкий мост между **обычным ChatGPT Chat** и локальным Windows-компьютером через стандартный MCP. ChatGPT остаётся интеллектом и выбирает инструменты; локальная часть не содержит второго planner/agent brain.

Для продолжения разработки из нового Chat/Codex сначала читайте [`AGENTS.md`](AGENTS.md) и [`project-context/START_HERE.md`](project-context/START_HERE.md).

## Принятая основа

```text
ordinary ChatGPT Chat
  -> ChatGPT custom MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> 1MCP on loopback / focused local adapters
  -> replaceable local capabilities
  -> local programs/files/devices/models
```

Полный reference round trip принят 2026-08-10: обычный ChatGPT вызвал локальный Sequential Thinking через Secure MCP Tunnel и получил результат в том же чате.

## Текущее направление Stage 24

Реальные ordinary-Chat тесты дали два важных результата.

Во-первых, **конкретные типизированные действия работают**. Через один `Chat Local Bridge Test` уже пройдены:

- scoped Filesystem read/write;
- `browser_navigate`;
- `browser_find`;
- `browser_click`;
- совместный Filesystem + Browser workflow в одном ordinary Chat.

Во-вторых, generic adaptive поверхность `tool_list` / `tool_schema` / `tool_invoke` + lifecycle не стала принятым product contract: read-only list/status/discovery доходили до MCP, а lifecycle/schema/generic invocation блокировались до MCP. Adaptive runtime остаётся полезной диагностической/CI инфраструктурой, но не основным Chat-facing интерфейсом.

Также измерено давление на размер action snapshot: при 34 локальных typed actions Chat фактически показывал 20, а после сокращения локального набора до 24 нужные более поздние Browser actions стали доступны после Refresh/new Chat. Это **наблюдаемое поведение текущей конфигурации**, а не заявленный официальный лимит OpenAI.

Поэтому текущая задача Stage 24 — получить масштабируемую typed capability surface с точными схемами и честной семантикой, не создавая отдельный Chat app для каждого backend и не пряча всё за непрозрачный `tool_invoke`.

## Принятые direct-профили

### `reference`

Harmless Sequential Thinking для connectivity/smoke tests.

### `files-readonly`

- один Filesystem MCP;
- один явно выбранный root;
- broad/system roots запрещены;
- create/write/edit/move отключены;
- ordinary-Chat E2E чтения marker-файла пройден.

### `browser-isolated`

- Microsoft Playwright MCP;
- isolated/headless Chrome;
- service workers/codegen и опасные evaluate/file-upload/direct-request tools отключены;
- local profile/tunnel readiness пройден;
- свежий ordinary-Chat typed `browser_navigate` E2E пройден.

Direct-профили остаются диагностическими/reference boundaries. Они не означают постоянный запрет на совместную работу нескольких backend.

## Windows bootstrap/manager

Текущий bootstrap рассчитан на PowerShell 7+, Node/npm и обычный Windows user account:

```powershell
.\scripts\bootstrap-chat-platform.ps1
```

Он проверяет окружение и pinned dependencies, устанавливает проверенный официальный `openai/tunnel-client`, создаёт tunnel profile через официальный CLI, хранит runtime key через Windows DPAPI `CurrentUser`, устанавливает standalone manager под `%LOCALAPPDATA%\ChatAgentPlatform\app`, создаёт shortcut и выполняет reference smoke test.

Реальный Stage 24 тест обнаружил split-brain между установленной и source-копией manager: stale installed runtime мог оставаться на `127.0.0.1:3050`. Текущий функциональный head `64fa0a27...` добавляет общий owner-state и fail-closed port handling; remote Windows/CI/security checks зелёные, target-machine acceptance этой точной правки ещё нужен.

Manager/tray — только lifecycle/UI слой. Он не является агентом, MCP gateway или planner.

## Принцип безопасности

Рабочая модель:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Возможность может быть зарегистрирована, не запущена; нужные процессы включаются по задаче; чувствительные операции получают соответствующий scope/authorization.

Безопасность не должна превращаться в бесконечные approval-карточки. Предпочтение: scoped roots/workspaces, backup/git/rollback, bounded tools и подтверждение действительно значимых/необратимых последствий.

При этом app permission mode — не единственный слой OpenAI safety: в реальном тесте большой составной local-file -> browser -> write запрос блокировался даже при `Allow all actions`, хотя те же typed calls по отдельности проходили.

## Local specialist inference — следующий слой

После Stage 24 планируется локальное specialist inference без второго AI planner.

Первый runtime-manager кандидат: **LM Studio / `llmster`** — для model discovery, estimate-before-load, hardware-aware GPU/variant choice, JIT/load/unload, TTL и auto-evict.

Первый preferred `local-vision` model candidate: **`LiquidAI/LFM2.5-VL-3B`**, официально выпущенный 2026-08-12. Liquid AI публикует screen/UI understanding, OCR/document/chart understanding, grounding, multi-image и GGUF/llama.cpp + ONNX support.

ChatGPT остаётся мозгом; local-vision — глаза. Ни LM Studio, ни конкретная модель не считаются принятыми, пока не пройдут target Windows benchmark.

## Правило выбора модулей

1. официальный/vendor MCP или mature local runtime;
2. зрелый open-source MCP/runtime;
3. готовый local API/CLI + маленький typed adapter;
4. project-owned focused adapter только для измеримого отсутствующего boundary.

Никаких обязательных дополнительных SaaS для базовых локальных возможностей.

## Состояние разработки

Stage 21–23 завершены. Stage 24 в работе. Точная текущая точка — [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md). План — [`project-context/ROADMAP.md`](project-context/ROADMAP.md).

Не считайте README более свежим источником, чем код/tests/CI и `CURRENT_STATE.md`.

## Security

Секреты, tunnel IDs и пользовательские абсолютные пути не являются repository content. См. `SECURITY.md` и `project-context/SECURITY_POLICY.md`.

## License / Support

MIT License без дополнительных обязательных условий. Поддержка проекта добровольна и не влияет на лицензионные права.
