# Architecture

## Target v1.4

Chat является primary intelligence. Project Binding, capability requirements,
runtime profile и Project Memory дают контекст. Один локальный Rust binary
применяет policy, управляет artifacts/jobs/secrets primitives и вызывает зрелые
native-edge tools через их штатные interfaces.

```text
Chat / Codex
    ↓ bootstrap + explicit project binding
agent-platform.exe
    ├─ contracts + policy
    ├─ artifact store
    ├─ lightweight jobs (только после Stage 1)
    └─ adapters
         ├─ FFmpeg → CLI
         ├─ REAPER → Lua/ReaScript
         ├─ Blender → Python API
         └─ Browser → Playwright/MCP
```

Remote Transport и MCP aggregation отсутствуют, пока capability probe не докажет
необходимость. Один binary не означает один неразделимый module.

## Transitional state

Текущий Python CLI — временный architecture spike и behavioral oracle для Rust
миграции. Он уже доказывает binding → policy → artifact → FFmpeg → validation.
Requirements и runtime availability хранятся отдельно. Shared JSON schemas,
fixtures и Project Memory переживают замену implementation language.

