# Agent Session Temporary-Chat bootstrap-lifetime re-entry

Status: **STAGE RESEARCH BRIEF — NARROW**

Research date: **2026-09-04**

Triggering PR: **#149**

Triggering HEAD: `27bc84c8ce672291519d0ea0b655bca2bb4440c8`

Accepted BASE: `90a8e16e6a1badecd3315968339ca691634b7ee4`

Applicable repository skill: `.agents/skills/stage-research/SKILL.md` v1.2.

This is a fresh-review-triggered re-entry for one release-critical authority gap in the already-selected ephemeral `chatgpt-temporary` profile. It does not reopen persistent conversation recovery or broaden generic Agent Session scope.

## 1. Triggering finding and falsification

Fresh ordinary-ChatGPT review of exact HEAD `27bc84c8ce672291519d0ea0b655bca2bb4440c8` reported one P1 interleaving:

```text
project launch_state becomes launch-attempted
 -> task bootstrap URL contains private run_id in fragment
 -> Chrome dies before the first IndexedDB browser claim
 -> Chromium restores the bootstrap URL after restart
 -> new MV3 service-worker lifetime sees no durable browser claim
 -> restored page is parsed as a fresh initial context
 -> new service worker creates the first claim and can request Send authority
```

Development-side falsification confirms the mechanism. The existing `LIVE_PRE_SEND_CLAIMS` fence protects only an already-created browser claim. It does not protect the interval before the first claim exists, and the task URL itself currently carries enough private correlation to enter the fresh-claim branch again.

Disposition of the review finding: **CONFIRMED**.

## 2. Current platform evidence

Two current Chromium/Chrome properties are directly relevant.

1. Chromium session history persists navigation entries, including URL state, so tabs can be restored between Chromium restarts. Source researched 2026-09-04: `https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/session_history.md`.
2. Chrome MV3 extension service-worker global variables are explicitly ephemeral and are lost when the worker terminates; Chrome recommends treating unexpected termination as normal lifecycle behavior. Source researched 2026-09-04: `https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle`.

Therefore a URL-carried private launch capability is not a valid browser-lifetime fence, while an in-memory MV3 witness is suitable only when the project arranges authority ordering so that the witness exists **before** durable launch-attempt authority is committed.

## 3. Exact stage question

> What is the smallest adapter-local mechanism that prevents a restored Temporary bootstrap URL from reconstructing first-Send authority after complete browser/service-worker lifetime loss, including the interval before the first durable browser claim?

Required invariants:

- generic Delegation identity/state stays unchanged;
- one launch attempt remains durably committed before the task-bearing worker URL is physically opened;
- private `run_id` is not persisted in task/browser session history;
- first browser claim remains an extension-origin IndexedDB unique-key transaction;
- complete MV3/browser lifetime loss before first claim cannot recreate private controller authority;
- controller restart while the original extension lifetime remains alive may still continue the same prepared delivery;
- no second child launch, no second Send, no provider-conversation recovery, no new public tool;
- unresolved failure remains fail-closed/open.

## 4. Architecture lineage

### Bounded Agent Session / Delegation lifecycle — `KEEP`

No generic state field, generic scheduler, provider identity or persistent-session contract is added.

### First-provider browser delivery ownership — `REFINE`

Keep IndexedDB unique delivery claim and `LIVE_PRE_SEND_CLAIMS`, but add a strictly adapter-local **preflight handoff** so the private run capability is installed only in the currently live MV3 service worker before the project commits the task launch.

### `chatgpt-temporary` provider adapter — `REFINE`

Replace direct task-URL bootstrap with:

```text
prepared delegation
 -> neutral ChatGPT preflight URL carrying only one bounded preflight nonce
 -> existing content-script no-task path emits its ordinary resume-intent probe
 -> current MV3 service worker recognizes the sender as the neutral preflight page
 -> service worker receives private run/correlation handoff in memory
 -> service worker acknowledges the handoff
 -> controller durably commits launch-attempted
 -> controller emits task-bearing Temporary URL with one opaque launch handle only
 -> content page presents that opaque handle in the existing fragment envelope
 -> same live service worker resolves handle -> private run_id
 -> browser claim -> project Send authority
```

The task URL no longer contains the private `run_id`. To avoid a needless content/policy protocol rewrite, the existing fragment key name `cap_run_id` is retained as a compatibility envelope, but its value is now the random **launch handle**, not the durable run capability. This naming compatibility has no authority semantics: every task message is resolved through the current service-worker `LIVE_LAUNCHES` map before browser claim/controller access, and the real `run_id` is injected only inside the background worker.

### Persistent/recoverable browser identity — `DEFER`

No durable browser lease/session generation is introduced. The handoff is intentionally lost on MV3/browser lifetime loss. Persistent existing-session identity remains future Prime/existing-session research.

## 5. Architecture primitive and adjacent domain

New narrow primitive: **ephemeral preflight capability handoff with commit ordering**.

Engineering domains:

- capability security: the private controller capability is handed to one live trusted extension context and is not reconstructible from browser history;
- write-ahead/commit ordering: the live witness is installed before durable `launch-attempted` and before the task URL is exposed;
- crash consistency: every crash boundary either leaves the delegation `prepared` with no task-bearing launch committed, or `launch-attempted` with a task handle that a new service-worker lifetime cannot resolve.

No durable lease, queue, journal, browser-session registry or new generic persistence owner is added.

## 6. Alternatives

### A — strip `run_id` from the task URL at `document_start`

Rejected. It reduces exposure time but leaves an unavoidable crash interval between navigation/session-history creation and content-script cleanup. Chromium persists navigation URLs for restart restoration, so cleanup-after-navigation cannot prove the required pre-claim failure boundary.

### B — infer browser restoration from navigation type, tab id, history length or other page heuristics

Rejected. Those signals are provider/browser implementation observations, not a stable project authority boundary, and tab/session restoration can recreate page state with new runtime objects. The existing tab-ID ABA history already shows why numeric browser identity is insufficient.

### C — disable Chrome session restoration or require special user/browser settings

Rejected. This would make a security guarantee depend on mutable user/browser configuration outside CAP authority and would not cover MV3 service-worker termination while Chrome remains open.

### D — preflight handoff before durable task launch

Selected. The private run capability exists in the durable local Control Plane and in one live extension service-worker map only. The task URL contains only an opaque launch handle. A new service-worker lifetime has no map entry and cannot derive the private run capability from IndexedDB or URL state.

Decision: **SELECTED / NARROW**.

## 7. Crash matrix

| Boundary | Durable delegation | Browser/extension state | Required result |
|---|---|---|---|
| Before preflight | prepared/open | no trusted live handoff | safe to retry neutral preflight; no worker task URL or Send authority exists |
| Preflight request before live map install | prepared/open | no live launch capability | no task launch; retry preflight is safe |
| Live map installed before commit | prepared/open | current MV3 lifetime has private handoff | commit may proceed; if lifetime dies first, no task launch is committed |
| Commit `launch-attempted` after live map install | launch-attempted/prepared | current MV3 lifetime has launch handle -> private run mapping | launcher may open exactly one task URL |
| Chrome/MV3 dies after commit but before first browser claim | launch-attempted/prepared | live map lost; task URL may be restored with opaque handle | restored page cannot resolve run_id, cannot create first claim, cannot request Send |
| First browser claim committed | launch-attempted or child-bound / prepared | durable claim + live claim witness | existing one-Send rules apply |
| MV3/browser dies after claim | prepared/claimed/unknown/delivered as applicable | all live maps/witnesses lost | no Send/monitor/capture authority reconstructed |
| Controller restarts while original MV3 lifetime lives | durable state unchanged | live launch map remains in extension | same run may reconnect; no new physical launch |
| Result recorded | delivered/recorded | browser irrelevant | terminal readback only |

## 8. Minimum implementation

1. add an adapter-local neutral preflight phase before `launch-attempted` is committed for a new delegation;
2. create a one-time preflight nonce in controller memory/output only for a `prepared/open` first launch;
3. let the exact runtime-attested MV3 service worker exchange that nonce for the private run/correlation data and store it only in an in-memory launch-handle map;
4. require the service worker to acknowledge/store that map entry before the controller commits `launch-attempted` and writes the task `launch.json`;
5. ensure the task URL contains only a bounded opaque launch handle, never the private `run_id`; retaining `cap_run_id` as the legacy fragment **key name** is acceptable only when its value is the launch handle and tests prove the private capability differs and is absent from the URL/projection;
6. do not persist `run_id` in the browser IndexedDB delivery claim;
7. resolve every task message through the live launch-handle map before browser claim/controller access, replacing the compatibility-envelope value with the real private `run_id` only inside the service worker;
8. preserve existing IndexedDB unique-claim, `LIVE_PRE_SEND_CLAIMS`, exact source attestation, delivery reconciliation and result-capture behavior;
9. do not add extension permissions, a durable browser lease, a provider-conversation recovery path, a public tool or a generic Delegation state field.

## 9. Acceptance shields

Focused tests must prove:

- task URLs contain no private `run_id` and do contain one opaque launch handle distinct from the private capability;
- no task-bearing launch URL exists before successful preflight handoff/commit;
- a task message cannot reach `claimBrowserSend` when its launch handle is absent from the current service-worker map;
- clearing/restarting the background lifetime before first claim makes the restored task handle unusable even when no IndexedDB claim exists;
- IndexedDB claim records contain no `run_id` from which a new lifetime could reconstruct controller authority;
- duplicate tabs in the same live lifetime still produce at most one browser claim/Send;
- existing-claim/tab-ABA/background-restart fences remain fail closed;
- controller restart with the original live extension context can still continue the same prepared delivery without a second launch;
- normal uninterrupted physical run still produces one Send and one exact worker result;
- final target-Windows browser-loss test includes the previously uncovered **pre-first-claim** interval as well as the already-covered post-claim loss boundary.

## 10. Decision

**NARROW**.

Implement only the adapter-local preflight handoff above. This is a correction to the first-provider launch authority ordering, not a persistent browser/session identity system. Any implementation change moves HEAD, invalidates the review on `27bc84c8...`, and requires a new exact-head fresh semantic review before physical acceptance.
