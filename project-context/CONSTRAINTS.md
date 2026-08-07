# Constraints

- Chat/model hints не определяют effective risk.
- Бинарные media payload не передаются через текстовый контракт.
- Artifact path после импорта обязан оставаться внутри Artifact Store.
- Никаких секретов в конфигурации, manifest или результате.
- Contract не является основанием для отдельного service.
- Новый platform core — Rust-first; native tools не переписываются ради Rust purity.
- Python slice удаляется только после Rust behavioral parity.
- MCP/transport/workflow engine не входят в Stage 1 migration scope.
- Один binary не является основанием для монолитной внутренней архитектуры.
