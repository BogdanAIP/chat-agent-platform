# Constraints

These are architectural invariants, not historical stage notes.

- Chat/model hints never lower the effective risk derived by policy.
- External side effects require a fresh guarded policy decision and a consumed one-shot `ConfirmationPermit`.
- Binary media payloads are never transported through text contracts or the Yandex relay.
- Workflow processing must use immutable registered Artifact Store snapshots; policy/idempotency SHA must identify the same bytes actually processed.
- Artifact paths after registration must remain inside the bound Artifact Store.
- Secrets never appear in project config, capability manifests, runtime results, OpenAPI files or command-line arguments when a safer channel exists.
- Secret consumer identity comes from immutable locked `CapabilitySelection`, not caller-provided strings.
- One persisted job may have only one physical executor at a time.
- Unknown capability/config fields fail closed; configuration must not contain security-looking metadata that runtime silently ignores.
- New platform core code is Rust-first. Mature native/opensource tools are wrapped through typed adapters rather than rewritten for Rust purity.
- No arbitrary shell/FFmpeg/Python/REAPER command surface is exposed to Chat.
- Yandex transport stays thin: task/result/heartbeat JSON only, no media storage or business logic.
- Relay remains off by default; no Windows autostart/service unless a later lifecycle requirement justifies it.
- Database, Redis, message broker, workflow engine, VPS or extra daemon are not baseline dependencies and require an independently proven need.
- Python core/oracle is removed only after a deliberate parity/migration gate.
- Browser/video/distribution adapters are conditional on concrete scenarios, not installed as a speculative tool zoo.
- Repository remains private unless there is a deliberate product decision or GitHub Actions limits actually block development; public conversion is not a routine CI optimization.
- `LicenseRef-UNLICENSED` is metadata for the current no-license state, not permission to distribute the repository as open source.
