# Chat Agent Platform

Тонкий мост между **обычным ChatGPT Chat** и локальным Windows-компьютером через стандартный MCP. ChatGPT остаётся интеллектом и выбирает инструменты; локальная часть не содержит второго агента или собственного AI/workflow runtime.

Для продолжения разработки из нового Chat/Codex сначала читайте [`AGENTS.md`](AGENTS.md) и [`project-context/START_HERE.md`](project-context/START_HERE.md).

## Принятая основа

```text
ordinary ChatGPT Chat
  -> ChatGPT custom MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> 1MCP on loopback
  -> replaceable MCP backends
  -> local programs/files/devices
```

Полный reference round trip принят 2026-08-10: обычный ChatGPT вызвал локальный Sequential Thinking через Secure MCP Tunnel и получил результат в том же чате.

## Текущее направление Stage 24

Реальный тест показал, что локальная смена профиля 1MCP не обновляет уже обнаруженный ChatGPT action snapshot. Создавать отдельный Chat app/plugin для Filesystem, Browser, REAPER, Blender, Origin, FFmpeg и каждого будущего модуля не является целевым UX.

Поэтому Stage 24 сейчас проверяет **один стабильный Chat-facing contract** на штатном Lazy Loading 1MCP:

```text
tool_list
tool_schema
tool_invoke
```

и ограниченные lifecycle tools для заранее разрешённого локального каталога:

```text
mcp_list
mcp_status
mcp_enable
mcp_disable
mcp_reload
```

Backend MCP регистрируются локально, стартуют выключенными и включаются по задаче. Если конкретная задача требует нескольких backend одновременно, архитектура должна это позволять. Инструменты произвольной установки/удаления/редактирования каталога не должны публиковаться в ordinary Chat.

**Adaptive пока экспериментальный и не принят.** Принятые direct-профили сохраняются как диагностические/reference paths, пока adaptive не пройдёт CI и реальный ordinary-Chat acceptance.

## Принятые direct-профили

### `reference`

Harmless Sequential Thinking для connectivity/smoke tests.

### `files-readonly`

- один Filesystem MCP;
- один явно выбранный root;
- broad/system roots запрещены;
- create/write/edit/move отключены;
- ordinary-Chat E2E чтения реального marker-файла пройден 2026-08-12.

### `browser-isolated`

- Microsoft Playwright MCP;
- isolated/headless Chrome;
- service workers/codegen и опасные evaluate/file-upload/direct-request tools отключены;
- локальный profile/tunnel readiness пройден;
- ordinary-Chat browser E2E через старый app snapshot не завершён, потому что Chat продолжил показывать filesystem actions.

Direct-профили доказывают отдельные capability boundaries. Они не означают постоянный архитектурный запрет на совместную работу нескольких backend в adaptive workflow.

## Windows bootstrap/manager

Текущий bootstrap рассчитан на PowerShell 7+, Node/npm и обычный Windows user account:

```powershell
.\scripts\bootstrap-chat-platform.ps1
```

Он проверяет окружение и pinned dependencies, устанавливает проверенный официальный `openai/tunnel-client`, создаёт tunnel profile через официальный CLI, хранит runtime key через Windows DPAPI `CurrentUser`, устанавливает standalone manager под `%LOCALAPPDATA%\ChatAgentPlatform\app`, создаёт shortcut и выполняет reference smoke test.

Manager/tray — только lifecycle/UI слой. Он не является агентом, MCP gateway или planner.

## Принцип безопасности

Безопасность не должна превращаться в блокировку полезных сценариев. Рабочая модель:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Возможность может быть зарегистрирована, не запущена; нужные процессы включаются по задаче; чувствительные операции получают соответствующие scope/confirmation. Широкий always-on baseline с локальными данными и открытой сетью не нужен, но легитимный workflow может временно использовать несколько backend одновременно.

## Правило выбора модулей

1. официальный/vendor MCP;
2. зрелый open-source MCP;
3. готовый local API/CLI + маленький adapter;
4. project-owned MCP только для измеримого отсутствующего boundary.

Никаких обязательных дополнительных SaaS для базовых локальных возможностей.

## Состояние разработки

Stage 21–23 завершены. Stage 24 в работе. Точная текущая точка, включая последний падающий adaptive acceptance, находится в [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md). План — [`project-context/ROADMAP.md`](project-context/ROADMAP.md).

Не считайте README более свежим источником, чем код/tests/CI и `CURRENT_STATE.md`.

## Security

Секреты, tunnel IDs и пользовательские абсолютные пути не являются repository content. См. `SECURITY.md` и `project-context/SECURITY_POLICY.md`.

## License / Support

MIT License без дополнительных обязательных условий. Поддержка проекта добровольна и не влияет на лицензионные права.
