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

## ADR-005 — adopt v1.4 Rust-first / native-edge

Целевой локальный core поставляется как один Windows Rust binary. Выбор оправдан
process control, path/policy enforcement, низкой runtime-зависимостью и будущими
artifact/job/secret primitives. FFmpeg, REAPER, Blender, Browser и Git сохраняют
свои native interfaces; Rust-first не означает Rust-only.

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
должен иметь измеримую пользу для Stage 0–19, не дублировать зрелый инструмент без
причины и оставаться заменяемым. Отдельная пользовательская authority всё ещё
нужна для необратимых/внешних действий, новых расходов, раскрытия секретов или
изменения продуктовой цели.

## ADR-008 — safe native Windows credential backend for Stage 7

Stage 7 использует `windows-native-keyring-store` + `keyring-core` как тонкий
safe Rust adapter к Windows Credential Manager. Это сохраняет native Windows
secret storage и правило workspace `unsafe_code = "forbid"`, не добавляя daemon,
внешний vault, собственную криптографию или отдельный процесс. Default `search`
feature отключён, потому что платформе не нужен поиск по системному хранилищу.
`zeroize` используется для гарантированного стирания краткоживущего буфера после
consumer callback.

Замена backend не должна менять публичную модель `SecretStore`: если появится
поддерживаемый safe Windows credential API с меньшим dependency footprint,
`windows-native-keyring-store` и `keyring-core` удаляются вместе и заменяется
только platform-specific backend. `zeroize` удаляется только при наличии
эквивалентной гарантии, что очистка secret bytes не будет оптимизирована
компилятором. До замены зависимости фиксируются `Cargo.lock` и проверяются Windows
CI; новый service/process для Secret Store не допускается без отдельной lifecycle
потребности.

## ADR-009 — canonical standards/contracts, not a canonical cloud provider

Stage 4 не имеет канонического Yandex/VPS/cloud transport. Каноническими являются
границы MCP, локальной безопасности и execution contracts, а способ reachability
выбирается при развёртывании.

Целевой MCP boundary должен опираться на официальный Rust SDK `rmcp`, а не
расширять самописную реализацию меняющегося стандарта. Для переносимого UI
принимается открытый **MCP Apps** standard: общие `ui://` resources и `ui/*`
bridge являются primary contract; host-specific API используются только как
feature-detected extensions поверх portable foundation.

Для remote MCP первым проверяется самый простой переносимый вариант — обычный
public HTTPS Streamable HTTP endpoint (`/mcp`). Current OpenAI plugin development
flow принимает такой endpoint напрямую, поэтому Secure MCP Tunnel не является
обязательной частью OpenAI integration.

Официальный **OpenAI Secure MCP Tunnel** принимается как optional
private-reachability adapter: локальный `tunnel-client` инициирует outbound HTTPS,
получает MCP work, проксирует его к локальному MCP server и возвращает результат.
Он применяется, когда private reachability действительно полезна и account /
Platform access её поддерживает. Tunnel остаётся OpenAI-specific edge component,
требует Platform tunnel identity/runtime credentials и не должен считаться частью
ChatGPT subscription или universal core.

Для других hosts или когда public HTTPS/private caller-native path неудобен,
используются зрелые reverse-tunnel/reverse-proxy решения (например frp/zrok
class), а не собственная реализация NAT traversal, multiplexing, ACME/TLS
automation или public routing.

Существующий `poll/result/offline` transport сохраняется как
`polling-relay-http-v1` compatibility profile для сценариев, где standard MCP
reachability недоступна. Его Windows-клиент уже provider-neutral: конфигурация
содержит только HTTPS `endpoint` и `secret_ref`. Rust `relay-server` является
reference/fallback implementation этого polling-профиля; Yandex Function/Object
Storage — ещё один проверенный backend implementation.

Historical acceptance нельзя терять: 2026-08-06 установленный ChatGPT integration
`Music Video MCP Yandex Test` успешно выполнил `local_ping` на реальном Windows
agent и вернул результат обратно в ChatGPT. Поэтому Hosted Chat round trip уже
доказан; отдельный native `/mcp` test является migration/portability gate, а не
повторным Stage 4 exit gate.

Смена Yandex на VPS, caller-native tunnel, другой cloud/serverless provider или
другой MCP host не должна менять локальные capability contracts, policy,
artifact/job semantics или исполнители. Provider-specific SDK/enum в core
запрещён без отдельной доказанной необходимости.

Подробная схема и migration rules: `project-context/CONNECTOR_ARCHITECTURE.md`.
