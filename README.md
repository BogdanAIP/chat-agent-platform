# Chat Agent Platform

Chat-centric платформа с **Rust-first локальным execution core** и тонкими адаптерами к зрелым инструментам. Chat остаётся primary intelligence; локальный `agent-platform.exe` отвечает за проверяемые контракты, Project Binding, tool selection, policy, artifacts, jobs, secrets и выполнение разрешённых capabilities.

Репозиторий публичный и распространяется по стандартной **MIT License** без дополнительных обязательных условий.

## Архитектура

```text
Chat / Codex
    |
    | GitHub context + optional thin remote call
    v
explicit Project Binding
    |
    +--> Yandex API Gateway -> Cloud Function -> Object Storage JSON rendezvous
    |                                      ^
    |                                      | outbound HTTPS long poll
    |                                      |
    `-------------------------------- agent-platform.exe (Rust)
                                           |-- strict capability requirements + locked executor
                                           |-- Policy Enforcement Point + one-shot guarded confirmation
                                           |-- Artifact Store + immutable input snapshots
                                           |-- persistent jobs + exclusive physical execution lock
                                           |-- Windows Credential Manager Secret Store
                                           `-- typed adapters
                                                 |-- FFmpeg / FFprobe
                                                 |-- REAPER via limited Lua/ReaScript
                                                 `-- Matchering 2.0.6 as replaceable Python edge process
```

Yandex не содержит media/business logic и не хранит media-файлы. API Gateway + Cloud Function + Object Storage используются только как небольшой JSON rendezvous для Hosted Chat -> Windows. Gateway нужен для сохранения GPT Actions Bearer auth: прямой Yandex Function URL использует `Authorization` для platform invocation и не подходит как внешний GPT Actions endpoint.

## Реализовано

- однозначный Project Binding и Project Memory/bootstrap;
- versioned JSON Schema contracts;
- fail-closed capability manifest/requirements: quality, reliability, determinism, execution path, fallback, enabled/cost gates;
- runtime capability profile, генерируемый из того же locked selection source of truth;
- Policy Enforcement Point с independently derived effective risk;
- one-shot guarded confirmation с TTL, stable action binding, replay protection и atomic consume;
- SHA-256 Artifact Store, recovery, data classification и controlled external staging;
- Windows Credential Manager Secret Store с executor ACL и zeroized secret buffers;
- persistent JobStore с idempotency/checkpoints/retry и exclusive per-job execution lock;
- immutable input capture: idempotency/policy identity привязаны к тем же байтам, которые реально обрабатываются;
- typed FFmpeg media operations, EBU R128 analysis/normalization, duration-aware timeouts;
- REAPER render adapter и реальный пользовательский Stage 12 acceptance;
- technical mastering + reference mastering через pinned Matchering 2.0.6;
- outbound-only Yandex relay через API Gateway с независимыми local/remote tokens, minimal public health и hosted Windows E2E;
- реальный Yandex API Gateway -> Function -> Object Storage -> Windows Stage 4 transport acceptance от 2026-08-09;
- Windows CI, pinned Rust/FFmpeg, RustSec/cargo-deny policy, CycloneDX SBOM, full-history secret scan, third-party license notices и Dependabot;
- активный `main-protection` ruleset с обязательными `verify-windows` + `gitleaks-history`.

## Текущая граница Stage 4

Реальная cloud-to-local цепочка уже доказана:

- `local_ping`: `pong=true`, `executed_locally=true`;
- `runtime_self_test`: success;
- controlled write/read и cleanup: passed;
- relay после acceptance штатно выключен;
- фоновых worker-процессов не осталось.

**Остался только финальный ChatGPT-originated call через private GPT Action.** Пока именно этот вызов не пройден, Stage 4 остаётся `partial / live-transport accepted`, а через remote surface разрешены только:

- `local_ping`;
- `runtime_self_test`.

## Быстрый локальный старт

Из корня репозитория:

```powershell
cargo run -- --repo-root . diagnose --project-id demo
cargo run -- --repo-root . bootstrap --project-id demo --capability media.inspect
cargo run -- --repo-root . audit --project-id demo
cargo run -- --repo-root . self-test --project-id demo
cargo run -- --repo-root . inspect --project-id demo --file C:\path\to\audio.wav
powershell -File scripts\verify.ps1
```

Relay после одноразовой настройки всегда остаётся выключенным, пока его явно не запустили:

```powershell
agent-platform relay start --project-id chat-agent-platform
agent-platform relay status --project-id chat-agent-platform
agent-platform relay stop --project-id chat-agent-platform
```

Инструкция по private GPT Action: `project-context/STAGE4_CHATGPT_ACTIONS_SETUP.md`.

## Помочь проекту / Support the Project

Поддержка проекта добровольная и **не является условием MIT License**. Способы поддержки и адреса для донатов будут добавлены отдельно; отсутствие доната никак не ограничивает права, предоставленные лицензией MIT.

## Правила развития

1. Не добавлять service/database/broker только «на будущее».
2. Использовать mature бесплатные/open-source edge tools, если они дают лучший результат, не перенося их внутрь core.
3. Никаких arbitrary shell/FFmpeg/Python options наружу: capabilities должны оставаться typed и policy-gated.
4. External side effect требует свежей policy evaluation и consumed `ConfirmationPermit`.
5. Любая новая capability должна иметь positive/negative/integration evidence пропорционально риску.
6. Python v0.1 остаётся только behavioral oracle до отдельного migration/removal gate.

Фактическое состояние этапов: `project-context/CURRENT_STATE.md`. Порядок дальнейшей работы: `project-context/ROADMAP.md`. Известные ограничения: `project-context/KNOWN_ISSUES.md`.