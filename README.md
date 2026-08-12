# Chat Agent Platform

Тонкий мост между **обычным ChatGPT Chat** и локальным Windows-компьютером через стандартный MCP. ChatGPT остаётся интеллектом и выбирает инструменты; локальная часть не содержит второго агента, собственного tunnel/gateway или универсального execution core.

## Принятая архитектура

```text
ordinary ChatGPT Chat
  -> ChatGPT custom MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> 1MCP on 127.0.0.1:3050
  -> one explicit least-privilege task profile
  -> replaceable MCP servers/adapters
  -> local programs/files/devices
```

Полный reference round trip принят 2026-08-10: обычный ChatGPT вызвал локальный `sequential_thinking`, и результат вернулся в тот же чат.

## Первый запуск на Windows

Текущий bootstrap рассчитан на PowerShell 7+, Node/npm и обычный Windows user account:

```powershell
.\scripts\bootstrap-chat-platform.ps1
```

Bootstrap выполняет полный локальный setup:

1. проверяет Windows, PowerShell, Node/npm/npx и pinned 1MCP;
2. получает принятый официальный `openai/tunnel-client` для архитектуры Windows;
3. проверяет release tag, официальный `SHA256SUMS.txt`, pinned SHA-256 и GitHub release digest;
4. устанавливает `tunnel-client.exe` в `%LOCALAPPDATA%\ChatAgentPlatform\bin`;
5. запрашивает или повторно использует `CONTROL_PLANE_TUNNEL_ID`;
6. создаёт профиль `local-1mcp` штатной командой `tunnel-client init` для `http://127.0.0.1:3050/mcp`;
7. копирует проверенный manager/runtime bundle в `%LOCALAPPDATA%\ChatAgentPlatform\app`;
8. при первом запуске скрыто запрашивает `CONTROL_PLANE_API_KEY` и хранит его через Windows DPAPI `CurrentUser`;
9. создаёт desktop shortcut;
10. по умолчанию выполняет smoke test `MCP ready + Tunnel ready`, затем оставляет платформу выключенной.

После успешного bootstrap рабочий desktop manager запускается из `%LOCALAPPDATA%` и не зависит от расположения git checkout.

Для runtime API key нужны только права туннеля, необходимые обычному tunnel runtime (`Tunnels: Read + Use`). Административный API key manager не использует.

## Локальный manager

Прямые команды установленного controller доступны из `%LOCALAPPDATA%\ChatAgentPlatform\app\scripts`:

```powershell
.\chat-platform-controller.ps1 -Action Status
.\chat-platform-controller.ps1 -Action Start
.\chat-platform-controller.ps1 -Action Stop
```

Tray является только UI: он не определяет процессы, PID или health самостоятельно, а отображает авторитетное состояние controller. Зелёный статус возможен только при одном активном MCP-профиле, готовом MCP и готовом Secure MCP Tunnel.

## Профили обычного Chat

### `reference`

Только harmless Sequential Thinking. Используется для connectivity/smoke tests.

### `files-readonly`

- один Filesystem MCP;
- один явно выбранный локальный root;
- целый диск и broad/system roots запрещены;
- create/write/edit/move отключены;
- browser отсутствует.

### `browser-isolated`

- один Microsoft Playwright MCP;
- isolated/headless Chrome;
- filesystem отсутствует;
- service workers и codegen отключены;
- unsafe code/evaluate/file-upload/direct-network tools отключены.

Filesystem и open-web browser намеренно не объединяются в постоянный baseline profile: read-only локальные данные плюс сетевой browser уже образуют путь утечки при prompt injection.

## Почему активный репозиторий небольшой

Stage 22 удалил старый project-owned Rust/Python core, `/gpt`, polling relay, Yandex gateway/deploy и media/mastering platform core. Полная старая реализация сохранена в Git history и может использоваться только как материал для точечного MCP adapter, если готовое решение не пройдёт реальные тесты.

Правило выбора локальной возможности:

1. официальный/vendor MCP;
2. зрелый open-source MCP;
3. готовый local API/CLI + маленький adapter;
4. только затем project-owned MCP для измеримого отсутствующего boundary.

## Состояние разработки

Stage 21–23 завершены. Stage 24 доводит least-privilege profiles и локальный lifecycle/bootstrap до принятого состояния. После этого Stage 25 — реальные application benchmarks для REAPER, Origin, FFmpeg, Blender и Windows UI fallback.

Актуальное состояние: `project-context/CURRENT_STATE.md`. План: `project-context/ROADMAP.md`.

## Security

Секреты, tunnel IDs и пользовательские абсолютные пути не являются repository content. Runtime key хранится локально через DPAPI. См. `SECURITY.md` и `project-context/SECURITY_POLICY.md`.

## License / Support

MIT License без дополнительных обязательных условий. Поддержка проекта остаётся добровольной и не влияет на лицензионные права.
