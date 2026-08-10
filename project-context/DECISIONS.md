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

ADR-010 и ADR-011 supersede предположение, что этот Rust binary должен оставаться
универсальным bridge core. Rust остаётся допустимым для действительно отсутствующих
локальных adapters.

## ADR-006 — strangler migration with behavioral parity

Python не переписывается одним risky change. Rust последовательно воспроизводит
тот же shared contract и fixtures; default переключается после parity; удаление
Python выполняется отдельным change set после стабилизационного gate.

## ADR-007 — autonomous implementation authority through Stage 19

Пользователь разрешил Chat самостоятельно вести реализацию до Stage 19
включительно и принимать технические решения без отдельного согласования, если
они служат целям проекта. Разрешение не отменяет architecture, quality, security,
cost и no-zoo gates.

## ADR-008 — safe native Windows credential backend for Stage 7

Stage 7 использует `windows-native-keyring-store` + `keyring-core` как тонкий
safe Rust adapter к Windows Credential Manager. После ADR-010/011 этот backend
является частью existing experimental inventory, а не обязательной зависимостью
будущего bridge runtime.

## ADR-009 — canonical standards/contracts, not a canonical cloud provider — retained, narrowed

Канонического Yandex/VPS/cloud transport нет. Standard MCP остаётся canonical
remote protocol boundary, а reachability/control-plane должен выполняться зрелой
инфраструктурой.

Historical acceptance сохраняется: legacy Yandex path доказал Hosted Chat -> local
Windows execution; Tailscale Funnel доказал public HTTPS -> localhost reachability.

## ADR-010 — ordinary ChatGPT Chat + off-the-shelf MCP runtime is the target bridge

### Decision

Продукт определяется как универсальный мост:

```text
ordinary ChatGPT Chat
  -> standard MCP
  -> mature reachability/control plane
  -> mature local MCP runtime/gateway
  -> replaceable MCP servers/adapters
  -> local programs/files/devices
```

ChatGPT Chat остаётся primary intelligence/orchestrator. Work, Codex и OpenAI model
API не являются обязательным normal-runtime path проекта.

Локальные программы и сценарии являются заменяемыми modules, а не platform core.

### Build-vs-buy rule

Для каждой инфраструктурной функции и capability действует порядок:

1. official/vendor implementation;
2. mature maintained open-source implementation;
3. mature generic adapter/proxy;
4. project-owned code only for the exact missing boundary.

Наличие уже написанного собственного кода не является причиной сохранить его как
mandatory dependency.

### Local runtime candidate

1MCP выбран первым минимальным Windows-friendly aggregated MCP runtime и принят
после реального Stage 21 round trip.

Fallbacks используются только для измеримого gap:

- ToolHive — isolation/auth/audit/governance/runtime management;
- agentgateway — protocol/security/routing edge;
- Docker MCP Toolkit — когда Docker Desktop сам принят как baseline.

## ADR-011 — OpenAI Secure MCP Tunnel is the primary ChatGPT-to-local transport

### Decision

После реального acceptance 2026-08-10 основной путь фиксируется как:

```text
ordinary ChatGPT Chat
  -> development MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official `openai/tunnel-client`
  -> 1MCP on localhost
  -> replaceable MCP module
```

Stage 21 доказал этот путь реальным вызовом `sequential_thinking` и возвратом
результата в тот же ChatGPT conversation.

### Consequences

- Project-owned public MCP ingress не нужен для нормальной ChatGPT-local связи.
- Tailscale Funnel больше не является обязательным transport dependency; он
  остаётся optional/fallback reachability.
- Existing HTTPS `443`/Yandex path пока сохраняется как rollback/reference и не
  получает новых feature investments.
- Runtime API key для tunnel-client хранится вне git и имеет только `Tunnels
  Read + Use`.
- `openai/tunnel-client` и 1MCP являются заменяемыми зрелыми компонентами, а не
  новой собственной platform core.
- Project-owned code концентрируется на configuration/lifecycle UX и missing
  local adapters.

### Security

Stage 21 принимал только harmless Sequential Thinking reference tool.

Secure tunnel != permission model для локальных privileged tools. Filesystem,
shell, browser, application control и secrets подключаются только после отдельного
exposure/auth/confirmation profile и negative tests.

### Existing Rust/Yandex core

После acceptance old subsystems переходят в Stage 22 classification:

- remove;
- extract as optional MCP module;
- retain for concrete measured requirement;
- archive/reference.

Wholesale deletion до этой классификации не выполняется.

### Acceptance authority

Реальный ChatGPT surface пользователя является практическим acceptance gate.
Успешный custom MCP round trip подтверждает этот environment, но не является
универсальной гарантией для всех Plus accounts или будущих product packages.

Подробности: `BRIDGE_ARCHITECTURE.md`, `BRIDGE_PILOT.md`, `ROADMAP.md`.
