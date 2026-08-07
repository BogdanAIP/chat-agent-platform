# Roadmap v1.4

Это исполняемый порядок разработки, а не список обещаний. Этап начинается только
после прохождения предыдущего обязательного gate и считается завершённым только по
проверяемому результату. Source of truth: этот файл + `CURRENT_STATE.md`;
runtime evidence хранится отдельно в `runtime/`.

## Статусы

- **done** — exit gate пройден реальным сценарием;
- **partial** — полезная часть реализована, exit gate не закрыт;
- **planned** — обязательный этап ещё не начат;
- **conditional** — выполняется только при доказанном gap/спросе.

## Horizon A — Rust core

### Stage 0. Reality baseline + Project Binding — partial

Есть однозначный Project Binding, разделение versioned requirements/runtime profile,
Rust local path и Chat → GitHub read/write. Hosted Chat → local execution/MCP surface
ещё не подтверждён; пользовательская локальная среда остаётся отдельным evidence.

Exit gate: каждый обязательный requirement имеет рабочий path либо явный gap и
fallback; соседний проект нельзя выбрать неявно.

### Stage 1. Rust vertical architecture validation — done

`binding → policy → artifact → FFprobe/FFmpeg → validation → tool-v1` реализован в
Rust. Python сохранён только как behavioral oracle. Реальный WAV, SHA-256, metadata,
policy-bypass negative test, fmt/clippy/tests и Rust/Python parity проходят.

### Stage 2. Core Contracts v1 — done

Versioned JSON Schemas для tool request/result, artifact, policy decision, secret
reference и job встроены в Rust; positive/negative fixtures общие с Python oracle.
Transport Contract не создаётся до появления transport.

### Stage 3. Project Memory + Bootstrap + Skills — done

Project Memory, generated capability audit, Bootstrap, media-inspection,
github-development, ограниченный mastering skill и handoff template существуют.
Новая сессия получает Project Binding, три минимальных context-файла и один
релевантный capability slice.

## Horizon B — безопасное выполнение

### Stage 4. Local execution + transport capability probe — partial

Локальный Rust `self-test` проверяет policy, ping, controlled write/read/cleanup,
FFmpeg/ffprobe health и contracts. Hosted Chat → local execution/reconnect ещё не
доказан.

Exit gate: либо принято ADR «transport не нужен», либо выбран один тонкий transport
adapter без media/business logic.

### Stage 5. MCP discovery/runtime comparison — conditional

Сначала native/direct MCP surface. 1MCP/ToolHive/другие слои добавляются только при
измеримом выигрыше по context/governance/isolation; кандидаты не устанавливаются
одновременно «на будущее».

### Stage 6. Tool Manifest + selection + hardened PEP — done

`tools.yaml` + `tool-lock.yaml`, required-quality/cost gates, immutable
`CapabilitySelection`, независимые `decision/effective_risk`, guarded confirmation
binding по capability/parameters/data class/hash. Model hint не снижает enforcement.
Windows CI покрывает negative gates и bypass resistance.

### Stage 7. Secret Store + consumer ACL — done

Windows Credential Manager через safe Rust backend, без собственной криптографии,
`unsafe`, vault или daemon. Metadata не содержит raw value; ACL принимает только
выбранный Stage 6 executor; краткоживущий secret buffer zeroize-ится. Windows test
доказывает allowed consumer и denial FFmpeg. Dependencies зафиксированы и имеют ADR
с планом замены.

### Stage 8. Artifact hardening + staging — done

Pending lifecycle, per-artifact locks, atomic publish/manifest, recovery records,
SHA/path/contract validation, fail-closed recovery. External staging разрешён только
для `public/project` и allowlisted executor; private/sensitive запрещены; временная
копия проверяется по SHA и удаляется RAII cleanup. Unknown orphan data сохраняется.

### Stage 9. Single-binary supervisor — conditional

`start/status/diagnose/stop`, tray/service — только после реальной независимой
lifecycle-потребности. Нельзя превращать платформу в постоянно работающий зоопарк.

### Stage 10. GitHub Actions — complete baseline

Windows CI выполняет fmt, strict clippy, Rust tests, contract fixtures, Python
oracle/parity, release build и artifact upload. PR → CI → squash merge доказан на
чистых hosted runners. Supply-chain audit/signing остаются отдельным усилением.

## Horizon C — профессиональное media/audio

### Stage 11. FFmpeg professional adapter — done

Typed capabilities: `media.inspect`, `media.validate`, `media.convert`,
`media.extract_audio`, `media.normalize_loudness`, `media.mux`. Один low-level
FFmpeg runner с timeout/kill; произвольные shell/FFmpeg args/output paths наружу не
выставлены.

- convert: lossless WAV/FLAC;
- extract: PCM 24-bit WAV;
- normalize: two-pass EBU R128 loudnorm + LUFS/true-peak post-validation;
- mux: video stream copy + FLAC audio → Matroska;
- outputs: temp → technical validation → Artifact Store → cleanup.

Requirements/tool lock/policy/runtime profile согласованы. Реальные Windows tests
проверяют все операции и негативный AAC case. PR #6 и push-CI на `main` зелёные.

### Stage 12. REAPER adapter — partial

Выбран путь Rust → ограниченный Lua/ReaScript → штатный REAPER CLI, без UI-click
automation и без нового daemon. Реализовано:

- typed session/track/marker specs;
- только зарегистрированные и FFprobe-valid audio artifacts как inputs;
- Lua escaping и pre-execution validation;
- driver для track creation, media import, markers, render settings и project save;
- WAV render config через documented `RENDER_FORMAT="evaw"`;
- `reaper-probe` для безопасного обнаружения `reaper.exe`;
- запрет `os.execute`, `io.popen` и generic `Main_OnCommand`;
- locked capability `audio.reaper_render` через Project Binding → selector → PEP;
- одна CLI-команда `reaper-render` для полного локального сценария;
- authoring только в `-newinst`, completion marker после сохранения `.rpp`,
  authoring timeout 45 сек;
- `-renderproject` в отдельном instance, render timeout 3 минуты;
- render считается готовым только после стабилизации файла и FFprobe-valid WAV;
- sample rate дополнительно проверяется Stage 11 inspection;
- `.rpp` и WAV импортируются обратно в Artifact Store;
- request-scoped workspace очищается на success/error/timeout.

Windows CI проверяет generator, corrupt-media rejection, strict Clippy, lifecycle
helper на реально запускаемом изолированном child process и полную регрессию. REAPER
на hosted CI намеренно не устанавливается/не эмулируется, поэтому зелёный CI не
подменяет реальное пользовательское E2E.

Exit gate **ещё не пройден**: на машине с установленным REAPER нужно реально
выполнить `reaper-render` и получить валидированные project + rendered WAV artifacts.
После успешного результата обновляется runtime evidence, Stage 12 становится `done`
и только тогда начинается Stage 13.

### Stage 13. Audio analysis/mastering decision layer — planned

Создать benchmark corpus и decision logic поверх зрелых анализаторов.

Exit gate: technical metrics и professional quality acceptance проходят на
репрезентативном корпусе, а не на одном тестовом тоне.

### Stage 14. Workflow runtime gate — conditional

Сначала лёгкий Rust job state machine: persistence, cancellation, idempotency,
retry, checkpoints, resume. Prefect/Node-RED/другой runtime сравнивать только если
реальный workflow остаётся незакрыт.

Exit gate: выбран один runtime; нет собственной копии Prefect и лишнего сервиса.

### Stage 15. Production mastering workflow — planned

Первый длинный workflow с job ID, recovery, artifacts и quality gate.

Exit gate: результат переживает новую сессию; retry не дублирует опасные действия;
benchmark quality подтверждён.

## Horizon D — расширение только по спросу

### Stage 16. Browser automation + platform policy — conditional

API/connector → Playwright/Browser MCP → UI automation. Node только edge runtime,
не core dependency.

### Stage 17. Video production — conditional

FFmpeg composition, Blender API/addons и внешние generators подключаются через
artifacts/policy/jobs; provider не становится внутренней архитектурой.

### Stage 18. Distribution adapters — conditional

Только guarded prepare/confirm, platform-policy checks и точная привязка к artifact
hash/destination/cost.

### Stage 19. Additional professional capabilities — conditional

Capability добавляется только при реальном сценарии, quality benchmark,
определённом adapter owner и собственном exit gate.

### Stage 20. Operations audit — planned

Recovery, upgrades, retention, logs, secrets, costs, dependency decay,
single-binary promise и no-zoo ограничения проверяются на реальной эксплуатации.

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
10. Следующий обязательный этап не начинается до прохождения exit gate текущего.
