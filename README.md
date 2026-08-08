# Chat Agent Platform

Chat-centric агентная платформа с Rust-first локальным ядром и ограниченными
адаптерами к зрелым профессиональным инструментам. Chat остаётся основной
интеллектуальной частью; локальный `agent-platform.exe` отвечает за Project Binding,
выбор capability, policy, secrets, artifacts, jobs и проверяемое выполнение.

Целевая схема:

```text
Chat / CLI
   ↓
Project Binding → Capability Registry → Policy Enforcement
   ↓
Artifact Store + Secret Store + Persistent Jobs
   ↓
Rust typed adapters
   ├─ FFmpeg / FFprobe
   ├─ REAPER / ReaScript
   ├─ Matchering edge runtime
   └─ Yandex outbound relay для Hosted Chat → Windows
```

Python v0.1 пока сохранён только как behavioral oracle для parity-проверок. Он не
является целевым ядром платформы.

## Быстрый старт

```powershell
cargo run -- --repo-root . diagnose --project-id demo
cargo run -- --repo-root . probe --project-id demo
cargo run -- --repo-root . bootstrap --project-id demo --capability media.inspect
cargo run -- --repo-root . audit --project-id demo
cargo run -- --repo-root . self-test --project-id demo
cargo run -- --repo-root . inspect --project-id demo --file C:\path\to\audio.wav
cargo run -- --repo-root . produce-master --project-id demo --file C:\path\to\audio.wav
cargo run -- --repo-root . reference-master --project-id demo --target C:\target.wav --reference C:\reference.wav
cargo run -- --repo-root . relay status --project-id demo
powershell -File scripts\verify.ps1
```

Команды запускаются из корня репозитория. Публичные операции возвращают
структурированный JSON; бинарные данные в ответ не попадают. Файлы регистрируются в
локальном Artifact Store и дальше адресуются по `artifact_id`/SHA-256.

## Что уже реализовано

- однозначный Project Binding через `config/projects.yaml`;
- versioned contracts для tool request/result, artifacts, policy, secrets, jobs и
  relay;
- locked capability selection с quality/cost gates и независимым effective risk;
- Windows Secret Store на Credential Manager без собственной криптографии и без
  `unsafe` в platform crate;
- Artifact Store с pending lifecycle, SHA-256, atomic publish, recovery и
  ограниченным external staging;
- persistent JobStore с atomic state, checkpoints/retry и отдельной
  межпроцессной блокировкой фактического выполнения job;
- immutable SHA-verified input snapshots для Stage 15/19 workflows;
- typed FFmpeg/FFprobe операции без arbitrary shell/argument surface;
- REAPER adapter через ограниченный Lua/ReaScript и изолированные процессы;
- mastering analysis + technical delivery mastering;
- reference-based mastering через replaceable Matchering 2.0.6 edge runtime;
- outbound-only Yandex relay для Hosted Chat → локальный Windows agent с отдельными
  local/remote токенами, immutable Object Storage rendezvous и allowlist только
  `local_ping`/`runtime_self_test` на текущем Stage 4;
- Windows CI, real Matchering E2E, реальный пользовательский REAPER acceptance и
  Rust/Python parity checks.

## Текущее ограничение Stage 4

Код relay и hosted Windows E2E пройдены, но Stage 4 всё ещё считается `partial`.
Финальный gate требует реального пользовательского маршрута:

```text
ChatGPT → Yandex Function → Object Storage rendezvous
        → явно включённый agent-platform.exe на Windows
        → runtime_self_test → ответ обратно в ChatGPT
```

До прохождения этого сценария проект не утверждает, что Hosted Chat → local
execution доказан на пользовательском аккаунте.

## Что намеренно не добавлено

Нет отдельного workflow-сервиса, Redis, PostgreSQL, Kubernetes, постоянного VPS,
универсального shell executor или второго агентного фреймворка. Такие компоненты
добавляются только при доказанном lifecycle/scale requirement.

Browser automation, video production и distribution adapters остаются conditional.
Перед внешними публикациями/платными side effects требуется закончить guarded
prepare/confirm protocol.

## Source of truth

Фактическое состояние и порядок разработки:

- `project-context/CURRENT_STATE.md`
- `project-context/ROADMAP.md`
- код и CI evidence в репозитории.

`project-context/KNOWN_ISSUES.md` содержит только остающиеся известные ограничения.

## Лицензия

Публичная open-source лицензия пока не выбрана; репозиторий остаётся `UNLICENSED` до
отдельного решения о лицензировании.
