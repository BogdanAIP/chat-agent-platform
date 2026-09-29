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


### Target-Windows evidence for the refined lifecycle

The refined runtime code commit
`ce8549d8f5421867cf54a660edc77f141d2dcca4` was bootstrapped into the
Windows installed layout on 2026-09-29. SHA-256 comparison confirmed that the
installed `chat-platform-update.ps1` and
`runtime/control_plane/platform_update.py` bytes were identical to the
candidate checkout before the production-path probe.

The public installed CAP `procedure_run` surface then produced the following
evidence without any repository/branch/path/command authority in the request:

- `check` completed successfully against fixed
  `BogdanAIP/chat-agent-platform/main`; the updater result exposed
  `request_id=null`, confirming the refined updater result schema was live.
- A single `request_update` returned request id
  `79b6f844677a854d4f2e858947ba2057`; subsequent
  `status(request_id)` returned `completed`,
  `correlation_verified=true`, `recovered_by_status=false`, updater PID
  `23556`, and a request-specific updater result carrying the same request id.
- The previously failing concurrency case was repeated through the same public
  CAP surface. Two near-consecutive requests
  `f7df372271e64157a36f286480ed5698` and
  `4e91a236001a3e08d175e0803e4fb1ab` were both accepted. Their later
  `status(request_id)` calls both returned `completed` with
  `correlation_verified=true`; the request-specific updater PIDs were
  `23856` and `13916` respectively. Neither request consumed or invalidated
  the other's terminal evidence.

This is direct target-Windows evidence for the refined **runtime code** at
`ce8549d8...`. The commit that appends this evidence changes only this research
document; reviewers should therefore treat `ce8549d8...` as the physically
qualified runtime tree and separately verify that the evidence-only successor
does not alter runtime or test code.


## Refined exact-head target-Windows evidence

Refined candidate commit `ce8549d8f5421867cf54a660edc77f141d2dcca4` was installed into the
target Windows installed layout using the repository bootstrap. SHA-256 comparison
confirmed byte identity between the candidate checkout and
`%LOCALAPPDATA%\ChatAgentPlatform\app` for both
`scripts/chat-platform-update.ps1` and
`runtime/control_plane/platform_update.py`.

The installed CAP semantic runtime was then started and the production public
`procedure_run` surface was used, rather than importing the candidate directly from
the development checkout.

Observed production-path evidence on the target Windows host:

1. `platform_update_v1/check` completed with `status=current` against the fixed
   `BogdanAIP/chat-agent-platform/main` updater.
2. One `request_update` returned request id
   `79b6f844677a854d4f2e858947ba2057`; subsequent
   `status(request_id)` returned `completed`,
   `correlation_verified=true`, `updater_exit_code=0`, and a request-specific
   updater result carrying the same request id.
3. Two near-concurrent production `request_update` calls returned distinct request
   ids `793e3ca29de1b8d851bf9b86adeb04a5` and
   `edc2080f6e85e4717a81743c00111ad4`. Both later reconciled independently as
   `completed` with `correlation_verified=true`, distinct updater PIDs, exit code
   zero, and updater results carrying the matching request id. This is the same class
   of interleaving that physically reproduced the pre-fix false
   `updater_result_not_correlated` outcome on `7fda819...`.
4. Focused Windows tests covering the procedure, canonical updater contract, and
   Stage 26.3A surface passed 34/34. Semantic six-tool/procedure acceptance also
   passed against the refined candidate.

Crash/restart reconciliation is covered by the request-specific updater-owned durable
result contract and focused tests that remove the trampoline receipt from the state
model and recover it through `status(request_id)`. The bounded no-evidence case is
covered by a test that transitions to `manual_recovery_required` after the
reconciliation deadline rather than permitting indefinite `pending`.

This evidence is candidate-specific. Any subsequent material commit requires the
normal exact-HEAD test/CI/review reconciliation before merge.


## Stage Research re-entry — updater-owned request correlation and target continuity

This re-entry is required by `.agents/skills/stage-research/SKILL.md` v1.2 after
independent review exposed two failure classes that invalidated the previous
`NARROW` decision: concurrent request/result ownership and crash/restart loss of the
trampoline correlation owner. The previous instruction **"Do not change the canonical
updater" is superseded by the fresh decision below only for the bounded internal
request-correlation refinement described here.**

### Stage goal

Keep `platform_update_v1` a closed, fixed-official-main procedure while making
`request_update -> status(request_id)` truthful across:

- two near-concurrent accepted update requests;
- caller/CAP/OpenResearch teardown after acceptance;
- abrupt loss of the detached trampoline after updater launch;
- CAP restart before the secondary receipt is persisted;
- a future official-main update that would otherwise remove the very
  `platform_update_v1/status(request_id)` surface needed for reconciliation.

Generic shell, repository, branch, path, executable, command, environment or arbitrary
update-target authority remains out of scope.

### Current project baseline and observed failures

The existing updater remains the sole installation/effect owner and remains fixed to
`BogdanAIP/chat-agent-platform/main`. The semantic Control Plane remains the public
authority boundary.

Two failures are now direct project evidence:

1. on target Windows, two accepted no-op requests against `7fda819...` physically
   reproduced a false `updater_result_not_correlated` result because both trampolines
   consumed one global `platform-update-result.json`;
2. independent review showed that if the trampoline disappeared after durable
   acceptance but before its receipt write, no surviving component could safely
   terminalize that request, so `status(request_id)` could remain pending forever.

### Architecture lineage

- **Capability authorization / consequence policy — KEEP.** The deterministic project
  Control Plane still owns admission. The public request schema remains closed and
  cannot select an updater implementation or target.
- **Existing fixed official-main updater — REFINE, not replace.** The updater already
  owns the actual installation side effect and its mutex. It gains only an internally
  generated request nonce and one request-specific terminal-result write. No second
  executor or update service is introduced.
- **Local durable-state mechanics — REUSE_MORE.** Continue using the project's bounded
  sibling-temp/replace JSON persistence pattern and existing updater mutex rather than
  introducing SQLite, a WAL service, event bus, or generic journal.
- **Transition/completion authority — KEEP.** Updater/process exit is evidence for this
  bounded operation only; it does not replace project Verification Kernel or Finish
  Gate authority elsewhere.

No canonical reuse-baseline owner is replaced. The refinement keeps previously
project-owned authority project-owned, so no `ARCHITECTURE_REUSE_BASELINE.md` role
assignment changes.

### Architecture primitives and engineering domains

The refined mechanism uses only:

1. **Opaque request/idempotency token** — request correlation and duplicate-safe API
   design. AWS documents client tokens specifically for mutating asynchronous
   operations whose completion can be ambiguous to callers:
   https://docs.aws.amazon.com/ec2/latest/devguide/ec2-api-idempotency.html
2. **Request-owned durable terminal record** — local crash/restart reconciliation.
   The request nonce names a bounded terminal record written by the component that
   owns the physical update effect.
3. **Reconciliation from durable observed state** — controller/reconciliation design.
   Kubernetes controller guidance emphasizes idempotent reconciliation from current
   state rather than assuming immediate read-after-write freshness:
   https://kubernetes.io/blog/2026/07/29/controller-runtime-cache-explained/
4. **Atomic replacement of bounded state files** — filesystem persistence. Windows
   documents replace-file semantics as a single replacement operation:
   https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilea

These sources support the mechanism classes; project-specific correctness still
depends on the failure matrix and target-Windows falsification below.

### Alternatives considered

| Approach | Owner | Crash/concurrency behavior | Decision |
|---|---|---|---|
| Keep one global result and correlate by PID/time after child exit | trampoline + shared global file | physically failed: a second serialized updater may delete/replace the first result before its trampoline reads it | **REJECT** |
| Serialize admission so only one request may be accepted until receipt completion | admission layer | removes the observed A/B race but still leaves accepted state dependent on one trampoline owner; unnecessary caller-level serialization | **REJECT** |
| Capture only each updater's stdout in its trampoline | trampoline | fixes cross-request result mixing but still loses terminal ownership if the trampoline crashes after the updater effect | **REJECT** |
| Updater-owned `<request_id>.updater.json` plus status reconciliation | updater/effect owner | concurrent results are disjoint; terminal evidence survives trampoline/CAP restart; status can recover or fail closed after a bounded deadline | **SELECT** |

### Failure/crash matrix

The table below records every section-9 field per release-critical boundary. “Additional
physical effects” means effects permitted **after** the boundary is observed; completion
of an already-running updater is distinguished from authorizing another update attempt.

| Boundary | Authoritative durable state | Possible physical state | Fresh evidence required | Retry disposition | Maximum additional physical effects permitted | Invariant / test proving the rule |
|---|---|---|---|---|---|---|
| before durable request intent | none | no updater for this request has been authorized | none for the abandoned attempt; a later call must create a new request id | **allowed only as a new request** | at most one updater effect from the later independently accepted request | \`_request_update\` persists the request before trampoline launch; \`test_request_update_persists_random_correlation_and_detaches_trampoline\` proves ordering and closed reconciliation handle |
| request record durable, before trampoline delivery/launch | \`<request_id>.request.json\` only | no effect yet if launch truly has not occurred; after a crash the caller may not safely distinguish that state from a just-started trampoline | request-specific receipt or \`<request_id>.updater.json\`; absence alone is not success/failure evidence | **blocked; reconciliation required** | **0 retry effects**; no recovery path launches another updater; an already-dispatched original attempt may still complete once | \`status(request_id)\` returns \`pending\` until request-specific evidence or deadline; \`test_status_stops_reporting_pending_after_reconciliation_deadline\` proves bounded terminal ambiguity without retry |
| trampoline/updater delivery in progress or partial update effect | request record; no terminal request-specific updater result yet | updater may be running, quiesce may have happened, install/bootstrap may be partial | exact request-specific updater result with matching nonce/action/PID/time; canonical updater logs/state may inform manual diagnosis but do not authorize retry | **blocked; reconciliation required** | **0 additional update attempts**; the one already-authorized updater may finish, and canonical recovery may perform at most its one bounded platform-start recovery action | updater mutex + fixed argv prevent a second effect inside one attempt; updater recovery tests including \`test_running_platform_is_quiesced_before_bootstrap_and_restarted_after_failure\` prove bounded recovery |
| external update effect happened, before request-specific durable outcome write | request record only | installed files/state may already have changed; outcome file may be absent because of crash/persistence failure | only a safely correlated \`<request_id>.updater.json\` may terminalize automatically; otherwise manual inspection after deadline | **blocked; never blind-retry** | **0 additional update attempts** | updater writes request-specific terminal result before legacy global result; contract test asserts write ordering; no-evidence deadline test proves no automatic replay |
| request-specific updater outcome durable, before trampoline receipt | request + \`<request_id>.updater.json\` | update is terminal; trampoline may be alive, dead, or CAP may restart | validate nonce, \`action=update\`, integer updater PID and \`completed_at >= accepted_at\` | **retry blocked; reconcile to terminal receipt** | **0** | \`test_status_recovers_receipt_from_request_specific_updater_result\` proves \`status(request_id)\` synthesizes \`recovered_by_status=true\`; target-Windows installed-layout request/status physically reproduced this path contract |
| request-specific outcome replacement/persistence fails while effect may already be terminal | request only or prior valid request-specific file; legacy global file is non-authoritative for this request | update may be terminal even though new request-specific outcome was not durably published | existing valid request-specific file if any; otherwise no automatic terminal evidence | **blocked; after deadline manual recovery required** | **0 additional update attempts** | sibling-temp/replace JSON write is bounded; \`status\` never falls back to \`platform-update-result.json\`; deadline test prevents indefinite pending/retry |
| restart/load/reconciliation with receipt missing | request plus maybe request-specific updater result | updater may be gone; effect may be terminal | reread durable request-specific result and validate nonce/action/PID/time | **retry blocked; reconcile only** | **0** | \`test_status_recovers_receipt_from_request_specific_updater_result\`; installed target production \`status(request_id)\` returned correlated terminal state after detached execution boundary |
| stale or ambiguous observation after restart | request exists but no safely correlated request-specific result; any shared/global state may describe another request | physical state is one of: not started, in-flight/partial, or terminal without durable request-owned evidence; the system deliberately does not select among them from stale evidence | exact request-owned result only; shared global result is explicitly insufficient | **blocked; manual recovery after deadline** | **0** | \`test_trampoline_ignores_shared_global_result\`; behavioral future-target qualification injects a contradictory global result while requiring recovery from the request-specific result |
| two concurrent/duplicate callers each obtain distinct accepted request ids | two immutable request records; each has its own future updater/receipt path | updater mutex serializes physical updater executions, while both callers may be awaiting independent results | each caller must observe only its own \`<request_id>.updater.json\`/receipt | **no retry from either status path; reconcile independently** | per request: **0 retry effects** after acceptance; across two separately accepted requests, at most the two explicitly authorized updater attempts | target-Windows production probe on refined installed runtime submitted two near-concurrent requests and both independently returned \`completed\`, matching request ids and \`correlation_verified=true\`; pre-fix same probe reproduced the false-correlation bug |
| identity replacement / ABA-style reuse | request files remain in bounded history and request ids are 128-bit cryptographic nonces | an old terminal request may coexist with newer requests but has a distinct filename/nonce | exact request id supplied by caller and exact matching durable record | **old request is never reactivated; unknown/malformed ids fail closed** | **0** for the old identity | \`test_unknown_or_malformed_status_request_fails_closed\`, request-history bound, closed 32-lowercase-hex validation; no status operation can select repository/path/PID or another identity source |
| compensation/recovery while earlier update outcome is unresolved | request plus updater state/logs; possibly no request-specific terminal result yet | canonical updater may have performed one bounded recovery platform start after bootstrap failure | terminal request-specific updater result for automatic reconciliation; otherwise manual recovery | **update retry blocked**; compensation is not permission for a second update | at most **one bounded recovery platform-start effect**, and **0 additional update attempts** | canonical updater tests prove stop-before-bootstrap and one recovery start on failure; fixed updater mutex/argv and status logic expose no retry command |
| future official-main target before quiesce/bootstrap | current installed runtime remains authoritative; candidate exists only in detached worktree/cache | current CAP still running; candidate has caused no install effect | current updater must behaviorally qualify target request-recovery semantics, closed semantic schema, CLI dispatch and packaging before quiesce | **blocked if qualification fails** | **0** | \`Test-CapTargetPlatformUpdateProcedureContract\` executes candidate \`status(request_id)\` against isolated temp state (recovery, contradictory global result, pending, deadline) and validates dispatch/schema/packaging; negative target fixtures must fail before install |

No release-critical cell is answered with unknown. No cell permits automatic replay of an
ambiguous update effect. The only retry allowed without reconciliation is a brand-new request
created before any durable intent existed; all post-intent ambiguity is reconciliation-only or
manual-recovery-only.

### Failure shields

- `RequestId` is generated internally and validated as 32 lowercase hex characters.
- It is accepted by the canonical updater only with internal `Action=Update`.
- The updater writes `<request_id>.updater.json` **before** the shared legacy result.
- Request reconciliation reads only the request-specific result, never the global
  result.
- `status(request_id)` may synthesize a receipt only when request id, action,
  updater PID type and completion time validate against the durable request.
- A bounded reconciliation deadline terminates ambiguous no-evidence state as
  `manual_recovery_required`.
- Target continuity qualification must verify that the future target contains
  structurally valid Python procedure/CLI dispatch, the closed semantic
  `check/request_update/status` schema, request-correlated status rules, and bootstrap
  packaging for those assets before the current runtime is quiesced.

### Problem evidence vs solution evidence

**Problem evidence:** the two-request race was physically reproduced on the target
Windows host; independent review separately demonstrated the lost-trampoline
indefinite-pending state and future-target continuity gap.

**Solution evidence:** request/idempotency tokens are an established mechanism for
asynchronous mutating operations; durable per-operation state is owned here by the
component that performs the effect; reconciliation uses that durable operation-specific
state rather than transient caller state; atomic replacement preserves bounded local
state updates. The refined target-Windows concurrent probe demonstrates that two
distinct requests now both reconcile independently.

### Verification plan

The refined design must pass all of the following on one immutable final HEAD:

1. focused procedure/updater tests including wrong shared-global-result injection;
2. recovery from a missing trampoline receipt using the updater-owned
   `<request_id>.updater.json`;
3. bounded `manual_recovery_required` when safe terminal evidence never appears;
4. behavioral target-continuity probes that reject a target missing
   `platform_update.py` or the semantic `status(request_id)` contract;
5. target-Windows installed-layout `check -> request_update -> status(request_id)`;
6. target-Windows two-request concurrency with both requests independently correlated;
7. hosted CI/security/Windows acceptance;
8. a fresh ordinary-ChatGPT independent semantic review of the exact final HEAD.

Any new persistence owner, generic target selector, automatic retry after ambiguous
state, or new authority surface invalidates this decision and requires re-entry again.

### Complexity budget

The refinement adds one optional internal updater parameter, one request-specific
terminal file per bounded request, status recovery logic, and target-continuity
qualification. It replaces dependence on a racy shared-result read and avoids a new
database, daemon, event bus, generic task framework or second updater.

### Fresh architecture decision — NARROW

**NARROW. Production implementation may resume only for this bounded refinement:**

- keep the fixed official-main updater as sole installation authority;
- permit only internally generated `RequestId` to flow into updater
  `Action=Update`;
- let that updater durably own `<request_id>.updater.json`;
- let `status(request_id)` recover from that exact record or terminate ambiguity as
  `manual_recovery_required`;
- strengthen future-target continuity before quiesce so the remote update/status
  capability cannot silently remove itself.

Do **not** add repository/branch/path/executable/command selectors, a generic shell,
automatic retry of ambiguous update effects, a new persistence service, or broader
computer-control authority under this decision.
