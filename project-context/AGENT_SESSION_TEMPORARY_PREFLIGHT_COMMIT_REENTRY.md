# Agent Session Temporary-Chat preflight commit/restart re-entry

Status: **STAGE RESEARCH BRIEF — NARROW**

Research date: **2026-09-04**

Triggering PR: **#149**

Accepted BASE: `90a8e16e6a1badecd3315968339ca691634b7ee4`

Applicable repository skill: `.agents/skills/stage-research/SKILL.md` v1.2.

This is a fresh-review-triggered re-entry for two release-critical crash/acknowledgement gaps in the adapter-local preflight mechanism. It does not reopen provider-conversation recovery, add a durable browser lease, or widen the generic Delegation state model.

## 1. Triggering findings and development-side falsification

Fresh ordinary-ChatGPT review of the then-frozen PR #149 head reported two P1 failures. Both survive direct falsification against the implementation.

### P1-A — commit-response ambiguity destroys the sole live launch mapping

Current `background.js::prepareLiveLaunch()` installs `launch_handle -> private run_id` in `LIVE_LAUNCHES`, calls `/preflight-commit`, and deletes the mapping on every commit-call exception.

The controller can durably commit `launch-attempted` and publish/activate the launch before the HTTP response reaches the MV3 caller. If that response is lost, the catch branch deletes the only live mapping even though the durable commit may already have happened. The qualification launcher independently watches controller-side `launch.json` and may then open the task URL. The opened task contains only the opaque handle, so it can no longer resolve to the private controller capability.

Disposition: **CONFIRMED**.

### P1-B — controller crash after durable launch commit can strand a still-live MV3 owner

`TemporaryControllerState` currently calls `prepare_temporary_session()`, which can durably mark `launch-attempted`, before the controller finishes its task launch projection/activation. A controller crash in that interval leaves the generic delegation non-prepared. The original MV3 worker may still hold the correct ephemeral handle mapping, but the restarted controller does not preserve the old handle and the launcher has no safe one-launch continuation path.

The previous crash matrix covered browser/service-worker loss but omitted this controller-commit/projection interval.

Disposition: **CONFIRMED**.

## 2. Current project truth and long-horizon boundary

The current accepted/narrow target remains:

```text
one manager
 -> one fresh read-only Temporary worker
 -> one bounded delivery
 -> one real correlated result when captured
```

`fresh_readonly_worker_v1` is an **ephemeral independence profile**, not the future persistent Agent Session model.

Required invariants remain:

- generic Delegation identity/state is provider-neutral;
- private durable `run_id` never appears in task/browser-history URL state, worker prompt or IndexedDB claim;
- a complete MV3/browser lifetime loss cannot reconstruct launch/Send authority;
- controller restart while the original MV3 lifetime survives may continue the already-selected single launch;
- ambiguous transport acknowledgement is observation uncertainty, not proof that a commit did or did not happen;
- no second physical Send, no provider-conversation recovery, no scheduler/event bus, no durable browser lease.

## 3. Architecture lineage

### Bounded Agent Session / Delegation lifecycle — `KEEP`

No new generic state field or generic recovery service is required. `launch-attempted`, delivery state and terminal result semantics remain unchanged.

### First-provider browser delivery ownership — `REFINE`

Keep the live MV3 `launch_handle -> private run_id` mapping and IndexedDB one-Send claim. Refine ownership so the **same neutral preflight tab** becomes the only task-navigation owner for that live handoff.

### Physical qualification launcher — `REFINE`

The PowerShell launcher continues to open the neutral preflight and verify exact source/runtime evidence, but it no longer independently opens the task-bearing URL from `launch.json`. Controller-side projection is evidence/status, not a second physical-launch authority.

### Persistent/recoverable browser identity — `DEFER`

No durable handle/session registry is introduced. If the MV3 lifetime dies, the mapping dies and task navigation cannot be reconstructed. Persistent existing-session identity remains future Prime/existing-session work.

## 4. Architecture primitives and adjacent domains

### Application-level idempotent commit replay

Domain: distributed-systems retry/idempotency.

Guarantee here: retrying the same preflight commit with the same preflight/launch identity cannot create another logical launch and must return semantically equivalent committed state when the first request already succeeded.

RFC 9110 §9.2.2 notes that retry after communication failure is safe only when request semantics are known to be idempotent or the original application can be detected. AWS Builders' Library similarly recommends a caller-provided request identity and semantically equivalent responses for safe retries when the first response may be lost.

Primary/strong sources:

- https://www.rfc-editor.org/rfc/rfc9110.html#name-idempotent-methods
- https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/

### Reconciliation from authoritative durable state

Domain: crash recovery / state-machine reconciliation.

Guarantee here: a failed `/preflight-commit` response is treated as ambiguous. While the original live MV3 mapping survives, the adapter may query the token-authenticated controller status and continue only if exact delegation/delivery/head/prompt/generation state proves that the commit happened and the delivery is still `prepared/open`.

The durable generic Delegation state remains authority; `launch.json` is not promoted into recovery authority.

### Single-owner same-page navigation

Domain: browser navigation / capability ownership.

Guarantee here: the neutral preflight content context that established the live mapping replaces itself with the task URL after commit proof. The PowerShell launcher does not create a second task tab from a controller projection.

`location.replace()` replaces the current page instead of adding the old preflight page as a new history entry. This is useful hygiene, but the security guarantee does **not** depend on history cleanup; task restoration in a new MV3 lifetime still fails because the live mapping is absent.

Reference:

- https://developer.mozilla.org/en-US/docs/Web/API/Location/replace

### Ephemeral MV3 live ownership

Domain: browser extension lifecycle.

Chrome explicitly documents that MV3 service-worker globals are lost on termination and that service workers should be resilient to unexpected termination. Here that ephemerality is deliberate authority scoping, not persistence: losing `LIVE_LAUNCHES` means fail closed.

Reference:

- https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle

## 5. Problem evidence vs solution evidence

### Problem evidence

- The controller mutates durable state before an HTTP acknowledgement is guaranteed to reach the extension.
- The current background catch path deletes the live mapping on any commit exception.
- The current PowerShell launcher independently opens the task URL once controller-side projection is visible.
- The controller can crash after durable `launch-attempted` but before completing its in-memory activation/projection path.

These facts create the two confirmed P1 windows.

### Solution evidence

RFC 9110 and AWS both distinguish communication failure from operation failure and support replay/reconciliation only when application semantics are idempotent. The existing controller already has the essential same-handle idempotent branch for a committed live handoff; the missing pieces are retaining the live mapping across acknowledgement ambiguity and reconciling against durable state rather than assuming an exception means rollback.

Chrome's documented MV3 lifecycle supports keeping the mapping intentionally non-durable: controller restart may be recoverable while the original service-worker lifetime survives, whereas service-worker/browser restart remains fail closed.

Using the original preflight tab as the single browser navigation owner removes the current split authority where the extension owns the private live mapping but PowerShell independently owns task-tab creation.

## 6. Materially distinct approaches

### A — keep current split launcher/extension ownership and add retries

Owner: controller projection + PowerShell task launch + MV3 mapping.

Failure: retry alone does not solve ambiguous commit unless mapping survives, and controller restart still leaves two independent notions of whether task navigation should happen.

Decision: **REJECT**.

### B — persist launch handle/private handoff durably for restart

Owner: new adapter durable browser-launch registry.

Strength: controller could reconstruct the exact task launch after restart.

Failure/cost: creates the durable browser/session identity mechanism that the ephemeral Temporary profile deliberately rejected; if it persisted private authority it would also weaken the complete-browser-loss boundary.

Decision: **REJECT** for #149.

### C — deterministic handle plus launcher re-open on restart

Owner: controller derives the same opaque handle and PowerShell may reopen the task URL.

Strength: no new durable state.

Failure: controller restart after the original task tab may already have opened can create a second physical child tab. IndexedDB still limits Send, but the generic one-launch contract is weakened and the launcher remains a second browser-launch owner.

Decision: **REJECT**.

### D — same-live-MV3 reconciliation + preflight self-navigation

Owner: durable Delegation state proves commit; the original live MV3/preflight tab owns the one browser navigation.

Mechanism:

```text
neutral preflight tab
 -> /preflight returns one handle + private correlation + task URL to MV3 only
 -> MV3 stores all of it in one live record bound to that preflight tab
 -> /preflight-commit
 -> success OR ambiguous response
 -> keep live record
 -> prove commit by exact token-authenticated /status when needed
 -> same preflight tab location.replace(task URL)
```

Controller crash after durable commit is recoverable because the surviving MV3 record still has the exact task URL/private token and can reconcile against the restarted controller's durable status. Browser/MV3 loss remains fail closed because the record disappears.

Decision: **SELECTED / NARROW**.

## 7. Failure / crash matrix

| Boundary | Durable state | Live browser state | Rule | Max extra physical task/Send effects |
|---|---|---|---|---|
| Before `/preflight` | prepared/open | neutral tab only | retry neutral preflight | 0 task / 0 Send |
| `/preflight` response before live-map install | prepared/open | no owned live record | fail/retry same neutral bootstrap | 0 / 0 |
| Live map installed before commit request | prepared/open | exact preflight tab owns handle/run/task URL | commit may be retried with same identity | 0 / 0 |
| Commit not applied, response fails | prepared/open | live map survives | retry same commit while same controller/preflight capability is valid; otherwise remain prepared and require a new neutral preflight | 0 / 0 |
| Commit applied, response arrives | launch-attempted/prepared/open | live map survives | same preflight tab navigates once | 1 task / at most 1 Send |
| Commit applied, response lost | launch-attempted/prepared/open | live map survives | do **not** delete map; reconcile `/status`; navigate only after exact committed status | 1 / at most 1 |
| Controller crashes after durable commit before HTTP response/projection | launch-attempted/prepared/open | original MV3/preflight survives | restarted controller reconstructs durable status; old live record authenticates with private run token; same tab then navigates | 1 / at most 1 |
| Controller restarts before commit applied | prepared/open | stale old live record may survive | old commit/preflight capability is not assumed current; no task navigation without committed status; new launcher may open a new neutral preflight | 0 until one new valid preflight |
| MV3/browser dies after durable commit before navigation | launch-attempted/prepared/open | live map gone | fail closed; restored opaque task/preflight data cannot recover private token | 0 additional |
| Preflight self-navigation committed, MV3 dies before first IndexedDB claim | launch-attempted/prepared/open | task URL may restore, live map gone | restored task fails before claim/controller access | 0 additional |
| First browser claim committed | launch-attempted/child-bound as applicable | existing one-Send fences apply | no second Send; browser-loss path remains fail closed | 0 additional Sends |
| Result recorded | delivered/recorded | browser irrelevant | terminal readback only | 0 |

No release-critical matrix cell requires a durable browser lease or permits a second Send.

## 8. Minimum implementation

Must have now:

1. `/preflight` computes the exact task URL but returns it only to the extension service worker; it does not publish/open it in browser history;
2. `LIVE_LAUNCHES` stores the task URL, exact correlation and the owning preflight `tab.id` together with the private run token;
3. once a live record is installed, a commit transport exception does **not** delete it;
4. same-live-tab retries reuse the same record/handle and the same commit identity;
5. ambiguous commit is reconciled through token-authenticated `/status` and exact delegation/delivery/head/prompt/generation checks;
6. controller status exposes enough non-secret provenance fields for that exact reconciliation;
7. the neutral preflight content context retries/reconciles while it remains alive and calls `location.replace(task_url)` only after commit proof;
8. PowerShell opens only the neutral preflight; it never independently `Start-Process`es the task URL;
9. a second preflight tab cannot replace/steal the live record already owned by another tab;
10. preserve existing IndexedDB unique claim, `LIVE_PRE_SEND_CLAIMS`, source attestation, delivery ambiguity and result capture semantics.

Explicitly not added:

- durable browser/session lease;
- provider conversation identity;
- durable launch-handle registry;
- generic scheduler or event bus;
- blind relaunch/resend.

## 9. Acceptance shields

Behavioral/fault-injection tests must prove:

- server-side commit followed by simulated response loss leaves the live mapping intact and status reconciliation returns the one task navigation;
- commit request failure before application leaves durable state prepared and produces no task navigation;
- controller restart after durable commit but before the original commit acknowledgement can be followed by the same surviving live MV3/preflight identity and yields exactly one navigation path;
- preflight content uses `location.replace()` only after a background response that proves `launch-attempted/prepared/open` with exact correlation/provenance;
- launcher contains only one browser `Start-Process`, for the neutral preflight URL, and never opens `launch.launch_url`;
- duplicate preflight tabs cannot both own/navigation-arm the same live launch;
- complete MV3/browser loss still destroys the launch mapping and a restored task URL fails before IndexedDB/controller effects;
- all earlier one-Send, timeout-result, ACK-loss, cleanup/capture and runtime-provenance tests remain green.

Final target-Windows acceptance must add an **ambiguous preflight-commit/restart** fault case if deterministic fault injection can be performed without changing reviewed source. Otherwise the exact fault mechanism must be covered by deterministic runtime tests and the physical B1/B2 browser-loss gates remain mandatory.

## 10. Architecture decision

**NARROW — implementation may proceed** with same-live-MV3 commit reconciliation and preflight self-navigation only.

This refines adapter-local launch ownership. It does not create the future persistent Agent Session mechanism and does not weaken complete-browser-loss fail-closed behavior.

Re-enter Stage Research again if implementation requires durable browser identity, a second task-navigation owner, a new persistence journal, provider-conversation recovery, or any retry that cannot be made semantically idempotent and reconciled from durable state.