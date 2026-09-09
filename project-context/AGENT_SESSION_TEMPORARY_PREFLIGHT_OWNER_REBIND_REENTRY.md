# Agent Session Temporary-Chat same-live preflight owner rebind re-entry

Status: **STAGE RESEARCH BRIEF — NARROW**

Research date: **2026-09-04**

Triggering PR: **#149**

Accepted BASE: `90a8e16e6a1badecd3315968339ca691634b7ee4`

Applicable repository skill: `.agents/skills/stage-research/SKILL.md` v1.2.

This brief supersedes only the deterministic-HMAC-handle subproposal in `AGENT_SESSION_TEMPORARY_PREFLIGHT_COMMIT_REENTRY.md`. The two review findings remain confirmed. Further implementation analysis found that a stable cross-controller handle is not required if the live MV3 worker remains the sole browser-navigation owner and later neutral preflights can rebind that same live owner to the restarted controller before any new commit occurs.

## 1. Exact problem retained

Two release-critical windows must still close:

1. `/preflight-commit` may succeed durably while its HTTP acknowledgement is lost; deleting the only live `launch_handle -> run_id` mapping would strand the launch.
2. the controller may crash after durable `launch-attempted` but before the commit response/projection completes; if the original MV3/preflight context survives, it must still be able to continue the already-selected one-launch path.

Complete MV3/browser lifetime loss remains intentionally fail-closed.

## 2. Why the HMAC handle proposal is unnecessary

A deterministic HMAC-derived public handle would let a restarted controller reproduce commit correlation, but it adds a cryptographic derivation primitive to solve a narrower ownership problem.

The controller does not authorize task actions by `launch_handle`. The actual controller capability remains private `run_id`; generic durable state plus exact delegation/delivery/head/prompt/generation establishes the committed logical launch. The browser-side requirement is only to ensure that **one surviving live MV3/preflight owner** is allowed to turn that durable commit into one task navigation.

The live worker already has enough information to do that:

```text
owner_tab_id
private run_id
current launch_handle + task URL
exact delegation/delivery/task/head/prompt correlation
current controller preflight capability when prepared
```

Therefore stable handle identity across controller process lifetimes is not necessary. What is necessary is that a restarted controller's new prepared handoff cannot create a second live navigation owner while the old owner survives.

Decision on prior HMAC subproposal: **REJECT / NOT ADOPTED** for #149 as unnecessary mechanism depth.

## 3. Selected primitive — same-live owner-preserving rebind

Domain: ephemeral ownership + idempotent retry/reconciliation.

The MV3 worker keeps one live launch owner for one delegation/delivery. The map may be keyed by the current opaque handle for task-message resolution, but ownership lookup is additionally by exact delegation/delivery and `owner_tab_id`.

After controller restart while durable state is still `prepared/open`:

```text
new neutral preflight tab
 -> new controller /preflight returns same run/delegation/delivery/task/head/prompt
    but possibly a new opaque handle/task URL
 -> MV3 finds an existing live owner for that exact delegation
 -> validates the private run and all exact correlation fields
 -> rekeys/refreshes that SAME live record to the new handle/preflight capability/task URL
 -> preserves original owner_tab_id
 -> new neutral tab receives no navigation authority
 -> original owner tab's next retry uses the refreshed record
 -> commit/reconcile
 -> only original owner tab may receive task navigation
```

If the controller restart happened **after** durable `launch-attempted`, it exposes no new neutral preflight. The surviving old owner keeps its old handle/task URL and reconciles the token-authenticated `/status` directly. Because no new prepared preflight can commit in that state, exact durable launch/delegation/delivery/head/prompt/generation is sufficient proof for that surviving owner.

## 4. Architecture lineage

### Generic Delegation — `KEEP`

No generic state field changes.

### Temporary browser launch ownership — `REFINE`

Use one live owner per exact delegation/delivery in the current MV3 lifetime. Handle changes caused by a controller restart before commit may refresh the record, but never transfer `owner_tab_id`.

### Deterministic HMAC launch handle — `REJECT`

Not required once owner-preserving rebind prevents prepared-state ABA. Avoid adding cryptographic protocol surface that is not needed by the selected first profile.

### Persistent browser/session identity — `DEFER`

No durable owner registry, provider conversation identity or restart lease.

## 5. Evidence

Problem evidence remains the reviewed implementation and crash ordering: durable commit can precede HTTP acknowledgement, and controller restart can occur while MV3 state survives.

Solution evidence remains standard idempotency/reconciliation guidance:

- RFC 9110 §9.2.2: communication failure does not prove an operation failed; retry is safe only with idempotent semantics or application knowledge of the original request: https://www.rfc-editor.org/rfc/rfc9110.html#name-idempotent-methods
- AWS Builders' Library: caller/request identity plus semantically equivalent replay/reconciliation is the basis for safe retry after ambiguous responses: https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/
- Chrome MV3 lifecycle: service-worker globals are ephemeral and may disappear unexpectedly, so current-memory ownership is valid only as an intentionally fail-closed same-lifetime scope: https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle
- `location.replace()` supports using the existing neutral preflight tab as the one task-navigation owner rather than creating another browser tab: https://developer.mozilla.org/en-US/docs/Web/API/Location/replace

## 6. Failure matrix

| Boundary | Durable state | Same MV3 owner | Rule |
|---|---|---|---|
| preflight prepared, no commit | prepared/open | original owner exists | retry same commit |
| commit applied, ACK lost | launch-attempted/prepared/open | original owner exists | retain record; reconcile authenticated status; navigate once |
| controller crash after commit | launch-attempted/prepared/open | original owner exists | restarted controller status proves committed state; old owner navigates old task URL |
| controller crash before commit | prepared/open | original owner exists | new neutral preflight may refresh controller capability/handle/task URL into old record; ownership stays old tab |
| second neutral preflight during same lifetime | prepared/open | original owner exists | may refresh matching record; second tab never receives navigation authority |
| original owner tab is gone but MV3 survives | prepared/open | owner cannot act | fail closed; do not transfer ownership |
| MV3/browser lifetime lost after commit | launch-attempted/open | no owner record | fail closed; no task/Send authority reconstruction |
| task navigation occurred, MV3 lost before first claim | launch-attempted/open | map lost | restored task handle cannot resolve; no claim/controller access |
| first IndexedDB claim exists | existing one-Send state | as previously specified | no second Send/recovery authority |

## 7. Minimum implementation

Must have now:

1. `/preflight` returns the exact task URL privately to MV3 before commit; it is not independently opened by PowerShell.
2. The live record stores `owner_tab_id`, private `run_id`, current handle/task URL, preflight capability and exact correlation.
3. Commit transport exceptions never delete the live record.
4. The owner reconciles ambiguous commit through private-token `/status` and exact delegation/delivery/head/prompt/generation.
5. A new prepared preflight in the same MV3 lifetime searches for an existing live record by delegation/delivery, not only by handle.
6. If exact private/correlation values match, it may replace the record's current handle/task URL/preflight capability while preserving `owner_tab_id`.
7. A non-owner neutral tab never receives `navigate_url`.
8. The owner preflight content retries and calls `location.replace(task_url)` only after commit proof.
9. PowerShell opens only neutral preflight and never the task URL.
10. Status need not expose or persist a cross-controller launch handle; exact durable launch state plus private-token correlation is sufficient only because prepared-state rebinding prevents a competing live commit owner.

## 8. Acceptance shields

Behavioral/fault-injection tests must prove:

- commit applied + response lost retains the live mapping and returns navigation after exact status reconciliation;
- controller crash after durable commit can be reconciled by the surviving old owner without `launch.json` becoming browser authority;
- controller restart before commit followed by a new neutral preflight refreshes the old owner record rather than creating a second navigation owner;
- second preflight tab cannot receive `navigate_url`;
- old handle is removed when a prepared-state rebind installs the new handle;
- original owner loss does not transfer ownership;
- content calls `location.replace()` only for `preflight-navigation-ready` with a task URL that passes `policy.parseIntent` and response correlation;
- PowerShell contains exactly one browser launch for the neutral preflight and no task `Start-Process`;
- complete MV3/browser loss remains fail closed before first claim and after claim;
- all previous one-Send, timeout-result, delivery/capture ambiguity and provenance tests remain green.

## 9. Decision

**NARROW — implementation may proceed** with same-live owner-preserving rebind, ambiguous-commit reconciliation and preflight self-navigation.

This is narrower than the superseded HMAC-handle subproposal and preserves the intended future boundary: persistent cross-browser/session identity remains Prime/existing-session research, not Temporary adapter authority.