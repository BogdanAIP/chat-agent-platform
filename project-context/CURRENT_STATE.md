# Current State

Локальная часть Stage 0–1 реализована как исполняемый vertical slice. Поддерживается
одна capability: `media.inspect` через FFmpeg/ffprobe. Сквозной тест создаёт
настоящий WAV, применяет policy до импорта, регистрирует artifact, измеряет
metadata/LUFS и валидирует ответ.

Hosted Chat → GitHub write surface подтверждён реальным branch/edit/PR циклом в
PR #3. Hosted Chat → local execution transport и account-level MCP write/modify
ещё не проверены и не считаются доступными. Подтверждённый локальный execution
path сейчас — local/Codex CLI.

Stage 2 contracts формализованы JSON Schema и применяются в исполняемом пути.
Stage 3 завершён: Bootstrap skill валиден, а команда `bootstrap` возвращает только
Project Binding, три минимальных context-файла и релевантный capability slice.
Generated `CHATGPT_CAPABILITIES.md` строится из requirements и runtime profile,
поэтому человекочитаемый audit не создаёт второй source of truth.

Архитектурный план v1.4 принят с Rust-first/native-edge. Python v0.1 заморожен как
architecture spike и behavioral oracle.

Rust Stage 1 завершён локально: один `agent-platform.exe` выполняет
`diagnose/probe/bootstrap/audit/self-test/inspect/inspect-artifact`, применяет
binding/policy, импортирует и хеширует artifact, вызывает FFmpeg/ffprobe и
валидирует contracts. Artifact Store блокирует параллельные записи, атомарно
публикует manifest, проверяет containment и SHA-256 при чтении по ID. Release
binary baseline — 5 808 640 bytes.
Rust/Python parity подтверждён на реальном WAV; typed inspection возвращает
integrated LUFS, LRA и true peak dBTP.

Stage 2 завершён: шесть schemas встроены в binary, общие positive/negative fixtures
проходят в Rust и Python. Stage 3 завершён: четыре skills валидированы и
forward-tested. Единый `scripts/verify.ps1` проверяет Rust, contracts, Python
oracle, parity и release build на Windows CI. Внешние FFmpeg/ffprobe процессы
ограничены 60 секундами и принудительно завершаются с retryable `TOOL_TIMEOUT`
при зависании.

Stage 6 завершён на Windows-hosted runner: capability-level `tools.yaml` и
`tool-lock.yaml` выбирают locked executor только после mandatory quality/cost
gates; PEP хранит `decision` отдельно от `effective_risk`; model risk hint не может
понизить enforcement. Guarded preview получает SHA-256 confirmation binding,
зависящий от capability, parameters, data class и effective risk. Негативные тесты
доказывают rejection basic executor для professional requirement, cost gate и
инвалидацию binding при изменении artifact hash/parameters.

Stage 7 завершён на Windows-hosted runner. `SecretStore` хранит raw values в
Windows Credential Manager через safe Rust backend, а versioned metadata содержит
только secret ref, ACL и credential target. Consumer identity берётся из
`CapabilitySelection`, выданного Stage 6 registry; секрет доступен только внутри
короткого callback и затем стирается из локального буфера. Интеграционный test
доказывает разрешённый доступ, отказ `rust.local.ffmpeg` и отсутствие raw value в
metadata/errors. Зависимости зафиксированы в `Cargo.lock`; ADR-008 описывает их
назначение и замену без добавления отдельного vault/service.

Приватный remote `BogdanAIP/chat-agent-platform` работает через GitHub plugin и
авторизованный GitHub CLI. Проверены branch → draft PR → CI → ready → squash merge
для предыдущих PR; PR #3 дополнительно доказал прямой Chat → GitHub write path.
