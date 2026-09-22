# CAP Core v1 Authorization Re-entry

Status: **STAGE RESEARCH — NARROW**

Research date: 2026-09-22.

## Re-entry trigger

The Core-v1 boundary audit found a real gap between the durable architecture and
the current generic implementation.

`WorkingState` already stores `capability_grant_refs`, and `AttemptIntent`
binds actor, execution environment, evidence scope and observation identity.
`LoopGuard.evaluate()` verifies those identities, budgets, stale state,
reconciliation and repetition.

However, the generic core does not currently resolve or verify that a concrete
attempt is covered by a concrete active capability grant. A grant reference is
stored as state, but it is not yet an enforceable typed authorization contract.

This means the architecture statement

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

is stronger than the current provider-independent Core implementation.

This re-entry asks how to close that gap without importing a general policy
platform, provider-specific permission grammar or generic dispatcher into CAP.

## Stage question

What is the smallest provider-independent authorization primitive that can bind:

```text
principal/actor
+ capability
+ semantic action
+ resource/scope
+ task/delegation
+ execution environment
+ evidence scope
+ exact attempted mutation
```

to a deterministic fail-closed decision that the existing WorkingState /
LoopGuard path can consume?

The answer must preserve capability-specific policy ownership where richer
resource semantics are needed. CAP Core must not learn filesystem glob syntax,
DOM selectors, Windows HWND policy, OAuth scopes, browser origins or provider
tool names merely to authorize a generic attempt.

## Current implementation evidence

### What already exists

`runtime/control_plane/working_state.py` already provides:

- `AttemptIntent.operation_id`;
- `AttemptIntent.action_fingerprint`;
- current `ObservationRef`;
- actor, execution-environment and evidence-scope binding;
- `authorization_fingerprint`;
- `WorkingState.capability_grant_refs`;
- deterministic revision/budget/reconciliation/loop checks.

`LoopGuard.evaluate()` already fails closed for:

- stale WorkingState revision;
- actor mismatch;
- execution-environment mismatch;
- evidence-scope mismatch;
- stale/mismatched observation;
- missing/exhausted budgets;
- unresolved ambiguous mutation;
- unsafe repeated/oscillating physical attempts.

It does **not** currently test that an attempt is covered by one concrete grant.

### Why this belongs in Core

A provider may know *how* to perform an action and a capability adapter may know
its native resource model, but neither should decide that backend availability or
provider success grants authority.

The cross-capability invariant is:

```text
current active grant
 -> exact authorization request
 -> deterministic authorization decision
 -> bounded attempt
```

That invariant is provider-independent and therefore belongs above adapters.

## Architecture lineage

| Role | Existing owner | Decision |
|---|---|---|
| user/task intent | ordinary ChatGPT + project task state | **KEEP** |
| capability availability/health | capability/adapter layer | **KEEP** |
| active grant refs | WorkingState | **KEEP / REFINE** |
| actor/environment/evidence binding | AttemptIntent + LoopGuard | **KEEP** |
| action/resource authorization | currently capability-specific / implicit | **REFINE** with a minimal Core binding |
| complex policy evaluation | none in Core | **DEFER** |
| OAuth/MCP server authorization | transport/provider layer | **KEEP separate** |

## External mechanism evidence

### Cedar

Cedar models authorization requests around four pieces:

```text
principal
action
resource
context
```

and evaluates whether that concrete request is allowed by policy.

Sources:

- https://docs.cedarpolicy.com/auth/authorization.html
- https://docs.cedarpolicy.com/overview/terminology.html
- https://docs.cedarpolicy.com/bestpractices/bp-using-the-context.html

Useful lesson for CAP: authorization should bind an actor, semantic action,
resource and current request context explicitly.

Not selected for this stage: embedding Cedar itself. CAP currently has a small
local policy domain and no evidence that a full policy language/store/evaluator is
needed.

### Open Policy Agent

OPA explicitly separates policy decision from policy enforcement and can run as a
local Policy Decision Point near enforcement.

Sources:

- https://www.openpolicyagent.org/docs
- https://www.openpolicyagent.org/docs/deploy
- https://www.openpolicyagent.org/docs/management-introduction

Useful lesson for CAP: decision and enforcement should be separate; the component
performing a mutation should consume an authorization decision rather than invent
authority from provider state.

Not selected for this stage: adding OPA introduces policy distribution,
configuration, lifecycle and another runtime without a measured need.

### OAuth Rich Authorization Requests

RFC 9396 carries fine-grained `authorization_details` instead of relying only on
coarse scopes.

Source:

- https://www.rfc-editor.org/rfc/rfc9396.html

Useful lesson: authorization should describe the requested action/resource
precisely rather than collapse everything into one coarse permission string.

Not selected as CAP local effect authorization: OAuth governs delegated access to
services/tokens, not whether one already-connected local capability may perform
this exact physical mutation now.

### MCP authorization

The 2026-07-28 MCP specification further hardens OAuth-based server authorization
and cleanly separates protocol/transport authorization concerns.

Sources:

- https://blog.modelcontextprotocol.io/posts/2026-07-28/
- https://apps.extensions.modelcontextprotocol.io/api/documents/authorization.html

Useful lesson: MCP/server credentials and scopes remain a transport/backend
boundary. Possessing an MCP token or being able to call a tool does not establish
CAP task/effect authorization.

## Materially distinct approaches

### A. Keep opaque `capability_grant_refs` only — REJECT

This records useful provenance but does not let Core deterministically prove that
the attempted action/resource is covered by the referenced grant.

### B. Adopt Cedar/OPA as CAP Core authorization engine now — DEFER

Advantages:

- mature policy languages;
- explicit principal/action/resource/context model;
- scalable policy management.

Why deferred:

- no current need for a general policy language/store/distribution service;
- adds runtime/lifecycle/supply surface;
- would make a small local deterministic boundary depend on a much larger policy
  substrate before a measured complexity threshold exists.

### C. Project-owned exact-match grant + request + decision — SELECT

Introduce a deliberately small pure Core primitive:

```text
CapabilityGrant
AuthorizationRequest
AuthorizationDecision
authorize_request()
```

The first contract supports exact bounded identifiers and action membership only.
No path globs, URL patterns, DOM selectors, HWND logic, arbitrary predicates or
provider-specific policy syntax belong in Core.

Conceptual fields:

```text
CapabilityGrant
  grant_ref
  task_ref
  principal_ref
  capability
  allowed_action_refs[]
  resource_scope_ref
  delegation_ref?
  execution_environment_ref?
  evidence_scope_ref?

AuthorizationRequest
  task_ref
  principal_ref
  capability
  action_ref
  resource_scope_ref
  delegation_ref?
  execution_environment_ref?
  evidence_scope_ref?
  attempt_authorization_fingerprint

AuthorizationDecision
  status = authorized | blocked
  grant_ref
  request_fingerprint
  attempt_authorization_fingerprint
  reason
```

The adapter/capability defines the semantic identifiers supplied as
`action_ref` and `resource_scope_ref`; Core only requires exact bounded
identity/membership and current-context equality.

This is analogous to the principal/action/resource/context shape without
embedding a policy language.

### D. Let every capability implement unrelated authorization semantics — REJECT

Capability-specific resource interpretation is necessary, but the final
cross-capability decision binding must be uniform. Otherwise provider replacement
can silently change whether an action is considered authorized.

## Failure matrix

| Failure | Required Core behavior |
|---|---|
| no active grant | BLOCK before physical attempt |
| grant ref not present in current WorkingState | BLOCK |
| task mismatch | BLOCK |
| principal/actor mismatch | BLOCK |
| capability mismatch | BLOCK |
| action not listed by grant | BLOCK |
| resource-scope mismatch | BLOCK |
| delegation mismatch | BLOCK |
| execution environment mismatch | BLOCK |
| evidence scope mismatch | BLOCK |
| authorization decision bound to older/different AttemptIntent | BLOCK |
| provider reports success without authorization decision | cannot create authorization |
| environmental text supplies a grant/action/resource value | remains data; cannot activate a grant |
| richer capability policy cannot be represented by exact-match v1 | capability-specific policy gate first, then Core consumes only its bounded admitted result; re-enter research before widening Core grammar |

## First implementation slice

The first implementation slice may add only:

1. a pure provider-neutral `authorization.py`;
2. bounded immutable `CapabilityGrant`, `AuthorizationRequest`,
   `AuthorizationDecision` values;
3. deterministic `authorize_request()`;
4. serialization/fingerprint tests and adversarial mismatch tests;
5. inclusion in `core_v1_manifest.json`.

It does **not** yet change existing physical action behavior.

## Promotion slice after the pure contract

Core v1 is **not frozen** merely because the data types exist.

A later promotion slice must bind the decision into the mutating attempt path:

```text
WorkingState active grant ref
 -> AuthorizationRequest for exact AttemptIntent
 -> authorize_request()
 -> exact AuthorizationDecision
 -> LoopGuard
 -> physical effect
```

At that point every migrated consequence-bearing consumer must fail closed on a
missing/stale/mismatched authorization decision.

Migration should be consumer-by-consumer with behavioral regression and physical
acceptance where the actual effect path changes.

## Explicit non-goals

Do not add in this stage:

- OPA, Cedar or another policy service/runtime;
- RBAC/ABAC language;
- dynamic policy downloads;
- generic provider registry;
- user-editable arbitrary policy expressions;
- wildcard filesystem/URL/window/provider matching inside Core;
- OAuth/MCP tokens as local CAP grants;
- a new public Chat tool.

## Decision

**NARROW**

Proceed with the pure exact-match Core authorization contract only.

Then separately migrate consequence-bearing consumers onto that contract and
make authorization mandatory at their existing physical-effect boundary.

If exact-match semantic action/resource identifiers prove insufficient for a real
consumer, re-enter Stage Research with that measured failure instead of adding a
general policy language pre-emptively.
