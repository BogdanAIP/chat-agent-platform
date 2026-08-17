# Chat Agent Platform

Тонкий мост между **обычным ChatGPT Chat** и локальным Windows-компьютером через стандартный MCP. ChatGPT остаётся интеллектом/планировщиком; локальная часть выполняет только ограниченные детерминированные действия или специализированное восприятие.

Для продолжения разработки сначала читайте [`AGENTS.md`](AGENTS.md), [`project-context/START_HERE.md`](project-context/START_HERE.md) и текущий Stage 25.1 контракт [`project-context/STAGE25_1_VISION_INTEGRATION.md`](project-context/STAGE25_1_VISION_INTEGRATION.md).

## Принятая основа

Нормальный путь после Stage 24.1:

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> direct stdio semantic-projection
  -> replaceable task-active MCP backends / focused adapters
  -> local programs/files/devices/models
```

1MCP не удалён: он остаётся внутренней diagnostic/adaptive/aggregation инфраструктурой, но обычный public `semantic` проходит напрямую через stdio.

Принятая публичная semantic surface всё ещё содержит ровно пять действий:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

## Stage 25 grounding — safety baseline принят

PR #73 слит в `main` как:

```text
acc6334ef0114d3ca6b6a243d904605cd00a321a
Stage 25: safe local vision grounding benchmark (#73)
```

Текущий реальный baseline на целевом ноутбуке:

```text
runtime = llama.cpp b10448 / ad1de39e0
model = LiquidAI LFM2.5-VL-450M F16
mmproj = F16
CPU = 8 threads
ctx = 2048
```

С открытым Chrome прошли:

- Search — HIT;
- Send — HIT;
- enabled Send/state disambiguation — HIT;
- Gamma repeated-row — безопасный ABSTAIN;
- tiny indicator — безопасный ABSTAIN;
- отсутствующий Export CSV — корректный ABSTAIN;
- false clicks = 0;
- provider/context errors = 0.

Точность по присутствующим целям сейчас 3/5. Поэтому vision — безопасный fallback-кандидат, а не основной browser controller.

Старые тексты про LM Studio/`llmster`, 450M Q4 и «ещё не запущенный target benchmark» — историческая исследовательская часть и не описывают текущий принятый runtime/model baseline.

## Stage 25.1 — интеграция visual fallback

Следующий этап не добавляет «слепой клик по координате».

Правильная граница:

```text
web operation
  -> semantic DOM/accessibility grounding first
  -> если semantic target отсутствует/неоднозначен:
       SAME Playwright page/session
       -> capture
       -> local vision
       -> deterministic validation + freshness
       -> action в той же page/session ИЛИ ABSTAIN
```

Если нельзя доказать, что screenshot и действие относятся к одному неизменившемуся browser state, автоматическое действие запрещено.

`semantic-projection` не должен превращаться в model manager, workflow brain или универсальный gateway. Управление моделью должно жить в отдельном узком lifecycle-компоненте с проверкой памяти, health, cleanup и idle unload.

## Windows bootstrap/manager

Bootstrap:

```powershell
.\scripts\bootstrap-chat-platform.ps1
```

Менеджер/tray отвечает только за lifecycle/configuration/diagnostics. Секрет tunnel-client хранится через Windows DPAPI. Для shared runtime действует один authoritative owner и fail-closed обработка конфликтов.

## Безопасность

Основная модель:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Возможность может быть установлена, но не запущена; тяжёлые процессы включаются только по необходимости; операция выполняется только в принятом scope.

Для browser vision дополнительно действует правило:

```text
uncertain/stale grounding -> ABSTAIN -> zero page mutation
```

## Текущий приоритет разработки

1. синхронизация source-of-truth после #73;
2. same-session browser capture/ground/action contract;
3. integration acceptance HIT + ABSTAIN/no-action;
4. local vision lifecycle/resource admission;
5. усиление verifier и stale/adversarial tests;
6. security regressions;
7. static analysis/dependency reproducibility;
8. только потом расширение product surface и стабильный release.

Точная текущая точка: [`project-context/CURRENT_STATE.md`](project-context/CURRENT_STATE.md). План: [`project-context/ROADMAP.md`](project-context/ROADMAP.md).

## License / Support

MIT License. Поддержка проекта добровольна и не влияет на лицензионные права.
