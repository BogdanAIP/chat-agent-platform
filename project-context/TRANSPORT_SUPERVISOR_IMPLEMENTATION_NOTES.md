# Transport Supervisor implementation notes

Status: **hard local tunnel kill/recovery accepted; first network reconnect attempt failed and exposed a recovery-publication defect; remaining physical qualification is still in progress**.

## Current implementation slice

PR #94 implements the first self-healing transport-supervisor slice around the accepted direct-stdio semantic transport:

- `scripts/tunnel-reliability-health.ps1` classifies layered local/control-plane/remote health;
- `scripts/chat-platform-supervisor.ps1` owns desired-state reconciliation and bounded repair;
- `scripts/install-chat-platform-supervisor.ps1` installs the qualification supervisor as a current-user Scheduled Task;
- `scripts/transport-supervisor-qualification.ps1` performs the first target-Windows kill/recovery gate;
- automatic recovery is restricted to the exact installed direct controller;
- the persistent tunnel id remains stable and normal recovery never performs remote tunnel CRUD;
- authentication/permission/resource-loss states block destructive restart loops;
- transient remote metadata errors wait/re-probe;
- restart failures use 0/2/10/30s burst retry followed by indefinite low-rate retry with jitter.

## Durable recovery-transaction contract

A recovered runtime is not yet a completed recovery transaction. The supervisor must distinguish at least these facts:

```text
recovery attempt started
 -> owned runtime replacement invoked
 -> post-recovery runtime health verified
 -> recovery receipt committed
 -> supervisor snapshot committed
 -> later heartbeat proves supervisor continued reconciling
```

The physical gate must never infer success only from a new tunnel PID or a healthy manager status. A runtime may recover while the supervisor is blocked or unable to publish its own transaction state.

Publication failure after a verified runtime recovery is also different from runtime failure. It must **not** authorize another destructive restart of an already-ready runtime merely to recreate a missing receipt. The implementation should retry/reconcile the publication phase independently and remain idempotent.

A future persistent recovery-state schema should therefore be able to represent an in-progress/pending-publication recovery phase separately from the ordinary restart backoff count. If that representation is introduced, a later reconcile may finalize a verified pending transaction but must not fabricate attribution from ambiguous evidence.

## Failure-class-specific backoff

Retry/backoff state is scoped to the failure/recovery class that created it; it is not a global permission to postpone every later recovery action.

In particular:

```text
REMOTE_METADATA_UNAVAILABLE
 -> wait_and_probe
 -> next_retry_at in the future

then later:

LOCAL_TUNNEL_NOT_RUNNING
 -> restart_runtime
```

must **not** inherit the older `wait_and_probe` delay. A newly observed hard local runtime failure that requires `restart_runtime` preempts a pending wait-only metadata delay and may begin bounded local repair on the current reconcile cycle.

This preemption does not remove restart-storm protection. A `next_retry_at` produced by an actual failed `restart_runtime` attempt remains authoritative for later `restart_runtime` attempts. Authentication/permission/resource-loss `blocked` states continue to outrank local restart symptoms according to the health-classification contract.

This distinction is required because the supervisor observes multiple independent evidence layers whose failure class can change between reconciliation cycles. A retry deadline from one layer must not silently become authority over a different, higher-priority local failure class.

## Desired-state vs ownership boundary

The qualification slice currently derives desired running/stopped state from the existing authoritative manager owner record. That is acceptable as a temporary compatibility seam, but it is not the final product model.

Before Stage 27 product integration, persist these as separate concepts:

```text
desired_state
  = explicit user/platform intent: running | stopped

runtime_owner
  = exact controller/runtime identity currently holding lifecycle ownership
```

A missing/corrupt owner record must not silently rewrite user intent, and stale desired state must not authorize ownership of an arbitrary controller. The supervisor must continue to re-read exact ownership under the shared lifecycle mutex before mutation so explicit Stop wins.

## Physical qualification evidence

### Attempt 1 — lifecycle race

Exact tested head `90cce25d7c6dbe5b34d28a8647f105d6defc6c8d` failed before fault injection because the qualification installer started the supervisor before the harness prepared the baseline. The supervisor and the public manager then correctly serialized on `Local\ChatAgentPlatformControllerOperation`, exposing a qualification-only race. The harness was changed to install with `-NoStart`, prepare the baseline first, and start the supervisor only afterward.

### Attempt 2 — PowerShell `$LASTEXITCODE` misuse

Exact tested head `b28fd85b4ea7678a1a50cb557c2754e41d7439c2` failed immediately after a successful PowerShell installer invocation because the qualification harness read `$LASTEXITCODE` under StrictMode even though `.ps1` invocation does not guarantee that native-process status variable is set. Evidence recorded `supervisor_started=false`, proving that fault injection had not begun. The harness now relies on terminating PowerShell errors instead of `$LASTEXITCODE` for installer calls.

### Attempt 3 — inherited redirected-pipe hang in qualification manager mutation

Exact tested head `4878476d86216b633ab4cb22a716ee61e4ed2974` established a new direct runtime but the qualification process remained blocked before supervisor start. The manager child process had exited and the replacement tunnel was alive, but the harness was still waiting on `ReadToEndAsync().GetResult()` for redirected stdout/stderr inherited by a long-lived descendant. The qualification harness now captures stdout/stderr only for `Status`; `Start`/`Stop` mutations do not create redirected pipes.

### Attempt 4 — recovery occurred, but supervisor liveness/state contract was not actually proven

Exact tested head `4cefc75c7bc61df55d16893b2ef5e956e7843e76` reached the real fault injection:

- healthy baseline was recorded with `runtime_ready=true`, `openai_ready=true`, and `health_code=READY`;
- owned tunnel PID `10076` was killed;
- the same supervisor PID `16500` remained alive;
- a new tunnel PID `10772` appeared;
- manager status recovered to `runtime_ready=true`;
- qualification wrote `summary.json` with `result=PASSED` and `tunnel_pid_changed=true` / `supervisor_pid_stable=true`.

However, several minutes later both `supervisor.json` and `supervisor-recovery.json` were still absent while supervisor PID `16500` was still present. This exposed the inherited redirected-pipe hazard inside `chat-platform-supervisor.ps1`: the supervisor could launch the replacement runtime and then remain blocked while the qualification harness incorrectly treated process existence plus recovered manager runtime as success.

Therefore attempt 4 is **not accepted**.

### Attempt 5 — strict receipt gate correctly rejected an incomplete transaction

Exact tested head `28c6ab835bbe5800f53de94c945a3407cfbde217` passed the hosted checks and local transport-supervisor tests, then reached real fault injection. The exact owned tunnel process was killed and manager status later returned fully healthy state, proving that a replacement runtime came up.

The stricter qualification correctly returned `FAILED` because it did not observe a verified post-fault recovery receipt within the bounded window:

```text
Supervisor did not publish a verified post-recovery receipt.
```

This result is important: manager/runtime recovery alone is insufficient evidence for supervisor transaction completion.

Subsequent head `dfa6c930a6a179bc3426a46275215337e77627cf` hardened the receipt path by:

- canonicalizing persisted recovery timestamps as UTC;
- making qualification timestamp comparisons type-safe;
- retrying only the atomic state-file replacement during short Windows reader-sharing races;
- separating runtime-recovery failure from post-recovery receipt publication failure;
- preserving captured output for bounded `Status` calls while keeping controller `Start`/`Stop` mutations free of redirected inheritable pipes;
- capturing live failure receipts/log tail before qualification uninstall.

### Attempt 6 — remote wait backoff delayed a later hard local failure

Exact tested head `dfcd07c5d6becfff747b43c29d2ab752a5059347` established a healthy local direct semantic baseline but remote metadata probing was temporarily unavailable. The supervisor therefore recorded:

```text
health_code=REMOTE_METADATA_UNAVAILABLE
recovery_action=wait_and_probe
next_retry_at=2026-08-23T08:34:05.0039182Z
```

After fault injection killed the exact owned tunnel, the classifier correctly changed to:

```text
health_code=LOCAL_TUNNEL_NOT_RUNNING
recovery_action=restart_runtime
runtime_ready=false
```

but the supervisor retained the old `wait_and_probe` deadline and reported `backoff`. The first local recovery attempt did not begin until `2026-08-23T08:34:22.3980108Z`, leaving too little time inside the qualification's 120-second recovery window. The qualification correctly failed with:

```text
Supervisor did not recover the killed direct tunnel within 120 seconds.
```

Rollback restored the previous direct controller. The preserved state/log evidence proved that classification was correct; the bug was cross-failure-class reuse of retry state, not failure to observe the dead tunnel.

The correction makes a current `restart_runtime` action preempt an earlier `last_action=wait_and_probe` deadline while preserving deadlines created by failed `restart_runtime` attempts.

### Attempt 7 — hard local tunnel kill/recovery accepted

Exact tested head `b03442b66b05bf0f51000ff43f2f386e1495a1ec` was fetched from `origin/chat/transport-supervisor-v1`, checked against `REMOTE_HEAD`, mounted in a detached worktree, and checked again as `TEST_HEAD` before physical execution.

The qualification then killed exact owned tunnel PID `6812` and accepted only after all required transaction/liveness evidence was observed:

```text
TRANSPORT_SUPERVISOR_QUALIFICATION_RESULT=PASSED
OLD_TUNNEL_PID=6812
NEW_TUNNEL_PID=4828
TUNNEL_PID_CHANGED=True
SUPERVISOR_PID_STABLE=True
SUPERVISOR_RECEIPT_VERIFIED=True
SUPERVISOR_HEARTBEAT_VERIFIED=True
RECOVERY_RECEIPT_TOTAL_BEFORE_FAULT=0
RECOVERY_RECEIPT_TOTAL_RECOVERIES=1
RUNTIME_READY_AFTER_RECOVERY=True
HEALTH_CODE_AFTER_RECOVERY=READY
OPENAI_CONTROL_READY_AFTER_RECOVERY=True
DESIRED_STATE_BEFORE=running
DESIRED_STATE_RESTORED=running
```

Machine-local evidence directory:

```text
C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-qualification\run-20260823-115911
```

This physically accepts the hard local tunnel kill/recovery gate on exact tested head `b03442b66b05bf0f51000ff43f2f386e1495a1ec`. It does not accept later documentation-only heads or any remaining physical gate.

The `REMOTE_METADATA_UNAVAILABLE` state is not by itself evidence that local recovery failed. Local runtime, remote metadata/control-plane and ordinary-Chat route evidence remain independent dimensions.

### Attempt 8 — offline stability passed; reconnect gate failed and exposed recovery-publication bug

Exact tested head `cc41e836be890f88ae01d6cddfa0adf5e0d73fb7` was fetched and checked in a detached worktree before running `transport-supervisor-network-qualification.ps1`.

Machine-local evidence directory:

```text
C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-network-qualification\run-20260823-141923
```

The offline portion behaved as intended:

```text
runtime_ready=true
openai_ready=false
health_code=REMOTE_METADATA_UNAVAILABLE
recovery_action=wait_and_probe
control_plane_poll_fresh=true
```

For the full 45-second offline observation, the qualification reported no supervisor PID churn, no tunnel PID churn and no recovery-count increase. This confirms the current supervisor does not create a restart storm merely because remote metadata/control-plane access is temporarily unavailable.

The reconnect portion did **not** pass. The supervisor later classified `REMOTE_TUNNEL_DISCONNECTED` and began recovery at `2026-08-23T11:24:41Z`. Runtime recovery completed at about `11:25:25Z`, and `supervisor-recovery.json` advanced to `total_recoveries=1`, proving that a destructive runtime replacement occurred. That alone means the strict reconnect-without-local-churn gate was not satisfied.

The same physical run exposed a second independent defect after the runtime recovery: recovery snapshot publication failed with:

```text
recovery publication failed attempt=1 error_type=CommandNotFoundException
```

The cause was the PowerShell call-site expression:

```text
-SupervisorState (if (...) { 'healthy' } else { 'degraded' })
```

The script parsed, but PowerShell treated that grouped `if` form incorrectly at runtime in this argument position. The correction computes the state first as a normal PowerShell statement and then passes the value:

```text
$postSupervisorState = if (...) { 'healthy' } else { 'degraded' }
-SupervisorState $postSupervisorState
```

A regression test now forbids the old grouped form. The network qualification harness also records `reconnect-samples.json` with runtime/openai health, remote status, control-plane poll freshness, supervisor/tunnel PIDs and recovery count, and explicitly reminds the operator to restore any VPN/proxy path required for OpenAI before confirming reconnect.

Attempt 8 is **not accepted**. The strict no-local-churn reconnect criterion remains unchanged.

## Current candidate

The accepted hard-kill evidence remains permanently scoped to `b03442b66b05bf0f51000ff43f2f386e1495a1ec`; Attempt 8 remains a failed network qualification on `cc41e836be890f88ae01d6cddfa0adf5e0d73fb7`.

Current branch development contains the post-Attempt-8 recovery-publication fix, regression coverage, and improved reconnect diagnostics. Resolve the exact live PR head from GitHub before any physical qualification and bind the next run to that SHA; do not transfer evidence from older heads.

The implementation remains Draft while the remaining transport gates are qualified.

## Required next gate

Repeat the network disconnect/reconnect qualification on the exact post-Attempt-8 candidate:

```text
healthy running baseline
 -> external network disconnect while local processes remain intact
 -> transient remote/control-plane loss does not cause restart storm or churn a healthy local runtime
 -> network reconnect with the same external path restored, including required VPN/proxy routing
 -> automatic return to healthy state without manual manager restart
 -> supervisor PID remains stable
 -> tunnel PID remains stable
 -> recovery count does not increase
 -> later heartbeat proves continued reconciliation
```

If the tunnel cannot restore its control-plane connection without process replacement after the exact external route is restored, keep the gate failed and treat that as a transport-client/reconnect limitation rather than weakening the acceptance rule.

## Remaining physical gates

After network disconnect/reconnect, the remaining target-Windows gates are:

- sleep/resume -> automatic recovery;
- reboot/logon -> supervisor automatically starts and restores desired running state;
- ordinary ChatGPT semantic call -> fresh ChatGPT E2E receipt;
- idle resource-use measurement and recovery-latency evidence;
- remove the visible blank console window observed during Scheduled Task startup before product integration.
