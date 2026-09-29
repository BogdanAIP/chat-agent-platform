# Platform Update Procedure v1 — Stage Research

Research date: 2026-09-28

Repository base: `BogdanAIP/chat-agent-platform@24ed938c587c9d3e2288c92bc156ccc476c955f3`

Applicable repository skills:

- `.agents/skills/stage-research/SKILL.md` v1.2
- `.agents/skills/source-code-research/SKILL.md` v1.0

## Goal

Allow the already-installed CAP runtime on the user's Windows machine to request and reconcile its own **existing bounded main updater** through the accepted `procedure_run` tool.

The change must not expose a shell, arbitrary executable, arbitrary repository, arbitrary branch, path selector, GitHub credential, or second updater implementation.

Selected public contract:

```text
procedure_run
  procedure=platform_update_v1
  action=check | request_update | status
```

The semantic surface remains exactly six public tools.

## Current project evidence

The accepted updater already exists in:

- `scripts/chat-platform-update.ps1`
- `scripts/chat-platform-update-core.ps1`
- `scripts/chat-platform-tray-update.ps1`
- `scripts/bootstrap-chat-platform.ps1`

Current updater properties on the exact base:

- source is fixed to `BogdanAIP/chat-agent-platform`, branch `main`;
- remote identity is allowlisted;
- update cache is a private bare repository;
- remote main is fetched atomically;
- installed -> target ancestry is checked before update;
- exact detached target worktree is created and verified;
- target must contain the accepted self-update contract before bootstrap;
- an OS mutex serializes updater ownership;
- installed runtime is quiesced before bootstrap and restarted after success;
- recovery attempts restart on update failure;
- durable status is written to `platform-update.json` and terminal outcome to
  `platform-update-result.json`.

Physical development-session evidence on 2026-09-28 additionally showed that the
installed updater can be invoked on the target Windows host through the existing
OpenResearch local runner, and `-Action Check` returned `status=current` with
installed and target SHA both
`24ed938c587c9d3e2288c92bc156ccc476c955f3`. This is bootstrap evidence, not
release acceptance for the new procedure.

## Source-code evidence

### Chat Agent Platform — exact base

Repository/ref:
`BogdanAIP/chat-agent-platform@24ed938c587c9d3e2288c92bc156ccc476c955f3`

Inspected mechanisms:

- `scripts/chat-platform-update.ps1`:
  mutex ownership, check/update decision, quiesce, exact worktree bootstrap,
  restart/recovery, terminal result;
- `scripts/chat-platform-update-core.ps1`:
  fixed official remote/main, SHA validation, atomic fetch, ancestry check,
  exact worktree;
- `scripts/chat-platform-tray-update.ps1`:
  updater launched as a separate process and terminal result reconciled by
  process id + completion time rather than stdout pipes;
- `runtime/semantic-projection/bin/semantic-control-plane-projection.mjs`:
  closed registered-procedure union and child environment allowlist;
- `runtime/control_plane/cli.py`:
  exact registered procedure dispatch.

Classification: **OPEN_IMPLEMENTED**.

Lesson: **REUSE_COMPONENT / REFINE ADAPTER ONLY**. The updater remains the sole
installation authority. The new procedure is only a fixed adapter to it.

### OpenAI Codex

Repository/ref:
`openai/codex@46d2585ea4347fe93446db57ec3e07ef234907e8`

Inspected:

- `codex-rs/tui/src/update_action.rs`
- `codex-rs/app-server-daemon/src/update_loop.rs`
- `codex-rs/app-server-daemon/src/manual_update.rs`

Mechanism observed:

- update choices are represented as typed variants rather than caller-supplied
  arbitrary command strings;
- daemon/update-loop owns scheduled/manual update lifecycle;
- Windows updater ownership and restart/handoff are explicit;
- manual update requests are separated from updater execution ownership.

Classification: **OPEN_IMPLEMENTED**.

Lesson: **REFERENCE_ONLY**. Preserve a typed, fixed update request surface and
keep lifecycle ownership below Chat planning authority.

### GitHub Desktop

Repository/ref:
`desktop/desktop@f2686bcec9239a9f8c5d53e2e90bc3a4dd02059f`

Inspected:

- `app/src/ui/lib/update-store.ts`
- `app/src/main-process/app-window.ts`

Mechanism observed:

- update checks use a product-controlled update URL;
- update state is explicit;
- downloaded update installation is owned by the native updater;
- quit/install lifecycle is guarded rather than delegated to arbitrary renderer
  execution.

Classification: **OPEN_IMPLEMENTED**.

Lesson: **REFERENCE_ONLY**. Keep source selection fixed and expose lifecycle
state rather than generic local execution.

## Alternatives

1. **Continue using OpenResearch/Tura as bootstrap forever.**
   Works now, but makes CAP maintenance depend on an unrelated research runner
   and does not make CAP self-maintaining. Rejected as permanent architecture.

2. **Expose generic PowerShell/command execution through `procedure_run`.**
   It would solve update and many other tasks but materially destroys the
   closed-procedure trust boundary. Rejected.

3. **Add repo/branch/path parameters to an update procedure.**
   Unnecessary because the accepted updater already fixes official main.
   Rejected.

4. **Selected: fixed adapter around the existing updater.**
   Smallest change; no second installer; no generic dispatch.

## Authority and lineage

- Existing six-tool public semantic surface: **KEEP**.
- Existing deterministic Control Plane / registered procedure boundary: **KEEP**.
- Existing bounded official-main updater: **REUSE_MORE**.
- Tray UI remains a human entry point, not the only update authority: **REFINE**.
- Generic shell/native-host authority: **DEFER** to its own stage.
- Windows UIA/computer-use authority: **DEFER** to the next separately researched
  integration after self-update is established.

## Failure / crash matrix

| Boundary | Existing durable evidence | Possible result | Required behavior |
|---|---|---|---|
| Before request launch | existing update state/result | none | return error, no install |
| Request accepted, before updater mutex | no new CAP state owner | none | updater owns admission |
| Updater mutex busy | updater state/result | no second install | fail/observe; no generic retry path |
| During fetch/decision | updater state | no install or blocked | preserve updater error/blocked state |
| After quiesce, before bootstrap | updater state=installing | runtime temporarily unavailable | updater recovery owns restart |
| During bootstrap | updater logs/state | old/new runtime may be partial until bootstrap completes | canonical updater recovery; procedure never claims success |
| Update completes while caller disconnects | terminal result file | update may have succeeded | reconnect and call `status` |
| Caller repeats request after lost acknowledgement | updater mutex/current-state check | at most same official-main convergence | reconcile with `status`; no arbitrary second effect |

The procedure must never translate launch acknowledgement into update success.

## Selected v1 contract

`platform_update_v1` supports exactly:

- `check`: synchronously invoke installed updater with `-Action Check` and
  return its bounded JSON result;
- `request_update`: start the installed updater with fixed `-Action Update`
  in a separate process and return only `accepted` + process id;
- `status`: read only the fixed updater state/result files under
  `%LOCALAPPDATA%\ChatAgentPlatform\state`.

No caller path, URL, branch, command, environment, executable or credential is
accepted.

## Verification

Before merge:

1. unit tests for exact schema and rejection of extra fields;
2. tests that adapter resolves only the installed updater path;
3. tests that subprocess argv is fixed and `shell=False`;
4. tests for malformed/missing state/result fail-closed behavior;
5. existing six-tool and procedure-surface tests remain green;
6. hosted CI on exact head;
7. fresh independent ordinary-ChatGPT semantic review on exact BASE..HEAD;
8. target Windows physical check: `check`, then an update/no-op update request,
   disconnect/reconnect if applicable, and `status` reconciliation.

## Decision

**NARROW**

Implement only the fixed official-main `platform_update_v1` adapter described
above. Do not add generic process execution, arbitrary updater source selection,
Windows GUI authority, or a new persistence owner in this stage.


## Target-Windows job-containment refinement

Physical probing on the target Windows host after the initial implementation found
that the live CAP semantic/tunnel/tray processes all report `IsProcessInJob=True`.
A first `request_update` probe launched from an OpenResearch local run without an
explicit breakaway flag did not leave a new updater terminal result after the
OpenResearch-owned run died, so plain `DETACHED_PROCESS` is not accepted as sufficient
evidence for escaping Windows Job Object ownership.

A bounded follow-up probe launched a harmless delayed Python child with
`CREATE_BREAKAWAY_FROM_JOB | DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP |
CREATE_NO_WINDOW`. The parent OpenResearch run exited, and a separate later run
observed the child-created `%TEMP%\\cap-breakaway-probe.txt` marker with exact text
`BREAKAWAY_OK`.

A second target-Windows probe then falsified the assumption that applying the
same breakaway flags directly to `pwsh.exe` is sufficient. A harmless detached
PowerShell child launched with the full flag set did not leave its delayed marker after
the OpenResearch-owned parent run exited. The same experiment with a detached Python
child did leave the expected marker `PYTHON_BREAKAWAY_OK` in a separate later run.

Refinement: `request_update` launches a fixed internal Python trampoline with
`CREATE_BREAKAWAY_FROM_JOB | DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP |
CREATE_NO_WINDOW`. The trampoline accepts no caller parameters, resolves only the
installed official-main updater, and runs that updater synchronously with fixed
`-Action Update` argv. This preserves the closed public contract while moving the
PowerShell updater below a process that is physically proven to survive the caller's
Job Object cleanup.

Target-Windows physical evidence on code head
`54050e70e4b177871c50388bb63ab1e088286758` completed the required no-op handoff:
`check` returned installed/target
`24ed938c587c9d3e2288c92bc156ccc476c955f3`; `request_update` returned
`accepted` with trampoline process id 21452; and a separate later `status` call
observed a fresh terminal updater result with process id 6428, action `update`,
status `current`, and completion time `2026-09-29T04:13:15.9253650+00:00`.
The parent OpenResearch run had already exited before reconciliation. This is direct
target-machine evidence that the trampoline survives caller teardown and that updater
state/result ownership remains with the existing updater.


## Stage Research re-entry — request correlation and trampoline lifecycle

Research re-entry date: 2026-09-29.

Trigger. Target-Windows probing falsified the original direct-PowerShell
process-containment assumption and introduced a breakaway Python trampoline.
Independent exact-head review then found that the original status contract
could misattribute a stale global updater result to a newly accepted
request_update. Both are material lifecycle and recovery changes, so the
earlier NARROW decision is not sufficient for the final architecture.

Fresh evidence and failure class. The accepted tray adapter already avoids
stale updater results by correlating the direct updater PID and a start-time
lower bound. The global updater result cannot itself carry a caller-generated
nonce without widening the accepted updater contract. Therefore the smallest
closed adaptation is to keep the updater unchanged and make the internal
breakaway trampoline the correlation owner. request_update generates an opaque
128-bit request id and durably records its acceptance time under the fixed CAP
state directory before launch. The trampoline receives only that internally
generated id, launches only the installed official-main updater, waits for the
exact child process, then accepts the canonical updater result only when its
action is update, its process_id equals that exact child PID, and its
completed_at is not earlier than the request acceptance time. It writes a
request-specific bounded terminal receipt. status requires the opaque request
id and reads only that request record and receipt; it never treats an unrelated
global result as the request outcome.

Authority. The public inventory remains six tools. No repository, branch,
path, executable, environment, shell, PID, HWND or backend selector is added.
The new request_id is a fixed-format read and reconciliation selector for a
procedure-created record, not execution authority. Request history is bounded
to 128 accepted records and admission fails closed at the bound.

Revised failure matrix.

| Boundary | Durable request evidence | Possible effect | Reconciliation |
|---|---|---|---|
| before request record | none | none | return error |
| record written, trampoline launch fails | request record may briefly exist | none | launch fails and record is removed |
| trampoline accepted, before updater launch | request record | none | status(request_id) is pending |
| updater mutex busy or no new canonical result | request record plus request-specific error receipt | none from this updater | stale global result is rejected by child PID and time correlation |
| updater runs and caller or CAP disconnects | request record | update may occur | breakaway trampoline survives and writes request-specific receipt |
| updater result PID, action or time mismatch | request record plus error receipt | unknown external updater activity | fail closed; no success attribution |
| matching updater terminal result | request record plus correlated receipt | canonical updater outcome recorded | status(request_id) returns only the matching receipt |
| repeated status | same fixed files | no new effect | idempotent read |

Fresh decision — NARROW. Proceed only with the request-specific correlation
adapter above, retaining the Python breakaway trampoline because target-Windows
evidence falsified direct PowerShell survival. Do not change the canonical
updater or expose generic process or shell authority. Before merge, re-run
focused and hosted tests, then install the exact candidate on the target
Windows host and execute the real ordinary-Chat to Secure MCP Tunnel to
installed semantic projection to procedure_run path for check, request_update,
caller or runtime teardown or reconnect as applicable, and status(request_id).
OpenResearch execution remains bootstrap and qualification support and is not
a substitute for that final production-path gate.

## Independent-review concurrency and crash-recovery refinement

A fresh ordinary-ChatGPT review of exact HEAD
`7fda8192129755accbe8c35098a8295032fecc87` identified two supported lifecycle
failures after falsification.

First, two valid `request_update` calls could both be accepted. The existing updater
mutex serialized updater mutation, but each detached Python trampoline read the same
global `platform-update-result.json` only after its updater process exited. A second
updater could therefore delete or replace that global file before the first trampoline
consumed it. This was reproduced physically on the target Windows host: two near-
simultaneous no-op requests were accepted; one reconciled with
`correlation_verified=true`, while the other recorded
`updater_result_not_correlated` despite `updater_exit_code=0`.

Second, the trampoline was the sole producer of the request-specific receipt. Abrupt
loss of that trampoline after durable acceptance could therefore leave
`status(request_id)` pending forever even if the canonical updater had already
reached a terminal result.

The selected refinement keeps the existing updater as the sole installation authority
but gives it one additional **internal correlation parameter**:
`-RequestId <32-lowercase-hex>`. This value is generated by the bounded procedure;
it is not a repository, branch, path, command, executable, environment or credential
selector. When present, the updater writes its normal global result for tray/backward
compatibility and also atomically writes
`%LOCALAPPDATA%\\ChatAgentPlatform\\state\\platform-update-requests\\<request_id>.updater.json`.
That request-specific result includes the nonce and updater PID.

The detached trampoline now launches the installed updater with its exact request id
and reads only that request-specific updater result. Concurrent requests therefore do
not consume one another's shared result file. More importantly, the updater itself is
now a durable request-specific terminal-result owner. If the trampoline disappears
before writing its secondary receipt, `status(request_id)` can validate the exact
request-specific updater result against the durable request record and synthesize the
receipt with `recovered_by_status=true`. If neither a receipt nor safely correlated
request-specific updater result appears within the bounded reconciliation deadline,
status becomes `manual_recovery_required` rather than remaining `pending`
indefinitely.

The target self-update continuity gate is extended so a future main cannot silently
remove the request-specific updater-result contract while retaining the remote
procedure. The public Chat schema remains unchanged apart from the already selected
closed `platform_update_v1` actions and request id required by `status`.

Required falsification before merge of the refined head:

1. focused procedure/updater tests, including a deliberately wrong shared global
   result while the correct request-specific updater result is present;
2. recovery of a missing trampoline receipt from an exact request-specific updater
   result;
3. bounded transition to `manual_recovery_required` when no safe terminal evidence
   exists;
4. target-Windows no-op request/update/status on the exact refined head;
5. target-Windows concurrent no-op requests with distinct request ids, both
   independently reconcilable;
6. fresh independent ordinary-ChatGPT semantic review on the exact refined head.

The reproduced `7fda819...` failure is evidence for the necessity of this refinement;
it is not evidence that the refined head is correct. Only the exact refined-head
physical and independent-review gates can establish that.
