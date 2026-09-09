# Agent Session Pre-Send Restart Fence

Status: **STAGE RESEARCH FOLLOW-UP — NARROW**

Research date: **2026-09-04**

Triggering reviewed HEAD: `0eeac6a755764e7151942382c72c8db20b003bcc`

Accepted BASE: `90a8e16e6a1badecd3315968339ca691634b7ee4`

Applicable authority:

- `.agents/skills/stage-research/SKILL.md` v1.2
- `.agents/skills/code-review/SKILL.md` v1.1
- `project-context/AGENT_SESSION_BROWSER_RECOVERY_HARDENING.md`

## 1. Trigger

The fresh ordinary-ChatGPT review of exact HEAD `0eeac6a755764e7151942382c72c8db20b003bcc` found one P1 in the pre-conversation-binding Send-owner fence.

The existing durable IndexedDB claim stored only `claim_tab_id`. The prior fix correctly rejected a simultaneously losing tab with a different live numeric ID, but it treated equality with the persisted number as sufficient proof that an existing `prepared` claim still belonged to the same owner. Chrome tab IDs are only browser-session scoped. After complete Chrome restart a restored duplicate may therefore receive the old owner's numeric ID while retaining the same launch-shaped URL/private fragment.

Development-side falsification confirms the finding. Exact HEAD/prompt/runtime correlation and controller state do not distinguish that ABA case because the failure occurs before provider `conversation_id` binding while durable delivery remains `prepared`.

## 2. Decision

**NARROW — fail closed across any MV3 service-worker lifetime break before local Send authority is committed.**

Do not add a new durable browser-session lease, permission, scheduler, provider field or generic delegation state for this first adapter.

The durable IndexedDB claim continues to own the one-Send exclusion. A separate in-memory `LIVE_PRE_SEND_CLAIMS` set is populated only when this exact service-worker lifetime successfully commits the new IndexedDB claim. The existing-claim/`prepared` recovery branch may request project-local Send authority only when both are true:

1. the delivery ID is present in `LIVE_PRE_SEND_CLAIMS`; and
2. the persisted `claim_tab_id` equals the current sender tab ID.

A service-worker restart clears the in-memory set by construction. Therefore complete Chrome restart, service-worker eviction, or any other background-lifetime break revokes pre-Send recovery authority even though the durable IndexedDB claim remains. A later page can never recreate that ephemeral proof merely from the launch URL, private `run_id`, visible correlation, or a reused numeric tab ID.

This is intentionally stricter than browser-session-scoped recovery: a same-browser service-worker restart can lose liveness before provider conversation binding. That bounded loss is accepted because no physical Send has been authorized by this recovery path, while the durable browser claim continues to prevent an unsafe alternate Send. CAP prefers fail-closed bounded loss over adding a second durable ownership/lease mechanism at the current one-worker scope.

## 3. Why the ephemeral state is safe

MV3 service-worker globals are not treated as durable truth. Here their loss is the security action: losing `LIVE_PRE_SEND_CLAIMS` removes authority rather than granting or reconstructing it.

The durable facts remain in IndexedDB and the project Control Plane. The in-memory set is only a narrowing witness that the current worker lifetime itself observed the successful `store.add()` commit. It cannot be recovered from durable state after restart.

Provider-conversation recovery remains unchanged. Once a stable `conversation_id` has been monotonically bound after the physical Send, restart recovery is monitor-only and continues to require exact provider conversation identity, visible correlation, live controller state and current execution/runtime provenance.

## 4. Failure matrix delta

| Boundary | Durable claim | Live pre-Send witness | Rule | Additional Send authority |
|---|---|---|---|---|
| Initial `store.add()` commits in current worker | exact claim | present | exact owner tab may continue/recover local authority | at most original one-Send path |
| Concurrent duplicate loses claim | exact claim | present for winner delivery | different tab ID rejected | none |
| MV3 service worker restarts before local authority | exact unbound claim | absent | fail closed even if numeric tab ID matches | none |
| Complete Chrome restart before conversation binding | exact unbound claim | absent | fail closed even under tab-ID ABA/reallocation | none |
| Provider conversation already bound | exact bound claim | irrelevant | existing conversation-bound monitor recovery only | none |

## 5. Acceptance shields

Focused deterministic tests must prove:

- a simultaneously losing tab with a different ID still cannot obtain local Send authority;
- the exact owner can use the existing-claim/`prepared` path only while the current service-worker lifetime retains the live claim witness;
- a fresh service-worker context with the same durable claim and the same reused numeric owner tab ID receives `send_authorized=false` and never calls project-local Send authority;
- the prior delivered-ack-loss and capture-ack-loss regressions remain green;
- execution-generation changes with the modified `background.js` bytes;
- no extension permission or public tool is added.

Final physical qualification after a fresh semantic PASS must include the complete Chrome close/reopen pre-conversation negative case and prove zero additional Send authority before proceeding to the already-required conversation-bound restart recovery case.

## 6. Scope

No change to generic `DelegationIdentity`, durable Control Plane state, provider `conversation_id` semantics, cleanup/capture authority, six-tool public surface, scheduler policy, worker fan-out, mutating workers, rich-context workers or Prime integration.

Any commit implementing this follow-up makes the `0eeac6a...` review stale. The next semantic gate must review the final exact HEAD after hosted checks are green.
