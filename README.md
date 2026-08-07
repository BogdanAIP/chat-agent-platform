# Chat Agent Platform — Rust-first vertical slice

Архитектура v1.4: один Rust local core и зрелые native-edge инструменты. Python
v0.1 временно сохранён как behavioral oracle до завершения parity migration.

Сценарий:

```text
CLI/Chat → Rust Project Binding → Policy Enforcement → Artifact Store
         → ffprobe + FFmpeg loudness analysis → validation → tool-v1 result
```

## Быстрый старт

```powershell
cargo run -- --repo-root . diagnose --project-id demo
cargo run -- --repo-root . probe --project-id demo
cargo run -- --repo-root . bootstrap --project-id demo --capability media.inspect
cargo run -- --repo-root . audit --project-id demo
cargo run -- --repo-root . self-test --project-id demo
cargo run -- --repo-root . inspect-artifact --project-id demo --artifact-id art_...
cargo run -- --repo-root . inspect --project-id demo --file C:\path\to\audio.wav
powershell -File scripts\verify-parity.ps1
powershell -File scripts\verify.ps1
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
```

Команды запускаются из корня репозитория. Rust `inspect` печатает JSON по контракту
`tool-v1`; бинарные данные в ответ не попадают. Входной файл импортируется в
локальный Artifact Store и дальше адресуется по `artifact_id`.

Временные Python bootstrap/audit/oracle команды описаны в
`project-context/MIGRATION_PLAN.md` и не являются целевой поставкой.

## Что реализовано

- однозначный Project Binding через `config/projects.yaml`;
- разделение project requirements и runtime capability profile;
- технический policy gate с independently derived effective risk;
- локальный JSON Artifact Store с hash, provenance и data classification;
- реальный Rust media inspection через `ffprobe` и `ffmpeg`/EBU R128;
- валидация технических метаданных и contract-compliant result;
- JSON Schema contracts для tool request/result, artifact, policy decision,
  secret reference и async job;
- проектный Bootstrap skill и минимальная загрузка Project Memory;
- Rust/Python parity script и сквозные тесты на настоящем WAV.

## Границы первой поставки

Это архитектурный vertical slice, а не вся платформа. Здесь пока нет remote
transport, MCP gateway, async job runtime, Secret Store, staging во внешние
сервисы и guarded prepare/confirm. Их добавление отложено до доказанной
необходимости, как требует исходный план.
