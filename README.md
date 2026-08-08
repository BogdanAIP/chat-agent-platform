# Chat Agent Platform

Chat-centric платформа с **Rust-first локальным execution core** и тонкими адаптерами к зрелым инструментам. Chat остаётся primary intelligence; локальный `agent-platform.exe` отвечает за проверяемые контракты, Project Binding, tool selection, policy, artifacts, jobs, secrets и выполнение разрешённых capabilities.

Репозиторий сейчас приватный. Open-source лицензия **ещё не выбрана**; `LicenseRef-UNLICENSED` означает именно это и не является разрешением на публичное распространение.

## Архитектура

```text
Chat / Codex
    |
    | GitHub context + optional thin remote call
    v
explicit Project Binding
    |
    v
agent-platform.exe (Rust)
    |-- strict capability requirements + locked executor
    |-- Policy Enforcement Point + one-shot guarded confirmation
    |-- Artifact Store + immutable input snapshots
    |-- persistent jobs + exclusive physical execution lock
    |-- Windows Credential Manager Secret Store
    |-- typed adapters
    |     |-- FFmpeg / FFprobe
    |     |-- REAPER via limited Lua/ReaScript
    |     `-- Matchering 2.0.6 as replaceable Python edge process
    `-- outbound-only Yandex relay (Stage 4, off by default)
```

Yandex не содержит media/business logic и не хранит media-файлы. Cloud Function + Object Storage используются только как небольшой JSON rendezvous для Hosted Chat -> Windows. Высокоценные локальные capabilities через этот transport пока не экспортируются.

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
- outbound-only Yandex long-poll relay с независимыми local/remote tokens, minimal public health и hosted Windows E2E;
- Windows CI, pinned Rust/FFmpeg, RustSec/cargo-deny policy, CycloneDX SBOM и Dependabot.

## Текущая граница Stage 4

Hosted CI доказывает relay lifecycle, Credential Manager, local allowlist, lost-ACK retry, `local_ping`, `runtime_self_test`, gateway auth и immutable Object Storage rendezvous. **Последний реальный ChatGPT -> Yandex -> Windows -> ChatGPT round trip отложен вручную**, поэтому Stage 4 остаётся `partial / E2E-ready`.

До этого испытания через remote surface разрешены только:

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
agent-platform relay start
agent-platform relay status
agent-platform relay stop
```

## Правила развития

1. Не добавлять service/database/broker только «на будущее».
2. Использовать mature бесплатные/open-source edge tools, если они дают лучший результат, не перенося их внутрь core.
3. Никаких arbitrary shell/FFmpeg/Python options наружу: capabilities должны оставаться typed и policy-gated.
4. External side effect требует свежей policy evaluation и consumed `ConfirmationPermit`.
5. Любая новая capability должна иметь positive/negative/integration evidence пропорционально риску.
6. Python v0.1 остаётся только behavioral oracle до отдельного migration/removal gate.

Фактическое состояние этапов: `project-context/CURRENT_STATE.md`. Порядок дальнейшей работы: `project-context/ROADMAP.md`. Известные ограничения: `project-context/KNOWN_ISSUES.md`.
