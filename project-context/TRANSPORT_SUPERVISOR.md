# Transport Reliability / Self-Healing Supervisor

Status: **ACCEPTED RELIABILITY FOUNDATION; LOW-POWER OPERATOR MODES TARGET-QUALIFIED; ORDINARY-CHAT ON/OFF GATES PASSED**.

This document defines the current transport reliability boundary for the ordinary-Chat Secure MCP Tunnel path. Transport Supervisor v1 was accepted through PR #94. PR #100 refines its idle operating model after target-Windows measurements showed that the previous tray/status cadence and 10-second supervisor cadence produced unnecessary transient PowerShell/WMI activity.

Transport reliability remains a lifecycle/operations boundary. It does not replace the Stage 26.3 deterministic procedure Control Plane and it does not create another planner.

## Normal transport

```text
ordinary ChatGPT
 -> Chat Local Bridge Test
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio secure semantic launcher
 -> canonical six-tool semantic projection
 -> deterministic Control Plane / focused capabilities
```

1MCP is optional internal Extension Manager infrastructure and is not a normal-route dependency or authorization source.

## Authority boundary

The Transport Supervisor may only maintain platform-owned transport/runtime state required by the user's explicit desired state. It is not:

- a general planner;
- the Stage 26.3 procedure Control Plane;
- a capability authorization engine;
- a generic process manager;
- a generic shell/Python execution surface;
- a tunnel CRUD administrator by default.

The persistent `tunnel_*` id remains the stable anchor. Normal recovery restarts/reconnects replaceable local processes around that same id. Routine recovery must not delete/recreate/rotate the remote tunnel resource.

The runtime remains in the current Windows user context because the accepted credential storage uses DPAPI `CurrentUser`.

## Persistent state and ownership

The current lifecycle separates user intent, runtime ownership and readiness evidence:

```text
state/desired-state.json
  -> requested running | stopped state

state/manager-owner.json
  -> authoritative manager ownership receipt

state/semantic-direct.json
  -> direct runtime/tunnel identity

state/supervisor.json
  -> last automatic deep-reconcile snapshot

state/manual-status.json
  -> lightweight Manual readiness/diagnostic receipt

state/operation-mode.json
  -> manual | automatic
```

`desired-state.json` is user intent. `manager-owner.json` proves manager ownership; it is not by itself a READY proof. In Manual mode the visible READY boundary also requires the persisted local MCP/tunnel readiness fields and a control-plane poll confirmation. A stale lifecycle completion must never overwrite newer user intent.

## Operator modes

PR #100 introduces two explicit persistent modes.

### Manual

Manual mode is the low-background explicit-control mode. Manual + OFF is the zero-periodic-work state.

```text
Manual + OFF
 -> supervisor Scheduled Task is not running a reconcile loop
 -> tunnel-client is stopped
 -> semantic node runtime is stopped
 -> no periodic manager Status call
 -> no periodic WMI/CIM process scan
 -> no periodic network health probe
 -> tray waits on FileSystemWatcher events
```

Start/Stop remains explicit through the public manager. During an explicit Start/Stop action the tray uses a short-lived 250 ms completion timer.

After a successful local Manual Start, if the state is still yellow, the tray performs only a bounded readiness-confirmation loop by launching the installed `tunnel-client health` command directly. It does not launch PowerShell and does not reconstruct ownership through WMI/CIM. The confirmation requires local process/health/ready evidence plus a successful control-plane poll. Failed confirmation attempts back off from 2 seconds up to 30 seconds and each health process is bounded to 8 seconds. Once READY is confirmed, that confirmation loop stops and the tray returns to event-driven idle behavior.

Therefore Manual green means that the manager-owned local runtime and control-plane path were successfully confirmed for the current running state. It does **not** mean that the tray continuously probes OpenAI or continuously proves the current ChatGPT app session after green.

The tray does not reconstruct process ownership with WMI. `manual-status.json` is a readiness/diagnostic receipt and must not become a contradictory authority source.

### Automatic

Automatic mode is an opt-in low-frequency reliability monitor.

```text
switch to Automatic
 -> one immediate supervisor Reconcile
 -> launcher sleeps for 30 minutes
 -> one next Reconcile
 -> repeat while mode remains Automatic
```

The Scheduled Task remains registered and its console-free `wscript.exe` launcher reads `operation-mode.json` directly through `Scripting.FileSystemObject`; reading the mode does not launch PowerShell. A deep reconcile launches one bounded PowerShell process, waits for it, and then the launcher is dormant for 30 minutes.

Switching back to Manual causes the automatic launcher/task to stop. Switching modes does not implicitly reverse the user's desired running/stopped state.

## Tray model

The tray is a low-power status/control client, not a second supervisor.

It reads cached/persisted state and reacts to file changes through `FileSystemWatcher`. It does not perform an idle `-Action Status` loop and it does not poll WMI/process ownership.

Visible states are intentionally simple:

```text
red    = explicitly stopped
yellow = switching / local runtime or control-plane confirmation incomplete
green  = manager-owned local runtime + MCP/tunnel + control-plane poll confirmed
```

Green is deliberately stronger than ownership alone, but it is still not a continuous end-to-end claim about the current ChatGPT app/connector session. Only a real ordinary-Chat semantic tool call proves that final route at that moment.

## Health model

Local runtime health, remote/control-plane health and ChatGPT-route health remain distinct evidence layers.

Minimum semantic distinction:

```text
desired_state
runtime / semantic process
mcp_ready
tunnel process / local health / local ready
control-plane poll freshness
remote tunnel metadata status
openai_control_ready
chatgpt_route_status
health_code
recovery action / retry state
```

Important invariant:

```text
local health != remote/control-plane health != ChatGPT route health
```

`openai_control_ready=true` is not proof that a particular ChatGPT app/connector route is currently usable. Only a real ordinary-Chat semantic tool call proves that final route.

## Startup failure handling

A transient remote/control-plane outage must not destroy an otherwise healthy local runtime.

The direct semantic startup path uses a real wall-clock 45-second local readiness budget. Local startup success requires tunnel process health, MCP readiness and exactly one expected semantic child. A missing fresh control-plane poll is recorded as degraded remote evidence rather than used as a reason to tear down the healthy local runtime.

Manual tray readiness remains stricter than local startup survival: after the manager owns the local runtime, the tray stays yellow until its bounded `tunnel-client health --require-control-plane-poll` confirmation succeeds. This separates two concerns:

```text
preserve healthy local runtime across transient network failure
!=
claim green before control-plane confirmation
```

## Failure classification and recovery

Failures are classified before recovery. Representative policy:

| Failure class | Automatic action |
|---|---|
| owned tunnel process died | bounded restart owned runtime, verify |
| semantic/MCP child unavailable | bounded restart owned runtime, verify |
| local health stale/unready | bounded restart/reconnect, verify |
| control-plane poll stale/disconnected | network-aware bounded recovery |
| network unavailable | wait/backoff; do not restart-storm |
| transient OpenAI 5xx/service unavailable | `wait_and_probe`; preserve healthy local runtime |
| remote metadata rate limit | `wait_and_probe` |
| 401 authentication failure | block destructive restart loop; report auth requirement |
| 403 permission failure | block destructive restart loop; report permission requirement |
| conclusive remote resource loss | block local restart loop; require operator/rebind action |
| ChatGPT/app route failure with healthy local runtime | report route failure; do not destroy healthy local runtime |
| ambiguous/unknown evidence | conservative degraded state; no destructive guessing |

`REMOTE_METADATA_UNAVAILABLE` and `REMOTE_METADATA_RATE_LIMITED` are non-destructive remote-observation failures: the correct action is `wait_and_probe`, not local runtime churn.

## Resource model

The original Supervisor v1 accepted a frequent reconciliation loop as a correctness fallback. Physical target use later showed that the combined tray + supervisor cadence was too expensive for an otherwise idle laptop.

The qualified low-power model is now:

```text
Manual + OFF:
  zero periodic platform work

Manual + ON, before READY confirmation:
  bounded direct tunnel-client health confirmation with backoff
  no PowerShell/WMI ownership/status loop

Manual + ON, after READY confirmation:
  runtime remains running
  tray returns to event-driven idle
  no periodic deep supervisor reconcile

Automatic:
  one deep reconcile immediately
  then 30-minute dormant interval
```

Heavy capabilities such as Playwright or local visual models remain task-driven/on-demand.

The resource acceptance metric is physical behavior, not an estimated interval. PR #100 target evidence is indexed in `EVIDENCE_INDEX.md`.

## Console-free Windows persistence

The supervisor and status indicator are installed as current-user Scheduled Tasks with limited privileges and console-free `wscript.exe` launchers. The supervisor task remains independent from tray lifetime.

The launcher must not create a visible PowerShell console window during normal operation. Manual mode may leave the supervisor task in `Ready` rather than `Running`; this is expected.

## Current accepted/qualified physical evidence

Transport Supervisor v1 already has accepted target evidence for:

- killed tunnel-client recovery;
- network disconnect/reconnect behavior;
- sleep/resume;
- reboot/logon restoration;
- ordinary-Chat semantic E2E after reboot;
- resource/recovery latency;
- console-free task launch;
- persistent desired-state/runtime-owner separation.

PR #100 additionally qualified on the target Windows laptop:

- tray/status reduction removed the old 2-second manager status path;
- Manual + OFF leaves no tunnel-client/node runtime and produced zero measured CPU delta for the remaining background tray PowerShell over a 60-second idle observation;
- Automatic performed one immediate Reconcile and then left `supervisor.json` unchanged for the following 60 seconds, consistent with the 30-minute dormant interval;
- during that Automatic observation the local runtime/MCP/tunnel were ready; transient `REMOTE_METADATA_UNAVAILABLE` was truthfully reported without restart churn;
- a later physical failure exposed that startup incorrectly destroyed the local runtime after transient control-plane TLS timeouts; the startup boundary was corrected so locally healthy runtime survives that outage;
- Manual green was tightened so ownership alone is insufficient: current-run local readiness and a successful control-plane poll confirmation are required;
- all seven required GitHub workflows passed on exact head `092081be7d99dbeee6f092a6d48066d1a95e37c2`;
- on that exact installed head, a fresh ordinary-Chat `Chat Local Bridge Test` `workspace_read(operation=roots)` succeeded and returned the configured `ordinary-chat-E4F49B4A` workspace;
- after explicit Manual OFF/red, the same ordinary-Chat call no longer reached the local tool and ended with remote `HTTP 504`, proving the route was unavailable while the local runtime was stopped.

Exact heads and measurements belong in `EVIDENCE_INDEX.md`, not here.

## Acceptance boundaries

Automated CI/contract tests must continue to protect:

- exactly six public semantic tools;
- direct-stdio normal binding;
- no normal-route 1MCP dependency;
- bounded Start/Stop authority in the manager;
- one authoritative manager-owned runtime;
- explicit Stop wins over stale recovery/start completions;
- no plaintext tunnel credentials in logs/state;
- console-free task launch;
- event-driven Manual idle after READY and zero-periodic Manual + OFF behavior;
- Manual green requires confirmed local readiness plus control-plane poll, not ownership alone;
- no recurring deep reconcile in Manual mode;
- 30-minute Automatic cadence;
- failure-class-aware non-destructive handling of transient remote/control-plane outages.

Physical target checks remain required when lifecycle/resource behavior changes. A passing unit/CI suite alone cannot prove idle CPU or end-to-end ordinary-Chat connectivity.

## Relationship to Stage 26.3 and Stage 27

- Stage 26.3 owns deterministic verified procedure execution.
- Transport Supervisor owns availability/lifecycle of the ChatGPT-to-local transport.
- Stage 27 distribution/maintenance will later absorb the accepted supervisor into update/repair/doctor/uninstall/key-rotation/lifecycle UX.

These authority boundaries must remain separate.

## Residual work

Remote OpenAI/network availability cannot be guaranteed by the local platform. Manual green is not a continuously refreshed ordinary-Chat E2E monitor after the initial current-run confirmation; a real ChatGPT semantic call remains the authoritative route proof when that distinction matters.

Observed ordinary-Chat `workspace_read(operation=roots)` latency after reconnect/restart improved across repeated successful calls from approximately `51 s -> 16 s -> 5.085 s`. The local semantic projection also lazily starts and caches its filesystem MCP backend on first use, so cold and warm calls are not equivalent. This latency is accepted as non-critical for the current transport correctness gate and optimization is explicitly deferred in favor of capability development. Future work may profile local cold-start versus OpenAI/tunnel delivery latency, but must not restore recurring PowerShell/WMI polling merely to reduce first-call latency.
