# Decisions

## ADR-001 — vertical slice before infrastructure

Начать с Stage 0–1 и реального `media.inspect`, не создавая transport, gateway,
workflow engine или отдельные services.

## ADR-002 — Python architecture spike + FFmpeg

Первый slice реализован на Python для дешёвой проверки binding, policy, contracts,
artifact manifest и FFmpeg. После v1.4 он классифицирован как временный behavioral
oracle, а не целевой platform core.

## ADR-003 — JSON-compatible YAML for bootstrap configs

Первые YAML-файлы записаны в JSON-синтаксисе (валидный YAML 1.2), чтобы не
добавлять parser dependency до появления реальной потребности в полном YAML.

## ADR-004 — JSON Schema as the contract validator

Стандартные execution contracts валидируются зрелой библиотекой `jsonschema`.
Собственная предметная логика остаётся в проекте, но реализация стандарта не
дублируется частичным самописным validator.

## ADR-005 — adopt v1.4 Rust-first / native-edge — historical, superseded for bridge core

Целевой локальный core v1.4 поставлялся как один Windows Rust binary. Решение было
полезно для проверки process control, path/policy enforcement, artifact/job/secret
primitives и реальных локальных media executors.

ADR-010 supersedes the assumption that this Rust binary must remain the universal
bridge core. Rust remains allowed for genuinely missing local adapters.

## ADR-006 — strangler migration with behavioral parity

Python не переписывается одним risky change. Rust последовательно воспроизводит
тот же shared contract и fixtures; default переключается после parity; удаление
Python выполняется отдельным change set после стабилизационного gate.

## ADR-007 — autonomous implementation authority through Stage 19

Пользователь разрешил Chat самостоятельно вести реализацию до Stage 19
включительно и принимать технические решения без отдельного согласования, если
они служат целям проекта. Разрешение включает внедрение полезных технических
решений, но не отменяет architecture, quality, security, cost и no-zoo gates.

Это не разрешение на бесконечное расширение продукта: новый component/dependency
должен иметь измеримую пользу, не дублировать зрелый инструмент без причины и
оставаться заменяемым. Отдельная пользовательская authority всё ещё нужна для
необратимых/внешних действий, новых расходов, раскрытия секретов или изменения
продуктовой цели.

## ADR-008 — safe native Windows credential backend for Stage 7

Stage 7 использует `windows-native-keyring-store` + `keyring-core` как тонкий
safe Rust adapter к Windows Credential Manager. Это сохраняет native Windows
secret storage и правило workspace `unsafe_code = "forbid"`, не добавляя daemon,
внешний vault, собственную криптографию или отдельный процесс.

После ADR-010 этот backend является частью existing experimental inventory, а не
обязательной зависимостью будущего bridge runtime. Если выбранный mature MCP
runtime/host закрывает secret/auth requirement достаточным способом, отдельный
project-owned Secret Store не сохраняется только из-за sunk cost.

## ADR-009 — canonical standards/contracts, not a canonical cloud provider — retained, narrowed by ADR-010

Канонического Yandex/VPS/cloud transport нет. Standard MCP остаётся canonical
remote protocol boundary, а NAT/TLS/public routing должны выполняться зрелой
инфраструктурой.

Historical acceptance сохраняется: 2026-08-06 установленный ChatGPT integration
`Music Video MCP Yandex Test` успешно выполнил `local_ping` на реальном Windows
agent и вернул результат обратно в ChatGPT. 2026-08-10 Tailscale Funnel также
доказал прямую public HTTPS reachability до localhost.

ADR-010 меняет способ реализации MCP/local runtime: вместо обязательного
project-owned `rmcp` server сначала используется готовый maintained MCP
runtime/gateway. Собственный MCP server допускается только после доказанного
неустранимого compatibility gap.

## ADR-010 — ordinary ChatGPT Chat + off-the-shelf MCP runtime is the target bridge

### Decision

Продукт определяется как универсальный мост:

```text
ordinary ChatGPT Chat
  -> standard MCP
  -> mature reachability
  -> mature local MCP runtime/gateway
  -> replaceable MCP servers/adapters
  -> local programs/files/devices
```

ChatGPT Chat остаётся primary intelligence/orchestrator. Work, Codex и OpenAI API
не являются обязательным model/runtime path проекта.

Локальные программы и сценарии (REAPER, FFmpeg, Origin, Blender, browser, files,
CAD, local models, hardware и т.д.) являются заменяемыми modules, а не частями
platform core.

### Build-vs-buy rule

Для каждой инфраструктурной функции и capability действует порядок:

1. official/vendor implementation;
2. mature maintained open-source implementation;
3. mature generic adapter/proxy;
4. project-owned code only for the exact missing boundary.

Наличие уже написанного собственного кода не является причиной сохранить его как
mandatory dependency.

### First runtime candidate

Первым проверяется 1MCP как минимальный готовый Windows-friendly aggregated MCP
runtime. Первый реальный pilot не содержит project-owned MCP implementation:

```text
ChatGPT Chat
  -> Tailscale Funnel :8443
  -> 1MCP 127.0.0.1:3050
  -> official Sequential Thinking reference MCP server
```

Если direct native-MCP acceptance проходит, 1MCP принимается как default runtime,
пока не появится измеримая причина заменить его.

Если возникает конкретный gap:

- ToolHive — first fallback для isolation/auth/audit/governance/protocol translation;
- agentgateway — optional protocol/security edge;
- Docker MCP Toolkit — только когда Docker Desktop сам по себе принят как baseline.

Нельзя одновременно тащить все кандидаты «на всякий случай».

### Existing Rust/Yandex core

Existing `agent-platform.exe`, `/gpt`, polling relay, Yandex assets, universal
policy/job/artifact/confirmation layers and media workflows remain temporary
experimental inventory until the new path is accepted.

После acceptance каждый subsystem получает одну классификацию:

- remove;
- extract as optional MCP module;
- retain for a concrete measured requirement;
- archive/reference.

### Security

Public tunnel != authorization. Первый unauthenticated pilot допускается только с
одним harmless reference server и временным Funnel listener. Privileged modules
(filesystem, shell, browser, app control, secrets) не подключаются до отдельного
accepted auth/permission profile.

### Acceptance authority

Реальный ChatGPT surface пользователя является практическим acceptance gate.
Публичная документация тарифов OpenAI не считается основанием обещать одинаковый
full-MCP behavior всем Plus accounts, если это не подтверждено официально.

Подробности: `BRIDGE_ARCHITECTURE.md`, `BRIDGE_PILOT.md`, `ROADMAP.md`.
