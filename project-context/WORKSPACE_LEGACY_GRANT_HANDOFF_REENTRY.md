# Workspace Legacy Grant Handoff Re-entry

Status: **STAGE RESEARCH — NARROW**

Research date: 2026-09-23.

## Trigger

The final CAP Core-v1 freeze audit found one remaining consequence-bearing legacy path.

Schema-2 checkpoints for `verified_workspace_artifact_v1` retain the historical shared
`stage26-3a-qualification` admission in `WorkingState.capability_grant_refs`.
The previous grant-binding re-entry deliberately allowed those checkpoints to continue
through the legacy structural `LoopGuard.evaluate() / WorkingState.record_attempt()`
path for compatibility.

That preserves old recovery behavior, but it also means a resumed schema-2 checkpoint at
`staged_verified` or `final_verified` can still perform a **new** filesystem mutation
without the Core-v1 exact grant contract. That is incompatible with the proposed Core-v1
freeze boundary.

## Exact question

How can a truthful historical schema-2 checkpoint continue safely without:

- retroactively pretending an earlier physical action had the new grant;
- discarding already recorded WorkingState attempts/reconciliation;
- blind replay;
- adding a grant database or policy engine;
- keeping any future consequence-bearing mutation on `record_attempt()`?

## Evidence

### Repository evidence

The current schema-2 contract accepts only the shared qualification admission. The
resume path restores that WorkingState and, after fresh state verification, can proceed
to `final_create` or `staging_cleanup`. Current helper dispatch then selects legacy
`evaluate()` and `record_attempt()` whenever the shared admission remains active.

### External authorization evidence

Cedar evaluates a concrete authorization request over principal/action/resource/context
against the current policy/entity state. Its public authorizer takes a `Request`,
`PolicySet`, and `Entities` for each decision. Current source inspected:
`cedar-policy/cedar@1dd5fb84743c6509b8b7fc8fa178604d5513307d`,
`cedar-policy-core/src/authorizer.rs`.

OPA likewise separates decision evaluation from application enforcement. Its SDK evaluates
the current input/policy state per decision, while the integrating application owns how
that result is enforced. Current source inspected:
`open-policy-agent/opa@620b7a54c1cca80abe1c0ea831b4598379fa1f98`,
`v1/sdk/opa.go` and `docs/docs/integration.md`.

Official current docs additionally reinforce exact request scope and fail-closed
integration:
- https://docs.cedarpolicy.com/auth/authorization.html
- https://docs.cedarpolicy.com/bestpractices/bp-authorization-patterns.html
- https://www.openpolicyagent.org/docs/operations

These sources support forward authorization from current validated state. They do not
justify rewriting historical action authority after the fact.

## Alternatives

### A. Preserve schema-2 legacy mutation path — REJECT

This keeps a real future mutation outside Core-v1 authorization and therefore blocks
freeze.

### B. Rewrite historical schema-2 attempts as if they used the new grant — REJECT

That would falsify historical authority evidence.

### C. Reject every schema-2 resume — SAFE BUT REJECTED

Fail-closing all old checkpoints would remove the authority gap but unnecessarily discard
already accepted crash-recovery compatibility.

### D. Forward-only grant handoff after fresh reconciliation/state proof — SELECT

Keep all historical attempts/reconciliations unchanged.

Before any **new** physical mutation:

1. load and validate the genuine schema-2 checkpoint;
2. reconcile any prepared historical intent first, using the historical bookkeeping path
   only to describe that already-attempted effect;
3. require no unresolved attempt;
4. obtain a fresh authoritative workspace observation and verify the current resumable
   node/state exactly;
5. replace only the active capability grant set with the deterministic schema-3 concrete
   grant;
6. record an evidence ref for that authority handoff and advance WorkingState revision;
7. durably checkpoint schema 3;
8. allow all subsequent physical mutations only through
   `evaluate_authorized() / record_authorized_attempt()`.

The handoff does not authorize or rewrite any prior physical attempt.

## Core primitive

Add one bounded WorkingState operation:

`replace_capability_grants(grant_refs, evidence_ref, expected_revision)`

Rules:

- exact current revision required;
- grant refs are bounded normalized refs;
- evidence ref is required;
- unresolved mutating outcomes block grant replacement;
- no attempt/failure/reconciliation history is changed;
- budgets are unchanged;
- revision increments once;
- the evidence ref is appended to existing WorkingState evidence.

This is active-authority state maintenance, not a registry, policy engine, or grant store.

## Failure matrix

| Boundary | Failure | Required behavior |
|---|---|---|
| schema-2 load | malformed/tampered historical state | fail closed |
| prepared historical intent | effect remains unknown | no handoff, no new mutation |
| fresh resumable-state proof | mismatch/ambiguity | no handoff, no mutation |
| grant replacement | stale revision | fail closed |
| grant replacement | unresolved attempt exists | fail closed |
| handoff checkpoint | durable write fails | no later mutation in that call |
| post-handoff transition | exact grant/request/intent mismatch | block before delivery |
| prior history | old attempt lacked new grant | history remains unchanged and is not reclassified |
| completed schema-2 checkpoint | no future mutation needed | may be verified/read as historical state; no synthetic grant required |

## Failure-class guard

After this change:

- `_workspace_guard_decision()` must have no legacy branch;
- all newly delivered workspace mutations must use `evaluate_authorized()`;
- `_record_workspace_attempt()` must always use `record_authorized_attempt()`;
- any use of legacy `record_attempt()` in the workspace consumer is restricted to
  reconciliation bookkeeping for an already-prepared schema-2 historical intent and
  cannot sit on a path that initiates a new delivery.

Tests must prove a schema-2 `staged_verified` checkpoint is upgraded to schema 3 before
`final_create`, and a schema-2 `final_verified` checkpoint is upgraded before
`staging_cleanup`.

## Architecture lineage

- Capability authorization — **REUSE_MORE** existing project Core.
- WorkingState — **REFINE** with one bounded active-grant replacement operation.
- Workspace crash/recovery semantics — **KEEP**.
- Filesystem delivery mechanics — **KEEP**.
- Verification Kernel / Finish Gate — **KEEP**.
- External policy engine / grant registry — **REJECT**.

## Acceptance

L1:
- WorkingState grant replacement revision/evidence/unresolved checks;
- exact schema-2 -> schema-3 forward handoff tests;
- prior attempt history remains byte-for-byte semantically unchanged;
- wrong/tampered grant remains fail closed;
- no legacy guard branch before any new workspace delivery.

L2:
- existing workspace crash/reconciliation suites;
- Core authorization/enforcement suites;
- six-tool Semantic Projection acceptance;
- full hosted CI/security.

No new physical filesystem behavior is introduced; the existing exact file mechanics are
unchanged. If tests reveal a change in physical delivery or crash/retry semantics, re-enter
Stage Research.

## Decision

**NARROW**

Implement only the forward-only schema-2 grant handoff and the minimal WorkingState
active-grant replacement primitive. Do not add a policy engine, grant registry, automatic
retry, new public tool, or new provider abstraction.
