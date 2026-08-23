# Transport Supervisor implementation notes

Status: **hard local tunnel kill/recovery accepted; external network disconnect/reconnect accepted; Windows sleep/resume accepted; remaining physical qualification is still in progress**.

## Current implementation slice

PR #94 implements the first self-healing transport-supervisor slice around the accepted direct-stdio semantic transport:

- `scripts/tunnel-reliability-health.ps1` classifies layered local/control-plane/remote health;
- `scripts/chat-platform-supervisor.ps1` owns desired-state reconciliation and bounded repair;
- `scripts/install-chat-platform-supervisor.ps1` installs the qualification supervisor as a current-user Scheduled Task;
- `scripts/transport-supervisor-qualification.ps1` performs the target-Windows hard local tunnel kill/recovery gate;
- `scripts/transport-supervisor-network-qualification.ps1` performs the observational target-Windows external network disconnect/reconnect gate;
- `scripts/transport-supervisor-sleep-resume-qualification.ps1` performs the physical Windows sleep/resume gate and verifies Windows power events;
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

## Network reconnect acceptance contract

The external-network gate has two phases with different safety requirements.

During the confirmed offline observation window, the local runtime is expected to remain intact and the supervisor must not create a restart storm merely because remote/control-plane metadata is unavailable:

```text
offline
 -> local runtime stays ready
 -> supervisor PID stays stable
 -> tunnel PID stays stable
 -> recovery count does not increase
```

After the external path is restored, two recovery modes are valid:

```text
A. seamless
   -> tunnel-client restores control-plane polling itself
   -> same tunnel PID
   -> recovery delta = 0

B. bounded_recovery
   -> external API is reachable but the existing control-plane poll remains stale
   -> supervisor classifies REMOTE_TUNNEL_DISCONNECTED -> restart_runtime
   -> exactly one committed recovery
   -> new tunnel PID
   -> same supervisor PID
   -> final supervisor state healthy / READY / recovery_action=none
   -> consecutive_attempts=0 and last_success_at is published
```

The bounded path is intentional fallback behavior rather than a restart storm. The pinned official `openai/tunnel-client v0.0.11` control-plane poller already retries transport failures with exponential backoff/jitter in-process; the supervisor remains a second-level recovery layer when remote metadata has recovered but the client poll is still stale.

The qualification harness therefore continues to forbid all recovery during the offline observation period, but no longer incorrectly requires zero recovery after connectivity returns. It also waits for the post-reconnect process state and recovery receipt to settle into one coherent pair before deciding whether the run was seamless or bounded recovery.

## Sleep/resume acceptance contract

The physical Windows sleep/resume gate must prove an actual power-state transition rather than a pause in the terminal. Accepted evidence is either classic sleep (`Kernel-Power 42` followed by `107`/Power-Troubleshooter `1`) or Modern Standby (`Kernel-Power 506 -> 507`) for at least the configured minimum duration.

The local lifecycle contract across an ordinary sleep cycle is:

```text
healthy running baseline
 -> real Windows sleep
 -> resume
 -> desired running owner survives
 -> same supervisor PID survives
 -> required external network/VPN/proxy path is restored before operator confirmation
 -> direct semantic runtime returns to READY
 -> tunnel resumes either seamlessly or through one bounded recovery
 -> later supervisor heartbeat advances
```

The supervisor does not own an external VPN/proxy client. Therefore a remote `401/403/resource_missing` observed while that external route is not yet restored remains a fail-closed `blocked` state and must not authorize destructive local restart. The qualification operator must restore any required external path before confirming resume and starting the bounded readiness window.

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

This physically accepts the hard local tunnel kill/recovery gate on exact tested head `b03442b66b05bf0f51000ff43f2f386e1495a1ec`. It does not accept later heads or any remaining physical gate.

### Attempt 8 — offline stability passed; reconnect exposed recovery-publication bug

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

The reconnect portion later classified `REMOTE_TUNNEL_DISCONNECTED` and began recovery at `2026-08-23T11:24:41Z`. Runtime recovery completed at about `11:25:25Z`, and `supervisor-recovery.json` advanced to `total_recoveries=1`.

The same physical run exposed an independent defect after runtime recovery: recovery snapshot publication failed with:

```text
recovery publication failed attempt=1 error_type=CommandNotFoundException
```

The cause was the PowerShell call-site expression:

```text
-SupervisorState (if (...) { 'healthy' } else { 'degraded' })
```

The correction computes the state first as a normal PowerShell statement and then passes the value:

```text
$postSupervisorState = if (...) { 'healthy' } else { 'degraded' }
-SupervisorState $postSupervisorState
```

A regression test forbids the old grouped form. Attempt 8 remains **not accepted** because recovery publication itself was broken.

### Attempt 9 — external network disconnect/reconnect accepted via bounded recovery

Exact tested head: `5c9e5b7bcd93fa054d99ef449d43d6d12df8c127`.

Machine-local evidence directory:

```text
C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-network-qualification\run-20260823-145633
```

The physical run again proved the offline safety contract:

- baseline supervisor PID `19872` remained unchanged;
- baseline tunnel PID `19664` remained unchanged throughout the 45-second offline observation;
- local runtime stayed ready while OpenAI/control-plane readiness became false;
- no recovery occurred during the offline observation (`total_recoveries=0`).

After the same external route was restored, saved reconnect samples showed this transition:

```text
2026-08-23T11:59:32Z
  runtime_ready=false
  openai_ready=false
  health_code=REMOTE_TUNNEL_DISCONNECTED
  recovery_action=restart_runtime
  remote_tunnel_status=ready
  control_plane_poll_fresh=false

2026-08-23T11:59:41Z
  runtime_ready=true
  openai_ready=true
  health_code=READY
  recovery_action=none
  remote_tunnel_status=ready
  control_plane_poll_fresh=true
```

The committed receipts then proved one bounded recovery rather than a loop:

```text
SUPERVISOR_PID=19872        # unchanged
OLD_TUNNEL_PID=19664
NEW_TUNNEL_PID=15156
RECOVERY_TOTAL=0 -> 1
consecutive_attempts=0
last_attempt_at=2026-08-23T11:58:57.4618035Z
last_success_at=2026-08-23T11:59:42.0780988Z
supervisor_state=healthy
health_code=READY
recovery_action=none
runtime_ready=true
openai_control_ready=true
remote_tunnel_status=ready
control_plane_poll_fresh=true
```

The old harness still emitted `FAILED` because its acceptance rule incorrectly required the tunnel PID and recovery count to remain unchanged even **after** connectivity had returned. That was a qualification-contract false negative, not a runtime failure. This is accepted by explicit evidence review against the corrected two-mode reconnect contract above; the exact stored samples/receipts are the primary physical evidence.

The corrected harness now accepts either in-process seamless reconnect (`same PID`, recovery delta `0`) or exactly one bounded supervisor recovery (`new PID`, recovery delta `1`, same supervisor PID, final healthy `READY`). It still rejects any PID churn or recovery while the machine is actually offline and waits for process/receipt publication to settle before classifying the mode.

### Attempt 10 — Modern Standby proven; external authorization path remained blocked

Exact tested head: `809abf1abd8b8e79fb387feb78f347432229099c`.

Machine-local evidence directory:

```text
C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-sleep-resume-qualification\run-20260823-162717
```

The machine physically entered and resumed from Modern Standby (`Kernel-Power 506 -> 507`) for `72.6 s`. Desired running ownership survived, supervisor PID `16120` and tunnel PID `15780` stayed stable, local MCP/tunnel readiness remained intact, and recovery count stayed `0`.

The run nevertheless failed because every post-resume sample for the full 240-second readiness window reported `REMOTE_TUNNEL_FORBIDDEN / blocked`. This fail-closed behavior was correct: the supervisor must not restart a healthy local runtime to try to repair a conclusive remote authorization result. The run is not accepted as sleep/resume evidence.

### Attempt 11 — Windows sleep/resume accepted via seamless Modern Standby recovery

Exact tested head: `809abf1abd8b8e79fb387feb78f347432229099c`.

Machine-local evidence directory:

```text
C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-sleep-resume-qualification\run-20260823-165435
```

The physical run used the same code head as Attempt 10 but restored the required external VPN/network path before the operator confirmed resume. The harness then produced machine-readable `PASSED` evidence:

```text
TRANSPORT_SUPERVISOR_SLEEP_RESUME_QUALIFICATION_RESULT=PASSED
POWER_EVENT_MODE=modern-standby
SLEEP_EVIDENCE_SECONDS=20.329
SUPERVISOR_PID=3904
SUPERVISOR_PID_STABLE=True
OLD_TUNNEL_PID=3540
NEW_TUNNEL_PID=3540
RESUME_MODE=seamless
RECOVERY_TOTAL_BEFORE=0
RECOVERY_TOTAL_AFTER=0
RECOVERY_COUNT_DELTA=0
RESUME_RUNTIME_READY=True
RESUME_OPENAI_READY=True
SUPERVISOR_HEARTBEAT_VERIFIED=True
```

The summary also proved `desired_state_before=running` and `desired_state_after=running`. Therefore the ordinary Windows Modern Standby sleep/resume gate is accepted on exact head `809abf1abd8b8e79fb387feb78f347432229099c`.

Attempt 10 remains preserved as a useful negative control: an external VPN/proxy path is an environmental precondition outside the supervisor's authority, while conclusive `403` remains a blocked fail-closed state.

## Current candidate

Accepted physical evidence remains scoped to exact tested heads:

- hard local tunnel kill/recovery: `b03442b66b05bf0f51000ff43f2f386e1495a1ec`;
- external network disconnect/reconnect: `5c9e5b7bcd93fa054d99ef449d43d6d12df8c127`;
- Windows sleep/resume: `809abf1abd8b8e79fb387feb78f347432229099c`.

The moving PR head may contain later documentation or qualification-harness changes. Do not transfer physical evidence to that moving head; resolve the exact live head from GitHub before any later physical qualification.

The implementation remains Draft while the remaining transport gates are qualified.

## Required next gate

The next target-Windows physical gate is reboot/logon behavior:

```text
healthy desired-running baseline
 -> install/current-user supervisor task is present
 -> physical Windows reboot
 -> user logon
 -> supervisor starts automatically from the logon trigger
 -> desired running state survives reboot
 -> direct semantic runtime returns to healthy READY without manual platform restart
 -> any required recovery is bounded and durably receipted
 -> later heartbeat proves continued reconciliation
```

The reboot qualification must use a real Windows reboot and must not infer success merely from a later manually started runtime. Pre-reboot evidence and post-logon evidence need separate durable files because the qualification process itself cannot survive reboot.

## Remaining physical gates

After reboot/logon, the remaining target-Windows gates are:

- ordinary ChatGPT semantic call -> fresh ChatGPT E2E receipt;
- idle resource-use measurement and recovery-latency evidence;
- remove the visible blank console window observed during Scheduled Task startup before product integration.

A separate pre-product lifecycle step must also split persistent user `desired_state` from runtime ownership instead of using `manager-owner.json` as both concepts.
