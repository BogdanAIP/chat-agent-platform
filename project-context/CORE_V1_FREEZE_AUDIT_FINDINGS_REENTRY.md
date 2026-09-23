# Core v1 Freeze Audit Findings Re-entry

Status: **STAGE RESEARCH — NARROW**

Research date: 2026-09-23.

## Trigger

A fresh aggregate Core-v1 freeze audit reproduced two remaining consequence-bearing
authority defects on exact HEAD
`e4f09644c8f1b85017c4a49e3073e12877cd236d`:

1. after an attempted semantic Browser mutation ends without a verified PASS,
   the same activation can issue another mutation and receive a fresh exact grant,
   because direct Browser authorization is stateless across public tool calls;
2. `verified_workspace_artifact_v1` can delete verified-owned files in its
   failure rollback/finally path without running the deletion through the Core
   authorization/attempt path.

The audit also checked the Windows five-transition loop and did not reproduce a
third defect: delivery ambiguity stops later transitions there, while repeat is
allowed only after a failure proven before input.

## Exact stage question

What is the smallest correction that makes the freeze invariant true:

```text
UNKNOWN / unverified delivery cannot authorize later physical mutation
and
every new physical workspace mutation consumes exact Core authority
```

without adding a new policy engine, durable ordinary-chat session service,
provider framework, retry scheduler or public tool?

## Finding A — semantic Browser ambiguity

### Current behavior

The direct semantic Browser path is:

```text
fresh snapshot
 -> exact request-derived CapabilityGrant
 -> one provider mutation
 -> fresh verification
 -> PASS | FAIL | UNKNOWN
```

The original direct-mutation research assumed that a later identical call was safe
because preflight would observe an already-satisfied expected state and suppress
redelivery.

That assumption is incomplete. If delivery occurred but the final state remains
UNKNOWN or otherwise unverified and does not yet satisfy the declared expected
state, a later public call derives a fresh grant from the new `before` snapshot and
can physically deliver again.

### Selected correction

Use the existing process-lifetime `SemanticActivationContext` boundary as a
**one-way fail-closed mutation quarantine**, not as a retry/reconciliation engine.

Rules:

- once any Browser mutation has a proven delivery attempt and does not finish with
  a verified PASS, mark that semantic activation mutation-quarantined;
- all later mutating Browser operations in that activation (`web_open` and
  `web_interact`) fail closed before authorization/provider delivery;
- read-only `web_observe` remains available so the user/operator can inspect state;
- there is no in-activation automatic recovery, retry or "clear quarantine" API;
- a new semantic profile process creates a new activation identity as before;
- public tool schemas remain unchanged.

This is deliberately narrower than introducing WorkingState persistence for the
ordinary direct Browser route. It does not decide that a prior effect was applied
or not applied. It merely prevents CAP from issuing more physical Browser effects
while the current activation contains unresolved delivery evidence.

If later product requirements require in-session reconciliation and continuation
after Browser ambiguity, Stage Research must re-enter and promote this route to a
stateful Core-owned continuation contract.

### Why not add a durable retry ledger now

A durable per-chat logical task identity still does not exist on this route.
Inventing one here would create the exact new subsystem the Core freeze is trying
to avoid. The fail-closed activation quarantine closes the current safety defect
without minting retry authority.

## Finding B — workspace rollback deletion bypass

### Current behavior

The normal transition path uses exact grants for:

```text
stage_create
final_create
staging_cleanup
```

but the failure `finally` block may directly invoke
`_delete_verified_owned_file()` for staging/target compensation.

The file identity/digest checks make that deletion narrowly scoped, but ownership
proof is not authorization. It is still a new physical mutation.

### Selected correction

Do **not** add hidden rollback mutation actions.

For Core-v1 freeze, remove automatic physical compensation from the failure
`finally` path. The procedure must:

- leave any verified-owned residual staging/target object in place;
- record/checkpoint the rollback state as not removed;
- preserve WorkingState/history/evidence;
- require an explicit future reviewed recovery/cleanup operation if product
  requirements later need automatic compensation.

Rationale:

- automatic rollback is not required for truthful task success;
- adding `rollback_staging_delete` / `rollback_target_delete` would expand the
  consequence contract and recovery state solely to preserve cleanup convenience;
- residual artifacts are safer than an unauthorized delete;
- UNKNOWN already intentionally leaves artifacts in place.

The existing authorized `staging_cleanup` transition on the successful path is
unchanged.

## Failure shields

Implementation must prove:

1. an attempted Browser mutation with UNKNOWN cannot be followed by a second
   `web_interact` provider call in the same activation;
2. the quarantine also blocks `web_open` mutation after unresolved Browser
   delivery;
3. `web_observe` remains usable after quarantine;
4. a Browser mutation that verifies PASS does not quarantine the activation;
5. provider delivery failure plus unavailable/UNKNOWN verification quarantines;
6. public six-tool schemas are unchanged;
7. workspace failure/finally contains no physical delete/link/write compensation;
8. successful authorized `staging_cleanup` remains unchanged;
9. failure checkpoints truthfully report residual files instead of claiming them
   removed;
10. no new registry, scheduler, retry authority or provider framework is created.

## Acceptance

L1:
- deterministic injected Browser executor reproduction of UNKNOWN then repeat;
- assert one physical mutation only and second mutation fails before authorization/
  provider delivery;
- assert read-only Browser observation remains possible after quarantine;
- workspace forced-error tests asserting no rollback delete is called.

L2:
- semantic Browser verification/reconciliation suites;
- workspace crash/reconciliation suites;
- six-tool Semantic Projection acceptance;
- Core freeze-surface tests;
- full hosted CI/security.

The existing physical Windows acceptance is unaffected by these corrections.

## Decision

**NARROW**

Implement only:

- one-way semantic-activation Browser mutation quarantine after attempted
  non-PASS/unverified delivery;
- removal of failure-path workspace physical rollback deletes.

Do not add WorkingState persistence to ordinary Browser calls, a durable browser
retry ledger, new rollback actions, a policy engine, registry, public tool, or
Rust Native Host.
