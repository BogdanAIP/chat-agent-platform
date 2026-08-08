# Stage 4 archive reference

The uploaded `MusicVideoCompanion-Local-Agent-v0.2.1.zip` is treated as historical behavioral evidence, not as a runtime dependency.

Behavior retained from the proven experiment:

- permanent Yandex Cloud Function HTTPS endpoint;
- outbound-only Windows agent connection;
- `X-Agent-Token` authentication;
- `agent_action=poll` and `agent_action=result` protocol shape;
- IPv4/proxy/TLS hardening through Windows `curl.exe` fallback;
- reconnect/backoff behavior;
- explicit local tool allowlist;
- manual operator start/stop rather than mandatory autostart.

Behavior intentionally replaced:

- 1-second polling -> 25-second long polling;
- JSON config file raw token -> Windows Credential Manager;
- Python local agent -> `agent-platform.exe` Rust worker;
- process-window-only lifecycle -> typed `relay start/status/stop` commands;
- implicit function-instance state -> mounted Object Storage shared state;
- result retry that could re-execute a task -> local response cache keyed by request ID;
- test-file tools -> Stage 4 proof limited to `local_ping` and policy-gated `runtime_self_test`.

The original archive is not committed because it contains historical deployment-specific configuration and is not required to build or run the platform.
