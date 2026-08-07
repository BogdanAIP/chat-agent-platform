# Development Principles

## 1. Outcome before infrastructure

Начинать с короткого реального запроса и проверяемого результата. Не строить
gateway, registry, workflow engine или supervisor до сценария, который без него
невозможно надёжно выполнить.

## 2. Vertical slices before abstractions

Сначала проводить один путь через binding, policy, artifacts, executor и
validation. Обобщать только интерфейсы, уже проявившиеся минимум в одном
production-like потоке.

## 3. Rust-first, not Rust-only

Новый собственный platform core по умолчанию писать на Rust. Зрелые системы
использовать через их сильнейший native interface: FFmpeg CLI, REAPER Lua,
Blender Python, Playwright/Node, Git CLI/API. Переписывание ради единого языка
запрещено.

## 4. One binary is a delivery property, not a monolith

Стремиться к одному `agent-platform.exe`, сохраняя модули и чёткие boundaries.
Создавать отдельный crate или process только при независимом lifecycle,
изоляции, масштабировании либо повторном использовании.

## 5. Contract is not a service

Использовать JSON Schema, Rust types/traits и fixtures. Новый daemon не возникает
из-за появления нового DTO.

## 6. Explicit project binding

Любая write/import/job операция обязана иметь однозначный project ID и проверенный
root. При неоднозначности останавливаться; не угадывать по последней папке или
тексту Chat.

## 7. Policy derives authority

Модель передаёт контекст, но не полномочия. Effective risk вычисляется из
capability, parameters, target, artifact class, reversibility, external effects и
cost. `requested_risk_hint` никогда не снижает риск.

## 8. Deny by default at boundaries

Неизвестная capability, consumer, external destination, data class или secret ref
блокируется. Разрешения добавляются узко и тестируются отрицательным сценарием.

## 9. Artifact IDs over arbitrary paths

После импорта инструменты работают с устойчивым artifact ID. Store отвечает за
path containment, hash, provenance, classification и lifecycle. Бинарные данные
не проходят через Chat или JSON contracts.

## 10. Requirements are not runtime availability

Project requirements версионируются. Runtime profile — датированный снимок
конкретного ПК/surface. Outage меняет profile, но не переписывает требования.

## 11. Mature component first

Сложный стандартный слой брать из зрелого компонента. Собственный код оставлять
для уникальных policy, selection, context и quality logic. Не писать криптографию,
media codecs, browser engine, Git или MCP protocol stack.

## 12. Dependency gate

Добавлять зависимость, только если она уменьшает риск или существенный объём кода.
Проверять maintenance, license, security, platform support и transitive footprint.
Фиксировать lockfile; необязательные edge dependencies не включать в core startup.

## 13. Small reversible changes

Один change set решает одну проверяемую задачу. Сначала вводить совместимый путь,
затем переключать default, потом удалять старый путь после parity. Не смешивать
миграцию языка с изменением поведения.

## 14. Behavioral parity before replacement

Python spike является временным oracle. Rust получает те же fixtures и contracts.
Удаление Python разрешено только после parity по success/error behavior, artifacts,
policy и FFmpeg results.

## 15. Tests follow risk

- pure policy/contracts: быстрые unit/property tests;
- filesystem/process boundaries: integration tests с temp directories;
- FFmpeg: настоящий WAV, не mock-only;
- dangerous actions: обязательные negative/expiry/idempotency tests;
- quality claims: benchmark corpus.

Mocks не могут быть единственным доказательством интеграции.

## 16. Deterministic interfaces, tolerant measurements

Contract shape, IDs, error codes и policy decisions детерминированы. Media metrics
сравниваются с обоснованным tolerance, потому что версии FFmpeg и floating-point
могут давать малые расхождения.

## 17. Structured errors and safe retries

Каждая boundary error имеет stable code, human message, `retryable` и
`safe_to_retry`. Retry не повторяет external/guarded side effects без idempotency.

## 18. Observability without leakage

Логировать correlation IDs, capability, duration, executor version, outcome и
artifact IDs. Не логировать secrets, cookies, raw private payloads и signed URLs.

## 19. Generated views have one source

Markdown audits генерируются из YAML/JSON sources и runtime snapshot. Generated
файл маркируется и не редактируется вручную.

## 20. Progressive context and discovery

Загружать binding, три минимальных context-файла, релевантный skill и один
capability slice. Не отправлять весь manifest, все schemas и все tools в Chat.

## 21. Quality before price, price before excess

Mandatory quality gate выполняется до ranking стоимости. После достижения
требуемого качества выбирать минимальную полную стоимость владения: установка,
обслуживание, compute, API и ручной труд.

## 22. Security-sensitive work is two-phase

Guarded действие: prepare → immutable snapshot/preview → single-use confirmation →
exact execution. Изменение параметров, artifact hash, destination или cost требует
нового confirmation.

## 23. CI mirrors the real Windows path

Минимум: formatting, clippy with denied warnings, tests, schema fixtures, release
build и smoke test с FFmpeg. Linux-only CI не доказывает Windows-local product.
Тесты сами создают всё временное runtime-состояние и не зависят от ignored-файлов
или предварительного ручного запуска: зелёный warmed workspace не является
доказательством воспроизводимости.

## 24. Documentation describes reality

`CURRENT_STATE` говорит только о работающем. `ROADMAP` — о следующем. ADR фиксирует
решение и trade-off. Нельзя выдавать skeleton, schema или test double за capability.

## 25. Stop rules protect efficiency

Остановить расширение, если:

- нет реального пользовательского сценария;
- wrapper требует больше обслуживания, чем экономит;
- появляется второй core/runtime без доказанного gap;
- новая абстракция не уменьшает coupling минимум для двух реальных implementations;
- quality нельзя проверить;
- следующая операция требует новой пользовательской authority.
