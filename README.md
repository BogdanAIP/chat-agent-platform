# Chat Agent Platform

Chat-centric платформа с **Rust-first локальным execution core** и тонкими адаптерами к зрелым инструментам. Chat остаётся primary intelligence; локальный `agent-platform.exe` отвечает за проверяемые контракты, Project Binding, tool selection, policy, artifacts, jobs, secrets и выполнение разрешённых capabilities.

Репозиторий публичный и распространяется по стандартной **MIT License** без дополнительных обязательных условий.

## Архитектура

```text
ChatGPT private GPT Action
    -> Yandex API Gateway
    -> Cloud Function
    -> Object Storage JSON rendezvous
    <-> outbound HTTPS long poll
    <-> agent-platform.exe (Rust)

Codex MCP (optional)
    -> Gateway + Bearer
    OR
    -> direct public Function + X-MCP-Token
    -> same relay / same Windows agent
```

Yandex не содержит media/business logic и не хранит media-файлы. API Gateway нужен именно для GPT Actions Bearer auth: Yandex Cloud Functions удаляют входящий `Authorization` до пользовательского кода. Это не означает, что прямой Function URL бесполезен вообще. Для Codex текущая Function уже поддерживает MCP JSON-RPC и `X-MCP-Token`, поэтому direct Codex -> Function рассматривается как отдельный оптимизированный ingress-кандидат и будет принят только после реального Codex-originated теста.

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
- outbound-only Yandex relay с независимыми local/remote tokens, minimal public health и hosted Windows E2E;
- реальный Yandex API Gateway -> Function -> Object Storage -> Windows Stage 4 transport acceptance от 2026-08-09;
- application-auth regression test для `X-MCP-Token` direct Function candidate;
- Windows CI, pinned Rust/FFmpeg, RustSec/cargo-deny policy, CycloneDX SBOM, full-history secret scan, third-party license notices и Dependabot;
- fail-closed CodeQL v4 scan для Rust, Python и GitHub Actions; первый реальный SARIF-прогон прошёл без findings;
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

Отдельно, как необязательная оптимизация, будет проверен `Codex MCP -> direct Function + X-MCP-Token`. Его успех или неуспех не меняет критерий закрытия ChatGPT Stage 4.

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

План отдельной проверки direct Codex MCP: `project-context/STAGE4_CODEX_DIRECT_MCP_ACCEPTANCE.md`.

## Безопасность

Правила сообщения об уязвимостях и обращения с секретами: `SECURITY.md`. Не публикуйте реальные токены, credentials, private keys или exploit details в публичных issue/PR.

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