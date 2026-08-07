# Roadmap v1.4

Эта дорожная карта является исполняемым порядком разработки, а не списком
обещанных функций. Каждый этап начинается только после прохождения входного gate
и завершается проверяемым результатом. Source of truth для текущего положения —
этот файл вместе с `CURRENT_STATE.md`; live runtime остаётся в `runtime/`.

## Обозначения

- **done** — acceptance criteria пройдены реальным сценарием;
- **in progress** — работа начата, но exit gate ещё не пройден;
- **partial** — существует полезный результат, не закрывающий весь этап;
- **planned** — этап не начат;
- **conditional** — выполняется только после доказанного gap/спроса.

## Текущий маршрут

```text
v1.3 Python architecture spike
        ↓ сохранить contracts, fixtures и ожидаемое поведение
v1.4 Rust Stage 0–1 parity
        ↓ один agent-platform.exe + FFmpeg CLI
Stage 2–3 consolidation
        ↓
Chat/local execution probe
        ↓
следующий capability только по реальному пользовательскому сценарию
```

## Horizon A — доказать Rust core

### Stage 0. Reality baseline + Project Binding — partial

Результат:

- зафиксированы Git, Python, Node, FFmpeg/ffprobe и Rust toolchain;
- существует однозначный `demo` Project Binding;
- requirements отделены от runtime profile;
- локальный `media.inspect` имеет рабочий Rust execution path и Python behavioral oracle;
- Chat → GitHub read/write подтверждён реальным branch/edit/PR циклом через plugin;
- hosted Chat → local execution и account-level MCP write/modify не считаются доступными без probe.

Осталось:

- полностью синхронизировать Rust/Cargo/Windows target evidence в runtime profile;
- проверить реальный пользовательский WAV в пользовательской локальной среде;
- отдельно проверить Chat → local execution / MCP surface.

Exit gate: каждый обязательный requirement имеет рабочий path или явный gap с
fallback; соседний проект невозможно выбрать неявно.

### Stage 1. Rust vertical architecture validation — done

Перенести без расширения scope:

```text
binding → policy → artifact import → FFprobe/FFmpeg → validation → tool-v1
```

Сохранить Python slice как временный behavioral oracle. Rust и Python получают
один input WAV и обязаны совпасть по contract shape, duration, sample rate,
channels, codec и LUFS в установленном tolerance.

Exit gate:

- `agent-platform.exe inspect` проходит реальный WAV;
- binary payload не попадает в stdout/contract;
- ложный `requested_risk_hint=low` не обходит policy;
- artifact hash и metadata валидируются;
- `cargo fmt`, `clippy`, unit и integration tests проходят;
- Python не нужен для запуска Rust inspect path.

### Stage 2. Core Contracts v1 — done

JSON Schema для tool request/result, artifact, policy decision, secret reference и
job встроены в Rust binary. Общие positive/negative fixtures проходят Rust и
Python oracle. Transport Contract отсутствует, поскольку transport не участвует.

Exit gate: positive/negative fixtures валидируются одинаково Rust и временным
Python oracle; Transport Contract не создаётся до появления transport.

### Stage 3. Project Memory + Bootstrap + Skills — done

Довести набор:

- `VISION`, `ARCHITECTURE`, `DECISIONS`, `CONSTRAINTS`;
- `COST_POLICY`, `SECURITY_POLICY`, `DEVELOPMENT_PRINCIPLES`;
- `CURRENT_STATE`, `ROADMAP`, `KNOWN_ISSUES`;
- generated capability audit;
- `bootstrap`, `media-inspection`, `github-development`, skeleton `mastering`;
- handoff template.

Exit gate: новая сессия получает project binding, три минимальных context-файла и
один релевантный capability slice без полного пересказа архитектуры.

Rust `bootstrap`, `probe` и `audit` работают. `bootstrap`, `media-inspection`,
`github-development` и ограниченный `mastering` skills валидированы и проверены в
независимых сессиях; handoff template существует.

## Horizon B — дать Chat безопасный execution path

### Stage 4. Local execution + transport capability probe — partial

Сначала проверить native/direct surface. Отдельный transport добавлять только
если Chat иначе не достигает local execution. Probe: auth, ping, controlled file
write/read, health, reconnect, timeout, versions и structured errors.

Exit gate: принято ADR «transport не нужен» либо выбран один тонкий adapter;
transport не содержит media/business logic.

Локальный Rust path теперь имеет typed `self-test`: policy, ping, controlled
write/read/cleanup, FFmpeg/ffprobe health и contract validation. Remote transport и
reconnect probe пока отсутствуют.

### Stage 5. MCP discovery/runtime comparison — conditional

Для Chat: native app/plugin/direct MCP → поддерживаемый local adapter.
Для Codex/local: direct MCP → 1MCP при доказанном уменьшении контекста → ToolHive
только при реальной governance/isolation потребности.

Exit gate: выбран один path на поверхность; кандидаты не установлены одновременно
«на будущее».

### Stage 6. Tool Manifest + selection + hardened PEP — done

Ввести capability-level metadata и mandatory gates до ranking. Технически
обеспечить allow/deny/guarded; Chat не определяет effective risk.

Exit gate: professional requirement исключает basic executor, deny невозможно
обойти прямым вызовом, guarded возвращает immutable preview.

`config/tools.yaml` и `config/tool-lock.yaml` теперь задают manifest-backed locked
executor. `required_quality` берётся из versioned project requirements, а quality
и cost gates применяются до execution. PEP хранит `decision` отдельно от
`effective_risk`; `requested_risk_hint` не влияет на enforcement. Для guarded
операций создаётся SHA-256 confirmation binding по capability, parameters,
data class и effective risk, поэтому изменение параметров или artifact hash
инвалидирует подтверждение. Windows CI проверяет rejection basic executor для
professional requirement, mandatory cost gate, deny bypass resistance и
confirmation binding semantics; полный verify/release/artifact run прошёл успешно.

### Stage 7. Secret Store + consumer ACL — done

Использовать Windows Credential Manager/DPAPI через системные bindings, без
собственной криптографии. Secret refs не раскрывают значения.

Exit gate: разрешённый consumer получает секрет на минимальное время; FFmpeg,
логи, artifacts и Project Memory не получают raw value.

Реализован native Windows Credential Manager backend через safe Rust adapter без
`unsafe` в platform crate, отдельного vault/daemon и собственной криптографии.
Metadata содержит только `secret://` ref, consumer ACL и детерминированный
credential target. Доступ принимается только по `CapabilitySelection`, выданному
Stage 6 registry; raw bytes существуют внутри короткого callback и затем
стираются через `zeroize`. Интеграционный Windows test доказывает доступ
разрешённого executor, отказ `rust.local.ffmpeg` и отсутствие raw value в metadata
и access errors. Новые зависимости зафиксированы в `Cargo.lock`, а ADR-008
содержит причину выбора и план замены; полный Windows verify/release прошёл.

### Stage 8. Artifact hardening + staging — partial

Добавить lifecycle, concurrency-safe manifest/storage и staging policy.

Exit gate: data classification управляет external staging; checksum проверяется;
temporary copies очищаются; hash change инвалидирует confirmation.

Manifest updates сериализованы межпроцессной file lock и публикуются атомарной
заменой; concurrent-import test доказывает отсутствие lost updates. Recovery
незарегистрированных каталогов и staging ещё не готовы.
Lookup по `artifact_id` проверяет schema, path containment и SHA-256; повторный
анализ не требует произвольного пользовательского пути или новой копии.

### Stage 9. Single-binary supervisor — conditional

Один CLI entry point `start/status/diagnose/stop`. Tray/service — только после
подтверждённой эксплуатационной пользы.

Exit gate: один exe управляет только реально выбранными компонентами и не
превращается в постоянно работающий зоопарк.

### Stage 10. GitHub Actions — complete baseline

Добавить Windows CI: fmt, clippy с warnings-as-errors, tests, contract fixtures,
dependency/security audit и release build.

Exit gate: PR получает воспроизводимый результат; секреты только в GitHub Secrets;
release artifact проверен на чистой машине.

Windows workflow и единый `scripts/verify.ps1` доказаны локально и зелёными
запусками на чистых GitHub-hosted runner'ах. Проверены branch, draft PR, CI,
upload release artifact и squash merge в `main`. Dependency/security audit и
подписанный versioned release остаются отдельным усилением supply chain.

## Horizon C — профессиональные media capabilities

### Stage 11. FFmpeg professional adapter — partial

Расширять только typed operations: inspect, loudness, convert, extract, normalize,
mux/validate. CLI остаётся native edge; FFI требует измеримого выигрыша.

Exit gate: каждый operation имеет policy class, artifact contract, timeout,
structured error и technical validation.

Typed `inspect` уже возвращает metadata, EBU R128 integrated loudness, LRA и true
peak. Convert/extract/normalize/mux operations ещё не реализуются без сценария.

### Stage 12. REAPER adapter — planned

Rust contracts/policy/jobs → ограниченный Lua/ReaScript driver → REAPER.

Exit gate: проект/track/import/marker/save/render выполняются без произвольного
shell и возвращают валидированный artifact.

### Stage 13. Audio analysis/mastering decision layer — planned

Создать benchmark corpus и decision logic поверх готовых анализаторов.

Exit gate: технические метрики и профессиональная quality acceptance проходят на
репрезентативном корпусе, а не на одном тестовом тоне.

### Stage 14. Workflow runtime gate — conditional

Сначала проверить лёгкий Rust job state machine: persistence, cancellation,
idempotency, retry, checkpoints, resume. Prefect/Node-RED/другой engine сравнивать
только при незакрытом реальном workflow.

Exit gate: один выбранный runtime; нет собственной копии Prefect.

### Stage 15. Production mastering workflow — planned

Первый длинный workflow с job ID, recovery, artifacts и quality gate.

Exit gate: результат доступен после новой сессии; retry не дублирует опасные
действия; benchmark quality подтверждён.

## Horizon D — расширение по спросу

### Stage 16. Browser automation + platform policy — conditional

API/connector → Playwright/Browser MCP → UI automation. Node является edge runtime,
не core dependency.

### Stage 17. Video production — conditional

FFmpeg composition, Blender Python/native addons и внешние generators подключаются
через artifacts/policy/jobs. Ни один provider не становится внутренней архитектурой.

### Stage 18. Distribution adapters — conditional

Публикация только через guarded prepare/confirm, platform-policy checks и точную
привязку к artifact hash/destination/cost.

### Stage 19. Additional professional capabilities — conditional

Добавлять capability только при наличии реального сценария, quality benchmark,
владельца adapter и exit criteria.

### Stage 20. Operations audit — planned

Проверить recovery, upgrades, retention, logs, secrets, costs, dependency decay,
single-binary promise и no-zoo ограничения на реальной эксплуатации.

## Definition of Done для любого этапа

1. Реальный пользовательский сценарий проходит end-to-end.
2. Policy применяется технически, а не только prompt-инструкцией.
3. Ошибки структурированы; retry/idempotency определены.
4. Есть positive, negative и integration tests пропорционально риску.
5. Документация отражает фактическое состояние, а не намерение.
6. Runtime snapshot не подменяет versioned requirements.
7. Новая зависимость имеет причину, lockfile и план удаления/замены.
8. Нет нового process/service без независимого lifecycle requirement.
9. Editable sources и fixtures сохранены.
10. Следующий этап не начат до прохождения exit gate текущего.
