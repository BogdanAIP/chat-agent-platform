# Transport Reliability / Self-Healing Supervisor

Status: **PLANNED / CROSS-CUTTING RELIABILITY TRACK**.

This document records the transport-reliability work selected after the 2026-08-21 repository audit and repeated real failures of the ordinary-Chat Secure MCP Tunnel path.

It is **not** accepted product functionality yet and it does **not** replace the active Stage 26.3 Verified Procedure Runtime work. Stage 26.3 remains the release-critical deterministic execution-Control-Plane track. Transport reliability is a separate lifecycle/operations boundary that should be hardened before we rely on hosted ordinary-Chat E2E as an always-available capability.

## Why this track exists

The accepted normal transport remains:

```text
ordinary ChatGPT
 -> Chat Local Bridge Test
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> secure direct stdio launcher
 -> semantic-projection
 -> scoped local capabilities
```

Stage 24.1 proved this direct stdio path and removed 1MCP from the normal semantic critical path. 1MCP remains internal diagnostic/adaptive/aggregation infrastructure only.

The 2026-08-21 audit found that current manager health is not equivalent to end-to-end availability. On `main`, `scripts/semantic-direct-controller.ps1` treats the official tunnel client's local `/readyz` result as both `tunnel_ready` and `mcp_ready`. The tray can therefore become green while the ChatGPT/OpenAI route is unavailable above the local client.

A real failure observed from `Chat Local Bridge Test` returned an OpenAI-side `MCP SSE probe returned 404` for the configured `tunnel_*` resource. That request did not prove a local semantic or 1MCP failure. Current local restart/status logic cannot reliably distinguish this class from recoverable local transport failures.

The goal is therefore not an impossible promise that the OpenAI service can never fail. The goal is a transport that is **self-healing for recoverable local/network failures, fail-closed for non-recoverable remote failures, and diagnostically truthful at every layer**.

## Audit baseline

### Already present and reusable

The repository already has most of the skeleton required for a supervisor:

- persistent installation under `%LOCALAPPDATA%\ChatAgentPlatform`;
- official pinned `tunnel-client` installation and hash verification;
- `CONTROL_PLANE_API_KEY` protected with Windows DPAPI `CurrentUser`;
- a persistent tunnel id; the direct controller already stores `tunnel_id` in `semantic-direct.json`;
- exact owned-process discovery;
- official local health URL file and `/readyz` probing;
- direct stdio semantic transport;
- idempotent Start/Stop lifecycle;
- target evidence that a killed tunnel-client can be recreated by an explicit manager `Start`;
- a tray process that already polls manager status;
- structured local logs and state files;
- CI, CodeQL and secret-history scanning.

Do **not** duplicate these mechanisms.

### Current gaps

The audit identified the following reliability gaps on `main`:

1. **Health conflation.** `mcp_ready` and `tunnel_ready` are derived from the same local readiness result instead of independent evidence.
2. **No explicit remote-control-plane dimension.** The manager does not currently expose remote tunnel metadata/auth/poll health as separate status.
3. **No long-lived desired-state reconciler.** Recovery happens when an operator invokes Start; there is no independent process continuously restoring the requested state.
4. **Tray is UI, not supervision.** Closing/restarting the tray must not decide whether transport recovery exists.
5. **No failure-class-aware recovery state machine.** Process death, local MCP failure, network loss, 401, 403, remote resource loss and OpenAI product-side route failures must not all trigger the same restart.
6. **No restart-storm protection with indefinite low-rate recovery.** A self-healing service needs burst backoff plus continued future re-probing; it must neither spin forever nor permanently give up on a transient outage.
7. **No reboot/logon/resume recovery contract.** The current manager is not yet an always-on user-context service boundary.
8. **No truthful ChatGPT-route dimension.** Local/control-plane health cannot by itself prove that a particular ChatGPT app is presently routed to the tunnel.
9. **No dedicated fault-injection acceptance matrix for the transport supervisor.** Existing direct-tunnel tests prove startup/lifecycle/equivalence, not long-lived recovery.

### Existing experimental branch

An unmerged branch already exists:

```text
chat/tunnel-reliability-e2e-health
```

At audit time it is three commits ahead of `main` and modifies:

```text
scripts/semantic-direct-controller.ps1
scripts/tunnel-reliability-health.ps1
tests/test_tunnel_reliability_health.py
```

It contains useful prototype ideas: distinct local/remote health, `admin tunnels get`, control-plane poll freshness, recovery state and a watchdog loop.

It is **not authoritative or accepted**. It has no open PR, does not yet provide the intended independent supervisor/tray architecture, its tests mostly exercise the health classifier rather than the complete watchdog lifecycle, and the audited controller contains at least one malformed `Stop-Process` invocation in the semantic-child cleanup path. Future implementation may salvage reviewed pieces, but must not promote this branch by assumption.

## Architectural target

### Boundary

The supervisor belongs to the existing Windows manager/lifecycle boundary:

```text
ordinary ChatGPT                      local deterministic procedure Control Plane
      |                                             |
      v                                             v
OpenAI Secure MCP Tunnel                     task/procedure execution
      |
      v
Transport Supervisor
  -> desired transport state
  -> lifecycle ownership
  -> health observation
  -> bounded recovery
  -> status cache / diagnostics
      |
      +-> tunnel-client
      +-> secure semantic launcher / semantic-projection
```

The Transport Supervisor is **not**:

- a general planner;
- the Stage 26.3 procedure Control Plane;
- a capability authorization engine;
- a generic process manager for unrelated applications;
- a tunnel CRUD administrator by default;
- a reason to expose shell/Python execution to ChatGPT.

Its authority is limited to the platform-owned transport/runtime processes and state required to maintain the user's explicit desired platform state.

### Persistent tunnel resource as anchor

The accepted `tunnel_*` id should remain a stable anchor.

Normal recovery must restart/reconnect replaceable local pieces around the same id:

```text
persistent tunnel id
      |
      +-> replaceable tunnel-client process
      +-> replaceable semantic child process
      +-> replaceable network connection / poll loop
```

Do not automatically delete/recreate/rotate a tunnel resource as routine recovery. A new tunnel id can require ChatGPT connector/app rebinding and increases privilege requirements.

The long-lived supervisor must **not require `OPENAI_ADMIN_KEY` by default**. Continue using the least-privilege runtime key already stored with DPAPI. Read-only remote-health checks may use only officially supported runtime-key operations. Tunnel create/update/delete remains an explicit operator/admin workflow if ever needed.

## Required health model

The supervisor must expose independent evidence rather than one green boolean.

Minimum machine-readable dimensions:

```text
desired_state                 running | stopped
supervisor_state              starting | healthy | degraded | recovering | backoff | blocked | stopped

semantic_process              running | stopped | unknown
mcp_ready                     true | false | unknown

tunnel_process                running | stopped | conflict | unknown
tunnel_local_health           true | false | unknown
tunnel_local_ready            true | false | unknown
control_plane_poll_health     true | false | unknown
control_plane_poll_age        seconds | null

remote_tunnel_status          ready | unauthorized | forbidden | resource_missing | unavailable | unknown
openai_control_ready          true | false | unknown

chatgpt_route_status          pass | fail | stale | not_checked
last_chatgpt_e2e_at           timestamp | null

health_code                   stable machine-readable reason
last_recovery                 structured receipt
recovery_count                integer
next_retry_at                 timestamp | null
```

Names may evolve during implementation, but the semantic distinction must remain.

### Important end-to-end boundary

`openai_control_ready=true` is **not proof of `chatgpt_route_status=pass`**.

The local supervisor can prove local runtime and supported remote-control-plane facts. Only an actual ChatGPT tool call can prove the final app/connector route. Therefore the status model must preserve `not_checked`/`stale` rather than fabricate end-to-end success.

A successful hosted semantic call may update a last-known E2E receipt, but stale historical success must never mask current local/control-plane failure.

## Failure taxonomy and recovery policy

At minimum classify these cases separately:

| Failure | Local automatic action |
|---|---|
| owned tunnel process died | restart owned transport, verify |
| semantic/MCP child unavailable | restart/recreate owned runtime path, verify |
| local health endpoint stale/unready | bounded reconnect/restart, verify |
| control-plane poll stale/disconnected | reconnect/restart after network-aware checks |
| network unavailable | wait; do not restart-storm |
| transient OpenAI 5xx/service unavailable | backoff + re-probe; preserve local desired state |
| 401 authentication failure | block restart loop; report `AUTH_REQUIRED` |
| 403 permission failure | block restart loop; report `PERMISSION_REQUIRED` |
| remote tunnel resource conclusively missing | block local restart loop; report `REMOTE_TUNNEL_RESOURCE_MISSING` / rebind requirement |
| ChatGPT/app-side route failure while local/control plane remain healthy | report product/route failure; do not destroy healthy local runtime merely to look active |
| ambiguous/unknown evidence | conservative degraded state; bounded diagnostics; no destructive guessing |

Do not infer `REMOTE_TUNNEL_RESOURCE_MISSING` from any generic 404 unless the officially supported remote metadata operation unambiguously establishes that result.

### Backoff must be self-healing, not permanently self-disabling

Use two recovery tempos:

1. **bounded fast recovery** for fresh local failures, e.g. short delays such as 0/2/10/30 seconds;
2. **long-lived degraded retry** after the burst budget is exhausted, e.g. low-rate periodic re-probes while desired state remains `running`.

A transient network/OpenAI outage must be able to recover hours later without the user reopening PowerShell. `RECOVERY_EXHAUSTED` must not become a permanent dead state for failures still classified as recoverable.

Authentication/permission/resource-loss states are different: they may remain `blocked` until operator action or credential/configuration change is detected.

Add jitter and a single-instance recovery lock so multiple components cannot create restart storms.

## Supervisor process model

Preferred target:

```text
Windows user logon
 -> one Chat Agent Platform Supervisor in the same user context
 -> read desired_state
 -> reconcile owned transport/runtime
 -> periodically observe health
 -> recover when allowed
 -> write atomic status/receipts
```

Use the same user context because current secrets are DPAPI `CurrentUser`. Do not move the runtime to `LocalSystem` without a separate credential/storage review.

The supervisor must be independent from tray lifetime. The tray becomes a status/control client:

```text
Supervisor = owns reconciliation
Tray       = displays status + requests Start/Stop/Repair
```

Closing the tray must not silently kill a platform whose `desired_state=running`.

A Windows Scheduled Task at user logon is the preferred initial persistence mechanism unless a later release-grade service design proves a better fit. Sleep/resume and network-change handling may be event-assisted, but a low-cost periodic reconciliation loop remains the correctness fallback.

## Resource budget

The supervisor must remain lightweight and must not make heavy specialist models always-on.

Initial design targets, to be measured on the real target Windows machine:

- local cheap health observation roughly every 10 seconds while healthy;
- remote/control-plane observation roughly every 30–60 seconds while healthy, with cache/rate protection;
- more active probing only during bounded recovery;
- tray reads cached status instead of launching expensive full diagnostics every 2 seconds;
- local VLM, Playwright browser and other heavy capabilities remain task-driven/on-demand where their existing lifecycle allows it.

Acceptance must record real Working Set, process count and idle CPU rather than rely on estimates.

## Upstream-first rule

Before implementing custom supervision, inspect the **latest stable, published** official `openai/tunnel-client` release and determine whether it already provides production-suitable runtime supervision/status primitives.

The project currently pins reviewed `tunnel-client v0.0.11`. Do not silently switch to unreleased `master` behavior. If a later stable release provides equivalent lifecycle/recovery functions, prefer adopting and qualifying that upstream capability over duplicating it in PowerShell.

Any version change requires the existing supply-chain discipline: exact release review, checksum pinning, CI and target acceptance.

## Intended implementation shape

Likely project-owned assets:

```text
scripts/chat-platform-supervisor.ps1        # new: desired-state reconciliation loop
scripts/semantic-direct-controller.ps1      # refactor: bounded lifecycle/probes, not endless ownership loop
scripts/chat-platform-tray.ps1              # refactor: display/control client
scripts/bootstrap-chat-platform.ps1         # install supervisor + persistence

%LOCALAPPDATA%\ChatAgentPlatform\state\
  supervisor.json                            # atomic current status
  desired-state.json                         # explicit running/stopped request
  semantic-direct.json                       # existing runtime/tunnel identity

%LOCALAPPDATA%\ChatAgentPlatform\logs\
  supervisor.log
  controller.log
  semantic-direct-tunnel-*.log
```

Exact file names may change after implementation review. Preserve one authoritative runtime owner and existing manager-operation serialization.

## Acceptance matrix

The track is not accepted until both automated and physical Windows tests prove recovery and truthful blocking.

### Automated / fault-injection gates

Required cases include:

1. healthy state keeps exactly one owner/process set;
2. killed tunnel-client is recreated once, not duplicated;
3. unavailable semantic child becomes `LOCAL_MCP_UNAVAILABLE` and is recovered or truthfully degraded;
4. stale control-plane poll is distinct from local `/readyz`;
5. simulated network loss causes wait/backoff, not restart storm;
6. recovery resumes after a long transient outage without manual Start;
7. 401 does not restart-loop;
8. 403 does not restart-loop;
9. conclusive remote resource loss does not restart-loop or auto-create a new tunnel;
10. healthy local/control-plane state plus simulated ChatGPT-route failure does not trigger destructive local churn;
11. malformed/corrupt supervisor state fails closed and remains repairable;
12. concurrent Start/Stop/Repair cannot create multiple authoritative owners;
13. logs/status never contain plaintext tunnel credentials;
14. tray status is derived from supervisor status, not from an independent conflicting process scan.

### Physical target Windows gates

Deliberately exercise:

```text
healthy baseline
 -> kill tunnel-client
 -> automatic verified recovery

healthy baseline
 -> network disconnect
 -> no restart storm
 -> network reconnect
 -> automatic verified recovery

healthy baseline
 -> sleep/resume
 -> automatic verified recovery

user logon / reboot
 -> supervisor starts automatically
 -> desired running state is restored

ordinary ChatGPT
 -> semantic tool call
 -> last ChatGPT E2E receipt updated
```

Also measure idle resource use and recovery latency.

If an OpenAI product-side failure is present during the test, the correct result may be truthful `CHATGPT_ROUTE=FAIL` with local/control-plane layers green. That is a diagnostic success, not permission to fake a green E2E state.

## Relationship to Stage 26.3 and Stage 27

This work is cross-cutting:

- Stage 26.3 continues to define deterministic verified procedure execution;
- Transport Supervisor defines availability/lifecycle of the ChatGPT-to-local transport used to reach those capabilities;
- Stage 27 distribution/maintenance will later absorb the accepted supervisor into installer/update/repair/doctor/uninstall/key-rotation/lifecycle UI.

Do not merge transport recovery logic into the Stage 26.3 procedure Control Plane. They have different authority and failure semantics.

The supervisor is operationally high priority because future hosted Stage 26.3 physical E2E should not require repeated manual tunnel diagnosis/restart just to reach the capability under test.

## Definition of done

Transport reliability is accepted only when all of the following are true:

```text
local health != remote health != ChatGPT route health
```

is represented truthfully; recoverable local/network failures restore themselves; non-recoverable authentication/permission/resource failures stop destructive retry loops; transient failures remain re-probed indefinitely at a safe rate; Windows logon/reboot/sleep-resume behavior is proven; tray and logs expose the actual failure layer; secrets remain isolated; and ordinary ChatGPT can again use the accepted semantic surface after recovery without the user acting as a PowerShell operator.
