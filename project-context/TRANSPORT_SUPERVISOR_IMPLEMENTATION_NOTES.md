# Transport Supervisor implementation notes

Status: **ACTIVE QUALIFICATION NOTES / branch-scoped**.

Branch: `chat/transport-supervisor-v1`.

This file records the first implementation slice under the authoritative `TRANSPORT_SUPERVISOR.md` design. It must not be read as accepted product evidence until hosted CI and the required target-Windows physical gates pass.

## Current slice

Implemented assets:

```text
scripts/tunnel-reliability-health.ps1
scripts/semantic-direct-controller.ps1
scripts/chat-platform-supervisor.ps1
scripts/install-chat-platform-supervisor.ps1
scripts/transport-supervisor-qualification.ps1
tests/test_transport_supervisor.py
tests/test_transport_supervisor_qualification_contract.py
```

Key implementation decisions:

- use existing pinned official `tunnel-client v0.0.11`;
- use official `health --json --require-control-plane-poll` and read-only `admin --json tunnels get`;
- keep `tunnel_*` id persistent;
- no automatic tunnel create/update/delete;
- no long-lived `OPENAI_ADMIN_KEY`;
- keep recovery ownership outside the direct controller;
- supervisor shares `Local\ChatAgentPlatformControllerOperation` with the public manager;
- after acquiring the mutex, supervisor re-reads `manager-owner.json`; explicit Stop wins over recovery;
- only the exact installed direct controller is accepted as an automatic recovery target;
- burst restart retry is followed by long-lived low-rate retry rather than permanent exhaustion;
- metadata-only transient errors use wait/re-probe rather than destroying a locally healthy runtime;
- Scheduled Task runs in the current user context with limited privileges;
- tray/bootstrap integration is deferred until recovery mechanics pass physical qualification.

## First physical gate

`transport-supervisor-qualification.ps1` installs the qualification build, establishes a direct semantic runtime baseline, kills only the owned direct `tunnel-client.exe`, and requires:

```text
TRANSPORT_SUPERVISOR_QUALIFICATION_RESULT=PASSED
TUNNEL_PID_CHANGED=True
SUPERVISOR_PID_STABLE=True
RUNTIME_READY_AFTER_RECOVERY=True
```

The gate also preserves JSON evidence and resource measurements under `%LOCALAPPDATA%\ChatAgentPlatform\transport-supervisor-qualification`.

This first gate deliberately does **not** disable networking, suspend/reboot the machine, or claim ChatGPT-route success. Those remain later physical gates.
