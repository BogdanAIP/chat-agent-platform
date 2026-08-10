# Chat Agent Platform

Тонкий мост между **обычным ChatGPT Chat** и локальным компьютером через стандартный MCP. ChatGPT остаётся интеллектом и выбирает инструменты; репозиторий не содержит второго агента, собственного tunnel/gateway или универсального execution core.

## Принятая архитектура

```text
ordinary ChatGPT Chat
  -> ChatGPT custom MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> 1MCP on 127.0.0.1
  -> replaceable MCP servers/adapters
  -> local programs/files/devices
```

Полный round trip принят 2026-08-10: `Chat Local Bridge Test` успешно вызвал локальный `sequential_thinking`, и результат вернулся в тот же ChatGPT Chat.

## Почему репозиторий стал маленьким

Stage 22 удалил активную реализацию старой архитектуры: `agent-platform.exe`, `/gpt`, polling relay, Yandex gateway/deploy, Python oracle, media/mastering core и release pipeline для старого бинарника. Они сохранены в Git history и могут быть извлечены позже только как отдельные MCP-модули, если для нужной программы не найдётся хорошего готового решения.

Правило разработки:

1. официальный/vendor MCP;
2. зрелый open-source MCP;
3. готовый generic adapter/proxy;
4. только затем маленький project-owned adapter для конкретной программы.

## Локальный MCP runtime

Текущий проверенный runtime — `@1mcp/agent@0.34.4`. Безопасный reference-модуль находится в `runtime/mcp.json`.

```powershell
.\scripts\start-local-bridge.ps1
.\scripts\status-local-bridge.ps1
.\scripts\stop-local-bridge.ps1
```

Локальный MCP endpoint:

```text
http://127.0.0.1:3050/mcp
```

OpenAI Secure MCP Tunnel запускается официальным `openai/tunnel-client` отдельно и подключается к этому loopback endpoint. Runtime API key хранится только локально и должен иметь минимальные права `Tunnels: Read + Use`. Секреты и tunnel IDs в репозиторий не коммитятся.

## Безопасность

Reference-конфигурация содержит только `sequential_thinking`. Filesystem, shell, browser и управление локальными приложениями считаются привилегированными модулями и не добавляются до отдельного принятого профиля разрешений и негативных тестов.

См. `SECURITY.md` и `project-context/SECURITY_POLICY.md`.

## Что дальше

Stage 23 — каталог реальных локальных возможностей и выбор готовых MCP-модулей. Stage 24 — профиль безопасности для привилегированных модулей. Тонкий Windows manager рассматривается только после того, как модель модулей стабилизирована.

Актуальное состояние: `project-context/CURRENT_STATE.md`. План: `project-context/ROADMAP.md`.

## License / Support

MIT License без дополнительных обязательных условий. Механика `Support the Project` остаётся добровольной; способы поддержки будут добавлены отдельно.
